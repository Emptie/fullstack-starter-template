import { ref } from "vue"

export interface Toast {
  id: number
  message: string
  type: "success" | "error"
}

const toasts = ref<Toast[]>([])
let nextId = 0

export function useToast() {
  function addToast(message: string, type: "success" | "error" = "success") {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => removeToast(id), 3000)
  }

  function removeToast(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return { toasts, addToast, removeToast }
}
