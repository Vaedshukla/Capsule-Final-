import requests
import time

base_url = "http://127.0.0.1:8000/api/v1"

# 1. Project
proj_res = requests.post(f"{base_url}/projects/", json={
    "name": "E2E Final Test",
    "description": "Validation of the ingestion and compression pipelines."
})
proj_id = proj_res.json()["id"]
print(f"Project Created: {proj_id}")

# 2. Ingest Conversation
payload = {
  "source": "chatgpt",
  "project_hint": "E2E Final Test",
  "url": "https://chatgpt.com/e2e",
  "title": "Authentication Architecture",
  "messages": [
    {
      "role": "user",
      "content": "Should we use JWT or session cookies?",
      "position": 1
    },
    {
      "role": "assistant",
      "content": "We will use JWT because we need a stateless architecture.",
      "position": 2
    }
  ]
}

ingest_res = requests.post(f"{base_url}/ingest/conversation?project_id={proj_id}", json=payload)
conv_id = ingest_res.json()["conversation_id"]
print(f"Conversation Ingested: {conv_id}")

# Wait for embeddings and capsule creation (handled in background)
time.sleep(10)

# 3. Search
search_res = requests.get(f"{base_url}/retrieval/search?query=Why did we choose JWT?&project_id={proj_id}")
results = search_res.json().get("results", [])
print(f"Search Results: {len(results)}")
for r in results:
    print(f"- {r['type']}: {r['content'][:50]} (Sim: {r['similarity_score']})")
