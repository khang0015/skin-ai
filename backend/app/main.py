from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import io
import logging
import os
import tempfile
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from .config import settings
from .db.session import get_db, init_db, is_database_configured
from .ml.pipeline import AnalysisPipelineRunner
from .ml.registry import ModelRegistry
from .schemas import (
    AdminChatHistoryPage,
    AdminConversationDetail,
    AdminConversationItem,
    AnalyzeResponse,
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    ClientRequest,
    ConversationCreateRequest,
    ConversationItem,
    ConversationUpdateRequest,
    DefaultPipelineResponse,
    DefaultPipelineUpdate,
    DetectionResult,
    LLMSettingsResponse,
    LLMSettingsUpdate,
    MessageItem,
    RegistryConfigResponse,
    RegistryConfigUpdate,
)
from .services import db_service
from .services.document_loader import SUPPORTED_EXTENSIONS
from .services.rag_service import RAGService
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

app = FastAPI(title="Skin Lesion Detection + RAG API", version="0.2.0")

NOT_SKIN_ANSWER = (
    "Ảnh không được nhận dạng là ảnh da.\n\n"
    "Tip: Để hệ thống phát hiện chính xác hơn, hãy chụp cận cảnh vùng da nghi ngờ tổn thương, "
    "đặt vùng cần khám ở giữa ảnh, đủ sáng và hạn chế nền xung quanh."
)
NO_DETECTION_ANSWER = (
    "Ảnh là vùng da nhưng chưa phát hiện vùng tổn thương đủ rõ để phân loại.\n\n"
    "Tip: Hãy chụp cận cảnh hơn vùng nghi ngờ bệnh, đặt tổn thương ở giữa ảnh, đủ sáng "
    "và hạn chế rung/mờ để mô hình phát hiện chính xác hơn."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RAG_DOCS_DIR = Path(settings.rag_docs_dir)
RAG_DOCS_DIR.mkdir(parents=True, exist_ok=True)

model_registry = ModelRegistry(settings.model_registry_path)


def _try_load_active_registry_config() -> None:
    """Try to load active registry from DB.

    If the DB config is stale (references detectors/classifiers that no longer
    exist in the JSON file), keep the JSON file as source of truth instead.
    This prevents startup failures after model_registry.json was simplified.
    """
    if not is_database_configured():
        return
    db_gen = None
    try:
        db_gen = get_db()
        db = next(db_gen)
        active = db_service.get_active_registry_config(db)
        if active is not None:
            try:
                model_registry.reload_from_data(active.config)
                logger.info("Loaded active registry config from DB.")
            except (ValueError, KeyError) as exc:
                # DB config references models that no longer exist (e.g. cnn_keras).
                # Fall back to the JSON file and overwrite DB on next startup.
                logger.warning(
                    "DB registry config is stale (%s) — falling back to file. "
                    "Use POST /api/admin/default-pipeline/reset to clean DB.",
                    exc,
                )
    except Exception:
        logger.warning("Could not load active registry config from DB at startup.", exc_info=True)
    finally:
        if db_gen is not None:
            try:
                db_gen.close()
            except Exception:
                pass


_try_load_active_registry_config()
pipeline_runner = AnalysisPipelineRunner(
    model_registry,
    skin_threshold=settings.skin_threshold,
    detection_confidence_threshold=settings.detection_confidence_threshold,
)
rag_service = RAGService(
    knowledge_base_path=settings.knowledge_base_path,
    docs_dir=settings.rag_docs_dir,
    openai_api_key=settings.openai_api_key,
    openai_model=settings.openai_model,
    vector_store_path=settings.rag_vector_store_path,
    collection_name=settings.rag_collection_name,
    embedding_model=settings.rag_embedding_model,
    embedding_device=settings.rag_embedding_device,
    embedding_cache_dir=settings.rag_embedding_cache_dir,
    top_k=settings.rag_top_k,
    relevance_threshold=settings.rag_relevance_threshold,
    mmr_lambda=settings.rag_mmr_lambda,
    ollama_base_url=settings.ollama_base_url,
    ollama_model=settings.ollama_model,
    ollama_timeout=settings.ollama_timeout,
    rag_llm_backend=settings.rag_llm_backend,
)


@app.on_event("startup")
def startup_database() -> None:
    if not is_database_configured():
        logger.info("DATABASE_URL not configured — skipping DB init.")
        return
    db_gen = None
    try:
        init_db()
        db_gen = get_db()
        db = next(db_gen)
        active = db_service.get_active_registry_config(db)
        if active is None:
            db_service.save_registry_config(
                db,
                name="file-seed",
                config=model_registry.to_dict(),
                activate=True,
            )
            db_service.sync_pipeline_presets(db, model_registry.to_dict())
            db.commit()
            logger.info("Seeded DB with registry from JSON file.")
        else:
            try:
                model_registry.reload_from_data(active.config)
            except (ValueError, KeyError) as exc:
                # DB has stale config referencing removed models — overwrite with file.
                logger.warning(
                    "DB registry is stale (%s); overwriting with file-seed.", exc,
                )
                file_config = model_registry.to_dict()  # current = file (since reload failed)
                db_service.save_registry_config(
                    db, name="file-seed", config=file_config, activate=True,
                )
                db_service.sync_pipeline_presets(db, file_config)
                db.commit()
    except Exception:
        logger.exception("Database startup failed — continuing without DB persistence.")
    finally:
        if db_gen is not None:
            try:
                db_gen.close()
            except Exception:
                pass


@app.on_event("startup")
async def startup_rag_index() -> None:
    """Pre-build the RAG index at startup so the first request isn't slow."""
    try:
        count = await run_in_threadpool(rag_service.build_index, False)
        logger.info("RAG index ready: %d chunks", count)
    except Exception:
        logger.exception("RAG index build at startup failed — will retry on first request.")


@app.get("/api/health")
def health() -> dict:
    status: dict = {
        "status": "ok",
        "pipelines": sorted(model_registry.pipelines.keys()),
        "detectors": sorted(model_registry.detectors.keys()),
        "classifiers": sorted(model_registry.classifiers.keys()),
    }

    # Check database connectivity
    if is_database_configured():
        try:
            db_gen = get_db()
            db = next(db_gen)
            db.execute(text("SELECT 1"))
            status["database"] = "ok"
        except Exception as exc:
            status["database"] = f"error: {exc}"
            status["status"] = "degraded"
        finally:
            try:
                db_gen.close()
            except Exception:
                pass
    else:
        status["database"] = "not configured"

    # Check model files exist
    missing_models: list[str] = []
    for name, det in model_registry.detectors.items():
        from pathlib import Path as _Path
        mp = getattr(det, "model_path", "")
        if mp and mp not in ("openai-api", "huggingface-api") and not _Path(mp).exists():
            missing_models.append(f"detector:{name}")
    for name, clf in model_registry.classifiers.items():
        mp = getattr(clf, "model_path", "")
        if mp and mp not in ("openai-api", "huggingface-api") and not _Path(mp).exists():
            missing_models.append(f"classifier:{name}")
    if missing_models:
        status["missing_models"] = missing_models
        status["status"] = "degraded"

    # Check Ollama connectivity if configured
    if settings.ollama_base_url:
        try:
            ollama_ok = rag_service._ollama is not None and rag_service._ollama.is_available()
            status["ollama"] = "ok" if ollama_ok else "unreachable"
            if not ollama_ok:
                status["status"] = "degraded"
        except Exception as exc:
            status["ollama"] = f"error: {exc}"
            status["status"] = "degraded"

    status["rag_llm_backend"] = settings.rag_llm_backend

    return status


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="ADMIN_TOKEN is not configured.")
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token.")


