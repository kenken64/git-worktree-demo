#!/usr/bin/env python3
"""Cache management utility for the prompt compressor.

Usage:
  python cache_manager.py stats        # Show cache statistics
  python cache_manager.py cleanup      # Remove entries older than 30 days
  python cache_manager.py clear        # Clear all cache entries
  python cache_manager.py export       # Export cache to JSON
"""

import sys
import json
from pathlib import Path
from cache import get_cache


def show_stats():
    """Display detailed cache statistics."""
    cache = get_cache()
    stats = cache.get_cache_stats()
    
    if not stats or stats.get('total_entries', 0) == 0:
        print("Cache is empty.")
        return
    
    print("=== Compression Cache Statistics ===")
    print(f"Total entries: {stats['total_entries']:,}")
    print(f"Original text size: {stats['total_original_chars']:,} characters")
    print(f"Compressed text size: {stats['total_compressed_chars']:,} characters")
    print(f"Average reduction ratio: {stats['avg_reduction_ratio']:.1%}")
    print(f"Cache database size: {stats['cache_size_mb']:.1f} MB")
    print(f"Oldest entry: {stats['oldest_entry']}")
    print(f"Last accessed: {stats['last_accessed']}")
    
    # Calculate compression savings
    if stats['total_original_chars'] > 0:
        total_reduction = 1 - (stats['total_compressed_chars'] / stats['total_original_chars'])
        print(f"Total characters saved: {stats['total_original_chars'] - stats['total_compressed_chars']:,}")
        print(f"Overall compression: {total_reduction:.1%}")


def cleanup_old():
    """Remove cache entries older than 30 days."""
    cache = get_cache()
    removed = cache.cleanup_old_entries(days_old=30)
    print(f"Removed {removed} cache entries older than 30 days.")
    
    if removed > 0:
        print("Updated cache statistics:")
        show_stats()


def clear_cache():
    """Clear all cache entries after confirmation."""
    cache = get_cache()
    stats = cache.get_cache_stats()
    
    if not stats or stats.get('total_entries', 0) == 0:
        print("Cache is already empty.")
        return
    
    print(f"This will delete all {stats['total_entries']} cache entries.")
    confirm = input("Are you sure? (y/N): ").strip().lower()
    
    if confirm == 'y':
        cache.clear_cache()
        print("Cache cleared successfully.")
    else:
        print("Cache clear cancelled.")


def export_cache():
    """Export cache to JSON file."""
    cache = get_cache()
    stats = cache.get_cache_stats()
    
    if not stats or stats.get('total_entries', 0) == 0:
        print("Cache is empty, nothing to export.")
        return
    
    export_path = "cache_export.json"
    cache.export_cache(export_path)
    
    file_size = Path(export_path).stat().st_size / 1024 / 1024
    print(f"Exported {stats['total_entries']} cache entries to {export_path}")
    print(f"Export file size: {file_size:.1f} MB")


def show_usage():
    """Display usage information."""
    print(__doc__.strip())


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "stats":
            show_stats()
        elif command == "cleanup":
            cleanup_old()
        elif command == "clear":
            clear_cache()
        elif command == "export":
            export_cache()
        else:
            print(f"Unknown command: {command}")
            show_usage()
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
