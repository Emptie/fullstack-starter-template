<script setup lang="ts">
import { ref, onMounted } from "vue"
import { getHealth } from "../api/health"
import type { HealthCheck } from "@starter/shared"

const health = ref<HealthCheck | null>(null)
const error = ref<string | null>(null)
const loading = ref(true)

async function checkHealth() {
  loading.value = true
  error.value = null
  try {
    health.value = await getHealth()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to connect to backend"
  } finally {
    loading.value = false
  }
}

onMounted(checkHealth)
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <div class="w-full max-w-md space-y-6 p-8">
      <div class="text-center">
        <h1 class="text-3xl font-bold tracking-tight">Fullstack Starter</h1>
        <p class="mt-2 text-muted-foreground">Vue 3 + FastAPI monorepo template</p>
      </div>

      <!-- Health Check Card -->
      <div class="rounded-lg border bg-card p-6 shadow-sm">
        <h2 class="mb-4 text-lg font-semibold">Backend Health Check</h2>

        <div v-if="loading" class="text-muted-foreground">Loading...</div>

        <div v-else-if="error" class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-full bg-red-500"></span>
            <span class="font-medium text-red-500">Disconnected</span>
          </div>
          <p class="text-sm text-muted-foreground">{{ error }}</p>
          <button
            class="mt-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
            @click="checkHealth"
          >
            Retry
          </button>
        </div>

        <div v-else-if="health" class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-full bg-green-500"></span>
            <span class="font-medium text-green-600">Connected</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <span class="text-muted-foreground">Status</span>
            <span class="font-mono">{{ health.status }}</span>
            <span class="text-muted-foreground">Version</span>
            <span class="font-mono">{{ health.version }}</span>
            <span class="text-muted-foreground">Database</span>
            <span class="font-mono">{{ health.database }}</span>
          </div>
        </div>
      </div>

      <p class="text-center text-sm text-muted-foreground">
        Edit <code class="rounded bg-muted px-1 py-0.5">src/views/Home.vue</code> to get started
      </p>
    </div>
  </div>
</template>
