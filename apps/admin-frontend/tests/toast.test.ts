import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { useToast } from "@/composables/useToast"

describe("useToast", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Clear shared module state by removing all toasts
    const { toasts, removeToast } = useToast()
    const ids = toasts.value.map((t) => t.id)
    ids.forEach((id) => removeToast(id))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("addToast adds a toast to the reactive array", () => {
    const { toasts, addToast } = useToast()
    addToast("Hello!", "success")

    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe("Hello!")
    expect(toasts.value[0].type).toBe("success")
  })

  it("addToast defaults to success type", () => {
    const { toasts, addToast } = useToast()
    addToast("Default type")

    expect(toasts.value[0].type).toBe("success")
  })

  it("addToast creates error toast", () => {
    const { toasts, addToast } = useToast()
    addToast("Something failed", "error")

    expect(toasts.value[0].type).toBe("error")
    expect(toasts.value[0].message).toBe("Something failed")
  })

  it("removeToast removes a toast by id", () => {
    const { toasts, addToast, removeToast } = useToast()
    addToast("First")
    addToast("Second")

    const firstId = toasts.value[0].id
    removeToast(firstId)

    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe("Second")
  })

  it("auto-removes toast after timeout", () => {
    const { toasts, addToast } = useToast()
    addToast("Temporary")

    expect(toasts.value).toHaveLength(1)

    vi.advanceTimersByTime(3000)

    expect(toasts.value).toHaveLength(0)
  })

  it("does not auto-remove toast before timeout", () => {
    const { toasts, addToast } = useToast()
    addToast("Temporary")

    vi.advanceTimersByTime(2999)

    expect(toasts.value).toHaveLength(1)
  })
})
