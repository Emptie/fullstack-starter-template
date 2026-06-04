# Fullstack Starter Template

用 AI 构建你自己的 web 应用。不需要会写代码。

## 快速开始

### 第 1 步：安装前置依赖

你需要先装好这些工具。复制粘贴下面的命令到终端即可。

**macOS（推荐用 Homebrew）：**

```bash
# 1. 基础服务
brew install postgresql redis node
brew services start postgresql redis

# 2. 构建工具（如果还没有的话）
xcode-select --install          # 安装 make 等工具
curl -LsSf https://astral.sh/uv/install.sh | sh   # Python 包管理器
npm install -g pnpm             # 前端包管理器
```

> 装完 `uv` 后需要**重启终端**，或者运行 `source ~/.local/bin/env` 使其生效。

**Windows：**
1. [PostgreSQL](https://www.postgresql.org/download/windows/) — 安装时记住你设的密码
2. [Redis](https://github.com/tporadowski/redis/releases) — 下载 zip，解压后运行 `redis-server.exe`
3. [Node.js](https://nodejs.org/) — 下载 LTS 版本
4. [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python 包管理器
5. 打开命令提示符运行 `npm install -g pnpm`

**Linux（Ubuntu/Debian）：**
```bash
sudo apt install postgresql redis-server nodejs make
curl -LsSf https://astral.sh/uv/install.sh | sh
npm install -g pnpm
```

### 第 2 步：创建你自己的项目

1. 点击本页面右上角的 **"Use this template"** → **"Create a new repository"**
2. 给你的项目起个名字，点 Create repository
3. 把项目 clone 到本地：
   ```bash
   git clone https://github.com/你的用户名/你的项目名.git
   cd 你的项目名
   ```

### 第 3 步：安装项目依赖

```bash
make setup
```

这会自动安装所有需要的东西。大约需要 1-2 分钟。

### 第 4 步：启动项目

```bash
make dev
```

第一次运行时会提示你：
1. **数据库配置** — 直接按回车用默认值即可
2. **创建管理员账号** — 输入你的名字、邮箱和密码

启动成功后打开浏览器：
- 🌐 **用户端**：http://localhost:5173
- 🔧 **管理后台**：http://localhost:5174

## 开始构建你的应用

1. 安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)（如果你还没装）
2. 在项目目录打开终端，输入 `claude`
3. 告诉 Claude 你想做什么，比如：
   - "我想加一个博客功能，有文章列表和文章详情页"
   - "我想让用户可以上传头像"
   - "我想加一个待办事项功能"
4. Claude 会读取项目结构，理解约定，帮你实现

## 管理后台

项目自带一个管理后台（http://localhost:5174）。

第一次运行 `make dev` 时会提示你创建管理员账号。之后如果需要再加一个管理员：

```bash
make seed-admin
```

## 常用命令

| 命令 | 作用 |
|------|------|
| `make setup` | 安装所有依赖 |
| `make dev` | 启动用户端（前端 + 后端） |
| `make dev-all` | 启动全部 4 个应用（含管理后台） |
| `make stop` | 停止所有 dev server |
| `make seed-admin` | 创建管理员账号 |
| `make test` | 运行所有测试 |

## 你可以构建什么

任何 web 应用。这个 template 提供了：
- 用户注册和登录
- 密码重置
- 管理后台（用户管理、数据统计）
- 数据库（PostgreSQL）
- 缓存（Redis）

你只需要告诉 Claude 你想要什么功能。

## 遇到问题？

- `make: command not found` → 先装构建工具（macOS: `xcode-select --install`）
- `uv: command not found` → 安装 uv 后重启终端，或运行 `source ~/.local/bin/env`
- `pnpm: command not found` → 运行 `npm install -g pnpm`
- `make setup` 失败 → 确保装了 PostgreSQL、Redis 和 Node.js
- `make dev` 失败 → 确保 PostgreSQL 和 Redis 在运行（macOS: `brew services start postgresql redis`）
- 忘了管理员密码 → 运行 `make seed-admin` 创建新的管理员
- 任何错误 → 在终端里运行 `claude`，把错误信息给 Claude，它会帮你修
- 功能不符合预期 → 继续和 Claude 对话，描述你想要什么变化

## 项目结构

```
apps/web-frontend/     → 用户面向的网站
apps/web-backend/      → 用户面向的 API
apps/admin-frontend/   → 管理后台网站
apps/admin-backend/    → 管理后台 API
packages/shared-py/    → Python 共享类型
packages/shared-ts/    → TypeScript 共享类型（自动生成）
```

不需要手动改 `packages/shared-ts/` 里的文件 — 它们是自动生成的。
