import { describe, it, expect, beforeEach, vi } from "vitest"
import { createPinia, setActivePinia } from "pinia"
import { useAuthStore } from "@/stores/auth"

// Mock the router module
vi.mock("@/router", () => ({
  default: { push: vi.fn() },
}))

import router from "@/router"

// Mock the auth API module
vi.mock("@/api/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
  refreshToken: vi.fn(),
  getMe: vi.fn(),
}))

import * as authApi from "@/api/auth"

describe("useAuthStore", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it("starts unauthenticated", () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })

  it("clears auth on logout", () => {
    const store = useAuthStore()
    store.accessToken = "test-access"
    store.refreshToken = "test-refresh"
    localStorage.setItem("access_token", "test-access")
    localStorage.setItem("refresh_token", "test-refresh")

    store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.accessToken).toBe("")
    expect(store.refreshToken).toBe("")
    expect(localStorage.getItem("access_token")).toBeNull()
  })

  it("restores tokens from localStorage", () => {
    localStorage.setItem("access_token", "saved-access")
    localStorage.setItem("refresh_token", "saved-refresh")

    // Re-create pinia to trigger store initialization
    setActivePinia(createPinia())
    const store = useAuthStore()

    expect(store.accessToken).toBe("saved-access")
    expect(store.refreshToken).toBe("saved-refresh")
    expect(store.isAuthenticated).toBe(true)
  })

  describe("refreshAccessToken", () => {
    it("clears auth and redirects to login when no refresh token", async () => {
      const store = useAuthStore()
      store.refreshToken = ""

      await store.refreshAccessToken()

      expect(store.isAuthenticated).toBe(false)
      expect(store.accessToken).toBe("")
      expect(router.push).toHaveBeenCalledWith({ name: "login" })
    })

    it("refreshes tokens on success", async () => {
      const store = useAuthStore()
      store.refreshToken = "valid-refresh"

      vi.mocked(authApi.refreshToken).mockResolvedValueOnce({
        access_token: "new-access",
        refresh_token: "new-refresh",
      } as any)

      await store.refreshAccessToken()

      expect(store.accessToken).toBe("new-access")
      expect(store.refreshToken).toBe("new-refresh")
      expect(localStorage.getItem("access_token")).toBe("new-access")
      expect(router.push).not.toHaveBeenCalled()
    })

    it("clears auth and redirects to login on refresh failure", async () => {
      const store = useAuthStore()
      store.accessToken = "old-access"
      store.refreshToken = "bad-refresh"
      localStorage.setItem("access_token", "old-access")
      localStorage.setItem("refresh_token", "bad-refresh")

      vi.mocked(authApi.refreshToken).mockRejectedValueOnce(new Error("fail"))

      await store.refreshAccessToken()

      expect(store.isAuthenticated).toBe(false)
      expect(store.accessToken).toBe("")
      expect(store.refreshToken).toBe("")
      expect(localStorage.getItem("access_token")).toBeNull()
      expect(localStorage.getItem("refresh_token")).toBeNull()
      expect(router.push).toHaveBeenCalledWith({ name: "login" })
    })
  })
})
