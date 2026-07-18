import { api } from "../../shared/api/client";

export interface Citation {
  document_id: string | null;
  document_name: string;
  page_number: number;
  excerpt: string;
  relevance_score: number;
  rank: number;
}

export interface Message {
  id: string;
  role: "USER" | "ASSISTANT";
  content: string;
  confidence: number | null;
  latency_ms: number | null;
  created_at: string;
  citations: Citation[];
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export const listConversations = async (): Promise<Conversation[]> =>
  (await api.get("/conversations")).data;

export const createConversation = async (): Promise<Conversation> =>
  (await api.post("/conversations", {})).data;

export const listMessages = async (conversationId: string): Promise<Message[]> =>
  (await api.get(`/conversations/${conversationId}/messages`)).data;

export const askQuestion = async (conversationId: string, content: string): Promise<Message> =>
  (await api.post(`/conversations/${conversationId}/messages`, { content })).data;
