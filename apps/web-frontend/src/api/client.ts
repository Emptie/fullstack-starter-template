/**
 * Base API client for the web backend.
 *
 * Handles:
 * - Base URL configuration
 * - Auth header injection from localStorage
 * - 401 response interception with token refresh
 */

const API_BASE = "/api/v1"

interface ApiError {
  status: number
  message: string
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
    if (response.status === 401 && token && !path.includes("/auth/")) {
      // Try refreshing the token
      const refreshed = await tryRefresh()
      if (refreshed) {
        return request<T>(path, options)
      }
    }

    const error: ApiError = {
      status: response.status,
      message: response.statusText,
    }
    throw error
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
}
