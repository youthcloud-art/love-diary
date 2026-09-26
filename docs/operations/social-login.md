# 微信与 QQ 登录配置

项目已实现微信、QQ 两种网页登录方式：登录页生成二维码，服务端接收腾讯 OAuth 回调，桌面页面轮询登录状态；也可从二维码弹窗打开腾讯官方授权页。应用不会收集或保存用户的微信、QQ 密码。

## 上线前准备

扫码设备必须能够访问后端回调，因此正式联调需要一个公网 HTTPS 域名。`127.0.0.1` 只能用于页面开发，手机扫码后无法回调到电脑本机。

建议先将后端发布到 `https://api.example.com`，并设置：

```env
PUBLIC_BASE_URL=https://api.example.com
```

## 微信开放平台

1. 登录 [微信开放平台](https://open.weixin.qq.com/)，在“管理中心 → 网站应用”创建网站应用。
2. 完成开发者资质与网站应用审核，并申请“微信登录”能力。
3. 将授权回调域设置为后端公网域名；实际回调地址为：

   `https://api.example.com/api/v1/auth/oauth/wechat/callback`

4. 把网站应用的 AppID 和 AppSecret 写入 `apps/backend/.env`：

```env
WECHAT_WEB_APPID=你的微信网站应用AppID
WECHAT_WEB_SECRET=你的微信网站应用AppSecret
```

`WECHAT_APPID` / `WECHAT_SECRET` 保留给微信小程序的 `uni.login`，不要与网站应用凭据混用。

## QQ 互联

1. 登录 [QQ 互联](https://connect.qq.com/)，在“应用管理 → 网站应用”创建应用。
2. 完成开发者与网站资质审核并开通 QQ 登录。
3. 将网站回调地址设置为：

   `https://api.example.com/api/v1/auth/oauth/qq/callback`

4. 把 APP ID 和 APP Key 写入 `apps/backend/.env`：

```env
QQ_APPID=你的QQ互联APP_ID
QQ_SECRET=你的QQ互联APP_KEY
```

## 完整环境变量示例

```env
SECRET_KEY=至少32位的随机密钥
DATABASE_URL=sqlite:///./var/love_diary.db
PUBLIC_BASE_URL=https://api.example.com
CORS_ORIGINS=https://example.com
WECHAT_APPID=
WECHAT_SECRET=
WECHAT_WEB_APPID=
WECHAT_WEB_SECRET=
QQ_APPID=
QQ_SECRET=
```

保存后重启后端。登录页中的微信和 QQ 按钮会自动从“待配置”切换为真实二维码。二维码有效期为 5 分钟，回调使用随机 `state` 防止跨站请求伪造；扫码会话保存在数据库中，支持服务重启与多进程部署。

## 本地验收

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/auth/oauth/wechat/start
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/auth/oauth/qq/start
```

没有配置平台凭据时，接口会返回 `configured: false` 和需要登记的回调地址；配置完成后会返回 `session_id`、`authorization_url` 和 `qr_image_url`。
