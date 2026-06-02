<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { forgotPassword } from "@/api/auth"
import { useFormValidation, required, email as emailRule } from "@/composables/useFormValidation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

const router = useRouter()

const form = ref({ email: "" })
const serverError = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const loading = ref(false)

const { errors, validateAll } = useFormValidation({
  email: [required("Email"), emailRule()],
})

async function handleSubmit() {
  serverError.value = null
  successMessage.value = null
  if (!validateAll(form.value)) return

  loading.value = true
  try {
    const res = await forgotPassword({ email: form.value.email })
    successMessage.value = res.message
  } catch (e: unknown) {
    const err = e as { status?: number; message?: string }
    serverError.value = err.message || "Something went wrong. Please try again."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle>Forgot Password</CardTitle>
        <CardDescription>Enter your email to receive a reset link</CardDescription>
      </CardHeader>
      <CardContent>
        <form v-if="!successMessage" class="space-y-4" @submit.prevent="handleSubmit">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input id="email" v-model="form.email" type="email" placeholder="you@example.com" />
            <p v-if="errors.email" class="text-sm text-destructive">{{ errors.email }}</p>
          </div>

          <div v-if="serverError" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ serverError }}
          </div>

          <Button type="submit" :disabled="loading" class="w-full">
            {{ loading ? "Sending..." : "Send Reset Link" }}
          </Button>
        </form>

        <div v-else class="space-y-4">
          <div class="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
            {{ successMessage }}
          </div>
          <Button variant="outline" class="w-full" @click="router.push('/login')">
            Back to Sign In
          </Button>
        </div>

        <p class="mt-4 text-center text-sm text-muted-foreground">
          Remember your password?
          <RouterLink to="/login" class="text-primary underline hover:no-underline">Sign in</RouterLink>
        </p>
      </CardContent>
    </Card>
  </div>
</template>
