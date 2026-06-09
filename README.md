# intoMarkdown

A local web application that converts PDF book collections into clean, merged Markdown files using AI-assisted chapter ordering.

Drop a folder of PDF chapters into `books/`, click Convert — the app uses an LLM to determine the correct reading order, converts each PDF, and merges them into a single `.md` file per book.

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688) ![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6)

---

## Features

- **AI-powered ordering** — sends filenames to an LLM (via OpenRouter) to determine correct reading order: Preface → Parts → Chapters → Appendix
- **Smart filtering** — automatically skips full-book duplicates and marketing noise ("Why subscribe?", etc.)
- **Batch conversion** — convert all books in one click, with live status polling
- **Preview** — view the first 3,000 characters of any converted book in the browser
- **Re-convert** — reset and reprocess any book without restarting the server
- **Crash-safe** — server restart automatically recovers books stuck in processing state
- **SQLite tracking** — persistent conversion state survives restarts

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11 + FastAPI |
| PDF Conversion | [markitdown](https://github.com/microsoft/markitdown) |
| AI Ordering | OpenRouter API (`deepseek/deepseek-chat:free`) |
| Database | SQLite via SQLAlchemy |
| Frontend | TypeScript + Vite 5 |
| Styling | Plain CSS (dark theme) |

---

## Project Structure

```
intoMarkdown/
├── backend/
│   ├── main.py          # FastAPI app + 7 REST endpoints
│   ├── db.py            # SQLAlchemy models (Book, BookFile)
│   ├── ai_sorter.py     # OpenRouter LLM call for filename ordering
│   ├── converter.py     # markitdown PDF→MD conversion + merge
│   └── scanner.py       # books/ folder discovery
├── frontend/
│   └── src/
│       ├── main.ts              # App entry point
│       ├── api.ts               # Typed fetch wrapper
│       ├── components/
│       │   ├── BookCard.ts      # Per-book UI card
│       │   └── BookList.ts      # List with auto-polling
│       └── styles/main.css
├── books/               # Input: place book subfolders here
├── output/              # Output: generated .md files
├── prds/                # Product requirements document
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A free [OpenRouter](https://openrouter.ai) API key

### 1. Clone & install backend

```bash
git clone https://github.com/victorchaw/intoMarkdown.git
cd intoMarkdown

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API key

Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_key_here
```

Get a free key at [openrouter.ai](https://openrouter.ai) — no credit card required for free-tier models.

### 3. Build frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run

```bash
uvicorn backend.main:app --port 8000
```

Open **http://localhost:8000**

---

## Usage

1. Add PDFs to `books/` — either a single file or a subfolder of chapters (see below)
2. Click **Scan Books Folder** — the app discovers all books
3. Click **Convert** on a book (or **Convert All**)
4. Watch the status update in real time: `Discovered → Processing → Done`
5. Click **Preview** to inspect the output, or find the `.md` file in `output/`

### Supported folder structures

**Single PDF** — drop the file directly in `books/`:
```
books/
└── MyBook.pdf              → output/mybook.md
```

**Multi-chapter book** — one subfolder per book, PDFs inside:
```
books/
└── My Book Title/
    ├── Preface.pdf
    ├── Chapter 1 - Introduction.pdf
    ├── Chapter 2 - Core Concepts.pdf
    └── Appendix.pdf        → output/my_book_title.md (merged)
```

Both formats can coexist in `books/` at the same time.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/books` | List all books with status |
| POST | `/api/scan` | Scan `books/` for new books |
| POST | `/api/books/{id}/convert` | Convert a single book |
| POST | `/api/convert-all` | Convert all pending books |
| GET | `/api/books/{id}/files` | List files with AI sort order |
| GET | `/api/books/{id}/preview` | Preview first 3000 chars of output |
| DELETE | `/api/books/{id}/output` | Reset book for re-conversion |

Interactive API docs available at `http://localhost:8000/docs`

---

## Development

To run the frontend in hot-reload mode during development:

```bash
# Terminal 1 — backend
uvicorn backend.main:app --port 8000 --reload

# Terminal 2 — frontend dev server
cd frontend && npm run dev
```

The Vite dev server runs at `http://localhost:5173` and proxies `/api` to the backend.

> **Note:** To enable the API proxy in dev mode, add this to `frontend/vite.config.ts`:
> ```ts
> server: { proxy: { '/api': 'http://localhost:8000' } }
> ```

---

## License

MIT
