"""
Ollama LLM Client
=================
Calls Ollama's native REST API (POST /api/chat) directly via urllib
so there is no dependency on the openai SDK for this path.

Ollama runs on the Azure VM at 127.0.0.1:11434.
Access it locally via SSH tunnel:
  ssh -i Khang_key.pem -N -L 11434:localhost:11434 azureuser@20.244.6.94

Set OLLAMA_BASE_URL=http://localhost:11434 in .env to enable.
"""
from __future__ import annotations

import json
import logging
import socket
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Thin client for Ollama's /api/chat endpoint."""

    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        """
        Parameters
        ----------
        base_url : str
            Ollama base URL, e.g. "http://localhost:11434"
        model : str
            Ollama model tag, e.g. "qwen2.5:7b-instruct"
        timeout : int
            Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        """Quick liveness check — returns True if Ollama responds."""
        try:
            req = urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=3
            )
            return req.status == 200
        except Exception:
            return False

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 900,
        temperature: float = 0.2,
    ) -> str:
        """Send a chat request to Ollama and return the assistant reply text.

        Uses /api/chat with stream=false.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, (TimeoutError, socket.timeout)) or "timed out" in str(reason).lower():
                raise TimeoutError(
                    f"Ollama model '{self.model}' did not respond within {self.timeout} seconds. "
                    "The model may still be loading or generating slowly on the VM."
                ) from exc
            raise

        # Ollama /api/chat response: {"message": {"role": "assistant", "content": "..."}, ...}
        content = body.get("message", {}).get("content", "")
        return content.strip()
