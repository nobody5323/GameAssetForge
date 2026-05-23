# GameAsset Forge 工程设计文档

> 项目定位：面向独立游戏开发者的 AI 2D 游戏素材生成、质检、云端管理与分发平台。  
> 目标不是做一个“AI 画图壳子”，而是做一条从自然语言需求到可用游戏素材包的生产流水线。

---

## 1. 项目一句话介绍

GameAsset Forge 是一个 AI 2D 游戏素材生产平台。用户输入游戏设定后，系统通过 LLM 解析需求并生成结构化生图提示词，再调用图像生成模型生成素材，随后进行素材质量校验、分类入库、七牛云上传、CDN 预览分发，并支持导出 zip 素材包和 manifest.json，帮助独立游戏开发者快速获得可用的 2D 游戏资产。

---

## 2. 比赛目标与验收重点

### 2.1 作品目标

本项目选择方向：**2D 游戏素材生成**。

核心目标：

- 不是单张图片生成，而是生成一套结构化游戏素材；
- 不是只展示图片，而是完成素材管理、质检、上传、分发、导出；
- 不是纯调用第三方模型，而是体现自己的 Prompt Compiler、Quality Inspector、Asset Pipeline 等工程能力。

### 2.2 验收重点

| 验收点 | 项目对应能力 |
|---|---|
| 创新性 | Prompt Compiler、素材质检评分、云端资产分发 |
| 完整度 | 输入需求、生图、质检、分类、上传、导出闭环 |
| 工程质量 | 模块化架构、Provider 层、Mock 模式、可运行代码 |
| 过程规范 | 持续 commit、持续 PR、清晰 PR 描述 |
| 演示表达 | Demo 视频完整讲解主要功能和效果 |

---

## 3. 核心流程

```text
用户输入游戏需求
↓
LLM 解析需求，输出结构化资产任务
↓
Prompt Compiler 生成专业生图提示词
↓
Image Provider 调用生图模型生成素材
↓
Asset Quality Inspector 校验素材质量
↓
素材自动分类入库
↓
上传七牛云对象存储
↓
生成 CDN 预览链接
↓
导出 zip 素材包与 manifest.json
```

核心链路可以命名为：

```text
Input → Prompt Compiler → Image Provider → Quality Inspector → Cloud Asset Hub → Export
```

---

## 4. 产品功能规划

### 4.1 P0 必须完成

这些功能是项目能否成立的最低闭环。

- 用户输入游戏需求；
- 选择素材风格；
- 选择或自动识别素材类型；
- 生成结构化 Prompt；
- 调用生图 Provider 生成素材；
- 展示生成结果；
- 保存生成记录；
- 素材分类展示；
- 基础质量校验；
- README 启动说明；
- Demo 视频链接；
- 持续 PR 和 commit 记录。

### 4.2 P1 强烈建议完成

这些功能是让项目明显高于普通 AI 生图工具的关键。

- 七牛云上传；
- 生成云端预览链接；
- zip 素材包导出；
- manifest.json 自动生成；
- Prompt 版本记录；
- 质量评分面板；
- Mock Provider，保证无 API Key 也能演示。

### 4.3 P2 有时间再做

这些功能是加分项，不影响主闭环。

- Prompt A/B 测试；
- 小游戏预览页面；
- sprite sheet 生成；
- tileset 切图；
- 背景去除；
- 风格一致性高级评分；
- 多模型 Provider，如 NovelAI、FLUX、Stable Diffusion。

---

## 5. 项目创新点

### 5.1 Prompt Compiler：结构化提示词编排系统

项目不直接把用户原始输入发给生图模型，而是先将需求拆分为：

- 游戏类型；
- 游戏主题；
- 视觉风格；
- 素材类型；
- 生成用途；
- 技术约束；
- 负面约束。

然后由 Prompt Compiler 编译成适合 2D 游戏素材生成的专业提示词。

示例：

