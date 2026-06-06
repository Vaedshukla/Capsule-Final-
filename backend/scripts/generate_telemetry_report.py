import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.future import select
from sqlalchemy import func, cast, Integer
from app.db.session import async_session_maker
from app.models.mcp_telemetry import MCPTelemetry

async def generate_report():
    async with async_session_maker() as db:
        # Total Invocations
        stmt_total = select(func.count(MCPTelemetry.id))
        total_invocations = await db.scalar(stmt_total)

        if total_invocations == 0:
            print("No telemetry data found.")
            return

        # Latency & Memory Count by Tool
        stmt_stats = select(
            MCPTelemetry.tool_name,
            func.count(MCPTelemetry.id).label("calls"),
            func.avg(MCPTelemetry.latency_ms).label("avg_latency"),
            func.avg(MCPTelemetry.memory_count).label("avg_memory"),
            func.sum(
                cast(MCPTelemetry.memory_count == 0, Integer)
            ).label("failures")
        ).group_by(MCPTelemetry.tool_name)
        
        result_stats = await db.execute(stmt_stats)
        stats = result_stats.all()

        print("========================================")
        print("      MCP TELEMETRY ANALYTICS           ")
        print("========================================")
        print(f"Total Tool Invocations : {total_invocations}\n")
        
        for stat in stats:
            print(f"Tool: {stat.tool_name}")
            print(f"  - Invocations    : {stat.calls}")
            print(f"  - Avg Latency    : {stat.avg_latency:.1f} ms")
            print(f"  - Avg Memory Cnt : {stat.avg_memory:.1f} chunks")
            failure_rate = (stat.failures / stat.calls) * 100
            print(f"  - Failure Rate   : {stat.failures} ({failure_rate:.1f}%)\n")

if __name__ == "__main__":
    asyncio.run(generate_report())
