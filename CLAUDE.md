# CLAUDE.md

## 你是谁（AI 上下文）

这是一个全栈 monorepo starter template。使用它的人可能不会写代码。
他们告诉你想要什么功能，你负责在项目结构内正确实现。
你的目标：让使用者的想法变成可运行的代码。

## 项目边界（不要违反）

- 四个独立应用，四个独立进程。不要合并它们。
- 数据库迁移只在 web-backend 做。admin-backend 只读不迁移。
- Pydantic 类型是 single source of truth。TypeScript 类型是生成的。
  修改类型 → 改 shared-py → make generate。不要手改 shared-ts。
- 端口固定：web-frontend 5173, admin-frontend 5174, web-backend 8000, admin-backend 8001, PostgreSQL 5432。
- 不要引入新的数据库。PostgreSQL 是唯一的关系型数据库，Redis 是 token 缓存。本地运行不 Docker 化。
- 不要引入新的包管理器。前端用 pnpm，后端用 uv。
- PostgreSQL 必须在本地运行（不是 Docker）。Redis 也必须在本地运行。`make dev` 直接启动后端和前端，假设 PostgreSQL 和 Redis 已在本机运行。

## 项目结构（在哪里放东西）

apps/web-frontend/     → 用户面向的 Vue 3 前端
apps/web-backend/      → 用户面向的 FastAPI 后端
apps/admin-frontend/   → 管理后台 Vue 3 前端
apps/admin-backend/    → 管理后台 FastAPI 后端
packages/shared-py/    → Python 共享包（类型从这里出发）
packages/shared-ts/    → TypeScript 共享包（类型自动生成到这里）

## 添加新功能的流程

1. 在 packages/shared-py/src/starter_shared/types/ 定义 Pydantic 模型
2. make generate 生成 TypeScript 类型
3. 在 apps/web-backend/app/models/ 加 SQLAlchemy 模型
4. 在 apps/web-backend 运行 Alembic 生成迁移
5. 在 apps/web-backend/app/routes/ 加 API 路由
6. 在 apps/web-frontend/src/api/ 手写 API 客户端
7. 在 apps/web-frontend/src/views/ 加 Vue 页面
8. 如果管理后台也需要，在 admin-backend 和 admin-frontend 做同样的事

## 常见错误（不要犯）

- 不要在 admin-backend 里创建 Alembic 迁移
- 不要手改 packages/shared-ts/src/types/ 里的生成文件
- 不要跨应用直接导入代码（web-frontend 不能 import admin-frontend 的组件）
- 不要用 localStorage 存敏感信息（用 httpOnly cookie 或只存 token）
- shared-py 类型文件允许单向引用（如 admin.py → user.py），禁止循环导入
- 不要在 app 层级定义 Pydantic schema。用 shared-py 里的类型。

## 技术栈（不要偏离）

- Frontend: Vue 3.5 + Vite + shadcn-vue + Tailwind CSS 4
- Backend: FastAPI + SQLAlchemy 2.0 (async) + Pydantic 2
- Database: PostgreSQL（不锁定版本，本地运行）
- Cache/Token Store: Redis（refresh token + password reset token）
- Auth: JWT + Refresh Token + UserRole enum
- Monorepo: pnpm workspaces + uv workspaces

## 开发命令

make setup        → 安装所有依赖
make dev          → 启动 web-backend + web-frontend（PostgreSQL 和 Redis 需在本机运行）
make dev-all      → 启动所有四个应用
make up           → 启动所有 4 个应用（跳过 DB 初始化，假设 DB 已就绪）
make stop         → 停止所有 dev server
make generate     → 运行类型桥
make test         → 跑所有测试
make lint         → Lint 所有代码
make typecheck    → 类型检查所有代码
make scaffold     → 创建新功能的骨架文件
