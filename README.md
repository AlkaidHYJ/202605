# 企业智能数据洞察与数字员工协同平台

面向业务与运营团队的 **采-洗-析-问-协** 一体化 AI 数据中台（私有化部署）。

## 项目结构

```
0517_2/
├── backend/              # FastAPI 后台服务
├── frontend-user/        # 用户端 (Vue3 + Element Plus) :5173
├── frontend-admin/       # 管理端 (Vue3 + Element Plus) :5174
├── docker-compose.yml    # MySQL / Redis / Elasticsearch
└── 企业智能数据洞察与数字员工协同平台.md
```


## 快速启动

以下步骤按 Windows 本地环境整理，可直接照顺序执行。

### 1. 启动基础设施

先确认 Docker Desktop 已启动，再执行：

```bash
docker compose up -d
```

如果需要 Elasticsearch 且网络可访问官方镜像源，再执行：

```bash
docker compose --profile es up -d
```

#### Docker 拉取失败排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `failed to connect to the docker API` | Docker Desktop 未启动或未完成初始化 | 先启动 Docker Desktop，等待 Docker Engine 正常后再重试 `docker compose up -d` |
| `docker.elastic.co` 连接超时 | 官方 ES 源在国内常不可达 | 默认仅启动 MySQL + Redis，不强制拉起 ES |
| `mirror.baidubce.com` no such host | 百度镜像已失效 | 在 Docker Desktop 的 Docker Engine 中改用可用镜像源 |
| 修改配置后仍报旧镜像地址 | Docker 未重启 | Docker Desktop → **Restart** |

**修复镜像加速**（Docker Desktop → Settings → Docker Engine），示例：

```json
{
  "dns": ["223.5.5.5", "8.8.8.8"],
  "registry-mirrors": ["https://docker.m.daocloud.io"]
}
```

保存后点击 **Apply & Restart**，再执行 `docker compose up -d`。

#### 端口 3306 被占用

本机已安装 MySQL 时会占用 3306。项目已将 Docker MySQL 映射为 **8306**，后端 `.env` 中需设置 `MYSQL_PORT=8306`。
若要用本机 MySQL 而非 Docker，可停止 `docker compose` 中的 mysql 服务，并把 `.env` 改回 `3306` 及对应账号密码。

### 2. 后端

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

说明：如果 `.env` 已存在且数据库配置正确，可以直接执行 `python scripts/init_db.py` 和 `uvicorn ...`。

API 文档：http://127.0.0.1:8000/docs

### 3. 用户端

PowerShell 下如果 `npm run dev` 报脚本执行策略错误，请改用 `npm.cmd`：

```bash
cd frontend-user
npm.cmd install
npm.cmd run dev
```

### 4. 管理端

PowerShell 下同样建议使用 `npm.cmd`：

```bash
cd frontend-admin
npm.cmd install
npm.cmd run dev
```

### 5. 访问地址

```text
用户端：http://localhost:5173
管理端：http://localhost:5174
后端文档：http://127.0.0.1:8000/docs
```

## 试运行记录与报错处理

日期：2026-05-22

1. Docker 未启动时执行 `docker compose up -d` 会报 `failed to connect to the docker API`。处理方式是先启动 Docker Desktop，等 Docker Engine 正常后再启动容器。
2. 后端若直接启动且数据库未起来，会出现 `ConnectionRefusedError`。处理方式是先启动 MySQL 和 Redis，再运行 `python scripts/init_db.py` 和 `uvicorn app.main:app --host 0.0.0.0 --port 8000`。
3. Windows PowerShell 里直接执行 `npm run dev` 可能触发脚本执行策略限制。处理方式是改用 `npm.cmd install` 和 `npm.cmd run dev`。
4. 如果后端需要初始化环境变量，可先复制 `.env.example` 为 `.env`，再按实际数据库地址和端口检查配置。

## 演示账号

| 端     | 用户名  | 密码     |
|--------|---------|----------|
| 用户端 | user01  | user123  |
| 管理端 | admin   | admin123 |

## 已实现能力（V1 骨架）

- **认证鉴权**：JWT 登录、管理员权限校验
- **智能问数**：NL2SQL 占位生成 + SELECT 沙箱校验与执行
- **即时通讯**：群聊、敏感词 DFA 阻断/审计、管理端强制撤回（WebSocket 广播）
- **数字员工**：员工广场、多轮对话（Redis 上下文）
- **数字大屏**：已发布大屏列表与全屏预览
- **管理端**：用户/群/消息/敏感词/爬虫任务管理

## 技术栈

- 后端：FastAPI、SQLAlchemy、MySQL、PyJWT、Redis
- 前端：Vue 3、Vite、Element Plus、ECharts
- 基础设施：MySQL 8、Redis 7、Elasticsearch 8（消息检索扩展）
