from __future__ import annotations

import logging

import cv2
import numpy as np

from ..services.skin_detector import is_skin_image
from .registry import ModelRegistry
from .types import Detection

logger = logging.getLogger(__name__)

# Minimum YOLO confidence to consider a detection valid.
# Detections below this are discarded before classification.
DEFAULT_DETECTION_CONFIDENCE_THRESHOLD = 0.25


class AnalysisPipelineRunner:
    def __init__(
        self,
        registry: ModelRegistry,
        skin_threshold: float = 0.15,
        detection_confidence_threshold: float = DEFAULT_DETECTION_CONFIDENCE_THRESHOLD,
    ) -> None:
        self.registry = registry
        self.skin_threshold = skin_threshold
        self.detection_confidence_threshold = detection_confidence_threshold

    def run(self, image_path: str, image_bgr: np.ndarray, pipeline_name: str = "default") -> dict:
        config = self.registry.get_pipeline(pipeline_name)
        detector = self.registry.detectors[config.detector_name]
        classifier = self.registry.classifiers[config.classifier_name]

        warnings: list[str] = []

        def not_skin_result(ratio: float) -> dict:
            return {
                "pipeline": pipeline_name,
                "detector": detector.name,
                "classifier": classifier.name,
                "detections": [],
                "summary": "Ảnh không được nhận dạng là ảnh da.",
                "warnings": [],
                "is_skin": False,
                "skin_ratio": round(ratio, 4),
            }

        def no_detection_result(ratio: float) -> dict:
            return {
                "pipeline": pipeline_name,
                "detector": detector.name,
                "classifier": classifier.name,
                "detections": [],
                "summary": "Ảnh là vùng da nhưng chưa phát hiện vùng tổn thương đủ rõ để phân loại.",
                "warnings": [],
                "is_skin": True,
                "skin_ratio": round(ratio, 4),
            }

        # ── Step 1: Skin check ───────────────────────────────────────
        skin_ok, skin_ratio = is_skin_image(image_bgr, threshold=self.skin_threshold)
        if not skin_ok:
            return not_skin_result(skin_ratio)

        # ── Step 2: Detection ────────────────────────────────────────
        raw_detections = detector.detect(image_path)

        # Capture warning before any other code can overwrite it (thread-safe via property)
        det_warning = detector.last_warning
        if det_warning:
            warnings.append(f"[{detector.name}] {det_warning}")

        h, w = image_bgr.shape[:2]

        # Filter by confidence threshold
        detections = [
            det for det in raw_detections
            if det.confidence >= self.detection_confidence_threshold
        ]
        if raw_detections and not detections:
            warnings.append(
                f"[{detector.name}] All {len(raw_detections)} detection(s) below "
                f"confidence threshold ({self.detection_confidence_threshold:.0%}). "
                "Classification skipped."
            )

        classifier_input = getattr(config, "classifier_input", "crop")

        best_det: Detection | None = None
        if detections:
            best_score: tuple[float, int] = (-1.0, -1)
            for det in detections:
                x1, y1, x2, y2 = self._clamp_bbox(det, w=w, h=h)
                if x2 <= x1 or y2 <= y1:
                    continue
                area = (x2 - x1) * (y2 - y1)
                score: tuple[float, int] = (float(det.confidence), int(area))
                if score > best_score:
                    best_det = det
                    best_score = score
        else:
            if classifier_input == "crop":
                warnings.append(
                    f"[{detector.name}] No valid detections found. Classification skipped."
                )

        if best_det is None:
            return no_detection_result(skin_ratio)

        # ── Step 3: Classification ───────────────────────────────────
        results: list[dict] = []

        if classifier_input == "full":
            cls = classifier.classify(image_bgr)

            x1, y1, x2, y2 = self._clamp_bbox(best_det, w=w, h=h)
            bbox = [x1, y1, x2, y2]
            det_conf = float(best_det.confidence)

            results.append(
                {
                    "lesion_type": cls.label,
                    "confidence": min(det_conf, float(cls.confidence)),
                    "bbox": bbox,
                }
            )

        else:
            # crop mode: only classify if we have a valid detection
            if best_det is not None:
                x1, y1, x2, y2 = self._clamp_bbox(best_det, w=w, h=h)
                crop = image_bgr[y1:y2, x1:x2]
                cls = classifier.classify(crop)
                results.append(
                    {
                        "lesion_type": cls.label,
                        "confidence": min(float(best_det.confidence), float(cls.confidence)),
                        "bbox": [x1, y1, x2, y2],
                    }
                )

        # Capture classifier warning after classify() call
        cls_warning = classifier.last_warning
        if cls_warning:
            warnings.append(f"[{classifier.name}] {cls_warning}")

        if not results:
            summary = "No detections found."
        else:
            summary = ", ".join(
                f"{item['lesion_type']} ({item['confidence']:.2f})" for item in results
            )

        return {
            "pipeline": pipeline_name,
            "detector": detector.name,
            "classifier": classifier.name,
            "detections": results,
            "summary": f"Top findings: {summary}",
            "warnings": warnings,
            "is_skin": True,
            "skin_ratio": round(skin_ratio, 4),
        }

    @staticmethod
    def _clamp_bbox(det: Detection, w: int, h: int) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = det.bbox
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w - 1))
        y2 = max(0, min(y2, h - 1))
        return x1, y1, x2, y2
