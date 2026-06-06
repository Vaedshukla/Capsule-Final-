"""
Script to seed the synthetic dataset and run the evaluation benchmarks.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import async_session_maker
from app.evaluation.synthetic_dataset import SyntheticDatasetGenerator
from app.evaluation.retrieval_benchmark import RetrievalBenchmark
from app.evaluation.ranking_evaluator import RankingEvaluator
from app.evaluation.token_efficiency import TokenEfficiencyEvaluator
from app.evaluation.chunking_evaluator import ChunkingEvaluator
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.services.embeddings.embedding_service import EmbeddingService

async def main():
    print("Starting Phase 1B Validation Suite...\n")
    
    async with async_session_maker() as db:
        # 1. Seed Dataset
        print("1. Generating Synthetic Dataset...")
        generator = SyntheticDatasetGenerator(db)
        conversations = await generator.generate()
        print(f"   Generated {len(conversations)} synthetic conversations.")
        
        # 2. Embed Dataset
        print("2. Embedding and Chunking Dataset...")
        embed_service = EmbeddingService(db)
        total_chunks = 0
        for conv in conversations:
            chunks_generated = await embed_service.embed_conversation(conv.id)
            total_chunks += chunks_generated
        print(f"   Generated and embedded {total_chunks} chunks.\n")
        
        # 3. Run Benchmarks
        print("3. Running Retrieval Benchmark (Precision@K, MRR)...")
        benchmark = RetrievalBenchmark(db)
        bench_results = await benchmark.run_benchmark(k_values=[3, 5])
        print(f"   Avg Latency: {bench_results['avg_latency_ms']}ms")
        print(f"   MRR: {bench_results['mrr']}")
        print(f"   Precision@3: {bench_results['precision_at_k'][3]}")
        print(f"   Precision@5: {bench_results['precision_at_k'][5]}\n")
        
        # 4. Run Ranking Evaluator
        print("4. Running Ranking Evaluator...")
        ranking_eval = RankingEvaluator(db)
        ranking_results = await ranking_eval.compare_rankings()
        print(f"   Raw Cosine MRR: {ranking_results['avg_raw_mrr']}")
        print(f"   Ranked MRR: {ranking_results['avg_ranked_mrr']}")
        print(f"   MRR Improvement: {ranking_results['mrr_improvement']}\n")
        
        # 5. Run Token Efficiency
        print("5. Running Token Efficiency Analysis...")
        token_eval = TokenEfficiencyEvaluator(db)
        token_results = await token_eval.evaluate()
        print(f"   Avg Original Context Assumed: {token_results['avg_history_tokens_assumed']} tokens")
        print(f"   Avg Injected Context: {token_results['avg_injected_tokens']} tokens")
        print(f"   Compression Ratio: {token_results['avg_compression_ratio'] * 100:.2f}%\n")
        
        # 6. Run Chunking Evaluator
        print("6. Running Chunking Boundaries Evaluator...")
        chunking_eval = ChunkingEvaluator(db)
        chunking_results = await chunking_eval.evaluate_boundaries()
        print(f"   Total Messages: {chunking_results['total_messages']}")
        print(f"   Total Chunks: {chunking_results['total_chunks']}")
        print(f"   Avg Chunks/Message: {chunking_results['avg_chunks_per_msg']:.2f}")
        print(f"   Percent Within Bounds: {chunking_results['percent_chunks_within_target_bounds']:.2f}%\n")
        
        # 7. Run Failure Analysis
        print("7. Running Failure Analysis (False Positives/Negatives)...")
        failure_eval = FailureAnalyzer(db)
        failure_results = await failure_eval.analyze_failures()
        total_fps = sum(len(q["false_positives"]) for q in failure_results["failure_analysis"])
        total_fns = sum(len(q["false_negatives"]) for q in failure_results["failure_analysis"])
        print(f"   Total False Positives Detected: {total_fps}")
        print(f"   Total False Negatives Detected: {total_fns}\n")
        
        # 8. Measure Semantic Drift
        print("8. Measuring Semantic Drift...")
        drift_results = await failure_eval.measure_semantic_drift()
        for d in drift_results["semantic_drift"]:
            print(f"   Query: {d['query'][:30]}... -> MRRs: {d['mrr_by_fetch_limit']}")
        print("\n✅ Validation Suite Complete.")

if __name__ == "__main__":
    asyncio.run(main())
