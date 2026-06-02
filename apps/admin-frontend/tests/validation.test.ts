import { describe, it, expect } from "vitest"
import { useFormValidation, required, email, minLength, maxLength } from "@/composables/useFormValidation"

describe("useFormValidation", () => {
  it("validate passes with valid input", () => {
    const { errors, validate } = useFormValidation({
      name: [required("Name")],
    })
    expect(validate("name", "Alice")).toBe(true)
    expect(errors.name).toBeNull()
  })

  it("validate fails with first failing rule", () => {
    const { errors, validate } = useFormValidation({
      email: [required("Email"), email()],
    })
    expect(validate("email", "")).toBe(false)
    expect(errors.email).toBe("Email is required")
  })

  it("validateAll passes when all fields valid", () => {
    const { errors, validateAll } = useFormValidation({
      email: [required("Email"), email()],
      password: [minLength(8)],
    })
    expect(validateAll({ email: "user@example.com", password: "longpassword" })).toBe(true)
    expect(errors.email).toBeNull()
    expect(errors.password).toBeNull()
  })

  it("validateAll fails when one field is invalid", () => {
    const { errors, validateAll } = useFormValidation({
      email: [required("Email"), email()],
      password: [minLength(8)],
    })
    expect(validateAll({ email: "user@example.com", password: "short" })).toBe(false)
    expect(errors.password).toBe("Must be at least 8 characters")
  })

  it("required validator rejects empty string", () => {
    const rule = required("Field")
    expect(rule("")).toBe("Field is required")
    expect(rule("   ")).toBe("Field is required")
  })

  it("required validator accepts non-empty string", () => {
    const rule = required("Field")
    expect(rule("hello")).toBeNull()
  })

  it("email validator rejects invalid emails", () => {
    const rule = email()
    expect(rule("not-an-email")).toBe("Invalid email address")
    expect(rule("missing@tld")).toBe("Invalid email address")
    expect(rule("@missing.com")).toBe("Invalid email address")
  })

  it("email validator accepts valid emails", () => {
    const rule = email()
    expect(rule("user@example.com")).toBeNull()
    expect(rule("a@b.co")).toBeNull()
  })

  it("minLength validator rejects short strings", () => {
    const rule = minLength(8)
    expect(rule("short")).toBe("Must be at least 8 characters")
    expect(rule("")).toBe("Must be at least 8 characters")
  })

  it("minLength validator accepts strings of sufficient length", () => {
    const rule = minLength(5)
    expect(rule("hello")).toBeNull()
    expect(rule("longer")).toBeNull()
  })

  it("maxLength validator rejects long strings", () => {
    const rule = maxLength(5)
    expect(rule("toolong")).toBe("Must be at most 5 characters")
  })

  it("maxLength validator accepts strings within limit", () => {
    const rule = maxLength(5)
    expect(rule("ok")).toBeNull()
    expect(rule("hello")).toBeNull()
  })
})
