"""
Extraction Evaluator
Measures the hallucination rate and correctness of the LLM extraction.
Compares deterministic entity extraction against LLM extraction.
"""
from typing import List, Dict

class ExtractionEvaluator:
    @staticmethod
    def measure_hallucination_rate(deterministic_entities: List[str], llm_entities: List[str]) -> Dict[str, float]:
        """
        Returns a hallucination risk score.
        If the LLM generates many technical nouns that the deterministic regex missed,
        there's a high probability of hallucination or over-inference.
        """
        det_lower = {e.lower() for e in deterministic_entities}
        llm_lower = {e.lower() for e in llm_entities}
        
        if not llm_lower:
            return {"hallucination_rate": 0.0, "hallucinated_entities": []}
            
        hallucinations = llm_lower - det_lower
        rate = len(hallucinations) / len(llm_lower)
        
        return {
            "hallucination_rate": rate,
            "hallucinated_entities": list(hallucinations)
        }
    
    @staticmethod
    def evaluate_constraint_preservation(source_text: str, extracted_constraints: List[str]) -> float:
        """
        Checks if extracted constraints actually exist in the source text.
        (Simplified semantic check using keyword matching for validation).
        """
        if not extracted_constraints:
            return 1.0  # No constraints to hallucinate
            
        source_lower = source_text.lower()
        preserved = 0
        
        for constraint in extracted_constraints:
            # Check if key nouns from the constraint exist in the source
            words = constraint.lower().split()
            important_words = [w for w in words if len(w) > 4]
            
            if any(w in source_lower for w in important_words):
                preserved += 1
                
        return preserved / len(extracted_constraints)
