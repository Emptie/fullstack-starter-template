<script setup lang="ts">
import { useToast } from "@/composables/useToast"

const { toasts, removeToast } = useToast()
</script>

<template>
  <div class="fixed bottom-4 right-4 z-[60] flex flex-col-reverse gap-2">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium shadow-lg cursor-pointer"
        :class="{
          'bg-green-100 text-green-800': toast.type === 'success',
          'bg-red-100 text-red-800': toast.type === 'error',
        }"
        @click="removeToast(toast.id)"
      >
        {{ toast.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
