"""
Skin Detection Module
=====================
Sử dụng kết hợp Color-based Skin Detection (HSV + YCbCr) + Threshold
để xác định ảnh có phải ảnh da hay không.

Pipeline:
    1. Chuyển ảnh sang HSV → tạo mask da dựa trên range HSV.
    2. Chuyển ảnh sang YCbCr → tạo mask da dựa trên range Cb, Cr.
    3. AND hai mask lại → skin_mask.
    4. Tính tỷ lệ pixel da / tổng pixel.
    5. So sánh với ngưỡng → trả về True/False.
"""
from __future__ import annotations

import cv2
import numpy as np


# ── HSV range for skin pixels ────────────────────────────────────────
# H: 0-25  (skin hue range, low end)
# S: 20-255 (wide range to cover fair → dark skin)
# V: 50-255 (avoid very dark pixels)
HSV_LOWER = np.array([0, 20, 50], dtype=np.uint8)
HSV_UPPER = np.array([25, 255, 255], dtype=np.uint8)

# Extended HSV range (red/skin wraps around in HSV hue)
HSV_LOWER2 = np.array([165, 20, 50], dtype=np.uint8)
HSV_UPPER2 = np.array([180, 255, 255], dtype=np.uint8)

# ── YCbCr range for skin pixels ──────────────────────────────────────
# OpenCV COLOR_BGR2YCrCb outputs channels in [Y, Cr, Cb] order.
# Standard skin ranges: Cb ∈ [77, 127], Cr ∈ [133, 173]
# → In OpenCV [Y, Cr, Cb] order: [0, 133, 77] to [255, 173, 127]
YCRCB_LOWER = np.array([0, 133, 77], dtype=np.uint8)
YCRCB_UPPER = np.array([255, 173, 127], dtype=np.uint8)

# ── Default threshold ────────────────────────────────────────────────
DEFAULT_SKIN_THRESHOLD = 0.15  # 15%


def compute_skin_ratio(image_bgr: np.ndarray) -> float:
    """Tính tỷ lệ pixel da trong ảnh.

    Parameters
    ----------
    image_bgr : np.ndarray
        Ảnh BGR (OpenCV format).

    Returns
    -------
    float
        Tỷ lệ pixel da (0.0 – 1.0).
    """
    if image_bgr is None or image_bgr.size == 0:
        return 0.0

    # ── 1. HSV mask ──────────────────────────────────────────────────
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    mask_hsv1 = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    mask_hsv2 = cv2.inRange(hsv, HSV_LOWER2, HSV_UPPER2)
    mask_hsv = cv2.bitwise_or(mask_hsv1, mask_hsv2)

    # ── 2. YCrCb mask ───────────────────────────────────────────────
    ycrcb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YCrCb)
    mask_ycrcb = cv2.inRange(ycrcb, YCRCB_LOWER, YCRCB_UPPER)

    # ── 3. Kết hợp AND hai mask ──────────────────────────────────────
    skin_mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)

    # ── 4. Làm mượt để giảm nhiễu ───────────────────────────────────
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)

    # ── 5. Tính tỷ lệ ───────────────────────────────────────────────
    total_pixels = skin_mask.shape[0] * skin_mask.shape[1]
    skin_pixels = cv2.countNonZero(skin_mask)

    return skin_pixels / total_pixels if total_pixels > 0 else 0.0


def is_skin_image(
    image_bgr: np.ndarray,
    threshold: float = DEFAULT_SKIN_THRESHOLD,
) -> tuple[bool, float]:
    """Kiểm tra ảnh có phải ảnh da hay không.

    Parameters
    ----------
    image_bgr : np.ndarray
        Ảnh BGR (OpenCV format).
    threshold : float
        Ngưỡng tỷ lệ da tối thiểu (mặc định 0.15 = 15%).

    Returns
    -------
    tuple[bool, float]
        (is_skin, skin_ratio)
        - is_skin: True nếu ảnh được coi là ảnh da.
        - skin_ratio: Tỷ lệ pixel da (0.0 – 1.0).
    """
    ratio = compute_skin_ratio(image_bgr)
    return ratio >= threshold, ratio
