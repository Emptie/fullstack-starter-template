/**
 * Base API client for the web backend.
 *
 * Handles:
 * - Base URL configuration
 * - Auth header injection from localStorage
 * - 401 response interception with token refresh
 * - Error body extraction from backend {"detail": "..."} responses
 * - Redirect to /login when refresh fails
 */

import router from "@/router"

const API_BASE = "/api/v1"

/**
 * Typed API error with HTTP status and parsed message.
 *
 * The backend returns {"detail": "..."} on errors — we extract
 * that as the message, falling back to HTTP statusText.
 */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

/**
 * Attempt to parse a JSON error body from the response.
 * FastAPI returns {"detail": "..."} — we extract that string.
 */
async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (body && typeof body.detail === "string") {
      return body.detail
    }
    // Fallback: return the whole body as a string if it's a string
    if (typeof body === "string") {
      return body
    }
  } catch {
    // Response body wasn't valid JSON — fall through
  }
  return response.statusText || `Request failed with status ${response.status}`
}

/**
 * Clear auth tokens from localStorage and redirect to /login.
 * Called when token refresh fails (the user's session is over).
 */
function handleSessionExpired(): void {
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
  router.push({ name: "login" })
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("access_token")
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    if (response.status === 401 && token && path !== "/auth/refresh") {
      // Try refreshing the token
      const refreshed = await tryRefresh()
      if (refreshed) {
        return request<T>(path, options)
      }
      // Refresh failed — session is over
      handleSessionExpired()
    }

    const message = await parseErrorMessage(response)
    throw new ApiError(response.status, message)
  }

  return response.json() as Promise<T>
}

async function tryRefresh(): Promise<boolean> {
  const token = localStorage.getItem("refresh_token")
  if (!token) return false

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(token),
    })
    if (!res.ok) return false

    const data = await res.json()
    localStorage.setItem("access_token", data.access_token)
    localStorage.setItem("refresh_token", data.refresh_token)
    return true
  } catch {
    return false
  }
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
  patch<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    })
  },
}
