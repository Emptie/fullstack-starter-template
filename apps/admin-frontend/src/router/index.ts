import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "admin-login",
      component: () => import("@/views/Login.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/",
      component: () => import("@/layouts/AdminLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "admin-dashboard",
          component: () => import("@/views/Dashboard.vue"),
        },
        {
          path: "users",
          name: "admin-users",
          component: () => import("@/views/UserList.vue"),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem("admin_access_token")
  if (to.meta.requiresAuth && !token) {
    return { name: "admin-login", query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && token) {
    return { name: "admin-dashboard" }
  }
})

export default router
