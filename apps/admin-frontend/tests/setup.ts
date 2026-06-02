/**
 * Vitest global setup — ensure localStorage is available in happy-dom.
 * happy-dom v20+ in Node 24 may not expose localStorage by default
 * unless --localstorage-file is passed; this polyfill guarantees it.
 */
import { beforeEach } from "vitest"

const store = new Map<string, string>()

const localStorageMock: Storage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => store.set(key, String(value)),
  removeItem: (key: string) => store.delete(key),
  clear: () => store.clear(),
  get length() {
    return store.size
  },
  key: (_index: number) => null,
}

beforeEach(() => {
  store.clear()
})

// Replace if happy-dom didn't provide one
if (typeof globalThis.localStorage === "undefined" || globalThis.localStorage === undefined) {
  Object.defineProperty(globalThis, "localStorage", { value: localStorageMock, writable: true })
}
