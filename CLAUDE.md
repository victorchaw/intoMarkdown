# pdfToMkdown

## Goal
Local web app: scan `books/` folder → AI-sort PDF chapters → merge into one `.md` per book via `markitdown`.

## Stack
- **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy + SQLite (`converter.db`), `markitdown[pdf]`
- **AI**: OpenRouter API (`deepseek/deepseek-chat:free`) via `openai` SDK — sorts filenames, names output
- **Frontend**: TypeScript + Vite 5, plain CSS, dark UI, polls `/api/books` every 3s during processing
- **DB**: SQLite — `books` table (status, pdf_count, output_name) + `book_files` table (sort_order, included, skip_reason)

## Structure
```
backend/main.py       # FastAPI app, 7 API endpoints, lifespan startup resets stuck jobs
backend/db.py         # SQLAlchemy models: Book, BookFile
backend/ai_sorter.py  # OpenRouter call → JSON {output_name, ordered_files, skipped_files}
backend/converter.py  # MarkItDown.convert() per file, merge with --- separator
backend/scanner.py    # Discovers book subfolders + loose PDFs in books/
frontend/src/         # main.ts, api.ts, components/BookCard.ts, BookList.ts, styles/main.css
prds/pdf_to_markdown_mvp.md  # Full PRD
```

## Key Behaviors
- Skip: full-book duplicate PDF (same name as folder), marketing noise ("why subscribe")
- Merge order: AI determines (Preface→Parts→Chapters→Appendix); fallback = alphabetical
- Existing output → skip silently; Re-convert → DELETE `/api/books/{id}/output` then re-trigger
- Startup: resets any `processing` books to `discovered` (handles server crash/restart)

## Status (2026-06-09)
- [x] Backend API fully implemented
- [x] Frontend built, served by FastAPI at `http://localhost:8000`
- [x] Both test books discovered: "AI Engineer" (14 PDFs), "Building AI Intensive Python Applications" (19 PDFs)
- [x] OpenRouter API key configured in `.env`
- [ ] End-to-end conversion not yet verified (next step: click Convert in UI)

## Run
```bash
source venv/bin/activate && uvicorn backend.main:app --port 8000
```
