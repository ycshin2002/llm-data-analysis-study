"""Add one notebook cell that displays the latest evidence PNG files directly."""

from pathlib import Path

import nbformat


CHAPTER_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = CHAPTER_ROOT / "chapter06.ipynb"
TAG = "evidence-image-refresh"

notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
notebook.cells = [
    cell
    for cell in notebook.cells
    if TAG not in cell.get("metadata", {}).get("tags", [])
]

notebook.cells.append(
    nbformat.v4.new_markdown_cell(
        "## 증빙 이미지 최신본 확인\n\n"
        "PNG를 다시 저장한 뒤 바로 아래 셀만 실행하면 최신 이미지를 확인할 수 있습니다."
    )
)
notebook.cells.append(
    nbformat.v4.new_code_cell(
        '''# 증빙 이미지 즉시 새로고침
# PNG를 다시 저장한 뒤 이 셀만 실행하면 최신 원본을 직접 표시합니다.
from pathlib import Path
from IPython.display import Image as DisplayImage, display


def find_chapter06(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if candidate.name == "chapter06" and (candidate / "images").exists():
            return candidate
        nested = candidate / "chapter06"
        if (nested / "images").exists():
            return nested
    raise FileNotFoundError("chapter06/images를 찾지 못했습니다.")


preview_root = find_chapter06(Path.cwd())
for preview_name in ["step02_eda.png", "step04_llm.png"]:
    preview_path = preview_root / "images" / preview_name
    print(f"{preview_name} | {preview_path.stat().st_size:,} bytes")
    display(DisplayImage(filename=str(preview_path)))
''',
        metadata={"tags": [TAG]},
    )
)

nbformat.write(notebook, NOTEBOOK_PATH)
print("Preview cell added.")
