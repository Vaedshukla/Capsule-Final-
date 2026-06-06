import requests
import time

base_url = "http://127.0.0.1:8000/api/v1"

def run_accuracy_test():
    print("Running Capsule Accuracy Test...")

    # 1. Create a dedicated project for accuracy testing
    proj_res = requests.post(f"{base_url}/projects/", json={
        "name": "Accuracy Test Project",
        "description": "Project for automated accuracy evaluation."
    })
    
    if proj_res.status_code not in [200, 201]:
        print(f"Failed to create project: {proj_res.text}")
        return
        
    proj_id = proj_res.json()["id"]
    print(f"Project Created: {proj_id}")

    # 2. Ingest a high-density test conversation
    payload = {
        "source": "chatgpt",
        "project_hint": "Accuracy Test",
        "url": "https://chatgpt.com/accuracy",
        "title": "Caching Architecture Decision",
        "messages": [
            {
                "role": "user",
                "content": "We need to decide on a caching layer. Should we use Redis or Memcached? We need data persistence and complex data types.",
                "position": 1
            },
            {
                "role": "assistant",
                "content": "Given your requirement for data persistence and complex data types (like Hashes and Sets), Redis is the better choice. Memcached is strictly an in-memory key-value store without persistence.",
                "position": 2
            },
            {
                "role": "user",
                "content": "Okay, let's go with Redis then. What about the frontend framework?",
                "position": 3
            },
            {
                "role": "assistant",
                "content": "Since your team knows React and you need Server Side Rendering for SEO, Next.js is the standard recommendation.",
                "position": 4
            },
            {
                "role": "user",
                "content": "Let's stick to Vanilla React (Vite) for now to keep things simple. We don't actually need SEO.",
                "position": 5
            }
        ]
    }

    ingest_res = requests.post(f"{base_url}/ingest/conversation?project_id={proj_id}", json=payload)
    if ingest_res.status_code not in [200, 201]:
        print(f"Failed to ingest: {ingest_res.text}")
        return
        
    conv_id = ingest_res.json()["conversation_id"]
    print(f"Conversation Ingested: {conv_id}")

    print("Waiting for embeddings and compression to complete (15s)...")
    time.sleep(15)

    # 3. Test Retrieval Accuracy
    print("\n--- Testing Retrieval Accuracy ---")
    queries = [
        ("What caching layer did we choose?", "Redis"),
        ("What frontend framework are we using?", "Vanilla React"),
        ("Why didn't we use Memcached?", "persistence"),
        ("Why didn't we use Next.js?", "SEO")
    ]
    
    total_queries = len(queries)
    passed_queries = 0

    for query, expected_keyword in queries:
        search_res = requests.get(f"{base_url}/retrieval/search?query={query}&project_id={proj_id}")
        if search_res.status_code != 200:
            print(f"[FAIL] Failed retrieval for '{query}'")
            continue
            
        results = search_res.json().get("results", [])
        if not results:
            print(f"[FAIL] Empty results for '{query}'")
            continue
            
        # Check if the expected keyword is in the top result
        top_result = results[0]["content"]
        if expected_keyword.lower() in top_result.lower():
            print(f"[PASS] '{query}' -> Retrieved: {top_result[:60]}...")
            passed_queries += 1
        else:
            print(f"[FAIL] '{query}' -> Expected '{expected_keyword}', but got: {top_result[:60]}...")
            
    print(f"\nAccuracy Score: {passed_queries}/{total_queries} ({(passed_queries/total_queries)*100}%)")

if __name__ == "__main__":
    run_accuracy_test()
