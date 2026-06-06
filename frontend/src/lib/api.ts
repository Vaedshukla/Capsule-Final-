// Central API client — typed interface to the Capsule backend
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  color: string | null;
  created_at: string;
}

export interface Capsule {
  id: string;
  title: string;
  summary: string;
  decisions: string | null;
  insights: string | null;
  importance_score: number;
  access_count: number;
  created_at: string;
}

export interface SearchResult {
  id: string;
  type: "capsule" | "message";
  title: string;
  content: string;
  similarity_score: number;
  project_id: string | null;
  conversation_id: string | null;
  source_slug: string | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

export const capsuleApi = {
  // Projects
  getProjects: () => apiFetch<Project[]>("/api/v1/projects/"),
  createProject: (data: { name: string; description?: string; color?: string }) =>
    apiFetch<Project>("/api/v1/projects/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Capsules
  getCapsules: (projectId?: string) => {
    const q = projectId ? `?project_id=${projectId}` : "";
    return apiFetch<Capsule[]>(`/api/v1/capsules/${q}`);
  },
  getCapsule: (id: string) => apiFetch<Capsule>(`/api/v1/capsules/${id}`),
  compressCapsule: (conversationId: string) =>
    apiFetch<Capsule>(`/api/v1/capsules/compress/${conversationId}`, { method: "POST" }),

  // Retrieval
  search: (query: string, projectId?: string, limit = 10) =>
    apiFetch<SearchResponse>(
      `/api/v1/retrieval/search?q=${encodeURIComponent(query)}${projectId ? `&project_id=${projectId}` : ""}&limit=${limit}`
    ),

  // Health
  health: () => apiFetch<{ status: string; embedding_provider: string }>("/health"),
};
