from pathlib import Path

BOOKS_DIR = Path(__file__).parent.parent / "books"


def discover_books() -> list[dict]:
    """Return list of {folder_path, folder_name, is_loose_pdf} for each book found."""
    results = []

    if not BOOKS_DIR.exists():
        return results

    # Subfolders = books with chapter PDFs
    for entry in sorted(BOOKS_DIR.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            pdfs = list(entry.glob("*.pdf"))
            if pdfs:
                results.append(
                    {
                        "folder_path": str(entry),
                        "folder_name": entry.name,
                        "pdf_count": len(pdfs),
                        "is_loose_pdf": False,
                    }
                )

    # Loose PDFs directly in books/
    for entry in sorted(BOOKS_DIR.iterdir()):
        if entry.is_file() and entry.suffix.lower() == ".pdf":
            results.append(
                {
                    "folder_path": str(entry),
                    "folder_name": entry.stem,
                    "pdf_count": 1,
                    "is_loose_pdf": True,
                }
            )

    return results


def get_pdf_files(folder_path: str, is_loose_pdf: bool) -> list[str]:
    """Return list of PDF filenames in a book folder."""
    if is_loose_pdf:
        p = Path(folder_path)
        return [p.name]
    return sorted(f.name for f in Path(folder_path).glob("*.pdf"))
