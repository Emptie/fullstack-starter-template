<script setup lang="ts">
import { ref, onMounted } from "vue"
import { listUsers, deleteUser, updateUserRole } from "@/api/users"
import type { UserResponse, UserRole } from "@starter/shared"
import { ApiError } from "@/api/client"
import Button from "@/components/ui/button/Button.vue"
import Input from "@/components/ui/input/Input.vue"
import LoadingSpinner from "@/components/LoadingSpinner.vue"

const users = ref<UserResponse[]>([])
const loading = ref(true)
const search = ref("")

async function loadUsers() {
  loading.value = true
  try {
    users.value = await listUsers({ search: search.value || undefined })
  } finally {
    loading.value = false
  }
}

async function handleDelete(userId: number, userName: string) {
  if (!confirm(`Delete user "${userName}"? This cannot be undone.`)) return
  try {
    await deleteUser(userId)
    await loadUsers()
  } catch (err) {
    if (err instanceof ApiError) {
      alert(err.message)
    }
  }
}

async function handleRoleChange(userId: number, newRole: string) {
  try {
    await updateUserRole(userId, { role: newRole as UserRole })
    await loadUsers()
  } catch (err) {
    if (err instanceof ApiError) {
      alert(err.message)
    }
  }
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Users</h1>
    </div>
    <div class="mb-4">
      <Input
        v-model="search"
        placeholder="Search by name or email..."
        @keyup.enter="loadUsers"
        class="max-w-sm"
      />
    </div>
    <LoadingSpinner v-if="loading" text="Loading users..." />
    <div v-else class="rounded-md border">
      <table class="w-full text-sm">
        <thead class="border-b bg-muted/50">
          <tr>
            <th class="px-4 py-3 text-left font-medium">Name</th>
            <th class="px-4 py-3 text-left font-medium">Email</th>
            <th class="px-4 py-3 text-left font-medium">Role</th>
            <th class="px-4 py-3 text-left font-medium">Created</th>
            <th class="px-4 py-3 text-left font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="border-b last:border-0">
            <td class="px-4 py-3">{{ user.name }}</td>
            <td class="px-4 py-3">{{ user.email }}</td>
            <td class="px-4 py-3">
              <select
                :value="user.role"
                @change="handleRoleChange(user.id, ($event.target as HTMLSelectElement).value)"
                class="rounded-md border px-2 py-1 text-sm"
              >
                <option value="admin">admin</option>
                <option value="editor">editor</option>
                <option value="user">user</option>
              </select>
            </td>
            <td class="px-4 py-3 text-muted-foreground">
              {{ new Date(user.created_at).toLocaleDateString() }}
            </td>
            <td class="px-4 py-3">
              <Button variant="ghost" size="sm" @click="handleDelete(user.id, user.name)">
                Delete
              </Button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">No users found</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
