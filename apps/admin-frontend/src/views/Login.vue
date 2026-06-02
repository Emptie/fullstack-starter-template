<script setup lang="ts">
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { ApiError } from "@/api/client"
import { useFormValidation, required } from "@/composables/useFormValidation"
import Card from "@/components/ui/card/Card.vue"
import CardHeader from "@/components/ui/card/CardHeader.vue"
import CardTitle from "@/components/ui/card/CardTitle.vue"
import CardDescription from "@/components/ui/card/CardDescription.vue"
import CardContent from "@/components/ui/card/CardContent.vue"
import Input from "@/components/ui/input/Input.vue"
import Label from "@/components/ui/label/Label.vue"
import Button from "@/components/ui/button/Button.vue"

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref("")
const password = ref("")
const serverError = ref("")
const loading = ref(false)

const { errors, validateAll } = useFormValidation({
  email: [required("Email")],
  password: [required("Password")],
})

async function handleSubmit() {
  if (!validateAll({ email: email.value, password: password.value })) return

  serverError.value = ""
  loading.value = true

  try {
    await authStore.login(email.value, password.value)
    const raw = (route.query.redirect as string) || "/"
    const redirect = raw.startsWith("/") && !raw.startsWith("//") ? raw : "/"
    router.push(redirect)
  } catch (err) {
    if (err instanceof ApiError) {
      serverError.value = err.message
    } else if (err instanceof Error) {
      serverError.value = err.message
    } else {
      serverError.value = "Login failed"
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle>Admin Login</CardTitle>
        <CardDescription>Sign in to the admin panel</CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div v-if="serverError" class="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {{ serverError }}
          </div>
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input id="email" v-model="email" type="email" placeholder="admin@example.com" />
            <p v-if="errors.email" class="text-sm text-destructive">{{ errors.email }}</p>
          </div>
          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input id="password" v-model="password" type="password" placeholder="••••••••" />
            <p v-if="errors.password" class="text-sm text-destructive">{{ errors.password }}</p>
          </div>
          <Button type="submit" class="w-full" :disabled="loading">
            {{ loading ? "Signing in..." : "Sign in" }}
          </Button>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
