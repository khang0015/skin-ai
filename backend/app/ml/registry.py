from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .adapters.keras_classifier import KerasImageClassifier
from .adapters.openai_classifier import OpenAIVisionClassifier
from .adapters.hf_classifier import HuggingFaceVisionClassifier
from .adapters.pytorch_classifier import TorchCheckpointClassifier
from .adapters.ultralytics_yolo import UltralyticsYoloDetector
from .base import BaseClassifier, BaseDetector
from ..config import settings


@dataclass(frozen=True)
class PipelineConfig:
    name: str
    detector_name: str
    classifier_name: str
    classifier_input: str = "crop"  # 'crop' (bbox crop) | 'full' (original image)


class ModelRegistry:
    def __init__(self, registry_path: str) -> None:
        self.registry_path = Path(registry_path)
        self.raw_config: dict = {}
        self.detectors: dict[str, BaseDetector] = {}
        self.classifiers: dict[str, BaseClassifier] = {}
        self.pipelines: dict[str, PipelineConfig] = {}
        self._load()

    def _load(self) -> None:
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Model registry file not found: {self.registry_path}")

        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.reload_from_data(data)

    def reload_from_data(self, data: dict) -> None:
        self.raw_config = data
        self.detectors = {}
        self.classifiers = {}
        self.pipelines = {}

        for name, cfg in data.get("detectors", {}).items():
            kind = cfg.get("kind")
            model_path = cfg.get("model_path")

            if kind == "ultralytics_yolo":
                self.detectors[name] = UltralyticsYoloDetector(name=name, model_path=model_path)
            else:
                raise ValueError(f"Unsupported detector kind: {kind}")

        for name, cfg in data.get("classifiers", {}).items():
            kind = cfg.get("kind")
            model_path = cfg.get("model_path")
            input_size = int(cfg.get("input_size", 224))
            class_names = tuple(cfg.get("class_names", []))
            mean = cfg.get("mean")
            std = cfg.get("std")

            if kind == "keras":
                self.classifiers[name] = KerasImageClassifier(
                    name=name,
                    model_path=model_path,
                    class_names=class_names,
                    input_size=input_size,
                )
            elif kind == "pytorch_checkpoint":
                self.classifiers[name] = TorchCheckpointClassifier(
                    name=name,
                    model_path=model_path,
                    class_names=class_names,
                    input_size=input_size,
                    model_factory=cfg.get("model_factory"),
                    mean=tuple(mean) if mean else None,
                    std=tuple(std) if std else None,
                )
            elif kind == "openai_vision":
                from .adapters.openai_classifier import HAM10000_CLASSES
                self.classifiers[name] = OpenAIVisionClassifier(
                    name=name,
                    api_key=settings.openai_api_key,
                    model=cfg.get("model", settings.openai_model),
                    class_names=class_names if class_names else HAM10000_CLASSES,
                )
            elif kind == "huggingface_vision":
                from .adapters.openai_classifier import HAM10000_CLASSES as HF_CLASSES
                self.classifiers[name] = HuggingFaceVisionClassifier(
                    name=name,
                    api_key=settings.hf_api_key,
                    model=cfg.get("model", settings.hf_model),
                    class_names=class_names if class_names else HF_CLASSES,
                )
            else:
                raise ValueError(f"Unsupported classifier kind: {kind}")

        for name, cfg in data.get("pipelines", {}).items():
            classifier_input = str(cfg.get("classifier_input", "crop")).strip().lower()
            if classifier_input not in {"crop", "full"}:
                raise ValueError(
                    f"Unsupported classifier_input '{classifier_input}' in pipeline '{name}'. "
                    "Allowed: 'crop', 'full'."
                )
            self.pipelines[name] = PipelineConfig(
                name=name,
                detector_name=cfg["detector"],
                classifier_name=cfg["classifier"],
                classifier_input=classifier_input,
            )

    def get_pipeline(self, pipeline_name: str) -> PipelineConfig:
        if pipeline_name not in self.pipelines:
            options = ", ".join(sorted(self.pipelines.keys())) or "none"
            raise KeyError(f"Pipeline '{pipeline_name}' not found. Available: {options}")
        return self.pipelines[pipeline_name]

    def to_dict(self) -> dict:
        return self.raw_config
