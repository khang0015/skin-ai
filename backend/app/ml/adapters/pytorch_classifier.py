from __future__ import annotations

import importlib
import logging
import threading
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np

from ..base import BaseClassifier
from ..types import Classification

logger = logging.getLogger(__name__)


def _resolve_factory(factory_path: str) -> Callable[[], Any]:
    module_name, func_name = factory_path.split(":", maxsplit=1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    if not callable(func):
        raise TypeError(f"Factory is not callable: {factory_path}")
    return func


class TorchCheckpointClassifier(BaseClassifier):
    def __init__(
        self,
        name: str,
        model_path: str,
        class_names: tuple[str, ...],
        input_size: int = 224,
        model_factory: str | None = None,
        mean: tuple[float, float, float] | None = None,
        std: tuple[float, float, float] | None = None,
    ) -> None:
        super().__init__(name=name, model_path=model_path, class_names=class_names, input_size=input_size)
        self.model_factory = model_factory
        self.mean = mean
        self.std = std
        self._model: Any | None = None
        self._torch = None
        # Resolved class_names after checkpoint inspection — immutable after load
        self._resolved_class_names: tuple[str, ...] = class_names
        self._load_lock = threading.Lock()

    def _infer_num_classes(self, state_dict: dict[str, Any]) -> int | None:
        weight = state_dict.get("classifier.weight")
        if hasattr(weight, "shape") and len(weight.shape) >= 1:
            return int(weight.shape[0])
        return None

    def _load(self) -> Any | None:
        if self._model is not None:
            return self._model

        with self._load_lock:
            # Double-checked locking
            if self._model is not None:
                return self._model

            path = Path(self.model_path)
            if not path.exists():
                self.last_warning = f"Classifier model not found: {path}"
                return None

            torch = importlib.import_module("torch")
            self._torch = torch
            device = torch.device("cpu")

            checkpoint = torch.load(str(path), map_location=device)

            if self.model_factory:
                factory = _resolve_factory(self.model_factory)
                try:
                    model = factory(num_classes=len(self.class_names))
                except TypeError:
                    model = factory()

                state_dict = None
                if isinstance(checkpoint, dict):
                    if "state_dict" in checkpoint:
                        state_dict = checkpoint["state_dict"]
                    elif "model_state" in checkpoint:
                        state_dict = checkpoint["model_state"]
                    else:
                        state_dict = checkpoint

                if state_dict is None or not isinstance(state_dict, dict):
                    self.last_warning = (
                        "Torch checkpoint format is unsupported for factory loading. "
                        "Expected a dict-like state_dict or model_state."
                    )
                    return None

                inferred_classes = self._infer_num_classes(state_dict)

                # Resolve class_names WITHOUT mutating self.class_names
                resolved_names = self.class_names
                if inferred_classes and inferred_classes != len(self.class_names):
                    if inferred_classes > len(self.class_names):
                        extras = tuple(
                            f"class_{i}"
                            for i in range(len(self.class_names), inferred_classes)
                        )
                        resolved_names = (*self.class_names, *extras)
                    logger.warning(
                        "Classifier checkpoint has %d classes but config has %d. "
                        "Using checkpoint count for loading.",
                        inferred_classes,
                        len(self.class_names),
                    )
                    self.last_warning = (
                        f"Checkpoint class count ({inferred_classes}) differs from "
                        f"config ({len(self.class_names)}). Extra classes padded."
                    )

                # Store resolved names separately — never mutate self.class_names
                self._resolved_class_names = resolved_names

                if inferred_classes:
                    try:
                        model = factory(num_classes=inferred_classes)
                    except TypeError:
                        model = factory()

                missing, unexpected = model.load_state_dict(state_dict, strict=False)
                if missing:
                    logger.warning(
                        "Torch checkpoint missing keys (%d): %s",
                        len(missing),
                        missing[:5],
                    )
                if unexpected:
                    logger.warning(
                        "Torch checkpoint unexpected keys (%d): %s",
                        len(unexpected),
                        unexpected[:5],
                    )
            else:
                model = checkpoint
                self._resolved_class_names = self.class_names

            if hasattr(model, "eval"):
                model.eval()
            self._model = model

        return self._model

    def classify(self, image_bgr: np.ndarray) -> Classification:
        model = self._load()
        if model is None or self._torch is None:
            return Classification(label="unknown", confidence=0.0)

        torch = self._torch
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.input_size, self.input_size))
        tensor_np = resized.astype("float32") / 255.0
        if self.mean and self.std:
            mean = np.array(self.mean, dtype="float32")
            std = np.array(self.std, dtype="float32")
            tensor_np = (tensor_np - mean) / std
        tensor_np = np.transpose(tensor_np, (2, 0, 1))
        tensor = torch.tensor(tensor_np).unsqueeze(0)

        with torch.no_grad():
            output = model(tensor)
            if isinstance(output, (list, tuple)):
                output = output[0]
            scores = torch.softmax(output, dim=1)[0]
            idx = int(torch.argmax(scores).item())
            confidence = float(scores[idx].item())

        names = self._resolved_class_names
        label = names[idx] if idx < len(names) else f"class_{idx}"
        self.last_warning = None
        return Classification(label=label, confidence=confidence)
