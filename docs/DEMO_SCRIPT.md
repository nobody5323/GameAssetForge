# Demo Script — GameAsset Forge

预计时长：5-7 分钟。

## 0:00 - 0:30 项目简介

GameAsset Forge 是一个面向独立游戏开发者的 AI 2D 游戏素材生产与交付平台。它不只是生成单张图片，而是把自然语言需求变成一组结构化、可质检、可导出的游戏素材包。

## 0:30 - 1:30 痛点与方案

独立开发者常缺美术资源。普通 AI 生图工具产出零散，没有质检、分类、导出流程。
本项目的核心差异：**Prompt Compiler → Image Provider → Quality Inspector → Cloud Upload → Export → 交付**，形成闭环。

## 1:30 - 2:30 生成素材

打开 **素材生成** 页面：
1. 填写项目名称、游戏类型（platformer/rpg/roguelike/metroidvania）
2. 选择视觉风格（pixel_art/cartoon/dark_fantasy/cyberpunk）
3. 添加素材任务：character × 1、enemy × 1、item × 1
4. 选择 Prompt Compiler 模式（normal / professional）和目标模型
5. 点击 COMPILE PROMPT → 查看候选提示词
6. 点击 GENERATE ASSETS → 后端生成 PNG 并返回结果

## 2:30 - 3:30 Prompt Compiler 详解

展示 professional 模式下的三个方向候选：
- production_safe（稳定生产）
- style_exploration（风格探索）
- high_detail（高细节展示）

每个候选展示提取的 Tags、per-asset 提示词、Negative Prompt。切换到 LLM 配置页面展示可配置 OpenAI API Key。

## 3:30 - 4:00 素材库

打开 **素材库** 页面：
- 显示所有已生成素材（含 64×64 缩略图）
- 按类型筛选：全部 / character / enemy / item / tileset / ui / background
- 显示质量评分和 provider 标签

## 4:00 - 5:00 质量报告

打开 **质量报告** 页面：
- 下拉选择 generation ID
- 显示总分环形图（颜色编码：≥80 绿，60-79 黄，<60 红）
- 通过/不通过统计
- 每个素材展开 7 项检查详情（逐项显示扣分原因）

## 5:00 - 6:00 云端上传与导出

打开 **导出交付** 页面：
1. 选择 generation → EXPORT ZIP → 浏览器下载 zip 包
2. 解压展示：`manifest.json` + 分类目录 PNG 文件
3. UPLOAD TO CLOUD → 素材获得 `cloud://mock/...` 模拟 URL
4. 再回质量报告页面，验证 cloudUrl 已设置，交付就绪检查通过 ✅

## 6:00 - 6:30 创新点总结

1. **Prompt Compiler**：从自然语言到结构化提示词，支持多模型多方向
2. **Asset Quality Inspector**：7 项扣分制检查，参考 T2I-CompBench / GenEval / CGVQM
3. **Cloud Asset Hub**：Provider 模式云端上传，预留七牛云/S3 扩展
4. **Mock 全流程**：无任何 API Key 也能跑通完整流水线
