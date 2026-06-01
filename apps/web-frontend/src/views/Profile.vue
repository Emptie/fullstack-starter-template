<script setup lang="ts">
import { onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

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
    <Card class="w-full max-w-md">
      <CardHeader class="text-center">
        <CardTitle>Profile</CardTitle>
        <CardDescription>Your account information</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="authStore.user" class="space-y-4">
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

          <Button variant="outline" class="w-full" @click="handleLogout">
            Sign Out
          </Button>
        </div>

        <div v-else class="text-center text-muted-foreground">Loading...</div>
      </CardContent>
    </Card>
  </div>
</template>
