import { describe, it, expect, beforeEach, vi } from "vitest"
import { ApiError, apiClient } from "@/api/client"

// Mock the router module
vi.mock("@/router", () => ({
  default: { push: vi.fn() },
}))

// Import the mocked router so we can assert on it
import router from "@/router"

describe("ApiError", () => {
  it("is an Error subclass with status and message", () => {
    const err = new ApiError(422, "Validation error")
    expect(err).toBeInstanceOf(Error)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.name).toBe("ApiError")
    expect(err.status).toBe(422)
    expect(err.message).toBe("Validation error")
  })
})

describe("apiClient error handling", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  async function mockFetchOnce(body: unknown, status: number, statusText = "") {
    const response = new Response(JSON.stringify(body), {
      status,
      statusText,
      headers: { "Content-Type": "application/json" },
    })
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)
  }

  it("extracts detail from backend error body", async () => {
    await mockFetchOnce({ detail: "Email already registered" }, 409)

    try {
      await apiClient.post("/auth/register", { email: "a@b.com" })
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.status).toBe(409)
      expect(apiErr.message).toBe("Email already registered")
    }
  })

  it("falls back to statusText when body has no detail", async () => {
    await mockFetchOnce({}, 500, "Internal Server Error")

    try {
      await apiClient.get("/some-path")
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.status).toBe(500)
      expect(apiErr.message).toBe("Internal Server Error")
    }
  })

  it("falls back to generated message when statusText is also empty", async () => {
    await mockFetchOnce({}, 503, "")

    try {
      await apiClient.get("/some-path")
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.status).toBe(503)
      expect(apiErr.message).toBe("Request failed with status 503")
    }
  })

  it("handles string body in error response", async () => {
    const response = new Response('"Something went wrong"', {
      status: 400,
      statusText: "Bad Request",
      headers: { "Content-Type": "application/json" },
    })
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)

    try {
      await apiClient.get("/some-path")
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.status).toBe(400)
      expect(apiErr.message).toBe("Something went wrong")
    }
  })

  it("handles non-JSON body by falling back to statusText", async () => {
    const response = new Response("not json", {
      status: 502,
      statusText: "Bad Gateway",
    })
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)

    try {
      await apiClient.get("/some-path")
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.message).toBe("Bad Gateway")
    }
  })
})

describe("apiClient request", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it("makes fetch with correct URL and headers", async () => {
    const response = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)

    await apiClient.get("/test")

    expect(fetchSpy).toHaveBeenCalledWith("/admin/api/v1/test", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
  })

  it("includes Authorization header when token is present", async () => {
    localStorage.setItem("admin_access_token", "test-token")
    const response = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)

    await apiClient.get("/protected")

    expect(fetchSpy).toHaveBeenCalledWith("/admin/api/v1/protected", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer test-token",
      },
    })
  })

  it("handles 204 No Content", async () => {
    const response = new Response(null, { status: 204 })
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)

    const result = await apiClient.delete("/resource/1")
    expect(result).toBeUndefined()
  })
})

describe("apiClient 401 refresh flow", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it("tries refresh on 401 and retries the request", async () => {
    localStorage.setItem("admin_access_token", "old-token")
    localStorage.setItem("admin_refresh_token", "refresh-token")

    // First call: 401
    const unauthorized = new Response(JSON.stringify({ detail: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    })
    // Refresh call: success
    const refreshOk = new Response(
      JSON.stringify({ access_token: "new-token", refresh_token: "new-refresh" }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    )
    // Retry call: success
    const retryOk = new Response(JSON.stringify({ data: "result" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })

    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(unauthorized)
      .mockResolvedValueOnce(refreshOk)
      .mockResolvedValueOnce(retryOk)

    const result = await apiClient.get("/protected")
    expect(result).toEqual({ data: "result" })
    expect(localStorage.getItem("admin_access_token")).toBe("new-token")
    expect(localStorage.getItem("admin_refresh_token")).toBe("new-refresh")
  })

  it("calls handleSessionExpired when refresh fails on 401", async () => {
    localStorage.setItem("admin_access_token", "old-token")
    localStorage.setItem("admin_refresh_token", "bad-refresh")

    // First call: 401
    const unauthorized = new Response(JSON.stringify({ detail: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    })
    // Refresh call: failure
    const refreshFail = new Response(null, { status: 401 })

    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(unauthorized)
      .mockResolvedValueOnce(refreshFail)

    try {
      await apiClient.get("/protected")
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
    }

    expect(router.push).toHaveBeenCalledWith({ name: "admin-login" })
    expect(localStorage.getItem("admin_access_token")).toBeNull()
    expect(localStorage.getItem("admin_refresh_token")).toBeNull()
  })
})

describe("tryRefresh", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it("returns false when no refresh token is stored", async () => {
    // Make a request with an access token but no refresh token.
    // The 401 flow should fail to refresh and throw.
    localStorage.setItem("admin_access_token", "some-token")

    const unauthorized = new Response(JSON.stringify({ detail: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    })

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(unauthorized)

    try {
      await apiClient.get("/protected")
      expect.unreachable("Should have thrown")
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      expect((err as ApiError).status).toBe(401)
    }

    // Session expired handler should have been called
    expect(router.push).toHaveBeenCalledWith({ name: "admin-login" })
  })
})
