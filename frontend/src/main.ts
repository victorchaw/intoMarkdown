import "./styles/main.css";
import { api } from "./api";
import { BookList } from "./components/BookList";

const app = document.querySelector<HTMLDivElement>("#app")!;
app.innerHTML = `
  <div class="app">
    <header>
      <h1>PDF → Markdown Converter</h1>
      <div class="actions">
        <button class="btn btn-secondary" id="btn-scan">Scan Books Folder</button>
        <button class="btn btn-primary" id="btn-convert-all">Convert All</button>
      </div>
    </header>
    <div class="book-list" id="book-list"></div>
  </div>
`;

const bookList = new BookList(document.getElementById("book-list")!);

document.getElementById("btn-scan")!.addEventListener("click", async () => {
  const btn = document.getElementById("btn-scan") as HTMLButtonElement;
  btn.disabled = true;
  btn.textContent = "Scanning...";
  try {
    const result = await api.scan();
    await bookList.refresh();
    btn.textContent = `Scan Books Folder (+${result.added} new)`;
    setTimeout(() => { btn.textContent = "Scan Books Folder"; }, 3000);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("btn-convert-all")!.addEventListener("click", async () => {
  const btn = document.getElementById("btn-convert-all") as HTMLButtonElement;
  btn.disabled = true;
  try {
    const result = await api.convertAll();
    btn.textContent = `Queued ${result.queued}`;
    await bookList.refresh();
    setTimeout(() => {
      btn.textContent = "Convert All";
      btn.disabled = false;
    }, 2000);
  } catch {
    btn.disabled = false;
  }
});

bookList.refresh();
