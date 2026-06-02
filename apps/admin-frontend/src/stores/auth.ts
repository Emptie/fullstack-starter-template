import { defineStore } from "pinia"
import { ref, computed } from "vue"
import type { UserResponse } from "@starter/shared"
import * as authApi from "@/api/auth"

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserResponse | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem("admin_access_token"))
  const refreshToken = ref<string | null>(localStorage.getItem("admin_refresh_token"))

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem("admin_access_token", access)
    localStorage.setItem("admin_refresh_token", refresh)
  }

  function clearAuth() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem("admin_access_token")
    localStorage.removeItem("admin_refresh_token")
  }

  async function login(email: string, password: string) {
    const tokens = await authApi.adminLogin({ email, password })
    setTokens(tokens.access_token, tokens.refresh_token)
    await fetchProfile()
  }

  async function fetchProfile() {
    const profile = await authApi.getMe()
    if (profile.role !== "admin") {
      clearAuth()
      throw new Error("Admin access required")
    }
    user.value = profile
  }

  async function refreshAccessToken() {
    const token = localStorage.getItem("admin_refresh_token")
    if (!token) return false

    try {
      const tokens = await authApi.refreshToken(token)
      setTokens(tokens.access_token, tokens.refresh_token)
      return true
    } catch {
      clearAuth()
      return false
    }
  }

  async function logout() {
    clearAuth()
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    fetchProfile,
    refreshAccessToken,
    logout,
  }
})
