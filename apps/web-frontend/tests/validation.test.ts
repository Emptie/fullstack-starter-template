import { describe, it, expect } from "vitest"
import { useFormValidation, required, email, minLength, maxLength } from "@/composables/useFormValidation"

describe("useFormValidation", () => {
  it("validates required fields", () => {
    const { errors, validateAll } = useFormValidation({
      email: [required("Email")],
    })
    expect(validateAll({ email: "" })).toBe(false)
    expect(errors.email).toBe("Email is required")
  })

  it("passes valid data", () => {
    const { errors, validateAll } = useFormValidation({
      email: [required("Email"), email()],
    })
    expect(validateAll({ email: "user@example.com" })).toBe(true)
    expect(errors.email).toBeNull()
  })

  it("validates email format", () => {
    const { errors, validate } = useFormValidation({
      email: [email()],
    })
    expect(validate("email", "not-an-email")).toBe(false)
    expect(errors.email).toBe("Invalid email address")
    expect(validate("email", "good@example.com")).toBe(true)
  })

  it("validates min length", () => {
    const { errors, validate } = useFormValidation({
      password: [minLength(8)],
    })
    expect(validate("password", "short")).toBe(false)
    expect(errors.password).toBe("Must be at least 8 characters")
    expect(validate("password", "longenough")).toBe(true)
  })

  it("validates max length", () => {
    const { errors, validate } = useFormValidation({
      name: [maxLength(5)],
    })
    expect(validate("name", "toolong")).toBe(false)
    expect(errors.name).toBe("Must be at most 5 characters")
    expect(validate("name", "ok")).toBe(true)
  })
})