```text
用户输入：
我想做一个像素风横版闯关游戏，主题是赛博竹林，需要主角、敌人、金币和地砖。

结构化任务：
{
  "gameType": "platformer",
  "style": "pixel_art",
  "theme": "cyber bamboo forest",
  "assets": ["hero", "enemy", "coin", "tileset"]
}
```

Prompt Compiler 生成每个素材对应的 prompt，而不是只生成一张大图。

---

### 5.2 Asset Quality Inspector：素材质量校验系统

生成素材后，系统不直接认为结果可用，而是进入质量检查流程。

基础检查项：

| 检查项 | 说明 |
|---|---|
| 图片格式 | 是否为 PNG / JPG 等合法格式 |
| 图片尺寸 | 是否符合预期尺寸 |
| 文件命名 | 是否符合 hero_idle.png 等规范 |
| 素材完整度 | 是否包含用户要求的素材类型 |
| 分类结构 | 是否正确进入 character / enemy / item / tileset 等目录 |
| manifest | 是否生成 manifest.json |
| zip 导出 | 是否成功打包 |
| 云端上传 | 是否上传七牛云成功 |

评分示例：

```text
Asset Quality Score: 86 / 100

素材完整度：20 / 20
尺寸规范：12 / 15
命名规范：10 / 10
分类结构：15 / 15
manifest 文件：20 / 20
云端上传：9 / 10

问题提示：
1. enemy_slime.png 尺寸与其他素材不一致。
2. coin_icon.png 背景较复杂，建议重新生成或后处理。
```

---

### 5.3 Cloud Asset Hub：云端素材管理与分发

七牛云不是简单“存图片”，而是作为素材生产流水线中的云端基础设施。

项目中七牛云承担：

- 素材对象存储；
- 生成云端访问 URL；
- CDN 预览分发；
- 素材包 zip 存储；
- 生成记录中的云端链接保存；
- 后续支持团队协作下载。

---

## 6. 技术架构

### 6.1 推荐技术栈

| 模块 | 技术建议 |
|---|---|
| 前端 | React / Vite / Tailwind CSS |
| 后端 | Node.js / Express 或 NestJS |
| 数据存储 | SQLite / JSON 文件 / LowDB，MVP 阶段可简单实现 |
| 生图模型 | Image Provider 抽象，默认接入一个主模型，同时保留 Mock Provider |
| LLM | 用于需求解析和 prompt 生成，也可以先用规则模板替代 |
| 云存储 | 七牛云对象存储 |
| 打包导出 | adm-zip / archiver |
| 图片处理 | sharp / jimp，可用于尺寸检查和基础处理 |

### 6.2 总体架构

```text
frontend/
  用户输入页面
  素材生成页面
  素材库页面
  质量报告页面
  导出页面

backend/
  Prompt Compiler
  Image Provider
  Asset Generation Service
  Quality Inspector
  Asset Repository
  Qiniu Upload Service
  Export Service
```

---

## 7. 推荐目录结构

```text
gameasset-forge/
  README.md
  docs/
    PROJECT_ENGINEERING.md
    PR_PLAN.md
    DEMO_SCRIPT.md
  frontend/
    package.json
    src/
      pages/
        HomePage.jsx
        GeneratePage.jsx
        AssetLibraryPage.jsx
        QualityReportPage.jsx
      components/
        AssetCard.jsx
        PromptPreview.jsx
        QualityScorePanel.jsx
        UploadStatus.jsx
      api/
        assetApi.js
  backend/
    package.json
    src/
      app.js
      routes/
        assetRoutes.js
        exportRoutes.js
      services/
        assetGenerationService.js
        qualityInspectorService.js
        qiniuUploadService.js
        exportService.js
      prompt/
        promptCompiler.js
        templates/
          basePrompt.js
          stylePrompt.js
          assetTypePrompt.js
          technicalPrompt.js
          negativePrompt.js
      providers/
        imageProvider.js
        openaiImageProvider.js
        mockImageProvider.js
      repositories/
        assetRepository.js
      utils/
        fileUtils.js
        imageUtils.js
  storage/
    generated-assets/
    exports/
    db.json
  .env.example
  .gitignore
```

