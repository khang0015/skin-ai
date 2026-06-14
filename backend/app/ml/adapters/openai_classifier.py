"""
OpenAI Vision Classifier
========================
Gửi ảnh crop vùng tổn thương lên OpenAI GPT-4o (Vision) để phân loại
thành một trong 7 lớp bệnh da liễu của bộ dữ liệu HAM10000.

Các lớp (label chính xác trả về):
    akiec   – Actinic keratoses / Bowen's disease
    bcc     – Basal cell carcinoma
    bkl     – Benign keratosis
    df      – Dermatofibroma
    mel     – Melanoma
    nv      – Melanocytic nevus
    vasc    – Vascular lesion
"""
from __future__ import annotations

import base64
import logging
from typing import Any

import cv2
import numpy as np

from ..base import BaseClassifier
from ..types import Classification

logger = logging.getLogger(__name__)


def _is_unsupported_param_error(exc: Exception, param_name: str) -> bool:
    message = str(exc)
    return (
        "Unsupported parameter" in message
        and f"'{param_name}'" in message
        and "unsupported_parameter" in message
    )

# ── HAM10000 class labels (viết tắt) ────────────────────────────────
HAM10000_CLASSES: tuple[str, ...] = (
    "akiec",
    "bcc",
    "bkl",
    "df",
    "mel",
    "nv",
    "vasc",
)

# ── Mapping nhãn viết tắt → tên đầy đủ (để hiển thị cho user) ──────
HAM10000_FULL_NAMES: dict[str, str] = {
    "akiec": "actinic keratosis (Bowen's disease)",
    "bcc": "basal cell carcinoma",
    "bkl": "benign keratosis",
    "df": "dermatofibroma",
    "mel": "melanoma",
    "nv": "melanocytic nevus",
    "vasc": "vascular lesion",
}

# ── System prompt ────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are an expert dermatologist AI assistant. "
    "You will be given a dermoscopic image of a skin lesion. "
    "Your task is to classify the lesion into exactly ONE of the following 7 classes "
    "from the HAM10000 dataset:\n"
    "  akiec, bcc, bkl, df, mel, nv, vasc\n\n"
    "Rules:\n"
    "- Reply with ONLY the class label (one of the 7 above), nothing else.\n"
    "- No explanation, no punctuation, no extra text.\n"
    "- The response must be exactly one word from the list above."
)

USER_PROMPT = "Classify this skin lesion image. Reply with only the class label."


class OpenAIVisionClassifier(BaseClassifier):
    """Classifier sử dụng OpenAI GPT-4o Vision API."""

    def __init__(
        self,
        name: str,
        api_key: str,
        model: str = "gpt-4o",
        class_names: tuple[str, ...] = HAM10000_CLASSES,
    ) -> None:
        # model_path không cần thiết nhưng BaseClassifier yêu cầu
        super().__init__(
            name=name,
            model_path="openai-api",
            class_names=class_names,
            input_size=0,
        )
        self.api_key = api_key
        self.model = model
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Lazy-load OpenAI client."""
        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "Thư viện 'openai' chưa được cài đặt. "
                "Chạy: pip install openai"
            ) from exc

        self._client = OpenAI(api_key=self.api_key)
        return self._client

    @staticmethod
    def _encode_image(image_bgr: np.ndarray) -> str:
        """Encode ảnh BGR sang base64 (JPEG)."""
        success, buffer = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success:
            raise ValueError("Không thể encode ảnh sang JPEG.")
        return base64.b64encode(buffer.tobytes()).decode("utf-8")

    def classify(self, image_bgr: np.ndarray) -> Classification:
        """Gửi ảnh lên GPT-4o Vision và nhận lại class label."""
        self.last_warning = None

        if self.api_key in ("", "your-openai-api-key-here"):
            self.last_warning = "OPENAI_API_KEY chưa được cấu hình."
            return Classification(label="unknown", confidence=0.0)

        try:
            client = self._get_client()
            b64_image = self._encode_image(image_bgr)

            request_kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": USER_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                "temperature": 0.0,
            }

            # Newer models (e.g. gpt-5-*) require max_completion_tokens.
            # Older models typically use max_tokens.
            try:
                response = client.chat.completions.create(
                    **request_kwargs,
                    max_tokens=20,
                )
            except Exception as first_exc:
                if not _is_unsupported_param_error(first_exc, "max_tokens"):
                    raise
                response = client.chat.completions.create(
                    **request_kwargs,
                    max_completion_tokens=20,
                )

            raw_label = response.choices[0].message.content.strip().lower()
            logger.info("OpenAI raw response: '%s'", raw_label)

            # Validate label
            if raw_label in self.class_names:
                label = raw_label
            else:
                # Cố gắng match nếu GPT trả về có thêm ký tự thừa
                matched = [c for c in self.class_names if c in raw_label]
                if matched:
                    label = matched[0]
                    self.last_warning = (
                        f"OpenAI trả về '{raw_label}', đã map thành '{label}'."
                    )
                else:
                    self.last_warning = (
                        f"OpenAI trả về '{raw_label}' không nằm trong danh sách "
                        f"lớp hợp lệ. Mặc định: unknown."
                    )
                    return Classification(label="unknown", confidence=0.0)

            # Lấy tên đầy đủ để hiển thị
            full_name = HAM10000_FULL_NAMES.get(label, label)

            # GPT không trả về confidence score, dùng 1.0 cho label nó chọn
            return Classification(label=full_name, confidence=1.0)

        except Exception as exc:
            logger.exception("OpenAI classification failed")
            self.last_warning = f"OpenAI API error: {exc}"
            return Classification(label="unknown", confidence=0.0)
