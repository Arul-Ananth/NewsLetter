from __future__ import annotations

import asyncio
import logging

from PySide6.QtCore import QThread, Signal
from sentence_transformers import SentenceTransformer

from backend.common.services.llm.newsletter_service import newsletter_service

logger = logging.getLogger(__name__)


class AIWorker(QThread):
    progress_update = Signal(int)
    status_message = Signal(str)
    result_ready = Signal(str)

    def __init__(
        self,
        topic: str,
        context: str,
        user_id: int,
        session_id: str,
        api_keys: dict[str, str | None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.topic = topic
        self.context = context
        self.user_id = user_id
        self.session_id = session_id
        self.api_keys = api_keys
        self._cancelled = False
        self._embedder = None

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()

    def _select_device(self) -> str:
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except Exception as exc:
            self.status_message.emit(f"GPU detection failed, using CPU. Reason: {exc}")
        return "cpu"

    def _init_embedder(self) -> None:
        device = self._select_device()
        try:
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
            self.status_message.emit(f"Embedding device: {device}")
        except Exception as exc:
            self.status_message.emit(
                f"GPU init failed ({device}); falling back to CPU. Reason: {exc}"
            )
            try:
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                self.status_message.emit("Embedding device: cpu")
            except Exception as inner_exc:
                self.status_message.emit(f"Embedding init failed: {inner_exc}")

    def run(self) -> None:
        self._init_embedder()
        if self.isInterruptionRequested() or self._cancelled:
            self.status_message.emit("Generation cancelled.")
            self.result_ready.emit("")
            return

        try:
            self.status_message.emit("Starting AI generation...")
            result = asyncio.run(
                newsletter_service.generate_newsletter(
                    self.topic,
                    self.user_id,
                    self.context,
                    self.api_keys,
                    session_id=self.session_id,
                )
            )
            if self.isInterruptionRequested() or self._cancelled:
                self.status_message.emit("Generation cancelled.")
                self.result_ready.emit("")
                return
            self.result_ready.emit(result.content)
        except Exception as exc:
            logger.exception("AI generation failed: %s", exc)
            self.status_message.emit("Error occurred while generating the newsletter.")
            self.result_ready.emit("")
