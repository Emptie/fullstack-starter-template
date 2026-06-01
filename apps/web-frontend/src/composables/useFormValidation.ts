/**Lightweight form validation composable.

 * No external deps — just reactive errors + simple rules.
 * Designed for starter template simplicity over feature completeness.
 */

import { reactive } from "vue"

type Rules = Record<string, Array<(value: string) => string | null>>

export function useFormValidation(rules: Rules) {
  const errors = reactive<Record<string, string | null>>(
    Object.fromEntries(Object.keys(rules).map((key) => [key, null])),
  )

  function validate(field: string, value: string): boolean {
    const fieldRules = rules[field] ?? []
    for (const rule of fieldRules) {
      const msg = rule(value)
      if (msg) {
        errors[field] = msg
        return false
      }
    }
    errors[field] = null
    return true
  }

  function validateAll(values: Record<string, string>): boolean {
    let valid = true
    for (const field of Object.keys(rules)) {
      if (!validate(field, values[field] ?? "")) {
        valid = false
      }
    }
    return valid
  }

  return { errors, validate, validateAll }
}

// ── Common validators ──────────────────────────────────────

export const required = (label: string) => (v: string) =>
  v.trim() ? null : `${label} is required`

export const email = () => (v: string) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : "Invalid email address"

export const minLength = (min: number) => (v: string) =>
  v.length >= min ? null : `Must be at least ${min} characters`

export const maxLength = (max: number) => (v: string) =>
  v.length <= max ? null : `Must be at most ${max} characters`
