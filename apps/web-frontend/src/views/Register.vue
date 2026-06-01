<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useFormValidation, required, email as emailRule, minLength, maxLength } from "@/composables/useFormValidation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ name: "", email: "", password: "" })
const serverError = ref<string | null>(null)
const loading = ref(false)

const { errors, validateAll } = useFormValidation({
  name: [required("Name"), minLength(2), maxLength(64)],
  email: [required("Email"), emailRule()],
  password: [required("Password"), minLength(8)],
})

async function handleRegister() {
  serverError.value = null
  if (!validateAll(form.value)) return

  loading.value = true
  try {
    await authStore.register(form.value)
    router.push("/profile")
  } catch (e: unknown) {
    const err = e as { status?: number; message?: string }
    serverError.value = err.message || "Registration failed. Please try again."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle>Create Account</CardTitle>
        <CardDescription>Register to get started</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="handleRegister">
          <div class="space-y-2">
            <Label for="name">Name</Label>
            <Input id="name" v-model="form.name" type="text" placeholder="Your name" />
            <p v-if="errors.name" class="text-sm text-destructive">{{ errors.name }}</p>
          </div>

          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input id="email" v-model="form.email" type="email" placeholder="you@example.com" />
            <p v-if="errors.email" class="text-sm text-destructive">{{ errors.email }}</p>
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input id="password" v-model="form.password" type="password" placeholder="••••••••" />
            <p v-if="errors.password" class="text-sm text-destructive">{{ errors.password }}</p>
          </div>

          <div v-if="serverError" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ serverError }}
          </div>

          <Button type="submit" :disabled="loading" class="w-full">
            {{ loading ? "Creating account..." : "Create Account" }}
          </Button>
        </form>

        <p class="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?
          <RouterLink to="/login" class="text-primary underline hover:no-underline">Sign in</RouterLink>
        </p>
      </CardContent>
    </Card>
  </div>
</template>