---

## 8. 核心数据结构

### 8.1 用户请求结构

```json
{
  "projectName": "Cyber Bamboo Platformer",
  "gameType": "platformer",
  "style": "pixel_art",
  "theme": "cyber bamboo forest",
  "description": "A 2D side-scrolling game with cyberpunk bamboo forest atmosphere",
  "assets": [
    {
      "type": "character",
      "name": "hero",
      "description": "a brave cyber bamboo warrior"
    },
    {
      "type": "enemy",
      "name": "bamboo_slime",
      "description": "a small glowing slime monster"
    },
    {
      "type": "item",
      "name": "coin",
      "description": "a neon bamboo coin icon"
    },
    {
      "type": "tileset",
      "name": "ground_tile",
      "description": "cyber bamboo forest ground tile"
    }
  ]
}
```

### 8.2 生成记录结构

```json
{
  "id": "asset_001",
  "projectName": "Cyber Bamboo Platformer",
  "assetName": "bamboo_slime",
  "assetType": "enemy",
  "style": "pixel_art",
  "theme": "cyber bamboo forest",
  "promptVersion": "v1.0",
  "finalPrompt": "Generate a 2D pixel art enemy sprite...",
  "modelProvider": "mock/openai/novelai/flux",
  "localPath": "storage/generated-assets/enemy/bamboo_slime.png",
  "cloudUrl": "https://cdn.example.com/assets/bamboo_slime.png",
  "qualityScore": 86,
  "createdAt": "2026-05-23T10:00:00Z"
}
```

### 8.3 manifest.json 示例

```json
{
  "projectName": "Cyber Bamboo Platformer",
  "style": "pixel_art",
  "theme": "cyber bamboo forest",
  "engine": "generic",
  "assets": [
    {
      "name": "hero",
      "type": "character",
      "file": "character/hero.png",
      "width": 1024,
      "height": 1024
    },
    {
      "name": "bamboo_slime",
      "type": "enemy",
      "file": "enemy/bamboo_slime.png",
      "width": 1024,
      "height": 1024
    }
  ]
}
```

---

## 9. Prompt Compiler 设计

### 9.1 Prompt 分层

Prompt 不写成一整段，而是拆成多个层：

```text
角色定位层：你是专业 2D 游戏素材设计师
素材类型层：角色 / 敌人 / 道具 / 地图块 / UI / 背景
风格约束层：像素风 / 卡通风 / 暗黑风 / 赛博朋克风
技术约束层：主体居中、轮廓清晰、无文字、无水印、简单背景
负面约束层：避免写实摄影、3D 渲染、复杂背景、多个主体
输出元数据层：promptVersion、modelProvider、assetType、style
```

### 9.2 Prompt 模板示例

```text
You are a professional 2D game asset artist.
Generate a production-ready 2D game asset for indie game development.

Asset type: enemy sprite
Game theme: cyber bamboo forest
Visual style: pixel art
Subject: small glowing bamboo slime monster

Requirements:
- single enemy only
- centered composition
- clear silhouette
- readable at small size
- simple plain background
- no text
- no watermark
- suitable for 2D game engine import

Avoid:
- realistic photography
- 3D render
- complex background
- multiple characters
- blurry edges
- cropped object
- inconsistent art style
```

### 9.3 Prompt Compiler 伪代码

```js
function compileAssetPrompt({ assetType, style, theme, description, engine }) {
  const basePrompt = getBasePrompt();
  const assetPrompt = getAssetTypePrompt(assetType);
  const stylePrompt = getStylePrompt(style);
  const technicalPrompt = getTechnicalPrompt(engine);
  const negativePrompt = getNegativePrompt();

  return {
    promptVersion: "v1.0",
    finalPrompt: [
      basePrompt,
      `Theme: ${theme}`,
      `Description: ${description}`,
      assetPrompt,
      stylePrompt,
      technicalPrompt,
      negativePrompt
    ].join("\n\n")
  };
}
```

