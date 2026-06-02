<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
} from "@/api/users"
import type { UserResponse } from "@starter/shared"
import type { UserRole } from "@/api/users"
import { ApiError } from "@/api/client"
import Button from "@/components/ui/button/Button.vue"
import Input from "@/components/ui/input/Input.vue"
import Label from "@/components/ui/label/Label.vue"
import Card from "@/components/ui/card/Card.vue"
import CardHeader from "@/components/ui/card/CardHeader.vue"
import CardTitle from "@/components/ui/card/CardTitle.vue"
import CardContent from "@/components/ui/card/CardContent.vue"
import LoadingSpinner from "@/components/LoadingSpinner.vue"
import Toast from "@/components/Toast.vue"
import { useToast } from "@/composables/useToast"

const { addToast } = useToast()

// --- List state ---
const users = ref<UserResponse[]>([])
const totalUsers = ref(0)
const loading = ref(true)
const search = ref("")
const currentPage = ref(1)
const pageSize = 10

const totalPages = computed(() => Math.max(1, Math.ceil(totalUsers.value / pageSize)))

async function loadUsers() {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize
    const result = await listUsers({
      skip,
      limit: pageSize,
      search: search.value || undefined,
    })
    users.value = result.items
    totalUsers.value = result.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadUsers()
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadUsers()
}

// --- Create user dialog ---
const showCreateDialog = ref(false)
const createForm = ref({ name: "", email: "", password: "", role: "user" as string })
const createError = ref("")
const createLoading = ref(false)

function openCreateDialog() {
  createForm.value = { name: "", email: "", password: "", role: "user" as UserRole }
  createError.value = ""
  showCreateDialog.value = true
}

async function handleCreate() {
  createError.value = ""
  createLoading.value = true
  try {
    await createUser({ ...createForm.value, role: createForm.value.role as UserRole })
    showCreateDialog.value = false
    addToast("User created", "success")
    await loadUsers()
  } catch (err) {
    if (err instanceof ApiError) {
      createError.value = err.message
      addToast(err.message, "error")
    } else {
      createError.value = "Failed to create user"
      addToast("Failed to create user", "error")
    }
  } finally {
    createLoading.value = false
  }
}

// --- Edit user dialog ---
const showEditDialog = ref(false)
const editForm = ref({ id: 0, name: "", email: "", role: "user" as UserRole })
const editError = ref("")
const editLoading = ref(false)

function openEditDialog(user: UserResponse) {
  editForm.value = { id: user.id, name: user.name, email: user.email, role: user.role ?? "user" }
  editError.value = ""
  showEditDialog.value = true
}

async function handleEdit() {
  editError.value = ""
  editLoading.value = true
  try {
    await updateUser(editForm.value.id, {
      name: editForm.value.name,
      email: editForm.value.email,
      role: editForm.value.role,
    })
    showEditDialog.value = false
    addToast("User updated", "success")
    await loadUsers()
  } catch (err) {
    if (err instanceof ApiError) {
      editError.value = err.message
      addToast(err.message, "error")
    } else {
      editError.value = "Failed to update user"
      addToast("Failed to update user", "error")
    }
  } finally {
    editLoading.value = false
  }
}

// --- Delete ---
const deleteTarget = ref<UserResponse | null>(null)
const deleteLoading = ref(false)

