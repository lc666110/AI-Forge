# AI Forge

AI Forge 是面向 AI 全栈工程师的二次开发脚手架，内置多会话流式聊天、RAG 知识库、模型工具调用、用户密钥管理与极简管理后台。项目采用 MIT 协议。

## 技术栈

- 前端：Next.js 16.3、React 19.3、TypeScript 6、Tailwind CSS 3.4、Zustand、TanStack Query
- 后端：FastAPI 0.141、SQLAlchemy 2、Alembic、LangChain Text Splitters、OpenAI compatible API
- 基础设施：PostgreSQL 16 + pgvector、Redis 7、Docker Compose

## 快速启动

要求 Docker Engine 24+ 与 Docker Compose v2。

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

Windows PowerShell：

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
docker compose up --build
```

启动后访问：

- Web：http://localhost:3000
- Swagger：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

默认管理员由后端环境变量 `ADMIN_EMAIL` 和 `ADMIN_PASSWORD` 首次启动时创建。请在生产环境立即更换默认值。

## 环境变量

后端：

| 变量 | 说明 |
| --- | --- |
| `SECRET_KEY` | JWT 签名密钥，生产环境必须使用高强度随机值 |
| `ENCRYPTION_KEY` | 用户 API Key 的服务端加密主密钥；更换后旧密钥无法解密 |
| `DATABASE_URL` | SQLAlchemy 异步 PostgreSQL URL |
| `REDIS_URL` | Redis 连接地址，预留给限流与任务队列 |
| `ACCESS_TOKEN_MINUTES` | Access Token 有效分钟数 |
| `REFRESH_TOKEN_DAYS` | Refresh Token 有效天数 |
| `CORS_ORIGINS` | 逗号分隔的允许来源 |
| `TAVILY_API_KEY` | 网页搜索工具密钥，不配置时工具返回说明 |
| `ADMIN_EMAIL/PASSWORD` | 初始化管理员凭据 |

前端 `NEXT_PUBLIC_API_URL` 指向浏览器可访问的后端 `/api/v1` 地址。

## 使用流程

1. 注册或使用管理员账号登录。
2. 在“设置”中保存 OpenAI、DeepSeek 或通义千问密钥。密钥使用 Fernet 加密入库。
3. 在“对话”新建会话并开始流式聊天；模型会按需调用计算器、时间或网页搜索工具。
4. 在“知识库”创建知识库，上传不超过 20MB 的 PDF、DOCX、TXT 或 Markdown；索引完成后发起带引用的问答。

RAG 嵌入目前使用 OpenAI `text-embedding-3-small`（1536 维），因此知识库功能需要配置 OpenAI Key。聊天支持 `gpt-3.5-turbo`、`gpt-4o`、`gpt-5.6`、`deepseek-v4-pro`、`deepseek-flash` 和 `qwen-plus` 的 OpenAI-compatible 接口。

质量检查：

```bash
cd backend && ruff check . && black --check . && pytest
cd frontend && npm run lint && npm run build
docker compose config
```

## API 与安全说明

业务路由统一位于 `/api/v1`，响应为 `{ code, message, data }`；SSE 接口按 `data: JSON` 事件发送 `token`、`tool_start`、`tool_end`、`sources`、`done` 或 `error`。密码以 bcrypt 哈希保存，供应商密钥加密保存。生产部署应启用 HTTPS、使用 Secret Manager 注入密钥，并在网关增加限流与上传扫描。

## 常见问题

- **后端无法连接数据库**：确认 PostgreSQL 与 pgvector 容器已启动，并检查 `DATABASE_URL`。
- **知识库上传失败**：确认已配置 OpenAI Key、文件格式受支持且小于 20MB。
- **网页搜索无结果**：在后端 `.env` 配置 `TAVILY_API_KEY`。
- **修改前端 API 地址未生效**：该变量在镜像构建时注入，需要重新 `docker compose build frontend`。
- **生产迁移**：不要自动生成表；提交新的 Alembic revision 后执行 `alembic upgrade head`。
