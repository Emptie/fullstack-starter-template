# Admin Backend

管理后台 FastAPI API。使用 SQLAlchemy 2.0 async + Pydantic 2。

## 边界
- 所有路由必须使用 `get_current_admin_user` 依赖。不要加没有 admin 认证的路由。
- 不要创建 Alembic 迁移。数据库迁移由 web-backend 独占管理。
- 路由定义在 app/routes/，每个领域一个文件。
- 数据库模型在 app/models/。映射与 web-backend 相同的表（same table name, same columns）。
- 导入共享类型：from starter_shared.types import Xxx
- 导入共享数据库：from starter_shared.database import get_db
