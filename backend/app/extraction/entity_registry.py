"""
Entity Registry — provides canonical normalization for technical entities.
Prevents Knowledge Graph fragmentation by mapping aliases (e.g., 'postgres', 'pg') to a single canonical term ('PostgreSQL').
"""
from typing import Dict, List

# Core registry mapping alias -> canonical
# In Phase 3, this should be moved to a PostgreSQL table for dynamic user-defined aliases.
CANONICAL_MAPPING = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "pg": "PostgreSQL",
    "pgvector": "pgvector",
    
    "gpt4": "GPT-4",
    "gpt-4": "GPT-4",
    "gpt-4o": "GPT-4o",
    "gpt4o": "GPT-4o",
    
    "react": "React",
    "reactjs": "React",
    
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    
    "fastapi": "FastAPI",
    
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
}

def resolve_alias(entity: str) -> str:
    """Returns the canonical version of an entity, or the original if not found."""
    return CANONICAL_MAPPING.get(entity.lower().strip(), entity.strip())

def resolve_aliases(entities: List[str]) -> List[str]:
    """Resolves a list of entities into their unique canonical forms."""
    resolved = set()
    for e in entities:
        canonical = resolve_alias(e)
        resolved.add(canonical)
    return list(resolved)
