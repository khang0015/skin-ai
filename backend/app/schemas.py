from __future__ import annotations

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    lesion_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int]


class AnalyzeResponse(BaseModel):
    pipeline: str
    detector: str
    classifier: str
    detections: list[DetectionResult]
    summary: str
    warnings: list[str] = []
    is_skin: bool = True
    skin_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    detection_count: int = 0  # number of raw detections before confidence filtering


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    analysis_summary: str | None = None


class AskResponse(BaseModel):
    answer: str
    contexts: list[str]


class ClientRequest(BaseModel):
    client_id: str = Field(min_length=8)


class ConversationCreateRequest(ClientRequest):
    title: str | None = None


class ConversationUpdateRequest(ClientRequest):
    title: str | None = None


class ConversationItem(BaseModel):
    id: str
    client_id: str
    title: str | None = None
    summary: str | None = None
    created_at: str
    updated_at: str


class MessageItem(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    image_path: str | None = None
    analysis_summary: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: str


class ChatRequest(ClientRequest):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    analysis_summary: str | None = None
    analysis: dict | None = None
    image_base64: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageItem | None = None
    assistant_message: MessageItem | None = None
    answer: str
    contexts: list[str]


class RegistryConfigResponse(BaseModel):
    source: str
    config: dict


class RegistryConfigUpdate(BaseModel):
    name: str = "admin-active"
    config: dict
    activate: bool = True


# ── Default pipeline update (validated) ──────────────────────────────

class DefaultPipelineUpdate(BaseModel):
    """Validated payload for changing the default pipeline.

    The detector and classifier names must exist in the current registry —
    the endpoint enforces this at runtime. classifier_input is restricted
    to 'full' or 'crop' at the schema level.
    """
    detector: str = Field(min_length=1)
    classifier: str = Field(min_length=1)
    classifier_input: str = Field(pattern="^(full|crop)$", default="full")


class DefaultPipelineResponse(BaseModel):
    """Response for default-pipeline endpoint — typed and explicit."""
    detector: str
    classifier: str
    classifier_input: str
    available_detectors: list[str]
    available_classifiers: list[str]
    available_inputs: list[str] = ["full", "crop"]


# ── LLM backend settings ─────────────────────────────────────────────

class LLMSettingsResponse(BaseModel):
    """Current RAG LLM backend configuration."""
    backend: str          # "openai" | "ollama" | "auto"
    active_backend: str   # resolved backend actually in use: "openai" | "ollama" | "none"
    openai_model: str
    openai_configured: bool
    ollama_base_url: str
    ollama_model: str
    ollama_available: bool


class LLMSettingsUpdate(BaseModel):
    """Update RAG LLM backend at runtime (no server restart needed)."""
    backend: str = Field(
        description="Which LLM to use: 'openai', 'ollama', or 'auto'",
        pattern="^(openai|ollama|auto)$",
    )
