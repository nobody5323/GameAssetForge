# GameAsset Forge

GameAsset Forge 是一个面向独立游戏开发者的 AI 2D 游戏素材生产与交付平台。系统将自然语言需求转换为结构化生图提示词，通过 Provider 层生成素材，再进行质量检查、素材库管理、云端上传，最后导出 `manifest.json` + zip 素材包。

DEMO链接：https://www.bilibili.com/video/BV1nQGH6cEXm/?vd_source=e7d0bb56ba2148fba546b8f9f68aeb5f

## 技术栈

- **前端**：React 19 + Vite 6
- **后端**：Python 3.13 + FastAPI
- **存储**：JSON 文件数据库 + `storage/` + `runtime/` 目录
- **图片处理**：纯标准库 PNG 解析（struct/zlib），无 Pillow 依赖
- **导出**：`manifest.json` + zip（标准库 zipfile）
- **生图**：Mock / OpenAI（GPT Image / DALL-E），支持 micuapi.ai 中转站，无 Key 自动降级 Mock
- **图生图**：支持 `/v1/images/edits` multipart 以图生图（二次生成保持角色一致性）
- **云存储**：Mock Cloud Provider 默认，已接入七牛云 Kodo
<img width="1672" height="941" alt="已生成图像 1" src="https://github.com/user-attachments/assets/89d125ee-d03d-48aa-8245-4f42148091bf" />

## 核心流程

```text
用户输入需求
    ↓
Prompt Compiler 编译结构化提示词（支持 normal / professional 模式）
    ↓
Image Provider 生成 PNG 素材（Mock / GPT Image / micuapi.ai）
    ↓
二次生成（以图生图）：选择素材 → 动作姿态（移动/攻击/防御/技能）→ 保持角色一致性的变体
    ↓
Asset Quality Inspector 质量检查（6 维度加权评分制）
    ↓
素材分类入库（按 character/enemy/item/tileset/ui/background）
    ↓
云端上传（模拟或真实云存储，设置 cloudUrl）
    ↓
导出 — 按素材勾选或按 generation 导出 manifest.json + zip 素材包
```

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API 文档自动生成：http://127.0.0.1:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev                      # 开发模式 http://127.0.0.1:5173
npm run build                    # 生产构建
```

### 运行测试

```bash
# 后端（91 个测试）
cd backend && python -m pytest

# 前端（17 个测试）
cd frontend && npx vitest run
```

## Mock 模式（默认，无需 API Key）

```env
CLOUD_PROVIDER=mock
```

无 API Key 时自动使用 Mock Provider，完整流程可演示：
`Prompt 编译 → Mock 生成 → 质量检查 → 素材库 → 云端模拟上传 → manifest → zip 导出`

### 接入真实 LLM（可选）

在 LLM 配置页面或 `.env` 中设置：

```env
PROMPT_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_PROMPT_MODEL=gpt-5-mini
```

### 接入真实生图 API（可选）

在 **Image API 配置** 页面或 `.env` 中设置：

```env
# OpenAI
IMAGE_GEN_PROVIDER=openai
IMAGE_GEN_API_KEY=sk-...
IMAGE_GEN_MODEL=gpt-image-2
IMAGE_GEN_SIZE=1024x1024
```

在素材生成页选择目标模型（GPT Image）后，系统自动调用对应的真实 API。无凭证时自动降级为 Mock Provider。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/prompts/compile` | 编译提示词 |
| `GET/POST` | `/api/config/llm` | LLM 配置读写 |
| `GET/PUT` | `/api/config/image` | 生图 API 配置读写（OpenAI / micuapi.ai） |
| `GET/PUT` | `/api/config/cloud` | 云存储配置读写（Mock / 七牛云） |
| `POST` | `/api/assets/generate` | 生成素材 |
| `POST` | `/api/assets/{asset_id}/regenerate` | 单素材二次生成（指定动作） |
| `POST` | `/api/assets/batch-regenerate` | 批量二次生成（多动作） |
| `GET` | `/api/assets?category=` | 素材库列表 |
| `POST` | `/api/quality/inspect/{asset_id}` | 单素材质量检查 |
| `GET` | `/api/quality/report/{generation_id}` | Generation 质量报告 |
| `POST` | `/api/cloud/upload/{asset_id}` | 单素材云端上传 |
| `POST` | `/api/cloud/upload-generation/{generation_id}` | 批量云端上传 |
| `GET` | `/api/exports` | 可导出 Generation 列表 |
| `POST` | `/api/exports/selected` | 按素材 ID 勾选导出 zip |
| `POST` | `/api/exports/{generation_id}` | 按 generation 导出 zip |

## 原创工程亮点

### 1. Prompt Compiler

将用户自然语言需求拆分为游戏类型、主题、风格、素材类型，编译成适合不同模型（GPT Image / Mock Seed）的结构化提示词。
- normal 模式：快速生成紧凑提示词
- professional 模式：三个方向（production_safe / style_exploration / high_detail）探索候选
- 自动规则降级：无 LLM 密钥时使用规则引擎生成

