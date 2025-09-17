"""End-to-end prompt compressor pipeline with SQLite caching (Steps 1-6).

Optimized integration with caching:
- Step 0: check cache by content hash
- Step 1: chunk (compressor.split)
- Step 2: rate (rater.rate_chunks)
- Step 3: plan (compressor.plan)
- Step 4: compress loop (step4.compress_to_target)
- Step 5: recount (compressor.recount)
- Step 6: stitch + stats + cache result

Usage: python main.py [input_path] [--preset fast|balanced|quality]
"""
from __future__ import annotations

import sys, pathlib, json, time
from compressor import split, plan, recount
from rater import rate_chunks
from step4 import compress_to_target
from cache import cached_compress, get_cache
from config import get_config


def _assemble(chunks):
    # Keep original order using character positions
    return "".join(c["text"] for c in sorted(chunks, key=lambda c: c.get("start", 0)))


def main(argv):
    start_time = time.time()
    
    # Parse arguments
    inp = pathlib.Path(argv[1]) if len(argv) > 1 else pathlib.Path("original-prompt.md")
    preset = None
    if len(argv) > 2 and argv[2] == "--preset" and len(argv) > 3:
        preset = argv[3]
    
    config = get_config(preset)
    print(f"[main] using {preset or 'default'} preset: {config.compression_model}")
    
    text = inp.read_text(encoding="utf-8")

    # Ask operator for intent and reduction target upfront
    intent = input("Author intent/focus (one line): ").strip() or None
    rraw = input("Desired reduction (e.g., 0.30 or 30%): ").strip() or "0.30"
    if rraw.endswith('%'):
        reduce_by = float(rraw[:-1]) / 100.0
    else:
        val = float(rraw)
        reduce_by = val / 100.0 if val > 1 else val  # treat 25 as 25%, 0.25 as 25%

    def perform_compression():
        """Actual compression logic wrapped for caching."""
        # 1) Chunk
        chunks = split(text)

        # 2) Rate (uses intent in the system prompt)
        rate_chunks(chunks, model=config.rating_model, 
                   concurrency=config.rating_concurrency, intent=intent)

        # 3) Plan budget
        budget = plan(chunks, reduce_by=reduce_by)
        print(f"[main] tokens: original {budget['current']} -> target {budget['target']} ({int(reduce_by*100)}%)")

        # 4) Compress loop until we meet the target or hit no-improvement
        compress_to_target(chunks, target_tokens=budget["target"], 
                          model=config.compression_model,
                          batch_size=config.compression_batch_size,
                          intent=intent)

        # 5) Recount tokens
        final_tokens = recount(chunks)

        # 6) Stitch output
        out_text = _assemble(chunks)
        
        stats = {
            "original_tokens": budget["current"],
            "target_tokens": budget["target"],
            "final_tokens": final_tokens,
        }
        
        return out_text, chunks, stats

    # Use cached compression
    out_text, chunks, stats = cached_compress(
        text=text,
        compress_func=perform_compression,
        intent=intent,
        reduction_ratio=reduce_by,
        model_config={
            "rating_model": config.rating_model,
            "compression_model": config.compression_model,
            "preset": preset
        }
    )
    
    # Write output file
    out_path = inp.with_suffix(".compressed.md")
    out_path.write_text(out_text, encoding="utf-8")
    
    # Show results
    elapsed = time.time() - start_time
    result = {
        "file": str(inp),
        "output": str(out_path),
        "original_tokens": stats["original_tokens"],
        "target_tokens": stats["target_tokens"],
        "final_tokens": stats["final_tokens"],
        "cache_hit": stats.get("cache_hit", False),
        "elapsed_seconds": round(elapsed, 2),
        "preset": preset or "default"
    }
    
    print(json.dumps(result, indent=2))
    
    # Show cache stats
    cache_stats = get_cache().get_cache_stats()
    if cache_stats.get("total_entries", 0) > 0:
        print(f"\n[cache] {cache_stats['total_entries']} entries, "
              f"{cache_stats['cache_size_mb']:.1f}MB")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

