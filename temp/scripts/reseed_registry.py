"""Wipe model_registry_configs and pipeline_presets in the database, then
re-seed from the current model_registry.json file.

Usage:
    .venv\\Scripts\\python.exe scripts\\reseed_registry.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db.session import SessionLocal, is_database_configured
from backend.app.db.models import ModelRegistryConfig, PipelinePreset
from backend.app.ml.registry import ModelRegistry
from backend.app.services import db_service
from backend.app.config import settings


def main() -> None:
    if not is_database_configured():
        print("DATABASE_URL is not configured — nothing to do.")
        return

    # Load fresh config from JSON file
    registry = ModelRegistry(settings.model_registry_path)
    fresh_config = registry.to_dict()

    print("File config:")
    print("  detectors:   ", list(fresh_config.get("detectors", {}).keys()))
    print("  classifiers: ", list(fresh_config.get("classifiers", {}).keys()))
    print("  pipelines:   ", list(fresh_config.get("pipelines", {}).keys()))

    db = SessionLocal()
    try:
        # Wipe old configs and pipeline presets
        deleted_configs = db.query(ModelRegistryConfig).delete()
        deleted_presets = db.query(PipelinePreset).delete()
        db.flush()
        print(f"Deleted {deleted_configs} stale registry config(s).")
        print(f"Deleted {deleted_presets} stale pipeline preset(s).")

        # Seed fresh
        db_service.save_registry_config(
            db, name="file-seed", config=fresh_config, activate=True,
        )
        db_service.sync_pipeline_presets(db, fresh_config)
        db.commit()
        print("✓ Database re-seeded from model_registry.json")
    finally:
        db.close()


if __name__ == "__main__":
    main()
