# PR 3: 实现 FastAPI 后端骨架

## 新增/修改内容

- 新增 `backend/requirements.txt`，声明 FastAPI、Uvicorn、Pydantic、pytest、httpx 依赖。
- 新增 FastAPI 应用入口：
  - `backend/app/main.py`
  - `backend/app/__init__.py`
- 新增健康检查路由：
  - `backend/app/routes/health_routes.py`
  - `GET /api/health`
- 新增后端分层目录占位：
  - `routes/`
  - `services/`
  - `providers/`
  - `repositories/`
  - `prompt/`
  - `models/`
  - `utils/`
- 新增测试配置与 health 接口测试：
  - `backend/pytest.ini`
  - `backend/tests/test_health.py`
- 删除 `backend/.gitkeep`，因为后端目录已有真实工程文件。

## 功能描述

本 PR 完成 GameAsset Forge 的后端基础骨架，提供可启动的 FastAPI 应用和 `/api/health` 健康检查接口。

本 PR 只建立后端工程结构和最小 API 可用性，不实现 Prompt Compiler、Mock Provider、素材生成、质检、导出或上传逻辑。这些功能会在后续 PR 中逐步接入。

## 实现思路

- 使用 FastAPI 作为后端框架，适合快速构建接口、自动生成 API 文档，并方便后续接入 AI、图片处理和文件导出流程。
- 使用 `create_app()` 创建应用实例，便于后续测试和扩展中复用。
- 配置 CORS，允许当前前端开发地址 `http://127.0.0.1:4173` 和 `http://localhost:4173` 访问。
- 先建立完整后端分层目录，保证后续 PR 能按模块落地：
  - `routes` 负责 HTTP 路由；
  - `services` 负责编排业务流程；
  - `providers` 负责生图 Provider 抽象；
  - `repositories` 负责数据持久化；
  - `prompt` 负责 Prompt Compiler；
  - `models` 负责请求/响应数据结构；
  - `utils` 负责文件和图片工具。
- 使用 pytest + FastAPI TestClient 验证 health 接口，不依赖真实服务器进程即可自动测试。

## 测试方式

1. 安装后端依赖：

   ```bash
   python -m pip install -r backend/requirements.txt
   ```

2. 运行自动测试：

   ```bash
   cd backend
   python -m pytest
   ```

   本 PR 已验证结果：

   ```text
   1 passed
   ```

3. 启动后端服务：

   ```bash
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

   验证 Uvicorn 输出：

   ```text
   Uvicorn running on http://127.0.0.1:8000
   ```

4. 访问健康检查接口：

   ```text
   http://127.0.0.1:8000/api/health
   ```

   期望返回：

   ```json
   {
     "status": "ok",
     "service": "gameasset-forge-api",
     "version": "0.1.0"
   }
   ```

## 依赖与来源说明

- 本 PR 引入后端依赖：
  - `fastapi`：Web API 框架；
  - `uvicorn`：ASGI 开发服务器；
  - `pydantic`：后续请求/响应模型基础；
  - `pytest`：自动测试；
  - `httpx`：FastAPI TestClient 依赖。
- 未复用外部历史代码。
