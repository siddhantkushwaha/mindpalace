import { authHeaders, getToken } from './auth';

const API_BASE = '';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  error?: boolean;
}

export interface ChatRequest {
  message: string;
  chat_history: ChatMessage[];
  source_filter: string | null;
}

export interface ChatResponse {
  reply: string;
  sources: unknown[];
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  source_filter?: string | null;
}

export interface SearchResultItem {
  id: string;
  content: string;
  metadata: {
    document_id: string;
    source: string;
    source_id: string;
    content_type: string;
    title: string;
    url: string;
    chunk_index: number;
    total_chunks: number;
    created_at: number;
    ingested_at: number;
    expires_at: number;
  };
  distance: number;
}

export interface SearchResponse {
  results: SearchResultItem[];
}

export interface StatsResponse {
  collection: string;
  total_chunks: number;
}

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function postSearch(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/api/stats`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Stats failed: ${res.status}`);
  return res.json();
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export function createChatWebSocket(): WebSocket {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const token = getToken() ?? '';
  return new WebSocket(`${proto}//${window.location.host}/ws/chat?token=${encodeURIComponent(token)}`);
}

export const SOURCES = [
  { key: 'gmail', label: 'Gmail', icon: 'mail', color: '#ea4335' },
  { key: 'google_keep', label: 'Keep', icon: 'sticky_note_2', color: '#fbbc04' },
  { key: 'chrome_bookmarks', label: 'Bookmarks', icon: 'bookmark', color: '#4285f4' },
  { key: 'google_drive', label: 'Drive', icon: 'folder', color: '#34a853' },
  { key: 'google_photos', label: 'Photos', icon: 'photo_camera', color: '#a142f4' },
  { key: 'local_photos', label: 'Local Photos', icon: 'image', color: '#9333ea' },
] as const;

export function getSourceInfo(source: string) {
  return SOURCES.find((s) => s.key === source) ?? { key: source, label: source, icon: 'description', color: '#6b7280' };
}

export function formatDate(unix: number): string {
  if (!unix || unix < 0) return '';
  return new Date(unix * 1000).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

// ── Chat History API ───────────────────────────────

export interface ChatSessionSummary {
  id: string;
  title: string;
  source_filter: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatSessionDetail {
  id: string;
  title: string;
  source_filter: string | null;
  created_at: string;
  updated_at: string;
  messages: { id: string; role: string; content: string; created_at: string }[];
}

export async function listChatSessions(): Promise<ChatSessionSummary[]> {
  const res = await fetch('/api/chats', { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to list chats: ${res.status}`);
  return res.json();
}

export async function getChatSession(id: string): Promise<ChatSessionDetail> {
  const res = await fetch(`/api/chats/${encodeURIComponent(id)}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to get chat: ${res.status}`);
  return res.json();
}

export async function deleteChatSession(id: string): Promise<void> {
  const res = await fetch(`/api/chats/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete chat: ${res.status}`);
}

// ── API Key Management ─────────────────────────────

export interface ApiKeyInfo {
  id: string;
  key?: string;
  key_preview?: string;
  label: string;
  created_at: string;
}

export async function createApiKey(label: string = 'default'): Promise<ApiKeyInfo> {
  const res = await fetch('/api/auth/api-keys', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ label }),
  });
  if (!res.ok) throw new Error(`Failed to create API key: ${res.status}`);
  return res.json();
}

export async function listApiKeys(): Promise<ApiKeyInfo[]> {
  const res = await fetch('/api/auth/api-keys', { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to list API keys: ${res.status}`);
  return res.json();
}

export async function deleteApiKey(id: string): Promise<void> {
  const res = await fetch(`/api/auth/api-keys/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete API key: ${res.status}`);
}
