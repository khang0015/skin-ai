from __future__ import annotations

import importlib
import logging
import os
import threading
import unicodedata
from pathlib import Path
from typing import Any

from .document_loader import load_documents
from .rag_chunking import RagChunk, chunk_documents

logger = logging.getLogger(__name__)

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")


HAM10000_QUERY_HINTS: dict[str, str] = {
    "akiec": "actinic keratosis Bowen disease dày sừng ánh sáng tiền ung thư",
    "bcc": "basal cell carcinoma ung thư biểu mô tế bào đáy",
    "bkl": "benign keratosis seborrheic keratosis dày sừng lành tính",
    "df": "dermatofibroma u xơ bì",
    "mel": "melanoma ung thư hắc tố dấu hiệu ABCDE melanoma",
    "nv": "melanocytic nevus nốt ruồi lành tính",
    "vasc": "vascular lesion tổn thương mạch máu hemangioma angiokeratoma",
}

SECTION_HINTS: dict[str, str] = {
    "mel": "Melanoma",
    "nv": "Melanocytic Nevus",
    "bcc": "Basal Cell Carcinoma",
    "bkl": "Benign Keratosis",
    "df": "Dermatofibroma",
    "akiec": "Actinic Keratosis",
    "vasc": "Vascular Lesion",
}

NO_CONTEXT_NOTICE_PREFIXES = (
    "Lưu ý: câu trả lời sau đây dựa trên kiến thức chung của mô hình AI "
    "(không lấy từ cơ sở tri thức cục bộ).",
)

ASSISTANT_INTRO_ANSWER = (
    "Xin chào, tôi là trợ lý AI hỗ trợ phân tích ảnh da liễu và trả lời các câu hỏi "
    "liên quan đến chăm sóc da, dấu hiệu tổn thương da và thông tin bệnh da thường gặp.\n\n"
    "Tôi có thể hỗ trợ giải thích kết quả phân tích ảnh, gợi ý hướng theo dõi ban đầu "
    "và cung cấp thông tin tham khảo. Kết quả không thay thế chẩn đoán hoặc tư vấn "
    "trực tiếp từ bác sĩ da liễu."
)

RAG_SYSTEM_PROMPT = """
You are a dermatology AI assistant for educational and clinical-support use.
Answer in Vietnamese, clearly and concisely.
Use only the provided retrieved context and the image-analysis summary when present.
If the context is insufficient, say that the knowledge base does not contain enough information.
Do not invent facts, treatment decisions, dosages, or diagnoses beyond the context.
Always remind the user that the result is for reference and must be confirmed by a dermatologist.
""".strip()

# System prompt khi knowledge base không có context phù hợp.
# Cho phép LLM dùng kiến thức của mình, nhưng vẫn đặt biên rõ ràng.
RAG_NO_CONTEXT_SYSTEM_PROMPT = """
You are a dermatology AI assistant for educational and clinical-support use.
Answer in Vietnamese, clearly and concisely.

The local knowledge base does not contain information directly relevant to this question,
so answer using your own general medical/dermatology knowledge. Follow these rules:
- Be honest about uncertainty. If you do not know, say so.
- Do not invent specific dosages, drug names, or guideline citations you are not certain about.
- Keep medical advice general and cautious; recommend consulting a dermatologist for diagnosis.
- End with a short reminder that the result is for reference only.
""".strip()

_REPHRASE_PROMPT = """Given the conversation summary and recent user messages only, \
rephrase the follow-up question to be a standalone question that captures the full context. \
Use ONLY user messages to resolve co-references — do NOT incorporate assistant answers. \
If the follow-up already makes sense on its own, return it unchanged. \
Reply with ONLY the rephrased question, nothing else.

Conversation summary:
{summary}

Recent user messages:
{user_history}

Follow-up question: {question}
Standalone question:"""

_TITLE_PROMPT = """Generate a short, descriptive title (max 8 words, in Vietnamese) for a medical \
conversation that starts with the following exchange. Reply with ONLY the title, no quotes.

User: {user_msg}
Assistant: {ai_msg}
Title:"""

_SUMMARY_PROMPT = """Summarize this dermatology conversation in 2-3 sentences in Vietnamese. \
Focus on the main symptoms, diagnoses discussed, and key advice given.

{history}

Summary:"""

RAG_MAIN_MAX_TOKENS = int(os.getenv("RAG_MAIN_MAX_TOKENS", "2500"))
RAG_NO_CONTEXT_MAX_TOKENS = int(os.getenv("RAG_NO_CONTEXT_MAX_TOKENS", "2000"))


