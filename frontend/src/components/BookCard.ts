import { api, Book } from "../api";

const STATUS_LABELS: Record<string, string> = {
  discovered: "Discovered",
  pending: "Pending",
  processing: "Processing...",
  done: "Done",
  failed: "Failed",
};

function openPreview(book: Book) {
  api.preview(book.id).then((data) => {
    const modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3>${book.folder_name}</h3>
          <small>${data.total_chars.toLocaleString()} total characters</small>
          <button class="close-btn" onclick="this.closest('.modal-overlay').remove()">✕</button>
        </div>
        <pre class="modal-content">${escapeHtml(data.preview)}${data.total_chars > 3000 ? "\n\n[...]" : ""}</pre>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.remove();
    });
  });
}

function escapeHtml(s: string) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function createBookCard(book: Book, onAction: () => void): HTMLElement {
  const card = document.createElement("div");
  card.className = `book-card status-${book.status}`;
  card.dataset.id = String(book.id);

  const isDone = book.status === "done";
  const isProcessing = book.status === "processing";
  const isFailed = book.status === "failed";

  card.innerHTML = `
    <div class="book-info">
      <div class="book-name">${escapeHtml(book.folder_name)}</div>
      <div class="book-meta">
        <span class="status-badge status-${book.status}">${STATUS_LABELS[book.status] ?? book.status}</span>
        <span class="file-count">${book.file_count} PDF${book.file_count !== 1 ? "s" : ""}</span>
        ${book.output_name ? `<span class="output-name">${escapeHtml(book.output_name)}.md</span>` : ""}
      </div>
      ${isFailed && book.error_message ? `<div class="error-msg">${escapeHtml(book.error_message)}</div>` : ""}
    </div>
    <div class="book-actions">
      ${!isDone && !isProcessing ? `<button class="btn btn-primary" data-action="convert">Convert</button>` : ""}
      ${isDone ? `<button class="btn btn-secondary" data-action="preview">Preview</button>` : ""}
      ${isDone || isFailed ? `<button class="btn btn-danger" data-action="reconvert">Re-convert</button>` : ""}
    </div>
  `;

  card.querySelector("[data-action='convert']")?.addEventListener("click", async () => {
    await api.convertBook(book.id);
    onAction();
  });

  card.querySelector("[data-action='preview']")?.addEventListener("click", () => {
    openPreview(book);
  });

  card.querySelector("[data-action='reconvert']")?.addEventListener("click", async () => {
    await api.resetBook(book.id);
    await api.convertBook(book.id);
    onAction();
  });

  return card;
}
