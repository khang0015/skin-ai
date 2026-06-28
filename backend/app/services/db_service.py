from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from ..db.models import (
    AnonymousClient,
    Conversation,
    ImageAnalysis,
    Message,
    ModelRegistryConfig,
    PipelinePreset,
)


def dt(value: datetime | None) -> str:
    if not value:
        return ""
    # Always emit an explicit timezone to avoid clients interpreting naive
    # datetimes as local time (causes a consistent 7h skew on UTC+7 machines).
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value_utc = value.astimezone(timezone.utc)
    return value_utc.isoformat().replace("+00:00", "Z")


def ensure_client(db: Session, client_id: str, user_agent: str | None = None) -> AnonymousClient:
    client = db.get(AnonymousClient, client_id)
    if client is None:
        client = AnonymousClient(id=client_id, user_agent=user_agent)
        db.add(client)
        db.flush()
    else:
        client.user_agent = user_agent or client.user_agent
    return client


def create_conversation(db: Session, client_id: str, title: str | None = None) -> Conversation:
    ensure_client(db, client_id)
    conversation = Conversation(client_id=client_id, title=title or "Cuộc trò chuyện mới")
    db.add(conversation)
    db.flush()
    return conversation


def get_conversation_for_client(db: Session, conversation_id: str, client_id: str) -> Conversation | None:
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.client_id == client_id,
        Conversation.is_deleted.is_(False),
    )
    return db.execute(stmt).scalar_one_or_none()


def list_conversations(
    db: Session,
    client_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Conversation]:
    ensure_client(db, client_id)
    stmt = (
        select(Conversation)
        .where(
            Conversation.client_id == client_id,
            Conversation.is_deleted.is_(False),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_admin_conversations(db: Session) -> int:
    stmt = select(func.count(Conversation.id)).where(Conversation.is_deleted.is_(False))
    return db.execute(stmt).scalar_one()


def list_admin_conversations(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> list[tuple[Conversation, int]]:
    stmt = (
        select(Conversation, func.count(Message.id).label("message_count"))
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.is_deleted.is_(False))
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [(conversation, int(message_count or 0)) for conversation, message_count in db.execute(stmt).all()]


def get_admin_conversation(db: Session, conversation_id: str) -> tuple[Conversation, int] | None:
    stmt = (
        select(Conversation, func.count(Message.id).label("message_count"))
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(
            Conversation.id == conversation_id,
            Conversation.is_deleted.is_(False),
        )
        .group_by(Conversation.id)
    )
    row = db.execute(stmt).one_or_none()
    if row is None:
        return None
    conversation, message_count = row
    return conversation, int(message_count or 0)


def search_conversations(
    db: Session,
    client_id: str,
    query: str,
    limit: int = 30,
) -> list[Conversation]:
    """Search conversations by title or summary content."""
    ensure_client(db, client_id)
    like_pattern = f"%{query}%"
    stmt = (
        select(Conversation)
        .where(
            Conversation.client_id == client_id,
            Conversation.is_deleted.is_(False),
            or_(
                Conversation.title.ilike(like_pattern),
                Conversation.summary.ilike(like_pattern),
            ),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def delete_conversation(db: Session, conversation_id: str, client_id: str) -> bool:
    """Soft-delete a conversation."""
    conversation = get_conversation_for_client(db, conversation_id, client_id)
    if conversation is None:
        return False
    conversation.is_deleted = True
    db.flush()
    return True


def update_conversation_title(db: Session, conversation_id: str, title: str) -> None:
    db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(title=title, updated_at=datetime.now(timezone.utc))
    )
    db.flush()


def update_conversation_summary(db: Session, conversation_id: str, summary: str) -> None:
    db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(summary=summary)
    )
    db.flush()


def list_messages(
    db: Session,
    conversation_id: str,
    limit: int | None = None,
    offset: int = 0,
) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    if offset:
        stmt = stmt.offset(offset)
    if limit:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    analysis_summary: str | None = None,
    metadata: dict | None = None,
    image_path: str | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        image_path=image_path,
        analysis_summary=analysis_summary,
        message_metadata=metadata or {},
    )
    db.add(message)
    db.flush()
    db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=datetime.now(timezone.utc))
    )
    return message


