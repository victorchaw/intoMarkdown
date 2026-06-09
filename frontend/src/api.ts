const BASE = "/api";

export interface BookFile {
  id: number;
  filename: string;
  sort_order: number | null;
  included: boolean;
  skip_reason: string | null;
}

export interface Book {
  id: number;
  folder_name: string;
  output_name: string | null;
  status: "discovered" | "pending" | "processing" | "done" | "failed";
  error_message: string | null;
  file_count: number;
}

export interface PreviewResponse {
  preview: string;
  total_chars: number;
}

async function req<T>(path: string, method = "GET"): Promise<T> {
  const res = await fetch(BASE + path, { method });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listBooks: () => req<Book[]>("/books"),
  scan: () => req<{ added: number; total: number }>("/scan", "POST"),
  convertBook: (id: number) => req<{ status: string }>(`/books/${id}/convert`, "POST"),
  convertAll: () => req<{ queued: number }>("/convert-all", "POST"),
  getFiles: (id: number) => req<BookFile[]>(`/books/${id}/files`),
  preview: (id: number) => req<PreviewResponse>(`/books/${id}/preview`),
  resetBook: (id: number) => req<{ status: string }>(`/books/${id}/output`, "DELETE"),
};
