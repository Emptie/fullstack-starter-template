<script setup lang="ts">
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useFormValidation, required, email as emailRule, minLength } from "@/composables/useFormValidation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = ref({ email: "", password: "" })
const serverError = ref<string | null>(null)
const loading = ref(false)

const { errors, validateAll } = useFormValidation({
  email: [required("Email"), emailRule()],
  password: [required("Password"), minLength(8)],
})

async function handleLogin() {
  serverError.value = null
  if (!validateAll(form.value)) return

  loading.value = true
  try {
    await authStore.login(form.value.email, form.value.password)
    const redirect = (route.query.redirect as string) || "/profile"
    router.push(redirect)
  } catch (e: unknown) {
    const err = e as { status?: number; message?: string }
    serverError.value = err.message || "Login failed. Please check your credentials."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle>Sign In</CardTitle>
        <CardDescription>Enter your credentials to continue</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="handleLogin">
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
            {{ loading ? "Signing in..." : "Sign In" }}
          </Button>
        </form>

        <p class="mt-4 text-center text-sm text-muted-foreground">
          Don't have an account?
          <RouterLink to="/register" class="text-primary underline hover:no-underline">Register</RouterLink>
        </p>
      </CardContent>
    </Card>
  </div>
</template>
