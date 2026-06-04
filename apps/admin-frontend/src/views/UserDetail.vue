<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue"
import { useRoute, useRouter } from "vue-router"
import {
  getUser,
  updateUser,
  deleteUser,
  resetUserPassword,
} from "@/api/users"
import type { UserResponse, UserUpdateAdmin } from "@starter/shared"
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

const route = useRoute()
const router = useRouter()
const { addToast } = useToast()

// --- User data ---
const user = ref<UserResponse | null>(null)
const loading = ref(true)
const error = ref("")

async function loadUser() {
  loading.value = true
  error.value = ""
  try {
    const id = Number(route.params.id)
    if (isNaN(id)) {
      error.value = "Invalid user ID"
      return
    }
    user.value = await getUser(id)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      error.value = "User not found"
    } else {
      error.value = "Failed to load user"
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadUser)

function goBack() {
  router.push({ name: "admin-users" })
}

function roleBadgeClass(role?: string): string {
  switch (role) {
    case "admin":
      return "bg-blue-100 text-blue-700"
    case "editor":
      return "bg-green-100 text-green-700"
    default:
      return "bg-gray-100 text-gray-700"
  }
}

// --- Edit dialog ---
const showEditDialog = ref(false)
const editForm = ref({ name: "", email: "", role: "user" as UserRole })
const editError = ref("")
const editLoading = ref(false)

function openEditDialog() {
  if (!user.value) return
  editForm.value = {
    name: user.value.name,
    email: user.value.email,
    role: user.value.role ?? "user",
  }
  editError.value = ""
  showEditDialog.value = true
  nextTick(() => {
    document.getElementById("edit-name")?.focus()
  })
}

async function handleEdit() {
  editError.value = ""
  editLoading.value = true
  try {
    await updateUser(user.value!.id, {
      name: editForm.value.name,
      email: editForm.value.email,
      role: editForm.value.role,
    })
    showEditDialog.value = false
    addToast("User updated", "success")
    await loadUser()
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

// --- Reset password dialog ---
const showResetDialog = ref(false)
const resetForm = ref({ new_password: "", confirm_password: "" })
const resetError = ref("")
const resetLoading = ref(false)

function openResetDialog() {
  resetForm.value = { new_password: "", confirm_password: "" }
  resetError.value = ""
  showResetDialog.value = true
  nextTick(() => {
    document.getElementById("reset-new-password")?.focus()
  })
}

async function handleReset() {
  resetError.value = ""
  if (resetForm.value.new_password !== resetForm.value.confirm_password) {
    resetError.value = "Passwords do not match"
    return
  }
  if (resetForm.value.new_password.length < 8) {
    resetError.value = "Password must be at least 8 characters"
    return
  }
  resetLoading.value = true
  try {
    await resetUserPassword(user.value!.id, {
      new_password: resetForm.value.new_password,
    })
    showResetDialog.value = false
    addToast("Password reset successfully", "success")
  } catch (err) {
    if (err instanceof ApiError) {
      resetError.value = err.message
      addToast(err.message, "error")
    } else {
      resetError.value = "Failed to reset password"
      addToast("Failed to reset password", "error")
    }
  } finally {
    resetLoading.value = false
  }
}

// --- Delete ---
const showDeleteDialog = ref(false)
const deleteLoading = ref(false)

function openDeleteDialog() {
  showDeleteDialog.value = true
}

async function handleDelete() {
  deleteLoading.value = true
  try {
    await deleteUser(user.value!.id)
    addToast("User deleted", "success")
    router.push({ name: "admin-users" })
  } catch (err) {
    if (err instanceof ApiError) {
      addToast(err.message, "error")
    }
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <div>
    <!-- Breadcrumb -->
    <div class="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
      <button class="hover:text-foreground transition-colors" @click="goBack">
        Users
      </button>
      <span>/</span>
      <span class="text-foreground">{{ user?.name ?? "User" }}</span>
    </div>

    <LoadingSpinner v-if="loading" text="Loading user..." />

    <div v-else-if="error" class="text-center py-12">
      <p class="text-muted-foreground mb-4">{{ error }}</p>
      <Button variant="outline" @click="goBack">Back to Users</Button>
    </div>

    <div v-else-if="user">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ user.name }}</h1>
        <div class="flex flex-wrap gap-2">
          <Button variant="outline" @click="openEditDialog">Edit</Button>
          <Button variant="outline" @click="openResetDialog">Reset Password</Button>
          <Button variant="destructive" @click="openDeleteDialog">Delete</Button>
        </div>
      </div>

      <Card class="max-w-lg">
        <CardHeader>
          <CardTitle>User Information</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex justify-between">
            <span class="text-sm text-muted-foreground">Email</span>
            <span class="text-sm">{{ user.email }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-muted-foreground">Role</span>
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="roleBadgeClass(user.role)"
            >
              {{ user.role }}
            </span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-muted-foreground">Created</span>
            <span class="text-sm">{{ new Date(user.created_at).toLocaleDateString() }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-muted-foreground">User ID</span>
            <span class="text-sm font-mono">{{ user.id }}</span>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Edit User Dialog -->
    <div
      v-if="showEditDialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-dialog-title"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showEditDialog = false"
      @keydown.escape="showEditDialog = false"
    >
      <Card class="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle id="edit-dialog-title">Edit User</CardTitle>
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

    <!-- Reset Password Dialog -->
    <div
      v-if="showResetDialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="reset-dialog-title"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showResetDialog = false"
      @keydown.escape="showResetDialog = false"
    >
      <Card class="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle id="reset-dialog-title">Reset Password</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Set a new password for <strong>{{ user?.email }}</strong>.
            This will revoke all active sessions for this user.
          </p>
          <form @submit.prevent="handleReset" class="space-y-4">
            <div v-if="resetError" class="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {{ resetError }}
            </div>
            <div class="space-y-2">
              <Label for="reset-new-password">New Password</Label>
              <Input
                id="reset-new-password"
                v-model="resetForm.new_password"
                type="password"
                required
                minlength="8"
              />
            </div>
            <div class="space-y-2">
              <Label for="reset-confirm-password">Confirm Password</Label>
              <Input
                id="reset-confirm-password"
                v-model="resetForm.confirm_password"
                type="password"
                required
                minlength="8"
              />
            </div>
            <div class="flex gap-2 justify-end">
              <Button type="button" variant="outline" @click="showResetDialog = false">
                Cancel
              </Button>
              <Button type="submit" :disabled="resetLoading">
                {{ resetLoading ? "Resetting..." : "Reset Password" }}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>

    <!-- Delete Confirmation Dialog -->
    <div
      v-if="showDeleteDialog"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showDeleteDialog = false"
      @keydown.escape="showDeleteDialog = false"
    >
      <Card class="w-full max-w-sm mx-4">
        <CardHeader>
          <CardTitle id="delete-dialog-title">Delete User</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Are you sure you want to delete
            <strong>{{ user?.name }}</strong> ({{ user?.email }})?
            This cannot be undone.
          </p>
          <div class="flex gap-2 justify-end">
            <Button variant="outline" @click="showDeleteDialog = false">Cancel</Button>
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
