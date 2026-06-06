"""
Core ingestion pipeline.
Orchestrates the full flow: normalize → persist → embed → (async) compress
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.adapters.registry import get_adapter
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.source import Source


# from app.services.embedding_service import EmbeddingService
from app.services.embeddings.embedding_service import EmbeddingService


from app.ingestion.sanitizer import sanitizer

logger = structlog.get_logger()


class IngestionPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService(db)

    async def run(self, raw_payload: dict, project_id: str | None = None) -> Conversation:
        """
        Full ingestion flow:
        1. Normalize via adapter
        2. Resolve/create Source
        3. Persist Conversation + Messages
        4. Trigger async embedding generation
        Returns the persisted Conversation.
        """
        source_slug = raw_payload.get("source", "unknown")
        log = logger.bind(source=source_slug, project_id=project_id)

        # 1. Normalize
        adapter = get_adapter(source_slug)
        normalized = adapter.normalize(raw_payload)
        log.info("ingestion_normalized", message_count=len(normalized.messages))

        # 2. Resolve Source
        source = await self._get_or_create_source(normalized.source_slug)

        # 2.5. Idempotency Check (Prevent duplicate capture)
        if normalized.source_url and project_id:
            existing = await self.db.execute(
                select(Conversation).where(
                    Conversation.source_url == normalized.source_url,
                    Conversation.project_id == project_id
                )
            )
            if existing.scalars().first():
                raise ValueError("Duplicate: Conversation from this URL is already captured for this project.")

        # 3. Persist Conversation
        conversation = Conversation(
            project_id=project_id,
            source_id=source.id,
            title=normalized.title or f"Conversation from {normalized.source_slug}",
            source_url=normalized.source_url,
            captured_at=normalized.captured_at,
            message_count=len(normalized.messages),
            total_tokens=sum(m.token_count or 0 for m in normalized.messages),
            status="raw",
        )
        self.db.add(conversation)
        await self.db.flush()  # Get the conversation ID

        # 4. Persist Messages
        for nm in normalized.messages:
            # SANITIZATION LAYER: Strip secrets before DB write
            clean_content = sanitizer.sanitize(nm.content).content

            msg = Message(
                conversation_id=conversation.id,
                role=nm.role,
                content=clean_content,
                position=nm.position,
                token_count=nm.token_count,
                message_timestamp=nm.message_timestamp,
            )
            self.db.add(msg)

        await self.db.commit()
        await self.db.refresh(conversation)

        log.info("ingestion_persisted", conversation_id=str(conversation.id))

        # 5. Trigger embedding generation and capsule creation
        try:
            await self.embedding_service.embed_conversation(conversation.id)
            
            # 6. Trigger memory capsule generation
            from app.compression.capsule_builder import CapsuleBuilder
            builder = CapsuleBuilder(self.db)
            capsule, _ = await builder.build_from_conversation(str(conversation.id))
            if capsule:
                await self.embedding_service.embed_capsule(capsule.id)
                log.info("capsule_built_and_embedded", capsule_id=str(capsule.id))
                
        except Exception as e:
            log.warning("post_ingestion_tasks_failed", error=str(e), conversation_id=str(conversation.id))

        return conversation

    async def _get_or_create_source(self, slug: str) -> Source:
        """Get existing Source or create a new one."""
        result = await self.db.execute(select(Source).where(Source.slug == slug))
        source = result.scalars().first()
        if not source:
            source = Source(name=slug.title(), slug=slug)
            self.db.add(source)
            await self.db.flush()
        return source