---

## 10. Image Provider 设计

### 10.1 为什么需要 Provider 层

不要把项目写死成某一个模型 API。应该抽象成统一接口，便于替换模型，也便于无 Key 演示。

```text
ImageProvider.generate(prompt, options)
```

### 10.2 Provider 类型

| Provider | 用途 |
|---|---|
| Mock Provider | 本地演示，无 API Key 也能跑通流程 |
| OpenAI Image Provider | 通用 2D 素材生成 |
| NovelAI Provider | 动漫 / 日系 RPG 风格素材生成，可作为扩展 |
| FLUX / SD Provider | 低成本或本地部署扩展 |

### 10.3 返回结果

```json
{
  "provider": "mock",
  "model": "mock-image-generator",
  "imagePath": "storage/generated-assets/enemy/bamboo_slime.png",
  "prompt": "Generate a 2D pixel art enemy sprite...",
  "metadata": {
    "size": "1024x1024",
    "quality": "demo"
  }
}
```

---

## 11. Asset Quality Inspector 设计

### 11.1 评分规则

建议 MVP 阶段先做工程型评分，不强行做复杂 AI 图像理解。

| 维度 | 分值 | 检查方式 |
|---|---:|---|
| 素材完整度 | 20 | 是否生成了用户要求的素材类型 |
| 文件格式 | 10 | 是否为合法图片格式 |
| 图片尺寸 | 15 | 是否能读取尺寸，是否符合预期 |
| 命名规范 | 10 | 文件名是否包含 assetType 和 assetName |
| 分类结构 | 15 | 是否进入正确目录 |
| Prompt 记录 | 10 | 是否保存 finalPrompt 和 promptVersion |
| manifest | 10 | 是否进入 manifest.json |
| 云端上传 | 10 | 是否存在 cloudUrl 或上传状态 |

### 11.2 质量报告示例

```json
{
  "assetId": "asset_001",
  "score": 86,
  "checks": [
    {
      "name": "file_format",
      "passed": true,
      "score": 10,
      "message": "PNG file is valid"
    },
    {
      "name": "image_size",
      "passed": true,
      "score": 15,
      "message": "Image size is 1024x1024"
    },
    {
      "name": "cloud_upload",
      "passed": false,
      "score": 0,
      "message": "Cloud URL is missing"
    }
  ]
}
```

---

## 12. 七牛云模块设计

### 12.1 作用

七牛云用于素材资产的云端交付。

主要功能：

- 上传单个素材图片；
- 上传 zip 素材包；
- 返回云端 URL；
- 保存上传状态；
- 在素材库页面展示云端预览链接。

### 12.2 环境变量

`.env.example`：

```env
QINIU_ACCESS_KEY=your_access_key
QINIU_SECRET_KEY=your_secret_key
QINIU_BUCKET=your_bucket_name
QINIU_DOMAIN=https://your-cdn-domain.example.com
IMAGE_PROVIDER=mock
```

### 12.3 上传结果结构

```json
{
  "assetId": "asset_001",
  "localPath": "storage/generated-assets/enemy/bamboo_slime.png",
  "cloudKey": "gameasset-forge/enemy/bamboo_slime.png",
  "cloudUrl": "https://cdn.example.com/gameasset-forge/enemy/bamboo_slime.png",
  "uploadedAt": "2026-05-23T10:20:00Z"
}
```

---

## 13. 后端 API 设计

### 13.1 生成素材

```http
POST /api/assets/generate
```

请求：

```json
{
  "projectName": "Cyber Bamboo Platformer",
  "style": "pixel_art",
  "theme": "cyber bamboo forest",
  "description": "A platformer game asset pack",
  "assets": [
    { "type": "enemy", "name": "bamboo_slime", "description": "a glowing slime monster" }
  ]
}
```

响应：

