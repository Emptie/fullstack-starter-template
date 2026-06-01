import { describe, it, expect, beforeEach } from "vitest"
import { createPinia, setActivePinia } from "pinia"
import { useAuthStore } from "@/stores/auth"

describe("useAuthStore", () => {
  beforeEach(() => {
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
})
