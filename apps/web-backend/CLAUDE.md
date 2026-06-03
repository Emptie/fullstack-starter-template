# Web Backend

用户面向的 FastAPI API。使用 SQLAlchemy 2.0 async + Pydantic 2。

## 边界
- 路由定义在 app/routes/，每个领域一个文件。
- 数据库模型在 app/models/。
- 业务逻辑在 app/services/ 或直接在路由里（简单场景）。
- 只有这个应用管理 Alembic 迁移。admin-backend 不做迁移。
- 导入共享类型：from starter_shared.types import Xxx
- 导入共享数据库：from starter_shared.database import get_db

## 添加新 API 端点
1. 确保 shared-py 里有对应的 Pydantic schema
2. 在 app/models/ 定义 SQLAlchemy 模型
3. 运行 Alembic 迁移
4. 在 app/routes/ 创建或更新路由文件
