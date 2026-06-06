"""
Confidence Calibrator
Analyzes the distribution of composite confidence scores across capsules.
Ensures we don't suffer from extreme overconfidence or underconfidence.
"""
from typing import List, Dict
import math

class ConfidenceCalibrator:
    @staticmethod
    def calculate_distribution(scores: List[float]) -> Dict[str, float]:
        """
        Calculates mean, variance, and distribution buckets for confidence scores.
        """
        if not scores:
            return {}
            
        n = len(scores)
        mean = sum(scores) / n
        variance = sum((x - mean) ** 2 for x in scores) / n
        std_dev = math.sqrt(variance)
        
        buckets = {
            "0.0-0.2": sum(1 for s in scores if 0.0 <= s < 0.2) / n,
            "0.2-0.4": sum(1 for s in scores if 0.2 <= s < 0.4) / n,
            "0.4-0.6": sum(1 for s in scores if 0.4 <= s < 0.6) / n,
            "0.6-0.8": sum(1 for s in scores if 0.6 <= s < 0.8) / n,
            "0.8-1.0": sum(1 for s in scores if 0.8 <= s <= 1.0) / n,
        }
        
        is_calibrated = (buckets["0.8-1.0"] < 0.90) and (buckets["0.0-0.2"] < 0.50)
        
        return {
            "mean": round(mean, 3),
            "std_dev": round(std_dev, 3),
            "buckets": buckets,
            "is_calibrated": is_calibrated
        }
