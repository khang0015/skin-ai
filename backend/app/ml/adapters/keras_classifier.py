from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ..base import BaseClassifier
from ..types import Classification


class KerasImageClassifier(BaseClassifier):
    def __init__(self, name: str, model_path: str, class_names: tuple[str, ...], input_size: int = 224) -> None:
        super().__init__(name=name, model_path=model_path, class_names=class_names, input_size=input_size)
        self._model: Any | None = None

    def _load(self) -> Any | None:
        if self._model is not None:
            return self._model

        path = Path(self.model_path)
        if not path.exists():
            self.last_warning = f"Classifier model not found: {path}"
            return None

        keras = importlib.import_module("tensorflow.keras")
        self._model = keras.models.load_model(str(path))
        return self._model

    def classify(self, image_bgr: np.ndarray) -> Classification:
        model = self._load()
        if model is None:
            return Classification(label="unknown", confidence=0.0)

        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.input_size, self.input_size))
        tensor = resized.astype("float32") / 255.0
        tensor = np.expand_dims(tensor, axis=0)

        pred = model.predict(tensor, verbose=0)[0]
        idx = int(np.argmax(pred))
        confidence = float(pred[idx])
        label = self.class_names[idx] if idx < len(self.class_names) else f"class_{idx}"

        self.last_warning = None
        return Classification(label=label, confidence=confidence)
