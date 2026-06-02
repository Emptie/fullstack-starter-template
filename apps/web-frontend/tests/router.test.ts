import { describe, it, expect, beforeEach } from "vitest"
import { createRouter, createWebHistory, type Router } from "vue-router"

const StubView = { template: "<div>stub</div>" }

function createTestRouter(): Router {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: "/", name: "home", component: StubView },
      {
        path: "/login",
        name: "login",
        component: StubView,
        meta: { guestOnly: true },
      },
      {
        path: "/register",
        name: "register",
        component: StubView,
        meta: { guestOnly: true },
      },
      {
        path: "/profile",
        name: "profile",
        component: StubView,
        meta: { requiresAuth: true },
      },
      { path: "/:pathMatch(.*)*", name: "not-found", component: StubView },
    ],
  })
}

// Replicate the same guard logic from router/index.ts
function applyGuards(router: Router) {
  router.beforeEach((to) => {
    const token = localStorage.getItem("access_token")
    if (to.meta.requiresAuth && !token) {
      return { name: "login", query: { redirect: to.fullPath } }
    }
    if (to.meta.guestOnly && token) {
      return { name: "profile" }
    }
  })
}

describe("Router", () => {
  let router: Router

  beforeEach(() => {
    localStorage.clear()
    router = createTestRouter()
    applyGuards(router)
  })

  describe("catchAll route", () => {
    it("resolves unknown paths to the not-found route", () => {
      const resolved = router.resolve("/some/unknown/path")
      expect(resolved.name).toBe("not-found")
    })

    it("renders not-found for unmatched routes", async () => {
      await router.push("/does-not-exist")
      await router.isReady()
      expect(router.currentRoute.value.name).toBe("not-found")
    })
  })

  describe("auth guard — unauthenticated", () => {
    it("redirects /profile to /login when no token", async () => {
      await router.push("/profile")
      expect(router.currentRoute.value.name).toBe("login")
      expect(router.currentRoute.value.query.redirect).toBe("/profile")
    })

    it("allows access to /login when no token", async () => {
      await router.push("/login")
      expect(router.currentRoute.value.name).toBe("login")
    })

    it("allows access to /register when no token", async () => {
      await router.push("/register")
      expect(router.currentRoute.value.name).toBe("register")
    })
  })

  describe("auth guard — authenticated", () => {
    beforeEach(() => {
      localStorage.setItem("access_token", "valid-token")
    })

    it("redirects /login to /profile when authenticated", async () => {
      await router.push("/login")
      expect(router.currentRoute.value.name).toBe("profile")
    })

    it("redirects /register to /profile when authenticated", async () => {
      await router.push("/register")
      expect(router.currentRoute.value.name).toBe("profile")
    })

    it("allows access to /profile when authenticated", async () => {
      await router.push("/profile")
      expect(router.currentRoute.value.name).toBe("profile")
    })

    it("allows access to / when authenticated", async () => {
      await router.push("/")
      expect(router.currentRoute.value.name).toBe("home")
    })
  })
})