```json
{
  "success": true,
  "generationId": "gen_001",
  "assets": [
    {
      "id": "asset_001",
      "name": "bamboo_slime",
      "type": "enemy",
      "localPath": "storage/generated-assets/enemy/bamboo_slime.png",
      "qualityScore": 86
    }
  ]
}
```

### 13.2 获取素材列表

```http
GET /api/assets
```

### 13.3 获取质量报告

```http
GET /api/assets/:id/quality
```

### 13.4 上传七牛云

```http
POST /api/assets/:id/upload
```

### 13.5 导出素材包

```http
POST /api/exports/:generationId
```

---

## 14. 前端页面设计

### 14.1 首页

展示：

- 项目简介；
- 核心流程；
- 开始生成按钮；
- Demo 示例。

### 14.2 生成页面

包含：

- 项目名称输入；
- 游戏类型选择；
- 风格选择；
- 主题输入；
- 素材类型勾选；
- 用户描述输入；
- 生成按钮；
- Prompt 预览区域。

### 14.3 素材库页面

展示：

- 素材卡片；
- 素材类型筛选；
- 本地路径 / 云端链接；
- 质量评分；
- 上传状态；
- 下载按钮。

### 14.4 质量报告页面

展示：

- 总分；
- 各项检查结果；
- 问题提示；
- 重新生成按钮；
- 上传七牛云按钮；
- 导出素材包按钮。

---

## 15. Mock 模式设计

Mock 模式非常重要，因为评委可能没有你的 API Key。

Mock 模式要求：

- 不调用真实生图模型；
- 从 `storage/mock-assets/` 复制预置图片；
- 仍然完整走 Prompt Compiler、Quality Inspector、分类、上传、导出流程；
- README 中说明如何开启 Mock 模式。

环境变量：

```env
IMAGE_PROVIDER=mock
```

Mock Provider 仍然返回：

```json
{
  "provider": "mock",
  "model": "mock-provider-v1",
  "imagePath": "storage/generated-assets/enemy/bamboo_slime.png",
  "prompt": "...",
  "metadata": {
    "mock": true
  }
}
```

---

## 16. 开发计划与 PR 拆分

比赛规则强调持续 PR 和 commit，不能最后一天一次性导入所有代码。

### 16.1 分支策略

```text
main：保持可运行
feature/xxx：每个功能一个分支
PR：feature 分支合并到 main
```

### 16.2 推荐 PR 计划

| PR | 标题 | 内容 |
|---|---|---|
| PR 1 | 初始化项目结构与 README 草稿 | 创建前后端目录、基础 README、环境变量示例 |
| PR 2 | 实现前端首页和生成表单 | 用户输入需求、选择风格和素材类型 |
| PR 3 | 实现 Prompt Compiler | 模板化生成结构化生图提示词 |
| PR 4 | 实现 Mock Image Provider | 无 API Key 时可跑通生成流程 |
| PR 5 | 实现素材生成服务 | 串联 Prompt Compiler 和 Image Provider |
| PR 6 | 实现素材库与分类展示 | character/enemy/item/tileset 分类展示 |
| PR 7 | 实现 Asset Quality Inspector | 尺寸、格式、命名、完整度评分 |
| PR 8 | 实现 manifest.json 生成 | 将素材元数据写入 manifest |
| PR 9 | 实现 zip 素材包导出 | 打包 generated-assets 和 manifest |
| PR 10 | 实现七牛云上传服务 | 上传图片和 zip，保存 cloudUrl |
| PR 11 | 完善前端质量报告页面 | 展示质量评分和检查项 |
| PR 12 | 完善 README、截图和 Demo 视频链接 | 补充部署、依赖、原创说明、视频链接 |

### 16.3 PR 模板

每个 PR 描述必须包含：

```md
## 功能描述
本 PR 实现了 xxx 功能，用于 xxx。

## 实现思路
使用 xxx 技术实现，核心逻辑是 xxx。

## 测试方式
1. 执行 xxx 命令
2. 打开 xxx 页面
3. 输入 xxx
4. 验证 xxx 结果

## 依赖与来源说明
本 PR 是否引入第三方依赖：是 / 否  
如有依赖，请说明依赖用途。  
如复用历史代码，请说明来源。
```

