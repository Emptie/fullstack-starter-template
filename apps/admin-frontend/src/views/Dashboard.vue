<script setup lang="ts">
import { ref, onMounted } from "vue"
import { getDashboardStats } from "@/api/dashboard"
import type { DashboardStats } from "@starter/shared"
import Card from "@/components/ui/card/Card.vue"
import CardHeader from "@/components/ui/card/CardHeader.vue"
import CardTitle from "@/components/ui/card/CardTitle.vue"
import CardContent from "@/components/ui/card/CardContent.vue"
import LoadingSpinner from "@/components/LoadingSpinner.vue"

const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Dashboard</h1>
    <LoadingSpinner v-if="loading" text="Loading stats..." />
    <div v-else-if="stats" class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ stats.total_users }}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">Admins</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ stats.admin_count }}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">Editors</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ stats.editor_count }}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">Recent (30d)</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ stats.recent_registrations }}</div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
