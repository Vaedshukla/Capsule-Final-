"""
Failure Analyzer — inspects why retrieval succeeds or fails.
Identifies False Positives (high rank, irrelevant) and False Negatives (low rank, relevant).
"""
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker
from app.evaluation.retrieval_benchmark import BENCHMARK_QUERIES

class FailureAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.searcher = SemanticSearch(db)
        self.ranker = MemoryRanker(db)

    async def analyze_failures(self, limit: int = 20) -> Dict:
        """
        Analyzes false positives and false negatives for benchmark queries.
        """
        analysis_report = []

        for bq in BENCHMARK_QUERIES:
            query = bq["query"]
            truth = bq["ground_truth_keywords"]
            
            raw_chunks = await self.searcher.search_chunks(query=query, limit=limit)
            ranked_results = await self.ranker.rank(raw_chunks)
            
            false_positives = []
            false_negatives = []
            
            # Determine relevance for all fetched results
            relevance_map = {}
            for r in ranked_results:
                is_relevant = any(kw.lower() in r.content.lower() for kw in truth)
                relevance_map[r.id] = is_relevant
                
            # False Positives: Ranked in Top 3, but not relevant
            top_k = ranked_results[:3]
            for i, r in enumerate(top_k):
                if not relevance_map[r.id]:
                    false_positives.append({
                        "rank": i + 1,
                        "chunk_id": r.id,
                        "project_id": r.project_id,
                        "content_preview": r.content[:100] + "...",
                        "similarity_score": r.similarity_score,
                        "rank_score": r.rank_score,
                        "reason": "High vector similarity but lacks ground truth keywords. Potential cross-project contamination or terminology overlap."
                    })
                    
            # False Negatives: Relevant, but ranked below Top 3 (or completely missed)
            for i, r in enumerate(ranked_results):
                if relevance_map[r.id] and i >= 3:
                    false_negatives.append({
                        "rank": i + 1,
                        "chunk_id": r.id,
                        "project_id": r.project_id,
                        "content_preview": r.content[:100] + "...",
                        "similarity_score": r.similarity_score,
                        "rank_score": r.rank_score,
                        "reason": "Relevant chunk pushed down by MemoryRanker or low raw similarity."
                    })
                    
            # Check for total miss (if no results were relevant)
            if not any(relevance_map.values()):
                 false_negatives.append({
                     "rank": None,
                     "chunk_id": "MISSING",
                     "reason": "Embedding model completely failed to find the semantic match within the fetch limit."
                 })
                    
            analysis_report.append({
                "query": query,
                "false_positives": false_positives,
                "false_negatives": false_negatives
            })
            
        return {"failure_analysis": analysis_report}

    async def measure_semantic_drift(self) -> Dict:
        """
        Simulate drift by measuring MRR degradation as the result pool size increases.
        A healthy ranking system should maintain MRR even if limit increases.
        """
        drift_report = []
        limits_to_test = [5, 20, 50]
        
        for bq in BENCHMARK_QUERIES:
            query = bq["query"]
            truth = bq["ground_truth_keywords"]
            
            mrrs = {}
            for limit in limits_to_test:
                raw_chunks = await self.searcher.search_chunks(query=query, limit=limit)
                ranked = await self.ranker.rank(raw_chunks)
                
                rr = 0.0
                for i, r in enumerate(ranked):
                    if any(kw.lower() in r.content.lower() for kw in truth):
                        rr = 1.0 / (i + 1)
                        break
                mrrs[f"limit_{limit}"] = round(rr, 4)
                
            drift_report.append({
                "query": query,
                "mrr_by_fetch_limit": mrrs
            })
            
        return {"semantic_drift": drift_report}
