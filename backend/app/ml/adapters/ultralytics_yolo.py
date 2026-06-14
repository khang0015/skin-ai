from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from ..base import BaseDetector
from ..types import Detection


class UltralyticsYoloDetector(BaseDetector):
    def __init__(self, name: str, model_path: str) -> None:
        super().__init__(name=name, model_path=model_path)
        self._model: Any | None = None

    def _load(self) -> Any | None:
        if self._model is not None:
            return self._model

        path = Path(self.model_path)
        if not path.exists():
            self.last_warning = f"Detector model not found: {path}"
            return None

        ultralytics = importlib.import_module("ultralytics")
        yolo_cls = getattr(ultralytics, "YOLO")
        self._model = yolo_cls(str(path))
        return self._model

    def detect(self, image_path: str) -> list[Detection]:
        model = self._load()
        if model is None:
            return []

        results = model.predict(image_path, verbose=False)
        detections: list[Detection] = []

        for result in results:
            names = result.names
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                coords = box.xyxy[0].tolist()
                cls_idx = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                detections.append(
                    Detection(
                        bbox=[int(value) for value in coords],
                        label=names.get(cls_idx, str(cls_idx)),
                        confidence=confidence,
                    )
                )

        self.last_warning = None
        return detections
