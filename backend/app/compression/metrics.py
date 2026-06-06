from dataclasses import dataclass

@dataclass
class CompressionMetrics:
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    decision_count: int
    insight_count: int
    quality_score: float
