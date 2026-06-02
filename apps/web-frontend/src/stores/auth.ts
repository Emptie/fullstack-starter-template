import { defineStore } from "pinia"
import { ref, computed } from "vue"
import type { UserResponse } from "@starter/shared"
import router from "@/router"
import * as authApi from "@/api/auth"

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserResponse | null>(null)
  const accessToken = ref(localStorage.getItem("access_token") || "")
  const refreshToken = ref(localStorage.getItem("refresh_token") || "")

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem("access_token", access)
    localStorage.setItem("refresh_token", refresh)
  }

  function clearAuth() {
    user.value = null
    accessToken.value = ""
    refreshToken.value = ""
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
  }

  async function login(email: string, password: string) {
    const res = await authApi.login({ email, password })
    setTokens(res.access_token, res.refresh_token)
    await fetchProfile()
  }

  async function register(data: { email: string; password: string; name: string }) {
    const res = await authApi.register(data)
    setTokens(res.access_token, res.refresh_token)
    await fetchProfile()
  }

  async function fetchProfile() {
    try {
      user.value = await authApi.getMe()
    } catch {
      clearAuth()
    }
  }

  async function updateProfile(data: { name: string }) {
    user.value = await authApi.updateProfile(data)
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      clearAuth()
      router.push({ name: "login" })
      return
    }
    try {
      const res = await authApi.refreshToken(refreshToken.value)
      setTokens(res.access_token, res.refresh_token)
    } catch {
      clearAuth()
      router.push({ name: "login" })
    }
  }

  function logout() {
    clearAuth()
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    register,
    fetchProfile,
    updateProfile,
    refreshAccessToken,
    logout,
  }
})
