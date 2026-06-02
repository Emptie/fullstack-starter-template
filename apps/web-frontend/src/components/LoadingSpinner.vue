<script setup lang="ts">
interface Props {
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: "Loading...",
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-8">
    <div
      class="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent"
    />
    <p v-if="text" class="text-sm text-muted-foreground">{{ text }}</p>
  </div>
</template>
