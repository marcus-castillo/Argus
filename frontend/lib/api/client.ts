// Typed API client for the CiteCheck backend.
//
// Single source of truth for all backend calls. Every method is fully typed
// against lib/api/types.ts (which mirrors the FastAPI OpenAPI schema).

import type {
  DashboardStats,
  Citation,
  DocumentDetail,
  DocumentList,
  DocumentRead,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const V1 = `${API_BASE}/api/v1`;

export class ApiClientError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let code = "http_error";
    let message = `Request failed with ${res.status}`;
    try {
      const body = await res.json();
      if (body?.error) {
        code = body.error.code ?? code;
        message = body.error.message ?? message;
      } else if (body?.detail) {
        message =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiClientError(res.status, code, message);
  }
  return (await res.json()) as T;
}

export const api = {
  async health(): Promise<{ status: string; database: string }> {
    return handle(await fetch(`${V1}/health`, { cache: "no-store" }));
  },

  async listDocuments(limit = 50, offset = 0): Promise<DocumentList> {
    const res = await fetch(`${V1}/documents?limit=${limit}&offset=${offset}`, {
      cache: "no-store",
    });
    return handle<DocumentList>(res);
  },

  async uploadDocument(file: File): Promise<DocumentRead> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${V1}/documents`, {
      method: "POST",
      body: form,
    });
    return handle<DocumentRead>(res);
  },

  async getDocument(id: string): Promise<DocumentDetail> {
    return handle<DocumentDetail>(
      await fetch(`${V1}/documents/${id}`, { cache: "no-store" }),
    );
  },

  async getCitations(id: string): Promise<Citation[]> {
    return handle<Citation[]>(
      await fetch(`${V1}/documents/${id}/citations`, { cache: "no-store" }),
    );
  },

  async getDashboard(id: string): Promise<DashboardStats> {
    return handle<DashboardStats>(
      await fetch(`${V1}/documents/${id}/dashboard`, { cache: "no-store" }),
    );
  },

  reportUrl(id: string, format: "pdf" | "csv" | "json"): string {
    return `${V1}/documents/${id}/report.${format}`;
  },
};