---

## 17. README 必须包含的内容

README 是评委验收重点，建议包含：

```text
1. 项目名称
2. 项目简介
3. 选择议题：2D 游戏素材生成
4. 核心功能
5. 技术架构
6. 项目目录结构
7. 本地启动方式
8. 环境变量说明
9. Mock 模式说明
10. 七牛云配置说明
11. Prompt Compiler 设计说明
12. Asset Quality Inspector 设计说明
13. 第三方依赖清单
14. 原创功能说明
15. Demo 视频链接
16. 功能截图
17. 开发过程说明与 PR 链接
18. 后续计划
```

---

## 18. Demo 视频脚本

建议视频控制在 5 到 7 分钟。

```text
0:00 - 0:20 项目一句话介绍
说明这是 AI 2D 游戏素材生成与云端分发平台。

0:20 - 1:00 痛点说明
独立游戏开发者缺少美术资源，普通 AI 生图又难以直接进入游戏开发流程。

1:00 - 2:00 输入需求并生成素材
展示用户输入游戏主题、风格、素材类型，点击生成。

2:00 - 3:00 展示 Prompt Compiler
展示系统如何把用户输入转换为结构化 prompt。

3:00 - 4:00 展示生成结果和素材库
展示角色、敌人、道具、tileset 等分类结果。

4:00 - 5:00 展示质量评分
展示 Asset Quality Inspector 的评分和检查项。

5:00 - 6:00 展示七牛云上传和素材包导出
展示云端链接、manifest.json、zip 导出。

6:00 - 6:30 总结创新点
强调 Prompt Compiler、Quality Inspector、Cloud Asset Hub 三个核心亮点。
```

---

## 19. 项目风险与应对

| 风险 | 应对方案 |
|---|---|
| 生图 API 不稳定 | 提供 Mock Provider，保证流程可演示 |
| 生成效果不稳定 | 通过 Prompt Compiler 加强约束，通过质检提示问题 |
| 七牛云配置失败 | 本地保存仍可运行，README 说明环境变量配置 |
| 时间不够 | 优先完成 P0 + P1 核心闭环，不做复杂小游戏 |
| 被认为是套壳 | 突出 Prompt Compiler、Quality Inspector、manifest、zip、云端分发 |
| PR 不规范 | 严格按照 PR 模板，每个 PR 只做一件事 |

---

## 20. 可用于 AI Coding 的开发提示词

### 20.1 初始化项目

```text
请帮我初始化一个名为 GameAsset Forge 的全栈项目。
前端使用 React + Vite，后端使用 Node.js + Express。
项目需要包含 frontend、backend、docs、storage 目录。
请添加基础 README、.env.example、.gitignore，并保证项目可以本地启动。
```

### 20.2 Prompt Compiler

```text
请帮我实现一个 2D 游戏素材生成项目的 Prompt Compiler 模块。

要求：
1. 输入 assetType、style、theme、description、engine。
2. 根据 assetType 选择模板，包括 character、enemy、item、tileset、ui、background。
3. 根据 style 注入风格约束，包括 pixel_art、cartoon、dark_fantasy、cyberpunk。
4. 自动添加技术约束：single asset、centered、no text、no watermark、simple background、suitable for 2D game engine import。
5. 自动添加 negative prompt。
6. 输出 finalPrompt、promptVersion 和 metadata。
7. 代码要模块化，方便后续扩展。
8. 补充至少 5 个测试用例。
```

### 20.3 Quality Inspector

```text
请帮我实现 Asset Quality Inspector 模块。

要求：
1. 输入素材文件路径和素材 metadata。
2. 检查图片格式、图片尺寸、命名规范、分类目录、promptVersion、manifest 状态、cloudUrl 状态。
3. 每个检查项返回 passed、score、message。
4. 最终输出 0-100 的总分。
5. 代码需要可扩展，方便未来加入 CLIPScore 或风格一致性评分。
```

