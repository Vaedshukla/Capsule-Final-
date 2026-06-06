"""
Context injection endpoint.
Retrieves the most relevant MemoryCapsules for a query
and formats them into a ready-to-inject context payload.
"""
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.schemas.schemas import InjectionRequest, InjectionPayload, CapsuleOut
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker
from app.retrieval.context_assembler import ContextAssembler
from app.models.memory_capsule import MemoryCapsule
from app.models.graph import Injection

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/context",
    response_model=InjectionPayload,
    summary="Retrieve and format context for AI injection",
    description="""
    Given a natural language query, retrieves the most relevant MemoryCapsules
    and returns a pre-formatted context block ready to be prepended to an AI conversation.
    Also records the injection event for tracking.
    """,
)
async def inject_context(
    request: InjectionRequest,
    db: AsyncSession = Depends(get_db),
):
    searcher = SemanticSearch(db)
    capsule_results = await searcher.search_capsules(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit,
        min_similarity=0.3,
    )

    if not capsule_results:
        return InjectionPayload(
            context_header="## Capsule Context",
            capsules=[],
            formatted_context="No relevant memory found for this query.",
            token_estimate=10,
        )

    # Rerank
    ranker = MemoryRanker(db)
    ranked_results = await ranker.rank(capsule_results)

    # Assemble context
    assembler = ContextAssembler(db)
    formatted_context, token_estimate = await assembler.assemble(ranked_results, request.query)

    # We need the full capsule objects for tracking and output
    capsule_ids = [r.id for r in ranked_results if r.type == "capsule"]
    capsules = []
    if capsule_ids:
        result = await db.execute(select(MemoryCapsule).where(MemoryCapsule.id.in_(capsule_ids)))
        capsules = result.scalars().all()

    # Track injections
    for capsule in capsules:
        injection = Injection(
            capsule_id=capsule.id,
            target_source=request.target_source,
            query_used=request.query,
        )
        db.add(injection)
        capsule.access_count += 1

    await db.commit()

    capsule_outs = [CapsuleOut.model_validate(c) for c in capsules]

    logger.info(
        "context_injected",
        query=request.query[:50],
        capsule_count=len(capsules),
        token_estimate=token_estimate,
    )

    return InjectionPayload(
        context_header="## Capsule Context",
        capsules=capsule_outs,
        formatted_context=formatted_context,
        token_estimate=token_estimate,
    )