def ensure_database(db: Session | None = None) -> None:
    if not is_database_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    if db is None:
        return

    try:
        db.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check DATABASE_URL and database credentials.",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        ) from exc


# ── Image Analysis ──────────────────────────────────────────────────

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    pipeline: str = Form("default"),
) -> AnalyzeResponse:
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    # Stream-read with early size check to avoid loading huge files into memory.
    # UploadFile.read() supports a chunk size parameter; we loop manually so we
    # can reject oversized uploads without buffering the whole payload.
    chunks: list[bytes] = []
    total_read = 0
    chunk_size = 64 * 1024  # 64 KB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > max_bytes:
            raise HTTPException(status_code=413, detail="Uploaded file is too large.")
        chunks.append(chunk)
    data = b"".join(chunks)

    try:
        with Image.open(io.BytesIO(data)) as img:
            file_kind = (img.format or "").lower()
    except (UnidentifiedImageError, OSError):
        file_kind = ""

    if file_kind not in {"jpeg", "png", "bmp", "webp"}:
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    suffix_map = {"jpeg": ".jpg", "png": ".png", "bmp": ".bmp", "webp": ".webp"}
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix_map[file_kind]) as tmp:
        tmp.write(data)
        temp_image_path = tmp.name

    warnings: list[str] = []
    try:
        image_bgr = cv2.imread(temp_image_path)
        if image_bgr is None:
            raise HTTPException(status_code=400, detail="Could not decode image.")

        try:
            # Run CPU-bound inference in a thread pool to avoid blocking the event loop
            result = await run_in_threadpool(
                pipeline_runner.run,
                image_path=temp_image_path,
                image_bgr=image_bgr,
                pipeline_name=pipeline,
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        warnings.extend(result["warnings"])

        output_items = [DetectionResult(**item) for item in result["detections"]]
        return AnalyzeResponse(
            pipeline=result["pipeline"],
            detector=result["detector"],
            classifier=result["classifier"],
            detections=output_items,
            summary=result["summary"],
            warnings=warnings,
            is_skin=result.get("is_skin", True),
            skin_ratio=result.get("skin_ratio", 0.0),
            detection_count=len(result["detections"]),
        )
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)