### 2. 二次生成（以图生图）

基于已生成的素材创建保持角色一致性的动作变体，支持 6 种素材类型 × 4 种动作姿态：

- **character / enemy**：移动、攻击、防御、技能释放
- **item / tileset / ui / background**：对应类型的变体动作

技术实现：
- 通过 `/v1/images/edits` multipart 接口发送参考图，实现真正的以图生图
- 极简 prompt：动作标签 + 严格保持原图一致 + 原始角色描述
- 支持单素材和批量二次生成，结果自动入库

### 3. Asset Quality Inspector（加权评分制）

### 3. Asset Quality Inspector（加权评分制）

6 维度加权评分，每维度含子检查点，百分比权重：
1. 技术合规 — PNG 格式 / 尺寸 / 位深度（25%）
2. 内容完整性 — 非纯色 / 非空白 / 有效像素（20%）
3. 命名规范 — snake_case / 无特殊字符（10%）
4. 目录结构 — 类型目录归类（10%）
5. Prompt 质量 — 长度 / 关键词覆盖 / 名称匹配（20%）
6. 交付就绪 — cloudUrl / provider / 元数据完整（15%）

满分 100，及格线 60。

### 4. Cloud Asset Hub

Provider 模式的云端上传层，Mock 模式下返回 `cloud://mock/...` 格式模拟 URL。已接入七牛云 Kodo 对象存储，配置凭证后自动切换为真实上传，返回公开访问 URL。素材上传后 cloudUrl 被持久化到仓库。

### 5. 灵活导出

支持两种导出模式：
- **按素材勾选**：跨 generation 自由勾选素材，一键打包导出 zip
- **按 generation 导出**：选择某个 generation 批次全部导出

导出包包含 `manifest.json`（元数据 + 质量评分）和所有选中素材的 PNG 文件。

## 项目结构

```
GameAssetForge/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 运行时配置
│   │   ├── models/              # Pydantic 数据模型
│   │   ├── routes/              # API 路由
│   │   ├── services/            # 业务逻辑
│   │   ├── providers/           # 抽象 Provider 层（图片/云存储/LLM）
│   │   │   ├── gpt_image_provider.py  # GPT Image / DALL-E / micuapi.ai 中转
│   │   │   ├── mock_image_provider.py # Mock 降级 Provider
│   │   │   └── qiniu_cloud_provider.py  # 七牛云 Kodo 上传
│   │   ├── presets/              # 二次生成预设（动作/类型）
│   │   ├── repositories/        # 数据访问层
│   │   ├── prompt/              # Prompt Compiler 核心
│   │   └── utils/               # PNG 工具等
│   ├── tests/                   # pytest 测试
│   ├── runtime/                 # 运行时生成文件
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # 主应用 + 所有页面组件
│   │   ├── styles.css           # 像素风格全局样式
│   │   ├── assetGeneration.js   # API 助手（生成/二次生成/导出）
│   │   ├── generationRequest.js # 请求构建器
│   │   ├── promptCompiler.js    # 提示词编译助手
│   │   ├── imageConfig.js       # 生图配置助手
│   │   ├── cloudConfig.js        # 云存储配置助手
│   │   ├── llmConfig.js         # LLM 配置助手
│   │   └── exportHelpers.js     # 导出下载助手
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── PR_PLAN.md               # 12-PR 规划
│   ├── DEMO_SCRIPT.md           # Demo 脚本
│   ├── PROJECT_ENGINEERING.md   # 工程设计文档
│   └── pr-descriptions/         # 各 PR 详细描述
├── storage/                     # 静态度量（种子素材）
├── .env.example
└── README.md
```

## 文档索引

- PR 计划：[docs/PR_PLAN.md](docs/PR_PLAN.md)
- Demo 脚本：[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
- 工程设计：[docs/PROJECT_ENGINEERING.md](docs/PROJECT_ENGINEERING.md)

## 验收清单

- [x] Mock 模式可在无 API Key 环境运行
- [x] Prompt Compiler 可生成结构化提示词（normal + professional）
- [x] Mock Provider 可生成本地 PNG 素材
- [x] 素材生成流程可演示（前端 → 后端 → Provider → 入库）
- [x] 二次生成（以图生图）支持 6 种类型 × 4 种动作姿态
- [x] 二次生成支持单素材和批量模式
- [x] 素材库可按 category 分类展示（含缩略图 + Lightbox 放大预览）
- [x] 质量评分可查看（6 维度加权评分，0-100）
- [x] manifest.json 可生成（含完整元数据和评分）
- [x] 按素材勾选 / 按 generation 两种方式导出 zip
- [x] 云端上传或模拟上传状态可演示
- [x] GPT Image (DALL-E / gpt-image-2) 真实生图接口可配置
- [x] micuapi.ai 中转站支持（含图生图 /v1/images/edits）
- [x] 前端 Image API 配置页可独立管理生图凭证
- [x] README 包含启动说明、API 文档、原创功能说明
