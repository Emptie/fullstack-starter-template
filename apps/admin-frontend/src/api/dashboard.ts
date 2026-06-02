import type { DashboardStats } from "@starter/shared"
import { apiClient } from "./client"

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiClient.get<DashboardStats>("/dashboard/stats")
}
