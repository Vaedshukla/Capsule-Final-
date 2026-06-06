"""
CRUD endpoints for MemoryCapsules and compression triggers.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db, async_session_maker
from app.models.memory_capsule import MemoryCapsule
from app.schemas.schemas import CapsuleOut, CapsuleCreate
from app.compression.capsule_builder import CapsuleBuilder
from app.services.embeddings.embedding_service import EmbeddingService

import uuid
import asyncio
from typing import Dict, Any

# Simple in-memory job tracker for Stage 1. 
# Will be moved to Redis in Stage 7.
reprocess_jobs: Dict[str, Dict[str, Any]] = {}

router = APIRouter()
logger = structlog.get_logger()

class CompressionResponse(BaseModel):
    capsule: CapsuleOut
    metrics: dict

class ReprocessRequest(BaseModel):
    capsule_ids: Optional[List[str]] = None
    extraction_version: Optional[str] = None
    project_id: Optional[str] = None
    use_llm: bool = True


@router.get("/", response_model=List[CapsuleOut], summary="List all memory capsules")
async def list_capsules(
    project_id: Optional[str] = None,
    extraction_version: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "importance_score",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(MemoryCapsule)
    
    if project_id:
        query = query.where(MemoryCapsule.project_id == project_id)
    if extraction_version:
        query = query.where(MemoryCapsule.extraction_version == extraction_version)
        
    sort_column = getattr(MemoryCapsule, sort_by, MemoryCapsule.importance_score)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
        
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/compress/{conversation_id}",
    response_model=CompressionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compress a conversation into a MemoryCapsule",
)
async def compress_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    builder = CapsuleBuilder(db)
    capsule, metrics = await builder.build_from_conversation(conversation_id)

    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not build capsule from this conversation (no assistant messages).",
        )

    # Embed the capsule summary
    embedding_service = EmbeddingService(db)
    await embedding_service.embed_capsule(capsule.id)

    logger.info("capsule_created", capsule_id=str(capsule.id))
    return CompressionResponse(capsule=capsule, metrics=metrics.model_dump() if hasattr(metrics, 'model_dump') else metrics.__dict__)


@router.post(
    "/reprocess",
    summary="Reprocess memory capsules (Background Job)",
)
async def reprocess_capsules(
    req: ReprocessRequest,
    db: AsyncSession = Depends(get_db),
):
    query = select(MemoryCapsule)
    if req.capsule_ids:
        query = query.where(MemoryCapsule.id.in_(req.capsule_ids))
    elif req.extraction_version:
        query = query.where(MemoryCapsule.extraction_version == req.extraction_version)
    elif req.project_id:
        query = query.where(MemoryCapsule.project_id == req.project_id)
    else:
        raise HTTPException(status_code=400, detail="Must provide capsule_ids, extraction_version, or project_id")

    result = await db.execute(query)
    capsules = result.scalars().all()
    
    if not capsules:
        return {"job_id": None, "message": "No capsules found matching criteria"}

    job_id = str(uuid.uuid4())
    capsule_ids_to_process = [c.id for c in capsules]
    conversation_ids = [c.conversation_id for c in capsules]
    
    reprocess_jobs[job_id] = {
        "status": "processing",
        "total": len(capsules),
        "processed": 0,
        "success": 0,
        "failed": 0
    }

    async def _process_batch(j_id: str, cap_ids: list, conv_ids: list, use_llm: bool):
        async with async_session_maker() as session:
            builder = CapsuleBuilder(session)
            for cap_id, conv_id in zip(cap_ids, conv_ids):
                try:
                    new_cap, metrics = await builder.build_from_conversation(conv_id, use_llm=use_llm)
                    if new_cap:
                        reprocess_jobs[j_id]["success"] += 1
                        # Remove old capsule to avoid duplicates
                        await session.execute(MemoryCapsule.__table__.delete().where(MemoryCapsule.id == cap_id))
                        await session.commit()
                    else:
                        reprocess_jobs[j_id]["failed"] += 1
                except Exception as e:
                    logger.error("reprocess_failed", cap_id=str(cap_id), error=str(e))
                    reprocess_jobs[j_id]["failed"] += 1
                finally:
                    reprocess_jobs[j_id]["processed"] += 1
                    
            reprocess_jobs[j_id]["status"] = "completed"

    asyncio.create_task(_process_batch(job_id, capsule_ids_to_process, conversation_ids, req.use_llm))

    return {"job_id": job_id, "total_found": len(capsules), "message": "Reprocessing started in background"}


@router.get("/reprocess/{job_id}", summary="Check reprocessing job status")
async def get_reprocess_status(job_id: str):
    if job_id not in reprocess_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return reprocess_jobs[job_id]


@router.get("/{capsule_id}", response_model=CapsuleOut, summary="Get a single capsule")
async def get_capsule(capsule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemoryCapsule).where(MemoryCapsule.id == capsule_id)
    )
    capsule = result.scalars().first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    # Track access
    capsule.access_count += 1
    await db.commit()
    return capsule