def add_image_analysis(db: Session, message_id: str, analysis: dict) -> ImageAnalysis:
    item = ImageAnalysis(
        message_id=message_id,
        pipeline_name=analysis.get("pipeline"),
        detector_name=analysis.get("detector"),
        classifier_name=analysis.get("classifier"),
        summary=analysis.get("summary"),
        is_skin=analysis.get("is_skin"),
        skin_ratio=analysis.get("skin_ratio"),
        detections=analysis.get("detections") or [],
        warnings=analysis.get("warnings") or [],
    )
    db.add(item)
    db.flush()
    return item


def get_recent_history(db: Session, conversation_id: str, limit: int = 12) -> list[dict[str, str]]:
    """Return the most recent `limit` messages without loading the full history."""
    # Count total messages to compute offset for the last `limit` rows
    from sqlalchemy import func as sa_func
    total: int = db.execute(
        select(sa_func.count(Message.id)).where(Message.conversation_id == conversation_id)
    ).scalar_one()
    offset = max(0, total - limit)
    messages = list_messages(db, conversation_id, limit=limit, offset=offset)
    return [{"role": item.role, "content": item.content} for item in messages]


def message_to_dict(message: Message) -> dict:
    result = {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "image_path": message.image_path,
        "analysis_summary": message.analysis_summary,
        "metadata": message.message_metadata or {},
        "created_at": dt(message.created_at),
    }
    # Include image_analysis data so chat history can render bounding boxes
    ia = message.image_analysis
    if ia is not None:
        result["metadata"]["image_analysis"] = {
            "pipeline": ia.pipeline_name,
            "detector": ia.detector_name,
            "classifier": ia.classifier_name,
            "summary": ia.summary,
            "is_skin": ia.is_skin,
            "skin_ratio": ia.skin_ratio,
            "detections": ia.detections or [],
            "warnings": ia.warnings or [],
        }
    return result


def conversation_to_dict(conversation: Conversation) -> dict:
    return {
        "id": conversation.id,
        "client_id": conversation.client_id,
        "title": conversation.title,
        "summary": conversation.summary,
        "created_at": dt(conversation.created_at),
        "updated_at": dt(conversation.updated_at),
    }


def admin_conversation_to_dict(conversation: Conversation, message_count: int = 0) -> dict:
    result = conversation_to_dict(conversation)
    result["message_count"] = message_count
    return result


def get_active_registry_config(db: Session) -> ModelRegistryConfig | None:
    stmt = select(ModelRegistryConfig).where(ModelRegistryConfig.is_active.is_(True))
    return db.execute(stmt).scalar_one_or_none()


def save_registry_config(db: Session, name: str, config: dict, activate: bool = True) -> ModelRegistryConfig:
    stmt = select(ModelRegistryConfig).where(ModelRegistryConfig.name == name)
    item = db.execute(stmt).scalar_one_or_none()
    if item is None:
        item = ModelRegistryConfig(name=name, config=config, is_active=activate)
        db.add(item)
    else:
        item.config = config
        item.is_active = activate

    if activate:
        db.execute(
            update(ModelRegistryConfig)
            .where(ModelRegistryConfig.name != name)
            .values(is_active=False)
        )
    db.flush()
    return item


def sync_pipeline_presets(db: Session, config: dict) -> None:
    pipelines = config.get("pipelines", {})
    db.query(PipelinePreset).delete()
    for name, pipeline in pipelines.items():
        db.add(
            PipelinePreset(
                name=name,
                detector_name=pipeline.get("detector", ""),
                classifier_name=pipeline.get("classifier", ""),
                classifier_input=pipeline.get("classifier_input", "crop"),
                is_default=name == "default",
                enabled=True,
            )
        )
    db.flush()
