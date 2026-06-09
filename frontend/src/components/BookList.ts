import { api, Book } from "../api";
import { createBookCard } from "./BookCard";

export class BookList {
  private container: HTMLElement;
  private pollInterval: ReturnType<typeof setInterval> | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  async refresh() {
    const books = await api.listBooks();
    this.render(books);
    this.managePoll(books);
  }

  private render(books: Book[]) {
    this.container.innerHTML = "";
    if (books.length === 0) {
      this.container.innerHTML = `<p class="empty-state">No books found. Click "Scan" to discover books.</p>`;
      return;
    }
    books.forEach((book) => {
      this.container.appendChild(createBookCard(book, () => this.refresh()));
    });
  }

  private managePoll(books: Book[]) {
    const hasProcessing = books.some((b) => b.status === "processing");
    if (hasProcessing && !this.pollInterval) {
      this.pollInterval = setInterval(() => this.refresh(), 3000);
    } else if (!hasProcessing && this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  destroy() {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }
}