# ── RAG Ask (stateless) ────────────────────────────────────────────

@app.post("/api/ask", response_model=AskResponse)
async def ask_rag(payload: AskRequest) -> AskResponse:
    answer, contexts = await run_in_threadpool(
        rag_service.answer,
        question=payload.question,
        analysis_summary=payload.analysis_summary,
    )
    return AskResponse(answer=answer, contexts=contexts)


# ── Conversations CRUD ──────────────────────────────────────────────

@app.post("/api/conversations", response_model=ConversationItem)
def create_conversation(
    payload: ConversationCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ConversationItem:
    ensure_database(db)
    item = db_service.create_conversation(db, payload.client_id, payload.title)
    db_service.ensure_client(db, payload.client_id, request.headers.get("user-agent"))
    db.commit()
    return ConversationItem(**db_service.conversation_to_dict(item))


@app.get("/api/conversations", response_model=list[ConversationItem])
def list_conversations(
    client_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[ConversationItem]:
    ensure_database(db)
    items = db_service.list_conversations(db, client_id, limit=limit, offset=offset)
    db.commit()
    return [ConversationItem(**db_service.conversation_to_dict(item)) for item in items]


@app.get("/api/conversations/search", response_model=list[ConversationItem])
def search_conversations(
    client_id: str,
    q: str = "",
    db: Session = Depends(get_db),
) -> list[ConversationItem]:
    """Search conversations by title or summary."""
    ensure_database(db)
    if not q.strip():
        items = db_service.list_conversations(db, client_id)
    else:
        items = db_service.search_conversations(db, client_id, q.strip())
    db.commit()
    return [ConversationItem(**db_service.conversation_to_dict(item)) for item in items]


@app.get("/api/conversations/{conversation_id}/messages", response_model=list[MessageItem])
def list_conversation_messages(
    conversation_id: str,
    client_id: str,
    db: Session = Depends(get_db),
) -> list[MessageItem]:
    ensure_database(db)
    conversation = db_service.get_conversation_for_client(db, conversation_id, client_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    messages = db_service.list_messages(db, conversation_id)
    return [MessageItem(**db_service.message_to_dict(item)) for item in messages]


@app.patch("/api/conversations/{conversation_id}", response_model=ConversationItem)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    db: Session = Depends(get_db),
) -> ConversationItem:
    """Rename a conversation."""
    ensure_database(db)
    conversation = db_service.get_conversation_for_client(db, conversation_id, payload.client_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if payload.title is not None:
        db_service.update_conversation_title(db, conversation_id, payload.title)
    db.commit()
    # Reload to get updated values
    conversation = db_service.get_conversation_for_client(db, conversation_id, payload.client_id)
    return ConversationItem(**db_service.conversation_to_dict(conversation))


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    client_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Soft-delete a conversation."""
    ensure_database(db)
    success = db_service.delete_conversation(db, conversation_id, client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.commit()
    return {"status": "ok"}


# ── Image helpers ───────────────────────────────────────────────────

def _save_base64_image(data_b64: str, prefix: str = "user") -> str:
    """Decode a base64 image string and save it to UPLOAD_DIR. Return the relative URL path."""
    # Strip data URI prefix if present (e.g. "data:image/png;base64,...")
    if "," in data_b64:
        data_b64 = data_b64.split(",", 1)[1]
    raw = base64.b64decode(data_b64)
    # Detect format
    try:
        with Image.open(io.BytesIO(raw)) as img:
            fmt = (img.format or "JPEG").lower()
    except Exception:
        fmt = "jpeg"
    ext_map = {"jpeg": ".jpg", "png": ".png", "bmp": ".bmp", "webp": ".webp"}
    ext = ext_map.get(fmt, ".jpg")
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(raw)
    return f"/uploads/{filename}"


def _render_and_save_analysis_image(original_image_path: str, detections: list) -> str:
    """Render bounding boxes on the original image and save the result. Return URL path."""
    # Read the original image from the uploads directory
    abs_path = str(UPLOAD_DIR / Path(original_image_path).name)
    image_bgr = cv2.imread(abs_path)
    if image_bgr is None:
        return ""

    h, w = image_bgr.shape[:2]
    for idx, det in enumerate(detections):
        bbox = det.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox
        color = (0, 29, 225) if idx % 2 == 0 else (110, 118, 15)  # BGR colors
        cv2.rectangle(image_bgr, (x1, y1), (x2, y2), color, 2)
        label = f"{det.get('lesion_type', 'unknown')} {det.get('confidence', 0):.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_y = max(0, y1 - 6)
        cv2.rectangle(image_bgr, (x1, label_y - th - 4), (x1 + tw + 6, label_y + 2), color, -1)
        cv2.putText(image_bgr, label, (x1 + 3, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    filename = f"analysis_{uuid.uuid4().hex[:12]}.jpg"
    out_path = UPLOAD_DIR / filename
    cv2.imwrite(str(out_path), image_bgr)
    return f"/uploads/{filename}"


def _extract_label_hints(analysis: dict | None) -> list[str] | None:
    """Extract disease label codes from analysis detections for metadata filtering."""
    if not analysis:
        return None
    detections = analysis.get("detections") or []
    if not detections:
        return None

    # Map common lesion_type values back to HAM10000 codes
    type_to_code = {
        "melanoma": "mel",
        "mel": "mel",
        "nevus": "nv",
        "melanocytic_nevus": "nv",
        "nv": "nv",
        "basal_cell_carcinoma": "bcc",
        "bcc": "bcc",
        "benign_keratosis": "bkl",
        "bkl": "bkl",
        "actinic_keratosis": "akiec",
        "akiec": "akiec",
        "dermatofibroma": "df",
        "df": "df",
        "vascular_lesion": "vasc",
        "vasc": "vasc",
    }

    codes = set()
    for det in detections:
        lesion_type = (det.get("lesion_type") or "").lower().strip()
        code = type_to_code.get(lesion_type)
        if code:
            codes.add(code)
    return list(codes) if codes else None


# ── Chat with Memory ────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_memory(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ChatResponse:
    ensure_database(db)
    db_service.ensure_client(db, payload.client_id, request.headers.get("user-agent"))

    is_new_conversation = not payload.conversation_id

    if payload.conversation_id:
        conversation = db_service.get_conversation_for_client(
            db,
            payload.conversation_id,
            payload.client_id,
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        title = payload.message[:72] if payload.message else "Cuộc trò chuyện mới"
        conversation = db_service.create_conversation(db, payload.client_id, title)

    # Validate base64 image size before decoding
    user_image_path = None
    if payload.image_base64:
        b64_data = payload.image_base64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        # Base64 encodes 3 bytes as 4 chars; rough size estimate
        estimated_bytes = len(b64_data) * 3 // 4
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if estimated_bytes > max_bytes:
            raise HTTPException(status_code=413, detail="Image data is too large.")
        try:
            user_image_path = await run_in_threadpool(
                _save_base64_image, payload.image_base64, "user"
            )
        except Exception:
            logger.debug("Failed to save user image", exc_info=True)

    history = db_service.get_recent_history(db, conversation.id, limit=12)
    user_message = db_service.add_message(
        db,
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
        analysis_summary=payload.analysis_summary,
        metadata={"has_analysis": bool(payload.analysis)},
        image_path=user_image_path,
    )

    # Save analysis result and render bounding-box image (async, non-blocking)
    analysis_image_path = None
    if payload.analysis:
        db_service.add_image_analysis(db, user_message.id, payload.analysis)
        if user_image_path and payload.analysis.get("detections"):
            try:
                analysis_image_path = await run_in_threadpool(
                    _render_and_save_analysis_image,
                    user_image_path,
                    payload.analysis["detections"],
                )
            except Exception:
                logger.debug("Failed to render analysis image", exc_info=True)

    is_not_skin_analysis = bool(payload.analysis and payload.analysis.get("is_skin") is False)
    is_no_detection_analysis = bool(
        payload.analysis
        and payload.analysis.get("is_skin") is True
        and not (payload.analysis.get("detections") or [])
    )
    if is_not_skin_analysis:
        answer = NOT_SKIN_ANSWER
        contexts = []
    elif is_no_detection_analysis:
        answer = NO_DETECTION_ANSWER
        contexts = []
    else:
        label_hints = _extract_label_hints(payload.analysis)
        conv_summary = conversation.summary if not is_new_conversation else None

        answer, contexts = await run_in_threadpool(
            rag_service.answer_with_history,
            question=payload.message,
            chat_history=history,
            analysis_summary=payload.analysis_summary,
            label_hints=label_hints,
            conversation_summary=conv_summary,
        )

    assistant_metadata: dict = {"contexts": contexts}
    if payload.analysis:
        assistant_metadata["image_analysis"] = {
            "pipeline": payload.analysis.get("pipeline"),
            "detector": payload.analysis.get("detector"),
            "classifier": payload.analysis.get("classifier"),
            "summary": payload.analysis.get("summary"),
            "is_skin": payload.analysis.get("is_skin"),
            "skin_ratio": payload.analysis.get("skin_ratio"),
            "detections": payload.analysis.get("detections") or [],
            "warnings": payload.analysis.get("warnings") or [],
        }

    assistant_message = db_service.add_message(
        db,
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        metadata=assistant_metadata,
        image_path=analysis_image_path,
    )

    # Auto-generate title for new conversations using LLM
    if is_new_conversation and not is_not_skin_analysis and not is_no_detection_analysis:
        try:
            ai_title = await run_in_threadpool(
                rag_service.generate_conversation_title, payload.message, answer
            )
            db_service.update_conversation_title(db, conversation.id, ai_title)
        except Exception:
            logger.debug("Auto-title generation failed", exc_info=True)

    # Update conversation summary on first exchange and every 4 messages after
    all_messages = db_service.list_messages(db, conversation.id)
    msg_count = len(all_messages)
    should_summarize = is_new_conversation or (msg_count >= 4 and msg_count % 4 == 0)
    if should_summarize and not is_not_skin_analysis and not is_no_detection_analysis:
        try:
            msg_dicts = [{"role": m.role, "content": m.content} for m in all_messages]
            summary = await run_in_threadpool(
                rag_service.generate_conversation_summary, msg_dicts
            )
            if summary:
                db_service.update_conversation_summary(db, conversation.id, summary)
        except Exception:
            logger.debug("Auto-summary generation failed", exc_info=True)

    db.commit()
    return ChatResponse(
        conversation_id=conversation.id,
        user_message=MessageItem(**db_service.message_to_dict(user_message)),
        assistant_message=MessageItem(**db_service.message_to_dict(assistant_message)),
        answer=answer,
        contexts=contexts,
    )


# ── Admin endpoints ─────────────────────────────────────────────────

@app.get("/api/admin/registry", response_model=RegistryConfigResponse)
def get_admin_registry(
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RegistryConfigResponse:
    ensure_database(db)
    active = db_service.get_active_registry_config(db)
    if active is not None:
        return RegistryConfigResponse(source="database", config=active.config)
    return RegistryConfigResponse(source="file", config=model_registry.to_dict())


@app.put("/api/admin/registry", response_model=RegistryConfigResponse)
def update_admin_registry(
    payload: RegistryConfigUpdate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RegistryConfigResponse:
    ensure_database(db)
    try:
        model_registry.reload_from_data(payload.config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid registry config: {exc}") from exc

    db_service.save_registry_config(db, payload.name, payload.config, activate=payload.activate)
    db_service.sync_pipeline_presets(db, payload.config)
    db.commit()
    return RegistryConfigResponse(source="database", config=payload.config)


@app.post("/api/admin/registry/export")
def export_admin_registry(
    _: None = Depends(require_admin),
) -> dict:
    return model_registry.to_dict()


@app.post("/api/admin/knowledge/upload")
async def upload_knowledge_document(file: UploadFile = File(...)) -> dict:
    """Upload a knowledge document and refresh the persistent RAG vector index."""
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported knowledge file type. Supported: {supported}",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    chunks: list[bytes] = []
    total_read = 0
    chunk_size = 64 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > max_bytes:
            raise HTTPException(status_code=413, detail="Uploaded file is too large.")
        chunks.append(chunk)

    if total_read == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    safe_stem = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in Path(original_name).stem
    ).strip("_") or "knowledge"
    filename = f"{safe_stem}_{uuid.uuid4().hex[:8]}{suffix}"
    target_path = RAG_DOCS_DIR / filename
    target_path.write_bytes(b"".join(chunks))

    try:
        indexed_chunks = await run_in_threadpool(rag_service.build_index, False)
    except Exception as exc:
        try:
            target_path.unlink(missing_ok=True)
        except Exception:
            logger.debug("Failed to remove knowledge upload after index error", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Index refresh failed: {exc}") from exc

    logger.info("Knowledge document uploaded: %s (%d bytes)", target_path, total_read)
    return {
        "status": "ok",
        "filename": filename,
        "bytes": total_read,
        "indexed_chunks": indexed_chunks,
        "docs_dir": str(RAG_DOCS_DIR),
    }


@app.get("/api/admin/chat-history", response_model=AdminChatHistoryPage)
def list_admin_chat_history(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
) -> AdminChatHistoryPage:
    """Return paginated chat conversations for the admin page."""
    ensure_database(db)
    page = max(1, page)
    per_page = min(max(1, per_page), 100)
    total = db_service.count_admin_conversations(db)
    total_pages = max(1, (total + per_page - 1) // per_page)
    if total and page > total_pages:
        page = total_pages

    items = db_service.list_admin_conversations(
        db,
        limit=per_page,
        offset=(page - 1) * per_page,
    )
    return AdminChatHistoryPage(
        items=[
            AdminConversationItem(**db_service.admin_conversation_to_dict(item, message_count))
            for item, message_count in items
        ],
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
    )


@app.get("/api/admin/chat-history/{conversation_id}", response_model=AdminConversationDetail)
def get_admin_chat_history_detail(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> AdminConversationDetail:
    """Return a full chat transcript for an admin modal."""
    ensure_database(db)
    conversation_row = db_service.get_admin_conversation(db, conversation_id)
    if conversation_row is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conversation, message_count = conversation_row
    messages = db_service.list_messages(db, conversation_id)
    return AdminConversationDetail(
        conversation=AdminConversationItem(
            **db_service.admin_conversation_to_dict(conversation, message_count)
        ),
        messages=[MessageItem(**db_service.message_to_dict(item)) for item in messages],
    )


# ── LLM backend admin (no token required, same as config) ───────────

@app.get("/api/admin/llm", response_model=LLMSettingsResponse)
def get_llm_settings() -> LLMSettingsResponse:
    """Return current RAG LLM backend configuration and live status."""
    # Check Ollama reachability (fast timeout, non-blocking for UI)
    ollama_available = False
    if rag_service._ollama is not None:
        try:
            ollama_available = rag_service._ollama.is_available()
        except Exception:
            pass

    # Determine what backend is actually active right now
    backend = rag_service.rag_llm_backend

    if backend == "ollama":
        active_backend = "ollama" if rag_service._ollama is not None else "none"
    elif backend == "openai":
        active_backend = "openai" if bool(rag_service.openai_api_key) else "none"
    else:
        # "auto": Ollama wins if configured AND reachable, else OpenAI if key set
        if rag_service._ollama is not None and ollama_available:
            active_backend = "ollama"
        elif bool(rag_service.openai_api_key):
            active_backend = "openai"
        else:
            active_backend = "none"

    return LLMSettingsResponse(
        backend=backend,
        active_backend=active_backend,
        openai_model=rag_service.openai_model,
        openai_configured=bool(rag_service.openai_api_key),
        ollama_base_url=rag_service._ollama.base_url if rag_service._ollama else "",
        ollama_model=rag_service._ollama.model if rag_service._ollama else settings.ollama_model,
        ollama_available=ollama_available,
    )


@app.put("/api/admin/llm", response_model=LLMSettingsResponse)
def update_llm_settings(payload: LLMSettingsUpdate) -> LLMSettingsResponse:
    """Switch RAG LLM backend at runtime without restarting the server.

    Allowed values: 'openai', 'ollama', 'auto'
    """
    rag_service.rag_llm_backend = payload.backend
    logger.info("RAG LLM backend switched to: %s", payload.backend)
    return get_llm_settings()


# ── Public admin endpoints (no token required) ──────────────────────

def _build_default_pipeline_response() -> DefaultPipelineResponse:
    """Build the typed response from the in-memory registry."""
    config = model_registry.to_dict()
    pipelines = config.get("pipelines", {})
    default = pipelines.get("default", {})
    return DefaultPipelineResponse(
        detector=default.get("detector", ""),
        classifier=default.get("classifier", ""),
        classifier_input=default.get("classifier_input", "full"),
        available_detectors=sorted(model_registry.detectors.keys()),
        available_classifiers=sorted(model_registry.classifiers.keys()),
    )


@app.get("/api/admin/config")
def get_admin_config_public() -> dict:
    """Return the full registry config (used by admin UI for cards)."""
    return model_registry.to_dict()


@app.get("/api/admin/default-pipeline", response_model=DefaultPipelineResponse)
def get_default_pipeline() -> DefaultPipelineResponse:
    """Return current default pipeline + available options for the dropdowns.

    Frontend only needs this for the config form — no full registry parsing.
    """
    return _build_default_pipeline_response()


@app.put("/api/admin/default-pipeline", response_model=DefaultPipelineResponse)
def update_default_pipeline(
    payload: DefaultPipelineUpdate,
    db: Session = Depends(get_db),
) -> DefaultPipelineResponse:
    """Update the default pipeline with strict validation.

    - detector and classifier must exist in the registry
    - classifier_input is constrained to 'full' or 'crop' (schema-level)
    - changes are persisted to DB and the in-memory registry is reloaded
    """
    ensure_database(db)

    # Validate names against the live registry
    if payload.detector not in model_registry.detectors:
        raise HTTPException(
            status_code=400,
            detail=f"Detector '{payload.detector}' không tồn tại. "
                   f"Available: {sorted(model_registry.detectors.keys())}",
        )
    if payload.classifier not in model_registry.classifiers:
        raise HTTPException(
            status_code=400,
            detail=f"Classifier '{payload.classifier}' không tồn tại. "
                   f"Available: {sorted(model_registry.classifiers.keys())}",
        )

    # Update only the 'default' pipeline; keep detectors/classifiers untouched
    config = model_registry.to_dict()
    config["pipelines"] = config.get("pipelines", {})
    config["pipelines"]["default"] = {
        "detector": payload.detector,
        "classifier": payload.classifier,
        "classifier_input": payload.classifier_input,
    }

    try:
        model_registry.reload_from_data(config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid config: {exc}") from exc

    db_service.save_registry_config(db, "admin-active", config, activate=True)
    db_service.sync_pipeline_presets(db, config)
    db.commit()

    logger.info(
        "Default pipeline updated: detector=%s, classifier=%s, input=%s",
        payload.detector, payload.classifier, payload.classifier_input,
    )
    return _build_default_pipeline_response()


@app.post("/api/admin/default-pipeline/reset", response_model=DefaultPipelineResponse)
def reset_default_pipeline(db: Session = Depends(get_db)) -> DefaultPipelineResponse:
    """Reset registry to the file on disk (model_registry.json).

    Useful when DB has stale config from a previous version
    (e.g. references to removed classifiers like cnn_keras).
    """
    ensure_database(db)
    try:
        model_registry._load()  # reload from JSON file
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reset failed: {exc}") from exc

    config = model_registry.to_dict()
    db_service.save_registry_config(db, "file-seed", config, activate=True)
    db_service.sync_pipeline_presets(db, config)
    db.commit()
    logger.info("Registry reset to file-seed.")
    return _build_default_pipeline_response()


# Backward compat: keep the old endpoint as an alias so older frontends still work.
@app.put("/api/admin/config/default-pipeline", response_model=DefaultPipelineResponse, deprecated=True)
def update_default_pipeline_legacy(
    payload: DefaultPipelineUpdate,
    db: Session = Depends(get_db),
) -> DefaultPipelineResponse:
    """Deprecated. Use PUT /api/admin/default-pipeline instead."""
    return update_default_pipeline(payload, db)


# ── Frontend serving ────────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@app.get("/")
def index() -> FileResponse:
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(
        index_file,
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/admin")
def admin_index(request: Request) -> FileResponse:
    if request.cookies.get("admin_page_auth") != _admin_page_cookie_value():
        login_file = FRONTEND_DIR / "admin-login.html"
        if not login_file.exists():
            raise HTTPException(status_code=404, detail="Admin login frontend not found")
        return FileResponse(login_file)

    admin_file = FRONTEND_DIR / "admin.html"
    if not admin_file.exists():
        raise HTTPException(status_code=404, detail="Admin frontend not found")
    return FileResponse(admin_file)


def _admin_page_cookie_value() -> str:
    return hashlib.sha256(
        f"admin-page:{settings.admin_page_password}".encode("utf-8")
    ).hexdigest()


@app.post("/admin/login")
def admin_login(password: str = Form("")) -> RedirectResponse:
    if not hmac.compare_digest(password, settings.admin_page_password):
        return RedirectResponse("/admin?error=1", status_code=303)

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        "admin_page_auth",
        _admin_page_cookie_value(),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return response


# Mount uploads directory for serving saved images
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
