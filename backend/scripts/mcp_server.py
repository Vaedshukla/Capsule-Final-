import asyncio
import os
import sys
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_maker
from app.models.project import Project
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker
from app.models.mcp_telemetry import MCPTelemetry

# Initialize FastMCP Server
mcp = FastMCP("capsule-mcp-server")


@mcp.tool()
async def list_projects() -> str:
    """
    List all available Project Capsule projects and their UUIDs.
    Use this tool to find the `project_id` required for memory searches.
    """
    start_time = time.perf_counter()
    async with async_session_maker() as db:
        stmt = select(Project).order_by(Project.created_at.desc())
        result = await db.execute(stmt)
        projects = result.scalars().all()

        if not projects:
            return "No projects found in Project Capsule."

        output = ["# Project Capsule — Available Projects\n"]
        for p in projects:
            output.append(f"- **{p.name}**: `{str(p.id)}`")

        # Telemetry
        latency_ms = (time.perf_counter() - start_time) * 1000
        telemetry = MCPTelemetry(
            tool_name="list_projects",
            latency_ms=latency_ms,
            memory_count=len(projects),
            avg_confidence=0.0
        )
        db.add(telemetry)
        await db.commit()

        return "\n".join(output)


@mcp.tool()
async def search_project_memory(query: str, project_id: Optional[str] = None) -> str:
    """
    Search the Project Capsule semantic memory for architectural decisions, constraints, risks, and discussions.
    Returns markdown-formatted summaries of the top retrieved Memory Capsules and Message Chunks.
    
    Args:
        query: The natural language search query (e.g., "What database decisions did we make?").
        project_id: Optional UUID of the project to filter by. Highly recommended to use list_projects first to find this.
    """
    start_time = time.perf_counter()
    
    # Check if project_id is a valid UUID, otherwise pass None
    if project_id and project_id.lower() == "none":
        project_id = None
        
    async with async_session_maker() as db:
        searcher = SemanticSearch(db)
        
        # We retrieve up to 10 top results across both capsules and chunks
        capsule_results = await searcher.search_capsules(
            query=query,
            project_id=project_id,
            limit=5,
            min_similarity=0.1,
        )
        message_results = await searcher.search_chunks(
            query=query,
            project_id=project_id,
            limit=5,
            min_similarity=0.1,
        )

        combined_results = capsule_results + message_results
        combined_results.sort(key=lambda r: r.similarity_score, reverse=True)

        if not combined_results:
            latency_ms = (time.perf_counter() - start_time) * 1000
            telemetry = MCPTelemetry(
                tool_name="search_project_memory",
                query=query,
                project_id=project_id,
                latency_ms=latency_ms,
                memory_count=0,
                avg_confidence=0.0
            )
            db.add(telemetry)
            await db.commit()
            return f"No context found in Project Capsule for query: '{query}'"

        # Apply Re-ranking
        ranker = MemoryRanker(db)
        ranked_results = await ranker.rank(combined_results)
        
        # Take the top 5 after ranking
        top_results = ranked_results[:5]

        output = [f"# Memory Context for: '{query}'\n"]
        
        for idx, res in enumerate(top_results, 1):
            source_info = f"Project ID: {res.project_id}"
            if res.source_slug:
                source_info += f" | Source: {res.source_slug}"
                
            output.append(f"## {idx}. [{res.type.upper()}] {res.title}")
            output.append(f"**Similarity Score:** {res.similarity_score:.2f} | **Rank Score:** {res.rank_score:.2f}")
            output.append(f"**Context:** {source_info}\n")
            output.append(f"{res.content}\n")
            output.append("---\n")

        # Telemetry
        latency_ms = (time.perf_counter() - start_time) * 1000
        memory_count = len(top_results)
        avg_confidence = sum(r.rank_score for r in top_results) / memory_count if memory_count > 0 else 0.0
        
        telemetry = MCPTelemetry(
            tool_name="search_project_memory",
            query=query,
            project_id=project_id,
            latency_ms=latency_ms,
            memory_count=memory_count,
            avg_confidence=avg_confidence
        )
        db.add(telemetry)
        await db.commit()

        return "\n".join(output)

if __name__ == "__main__":
    # When run directly, default to stdio transport.
    mcp.run()
