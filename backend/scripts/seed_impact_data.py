import asyncio
import uuid
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import async_session_maker
from app.models.project import Project
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.memory_capsule import MemoryCapsule
from app.models.message_chunk import MessageChunk
from app.models.user import User
from app.services.embeddings.embedding_service import EmbeddingService

async def seed_data():
    async with async_session_maker() as db:
        embed_service = EmbeddingService(db)
        
        print("Creating User & Projects...")
        user_id = uuid.uuid4()
        user = User(id=user_id, email=f"impact_{user_id}@projectcapsule.dev", password_hash="mock", is_active=True)
        db.add(user)
        await db.flush()
        
        alpha_id = uuid.uuid4()
        cog_id = uuid.uuid4()
        p1 = Project(id=alpha_id, user_id=user_id, name="Impact Project Alpha")
        p2 = Project(id=cog_id, user_id=user_id, name="Impact Cognitive-X")
        db.add(p1)
        db.add(p2)
        await db.flush()

        # Save project IDs to environment variables or a config file for the eval script
        with open(os.path.join(os.path.dirname(__file__), "impact_projects.json"), "w") as f:
            json.dump({"alpha_id": str(alpha_id), "cog_id": str(cog_id)}, f)

        conversations_data = [
            # 1. Architecture
            {
                "project_id": alpha_id,
                "title": "Core Database Architecture",
                "category": "Architecture decisions",
                "query": "Why did we choose PostgreSQL?",
                "messages": [
                    "We need to decide on our primary database. Should we use MongoDB or PostgreSQL?",
                    "Let's go with PostgreSQL. PostgreSQL selected over MongoDB because we need ACID compliance. Also, pgvector is required for memory embeddings."
                ],
                "expected": ["ACID compliance", "pgvector", "PostgreSQL selected over MongoDB"]
            },
            # 2. Rejected Alternatives
            {
                "project_id": alpha_id,
                "title": "Evaluating Graph Databases",
                "category": "Rejected alternatives",
                "query": "What database alternatives were rejected and why?",
                "messages": [
                    "What about using Neo4j for memory associations?",
                    "We rejected Neo4j because it adds too much operational overhead and pgvector is sufficient for semantic search."
                ],
                "expected": ["rejected Neo4j", "operational overhead", "pgvector is sufficient"]
            },
            # 3. Authentication Risks
            {
                "project_id": alpha_id,
                "title": "Auth Vulnerability Analysis",
                "category": "Authentication",
                "query": "What authentication risks were identified?",
                "messages": [
                    "Are there any risks with our JWT strategy?",
                    "Yes, token hijacking is a major risk. We must use short-lived JWT access tokens and HttpOnly cookies to mitigate XSS attacks."
                ],
                "expected": ["token hijacking", "short-lived JWT access tokens", "HttpOnly cookies", "XSS attacks"]
            },
            # 4. Deployment Constraints
            {
                "project_id": cog_id,
                "title": "VPC and Network Setup",
                "category": "Deployment",
                "query": "What deployment constraints exist?",
                "messages": [
                    "How are we deploying the Redis cache?",
                    "Redis latency over network is too high. The deployment constraint is that Redis must be in the same VPC as the application servers."
                ],
                "expected": ["Redis latency", "same VPC as the application servers"]
            },
            # 5. Planning Assumptions
            {
                "project_id": cog_id,
                "title": "Agent Workload Projections",
                "category": "Requirements",
                "query": "What assumptions were made during planning regarding agent workloads?",
                "messages": [
                    "How much traffic should we expect?",
                    "Our planning assumption is 100 concurrent agents. We assume each agent makes 5 memory retrieval requests per minute."
                ],
                "expected": ["100 concurrent agents", "5 memory retrieval requests per minute"]
            },
            # 6. Timeline Evolution
            {
                "project_id": alpha_id,
                "title": "Roadmap Adjustments",
                "category": "Timeline evolution",
                "query": "How did our architecture roadmap evolve over time?",
                "messages": [
                    "We originally planned the Next.js Dashboard for Phase 2.",
                    "We changed the timeline. The MCP Server was prioritized over the Dashboard to validate agent integration immediately."
                ],
                "expected": ["Next.js Dashboard for Phase 2", "MCP Server was prioritized over the Dashboard", "validate agent integration"]
            },
            # 7. Infrastructure
            {
                "project_id": cog_id,
                "title": "Containerization Strategy",
                "category": "Infrastructure",
                "query": "What infrastructure tools are we using?",
                "messages": [
                    "We need to ensure local environments are consistent.",
                    "Everything must be containerized using Docker Desktop. Avoid native build tools on Windows due to C++ compile errors."
                ],
                "expected": ["containerized using Docker Desktop", "Avoid native build tools on Windows"]
            },
            # 8. Historical Tradeoffs
            {
                "project_id": alpha_id,
                "title": "Embedding Models Tradeoff",
                "category": "Historical tradeoffs",
                "query": "What was the tradeoff between local vs cloud embeddings?",
                "messages": [
                    "Should we use OpenAI for embeddings?",
                    "The tradeoff: OpenAI gives higher dimensionality (1536) but costs money and adds latency. We chose all-MiniLM-L6-v2 for zero-cost local inference despite lower dimensionality (384)."
                ],
                "expected": ["OpenAI gives higher dimensionality", "costs money and adds latency", "chose all-MiniLM-L6-v2", "zero-cost local inference"]
            },
            # 9. Architecture Decisions
            {
                "project_id": cog_id,
                "title": "Ranking Engine",
                "category": "Architecture decisions",
                "query": "How is the filtering engine designed?",
                "messages": [
                    "How do we combine keyword and vector search?",
                    "We use Reciprocal Rank Fusion to blend BM25 and vector scores, combined with strict Confidence thresholding to drop noise."
                ],
                "expected": ["Reciprocal Rank Fusion", "blend BM25 and vector scores", "Confidence thresholding"]
            },
            # 10. Requirements
            {
                "project_id": alpha_id,
                "title": "Agent Integration Specs",
                "category": "Requirements",
                "query": "What are the requirements for agent communication?",
                "messages": [
                    "What does Cursor need to integrate with Capsule?",
                    "We must implement the Model Context Protocol over stdio. Asynchronous context injection is also a hard requirement."
                ],
                "expected": ["Model Context Protocol over stdio", "Asynchronous context injection"]
            },
            # Add 15 more procedurally generated to hit 25...
        ]

        # Procedurally generate 15 more conversations to hit the 25 count
        for i in range(11, 26):
            pid = alpha_id if i % 2 == 0 else cog_id
            conversations_data.append({
                "project_id": pid,
                "title": f"Synthetic Discussion {i}",
                "category": "Generated",
                "query": f"What was decided in discussion {i}?",
                "messages": [
                    f"Let's discuss topic {i}.",
                    f"We decided that topic {i} requires feature X_{i} and constraint Y_{i}."
                ],
                "expected": [f"feature X_{i}", f"constraint Y_{i}"]
            })

        print(f"Populating {len(conversations_data)} Conversations...")
        
        eval_queries = []
        for data in conversations_data:
            conv = Conversation()
            conv.id = uuid.uuid4()
            conv.project_id = data["project_id"]
            conv.title = data["title"]
            db.add(conv)
            await db.flush()
            
            full_text = " ".join(data["messages"])
            msg = Message()
            msg.id = uuid.uuid4()
            msg.conversation_id = conv.id
            msg.role = "assistant" 
            msg.content = full_text
            msg.position = 1
            db.add(msg)
            await db.flush()
            
            embedding = await embed_service.provider.embed(full_text)
            chunk = MessageChunk()
            chunk.id = uuid.uuid4()
            chunk.message_id = msg.id
            chunk.chunk_index = 0
            chunk.content = full_text
            chunk.embedding = embedding
            db.add(chunk)
            await db.flush()
            
            cap = MemoryCapsule()
            cap.id = uuid.uuid4()
            cap.project_id = data["project_id"]
            cap.conversation_id = conv.id
            cap.title = data["title"]
            cap.summary = full_text
            cap.decisions = json.dumps(data.get("expected", []))
            cap.embedding = embedding
            cap.confidence_score = 0.90
            cap.importance_score = 0.8
            db.add(cap)
            await db.flush()
            
            eval_queries.append({
                "project_id": str(data["project_id"]),
                "category": data["category"],
                "query": data["query"],
                "expected": data["expected"]
            })

        await db.commit()
        
        with open(os.path.join(os.path.dirname(__file__), "impact_ground_truth.json"), "w") as f:
            json.dump(eval_queries, f, indent=2)
            
        print("✅ Phase 4.5 Impact Dataset Seeded Successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
