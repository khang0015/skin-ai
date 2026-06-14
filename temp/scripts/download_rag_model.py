from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the local embedding model for RAG.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cache-dir", default="backend/models/embeddings")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
    os.environ.setdefault("USE_TF", "0")
    from sentence_transformers import SentenceTransformer

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    SentenceTransformer(args.model, cache_folder=str(cache_dir), device=args.device)
    print(f"Downloaded embedding model: {args.model}")
    print(f"Cache directory: {cache_dir.resolve()}")


if __name__ == "__main__":
    main()
