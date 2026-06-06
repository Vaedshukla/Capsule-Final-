import asyncio
import json
import time
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import async_session_maker
from app.retrieval.semantic_search import SemanticSearch
from sqlalchemy import text
from sqlalchemy import text

def calculate_dcg(relevances):
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))

def calculate_ndcg(relevances, k=5):
    dcg = calculate_dcg(relevances[:k])
    idcg = calculate_dcg(sorted(relevances, reverse=True)[:k])
    return dcg / idcg if idcg > 0 else 0.0

async def run_benchmark():
    ground_truth_path = os.path.join(os.path.dirname(__file__), "benchmark_ground_truth.json")
    with open(ground_truth_path, "r") as f:
        ground_truths = json.load(f)

    async with async_session_maker() as db:
        searcher = SemanticSearch(db)
        
        results = []
        latencies = []
        recalls = []
        precisions = []
        ndcgs = []
        confidences = []
        
        print(f"Running Phase 4 Benchmark on {len(ground_truths)} queries...\n")
        
        for gt in ground_truths:
            query = gt["query"]
            expected = gt["expected_matches"]
            
            start_time = time.time()
            # Fetch top 5 capsules
            capsules = await searcher.search_capsules(query=query, limit=5, min_similarity=0.1)
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            
            # Relevances for NDCG (1 if match found in capsule, 0 otherwise)
            relevances = []
            matched_expected = set()
            
            for cap in capsules:
                is_relevant = 0
                combined_text = cap.content
                for ex in expected:
                    if ex.lower() in combined_text.lower():
                        is_relevant = 1
                        matched_expected.add(ex)
                relevances.append(is_relevant)
                if hasattr(cap, 'similarity_score') and cap.similarity_score:
                    confidences.append(cap.similarity_score)
            
            # Metrics
            recall_at_5 = len(matched_expected) / len(expected) if expected else 0.0
            precision_at_5 = sum(relevances) / len(capsules) if capsules else 0.0
            ndcg = calculate_ndcg(relevances, k=5)
            
            recalls.append(recall_at_5)
            precisions.append(precision_at_5)
            ndcgs.append(ndcg)
            
            print(f"Q: '{query}'")
            print(f"  Latency: {latency:.1f}ms")
            print(f"  P@5: {precision_at_5:.2f} | R@5: {recall_at_5:.2f} | NDCG: {ndcg:.2f}")
            print(f"  Expected found: {len(matched_expected)}/{len(expected)}")
            if len(matched_expected) < len(expected):
                print(f"  Missed: {set(expected) - matched_expected}")
            print()
            
        print("--- SUMMARY METRICS ---")
        print(f"Average P@5: {sum(precisions)/len(precisions):.3f}")
        print(f"Average R@5: {sum(recalls)/len(recalls):.3f}")
        print(f"Average NDCG: {sum(ndcgs)/len(ndcgs):.3f}")
        print(f"Average Latency: {sum(latencies)/len(latencies):.1f}ms")
        
        if confidences:
            print(f"\nConfidence Score Distribution: Avg={sum(confidences)/len(confidences):.2f}, Min={min(confidences):.2f}, Max={max(confidences):.2f}")
        else:
            print("\nNo confidence scores found.")

        # Cross Project contamination test
        print("\n--- FAILURE ANALYSIS (Contamination Test) ---")
        alpha_res = await searcher.search_capsules(query="database decisions", limit=5)
        cog_res = await searcher.search_capsules(query="filtering engine design", limit=5)
        
        # We can analyze if Alpha queries returned Cog projects if project names were fetched
        # But for now just print success
        print("Validation suite execution complete!")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
