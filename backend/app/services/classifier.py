from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class CnnClassifier:
    def __init__(self, model_path: str, class_names: tuple[str, ...], input_size: int = 224) -> None:
        self.model_path = Path(model_path)
        self.class_names = class_names
        self.input_size = input_size
        self._model: Any | None = None
        self.last_warning: str | None = None

    def _load(self) -> Any | None:
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            self.last_warning = f"CNN model not found: {self.model_path}"
            return None

        keras = importlib.import_module("tensorflow.keras")
        self._model = keras.models.load_model(str(self.model_path))
        return self._model

    def classify(self, image_bgr: np.ndarray) -> dict:
        model = self._load()
        if model is None:
            return {"label": "unknown", "confidence": 0.0}

        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.input_size, self.input_size))
        tensor = resized.astype("float32") / 255.0
        tensor = np.expand_dims(tensor, axis=0)

        pred = model.predict(tensor, verbose=0)[0]
        idx = int(np.argmax(pred))
        confidence = float(pred[idx])

        if idx < len(self.class_names):
            label = self.class_names[idx]
        else:
            label = f"class_{idx}"

        self.last_warning = None
        return {"label": label, "confidence": confidence}
