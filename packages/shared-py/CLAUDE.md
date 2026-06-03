# Shared Python

所有后端共享的类型、数据库、安全、配置、token 存储。

## 最重要的事
- types/ 里的 Pydantic 模型是 single source of truth。
- 修改类型后必须运行 make generate 更新 TypeScript。
- types/ 里的文件保持扁平，不要互相导入。
- 新增类型后在 __init__.py 导出，并加入 scripts/generate_types.py 的 EXPORT_MODELS。

## 模块
- config/ — 应用配置（DatabaseSettings, SecuritySettings, RedisSettings, SmtpSettings）
- database/ — Async SQLAlchemy 引擎和 session 工厂
- security/ — JWT 签发/验证、密码哈希
- token_store/ — Redis token 存储（refresh token + password reset token）
- types/ — Pydantic 模型

## token_store 使用方式
- 在 app lifespan 中调用 init_redis() / close_redis()
- 在路由中通过 Depends(get_token_store) 注入 TokenStore
- 不要直接操作 Redis，通过 TokenStore 方法
