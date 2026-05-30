# GameAsset Forge

GameAsset Forge 是一个面向独立游戏开发者的 AI 2D 游戏素材生产与交付平台。系统将自然语言需求转换为结构化生图提示词，通过 Provider 层生成素材，再进行质量检查、素材库管理、云端上传，最后导出 `manifest.json` + zip 素材包。

DEMO链接：https://www.bilibili.com/video/BV1nQGH6cEXm/?vd_source=e7d0bb56ba2148fba546b8f9f68aeb5f

## 技术栈

- **前端**：React 19 + Vite 6
- **后端**：Python 3.13 + FastAPI
- **存储**：JSON 文件数据库 + `storage/` + `runtime/` 目录
- **图片处理**：纯标准库 PNG 解析（struct/zlib），无 Pillow 依赖
- **导出**：`manifest.json` + zip（标准库 zipfile）
- **生图**：Mock / OpenAI（GPT Image / DALL-E），无 Key 自动降级 Mock
- **云存储**：Mock Cloud Provider 默认，已接入七牛云 Kodo
<img width="1672" height="941" alt="已生成图像 1" src="https://github.com/user-attachments/assets/89d125ee-d03d-48aa-8245-4f42148091bf" />

## 核心流程

```text
用户输入需求
    ↓
Prompt Compiler 编译结构化提示词（支持 normal / professional 模式）
    ↓
Image Provider 生成 PNG 素材（Mock / GPT Image）
    ↓
Asset Quality Inspector 质量检查（7 项扣分制，参考 T2I-CompBench）
    ↓
素材分类入库（按 character/enemy/item/tileset/ui/background）
    ↓
云端上传（模拟或真实云存储，设置 cloudUrl）
    ↓
导出 manifest.json + zip 素材包
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
| `GET/PUT` | `/api/config/image` | 生图 API 配置读写（OpenAI） |
| `GET/PUT` | `/api/config/cloud` | 云存储配置读写（Mock / 七牛云） |
| `POST` | `/api/assets/generate` | 生成素材 |
| `GET` | `/api/assets?category=` | 素材库列表 |
| `POST` | `/api/quality/inspect/{asset_id}` | 单素材质量检查 |
| `GET` | `/api/quality/report/{generation_id}` | Generation 质量报告 |
| `POST` | `/api/cloud/upload/{asset_id}` | 单素材云端上传 |
| `POST` | `/api/cloud/upload-generation/{generation_id}` | 批量云端上传 |
| `GET` | `/api/exports` | 可导出 Generation 列表 |
| `POST` | `/api/exports/{generation_id}` | 导出 zip 下载 |

## 原创工程亮点

### 1. Prompt Compiler

将用户自然语言需求拆分为游戏类型、主题、风格、素材类型，编译成适合不同模型（GPT Image / Mock Seed）的结构化提示词。
- normal 模式：快速生成紧凑提示词
- professional 模式：三个方向（production_safe / style_exploration / high_detail）探索候选
- 自动规则降级：无 LLM 密钥时使用规则引擎生成

### 2. Asset Quality Inspector（扣分制）

参考 T2I-CompBench（属性绑定/对象关系）、GenEval（对象存在/计数/颜色/位置）、Intel CGVQM（游戏画面质量度量）设计 7 项扣分检查：
1. PNG 合规（致命项）— 非 PNG 直接 0 分
2. 尺寸规格（30分）— 分级扣分 + 2的幂 + 16对齐 + 纯色检测
3. 命名规范（20分）— snake_case / 无特殊字符
4. 目录分类（20分）— 类型目录结构
5. Prompt 质量（25分）— 长度分级 + 风格关键词 + 名称匹配
6. 元数据完整（15分）— ID/provider/版本号
7. 交付就绪（20分）— cloudUrl / 非 mock

满分 100，及格线 60。

### 3. Cloud Asset Hub

Provider 模式的云端上传层，Mock 模式下返回 `cloud://mock/...` 格式模拟 URL。已接入七牛云 Kodo 对象存储，配置凭证后自动切换为真实上传，返回公开访问 URL。素材上传后 cloudUrl 被持久化到仓库。

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
│   │   │   ├── gpt_image_provider.py  # OpenAI GPT Image / DALL-E
│   │   │   └── qiniu_cloud_provider.py  # 七牛云 Kodo 上传
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
│   │   ├── assetGeneration.js   # API 助手
│   │   ├── generationRequest.js # 请求构建器
│   │   ├── promptCompiler.js    # 提示词编译助手
│   │   ├── imageConfig.js       # 生图配置助手
│   │   ├── cloudConfig.js        # 云存储配置助手
│   │   └── llmConfig.js         # LLM 配置助手
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
- [x] 素材库可按 category 分类展示（含缩略图）
- [x] 质量评分可查看（扣分制，0-100，每项检查详情报）
- [x] manifest.json 可生成（含完整元数据和评分）
- [x] zip 素材包可导出下载
- [x] 云端上传或模拟上传状态可演示
- [x] GPT Image (DALL-E) 真实生图接口可配置
- [x] 前端 Image API 配置页可独立管理生图凭证
- [x] README 包含启动说明、API 文档、原创功能说明
