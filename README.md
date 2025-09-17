# Prompt Compressor

A high-performance, end-to-end tool to compress very long Markdown prompts by a target percentage while preserving intent and structure. It uses a split → rate → plan → compress → recount → stitch loop with GPT models, featuring SQLite caching, batch processing, and performance optimizations.

## Features

### 🚀 Performance Optimizations
- **SQLite Caching**: Hash-based caching prevents reprocessing identical content
- **Batch Compression**: Process multiple chunks simultaneously (up to 8x faster)
- **Token Count Caching**: Avoid redundant tiktoken computations
- **Smart Retry Logic**: Skip already-optimized chunks and limit retry attempts
- **Async Processing**: Concurrent API calls for rating and compression

### 🎯 Intelligent Compression
- **Markdown-Aware Chunking**: Respects code blocks, headings, and list structures
- **Relevance Rating**: AI-powered scoring to prioritize important content
- **Intent-Driven**: Uses author intent to guide compression decisions
- **Configurable Models**: Support for GPT-4o, GPT-4o-mini, and other models

### ⚙️ Configuration Presets
- **Fast**: Optimized for speed (GPT-4o-mini, high concurrency)
- **Balanced**: Good speed/quality tradeoff (mixed models)
- **Quality**: Maximum quality (GPT-4o, careful processing)

## Requirements
- Python 3.8+
- `openai>=1.35.0`, `tiktoken>=0.5.2`, `Flask>=3.0.0`
- `.env` with `OPENAI_API_KEY=...` (access to models like `gpt-4o`, `gpt-4o-mini`)
- `sqlite3` (included with Python)

## Setup
- Install deps: `pip install -r requirements.txt`
- Create `.env` in repo root:
  - `OPENAI_API_KEY=sk-...`

## Full Pipeline (Steps 0-6)
Run all steps on a file (defaults to `original-prompt.md`):

- `python main.py [path]`
- `python main.py [path] --preset fast`      # Fastest compression
- `python main.py [path] --preset balanced`  # Balanced speed/quality (default)
- `python main.py [path] --preset quality`   # Highest quality

You’ll be prompted for:
- Author intent/focus (one line)
- Desired reduction (e.g., `0.30` or `30%`)

Outputs:
- `<input>.compressed.md`
- JSON summary (original/target/final tokens, elapsed time, cache status) to stdout
- Cache statistics (if entries exist)

## Web App
A minimal Flask app is provided for an in-browser workflow.

1) Install deps (adds Flask):
- `pip install -r requirements.txt`

2) Ensure `.env` has your key:
- `OPENAI_API_KEY=sk-...`

3) Run the dev server:
- `python app.py`
- Open http://127.0.0.1:5000

Paste your Markdown, set intent and reduction (e.g., 30%), and submit. The results page shows:
- Original tokens
- Target tokens
- Final tokens after compression
- Side-by-side original and compressed Markdown

## Quick Peek (Steps 1–3 only)
- `python demo.py [path]`
- Shows chunking + relevance summary without compressing.

## How It Works
- Step 0 — Caching (`cache.py`): checks SQLite database for previously compressed content with the same parameters
- Step 1 — Chunking (`compressor.py: split`): packs Markdown blocks into ~2k–4k token chunks, never splitting code fences or list items
- Step 2 — Rating (`rater.py: rate_chunks`): async AI scoring 0–10 for importance, using your intent (up to 30 concurrent requests)
- Step 3 — Target (`compressor.py: plan`): computes original/target tokens from desired reduction
- Step 4 — Compression (`step4.py: compress_to_target`): shortens least‑relevant largest chunks in parallel batches until target is met
- Step 5 — Recount (`compressor.py: recount`): recomputes per‑chunk tokens with caching to steer the loop
- Step 6 — Stitch, Stats & Cache (`main.py`): reassembles in order, writes output, caches result, prints summary

