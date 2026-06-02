import { apiClient } from "./client"
import type {
  UserCreate,
  UserLogin,
  UserResponse,
  UserUpdate,
  PasswordChange,
  TokenResponse,
} from "@starter/shared"

export async function register(data: UserCreate): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/auth/register", data)
}

export async function login(data: UserLogin): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/auth/login", data)
}

export async function refreshToken(token: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>("/auth/refresh", token)
}

export async function getMe(): Promise<UserResponse> {
  return apiClient.get<UserResponse>("/auth/me")
}

export async function updateProfile(data: UserUpdate): Promise<UserResponse> {
  return apiClient.patch<UserResponse>("/auth/me", data)
}

export async function changePassword(data: PasswordChange): Promise<{ message: string }> {
  return apiClient.post<{ message: string }>("/auth/change-password", data)
}
