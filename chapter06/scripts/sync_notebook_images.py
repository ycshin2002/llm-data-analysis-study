"""images 폴더의 최신 PNG를 chapter06.ipynb에 다시 첨부한다.

실행:
    python scripts/sync_notebook_images.py
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

import nbformat


CHAPTER_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = CHAPTER_ROOT / "chapter06.ipynb"
IMAGE_DIR = CHAPTER_ROOT / "images"
IMAGE_NAMES = ["step02_eda.png", "step04_llm.png"]


def replace_image_reference(source: str, original_name: str, attachment_name: str) -> str:
    """상대경로 또는 기존 attachment 링크를 새 attachment 링크로 바꾼다."""
    stem = re.escape(Path(original_name).stem)
    pattern = rf"\]\((?:images/|attachment:){stem}(?:-[0-9a-f]+)?\.png\)"
    return re.sub(pattern, f"](attachment:{attachment_name})", source)


notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
updated: list[str] = []

for original_name in IMAGE_NAMES:
    image_path = IMAGE_DIR / original_name
    if not image_path.exists():
        print(f"건너뜀: {image_path.name} 없음")
        continue

    image_bytes = image_path.read_bytes()
    digest = hashlib.sha256(image_bytes).hexdigest()[:12]
    stem = image_path.stem
    attachment_name = f"{stem}-{digest}.png"
    encoded = base64.b64encode(image_bytes).decode("ascii")

    for cell in notebook.cells:
        if cell.cell_type != "markdown":
            continue
        if stem not in cell.source:
            continue

        cell.source = replace_image_reference(cell.source, original_name, attachment_name)
        attachments = cell.setdefault("attachments", {})
        for key in list(attachments):
            if key.startswith(f"{stem}-") or key == original_name:
                del attachments[key]
        attachments[attachment_name] = {"image/png": encoded}
        updated.append(original_name)

nbformat.write(notebook, NOTEBOOK_PATH)
print("최신 첨부 이미지 동기화:", ", ".join(updated) if updated else "없음")
