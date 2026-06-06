# Project Capsule — Architecture Documentation

## System Overview

Project Capsule is an **AI Workflow Memory & Context Continuity Infrastructure**.
It captures AI conversations from multiple platforms, compresses them into semantic memory units (Capsules), and retrieves them intelligently — acting as an operating system for AI workflow continuity.

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│         Browser Extension (WXT/MV3)          │
│                                             │
│  ChatGPT │ Claude │ Gemini DOM Adapters     │
│  Content Script + Background Service Worker │
└───────────────────┬─────────────────────────┘
                    │ HTTP POST
                    ▼
┌─────────────────────────────────────────────┐
│         FastAPI Backend (Local Agent)        │
│                                             │
│  API Gateway (/api/v1/)                     │
│    ├── /ingest/conversation                 │
│    ├── /retrieval/search                    │
│    ├── /capsules/                           │
│    ├── /projects/                           │
│    └── /inject/context                      │
│                                             │
│  Service Layer                              │
│    ├── IngestionPipeline                    │
│    ├── EmbeddingService                     │
│    ├── CapsuleBuilder (Compression)         │
│    └── SemanticSearch (Retrieval)           │
│                                             │
│  Provider Abstraction                       │
│    ├── EmbeddingProvider (local/openai)     │
│    └── ConversationAdapter (per platform)   │
└───────────────────┬─────────────────────────┘
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
┌──────────────────┐  ┌───────────────┐
│ PostgreSQL +     │  │     Redis      │
│ pgvector         │  │ (caching,      │
│                  │  │  queuing)      │
│ - users          │  └───────────────┘
│ - projects
│ - sources
│ - conversations
│ - messages       │ ← vector embeddings
│ - memory_capsules│ ← vector embeddings
│ - entities
│ - relationships
│ - injections
└──────────────────┘
```

---

## Core Concept: Memory Capsule

A **Memory Capsule** is NOT a raw chat export. It is:

- A **compressed semantic memory unit** created from an AI conversation
- Contains: title, summary, key decisions, insights, extracted tasks
- Has a **vector embedding** for semantic similarity search
- Has an **importance score** for retrieval ranking
- Tracks **access count** for usage optimization

### Capsule Lifecycle

```
Raw Conversation
    ↓  (extension captures)
Conversation + Messages stored in DB (status: "raw")
    ↓  (embedding service)
Message vectors generated (status: "embedded")
    ↓  (compression engine)
MemoryCapsule created with summary + decisions (status: "compressed")
    ↓  (retrieval)
Injected into new AI conversations via /inject/context
```

---

## Platform Adapter Pattern

Each AI platform has an isolated adapter to handle DOM extraction (in extension) and payload normalization (in backend):

```
Platform Slug → ConversationAdapter.normalize() → NormalizedConversation
```

Adapters are isolated to prevent platform-specific fragility from leaking into core logic.

---

## Embedding Provider Abstraction

```
EMBEDDING_PROVIDER=local   → LocalEmbeddingProvider (sentence-transformers, offline)
EMBEDDING_PROVIDER=openai  → OpenAIEmbeddingProvider (text-embedding-3-small)
```

Switch providers via environment variable — no code changes.

---

## Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 — Foundation | Architecture, ingestion, compression, retrieval | 🟢 In Progress |
| 2 — Memory Intelligence | LLM-powered compression, knowledge graph | ⚪ Planned |
| 3 — Cross-Platform | Cursor, IDE integrations, Git history | ⚪ Planned |
| 4 — Alpha Integration | Monitoring, policy, behavioral intelligence | ⚪ Planned |
