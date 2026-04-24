import type { APIResponse, ErrorResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
// Backend URL for direct calls (bypasses Next.js proxy for long-running LLM operations)
const BACKEND_DIRECT = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001/api/v1";
const DEFAULT_TIMEOUT_MS = 180_000; // 3 minutes for LLM-heavy operations

class APIError extends Error {
  status: number;
  correlationId?: string;

  constructor(message: string, status: number, correlationId?: string) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.correlationId = correlationId;
  }
}

function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrf_token="));
  return match ? match.split("=")[1] : null;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const csrfToken = getCsrfToken();
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    // Don't set Content-Type for FormData -- browser sets it with multipart boundary
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers as Record<string, string>),
  };

  // Include CSRF token on state-changing requests (SEC-07)
  if (csrfToken && options.method && options.method !== "GET") {
    headers["X-CSRF-Token"] = csrfToken;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(url, {
      credentials: "include",
      ...options,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new APIError("Request timed out. The operation may still be running.", 408);
    }
    throw err;
  }
  clearTimeout(timeoutId);

  if (!response.ok) {
    let message = "An error occurred";
    let correlationId: string | undefined;

    try {
      const errorBody = await response.json();
      message = errorBody.message || errorBody.detail || message;
      correlationId = errorBody.correlation_id;
    } catch {
      // Response body was not JSON
    }

    throw new APIError(message, response.status, correlationId);
  }

  return response.json();
}

async function requestDirect<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Same as request() but hits backend directly, bypassing Next.js proxy
  // Used for long-running LLM operations that exceed the proxy timeout
  const url = `${BACKEND_DIRECT}${path}`;
  const csrfToken = getCsrfToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (csrfToken && options.method && options.method !== "GET") {
    headers["X-CSRF-Token"] = csrfToken;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(url, {
      credentials: "include",
      ...options,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new APIError("Request timed out. The operation may still be running.", 408);
    }
    throw err;
  }
  clearTimeout(timeoutId);

  if (!response.ok) {
    let message = "An error occurred";
    let correlationId: string | undefined;
    try {
      const errorBody = await response.json();
      message = errorBody.message || errorBody.detail || message;
      correlationId = errorBody.correlation_id;
    } catch {}
    throw new APIError(message, response.status, correlationId);
  }

  return response.json();
}

export const api = {
  get: <T>(path: string) => request<APIResponse<T>>(path),

  post: <T>(path: string, body?: unknown) =>
    request<APIResponse<T>>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown) =>
    request<APIResponse<T>>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string) =>
    request<APIResponse<T>>(path, { method: "DELETE" }),

  // Long-running POST that bypasses Next.js proxy (direct to backend)
  longPost: <T>(path: string, body?: unknown) =>
    requestDirect<APIResponse<T>>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  // Long-running PUT that bypasses Next.js proxy
  longPut: <T>(path: string, body?: unknown) =>
    requestDirect<APIResponse<T>>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  upload: <T>(path: string, formData: FormData) => {
    const csrfToken = getCsrfToken();
    const headers: Record<string, string> = {};
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }
    return request<APIResponse<T>>(path, {
      method: "POST",
      headers,
      body: formData,
    });
  },
};

export { APIError };
