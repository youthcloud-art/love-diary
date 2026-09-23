# API 约定

- 基础路径：`/api/v1`
- 数据格式：JSON；文件上传使用 `multipart/form-data`
- 认证：`Authorization: Bearer <access_token>`
- 时间：ISO 8601，服务端时间按 UTC 存储
- 日期：`YYYY-MM-DD`

主要资源：`/auth`、`/spaces`、`/entries`、`/media`。

常见状态码：400 输入或文件无效；401 未登录；403 无权操作；404 资源不存在；409 空间或版本冲突；422 数据校验失败。
