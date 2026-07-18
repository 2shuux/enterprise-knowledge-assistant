import { api } from "../../shared/api/client";

export interface Doc {
  id: string;
  original_name: string;
  mime_type: string;
  file_size_bytes: number;
  status: "PROCESSING" | "INDEXED" | "FAILED";
  error_message: string | null;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
  indexed_at: string | null;
}

export async function listDocuments(): Promise<{ items: Doc[]; total: number }> {
  return (await api.get("/documents")).data;
}

export async function uploadDocument(file: File): Promise<Doc> {
  const form = new FormData();
  form.append("file", file);
  return (await api.post("/documents", form)).data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}

export async function reindexDocument(id: string): Promise<Doc> {
  return (await api.post(`/documents/${id}/reindex`)).data;
}
