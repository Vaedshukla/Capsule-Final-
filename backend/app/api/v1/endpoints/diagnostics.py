"""
Diagnostics endpoint for validating retrieval and ranking architecture.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker
from app.retrieval.context_assembler import ContextAssembler

from app.evaluation.retrieval_benchmark import RetrievalBenchmark
from app.evaluation.ranking_evaluator import RankingEvaluator
from app.evaluation.token_efficiency import TokenEfficiencyEvaluator
from app.evaluation.chunking_evaluator import ChunkingEvaluator
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.evaluation.chunk_visualizer import ChunkVisualizer

router = APIRouter()

@router.get("/retrieval", summary="Test retrieval and ranking quality")
async def diagnostics_retrieval(
    q: str = Query(..., description="The query to test"),
    limit: int = Query(20, description="Max raw results to fetch"),
    db: AsyncSession = Depends(get_db),
):
    searcher = SemanticSearch(db)
    
    # Fetch both capsules and chunks
    capsules = await searcher.search_capsules(query=q, limit=limit)
    chunks = await searcher.search_chunks(query=q, limit=limit)
    raw_results = capsules + chunks
    
    # Rank
    ranker = MemoryRanker(db)
    ranked = await ranker.rank(raw_results)
    
    # Assemble
    assembler = ContextAssembler(db)
    formatted_context, tokens = await assembler.assemble(ranked, q)
    
    return {
        "query": q,
        "raw_results_count": len(raw_results),
        "ranked_results": [
            {
                "id": r.id,
                "type": r.type,
                "title": r.title,
                "raw_similarity": r.raw_similarity,
                "rank_score": r.rank_score,
                "importance_score": r.importance_score,
                "recency_score": r.recency_score,
                "access_score": r.access_score,
            }
            for r in ranked
        ],
        "assembled_context": {
            "estimated_tokens": tokens,
            "budget": assembler.budget,
            "preview": formatted_context[:1000] + ("..." if len(formatted_context) > 1000 else "")
        }
    }

@router.get("/benchmark", summary="Run full retrieval benchmark suite")
async def diagnostics_benchmark(db: AsyncSession = Depends(get_db)):
    bench = RetrievalBenchmark(db)
    return await bench.run_benchmark(k_values=[3, 5])

@router.get("/ranking", summary="Compare raw cosine similarity vs MemoryRanker")
async def diagnostics_ranking(db: AsyncSession = Depends(get_db)):
    evaluator = RankingEvaluator(db)
    return await evaluator.compare_rankings()

@router.get("/economy", summary="Evaluate token reduction metrics")
async def diagnostics_economy(db: AsyncSession = Depends(get_db)):
    evaluator = TokenEfficiencyEvaluator(db)
    return await evaluator.evaluate()

@router.get("/chunking", summary="Evaluate chunk boundary distribution")
async def diagnostics_chunking(db: AsyncSession = Depends(get_db)):
    evaluator = ChunkingEvaluator(db)
    return await evaluator.evaluate_boundaries()

@router.get("/failures", summary="Analyze false positives and negatives")
async def diagnostics_failures(db: AsyncSession = Depends(get_db)):
    analyzer = FailureAnalyzer(db)
    return await analyzer.analyze_failures()

@router.get("/drift", summary="Measure semantic drift against limits")
async def diagnostics_drift(db: AsyncSession = Depends(get_db)):
    analyzer = FailureAnalyzer(db)
    return await analyzer.measure_semantic_drift()

@router.get("/chunk-boundaries/{message_id}", summary="Visualize chunk splits")
async def diagnostics_chunk_boundaries(message_id: str, db: AsyncSession = Depends(get_db)):
    visualizer = ChunkVisualizer(db)
    return await visualizer.visualize_message_chunks(message_id)
