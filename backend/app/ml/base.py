from __future__ import annotations

import threading
from abc import ABC, abstractmethod

import numpy as np

from .types import Classification, Detection


class BaseDetector(ABC):
    def __init__(self, name: str, model_path: str) -> None:
        self.name = name
        self.model_path = model_path
        # Thread-local storage so concurrent requests don't overwrite each other's warning
        self._local = threading.local()

    @property
    def last_warning(self) -> str | None:
        return getattr(self._local, "warning", None)

    @last_warning.setter
    def last_warning(self, value: str | None) -> None:
        self._local.warning = value

    @abstractmethod
    def detect(self, image_path: str) -> list[Detection]:
        raise NotImplementedError


class BaseClassifier(ABC):
    def __init__(
        self,
        name: str,
        model_path: str,
        class_names: tuple[str, ...],
        input_size: int = 224,
    ) -> None:
        self.name = name
        self.model_path = model_path
        self.class_names = class_names
        self.input_size = input_size
        # Thread-local storage so concurrent requests don't overwrite each other's warning
        self._local = threading.local()

    @property
    def last_warning(self) -> str | None:
        return getattr(self._local, "warning", None)

    @last_warning.setter
    def last_warning(self, value: str | None) -> None:
        self._local.warning = value

    @abstractmethod
    def classify(self, image_bgr: np.ndarray) -> Classification:
        raise NotImplementedError
