# GameAsset Forge

GameAsset Forge 是一个面向独立游戏开发者的 AI 2D 游戏素材生产与交付平台。项目目标不是做一个简单的 AI 生图页面，而是搭建一条从自然语言需求到可用游戏素材包的生产流水线。

用户输入游戏设定后，系统会将需求转换为结构化生图提示词，通过 Provider 层生成素材文件，再进行素材质量检查、素材库管理、`manifest.json` 生成、zip 素材包导出，并支持七牛云或本地模拟上传交付。

## 项目定位

本项目选择方向：**2D 游戏素材生成**。

核心目标：

- 生成一组结构化游戏素材，而不是单张图片；
- 提供素材管理、质检、上传、分发、导出闭环；
- 通过 Prompt Compiler、Asset Quality Inspector、Cloud Asset Hub 体现工程能力；
- 默认支持 Mock 模式，保证没有 API Key 也能演示完整流程。

## 技术栈规划

- 前端：React + Vite
- 后端：Python + FastAPI
- 存储：本地 JSON 文件 + `storage/` 目录
- 图片处理：Pillow
- 导出：`manifest.json` + zip 素材包
- 生图：默认 Mock Provider，后续可扩展 OpenAI / FLUX / Stable Diffusion 等 Provider
- 云端交付：七牛云；未配置密钥时使用本地模拟上传状态

## 核心流程

```text
用户输入需求
↓
Prompt Compiler 生成结构化提示词
↓
Image Provider 生成素材
↓
Asset Quality Inspector 质量检查
↓
素材分类入库
↓
七牛云或模拟上传
↓
导出 zip 素材包与 manifest.json
```

也可以概括为：

```text
Input -> Prompt Compiler -> Image Provider -> Quality Inspector -> Cloud Asset Hub -> Export
```

## 当前阶段

当前仓库处于 **PR 1：项目初始化与基础文档** 阶段。

本阶段已经完成：

- 创建基础项目目录；
- 添加环境变量示例；
- 添加 `.gitignore`；
- 添加 PR 拆分计划；
- 添加 Demo 视频脚本；
- 保留工程设计文档；
- 明确后续 12 个 PR 的实现路线。

运行时代码会在后续 PR 中逐步实现，具体见 [docs/PR_PLAN.md](docs/PR_PLAN.md)。

## 本地启动规划

后端启动方式：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端启动方式：

```bash
cd frontend
npm install
npm run dev
```

> 说明：当前 PR 1 只提交项目骨架和文档，以上命令会在后续前后端代码落地后可用。

## Mock 模式

Mock 模式默认开启：

```env
IMAGE_PROVIDER=mock
```

Mock Provider 不调用真实生图 API，而是使用本地预置或自动生成的演示素材，保证评审环境中没有 API Key 时也可以跑通完整流程：

```text
Prompt 编译 -> Mock 生成素材 -> 质量检查 -> 素材库展示 -> 上传状态 -> manifest -> zip 导出
```

## API 规划

后端计划提供以下接口：

- `GET /api/health`
- `POST /api/assets/generate`
- `GET /api/assets`
- `GET /api/assets/{asset_id}/quality`
- `POST /api/assets/{asset_id}/upload`
- `POST /api/exports/{generation_id}`

## 原创工程亮点

1. **Prompt Compiler**

   将用户自然语言需求拆分为游戏类型、主题、风格、素材类型、技术约束和负面约束，再编译成适合 2D 游戏素材生成的结构化提示词。

2. **Asset Quality Inspector**

   从图片格式、尺寸、命名规范、分类目录、Prompt 记录、manifest 状态、上传状态等维度检查素材是否可用，并给出 0-100 分质量评分。

3. **Cloud Asset Hub**

   将素材上传、云端访问 URL、CDN 预览链接、zip 素材包和生成记录统一管理，使素材能够被预览、分发和交付。

## 文档索引

- PR 计划：[docs/PR_PLAN.md](docs/PR_PLAN.md)
- PR 1 描述：[docs/pr-descriptions/PR_01_PROJECT_BOOTSTRAP.md](docs/pr-descriptions/PR_01_PROJECT_BOOTSTRAP.md)
- Demo 脚本：[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
- 工程说明：[docs/PROJECT_ENGINEERING.md](docs/PROJECT_ENGINEERING.md)
- 原始设计文档：`GameAssetForge工程设计文档(1) (1).md`

## 验收清单

- [ ] Mock 模式可在无 API Key 环境运行；
- [ ] Prompt Compiler 可生成结构化提示词；
- [ ] Mock Provider 可生成本地素材；
- [ ] 素材生成流程可演示；
- [ ] 素材库可分类展示；
- [ ] 质量评分可查看；
- [ ] manifest.json 可生成；
- [ ] zip 素材包可导出；
- [ ] 七牛云上传或模拟上传状态可演示；
- [ ] README 包含启动说明、依赖说明、原创功能说明；
- [ ] Demo 视频链接已补充；
- [ ] 项目截图已补充。
