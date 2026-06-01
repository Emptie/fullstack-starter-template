<script setup lang="ts">
import { onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    await authStore.fetchProfile()
  }
})

function handleLogout() {
  authStore.logout()
  router.push("/login")
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <div class="w-full max-w-md space-y-6 p-8">
      <div class="text-center">
        <h1 class="text-2xl font-bold tracking-tight">Profile</h1>
        <p class="mt-1 text-sm text-muted-foreground">Your account information</p>
      </div>

      <div v-if="authStore.user" class="rounded-lg border bg-card p-6 shadow-sm space-y-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <span class="text-muted-foreground">Name</span>
          <span class="font-medium">{{ authStore.user.name }}</span>

          <span class="text-muted-foreground">Email</span>
          <span class="font-medium">{{ authStore.user.email }}</span>

          <span class="text-muted-foreground">ID</span>
          <span class="font-mono text-xs">{{ authStore.user.id }}</span>

          <span class="text-muted-foreground">Created</span>
          <span class="font-mono text-xs">{{ new Date(authStore.user.created_at).toLocaleDateString() }}</span>
        </div>
      </div>

      <div v-else class="text-center text-muted-foreground">Loading...</div>

      <button
        class="w-full rounded-md border border-destructive px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/10"
        @click="handleLogout"
      >
        Sign Out
      </button>
    </div>
  </div>
</template>
