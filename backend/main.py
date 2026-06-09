import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

load_dotenv()

from backend.ai_sorter import sort_and_name
from backend.converter import convert_pdfs
from backend.db import Book, BookFile, get_db, init_db
from backend.scanner import BOOKS_DIR, discover_books, get_pdf_files


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Reset any books stuck in processing from a previous crashed/killed run
    from backend.db import SessionLocal
    db = SessionLocal()
    try:
        stuck = db.query(Book).filter(Book.status == "processing").all()
        for b in stuck:
            b.status = "discovered"
            b.error_message = "Interrupted by server restart"
            b.updated_at = datetime.utcnow()
        if stuck:
            db.commit()
            print(f"[startup] Reset {len(stuck)} stuck processing book(s)")
    finally:
        db.close()
    yield


app = FastAPI(title="PDF → Markdown Converter", lifespan=lifespan)

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


# ── Response models ────────────────────────────────────────────────────────────

class BookFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    sort_order: int | None
    included: bool
    skip_reason: str | None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folder_name: str
    output_name: str | None
    status: str
    error_message: str | None
    file_count: int


# ── API routes ─────────────────────────────────────────────────────────────────

@app.get("/api/books", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)):
    books = db.query(Book).order_by(Book.folder_name).all()
    return [
        BookOut(
            id=b.id,
            folder_name=b.folder_name,
            output_name=b.output_name,
            status=b.status,
            error_message=b.error_message,
            file_count=len(b.files) if b.files else b.pdf_count,
        )
        for b in books
    ]


@app.post("/api/scan")
def scan_books(db: Session = Depends(get_db)):
    discovered = discover_books()
    added = 0
    for item in discovered:
        existing = db.query(Book).filter(Book.folder_path == item["folder_path"]).first()
        if not existing:
            book = Book(
                folder_path=item["folder_path"],
                folder_name=item["folder_name"],
                pdf_count=item.get("pdf_count", 0),
                status="discovered",
            )
            db.add(book)
            added += 1
    db.commit()
    return {"added": added, "total": db.query(Book).count()}


def _run_conversion(book_id: int):
    from backend.db import SessionLocal

    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return

        book.status = "processing"
        book.error_message = None
        book.updated_at = datetime.utcnow()
        db.commit()

        # Determine if loose PDF
        is_loose = Path(book.folder_path).is_file()
        filenames = get_pdf_files(book.folder_path, is_loose)

        # AI sort
        print(f"\nProcessing: {book.folder_name}")
        ai_result = sort_and_name(filenames, book.folder_name)

        output_name = ai_result["output_name"]
        ordered_names = ai_result["ordered_files"]
        skipped = {s["filename"]: s["reason"] for s in ai_result.get("skipped_files", [])}

        # Persist file ordering
        db.query(BookFile).filter(BookFile.book_id == book.id).delete()
        for order_idx, fname in enumerate(ordered_names):
            db.add(BookFile(
                book_id=book.id,
                filename=fname,
                sort_order=order_idx,
                included=True,
                skip_reason=None,
            ))
        for fname, reason in skipped.items():
            db.add(BookFile(
                book_id=book.id,
                filename=fname,
                sort_order=None,
                included=False,
                skip_reason=reason,
            ))
        db.commit()

        # Build ordered Path list
        base_dir = Path(book.folder_path) if not is_loose else Path(book.folder_path).parent
        ordered_paths = [base_dir / fname for fname in ordered_names if (base_dir / fname).exists()]

        if not ordered_paths:
            raise ValueError("No valid PDF files to convert after filtering")

        # Convert
        output_path = convert_pdfs(ordered_paths, output_name)
        print(f"[DONE] {output_path.name}")

        book.output_name = output_name
        book.status = "done"
        book.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.status = "failed"
            book.error_message = str(e)
            book.updated_at = datetime.utcnow()
            db.commit()
        print(f"[ERROR] Book {book_id}: {e}")
    finally:
        db.close()


@app.post("/api/books/{book_id}/convert")
def convert_book(book_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.status == "processing":
        raise HTTPException(status_code=409, detail="Already processing")
    background_tasks.add_task(_run_conversion, book_id)
    return {"status": "queued"}


@app.post("/api/convert-all")
def convert_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.status != "done").all()
    for book in books:
        if book.status != "processing":
            background_tasks.add_task(_run_conversion, book.id)
    return {"queued": len(books)}


@app.get("/api/books/{book_id}/files", response_model=list[BookFileOut])
def get_book_files(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return sorted(book.files, key=lambda f: (f.sort_order is None, f.sort_order or 0))


@app.get("/api/books/{book_id}/preview")
def preview_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.status != "done" or not book.output_name:
        raise HTTPException(status_code=404, detail="Output not ready")
    output_path = OUTPUT_DIR / f"{book.output_name}.md"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file missing")
    content = output_path.read_text(encoding="utf-8")
    return {"preview": content[:3000], "total_chars": len(content)}


@app.delete("/api/books/{book_id}/output")
def reset_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.output_name:
        output_path = OUTPUT_DIR / f"{book.output_name}.md"
        if output_path.exists():
            output_path.unlink()
    book.status = "discovered"
    book.error_message = None
    book.output_name = None
    book.updated_at = datetime.utcnow()
    db.query(BookFile).filter(BookFile.book_id == book.id).delete()
    db.commit()
    return {"status": "reset"}


# ── Static files (frontend) ────────────────────────────────────────────────────

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        return FileResponse(str(index))
