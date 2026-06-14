from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _path_env(name: str, default: Path) -> str:
    value = os.getenv(name)
    return value if value else str(default)


@dataclass(frozen=True)
class Settings:
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    database_url: str = os.getenv("DATABASE_URL", "")
    admin_token: str = os.getenv("ADMIN_TOKEN", "")
    admin_page_password: str = os.getenv("ADMIN_PAGE_PASSWORD", "12345")

    yolo_model_path: str = os.getenv(
        "YOLO_MODEL_PATH", str(ROOT_DIR / "backend" / "models" / "yolov8s.pt")
    )
    cnn_model_path: str = os.getenv(
        "CNN_MODEL_PATH", str(ROOT_DIR / "backend" / "models" / "cnn_model.h5")
    )
    cnn_input_size: int = int(os.getenv("CNN_INPUT_SIZE", "224"))
    cnn_class_names: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv(
            "CNN_CLASS_NAMES",
            "melanoma,nevus,benign_keratosis,basal_cell_carcinoma,actinic_keratosis",
        ).split(",")
        if item.strip()
    )

    knowledge_base_path: str = _path_env(
        "KNOWLEDGE_BASE_PATH",
        ROOT_DIR / "backend" / "app" / "data" / "knowledge_base.md",
    )
    model_registry_path: str = _path_env(
        "MODEL_REGISTRY_PATH",
        ROOT_DIR / "backend" / "app" / "data" / "model_registry.json",
    )
    skin_threshold: float = float(os.getenv("SKIN_THRESHOLD", "0.15"))

    # Minimum YOLO detection confidence to pass to classifier
    detection_confidence_threshold: float = float(
        os.getenv("DETECTION_CONFIDENCE_THRESHOLD", "0.25")
    )

    # ── Upload directory for persisting user images ──────────────────
    upload_dir: str = _path_env(
        "UPLOAD_DIR",
        ROOT_DIR / "backend" / "uploads",
    )

    # Max age (days) for uploaded images before cleanup; 0 = disabled
    upload_cleanup_days: int = int(os.getenv("UPLOAD_CLEANUP_DAYS", "7"))

    # ── OpenAI GPT Vision Classifier ────────────────────────────────
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Timeout (seconds) for external API calls (OpenAI, HuggingFace)
    api_call_timeout: int = int(os.getenv("API_CALL_TIMEOUT", "60"))

    # Semantic RAG Retriever
    rag_docs_dir: str = _path_env(
        "RAG_DOCS_DIR",
        ROOT_DIR / "backend" / "app" / "data" / "docs" / "raw",
    )
    rag_vector_store_path: str = _path_env(
        "RAG_VECTOR_STORE_PATH",
        ROOT_DIR / "backend" / "app" / "data" / "vector_store",
    )
    rag_collection_name: str = os.getenv("RAG_COLLECTION_NAME", "skin_lesion_knowledge")
    rag_embedding_model: str = os.getenv(
        "RAG_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    rag_embedding_device: str = os.getenv("RAG_EMBEDDING_DEVICE", "cpu")
    rag_embedding_cache_dir: str = _path_env(
        "RAG_EMBEDDING_CACHE_DIR",
        ROOT_DIR / "backend" / "models" / "embeddings",
    )
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))

    # Minimum cosine similarity score (0–1) for a chunk to be included in context.
    # Chunks below this threshold are discarded even if they are top-k.
    rag_relevance_threshold: float = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.30"))

    # MMR lambda: 1.0 = pure relevance, 0.0 = pure diversity
    rag_mmr_lambda: float = float(os.getenv("RAG_MMR_LAMBDA", "0.6"))

    # ── Database connection pool ─────────────────────────────────────
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # ── HuggingFace Phi-4 Vision Classifier ─────────────────────────
    hf_api_key: str = os.getenv("HUGGING_FACE_API_KEY", "")
    hf_model: str = os.getenv("HF_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")

    # ── Ollama RAG LLM (local/tunneled) ──────────────────────────────
    # Set OLLAMA_BASE_URL to enable Ollama as the RAG generator.
    # When empty, Ollama is disabled and OpenAI is used instead.
    # Typical value after SSH tunnel: http://localhost:11434
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    # Timeout in seconds for Ollama requests (first token can be slow)
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    # Which LLM backend to use for RAG generation: "openai" | "ollama" | "auto"
    # "auto" = use Ollama if OLLAMA_BASE_URL is set, else fall back to OpenAI
    rag_llm_backend: str = os.getenv("RAG_LLM_BACKEND", "auto")


settings = Settings()