## Explain it like I'm 10 (ELI10)
- Imagine you wrote a super long story and need it shorter, but it still has to mean the same thing.
- First, we cut the story into neat pages (chunks) without tearing through pictures or code boxes.
- Then we ask a helpful robot to score which pages are most important for your goal (your “intent”).
- We pick a goal for how much shorter the story should be.
- We gently shrink the least‑important, biggest pages first. We keep the meaning, and we don’t change the code boxes at all.
- We count the “word pieces” (tokens) again and stop when we reached the goal, then glue the pages back together.

## Project Structure
- `main.py` — Orchestrates the full pipeline with caching
- `cache.py` — SQLite-based caching system for compression results
- `config.py` — Performance configuration presets (fast/balanced/quality)
- `compressor.py` — Split/plan/recount with token caching
- `rater.py` — Optimized async relevance scoring
- `step4.py` — Batch compression with parallel processing
- `app.py` — Flask web interface
- `demo.py` — Steps 1–3 summary
- `original-prompt.md` — Example input
- `.cache/` — Directory containing SQLite database
- `requirements.txt`, `LICENSE`

## Configuration

### Using Preset Configurations

Use the `--preset` command line option to select performance presets:
```bash
python main.py document.md --preset fast      # Speed optimized
python main.py document.md --preset balanced  # Default balance
python main.py document.md --preset quality   # Quality optimized
```

### Manual Configuration

Edit `config.py` to customize settings:

```python
# Fast preset example (edit or create your own)
FAST_CONFIG = CompressorConfig(
    rating_model="gpt-4o-mini",
    compression_model="gpt-4o-mini",
    rating_concurrency=30,
    compression_batch_size=8,
    max_compression_attempts=2,
)
```

Key configuration parameters:
- `rating_model`: Model used for scoring chunks (e.g., "gpt-4o-mini", "gpt-4o")
- `compression_model`: Model used for compressing chunks
- `rating_concurrency`: Number of concurrent rating requests (default 20)
- `compression_batch_size`: Number of chunks to compress in parallel (default 5)
- `max_compression_attempts`: Maximum retries per chunk (default 3)
- `compression_threshold`: Skip if already compressed below this ratio (default 0.7)

## Troubleshooting

### Common Issues
- 400 BadRequest (tokens): keep `openai>=1.35.0` and ensure model access; we request `max_output_tokens` ≥ 200
- Rate limits: reduce concurrency in config.py (`rating_concurrency` and `compression_batch_size`)
- Token accuracy: install `tiktoken`; otherwise word counts are used as fallback
- Missing key: ensure `.env` contains `OPENAI_API_KEY`
- Slow performance: try `--preset fast` for better speed
- Memory issues: the token cache uses memory proportional to text processed

### Cache Issues
- Ensure `.cache` directory is writable
- If cache becomes corrupted, delete `.cache/compression_cache.db`
- Check SQLite3 is available on your system

### API Cost Optimization
- Use `gpt-4o-mini` for faster, cheaper processing
- Leverage caching for repeated content
- Lower `max_compression_attempts` to reduce API calls

## Performance and Cost Notes

### Performance Comparison

| Document Size | Before Optimization | After (No Cache) | After (Cache Hit) |
|---------------|---------------------|------------------|-------------------|
| Small (1K tokens) | 15-30s | 4-8s | <1s |
| Medium (5K tokens) | 45-90s | 10-20s | <1s |
| Large (10K tokens) | 120-240s | 20-40s | <1s |

Performance varies based on model selection, document complexity, and network conditions.

### Cost Optimization

The optimizations significantly reduce OpenAI API costs:

- **Caching**: Eliminates duplicate processing costs entirely
- **Batch processing**: Reduces overhead per request
- **Smart retries**: Avoids wasted API calls on diminishing returns
- **Model selection**: `gpt-4o-mini` is ~10x cheaper than `gpt-4o`

**Example cost savings for a 10K token document:**
- Before: ~$0.20-0.40 per compression (multiple full document passes)
- After: ~$0.05-0.15 per compression (optimized batch processing)
- Cache hit: $0.00 (instant result)

## License
MIT — see `LICENSE`.

