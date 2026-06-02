<script setup lang="ts">
import { onMounted, ref, reactive } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useFormValidation, required, minLength, maxLength } from "@/composables/useFormValidation"
import { ApiError } from "@/api/client"
import * as authApi from "@/api/auth"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import LoadingSpinner from "@/components/LoadingSpinner.vue"

const router = useRouter()
const authStore = useAuthStore()

// ── Name editing ──────────────────────────────────────────
const isEditingName = ref(false)
const nameInput = ref("")
const nameSaving = ref(false)

const nameValidation = useFormValidation({
  name: [required("Name"), minLength(1), maxLength(64)],
})

function startEditName() {
  nameInput.value = authStore.user?.name ?? ""
  isEditingName.value = true
}

function cancelEditName() {
  isEditingName.value = false
  nameValidation.errors.name = null
}

async function saveName() {
  if (!nameValidation.validate("name", nameInput.value)) return
  nameSaving.value = true
  try {
    await authStore.updateProfile({ name: nameInput.value })
    isEditingName.value = false
  } catch (err) {
    if (err instanceof ApiError) {
      nameValidation.errors.name = err.message
    }
  } finally {
    nameSaving.value = false
  }
}

// ── Password change ───────────────────────────────────────
const showPasswordForm = ref(false)
const passwordSaving = ref(false)
const passwordSuccess = ref(false)
const passwordForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: "",
})

const passwordValidation = useFormValidation({
  old_password: [required("Current password")],
  new_password: [required("New password"), minLength(8), maxLength(128)],
  confirm_password: [required("Confirm password")],
})

function togglePasswordForm() {
  showPasswordForm.value = !showPasswordForm.value
  passwordSuccess.value = false
  resetPasswordForm()
}

function resetPasswordForm() {
  passwordForm.old_password = ""
  passwordForm.new_password = ""
  passwordForm.confirm_password = ""
  passwordValidation.errors.old_password = null
  passwordValidation.errors.new_password = null
  passwordValidation.errors.confirm_password = null
}

async function savePassword() {
  passwordSuccess.value = false
  const values = { ...passwordForm }
  const valid = passwordValidation.validateAll(values)

  if (values.confirm_password !== values.new_password) {
    passwordValidation.errors.confirm_password = "Passwords do not match"
    return
  }

  if (!valid) return

  passwordSaving.value = true
  try {
    await authApi.changePassword({
      old_password: values.old_password,
      new_password: values.new_password,
    })
    passwordSuccess.value = true
    resetPasswordForm()
    showPasswordForm.value = false
  } catch (err) {
    if (err instanceof ApiError) {
      passwordValidation.errors.old_password = err.message
    }
  } finally {
    passwordSaving.value = false
  }
}

// ── Logout ────────────────────────────────────────────────
function handleLogout() {
  authStore.logout()
  router.push("/login")
}

// ── Init ──────────────────────────────────────────────────
onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    await authStore.fetchProfile()
  }
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-md">
      <CardHeader class="text-center">
        <CardTitle>Profile</CardTitle>
        <CardDescription>Your account information</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="authStore.user" class="space-y-6">
          <!-- Email (read-only) -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <span class="text-muted-foreground">Email</span>
            <span class="font-medium">{{ authStore.user.email }}</span>

            <span class="text-muted-foreground">ID</span>
            <span class="font-mono text-xs">{{ authStore.user.id }}</span>

            <span class="text-muted-foreground">Created</span>
            <span class="font-mono text-xs">
              {{ new Date(authStore.user.created_at).toLocaleDateString() }}
            </span>
          </div>

          <!-- Name (editable) -->
          <div class="space-y-2">
            <Label>Name</Label>
            <div v-if="!isEditingName" class="flex items-center gap-2">
              <span class="font-medium">{{ authStore.user.name }}</span>
              <Button variant="outline" size="sm" @click="startEditName">Edit</Button>
            </div>
            <div v-else class="space-y-2">
              <Input v-model="nameInput" placeholder="Enter your name" />
              <p v-if="nameValidation.errors.name" class="text-sm text-destructive">
                {{ nameValidation.errors.name }}
              </p>
              <div class="flex gap-2">
                <Button size="sm" :disabled="nameSaving" @click="saveName">
                  {{ nameSaving ? "Saving..." : "Save" }}
                </Button>
                <Button variant="outline" size="sm" :disabled="nameSaving" @click="cancelEditName">
                  Cancel
                </Button>
              </div>
            </div>
          </div>

          <!-- Change password (expandable) -->
          <div class="space-y-2">
            <Button variant="outline" class="w-full" @click="togglePasswordForm">
              {{ showPasswordForm ? "Cancel Password Change" : "Change Password" }}
            </Button>

            <div v-if="showPasswordForm" class="space-y-3 rounded-md border p-4">
              <div class="space-y-1">
                <Label for="old-password">Current Password</Label>
                <Input
                  id="old-password"
                  v-model="passwordForm.old_password"
                  type="password"
                  placeholder="Enter current password"
                />
                <p v-if="passwordValidation.errors.old_password" class="text-sm text-destructive">
                  {{ passwordValidation.errors.old_password }}
                </p>
              </div>

              <div class="space-y-1">
                <Label for="new-password">New Password</Label>
                <Input
                  id="new-password"
                  v-model="passwordForm.new_password"
                  type="password"
                  placeholder="Enter new password"
                />
                <p v-if="passwordValidation.errors.new_password" class="text-sm text-destructive">
                  {{ passwordValidation.errors.new_password }}
                </p>
              </div>

              <div class="space-y-1">
                <Label for="confirm-password">Confirm New Password</Label>
                <Input
                  id="confirm-password"
                  v-model="passwordForm.confirm_password"
                  type="password"
                  placeholder="Confirm new password"
                />
                <p
                  v-if="passwordValidation.errors.confirm_password"
                  class="text-sm text-destructive"
                >
                  {{ passwordValidation.errors.confirm_password }}
                </p>
              </div>

              <Button class="w-full" :disabled="passwordSaving" @click="savePassword">
                {{ passwordSaving ? "Updating..." : "Update Password" }}
              </Button>
            </div>

            <p
              v-if="passwordSuccess"
              class="text-center text-sm text-green-600 dark:text-green-400"
            >
              Password updated successfully
            </p>
          </div>

          <!-- Sign out -->
          <Button variant="outline" class="w-full" @click="handleLogout">Sign Out</Button>
        </div>

        <LoadingSpinner v-else text="Loading profile..." />
      </CardContent>
    </Card>
  </div>
</template>
