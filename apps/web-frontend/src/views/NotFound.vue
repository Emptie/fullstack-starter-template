<script setup lang="ts">
import { useRouter } from "vue-router"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

const router = useRouter()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle class="text-4xl font-bold">404</CardTitle>
        <CardDescription>Page not found</CardDescription>
      </CardHeader>
      <CardContent class="flex justify-center">
        <Button @click="router.push({ name: 'home' })">Back to Home</Button>
      </CardContent>
    </Card>
  </div>
</template>
