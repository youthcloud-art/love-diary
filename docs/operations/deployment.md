# 部署说明

## 本地开发

使用根目录 `scripts/` 中的启动脚本。SQLite 数据保存在 `apps/backend/var/`，上传图片保存在 `apps/backend/uploads/`。

## PostgreSQL

```powershell
docker compose -f infra/docker/docker-compose.yml up -d
```

将后端 `DATABASE_URL` 设置为 `postgresql+psycopg://love:love@127.0.0.1:5432/love_diary`。生产环境必须更换示例密码。

## H5 与微信小程序

运行 `scripts/build.ps1` 后，H5 产物位于 `apps/frontend/dist/build/h5/`；微信产物位于 `apps/frontend/dist/build/mp-weixin/`。

正式上线需要 HTTPS、备案域名、微信后台合法域名配置，以及生产 AppID/AppSecret。建议使用 PostgreSQL、对象存储、反向代理、数据库备份和错误监控。
