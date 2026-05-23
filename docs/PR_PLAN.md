# GameAsset Forge PR Plan

## Strategy

Use 12 clear PRs so the project history demonstrates continuous development rather than a single large drop.

| PR | Branch | Title | Core Content | Acceptance |
|---|---|---|---|---|
| PR 1 | `feature/pr-01-project-bootstrap` | Initialize project structure and documentation | Create `frontend/`, `backend/`, `docs/`, `storage/`, README, `.env.example`, `.gitignore` | Repository structure and project positioning are clear |
| PR 2 | `feature/pr-02-frontend-shell` | Build frontend shell | React + Vite app, layout, navigation, page placeholders | `npm run dev` opens usable shell |
| PR 3 | `feature/pr-03-backend-fastapi-shell` | Build FastAPI shell | FastAPI app, `/api/health`, backend folders | Backend starts and health check responds |
| PR 4 | `feature/pr-04-generation-form` | Add generation form | Project, style, theme, description, asset type inputs | UI previews request JSON |
| PR 5 | `feature/pr-05-prompt-compiler` | Implement Prompt Compiler | Asset and style templates, prompt metadata, tests | At least 5 prompt scenarios pass |
| PR 6 | `feature/pr-06-mock-image-provider` | Implement Mock Image Provider | Provider interface and local mock generation | Generates local image paths without API keys |
| PR 7 | `feature/pr-07-asset-generation-service` | Implement generation service | Connect compiler, provider, repository, `POST /api/assets/generate` | API returns generationId and assets |
| PR 8 | `feature/pr-08-asset-library` | Implement asset library | `GET /api/assets`, frontend cards, filters | Assets appear by category |
| PR 9 | `feature/pr-09-quality-inspector` | Implement Quality Inspector | Format, size, naming, category, prompt, manifest, upload checks | Quality tests cover normal and failing cases |
| PR 10 | `feature/pr-10-quality-report-page` | Implement quality report page | `GET /api/assets/{id}/quality`, score UI | Report shows checks with messages |
| PR 11 | `feature/pr-11-manifest-and-zip-export` | Implement manifest and zip export | `manifest.json`, `POST /api/exports/{generationId}` | Zip contains assets and manifest |
| PR 12 | `feature/pr-12-cloud-and-demo-docs` | Implement cloud simulation and final docs | Upload endpoint, simulated URLs, README, demo script | Full mock demo can be run without secrets |

## PR Template

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
