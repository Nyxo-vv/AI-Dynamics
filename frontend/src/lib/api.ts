const API_BASE = "http://localhost:9100/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// Briefings
export function getBriefing(date: string) {
  return request<import("./types.ts").Briefing>(`/briefings/${date}`);
}

export function getRecentBriefings(days = 7) {
  return request<{ items: import("./types.ts").BriefingStatus[] }>(
    `/briefings/recent?days=${days}`
  );
}

export function generateBriefing(date: string) {
  return request<import("./types.ts").Briefing>("/briefings/generate", {
    method: "POST",
    body: JSON.stringify({ date }),
  });
}

export function searchBriefings(q: string, date?: string) {
  const params = new URLSearchParams({ q });
  if (date) params.set("date", date);
  return request<{ items: import("./types.ts").Article[]; total: number }>(
    `/briefings/search?${params}`
  );
}

// Articles
export function getArticles(params?: {
  page?: number;
  per_page?: number;
  tag?: string;
  source_id?: number;
  starred?: boolean;
  search?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.per_page) searchParams.set("per_page", String(params.per_page));
  if (params?.tag) searchParams.set("category", params.tag);
  if (params?.source_id) searchParams.set("source_id", String(params.source_id));
  if (params?.starred) searchParams.set("is_starred", "true");
  if (params?.search) searchParams.set("search", params.search);
  const qs = searchParams.toString();
  return request<{ items: import("./types.ts").Article[]; total: number; page: number; per_page: number; pages: number }>(
    `/articles${qs ? `?${qs}` : ""}`
  );
}

export function updateArticle(id: number, data: { is_read?: boolean; is_starred?: boolean }) {
  return request<import("./types.ts").Article>(`/articles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// Sources
export function getSources() {
  return request<{ items: import("./types.ts").Source[] }>("/sources");
}

// Fetch
export function triggerFetch() {
  return request<{ message: string }>("/fetch/run", { method: "POST" });
}

export function getFetchStatus() {
  return request<import("./types.ts").FetchStatus>("/fetch/status");
}

export function getBacklogStatus(date?: string) {
  const params = date ? `?date=${date}` : "";
  return request<{ unprocessed: number; total: number }>(`/fetch/backlog${params}`);
}
