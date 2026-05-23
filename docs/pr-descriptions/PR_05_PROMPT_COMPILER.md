# PR 5: Prompt Compiler 提示词工程闭环

## 新增/修改内容

- 新增 `POST /api/prompts/compile` 后端接口。
- 新增提示词请求、候选、素材提示词等 Pydantic 数据模型。
- 新增标签提取、模型提示词优化、提示词评分、规则降级 Provider、OpenAI LLM Provider。
- 前端生成页新增普通/专业模式、GPT Image/NovelAI 目标模型选择、编译和重新生成按钮。
- 前端新增候选提示词展示区，支持选择候选方案、查看评分、标签、每个素材的 finalPrompt 和 negativePrompt。
- 修复前端现有中文文案编码损坏，保证页面可读、可构建。
- 新增前后端单元测试，覆盖请求构建、候选选择、模式阈值、模型提示词结构和规则降级。

## 功能描述

本 PR 实现提示词工程阶段，不调用真实生图 API。用户在生成页填写游戏设定和素材清单后，可以先编译提示词：

- 普通模式返回 1 套候选，阈值 60 分。
- 专业模式返回 3 套整包候选，阈值 80 分。
- 专业模式方向固定为 `production_safe`、`style_exploration`、`high_detail`。
- GPT Image 输出自然语言型英文提示词。
- NovelAI 输出 tag-oriented 提示词，并单独返回 negative prompt。
- 无 OpenAI Key、请求失败或解析失败时，自动使用 `rule_fallback`，保证演示不中断。

## 实现思路

- 后端使用 FastAPI + Pydantic 定义稳定接口契约。
- `tag_extractor.py` 从项目名、游戏类型、风格、主题、描述和素材描述中提取结构化标签，并补充中文关键词对应的英文生图标签。
- `model_optimizers.py` 按目标模型生成两类提示词 profile：
  - `gpt_image`：自然语言结构，包含 subject、style、composition、game usability、technical requirements 和 Avoid 约束。
  - `novelai`：逗号分隔标签，negative prompt 独立输出。
- `prompt_scorer.py` 按结构完整度、素材类型匹配、模型适配度、技术约束和负面约束给出 0-100 分。
- `openai_llm_provider.py` 接入 OpenAI Responses API，文本模型通过 `OPENAI_PROMPT_MODEL` 配置；默认模型为 `gpt-5-mini`。OpenAI 官方模型页包含 GPT Image 系列图像模型和 GPT-5 系列文本模型，本 PR 只把 GPT Image 作为目标提示词 profile，不调用图像生成。
- `prompt_compiler.py` 统一执行真实 LLM 优先、规则降级兜底的策略。
- 前端保留当前像素风格，在生成页内增加 Prompt Compiler 控件和候选结果区；选中候选只保存在本地状态，PR7 再接入素材生成链路。

## 测试方式

后端：

```bash
cd backend
python -m pytest
```

已验证：

```text
6 passed
```

前端：

```bash
cd frontend
npm test
npm run build
```

已验证：

```text
2 test files passed
6 tests passed
vite build completed
```

接口人工验证：

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问：

```text
POST http://127.0.0.1:8000/api/prompts/compile
```

无 `OPENAI_API_KEY` 时应返回：

- `provider: "rule_fallback"`
- `fallback: true`
- 普通模式 1 个候选
- 专业模式 3 个候选

前端人工验证：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 4173
```

打开：

```text
http://127.0.0.1:4173/
```

检查：

- 页面能看到生成任务表单和 Prompt Compiler 区域。
- 切换普通/专业模式，请求预览中的 `mode` 同步变化。
- 切换 GPT Image/NovelAI，请求预览中的 `targetModel` 同步变化。
- 后端启动时点击 `COMPILE PROMPT` 能显示候选提示词。
- 点击候选标题会更新选中状态。

## 依赖与来源说明

- 后端复用 PR3 已引入的 `fastapi`、`pydantic`、`httpx`、`pytest`。
- 前端复用 PR2/PR4 已引入的 React、Vite、lucide-react、Vitest。
- OpenAI 模型信息参考官方模型文档：https://platform.openai.com/docs/models
- 本 PR 不引入新的生图 SDK，不调用真实图像生成模型。
