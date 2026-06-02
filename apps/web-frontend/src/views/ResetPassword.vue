<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter, useRoute } from "vue-router"
import { resetPassword } from "@/api/auth"
import { useFormValidation, required, minLength } from "@/composables/useFormValidation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

const router = useRouter()
const route = useRoute()

const token = ref("")
const form = ref({ password: "", confirmPassword: "" })
const serverError = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const loading = ref(false)

const { errors, validateAll } = useFormValidation({
  password: [required("Password"), minLength(8)],
  confirmPassword: [required("Confirm password")],
})

onMounted(() => {
  token.value = (route.query.token as string) || ""
  if (!token.value) {
    serverError.value = "Invalid or missing reset token. Please request a new reset link."
  }
})

async function handleSubmit() {
  serverError.value = null
  successMessage.value = null

  if (!token.value) {
    serverError.value = "Invalid or missing reset token."
    return
  }

  if (!validateAll(form.value)) return

  if (form.value.password !== form.value.confirmPassword) {
    errors.confirmPassword = "Passwords do not match"
    return
  }

  loading.value = true
  try {
    const res = await resetPassword({
      token: token.value,
      new_password: form.value.password,
    })
    successMessage.value = res.message
  } catch (e: unknown) {
    const err = e as { status?: number; message?: string }
    serverError.value = err.message || "Failed to reset password. The link may have expired."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle>Reset Password</CardTitle>
        <CardDescription>Enter your new password</CardDescription>
      </CardHeader>
      <CardContent>
        <form v-if="!successMessage" class="space-y-4" @submit.prevent="handleSubmit">
          <div class="space-y-2">
            <Label for="password">New Password</Label>
            <Input id="password" v-model="form.password" type="password" placeholder="••••••••" />
            <p v-if="errors.password" class="text-sm text-destructive">{{ errors.password }}</p>
          </div>

          <div class="space-y-2">
            <Label for="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              placeholder="••••••••"
            />
            <p v-if="errors.confirmPassword" class="text-sm text-destructive">
              {{ errors.confirmPassword }}
            </p>
          </div>

          <div v-if="serverError" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ serverError }}
          </div>

          <Button type="submit" :disabled="loading || !token" class="w-full">
            {{ loading ? "Resetting..." : "Reset Password" }}
          </Button>
        </form>

        <div v-else class="space-y-4">
          <div class="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
            {{ successMessage }}
          </div>
          <Button class="w-full" @click="router.push('/login')">
            Sign In with New Password
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