function confirmDelete(user: UserResponse) {
  deleteTarget.value = user
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await deleteUser(deleteTarget.value.id)
    deleteTarget.value = null
    addToast("User deleted", "success")
    await loadUsers()
  } catch (err) {
    if (err instanceof ApiError) {
      addToast(err.message, "error")
    }
  } finally {
    deleteLoading.value = false
  }
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Users</h1>
      <Button @click="openCreateDialog">Create User</Button>
    </div>

    <div class="mb-4">
      <Input
        v-model="search"
        placeholder="Search by name or email..."
        @keyup.enter="handleSearch"
        class="max-w-sm"
      />
    </div>

    <LoadingSpinner v-if="loading" text="Loading users..." />

    <div v-else>
      <div class="rounded-md border">
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
            <tr
              v-for="user in users"
              :key="user.id"
              class="border-b last:border-0 hover:bg-muted/30 cursor-pointer"
              @click="openEditDialog(user)"
            >
              <td class="px-4 py-3">{{ user.name }}</td>
              <td class="px-4 py-3">{{ user.email }}</td>
              <td class="px-4 py-3">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="{
                    'bg-blue-100 text-blue-700': user.role === 'admin',
                    'bg-green-100 text-green-700': user.role === 'editor',
                    'bg-gray-100 text-gray-700': user.role === 'user',
                  }"
                >
                  {{ user.role }}
                </span>
              </td>
              <td class="px-4 py-3 text-muted-foreground">
                {{ new Date(user.created_at).toLocaleDateString() }}
              </td>
              <td class="px-4 py-3">
                <Button variant="ghost" size="sm" @click.stop="confirmDelete(user)">
                  Delete
                </Button>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">
                No users found
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between mt-4">
        <p class="text-sm text-muted-foreground">
          {{ totalUsers }} user{{ totalUsers !== 1 ? "s" : "" }} total
        </p>
        <div class="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="currentPage <= 1"
            @click="goToPage(currentPage - 1)"
          >
            Previous
          </Button>
          <span class="text-sm text-muted-foreground">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          <Button
            variant="outline"
            size="sm"
            :disabled="currentPage >= totalPages"
            @click="goToPage(currentPage + 1)"
          >
            Next
          </Button>
        </div>
      </div>
    </div>

    <!-- Create User Dialog -->
    <div
      v-if="showCreateDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showCreateDialog = false"
    >
      <Card class="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle>Create User</CardTitle>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleCreate" class="space-y-4">
            <div v-if="createError" class="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {{ createError }}
            </div>
            <div class="space-y-2">
              <Label for="create-name">Name</Label>
              <Input id="create-name" v-model="createForm.name" required />
            </div>
            <div class="space-y-2">
              <Label for="create-email">Email</Label>
              <Input id="create-email" v-model="createForm.email" type="email" required />
            </div>
            <div class="space-y-2">
              <Label for="create-password">Password</Label>
              <Input id="create-password" v-model="createForm.password" type="password" required />
            </div>
            <div class="space-y-2">
              <Label for="create-role">Role</Label>
              <select
                id="create-role"
                v-model="createForm.role"
                class="w-full rounded-md border px-3 py-2 text-sm"
              >
                <option value="user">User</option>
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div class="flex gap-2 justify-end">
              <Button type="button" variant="outline" @click="showCreateDialog = false">
                Cancel
              </Button>
              <Button type="submit" :disabled="createLoading">
                {{ createLoading ? "Creating..." : "Create" }}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>

    <!-- Edit User Dialog -->
    <div
      v-if="showEditDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showEditDialog = false"
    >
      <Card class="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle>Edit User</CardTitle>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleEdit" class="space-y-4">
            <div v-if="editError" class="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {{ editError }}
            </div>
            <div class="space-y-2">
              <Label for="edit-name">Name</Label>
              <Input id="edit-name" v-model="editForm.name" required />
            </div>
            <div class="space-y-2">
              <Label for="edit-email">Email</Label>
              <Input id="edit-email" v-model="editForm.email" type="email" required />
            </div>
            <div class="space-y-2">
              <Label for="edit-role">Role</Label>
              <select
                id="edit-role"
                v-model="editForm.role"
                class="w-full rounded-md border px-3 py-2 text-sm"
              >
                <option value="user">User</option>
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div class="flex gap-2 justify-end">
              <Button type="button" variant="outline" @click="showEditDialog = false">
                Cancel
              </Button>
              <Button type="submit" :disabled="editLoading">
                {{ editLoading ? "Saving..." : "Save" }}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>

    <!-- Delete Confirmation Dialog -->
    <div
      v-if="deleteTarget"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="deleteTarget = null"
    >
      <Card class="w-full max-w-sm mx-4">
        <CardHeader>
          <CardTitle>Delete User</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Are you sure you want to delete
            <strong>{{ deleteTarget.name }}</strong> ({{ deleteTarget.email }})?
            This cannot be undone.
          </p>
          <div class="flex gap-2 justify-end">
            <Button variant="outline" @click="deleteTarget = null">Cancel</Button>
            <Button variant="destructive" :disabled="deleteLoading" @click="handleDelete">
              {{ deleteLoading ? "Deleting..." : "Delete" }}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
    <Toast />
  </div>
</template>
