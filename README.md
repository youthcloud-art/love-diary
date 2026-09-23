# 恋爱日记

一个面向情侣的双人远程同步日记产品。Python FastAPI 提供统一 API，uni-app（Vue 3）用一套代码发布浏览器 H5 和微信小程序。

## 项目导航

- `apps/backend/`：后端业务代码、依赖、上传目录和本地运行数据
- `apps/frontend/`：H5 / 微信小程序共用的前端代码
- `tests/backend/`：后端自动化测试
- `docs/product/`：产品需求、用户流程和迭代路线
- `docs/design/`：页面结构与视觉规范
- `docs/architecture/`：系统架构、数据模型和接口约定
- `docs/quality/`：测试策略与验收清单
- `docs/operations/`：配置、部署和运行维护
- `infra/docker/`：PostgreSQL 等基础设施配置
- `scripts/`：开发、测试和构建入口脚本

完整目录说明见 [docs/README.md](docs/README.md)。

## 快速启动

首次运行：

```powershell
cd apps/backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
cd ..\frontend
npm install
```

回到项目根目录，分别打开两个终端：

```powershell
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

- H5：<http://127.0.0.1:5173>
- API 文档：<http://127.0.0.1:8000/docs>

运行全部检查：

```powershell
.\scripts\test.ps1
.\scripts\build.ps1
```

部署和微信配置参见 [部署说明](docs/operations/deployment.md)。
