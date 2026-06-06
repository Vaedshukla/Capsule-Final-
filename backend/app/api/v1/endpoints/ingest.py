"""
POST /api/v1/ingest/conversation
The primary ingestion endpoint — called by the browser extension.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import IngestConversationIn, IngestConversationOut
from app.ingestion.pipeline import IngestionPipeline

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/conversation",
    response_model=IngestConversationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a captured AI conversation",
    description="""
    Accepts a conversation payload from the browser extension or API client.
    Normalizes via platform adapter, persists to DB, and triggers async embedding.
    """,
)
async def ingest_conversation(
    payload: IngestConversationIn,
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        pipeline = IngestionPipeline(db)
        raw = payload.model_dump()
        conversation = await pipeline.run(raw_payload=raw, project_id=project_id)

        return IngestConversationOut(
            conversation_id=str(conversation.id),
            status=conversation.status,
            message_count=conversation.message_count,
            summary_preview=conversation.summary,
        )
    except ValueError as e:
        logger.warning("ingestion_rejected", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error("ingest_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )
