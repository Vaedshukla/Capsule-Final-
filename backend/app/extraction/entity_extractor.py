"""
Hybrid Entity Extractor
Uses deterministic regex and dictionaries to extract technical nouns (e.g. frameworks, databases).
"""
import re
from typing import List
from app.extraction.entity_registry import resolve_aliases

# Common tech stack dictionary (can be expanded later via DB or config)
TECH_DICTIONARY = {
    "postgresql", "postgres", "redis", "fastapi", "react", "next.js", 
    "node.js", "docker", "kubernetes", "aws", "gcp", "azure", "jwt",
    "oauth", "tailwind", "typescript", "javascript", "python", "go",
    "rust", "graphql", "rest", "pgvector", "sqlalchemy"
}

class EntityExtractor:
    @staticmethod
    def extract_deterministic_entities(text: str) -> List[str]:
        """
        Extract entities based on known dictionaries and regex patterns.
        """
        found_entities = set()
        text_lower = text.lower()
        
        # 1. Dictionary Lookup
        for tech in TECH_DICTIONARY:
            # Word boundary regex to ensure exact match
            pattern = r'\b' + re.escape(tech) + r'\b'
            if re.search(pattern, text_lower):
                found_entities.add(tech)
                
        # 2. File Path extraction (lightweight regex)
        # e.g., src/components/Button.tsx or backend/app/models.py
        file_paths = re.findall(r'\b[\w\.\-]+/[\w\.\-/]+\.[a-zA-Z0-9]+\b', text)
        for path in file_paths:
            found_entities.add(path)
            
        return list(found_entities)
        
    @staticmethod
    def merge_entities(deterministic: List[str], probabilistic: List[str]) -> List[str]:
        """
        Merge LLM-extracted entities with deterministic ones.
        Prefer deterministic case/formatting.
        """
        merged = set(deterministic)
        det_lower = {e.lower() for e in deterministic}
        
        for p in probabilistic:
            if p.lower() not in det_lower:
                merged.add(p)
                
        # Resolve to canonical forms
        canonical_entities = resolve_aliases(list(merged))
        return canonical_entities
