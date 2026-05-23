# PR 1: 初始化项目结构与基础文档

## 新增/修改内容

- 新增 `backend/`、`frontend/`、`docs/`、`storage/` 项目目录骨架。
- 新增 `.env.example`，列出后续 Mock Provider、后端地址和七牛云配置需要的环境变量。
- 新增 `.gitignore`，忽略 Python、Node、环境变量和运行时生成文件。
- 新增 `README.md`，说明项目定位、技术栈、核心流程、Mock 模式和验收清单。
- 新增 `docs/PR_PLAN.md`，明确 12 个 PR 的分支、目标、内容和验收方式。
- 新增 `docs/DEMO_SCRIPT.md`，提供 5-7 分钟演示视频脚本。
- 新增 `docs/PROJECT_ENGINEERING.md`，记录工程设计落地说明。
- 保留原始工程设计文档 `GameAssetForge工程设计文档(1) (1).md`。

## 功能描述

本 PR 完成 GameAsset Forge 的项目初始化，为后续前端、后端、Prompt Compiler、Mock Provider、Quality Inspector、导出和云上传功能提供清晰的仓库结构与开发计划。

本 PR 不实现运行时代码，目标是建立可持续拆分 PR 的工程基础，让后续每个功能都能按独立分支、独立验收方式推进。

## 实现思路

- 技术栈按照项目计划确定为 React + Vite 前端、Python FastAPI 后端。
- 仓库结构先用 `.gitkeep` 固定空目录，避免提前混入 PR 2/PR 3 的具体实现代码。
- 文档先行，把产品定位、PR 分层、Demo 脚本、验收清单和环境变量都放入仓库，保证评审能理解项目不是单纯 AI 生图工具，而是一条素材生产流水线。
- `.gitignore` 预先忽略依赖目录、环境变量和运行时生成文件，但保留必要的目录占位文件。

## 测试方式

1. 执行：

   ```bash
   git status
   ```

   验证工作区干净。

2. 执行：

   ```bash
   git branch --show-current
   ```

   验证当前分支为 `feature/pr-01-project-bootstrap`。

3. 执行：

   ```bash
   git log --oneline --decorate --max-count=5
   ```

   验证本 PR 包含多个清晰 commit。

4. 检查仓库文件：

   ```bash
   rg --files
   ```

   验证存在 `README.md`、`.env.example`、`.gitignore`、`docs/PR_PLAN.md`、`docs/DEMO_SCRIPT.md`、`docs/PROJECT_ENGINEERING.md`、`backend/`、`frontend/`、`storage/`。

5. 人工检查 `README.md` 和 `docs/PR_PLAN.md`：
   - README 是否说明项目定位、技术栈、Mock 模式和验收清单。
   - PR 计划是否包含 12 个 PR 的分支名、功能内容和验收方式。

## 依赖与来源说明

- 本 PR 不引入第三方运行时依赖。
- 本 PR 的工程目标和功能拆分来自仓库中的工程设计文档。
- 未复用外部历史代码。
