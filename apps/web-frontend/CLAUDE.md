# Web Frontend

用户面向的 SPA。使用 Vue 3 + shadcn-vue + Tailwind CSS 4。

## 边界
- 不要引入 Element Plus、Ant Design Vue、或其他 UI 框架。只用 shadcn-vue。
- API 调用放在 src/api/ 目录，不要在组件里直接 fetch。
- 状态管理用 Pinia stores，放在 src/stores/。
- 路由定义在 src/router/。
- 所有类型从 @starter/shared 导入，不要在本地重新定义。

## 组件约定
- views/ 放页面级组件（对应路由）
- components/ 放可复用组件
- composables/ 放 Vue composables（use 开头）
