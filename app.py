from __future__ import annotations

from flask import Flask, render_template, request
from typing import Optional

from compressor import split, plan, recount
from rater import rate_chunks
from step4 import compress_to_target

app = Flask(__name__)


def _assemble(chunks):
    # Keep original order using character positions
    return "".join(c["text"] for c in sorted(chunks, key=lambda c: c.get("start", 0)))


def _parse_reduction(rraw: Optional[str]) -> float:
    if not rraw:
        return 0.30
    rraw = rraw.strip()
    try:
        if rraw.endswith('%'):
            return max(0.0, min(0.95, float(rraw[:-1]) / 100.0))
        val = float(rraw)
        # treat 25 as 25%, 0.25 as 25%
        frac = (val / 100.0) if val > 1 else val
        return max(0.0, min(0.95, frac))
    except Exception:
        return 0.30


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/compress")
def compress():
    text = request.form.get("text", "").strip()
    intent = (request.form.get("intent", "") or None)
    rraw = request.form.get("reduction", "0.30")

    if not text:
        return render_template("index.html", error="Please paste Markdown to compress."), 400

    reduce_by = _parse_reduction(rraw)

    # 1) Chunk
    chunks = split(text)

    # 2) Rate (uses intent)
    rate_chunks(chunks, intent=intent)

    # 3) Plan budget
    budget = plan(chunks, reduce_by=reduce_by)

    # 4) Compress loop
    compress_to_target(chunks, target_tokens=budget["target"], intent=intent)

    # 5) Recount tokens
    final_tokens = recount(chunks)

    # 6) Stitch
    out_text = _assemble(chunks)

    return render_template(
        "result.html",
        original_tokens=budget["current"],
        target_tokens=budget["target"],
        final_tokens=final_tokens,
        reduction=int(reduce_by * 100),
        original_text=text,
        compressed_text=out_text,
        intent=intent or "",
    )


if __name__ == "__main__":
    # Run the development server
    app.run(host="127.0.0.1", port=5000, debug=True)

