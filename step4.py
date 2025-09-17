"""STEP 04: optimized compress loop with batch processing and caching.
While current > target, compress chunks via GPT models starting from the
least‑relevant largest ones. Processes multiple chunks simultaneously;
stops when none improve or target is met.
"""
from __future__ import annotations
from typing import List, Dict, Optional
import asyncio

# Token counting cache to avoid recomputing
_token_cache = {}

def _tok(s: str) -> int:
    if s in _token_cache:
        return _token_cache[s]
    try:
        import tiktoken
        count = len(tiktoken.get_encoding("cl100k_base").encode(s))
    except Exception:
        count = len(s.split())
    _token_cache[s] = count
    return count

def _key(ch: Dict) -> tuple:
    return (ch.get("score", 5.0), -ch.get("tokens", _tok(ch.get("text",""))))

def _load_key() -> None:
    import os, pathlib
    if os.environ.get("OPENAI_API_KEY"): return
    try:
        for ln in pathlib.Path(".env").read_text(encoding="utf-8").splitlines():
            if ln.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = ln.split("=",1)[1].strip().strip('"').strip("'")
                break
    except Exception: pass

async def _compress_chunk_async(client, ch: Dict, new_tok: int, model: str, intent: Optional[str] = None) -> tuple[Dict, str, int]:
    """Compress a single chunk asynchronously."""
    t = ch["text"]
    t0 = _tok(t)
    sys = ("Shorten the Markdown chunk conservatively. Preserve meaning. "
           "KEEP code fences unchanged; do not alter code. Keep headings/lists. "
           f"Aim for <= {new_tok} tokens (roughly words). Return only the chunk.")
    if intent:
        sys += f" Author intent: {intent}"
    
    rsp = await client.responses.create(
        model=model,
        input=[{"role":"system","content":sys},{"role":"user","content":f"```md\n{t[:12000]}\n```"}],
        temperature=0,
        max_output_tokens=2048,
    )
    out = (getattr(rsp, "output_text", None) or "").strip() or t
    return ch, out, t0

def compress_to_target(
    chunks: List[Dict], target_tokens: int, model: str = "gpt-4o-mini", intent: Optional[str] = None,
    batch_size: int = 5
) -> List[Dict]:
    """Compress chunks to target with batch processing and smart fallbacks."""
    from openai import AsyncOpenAI
    _load_key()
    
    def total(): 
        return sum(_tok(c["text"]) for c in chunks)
    
    async def compress_batch_async():
        client = AsyncOpenAI()
        cur, it = total(), 0
        print(f"[compress] starting compression loop: {cur} -> {target_tokens} tokens")
        
        while cur > target_tokens and it < 32:
            it += 1
            improved = False
            candidates = sorted(chunks, key=_key)
            need = cur - target_tokens
            
            # Select up to batch_size chunks for compression
            batch_candidates = []
            for ch in candidates:
                t0 = _tok(ch["text"])
                # Skip if too small, already processed, or batch is full
                if (t0 <= 1 or len(batch_candidates) >= batch_size or 
                    ch.get('_compression_attempts', 0) >= 3):
                    continue
                
                # Skip if chunk is already well-compressed (diminishing returns)
                if ch.get('_original_tokens') and t0 < ch['_original_tokens'] * 0.7:
                    continue
                    
                if '_original_tokens' not in ch:
                    ch['_original_tokens'] = t0
                    
                new_tok = max(1, t0 - max(1, min(int(t0*0.4), need // max(1, batch_size))))
                batch_candidates.append((ch, new_tok))
            
            if not batch_candidates:
                break
                
            print(f"\r[compress] iteration {it}: compressing {len(batch_candidates)} chunks in parallel", end='', flush=True)
            
            # Process batch asynchronously
            tasks = [_compress_chunk_async(client, ch, new_tok, model, intent) 
                    for ch, new_tok in batch_candidates]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Apply successful compressions
            for result in results:
                if isinstance(result, Exception):
                    continue
                ch, out, t0 = result
                ch['_compression_attempts'] = ch.get('_compression_attempts', 0) + 1
                
                new_tokens = _tok(out)
                if new_tokens < t0:
                    ch["text"] = out
                    ch["tokens"] = new_tokens
                    improved = True
            
            cur = total()
            if improved:
                print(f"\r[compress] iteration {it}: batch completed, total: {cur} tokens" + " "*20)
            else:
                print(f"\n[compress] no improvements in batch at iteration {it}")
                break
                
        print(f"[compress] finished: {cur} tokens (target was {target_tokens})")
        return chunks
    
    return asyncio.run(compress_batch_async())

__all__ = ["compress_to_target"]