### 20.4 Mock Provider

```text
请帮我实现 Mock Image Provider。

要求：
1. 实现统一接口 generate(prompt, options)。
2. 不调用真实生图 API。
3. 根据 assetType 从 storage/mock-assets 中选择一张图片复制到 storage/generated-assets 对应目录。
4. 返回 imagePath、provider、model、prompt、metadata。
5. 保证后续 Quality Inspector、上传、导出流程可以继续运行。
```

---

## 21. 最终答辩表达

不要这样介绍：

```text
我做了一个 AI 生成图片工具。
```

应该这样介绍：

```text
我做的是一个面向独立游戏开发者的 AI 2D 游戏素材生产与云端分发平台。
系统通过 LLM 将用户自然语言需求转换为结构化生图提示词，调用图像生成模型产出素材，并通过素材质量校验、自动分类、七牛云上传、CDN 分发和素材包导出，实现从需求到可用游戏资产的完整闭环。
```

核心亮点表达：

```text
1. Prompt Compiler：将自然语言需求编译为面向游戏素材生产的结构化提示词。
2. Asset Quality Inspector：从格式、尺寸、命名、完整度、导出和上传状态等维度检查素材可用性。
3. Cloud Asset Hub：通过七牛云完成素材存储、预览、分发和素材包交付。
```

---

## 22. 验收前检查清单

提交前必须确认：

- [ ] 仓库是在开题后创建；
- [ ] commit 时间在比赛周期内；
- [ ] 没有最后一天一次性导入全部代码；
- [ ] 至少有多个清晰 PR；
- [ ] 每个 PR 标题和描述完整；
- [ ] main 分支代码可运行；
- [ ] README 有启动说明；
- [ ] README 有第三方依赖说明；
- [ ] README 有原创功能说明；
- [ ] README 有 Demo 视频链接；
- [ ] Demo 视频可访问、可播放、有声音讲解；
- [ ] Mock 模式可运行；
- [ ] 素材生成流程可演示；
- [ ] 质量评分可演示；
- [ ] zip 导出可演示；
- [ ] 七牛云上传或本地模拟上传状态可演示；
- [ ] manifest.json 能生成；
- [ ] 项目截图已放入 README。

---

## 23. 当前版本建议范围

三天比赛周期内建议不要贪多。最稳版本是：

```text
用户输入需求
↓
Prompt Compiler 生成提示词
↓
Mock / Image Provider 生成素材
↓
素材分类展示
↓
Quality Inspector 给出评分
↓
生成 manifest.json
↓
导出 zip
↓
上传七牛云并生成预览链接
```

只要这个闭环稳定，项目就比单纯 AI 生图工具强很多。

---

## 24. 版本规划

### v0.1 基础闭环

- 初始化项目；
- 前端输入表单；
- 后端生成接口；
- Mock Provider；
- 素材展示。

### v0.2 工程化生成

- Prompt Compiler；
- 素材类型模板；
- 风格模板；
- Prompt 预览；
- 生成记录保存。

### v0.3 质量与导出

- Asset Quality Inspector；
- 质量报告页面；
- manifest.json；
- zip 导出。

### v0.4 云端交付与验收

- 七牛云上传；
- 云端预览链接；
- README 完善；
- Demo 视频；
- PR 整理；
- 最终验收检查。

---

## 25. 总结

本项目的关键不是“能不能调用模型生成图片”，而是能否把 AI 生图能力工程化成一条游戏素材生产流水线。

最核心的三个工程能力：

```text
Prompt Compiler：生成得更准
Quality Inspector：判断能不能用
Cloud Asset Hub：让素材能管理、能预览、能交付
```

最终项目应呈现为：

```text
一句话需求 → 结构化 Prompt → 批量生成素材 → 自动质检 → 分类入库 → 七牛云分发 → zip + manifest 导出
```

这才是一个更容易让验收组眼前一亮的 2D 游戏素材生成项目。
