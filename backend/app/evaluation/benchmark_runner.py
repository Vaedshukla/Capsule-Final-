"""
Benchmark Runner — Evaluates embedding models, ranking strategies, and extraction schemas.
"""
import structlog
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.evaluation.ranking_evaluator import RankingEvaluator
from app.retrieval.semantic_search import SemanticSearch

logger = structlog.get_logger()

class BenchmarkRunner:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ranking_eval = RankingEvaluator(db, SemanticSearch)

    async def run_full_benchmark(self) -> Dict[str, Any]:
        """
        Run the complete evaluation suite.
        """
        logger.info("benchmark_started")
        
        ranking_results = await self.ranking_eval.compare_rankings()
        
        logger.info("benchmark_completed")
        
        return {
            "status": "success",
            "ranking_metrics": ranking_results,
            # Extraction metrics would be added here
        }
