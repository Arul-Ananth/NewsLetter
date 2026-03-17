from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)


class OCRWorker(QThread):
    status_message = Signal(str)
    result_ready = Signal(str)
    error_message = Signal(str)

    def __init__(self, image: QImage, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()

    def _to_pil(self):
        from PIL import Image

        qimage = self.image.convertToFormat(QImage.Format_RGBA8888)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        data = ptr.tobytes()
        if len(data) < qimage.sizeInBytes():
            data = ptr[: qimage.sizeInBytes()].tobytes()
        return Image.frombytes("RGBA", (width, height), data)

    def run(self) -> None:
        if self.isInterruptionRequested() or self._cancelled:
            return

        try:
            self.status_message.emit("Running OCR...")
            try:
                import numpy as np
                from PIL import Image
                import easyocr
            except ModuleNotFoundError:
                self.error_message.emit(
                    "OCR dependencies are missing. Please install easyocr and Pillow."
                )
                return

            gpu = False
            try:
                import torch

                gpu = torch.cuda.is_available()
            except Exception:
                gpu = False

            pil_image = self._to_pil()
            if self.isInterruptionRequested() or self._cancelled:
                return
            image_array = np.array(pil_image)
            reader = easyocr.Reader(["en"], gpu=gpu)
            results = reader.readtext(image_array, detail=0, paragraph=True)
            if self.isInterruptionRequested() or self._cancelled:
                return
            text = "\n".join(results).strip()
            self.result_ready.emit(text)
        except Exception as exc:
            logger.exception("OCR failed: %s", exc)
            self.error_message.emit("OCR failed. Please try again.")
