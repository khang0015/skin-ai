from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


class YoloDetector:
    def __init__(self, model_path: str) -> None:
        self.model_path = Path(model_path)
        self._model: Any | None = None
        self.last_warning: str | None = None

    def _load(self) -> Any | None:
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            self.last_warning = f"YOLO model not found: {self.model_path}"
            return None

        ultralytics = importlib.import_module("ultralytics")
        yolo_cls = getattr(ultralytics, "YOLO")
        self._model = yolo_cls(str(self.model_path))
        return self._model

    def detect(self, image_path: str) -> list[dict]:
        model = self._load()
        if model is None:
            return []

        results = model.predict(image_path, verbose=False)
        detections: list[dict] = []

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
                    {
                        "bbox": [int(value) for value in coords],
                        "label": names.get(cls_idx, str(cls_idx)),
                        "confidence": confidence,
                    }
                )

        self.last_warning = None
        return detections
