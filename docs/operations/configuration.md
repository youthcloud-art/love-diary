# 配置说明

后端从 `apps/backend/.env` 读取配置，可复制 `.env.example` 创建。

- `SECRET_KEY`：JWT 签名密钥，生产环境使用至少 32 字节随机值
- `DATABASE_URL`：开发默认 `sqlite:///./var/love_diary.db`
- `WECHAT_APPID` / `WECHAT_SECRET`：微信小程序登录配置
- `PUBLIC_BASE_URL`：图片对外访问地址
- `CORS_ORIGINS`：允许访问 API 的 H5 域名，多个值用逗号分隔

前端从 `apps/frontend/.env` 读取 `VITE_API_BASE`。微信真机不能使用 `127.0.0.1`，应设置为公网 HTTPS API 地址。
