"""
Retrieval Benchmark — calculates Precision@K and MRR for a set of benchmark queries.
"""
import time
import structlog
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker

logger = structlog.get_logger()

# Queries and ground truth matching words/phrases we expect to find in the top K
BENCHMARK_QUERIES = [
    {
        "query": "How are we doing auth sessions?",
        "ground_truth_keywords": ["opaque session tokens stored in Redis", "session:{user_id}"],
    },
    {
        "query": "What is the caching strategy for the dashboard?",
        "ground_truth_keywords": ["TTL of 15 minutes", "cache:analytics"],
    },
    {
        "query": "Frontend state management decision",
        "ground_truth_keywords": ["Zustand will prevent unnecessary re-renders", "React Context"],
    },
    {
        "query": "Fixing the docker build timeout",
        "ground_truth_keywords": ["Docker layer caching", "actions/cache"],
    }
]

class RetrievalBenchmark:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.searcher = SemanticSearch(db)
        self.ranker = MemoryRanker(db)

    async def run_benchmark(self, k_values: List[int] = [3, 5]) -> Dict:
        """Run the benchmark suite and return metrics."""
        results = {
            "mrr": 0.0,
            "precision_at_k": {k: 0.0 for k in k_values},
            "avg_latency_ms": 0.0,
            "queries": []
        }
        
        total_latency = 0.0
        mrr_sum = 0.0
        precision_sums = {k: 0.0 for k in k_values}
        
        for bq in BENCHMARK_QUERIES:
            query = bq["query"]
            truth = bq["ground_truth_keywords"]
            
            start_time = time.time()
            
            # Fetch and rank chunks
            raw_chunks = await self.searcher.search_chunks(query=query, limit=max(k_values))
            ranked_results = await self.ranker.rank(raw_chunks)
            
            latency = (time.time() - start_time) * 1000
            total_latency += latency
            
            # Evaluate relevance of each result
            relevance = []
            for r in ranked_results:
                is_relevant = any(kw.lower() in r.content.lower() for kw in truth)
                relevance.append(is_relevant)
                
            # Calculate MRR
            reciprocal_rank = 0.0
            for i, is_rel in enumerate(relevance):
                if is_rel:
                    reciprocal_rank = 1.0 / (i + 1)
                    break
            mrr_sum += reciprocal_rank
            
            # Calculate P@K
            p_at_k = {}
            for k in k_values:
                k_subset = relevance[:k]
                p_at_k[k] = sum(k_subset) / k if k > 0 else 0.0
                precision_sums[k] += p_at_k[k]
                
            results["queries"].append({
                "query": query,
                "latency_ms": round(latency, 2),
                "mrr": round(reciprocal_rank, 4),
                "p_at_k": {k: round(v, 4) for k, v in p_at_k.items()}
            })
            
        num_queries = len(BENCHMARK_QUERIES)
        if num_queries > 0:
            results["mrr"] = round(mrr_sum / num_queries, 4)
            results["avg_latency_ms"] = round(total_latency / num_queries, 2)
            for k in k_values:
                results["precision_at_k"][k] = round(precision_sums[k] / num_queries, 4)
                
        logger.info("benchmark_complete", metrics=results)
        return results
