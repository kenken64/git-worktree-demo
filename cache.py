"""SQLite caching system for prompt compression results.

Caches compressed results by content hash to avoid reprocessing identical content.
"""
from __future__ import annotations

import sqlite3
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import asdict


class CompressionCache:
    """SQLite-based cache for compression results."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """Initialize cache with database in cache_dir."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "compression_cache.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compression_cache (
                    content_hash TEXT PRIMARY KEY,
                    original_text TEXT NOT NULL,
                    compressed_text TEXT NOT NULL,
                    chunks_data TEXT NOT NULL,  -- JSON serialized chunks
                    original_tokens INTEGER NOT NULL,
                    final_tokens INTEGER NOT NULL,
                    reduction_ratio REAL NOT NULL,
                    intent TEXT,
                    model_config TEXT,  -- JSON serialized config
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash 
                ON compression_cache(content_hash)
            """)
            
            # Index for cleanup queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at 
                ON compression_cache(accessed_at)
            """)
    
    def _hash_content(self, text: str, intent: Optional[str] = None, 
                     reduction_ratio: float = 0.3) -> str:
        """Generate hash for content, intent, and compression parameters."""
        content_data = {
            "text": text.strip(),
            "intent": intent or "",
            "reduction_ratio": reduction_ratio
        }
        content_str = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def get_cached_result(self, text: str, intent: Optional[str] = None, 
                         reduction_ratio: float = 0.3) -> Optional[Dict]:
        """Get cached compression result if it exists."""
        content_hash = self._hash_content(text, intent, reduction_ratio)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM compression_cache 
                WHERE content_hash = ?
            """, (content_hash,))
            
            row = cursor.fetchone()
            if row:
                # Update accessed_at timestamp
                conn.execute("""
                    UPDATE compression_cache 
                    SET accessed_at = CURRENT_TIMESTAMP 
                    WHERE content_hash = ?
                """, (content_hash,))
                
                # Deserialize chunks data
                chunks_data = json.loads(row["chunks_data"])
                
                return {
                    "content_hash": row["content_hash"],
                    "original_text": row["original_text"],
                    "compressed_text": row["compressed_text"],
                    "chunks": chunks_data,
                    "original_tokens": row["original_tokens"],
                    "final_tokens": row["final_tokens"],
                    "reduction_ratio": row["reduction_ratio"],
                    "intent": row["intent"],
                    "model_config": json.loads(row["model_config"]) if row["model_config"] else None,
                    "created_at": row["created_at"],
                    "accessed_at": row["accessed_at"]
                }
        
        return None
    
    def cache_result(self, text: str, compressed_text: str, chunks: List[Dict],
                    original_tokens: int, final_tokens: int,
                    intent: Optional[str] = None, reduction_ratio: float = 0.3,
                    model_config: Optional[Dict] = None) -> str:
        """Cache compression result and return content hash."""
        content_hash = self._hash_content(text, intent, reduction_ratio)
        
        # Clean chunks data for serialization (remove internal metadata)
        clean_chunks = []
        for chunk in chunks:
            clean_chunk = {k: v for k, v in chunk.items() 
                          if not k.startswith('_')}
            clean_chunks.append(clean_chunk)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO compression_cache 
                (content_hash, original_text, compressed_text, chunks_data,
                 original_tokens, final_tokens, reduction_ratio, intent, model_config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content_hash,
                text,
                compressed_text,
                json.dumps(clean_chunks),
                original_tokens,
                final_tokens,
                reduction_ratio,
                intent,
                json.dumps(model_config) if model_config else None
            ))
        
        return content_hash
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(LENGTH(original_text)) as total_original_chars,
                    SUM(LENGTH(compressed_text)) as total_compressed_chars,
                    AVG(reduction_ratio) as avg_reduction_ratio,
                    MIN(created_at) as oldest_entry,
                    MAX(accessed_at) as last_accessed
                FROM compression_cache
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    "total_entries": row[0],
                    "total_original_chars": row[1] or 0,
                    "total_compressed_chars": row[2] or 0,
                    "avg_reduction_ratio": row[3] or 0.0,
                    "oldest_entry": row[4],
                    "last_accessed": row[5],
                    "cache_size_mb": os.path.getsize(self.db_path) / (1024 * 1024)
                }
        
        return {}
    
    def cleanup_old_entries(self, days_old: int = 30) -> int:
        """Remove entries older than specified days. Returns count of removed entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM compression_cache 
                WHERE accessed_at < datetime('now', '-{} days')
            """.format(days_old))
            
            return cursor.rowcount
    
    def clear_cache(self):
        """Clear all cache entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM compression_cache")
    
    def export_cache(self, export_path: str):
        """Export cache to JSON file."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM compression_cache")
            
            entries = []
            for row in cursor:
                entry = dict(row)
                entry["chunks_data"] = json.loads(entry["chunks_data"])
                if entry["model_config"]:
                    entry["model_config"] = json.loads(entry["model_config"])
                entries.append(entry)
            
            with open(export_path, 'w') as f:
                json.dump(entries, f, indent=2)


# Global cache instance
_cache_instance: Optional[CompressionCache] = None


def get_cache() -> CompressionCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CompressionCache()
    return _cache_instance


def cached_compress(text: str, compress_func, intent: Optional[str] = None,
                   reduction_ratio: float = 0.3, model_config: Optional[Dict] = None) -> Tuple[str, List[Dict], Dict]:
    """
    Wrapper function that checks cache before compression.
    
    Args:
        text: Original text to compress
        compress_func: Function that performs compression (should return compressed_text, chunks, stats)
        intent: Author intent for compression
        reduction_ratio: Target reduction ratio
        model_config: Model configuration used
    
    Returns:
        Tuple of (compressed_text, chunks, stats)
    """
    cache = get_cache()
    
    # Check cache first
    cached_result = cache.get_cached_result(text, intent, reduction_ratio)
    if cached_result:
        print(f"[cache] Found cached result for content hash: {cached_result['content_hash'][:10]}...")
        stats = {
            "original_tokens": cached_result["original_tokens"],
            "final_tokens": cached_result["final_tokens"],
            "reduction_ratio": cached_result["reduction_ratio"],
            "cache_hit": True,
            "created_at": cached_result["created_at"]
        }
        return cached_result["compressed_text"], cached_result["chunks"], stats
    
    # Not in cache, perform compression
    print("[cache] No cached result found, performing compression...")
    compressed_text, chunks, stats = compress_func()
    
    # Cache the result
    content_hash = cache.cache_result(
        text=text,
        compressed_text=compressed_text,
        chunks=chunks,
        original_tokens=stats.get("original_tokens", 0),
        final_tokens=stats.get("final_tokens", 0),
        intent=intent,
        reduction_ratio=reduction_ratio,
        model_config=model_config
    )
    
    print(f"[cache] Cached result with hash: {content_hash[:10]}...")
    stats["cache_hit"] = False
    
    return compressed_text, chunks, stats


__all__ = ["CompressionCache", "get_cache", "cached_compress"]
