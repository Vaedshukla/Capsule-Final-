"""
Synthetic Dataset Generator for evaluating retrieval pipelines.
Generates realistic conversation traces with noise, cross-project references,
and overlapping terminology.
"""
import uuid
import random
from datetime import datetime, timedelta

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.project import Project

# ─── Mock Datasets ────────────────────────────────────────────────────────────

CONVERSATIONS_DATA = [
    {
        "project_name": "Project Alpha (Auth)",
        "title": "Auth Refactor - JWT to Session",
        "messages": [
            ("user", "We need to fix the JWT expiration bug. Users are getting logged out while typing."),
            ("assistant", "The issue is that our JWTs have a hard 1-hour expiration and we aren't using refresh tokens. A better architecture would be to use opaque session tokens stored in Redis. This allows us to extend the session transparently on activity."),
            ("user", "How would the Redis schema look?"),
            ("assistant", "We can use `session:{user_id}:{session_id}` as the key, and store a JSON blob with user claims. The TTL can be set to 24 hours and updated on every request middleware."),
        ]
    },
    {
        "project_name": "Project Beta (Caching)",
        "title": "Redis Caching Strategy",
        "messages": [
            ("user", "The dashboard is slow. We need to cache the analytics queries."),
            ("assistant", "We can use Redis to cache the expensive aggregation queries. We should use a TTL of 15 minutes for real-time dashboards. For the key schema, let's use `cache:analytics:{org_id}:{time_range}`."),
            ("user", "What about cache invalidation?"),
            ("assistant", "Cache invalidation is notoriously hard. Instead of active invalidation, we should rely on short TTLs. If immediate consistency is required, we can use a pub/sub event to delete the specific `cache:analytics:{org_id}:*` keys when new data arrives."),
        ]
    },
    {
        "project_name": "Project Gamma (Frontend)",
        "title": "Frontend State Integration",
        "messages": [
            ("user", "Should we use React Context or Redux for the new dashboard?"),
            ("assistant", "For the new dashboard, React Context is sufficient for theme and auth state. However, for the complex analytics filtering state, Redux Toolkit or Zustand will prevent unnecessary re-renders. I recommend Zustand for its boilerplate-free API."),
            ("user", "Okay, how do we handle session state?"), # Overlapping term "session"
            ("assistant", "Session state should just be a React Context that wraps the app, reading from the HttpOnly cookie. We don't need Zustand for that."),
        ]
    },
    {
        "project_name": "Project Alpha (Auth)",
        "title": "FastAPI Architecture Decisions",
        "messages": [
            ("user", "How should we structure the FastAPI routes for the auth service?"),
            ("assistant", "We should use a modular monolithic structure. Separate routers for `/auth/login`, `/auth/logout`, and `/auth/session`. We'll inject the Redis connection pool using FastAPI Dependencies (`Depends()`)."),
            ("user", "What about middleware?"),
            ("assistant", "We need a middleware to check the session token on every request. It will read the `Authorization` header or cookie, query Redis, and attach the user object to `request.state.user`."),
        ]
    },
    {
        "project_name": "Project Delta (DevOps)",
        "title": "Deployment Pipeline Timeout",
        "messages": [
            ("user", "The GitHub Actions pipeline is timing out during the Docker build."),
            ("assistant", "The timeout is likely due to downloading Python dependencies from scratch on every run. We should implement Docker layer caching. Use `actions/cache` for the `~/.cache/pip` directory, and restructure the Dockerfile to copy `requirements.txt` before the rest of the source code."),
        ]
    }
]

class SyntheticDatasetGenerator:
    def __init__(self, db_session):
        self.db = db_session

    async def generate(self) -> list[Conversation]:
        """Generate projects, conversations, and messages in the database."""
        projects = {}
        conversations = []
        
        now = datetime.utcnow()
        
        for data in CONVERSATIONS_DATA:
            p_name = data["project_name"]
            if p_name not in projects:
                p = Project(name=p_name, description="Synthetic project")
                self.db.add(p)
                projects[p_name] = p
            
        await self.db.flush()
        
        for idx, data in enumerate(CONVERSATIONS_DATA):
            p = projects[data["project_name"]]
            
            # Stagger creation times
            conv_time = now - timedelta(days=idx)
            
            conv = Conversation(
                project_id=p.id,
                title=data["title"],
                source_id=None,
                status="raw"
            )
            self.db.add(conv)
            await self.db.flush()
            conversations.append(conv)
            
            for i, (role, content) in enumerate(data["messages"]):
                msg = Message(
                    conversation_id=conv.id,
                    role=role,
                    content=content,
                    position=i,
                    token_count=len(content) // 4,
                    message_timestamp=conv_time + timedelta(minutes=i)
                )
                self.db.add(msg)
                
        await self.db.commit()
        return conversations
