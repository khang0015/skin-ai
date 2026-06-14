"""
HuggingFace Vision Classifier
==============================
Gửi ảnh crop vùng tổn thương lên HuggingFace Inference API
sử dụng model Vision-Language (mặc định: Qwen2.5-VL-7B-Instruct)
để phân loại thành một trong 7 lớp bệnh da liễu của HAM10000.

Sử dụng huggingface_hub InferenceClient (OpenAI-compatible).

Lưu ý: Chỉ các model được serve qua HuggingFace Inference Providers
mới hoạt động. Danh sách model hỗ trợ:
  - Qwen/Qwen2.5-VL-7B-Instruct  (mặc định, khuyên dùng)
  - meta-llama/Llama-3.2-11B-Vision-Instruct
  - google/gemma-3-4b-it
  - ... (xem https://huggingface.co/models?pipeline_tag=image-text-to-text)
"""
from __future__ import annotations

import base64
import logging
from typing import Any

import cv2
import numpy as np

from ..base import BaseClassifier
from ..types import Classification
from .openai_classifier import HAM10000_CLASSES, HAM10000_FULL_NAMES

logger = logging.getLogger(__name__)

# ── Default HuggingFace model ID ────────────────────────────────────
DEFAULT_HF_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"

# ── Prompt ───────────────────────────────────────────────────────────
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


class HuggingFaceVisionClassifier(BaseClassifier):
    """Classifier sử dụng HuggingFace Inference Providers (vision models)."""

    def __init__(
        self,
        name: str,
        api_key: str,
        model: str = DEFAULT_HF_MODEL,
        class_names: tuple[str, ...] = HAM10000_CLASSES,
    ) -> None:
        super().__init__(
            name=name,
            model_path="huggingface-api",
            class_names=class_names,
            input_size=0,
        )
        self.api_key = api_key
        self.model = model
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Lazy-load HuggingFace InferenceClient."""
        if self._client is not None:
            return self._client

        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise ImportError(
                "Thư viện 'huggingface_hub' chưa được cài đặt. "
                "Chạy: pip install huggingface_hub"
            ) from exc

        # Force Hugging Face serverless inference provider. This avoids routing the
        # request to an OpenAI-compatible chat endpoint that may only support a
        # limited set of chat models.
        self._client = InferenceClient(provider="hf-inference", token=self.api_key)
        return self._client

    @staticmethod
    def _encode_image_base64(image_bgr: np.ndarray) -> str:
        """Encode ảnh BGR sang base64 (JPEG)."""
        success, buffer = cv2.imencode(
            ".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90]
        )
        if not success:
            raise ValueError("Không thể encode ảnh sang JPEG.")
        return base64.b64encode(buffer.tobytes()).decode("utf-8")

    @staticmethod
    def _encode_image_jpeg_bytes(image_bgr: np.ndarray) -> bytes:
        """Encode ảnh BGR sang bytes JPEG (phục vụ VQA endpoint)."""
        success, buffer = cv2.imencode(
            ".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90]
        )
        if not success:
            raise ValueError("Không thể encode ảnh sang JPEG.")
        return buffer.tobytes()

    @staticmethod
    def _is_not_chat_model_error(exc: Exception) -> bool:
        """Heuristic: phát hiện lỗi HF khi model không hỗ trợ chat-completions."""
        message = str(exc).lower()
        return (
            "not a chat model" in message
            or "model_not_supported" in message
            or "invalid_request_error" in message and "chat model" in message
        )

    def classify(self, image_bgr: np.ndarray) -> Classification:
        """Gửi ảnh lên HuggingFace Vision model và nhận lại class label."""
        self.last_warning = None

        if not self.api_key or self.api_key == "your-huggingface-api-key-here":
            self.last_warning = "HUGGING_FACE_API_KEY chưa được cấu hình."
            return Classification(label="unknown", confidence=0.0)

        try:
            client = self._get_client()

            # 1) Ưu tiên endpoint OpenAI-compatible chat.completions (phù hợp với chat-capable VLM)
            # 2) Nếu model không hỗ trợ chat, fallback sang visual_question_answering (VQA)
            raw_label: str | None = None
            confidence: float = 1.0
            try:
                b64_image = self._encode_image_base64(image_bgr)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": USER_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{b64_image}",
                                    },
                                },
                            ],
                        },
                    ],
                    max_tokens=20,
                    temperature=0.0,
                )
                raw_label = response.choices[0].message.content.strip().lower()
                logger.info("HuggingFace(chat) raw response: '%s'", raw_label)
            except Exception as chat_exc:
                if not self._is_not_chat_model_error(chat_exc):
                    raise

                jpeg_bytes = self._encode_image_jpeg_bytes(image_bgr)
                question = (
                    "Classify this dermoscopic image into exactly ONE class from: "
                    "akiec, bcc, bkl, df, mel, nv, vasc. "
                    "Reply with ONLY the class label."
                )
                vqa_outputs = client.visual_question_answering(
                    image=jpeg_bytes,
                    question=question,
                    model=self.model,
                    top_k=5,
                )
                if not vqa_outputs:
                    self.last_warning = "HuggingFace VQA trả về rỗng."
                    return Classification(label="unknown", confidence=0.0)

                best = vqa_outputs[0]
                raw_label = str(getattr(best, "answer", "")).strip().lower()
                confidence = float(getattr(best, "score", 0.0) or 0.0)
                logger.info(
                    "HuggingFace(VQA) raw response: '%s' (score=%.4f)",
                    raw_label,
                    confidence,
                )

            if raw_label is None:
                self.last_warning = "HuggingFace không trả về nhãn hợp lệ."
                return Classification(label="unknown", confidence=0.0)

            # Validate label
            if raw_label in self.class_names:
                label = raw_label
            else:
                # Cố gắng match nếu model trả về có thêm ký tự thừa
                matched = [c for c in self.class_names if c in raw_label]
                if matched:
                    label = matched[0]
                    self.last_warning = (
                        f"HuggingFace trả về '{raw_label}', đã map thành '{label}'."
                    )
                else:
                    self.last_warning = (
                        f"HuggingFace trả về '{raw_label}' không nằm trong danh sách "
                        f"lớp hợp lệ. Mặc định: unknown."
                    )
                    return Classification(label="unknown", confidence=0.0)

            # Lấy tên đầy đủ để hiển thị
            full_name = HAM10000_FULL_NAMES.get(label, label)

            # Nếu dùng VQA endpoint, score thường <1; nếu chat, mặc định 1.0
            confidence = max(0.0, min(1.0, float(confidence)))
            if confidence == 0.0:
                confidence = 1.0
            return Classification(label=full_name, confidence=confidence)

        except Exception as exc:
            logger.exception("HuggingFace classification failed")
            self.last_warning = f"HuggingFace API error: {exc}"
            return Classification(label="unknown", confidence=0.0)
