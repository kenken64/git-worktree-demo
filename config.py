"""Performance and model configuration for prompt compressor."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CompressorConfig:
    """Configuration settings for optimal performance."""
    
    # Model settings
    rating_model: str = "gpt-4o-mini"          # Faster, cheaper for rating
    compression_model: str = "gpt-4o-mini"     # Default compression model
    fallback_model: str = "gpt-4o"             # Higher quality fallback
    
    # Performance settings
    rating_concurrency: int = 20               # Concurrent rating requests
    compression_batch_size: int = 5            # Chunks compressed in parallel
    max_compression_attempts: int = 3          # Per-chunk retry limit
    
    # Quality thresholds
    compression_threshold: float = 0.7         # Skip if already 70% compressed
    min_chunk_tokens: int = 1                  # Minimum tokens to attempt compression
    
    # Timeout settings
    request_timeout: int = 30                  # API request timeout
    max_iterations: int = 32                   # Maximum compression iterations


# Preset configurations for different use cases
FAST_CONFIG = CompressorConfig(
    rating_model="gpt-4o-mini",
    compression_model="gpt-4o-mini",
    rating_concurrency=30,
    compression_batch_size=8,
    max_compression_attempts=2,
)

BALANCED_CONFIG = CompressorConfig(
    rating_model="gpt-4o-mini",
    compression_model="gpt-4o",
    rating_concurrency=20,
    compression_batch_size=5,
    max_compression_attempts=3,
)

QUALITY_CONFIG = CompressorConfig(
    rating_model="gpt-4o",
    compression_model="gpt-4o",
    rating_concurrency=10,
    compression_batch_size=3,
    max_compression_attempts=4,
)

# Default configuration
DEFAULT_CONFIG = BALANCED_CONFIG


def get_config(preset: Optional[str] = None) -> CompressorConfig:
    """Get configuration by preset name or default."""
    presets = {
        "fast": FAST_CONFIG,
        "balanced": BALANCED_CONFIG,
        "quality": QUALITY_CONFIG,
    }
    return presets.get(preset, DEFAULT_CONFIG)
