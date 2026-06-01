import { createRouter, createWebHistory } from "vue-router"
import Home from "@/views/Home.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: Home },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/Login.vue"),
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/views/Register.vue"),
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("@/views/Profile.vue"),
      meta: { requiresAuth: true },
    },
  ],
})

// Navigation guard: redirect unauthenticated users to /login
router.beforeEach((to) => {
  const token = localStorage.getItem("access_token")
  if (to.meta.requiresAuth && !token) {
    return { name: "login", query: { redirect: to.fullPath } }
  }
})

export default router
