<script setup lang="ts">
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import Button from "@/components/ui/button/Button.vue"
import { LayoutDashboard, Users, LogOut, Menu } from "lucide-vue-next"

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const sidebarOpen = ref(false)

const navItems = [
  { name: "Dashboard", icon: LayoutDashboard, route: "admin-dashboard" },
  { name: "Users", icon: Users, route: "admin-users" },
]

function navigateTo(routeName: string) {
  router.push({ name: routeName })
  sidebarOpen.value = false
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: "admin-login" })
}
</script>

<template>
  <div class="flex h-screen bg-background">
    <!-- Mobile overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-black/50 md:hidden"
      @click="sidebarOpen = false"
    />

    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-50 w-64 border-r bg-card transition-transform md:relative md:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex h-14 items-center border-b px-4">
        <span class="text-lg font-semibold">Admin Panel</span>
      </div>
      <nav class="flex flex-col gap-1 p-2">
        <button
          v-for="item in navItems"
          :key="item.route"
          @click="navigateTo(item.route)"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
          :class="route.name === item.route ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'"
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ item.name }}
        </button>
      </nav>
    </aside>

    <!-- Main content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Topbar -->
      <header class="flex h-14 items-center gap-4 border-b px-4">
        <button class="md:hidden" @click="sidebarOpen = !sidebarOpen">
          <Menu class="h-5 w-5" />
        </button>
        <div class="flex-1" />
        <span class="text-sm text-muted-foreground">{{ authStore.user?.email }}</span>
        <Button variant="ghost" size="sm" @click="handleLogout">
          <LogOut class="mr-2 h-4 w-4" />
          Logout
        </Button>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
