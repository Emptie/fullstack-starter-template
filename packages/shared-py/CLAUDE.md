# Shared Python

所有后端共享的类型、数据库、安全、配置。

## 最重要的事
- types/ 里的 Pydantic 模型是 single source of truth。
- 修改类型后必须运行 make generate 更新 TypeScript。
- types/ 里的文件保持扁平，不要互相导入。
- 新增类型后在 __init__.py 导出，并加入 scripts/generate_types.py 的 EXPORT_MODELS。
