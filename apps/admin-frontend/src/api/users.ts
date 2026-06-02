import type {
  AdminUserCreate,
  UserResponse,
  UserRole,
  UserUpdateAdmin,
  PaginatedUserResponse,
} from "@starter/shared"
import { apiClient } from "./client"

export async function listUsers(params?: {
  skip?: number
  limit?: number
  search?: string
  role?: UserRole
}): Promise<PaginatedUserResponse> {
  const query = new URLSearchParams()
  if (params?.skip !== undefined) query.set("skip", String(params.skip))
  if (params?.limit !== undefined) query.set("limit", String(params.limit))
  if (params?.search) query.set("search", params.search)
  if (params?.role) query.set("role", params.role)
  const qs = query.toString()
  return apiClient.get<PaginatedUserResponse>(`/users/${qs ? "?" + qs : ""}`)
}

export async function getUser(userId: number): Promise<UserResponse> {
  return apiClient.get<UserResponse>(`/users/${userId}`)
}

export async function createUser(data: AdminUserCreate): Promise<UserResponse> {
  return apiClient.post<UserResponse>("/users/", data)
}

export async function updateUser(
  userId: number,
  data: UserUpdateAdmin,
): Promise<UserResponse> {
  return apiClient.patch<UserResponse>(`/users/${userId}`, data)
}

export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/users/${userId}`)
}
