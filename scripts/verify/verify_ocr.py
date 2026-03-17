import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtGui import QImage

from backend.desktop.services.ocr_worker import OCRWorker


def main() -> int:
    try:
        import easyocr
        import torch
    except ModuleNotFoundError as exc:
        print(f"FAIL: OCR dependency missing: {exc}")
        return 1

    width, height = 320, 120
    pil_image = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(pil_image)
    draw.text((20, 40), "TEST", fill="black")

    raw = pil_image.tobytes("raw", "RGBA")
    qimage = QImage(raw, width, height, QImage.Format_RGBA8888)

    worker = OCRWorker(qimage)
    pil_from_qt = worker._to_pil()

    gpu = torch.cuda.is_available()
    reader = easyocr.Reader(["en"], gpu=gpu)
    results = reader.readtext(np.array(pil_from_qt), detail=0, paragraph=True)
    text = "\n".join(results).strip()
    print("--- OCR Result ---")
    print(text)
    if not text:
        print("FAIL: OCR produced empty result.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
