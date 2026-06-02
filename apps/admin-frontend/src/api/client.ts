/**
 * Base API client for the admin backend.
 *
 * Handles:
 * - Base URL configuration (/admin/api/v1)
 * - Auth header injection from localStorage (admin_ prefixed keys)
 * - 401 response interception with token refresh
 * - Error body extraction from backend {"detail": "..."} responses
 * - Redirect to admin login when refresh fails
 */

import router from "@/router"

const API_BASE = "/admin/api/v1"

/**
 * Typed API error with HTTP status and parsed message.
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
    if (typeof body === "string") {
      return body
    }
  } catch {
    // Response body wasn't valid JSON — fall through
  }
  return response.statusText || `Request failed with status ${response.status}`
}

/**
 * Clear auth tokens from localStorage and redirect to admin login.
 */
function handleSessionExpired(): void {
  localStorage.removeItem("admin_access_token")
  localStorage.removeItem("admin_refresh_token")
  router.push({ name: "admin-login" })
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("admin_access_token")
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
      const refreshed = await tryRefresh()
      if (refreshed) {
        return request<T>(path, options)
      }
      handleSessionExpired()
    }

    const message = await parseErrorMessage(response)
    throw new ApiError(response.status, message)
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

let refreshPromise: Promise<boolean> | null = null

async function tryRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    const token = localStorage.getItem("admin_refresh_token")
    if (!token) return false

    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(token),
      })
      if (!res.ok) return false

      const data = await res.json()
      localStorage.setItem("admin_access_token", data.access_token)
      localStorage.setItem("admin_refresh_token", data.refresh_token)
      return true
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()
  return refreshPromise
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
  delete<T>(path: string): Promise<T> {
    return request<T>(path, { method: "DELETE" })
  },
}
