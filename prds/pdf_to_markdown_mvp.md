# PDF → Markdown Converter — MVP PRD

## Overview

Local web application that scans a `books/` folder, uses an AI model (via OpenRouter) to determine correct reading order and clean naming, converts PDF chapters to Markdown using `markitdown`, and merges them into one `.md` file per book. Tracks conversion state in a local SQLite database.

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | Python 3.11 + FastAPI | Fast, async, auto OpenAPI docs, works on M1 |
| API server | Uvicorn | ASGI server for FastAPI |
| PDF conversion | markitdown[pdf] | Core PDF→MD library |
| AI ordering | OpenRouter API (openai SDK) | Free tier models for filename classification |
| Database | SQLite (via SQLAlchemy) | Zero install, M1 native, built into Python |
| Frontend | TypeScript + Vite | Type-safe, fast dev server |
| Styling | Plain CSS (no framework) | MVP simplicity |
| Env config | python-dotenv | `.env` for API key |

---

## Project Structure

```
pdfToMkdown/
├── books/                        # input: book subfolders with chapter PDFs
│   └── Book A/
│       ├── Chapter 1.pdf
│       └── Appendix.pdf
├── output/                       # output: one .md per book
│   └── book_a.md
├── prds/
│   └── pdf_to_markdown_mvp.md   # this document
├── backend/
│   ├── main.py                  # FastAPI app + routes
│   ├── db.py                    # SQLAlchemy models + session
│   ├── converter.py             # markitdown conversion logic
│   ├── ai_sorter.py             # OpenRouter LLM call for ordering
│   └── scanner.py               # books/ folder scanner
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── main.ts              # entry point
│   │   ├── api.ts               # typed fetch wrapper
│   │   ├── components/
│   │   │   ├── BookList.ts
│   │   │   └── BookCard.ts
│   │   └── styles/
│   │       └── main.css
│   ├── package.json
│   └── vite.config.ts
├── .env                         # OPENROUTER_API_KEY=your_key_here
└── requirements.txt
```

---

## Database Schema (SQLite via SQLAlchemy)

### `books` table

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | autoincrement |
| folder_path | TEXT UNIQUE | absolute path to book subfolder |
| folder_name | TEXT | display name |
| output_name | TEXT | snake_case filename (set by AI) |
| status | TEXT | `discovered` / `pending` / `processing` / `done` / `failed` |
| error_message | TEXT NULL | failure reason |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### `book_files` table

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| book_id | INTEGER FK → books.id | |
| filename | TEXT | original PDF filename |
| sort_order | INTEGER NULL | AI-assigned position (NULL = skipped) |
| included | BOOLEAN | false = skipped by AI |
| skip_reason | TEXT NULL | e.g. "full_book_duplicate", "marketing_noise" |

---

## API Endpoints (FastAPI)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/books` | List all books with status |
| POST | `/api/scan` | Rescan `books/` folder, add newly discovered books |
| POST | `/api/books/{id}/convert` | Convert one book (runs AI sort then markitdown) |
| POST | `/api/convert-all` | Convert all books with status != `done` |
| GET | `/api/books/{id}/files` | List files for a book with sort order |
| GET | `/api/books/{id}/preview` | First 2000 chars of output .md (if done) |
| DELETE | `/api/books/{id}/output` | Delete output file + reset status to `pending` |

---

## Frontend — Single Page App

**Main view (`/`):**
- Header: "PDF → Markdown Converter"
- Button: "Scan Books Folder" → `POST /api/scan`
- Button: "Convert All" → `POST /api/convert-all`
- Book list with one card per book:
  - Book name (folder_name)
  - Status badge: `discovered` / `pending` / `processing` / `done` / `failed`
  - PDF file count
  - "Convert" button (disabled if `done` or `processing`)
  - "Re-convert" button (visible if `done` — resets and requeues)
  - Error message (visible if `failed`)
  - "Preview" button (visible if `done` — shows first 2000 chars in modal)

**Polling:** frontend polls `GET /api/books` every 3 seconds while any book has status `processing`.

---

## Conversion Flow (per book)

1. **Scan** — discover folder → insert `books` row with status `discovered`
2. **Trigger** — user clicks Convert → status → `processing`
3. **AI Sort** — `ai_sorter.py` sends filenames to OpenRouter LLM → returns ordered list + output name
4. **Store** — insert rows into `book_files` (sort_order, included, skip_reason)
5. **Convert** — iterate ordered included files → `MarkItDown.convert()` per file
6. **Merge** — join sections with `\n\n---\n\n` separator
7. **Write** — save to `output/{output_name}.md`
8. **Done** — update book status → `done`
9. **Error** — any failure → status `failed`, store error_message

---

## AI Sorter Details

- **Model**: `deepseek/deepseek-chat:free` via OpenRouter
- **API**: OpenAI-compatible (`openai` Python SDK, custom `base_url`)
- **Input**: list of PDF filenames + book folder name
- **Expected JSON output**:
  ```json
  {
    "output_name": "building_ai_intensive_python_applications",
    "ordered_files": ["Preface _.pdf", "Part 1_.pdf", "Chapter 1_.pdf"],
    "skipped_files": [
      {"filename": "Building AI Intensive.pdf", "reason": "full_book_duplicate"},
      {"filename": "Why subscribe_.pdf", "reason": "marketing_noise"}
    ]
  }
  ```
- **Fallback**: JSON parse failure → alphabetical sort, slugified folder name, no skips

---

## Setup Instructions

### 1. Get a free OpenRouter API key

Visit [openrouter.ai](https://openrouter.ai) → sign up → copy API key.

### 2. Backend

```bash
cd pdfToMkdown
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Edit `.env`:
```
OPENROUTER_API_KEY=your_key_here
```

### 3. Frontend

```bash
cd frontend
npm install
npm run build        # production build (served by FastAPI)
# OR
npm run dev          # hot-reload dev server at http://localhost:5173
```

### 4. Run

```bash
# from project root, with venv active:
uvicorn backend.main:app --reload --port 8000
# Open http://localhost:8000
```

---

## MVP Scope

**In scope:**
- Scan `books/` folder, discover book subfolders
- AI-assisted reading order + output naming
- PDF-to-Markdown conversion via markitdown
- Merge chapters into one `.md` per book
- SQLite state tracking
- Simple web UI with live status polling
- Skip logic: duplicates, marketing noise
- Loose PDF support (books/ root → standalone .md)
- Re-convert (reset + rerun)

**Out of scope (future):**
- User authentication
- Cloud storage / remote books folder
- In-browser Markdown editor
- Multi-user support
- Real-time progress streaming (WebSockets)
- Batch download of all .md files
