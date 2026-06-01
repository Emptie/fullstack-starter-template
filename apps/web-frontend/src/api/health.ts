import { apiClient } from "./client"
import type { HealthCheck } from "@starter/shared"

export async function getHealth(): Promise<HealthCheck> {
  return apiClient.get<HealthCheck>("/health")
}
