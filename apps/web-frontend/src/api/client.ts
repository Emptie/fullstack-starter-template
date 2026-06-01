/**
 * Base API client for the web backend.
 *
 * All API calls go through this client which handles:
 * - Base URL configuration
 * - Content-Type headers
 * - Error handling
 *
 * The backend runs on port 8000. In development, Vite proxies /api requests
 * to avoid CORS issues (see vite.config.ts).
 */

const API_BASE = "/api/v1"

interface ApiError {
  status: number
  message: string
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error: ApiError = {
      status: response.status,
      message: response.statusText,
    }
    throw error
  }

  return response.json() as Promise<T>
}

export const apiClient = {
  get<T>(path: string): Promise<T> {
    return request<T>(path, { method: "GET" })
  },
  post<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    })
  },
}
