import type { UserLogin, TokenResponse, UserResponse } from "@starter/shared"
import { apiClient } from "./client"

export async function adminLogin(data: UserLogin): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/auth/login", data)
}

export async function refreshToken(token: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/auth/refresh", token)
}

export async function getMe(): Promise<UserResponse> {
  return apiClient.get<UserResponse>("/auth/me")
}
