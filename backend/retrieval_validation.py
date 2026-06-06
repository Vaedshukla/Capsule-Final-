import requests
import time
import json
import statistics

base_url = "http://127.0.0.1:8000/api/v1"

def fetch_projects():
    res = requests.get(f"{base_url}/projects/")
    res.raise_for_status()
    return res.json()

def run_retrieval_validation():
    print("Starting Retrieval Quality Validation...")
    projects = fetch_projects()
    if not projects:
        print("No projects found.")
        return

    # Select the first project or default to None
    test_project = projects[0]
    p_id = test_project["id"]

    queries = [
        "Why did we choose PostgreSQL?",
        "What authentication strategy are we using?",
        "How are we handling vector embeddings?",
        "What is the deployment strategy?",
        "What UI framework did we select?",
        "Are we using JWT or session cookies?",
        "How do we handle idempotency?",
        "What alternatives were rejected for the database?",
        "How is MCP integrated?",
        "What is the backend architecture?",
        "Which LLM model is used for embeddings?",
        "What was the timeline for Phase 1?",
        "How do we extract the DOM on ChatGPT?",
        "What is the CapsuleBuilder doing?",
        "Why did we reject MongoDB?",
        "How are duplicate ingestions handled?",
        "What is the fallback if embeddings fail?",
        "Are we using Docker?",
        "What is the data retention policy?",
        "How do we filter by project in retrieval?",
        "What was the biggest security risk identified?",
        "How do we parse JSON strings in Pydantic?",
        "What is the role of SemanticSearch?",
        "Why did we choose React for the extension?",
        "What was the final decision on observability?"
    ]

    latencies = []
    failures = 0
    empty_results = 0

    print(f"\nRunning {len(queries)} queries against Project: {test_project['name']} ({p_id})...")
    
    for q in queries:
        start_time = time.time()
        try:
            res = requests.get(f"{base_url}/retrieval/search?query={q}&project_id={p_id}")
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            
            if res.status_code != 200:
                failures += 1
                print(f"[FAIL] ({res.status_code}): {q}")
                continue
                
            data = res.json()
            results = data.get("results", [])
            
            if len(results) == 0:
                empty_results += 1
                
        except Exception as e:
            failures += 1
            print(f"[ERROR] Exception on query '{q}': {e}")

    # Cross-project contamination test
    print("\nRunning Cross-Project Contamination Test...")
    cross_failures = 0
    dummy_uuid = "00000000-0000-0000-0000-000000000000"
    try:
        res = requests.get(f"{base_url}/retrieval/search?query=PostgreSQL&project_id={dummy_uuid}")
        if res.status_code == 200:
            if len(res.json().get("results", [])) > 0:
                print("[WARN] Data leaked to dummy project!")
                cross_failures += 1
            else:
                print("[PASS] Cross-project isolation verified (0 results for dummy project).")
    except Exception as e:
        print(f"[ERROR] Exception on cross-project test: {e}")
        cross_failures += 1

    print("\n" + "="*40)
    print("RETRIEVAL VALIDATION SUMMARY")
    print("="*40)
    print(f"Total Queries: {len(queries)}")
    print(f"Failures: {failures}")
    print(f"Empty Results: {empty_results} (Expected if DB lacks data for query)")
    print(f"Cross-Project Leaks: {cross_failures}")
    print(f"Avg Latency: {statistics.mean(latencies):.2f} ms" if latencies else "Avg Latency: N/A")
    print(f"Max Latency: {max(latencies):.2f} ms" if latencies else "Max Latency: N/A")
    print(f"Min Latency: {min(latencies):.2f} ms" if latencies else "Min Latency: N/A")
    print("="*40)

if __name__ == "__main__":
    run_retrieval_validation()
