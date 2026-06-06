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
        user = User(id=user_id, email=f"test_{user_id}@projectcapsule.dev", password_hash="mock", is_active=True)
        db.add(user)
        await db.flush()
        
        alpha_id = uuid.uuid4()
        cog_id = uuid.uuid4()
        p1 = Project(id=alpha_id, user_id=user_id, name="Project Alpha")
        p2 = Project(id=cog_id, user_id=user_id, name="Cognitive-X")
        db.add(p1)
        db.add(p2)
        await db.flush()

        conversations_data = [
            # PROJECT ALPHA
            {
                "project_id": alpha_id,
                "title": "Architecture Planning: Database Selection",
                "messages": [
                    "We need to decide on our primary database. Should we use MongoDB or PostgreSQL?",
                    "Let's go with PostgreSQL. PostgreSQL selected over MongoDB because we need ACID compliance cited as a hard requirement. Also, pgvector required for memory embeddings."
                ],
                "decisions": ["PostgreSQL selected over MongoDB", "pgvector required", "ACID compliance cited"],
                "constraints": ["Must use relational DB"],
                "risks": ["Migration complexity"],
                "confidence": 0.95
            },
            {
                "project_id": alpha_id,
                "title": "Authentication Design",
                "messages": [
                    "How are we handling auth?",
                    "We have a constraint. Short-lived JWT access tokens are mandatory. We will use Redis-backed refresh sessions to manage state."
                ],
                "decisions": ["Implement JWT"],
                "constraints": ["Short-lived JWT access tokens", "Redis-backed refresh sessions"],
                "risks": ["Token hijacking"],
                "confidence": 0.90
            },
            {
                "project_id": alpha_id,
                "title": "Agent Communication Design",
                "messages": [
                    "How will agents query the DB?",
                    "We will build a Model Context Protocol server. This allows Cursor Integration natively. We also need Asynchronous context injection."
                ],
                "decisions": ["Model Context Protocol", "Cursor Integration"],
                "requirements": ["Asynchronous context injection"],
                "risks": [],
                "confidence": 0.88
            },
            
            # COGNITIVE-X
            {
                "project_id": cog_id,
                "title": "Infrastructure Decisions",
                "messages": [
                    "We are struggling with local setups.",
                    "Everything Must be containerized. Docker Desktop required. Avoid native build tools on Windows due to C++ compile errors."
                ],
                "decisions": ["Must be containerized"],
                "constraints": ["Docker Desktop required", "Avoid native build tools"],
                "risks": ["Windows native compilation failures"],
                "confidence": 0.92
            },
            {
                "project_id": cog_id,
                "title": "Deployment Strategy & Risks",
                "messages": [
                    "Are there any deployment risks?",
                    "Yes, Windows native compilation failures if we don't use Docker. Also Redis latency over network could be an issue if not in the same VPC."
                ],
                "decisions": [],
                "risks": ["Windows native compilation failures", "Redis latency over network"],
                "confidence": 0.85
            },
            {
                "project_id": cog_id,
                "title": "Filtering Engine Design",
                "messages": [
                    "How does the ranking engine work?",
                    "We use Reciprocal Rank Fusion to blend BM25 and vector scores, combined with strict Confidence thresholding to drop noise."
                ],
                "decisions": ["Reciprocal Rank Fusion", "Confidence thresholding"],
                "requirements": ["RRF must be weighted"],
                "confidence": 0.96
            },
            
            # NOISE
            {
                "project_id": alpha_id,
                "title": "Random Brainstorming (No Decisions)",
                "messages": [
                    "What if we used Neo4j? Or maybe Cassandra? Let's just think about it.",
                    "Yeah Neo4j is cool. No final decision made."
                ],
                "decisions": [],
                "risks": [],
                "confidence": 0.40
            },
            {
                "project_id": cog_id,
                "title": "Contradictory Database Chat",
                "messages": [
                    "Maybe Cognitive-X should use MongoDB instead of Postgres?",
                    "No, we rejected MongoDB. We are using Postgres just like Alpha."
                ],
                "decisions": ["Rejected MongoDB"],
                "risks": [],
                "confidence": 0.60
            }
        ]

        print("Populating Conversations, Messages, and Capsules...")
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
            msg.role = "assistant" # Must be assistant to be retrieved in RRF
            msg.content = full_text
            msg.position = 1
            db.add(msg)
            await db.flush()
            
            # Embed chunk
            embedding = await embed_service.provider.embed(full_text)
            chunk = MessageChunk()
            chunk.id = uuid.uuid4()
            chunk.message_id = msg.id
            chunk.chunk_index = 0
            chunk.content = full_text
            chunk.embedding = embedding
            db.add(chunk)
            await db.flush()
            
            # Create Capsule
            cap = MemoryCapsule()
            cap.id = uuid.uuid4()
            cap.project_id = data["project_id"]
            cap.conversation_id = conv.id
            cap.title = data["title"]
            cap.summary = full_text
            cap.decisions = json.dumps(data.get("decisions", []))
            cap.constraints = json.dumps(data.get("constraints", []))
            cap.risks = json.dumps(data.get("risks", []))
            cap.requirements = json.dumps(data.get("requirements", []))
            cap.embedding = embedding
            cap.confidence_score = data["confidence"]
            cap.importance_score = 0.8
            db.add(cap)
            await db.flush()

        await db.commit()
        print("✅ Phase 4 Benchmark Dataset Seeded Successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
