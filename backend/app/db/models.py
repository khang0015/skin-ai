from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


def new_uuid() -> str:
    return str(uuid4())


class AnonymousClient(Base):
    __tablename__ = "anonymous_clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    client_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("anonymous_clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    client: Mapped[AnonymousClient] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    image_analysis: Mapped["ImageAnalysis | None"] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ImageAnalysis(Base):
    __tablename__ = "image_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    detector_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    classifier_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_skin: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    skin_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    detections: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    warnings: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped[Message] = relationship(back_populates="image_analysis")


class PipelinePreset(Base):
    __tablename__ = "pipeline_presets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    detector_name: Mapped[str] = mapped_column(Text, nullable=False)
    classifier_name: Mapped[str] = mapped_column(Text, nullable=False)
    classifier_input: Mapped[str] = mapped_column(Text, default="full", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ModelRegistryConfig(Base):
    __tablename__ = "model_registry_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


Index("idx_conversations_client_updated", Conversation.client_id, Conversation.updated_at.desc())
Index("idx_conversations_client_deleted", Conversation.client_id, Conversation.is_deleted)
Index("idx_messages_conversation_created", Message.conversation_id, Message.created_at.asc())
Index("idx_model_registry_configs_active", ModelRegistryConfig.is_active)
