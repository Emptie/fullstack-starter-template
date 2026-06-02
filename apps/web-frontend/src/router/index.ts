import { createRouter, createWebHistory } from "vue-router"
import Home from "@/views/Home.vue"
import NotFound from "@/views/NotFound.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: Home },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/Login.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/views/Register.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("@/views/Profile.vue"),
      meta: { requiresAuth: true },
    },
    { path: "/:pathMatch(.*)*", name: "not-found", component: NotFound },
  ],
})

// Navigation guard: redirect unauthenticated users to /login
// and authenticated users away from guest-only pages
router.beforeEach((to) => {
  const token = localStorage.getItem("access_token")
  if (to.meta.requiresAuth && !token) {
    return { name: "login", query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && token) {
    return { name: "profile" }
  }
})

export default router
