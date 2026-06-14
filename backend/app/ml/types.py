from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Detection:
    bbox: list[int]
    label: str
    confidence: float


@dataclass
class Classification:
    label: str
    confidence: float
