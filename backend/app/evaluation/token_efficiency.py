"""
Token Economy Analysis — measures the token waste reduction of Capsule.
"""
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker
from app.retrieval.context_assembler import ContextAssembler
from app.evaluation.retrieval_benchmark import BENCHMARK_QUERIES

class TokenEfficiencyEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.searcher = SemanticSearch(db)
        self.ranker = MemoryRanker(db)
        self.assembler = ContextAssembler(db)

    async def evaluate(self) -> Dict:
        """
        Evaluate token efficiency of context assembly across benchmarks.
        """
        # Note: In a real scenario, "raw conversation tokens" would be the sum of 
        # all messages in the project/conversation. 
        # For this test, we'll assume a fixed average history size (e.g., 5000 tokens)
        # to demonstrate the compression ratio.
        
        avg_history_tokens = 5000.0
        
        total_injected = 0
        total_savings = 0
        
        reports = []
        
        for bq in BENCHMARK_QUERIES:
            query = bq["query"]
            
            # Fetch, rank, assemble
            raw_results = await self.searcher.search_chunks(query=query, limit=10)
            ranked = await self.ranker.rank(raw_results)
            formatted, tokens = await self.assembler.assemble(ranked, query)
            
            savings = avg_history_tokens - tokens
            ratio = savings / avg_history_tokens if avg_history_tokens > 0 else 0
            
            total_injected += tokens
            total_savings += savings
            
            reports.append({
                "query": query,
                "injected_tokens": tokens,
                "saved_tokens": int(savings),
                "compression_ratio": round(ratio, 4)
            })
            
        num = len(BENCHMARK_QUERIES)
        avg_injected = total_injected / num if num > 0 else 0
        avg_ratio = (avg_history_tokens - avg_injected) / avg_history_tokens if num > 0 else 0
        
        return {
            "avg_history_tokens_assumed": int(avg_history_tokens),
            "avg_injected_tokens": int(avg_injected),
            "avg_compression_ratio": round(avg_ratio, 4),
            "details": reports
        }
