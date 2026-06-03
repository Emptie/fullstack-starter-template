# Fullstack Starter Template

用 AI 构建你自己的 web 应用。不需要会写代码。

## 快速开始

1. 点击右上角 "Use this template" → 创建你自己的仓库
2. Clone 到本地
3. 确保安装了 PostgreSQL 和 Node.js
   - macOS: `brew install postgresql node` 然后 `brew services start postgresql`
   - Windows: 安装 [PostgreSQL](https://www.postgresql.org/download/windows/) 和 [Node.js](https://nodejs.org/)
   - Linux: `sudo apt install postgresql nodejs`
4. 打开终端，cd 到项目目录
5. 运行 `make setup`
6. 运行 `make dev`
7. 打开浏览器访问 http://localhost:5173 — 你应该看到登录页面

## 开始构建你的应用

1. 安装 Claude Code（如果你还没装）
2. 在项目目录打开终端，输入 `claude`
3. 告诉 Claude 你想做什么，比如：
   - "我想加一个博客功能，有文章列表和文章详情页"
   - "我想让用户可以上传头像"
   - "我想加一个待办事项功能"
4. Claude 会读取项目结构，理解约定，帮你实现

## 你可以构建什么

任何 web 应用。这个 template 提供了：
- 用户注册和登录
- 管理后台
- 数据库
- API

你只需要告诉 Claude 你想要什么功能。

## 遇到问题？

- `make setup` 失败 → 确保装了 PostgreSQL 和 Node.js
- `make dev` 失败 → 确保 PostgreSQL 在运行（macOS: `brew services start postgresql`）
- 任何错误 → 在终端里运行 `claude`，把错误信息给 Claude，它会帮你修
- 功能不符合预期 → 继续和 Claude 对话，描述你想要什么变化
