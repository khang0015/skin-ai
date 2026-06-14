from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.services.rag_service import RAGService


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the persistent semantic RAG vector index.")
    parser.add_argument("--knowledge-base", default=settings.knowledge_base_path)
    parser.add_argument("--docs-dir", default=settings.rag_docs_dir)
    parser.add_argument("--vector-store", default=settings.rag_vector_store_path)
    parser.add_argument("--collection", default=settings.rag_collection_name)
    parser.add_argument("--embedding-model", default=settings.rag_embedding_model)
    parser.add_argument("--embedding-device", default=settings.rag_embedding_device)
    parser.add_argument("--embedding-cache-dir", default=settings.rag_embedding_cache_dir)
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the collection.")
    args = parser.parse_args()

    Path(args.docs_dir).mkdir(parents=True, exist_ok=True)
    service = RAGService(
        knowledge_base_path=args.knowledge_base,
        docs_dir=args.docs_dir,
        vector_store_path=args.vector_store,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        embedding_device=args.embedding_device,
        embedding_cache_dir=args.embedding_cache_dir,
    )
    count = service.build_index(reset=args.reset)
    print(f"Indexed {count} chunks into collection '{args.collection}'.")
    print(f"Vector store: {Path(args.vector_store).resolve()}")


if __name__ == "__main__":
    main()