def _is_unsupported_param_error(exc: Exception, param_name: str) -> bool:
    message = str(exc)
    return (
        "Unsupported parameter" in message
        and f"'{param_name}'" in message
        and "unsupported_parameter" in message
    )


class LocalSentenceTransformerEmbedder:
    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        cache_dir: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir
        self._model: Any | None = None
        self._lock = threading.Lock()

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            module = importlib.import_module("sentence_transformers")
            model_cls = getattr(module, "SentenceTransformer")
            kwargs: dict[str, Any] = {"device": self.device}
            if self.cache_dir:
                kwargs["cache_folder"] = self.cache_dir
            self._model = model_cls(self.model_name, **kwargs)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        inputs = [self._format_document(text) for text in texts]
        return self._encode(inputs)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([self._format_query(text)])[0]

    def _encode(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(
            texts,
            batch_size=16,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.astype("float32").tolist()

    def _format_query(self, text: str) -> str:
        if "e5" in self.model_name.lower():
            return f"query: {text}"
        return text

    def _format_document(self, text: str) -> str:
        if "e5" in self.model_name.lower():
            return f"passage: {text}"
        return text


class RAGService:
    """Semantic RAG over local PDF, TXT, Markdown and DOCX knowledge files.

    LLM backend priority (controlled by rag_llm_backend):
      "ollama" → always use Ollama (error if unavailable)
      "openai" → always use OpenAI (error if key missing)
      "auto"   → use Ollama if ollama_base_url is set AND reachable,
                 otherwise fall back to OpenAI
    """

    # Default relevance threshold: chunks with score below this are discarded.
    # score = max(0, 1 - cosine_distance), so 0.30 means at least 30% similarity.
    DEFAULT_RELEVANCE_THRESHOLD = 0.30

    def __init__(
        self,
        knowledge_base_path: str,
        docs_dir: str | None = None,
        openai_api_key: str = "",
        openai_model: str = "gpt-4o",
        vector_store_path: str = "backend/app/data/vector_store",
        collection_name: str = "skin_lesion_knowledge",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        embedding_device: str = "cpu",
        embedding_cache_dir: str | None = "backend/models/embeddings",
        top_k: int = 4,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        mmr_lambda: float = 0.6,
        # Ollama settings
        ollama_base_url: str = "",
        ollama_model: str = "qwen2.5:7b-instruct",
        ollama_timeout: int = 120,
        rag_llm_backend: str = "auto",
    ) -> None:
        self.knowledge_base_path = Path(knowledge_base_path)
        self.docs_dir = Path(docs_dir) if docs_dir else None
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.vector_store_path = Path(vector_store_path)
        self.collection_name = collection_name
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold
        # MMR lambda: 1.0 = pure relevance, 0.0 = pure diversity
        self.mmr_lambda = mmr_lambda
        self._client: Any | None = None
        self._chroma_client: Any | None = None
        self._collection: Any | None = None
        self._collection_lock = threading.Lock()
        self.embedder = LocalSentenceTransformerEmbedder(
            model_name=embedding_model,
            device=embedding_device,
            cache_dir=embedding_cache_dir,
        )

        # ── Ollama backend ───────────────────────────────────────────
        self.rag_llm_backend = rag_llm_backend.lower().strip()
        self._ollama: Any | None = None
        if ollama_base_url:
            from .ollama_client import OllamaClient
            self._ollama = OllamaClient(
                base_url=ollama_base_url,
                model=ollama_model,
                timeout=ollama_timeout,
            )
            logger.info(
                "Ollama RAG backend configured: %s  model=%s",
                ollama_base_url,
                ollama_model,
            )

    # ── Index building ──────────────────────────────────────────────

    def build_index(self, reset: bool = False) -> int:
        """Build or refresh the vector index.

        Improvements over the original:
        - Stores doc_hash in metadata for stale-chunk detection.
        - Deletes chunks whose source file no longer exists (stale cleanup).
        - Deduplicates chunks from the same (source, heading, page) to avoid
          re-indexing identical content.
        """
        documents = load_documents(self.knowledge_base_path, self.docs_dir)
        chunks = chunk_documents(documents)
        collection = self._get_collection(reset=reset)

        if not chunks:
            return 0

        # ── Stale chunk cleanup ──────────────────────────────────────
        # Collect all source file_paths that are currently in the index
        # and delete chunks whose source no longer exists on disk.
        if not reset:
            self._cleanup_stale_chunks(collection, chunks)

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_documents(texts)
        metadatas = [self._metadata(chunk) for chunk in chunks]
        ids = [chunk.id for chunk in chunks]

        collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        logger.info("RAG index built/refreshed: %d chunks", len(chunks))
        return len(chunks)

    def _cleanup_stale_chunks(self, collection: Any, current_chunks: list[RagChunk]) -> None:
        """Remove chunks from the index whose source file no longer exists on disk,
        or whose doc_hash has changed (content was modified)."""
        try:
            total = collection.count()
            if total == 0:
                return

            # Build a map of current chunk ids → doc_hash
            current_ids = {chunk.id: chunk.doc_hash for chunk in current_chunks}
            current_file_paths = {chunk.file_path for chunk in current_chunks}

            # Fetch all existing metadata from the collection (in batches)
            batch_size = 500
            offset = 0
            ids_to_delete: list[str] = []

            while offset < total:
                result = collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas"],
                )
                existing_ids = result.get("ids", [])
                existing_metas = result.get("metadatas", [])

                for eid, emeta in zip(existing_ids, existing_metas):
                    emeta = emeta or {}
                    file_path = emeta.get("file_path", "")

                    # Source file deleted from disk
                    if file_path and file_path not in current_file_paths:
                        ids_to_delete.append(eid)
                        continue

                    # Content changed (doc_hash mismatch) — will be re-upserted
                    # but old chunk-index slots that no longer exist must be removed
                    if eid not in current_ids:
                        ids_to_delete.append(eid)

                offset += batch_size

            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info("Stale RAG chunks removed: %d", len(ids_to_delete))
        except Exception:
            logger.debug("Stale chunk cleanup failed (non-fatal)", exc_info=True)

    # ── Retrieval ───────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        return self.retrieve_with_context(query, top_k=top_k)

    def retrieve_with_context(
        self,
        query: str,
        top_k: int | None = None,
        label_hints: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve with optional metadata filtering based on disease labels."""
        collection = self._get_collection(reset=False)
        if collection.count() == 0:
            self.build_index(reset=False)

        if collection.count() == 0:
            return []

        requested_k = top_k or self.top_k
        expanded_query = self._expand_query(query)
        query_embedding = self.embedder.embed_query(expanded_query)

        # Fetch more candidates for reranking + MMR diversity selection
        n_candidates = min(max(requested_k * 5, 20), collection.count())

        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_candidates,
            "include": ["documents", "metadatas", "distances", "embeddings"],
        }

        # Metadata filtering: if we know disease labels, prefer matching sections
        if label_hints:
            section_names = [
                SECTION_HINTS[label]
                for label in label_hints
                if label in SECTION_HINTS
            ]
            if section_names:
                try:
                    filtered_kwargs = {**query_kwargs}
                    if len(section_names) == 1:
                        filtered_kwargs["where"] = {"heading": section_names[0]}
                    else:
                        filtered_kwargs["where"] = {"heading": {"$in": section_names}}
                    result = collection.query(**filtered_kwargs)
                    docs = result.get("documents", [[]])[0]
                    if docs:
                        return self._parse_query_result(
                            result, query, requested_k,
                            query_embedding=query_embedding,
                            label_hints=label_hints,
                        )
                except Exception:
                    logger.debug("Metadata-filtered query failed, falling back to unfiltered")

        result = collection.query(**query_kwargs)
        return self._parse_query_result(
            result, query, requested_k,
            query_embedding=query_embedding,
            label_hints=label_hints,
        )

    def _parse_query_result(
        self,
        result: dict[str, Any],
        query: str,
        requested_k: int,
        query_embedding: list[float] | None = None,
        label_hints: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        embeddings_raw = result.get("embeddings", [[]])[0]
        # ChromaDB may return numpy arrays or None — normalize to list of lists
        if embeddings_raw is None:
            embeddings: list = []
        else:
            try:
                embeddings = list(embeddings_raw)
            except TypeError:
                embeddings = []

        items: list[dict[str, Any]] = []
        for i, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances)
        ):
            score = max(0.0, 1.0 - float(distance))
            item: dict[str, Any] = {
                "text": document,
                "metadata": metadata or {},
                "score": score,
            }
            if i < len(embeddings):
                emb = embeddings[i]
                # Convert numpy array to plain list if needed
                if emb is not None:
                    try:
                        item["embedding"] = emb.tolist() if hasattr(emb, "tolist") else list(emb)
                    except Exception:
                        pass
            items.append(item)

        # 1. Apply relevance threshold — discard irrelevant chunks
        items = [it for it in items if it["score"] >= self.relevance_threshold]

        if not items:
            logger.debug(
                "All retrieved chunks below relevance threshold %.2f for query: %r",
                self.relevance_threshold,
                query,
            )
            return []

        # 2. Rerank with label_hints boost
        items = self._rerank(query, items, label_hints=label_hints)

        # 3. Deduplicate by (source, heading, page) — keep highest-scored per slot
        items = self._dedup(items)

        # 4. MMR diversity selection
        if query_embedding and len(items) > requested_k:
            items = self._mmr_select(items, query_embedding, requested_k)
        else:
            items = items[:requested_k]

        return items

    # ── Answer (stateless) ──────────────────────────────────────────

    def answer(self, question: str, analysis_summary: str | None = None) -> tuple[str, list[str]]:
        quick_answer = self._quick_local_answer(question)
        if quick_answer:
            return quick_answer, []

        retrieved = self.retrieve(question, top_k=self.top_k)
        contexts = [self._format_context(item) for item in retrieved]

        if not contexts:
            # KB không có context phù hợp → để LLM trả lời từ kiến thức chung
            answer = self._generate_without_context(
                question=question,
                analysis_summary=analysis_summary,
            )
            return answer, []

        answer = self._generate(question, retrieved, analysis_summary)
        return answer, contexts

    # ── Answer with history (conversational) ────────────────────────

    def answer_with_history(
        self,
        question: str,
        chat_history: list[dict[str, str]],
        analysis_summary: str | None = None,
        label_hints: list[str] | None = None,
        conversation_summary: str | None = None,
    ) -> tuple[str, list[str]]:
        quick_answer = self._quick_local_answer(question)
        if quick_answer:
            return quick_answer, []

        # Step 1: Rephrase using ONLY user messages + summary (avoid assistant drift)
        rephrased = self._rephrase_with_history(
            question, chat_history, conversation_summary=conversation_summary
        )

        # Step 2: Retrieve with metadata filtering if disease labels are known
        retrieved = self.retrieve_with_context(
            rephrased, top_k=self.top_k, label_hints=label_hints
        )
        contexts = [self._format_context(item) for item in retrieved]

        if not contexts:
            # KB không có context phù hợp → để LLM trả lời từ kiến thức chung
            answer = self._generate_without_context(
                question=question,
                analysis_summary=analysis_summary,
                chat_history=chat_history,
                conversation_summary=conversation_summary,
            )
            return answer, []

        # Step 3: Generate with condensed history
        answer = self._generate(
            question=question,
            retrieved=retrieved,
            analysis_summary=analysis_summary,
            chat_history=chat_history,
            conversation_summary=conversation_summary,
        )
        return answer, contexts

    # ── History-Aware Query Rephrasing ──────────────────────────────

    def _rephrase_with_history(
        self,
        question: str,
        chat_history: list[dict[str, str]],
        conversation_summary: str | None = None,
    ) -> str:
        """Rephrase using ONLY user messages to avoid contamination from
        potentially incorrect assistant answers."""
        if not chat_history:
            return question

        # Only use user messages — skip assistant turns to prevent drift
        user_messages = [
            msg.get("content", "")
            for msg in chat_history[-8:]
            if msg.get("role") == "user" and msg.get("content")
        ]

        if not user_messages:
            return question

        user_history_text = "\n".join(f"user: {m}" for m in user_messages)
        summary_text = conversation_summary or ""

        prompt = _REPHRASE_PROMPT.format(
            summary=summary_text,
            user_history=user_history_text,
            question=question,
        )
        rephrased = self._quick_llm_call(prompt, max_tokens=150, temperature=0.0)
        if rephrased:
            logger.debug("Rephrased: %r -> %r", question, rephrased)
            return rephrased
        return question

    # ── Conversation Title & Summary Generation ─────────────────────

    def generate_conversation_title(
        self, first_message: str, first_response: str
    ) -> str:
        prompt = _TITLE_PROMPT.format(
            user_msg=first_message[:300], ai_msg=first_response[:300]
        )
        title = self._quick_llm_call(prompt, max_tokens=100, temperature=0.3)
        if title:
            return title.strip("\"'")[:100]
        return first_message[:72] if first_message else "Cuộc trò chuyện mới"

    def generate_conversation_summary(
        self, messages: list[dict[str, str]]
    ) -> str:
        history_text = "\n".join(
            f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}"
            for msg in messages[-20:]
            if msg.get("content")
        )
        if not history_text.strip():
            return ""
        prompt = _SUMMARY_PROMPT.format(history=history_text)
        return self._quick_llm_call(prompt, max_tokens=120, temperature=0.3) or ""

    def _quick_llm_call(
        self, prompt: str, max_tokens: int = 60, temperature: float = 0.3
    ) -> str:
        backend, client = self._get_active_llm()

        if backend == "none":
            return ""

        if backend == "ollama":
            try:
                return client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except Exception as exc:
                logger.debug("Quick LLM call (ollama) failed: %s", exc)
                return ""

        # OpenAI path
        if self.openai_model.lower().startswith("gpt-5"):
            try:
                response = client.responses.create(
                    model=self.openai_model,
                    instructions="You are a helpful assistant. Reply concisely with only what is asked, no extra commentary.",
                    input=prompt,
                    max_output_tokens=max(max_tokens * 10, 500),
                )
                text = getattr(response, "output_text", None)
                if isinstance(text, str) and text.strip():
                    return text.strip()
                parts = []
                for item in getattr(response, "output", []) or []:
                    for content in getattr(item, "content", []) or []:
                        t = getattr(content, "text", None)
                        if t:
                            parts.append(str(t))
                return "\n".join(parts).strip()
            except Exception as exc:
                logger.debug("Quick LLM call (responses API) failed: %s", exc)
                return ""

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as first_exc:
            if _is_unsupported_param_error(first_exc, "max_tokens"):
                try:
                    response = client.chat.completions.create(
                        model=self.openai_model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return (response.choices[0].message.content or "").strip()
                except Exception as exc2:
                    logger.debug("Quick LLM call (completions retry) failed: %s", exc2)
            else:
                logger.debug("Quick LLM call (completions) failed: %s", first_exc)
        return ""

    # ── ChromaDB Collection ─────────────────────────────────────────

    def _get_collection(self, reset: bool = False) -> Any:
        chromadb = importlib.import_module("chromadb")
        chroma_config = importlib.import_module("chromadb.config")
        settings_cls = getattr(chroma_config, "Settings")
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        with self._collection_lock:
            if self._chroma_client is None:
                self._chroma_client = chromadb.PersistentClient(
                    path=str(self.vector_store_path),
                    settings=settings_cls(anonymized_telemetry=False),
                )

            if reset:
                try:
                    self._chroma_client.delete_collection(self.collection_name)
                except Exception:
                    pass
                self._collection = None

            if self._collection is None:
                self._collection = self._chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _metadata(chunk: RagChunk) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "source": chunk.source,
            "file_path": chunk.file_path,
            "chunk_index": chunk.chunk_index,
            "doc_hash": chunk.doc_hash,
        }
        if chunk.page is not None:
            metadata["page"] = chunk.page
        if chunk.heading:
            metadata["heading"] = chunk.heading
        return metadata

    @staticmethod
    def _format_context(item: dict[str, Any]) -> str:
        metadata = item.get("metadata", {})
        source = metadata.get("source", "unknown")
        page = metadata.get("page")
        heading = metadata.get("heading")
        location = f"{source}, page {page}" if page else source
        if heading:
            location = f"{location}, section {heading}"
        return f"[{location}] {item['text']}"

    def _get_openai_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if not self.openai_api_key or self.openai_api_key == "your-openai-api-key-here":
            return None
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("openai package is not installed; RAG will return retrieved context only.")
            return None
        self._client = OpenAI(api_key=self.openai_api_key)
        return self._client

    def _get_active_llm(self) -> tuple[str, Any]:
        """Return (backend_name, client) for the active LLM.

        Returns
        -------
        ("ollama", OllamaClient) | ("openai", OpenAI) | ("none", None)
        """
        if self.rag_llm_backend == "ollama":
            if self._ollama is None:
                logger.warning("RAG_LLM_BACKEND=ollama but OLLAMA_BASE_URL is not set.")
                return "none", None
            return "ollama", self._ollama

        if self.rag_llm_backend == "openai":
            client = self._get_openai_client()
            if client is None:
                logger.warning("RAG_LLM_BACKEND=openai but OPENAI_API_KEY is not set.")
                return "none", None
            return "openai", client

        # "auto": prefer Ollama if configured and reachable, else OpenAI
        if self._ollama is not None:
            if self._ollama.is_available():
                return "ollama", self._ollama
            else:
                logger.warning(
                    "Ollama configured but not reachable at %s — falling back to OpenAI.",
                    self._ollama.base_url,
                )

        client = self._get_openai_client()
        if client is not None:
            return "openai", client

        return "none", None

    def _generate(
        self,
        question: str,
        retrieved: list[dict[str, Any]],
        analysis_summary: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
        conversation_summary: str | None = None,
    ) -> str:
        backend, client = self._get_active_llm()
        contexts = [self._format_context(item) for item in retrieved]

        if backend == "none":
            return self._fallback_answer(question, contexts, analysis_summary)

        context_text = "\n\n".join(f"[{i + 1}] {context}" for i, context in enumerate(contexts))
        user_parts = [f"Question: {question}"]

        if conversation_summary:
            user_parts.append(f"Conversation summary so far:\n{conversation_summary}")

        if chat_history:
            recent = chat_history[-6:]
            history_text = "\n".join(
                f"{item.get('role', 'user')}: {item.get('content', '')}"
                for item in recent
                if item.get("content")
            )
            if history_text:
                user_parts.append(f"Recent conversation:\n{history_text}")

        if analysis_summary:
            user_parts.append(f"Image analysis summary: {analysis_summary}")
        user_parts.append(f"Retrieved context:\n{context_text}")
        user_parts.append("Answer in Vietnamese. Cite the source number when useful, e.g. [1].")
        user_prompt = "\n\n".join(user_parts)

        try:
            if backend == "ollama":
                answer = client.chat(
                    messages=[
                        {"role": "system", "content": RAG_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=RAG_MAIN_MAX_TOKENS,
                    temperature=0.2,
                )
            elif self.openai_model.lower().startswith("gpt-5"):
                answer = self._generate_responses_api(client, user_prompt)
            else:
                answer = self._generate_chat_completions(client, user_prompt)

            if answer:
                return answer
            logger.warning("LLM returned empty RAG answer; using fallback.")
            return self._fallback_answer(question, contexts, analysis_summary)
        except Exception as exc:
            logger.exception("RAG generation failed (backend=%s)", backend)
            return f"Không thể kết nối LLM ({exc}).\n\n" + self._fallback_answer(
                question, contexts, analysis_summary,
            )

    def _generate_responses_api(self, client: Any, user_prompt: str) -> str:
        response = client.responses.create(
            model=self.openai_model,
            instructions=RAG_SYSTEM_PROMPT,
            input=user_prompt,
            max_output_tokens=RAG_MAIN_MAX_TOKENS,
            stream=False,
        )
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        parts: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()

    def _generate_chat_completions(self, client: Any, user_prompt: str) -> str:
        request_kwargs: dict[str, Any] = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        try:
            response = client.chat.completions.create(
                **request_kwargs,
                max_tokens=RAG_MAIN_MAX_TOKENS,
            )
        except Exception as first_exc:
            if not _is_unsupported_param_error(first_exc, "max_tokens"):
                raise
            response = client.chat.completions.create(
                **request_kwargs,
                max_completion_tokens=RAG_MAIN_MAX_TOKENS,
            )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def _generate_without_context(
        self,
        question: str,
        analysis_summary: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
        conversation_summary: str | None = None,
    ) -> str:
        """Trả lời khi RAG không tìm được context phù hợp.

        Gọi LLM với knowledge base trống — model trả lời từ kiến thức của chính nó.
        """
        backend, client = self._get_active_llm()
        if backend == "none":
            return (
                "Cơ sở tri thức không có thông tin cho câu hỏi này, "
                "và LLM cũng chưa được cấu hình. Vui lòng đặt OPENAI_API_KEY "
                "hoặc bật Ollama tunnel để nhận câu trả lời."
            )

        # Build prompt giống _generate nhưng không có retrieved context
        user_parts = [f"Question: {question}"]
        if conversation_summary:
            user_parts.append(f"Conversation summary so far:\n{conversation_summary}")
        if chat_history:
            recent = chat_history[-6:]
            history_text = "\n".join(
                f"{item.get('role', 'user')}: {item.get('content', '')}"
                for item in recent
                if item.get("content")
            )
            if history_text:
                user_parts.append(f"Recent conversation:\n{history_text}")
        if analysis_summary:
            user_parts.append(f"Image analysis summary: {analysis_summary}")
        user_parts.append("Answer in Vietnamese.")
        user_prompt = "\n\n".join(user_parts)

        try:
            if backend == "ollama":
                answer = client.chat(
                    messages=[
                        {"role": "system", "content": RAG_NO_CONTEXT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=RAG_NO_CONTEXT_MAX_TOKENS,
                    temperature=0.3,
                )
                return self._strip_no_context_notice(answer)

            # OpenAI path
            if self.openai_model.lower().startswith("gpt-5"):
                response = client.responses.create(
                    model=self.openai_model,
                    instructions=RAG_NO_CONTEXT_SYSTEM_PROMPT,
                    input=user_prompt,
                    max_output_tokens=RAG_NO_CONTEXT_MAX_TOKENS,
                    stream=False,
                )
                output_text = getattr(response, "output_text", None)
                if isinstance(output_text, str) and output_text.strip():
                    return self._strip_no_context_notice(output_text)
                parts: list[str] = []
                for item in getattr(response, "output", []) or []:
                    for content in getattr(item, "content", []) or []:
                        text = getattr(content, "text", None)
                        if text:
                            parts.append(str(text))
                return self._strip_no_context_notice("\n".join(parts))

            # OpenAI chat completions
            request_kwargs: dict[str, Any] = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": RAG_NO_CONTEXT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            }
            try:
                response = client.chat.completions.create(
                    **request_kwargs,
                    max_tokens=RAG_NO_CONTEXT_MAX_TOKENS,
                )
            except Exception as first_exc:
                if not _is_unsupported_param_error(first_exc, "max_tokens"):
                    raise
                response = client.chat.completions.create(
                    **request_kwargs,
                    max_completion_tokens=RAG_NO_CONTEXT_MAX_TOKENS,
                )
            content = response.choices[0].message.content
            return self._strip_no_context_notice(content or "")

        except Exception as exc:
            logger.exception("LLM-only fallback failed (backend=%s)", backend)
            return (
                f"Cơ sở tri thức không có thông tin cho câu hỏi này, "
                f"và không thể kết nối LLM ({exc}). Vui lòng thử lại."
            )

    @staticmethod
    def _quick_local_answer(question: str) -> str | None:
        normalized = _normalize_for_match(question)
        compact = " ".join(normalized.split())
        identity_patterns = (
            "xin chao",
            "chao ban",
            "ban la ai",
            "ban la tro ly gi",
            "ban co the lam gi",
            "ban gioi thieu",
            "gioi thieu ban than",
            "gioi thieu ve ban",
            "xin chao ban la ai",
            "chao ban ban la ai",
            "chao ban hay gioi thieu",
            "hello who are you",
            "who are you",
        )
        if any(pattern in compact for pattern in identity_patterns):
            return ASSISTANT_INTRO_ANSWER
        return None

    @staticmethod
    def _strip_no_context_notice(answer: str) -> str:
        cleaned = (answer or "").strip()
        for prefix in NO_CONTEXT_NOTICE_PREFIXES:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].lstrip()
        return cleaned

    @staticmethod
    def _fallback_answer(
        question: str,
        contexts: list[str],
        analysis_summary: str | None = None,
    ) -> str:
        analysis_text = f"\nKết quả phân tích ảnh: {analysis_summary}" if analysis_summary else ""
        return (
            "Đây là câu trả lời dựa trên các đoạn ngữ cảnh được truy xuất từ cơ sở tri thức. "
            "Kết quả chỉ mang tính tham khảo và cần được bác sĩ da liễu xác nhận.\n\n"
            f"Câu hỏi: {question}{analysis_text}\n\n"
            "Các đoạn ngữ cảnh liên quan được hiển thị bên dưới."
        )

    @staticmethod
    def _expand_query(query: str) -> str:
        """Expand query with domain-specific terms.

        Two expansion strategies:
        1. HAM10000 code tokens (mel, nv, bcc…) → append full disease description.
        2. Vietnamese keywords without diacritics → append English equivalents
           so the multilingual embedding model can match English knowledge base content.
        """
        tokens = set(_normalize_for_match(query).split())
        hints = [hint for code, hint in HAM10000_QUERY_HINTS.items() if code in tokens]

        # Vietnamese keyword → English expansion for queries without diacritics
        _VI_EN_MAP = {
            "melanoma": "melanoma skin cancer ABCDE asymmetry border color diameter",
            "ung thu": "cancer carcinoma malignant",
            "da lieu": "dermatology skin lesion",
            "not ruoi": "nevus mole melanocytic",
            "dau hieu": "signs symptoms features",
            "nhan biet": "identify recognize diagnosis",
            "dieu tri": "treatment therapy management",
            "chan doan": "diagnosis diagnostic",
            "bcc": "basal cell carcinoma",
            "akiec": "actinic keratosis Bowen disease",
            "bkl": "benign keratosis seborrheic",
            "vasc": "vascular lesion hemangioma",
        }
        en_hints = []
        normalized_q = _normalize_for_match(query)
        for vi_key, en_val in _VI_EN_MAP.items():
            if _normalize_for_match(vi_key) in normalized_q:
                en_hints.append(en_val)

        all_hints = hints + en_hints
        if not all_hints:
            return query
        return f"{query}\n\nExpanded dermatology terms: {'; '.join(all_hints)}"

    @staticmethod
    def _rerank(
        query: str,
        items: list[dict[str, Any]],
        label_hints: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Rerank with:
        1. Token-based boost for disease codes in query.
        2. Direct label_hints boost (from image analysis) — more reliable than
           token matching since label_hints come from the classifier output.
        """
        tokens = set(_normalize_for_match(query).split())
        hint_codes = set(label_hints or [])

        for item in items:
            metadata = item.get("metadata", {})
            heading = str(metadata.get("heading", ""))
            text = str(item.get("text", ""))
            normalized_heading = _normalize_for_match(heading)
            normalized_text = _normalize_for_match(text)
            boost = 0.0

            # Boost from query tokens
            for code, section_hint in SECTION_HINTS.items():
                if code not in tokens:
                    continue
                if _normalize_for_match(section_hint) in normalized_heading:
                    boost += 0.25
                elif _normalize_for_match(section_hint) in normalized_text[:300]:
                    boost += 0.10

            # Boost from label_hints (image analysis result) — higher weight
            for code in hint_codes:
                section_hint = SECTION_HINTS.get(code, "")
                if not section_hint:
                    continue
                if _normalize_for_match(section_hint) in normalized_heading:
                    boost += 0.35
                elif _normalize_for_match(section_hint) in normalized_text[:300]:
                    boost += 0.15

            item["score"] = float(item.get("score", 0.0)) + boost

        return sorted(items, key=lambda it: it.get("score", 0.0), reverse=True)

    @staticmethod
    def _dedup(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate by (source, heading, page) — keep highest-scored chunk per slot.
        This prevents multiple near-identical chunks from the same section dominating results.
        """
        seen: dict[tuple, dict[str, Any]] = {}
        for item in items:
            meta = item.get("metadata", {})
            key = (
                meta.get("source", ""),
                meta.get("heading", ""),
                meta.get("page", ""),
            )
            if key not in seen or item.get("score", 0.0) > seen[key].get("score", 0.0):
                seen[key] = item
        # Preserve original score-sorted order
        return sorted(seen.values(), key=lambda it: it.get("score", 0.0), reverse=True)

    def _mmr_select(
        self,
        items: list[dict[str, Any]],
        query_embedding: list[float],
        k: int,
    ) -> list[dict[str, Any]]:
        """Maximal Marginal Relevance selection for diversity.

        Selects k items that balance relevance to the query and diversity
        among selected items. Items without embeddings fall back to score-only.
        """
        import math

        def cosine_sim(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        # Items without embeddings go to fallback pool
        with_emb = [it for it in items if it.get("embedding")]
        without_emb = [it for it in items if not it.get("embedding")]

        if not with_emb:
            return items[:k]

        selected: list[dict[str, Any]] = []
        remaining = list(with_emb)

        while len(selected) < k and remaining:
            if not selected:
                # First pick: highest relevance score
                best = max(remaining, key=lambda it: it.get("score", 0.0))
            else:
                # MMR: maximize λ·relevance − (1−λ)·max_similarity_to_selected
                best = None
                best_mmr = float("-inf")
                for candidate in remaining:
                    rel = float(candidate.get("score", 0.0))
                    max_sim = max(
                        cosine_sim(candidate["embedding"], sel["embedding"])
                        for sel in selected
                        if sel.get("embedding")
                    )
                    mmr_score = self.mmr_lambda * rel - (1 - self.mmr_lambda) * max_sim
                    if mmr_score > best_mmr:
                        best_mmr = mmr_score
                        best = candidate

            if best is None:
                break
            selected.append(best)
            remaining.remove(best)

        # Fill remaining slots from without_emb pool if needed
        if len(selected) < k:
            selected.extend(without_emb[: k - len(selected)])

        return selected


def _normalize_for_match(text: str) -> str:
    normalized = []
    ascii_text = "".join(
        char for char in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(char) != "Mn"
    )
    for char in ascii_text:
        if char.isalnum():
            normalized.append(char)
        else:
            normalized.append(" ")
    return " ".join("".join(normalized).split())
