# 示例：构建你的第一个功能 — 留言板

> 这个示例展示你如何用自然语言告诉 Claude 你想要什么，Claude 帮你实现。
> 你只需要读懂这个文档，确认结果符合你的预期。

## 你想要什么

一个留言板功能：
- 用户可以在首页看到所有留言
- 登录后可以发留言
- 管理员可以删除留言

## 你只需要做这些

### 第 1 步：打开 Claude Code

在项目目录的终端里输入：

```
claude
```

### 第 2 步：告诉 Claude 你想要什么

把下面这段话发给 Claude：

---

我想加一个留言板功能，具体要求：

1. 任何访问者都能看到留言列表（不需要登录）
2. 登录的用户可以发布留言（内容是文字，最多 500 字）
3. 留言按时间倒序排列，显示作者名字和发布时间
4. 管理员可以在管理后台删除留言
5. 首页改成留言板页面

技术要求（Claude 应该已经知道这些）：
- 类型定义从 shared-py 开始
- 用 make generate 生成 TypeScript 类型
- 数据库迁移在 web-backend 做

---

### 第 3 步：等 Claude 完成

Claude 会自动完成以下所有步骤（你不需要手动做任何事）：

```
1. 定义 Pydantic 类型          ← packages/shared-py/src/starter_shared/types/guestbook.py
2. 生成 TypeScript 类型        ← make generate
3. 创建 SQLAlchemy 模型        ← apps/web-backend/app/models/guestbook.py
4. 生成数据库迁移              ← alembic revision --autogenerate
5. 创建 API 路由               ← apps/web-backend/app/routes/guestbook.py
6. 创建管理后台 API            ← apps/admin-backend/app/routes/guestbook.py
7. 创建前端 API 客户端         ← apps/web-frontend/src/api/guestbook.ts
8. 创建留言板页面              ← apps/web-frontend/src/views/Guestbook.vue
9. 创建管理后台留言管理页面     ← apps/admin-frontend/src/views/GuestbookList.vue
10. 更新路由配置               ← router/index.ts
```

### 第 4 步：验证

Claude 完成后，你会看到类似这样的输出：

```
✅ 留言板功能已实现。运行 make dev-all 启动所有服务。

- 用户端：http://localhost:5173 — 首页现在是留言板
- 管理后台：http://localhost:5174 — 左侧菜单多了一个"留言管理"
- API：http://localhost:8000/docs — 可以看到新的 /api/v1/guestbook 端点
```

打开浏览器确认：
- http://localhost:5173 → 能看到留言板，登录后能发留言
- http://localhost:5174 → 管理后台能删除留言

### 如果不符合预期

继续和 Claude 对话，比如：

- "留言列表每页显示太多，改成每页 10 条"
- "留言框太小了，改大一点"
- "我想给留言加上表情功能"

Claude 会根据你的反馈调整代码。

---

## 背后发生了什么（好奇可以看看）

当你告诉 Claude 你想要什么功能时，Claude 遵循项目约定自动完成：

```
Pydantic 类型 (shared-py)
       ↓ make generate
TypeScript 类型 (shared-ts)
       ↓
SQLAlchemy 模型 (web-backend)
       ↓ alembic
数据库表
       ↓
API 路由 (web-backend)
       ↓
前端 API 客户端 (web-frontend)
       ↓
Vue 页面 (web-frontend)
```

这就是项目的"类型驱动"流程：类型是唯一的真相来源，从 Python 类型开始，一路到前端页面。

你不需要记住这些。Claude 知道怎么做。你只需要描述你想要什么。
