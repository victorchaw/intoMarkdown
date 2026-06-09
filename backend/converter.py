from pathlib import Path

from markitdown import MarkItDown

OUTPUT_DIR = Path(__file__).parent.parent / "output"
SECTION_SEPARATOR = "\n\n---\n\n"

_md = MarkItDown()


def convert_pdfs(ordered_paths: list[Path], output_name: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{output_name}.md"

    sections: list[str] = []
    for pdf_path in ordered_paths:
        print(f"  Converting: {pdf_path.name}")
        result = _md.convert(str(pdf_path))
        content = result.text_content.strip()
        if content:
            sections.append(content)

    merged = SECTION_SEPARATOR.join(sections)
    output_path.write_text(merged, encoding="utf-8")
    return output_path
