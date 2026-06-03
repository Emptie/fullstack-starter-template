# Admin Frontend

管理后台 SPA。使用 Vue 3 + shadcn-vue + Tailwind CSS 4。

## 边界
- 不要引入 Element Plus、Ant Design Vue、或其他 UI 框架。只用 shadcn-vue。
- API 调用放在 src/api/ 目录，不要在组件里直接 fetch。
- 状态管理用 Pinia stores，放在 src/stores/。
- 路由定义在 src/router/。
- 所有类型从 @starter/shared 导入，不要在本地重新定义。

## Auth（注意区别）
- Auth token 存在 localStorage，key 是 `admin_access_token` 和 `admin_refresh_token`。
- 请求时在 Authorization header 传 Bearer token。
- 不要使用 web-frontend 的 token（key 不同）。
