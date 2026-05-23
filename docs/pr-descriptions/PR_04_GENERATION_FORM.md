# PR 4: 实现素材生成输入表单

## 新增/修改内容

- 修改 `frontend/src/App.jsx`：
  - 将素材生成页从只读示例改为可编辑表单；
  - 支持编辑项目名称、游戏类型、视觉风格、主题和描述；
  - 支持素材任务行的启用/禁用、类型选择、名称编辑和描述编辑；
  - 支持新增素材任务和删除素材任务；
  - 右侧实时展示将来提交给后端的请求 JSON。
- 新增 `frontend/src/generationRequest.js`：
  - 抽离默认表单数据；
  - 抽离 `buildGenerationRequest()` 请求构建逻辑。
- 新增 `frontend/src/generationRequest.test.js`：
  - 覆盖请求预览生成；
  - 覆盖禁用素材不会进入请求 JSON。
- 修改 `frontend/src/styles.css`：
  - 增加素材任务行、复选框、删除按钮、紧凑标题等样式。
- 修改 `frontend/package.json` 和 `frontend/package-lock.json`：
  - 新增 `npm test`；
  - 引入 `vitest` 用于前端单元测试。

## 功能描述

本 PR 实现前端素材生成输入表单，让用户可以在页面中配置游戏项目和素材任务，并实时看到结构化请求 JSON。

本 PR 仍不调用后端 API，不生成真实素材。它的目标是完成后续 Prompt Compiler 和素材生成接口所需的前端输入面。

## 实现思路

- 使用 React `useState` 保存生成表单状态。
- 使用 `useMemo` 根据表单状态实时生成请求 JSON，避免手写重复预览逻辑。
- 将请求构建逻辑拆到 `generationRequest.js`，方便单元测试，也方便后续 API 调用复用。
- 表单中的素材任务使用数组管理，每一行对应一个素材任务：
  - `enabled` 控制是否进入请求；
  - `type/name/description` 对应后端 `assets[]` 字段；
  - 新增和删除操作只影响前端状态。
- 提交按钮当前只更新本地状态提示，后续 PR 会接入真实 API。

## 测试方式

1. 安装依赖：

   ```bash
   cd frontend
   npm install
   ```

2. 运行前端单元测试：

   ```bash
   npm test
   ```

   本 PR 已验证：

   ```text
   1 test file passed
   2 tests passed
   ```

3. 运行生产构建：

   ```bash
   npm run build
   ```

   本 PR 已验证构建通过。

4. 启动前端：

   ```bash
   npm run dev
   ```

   打开：

   ```text
   http://127.0.0.1:4173/
   ```

5. 人工验证：
   - 修改项目名称，右侧 JSON 的 `projectName` 同步变化；
   - 修改游戏类型、视觉风格、主题和描述，右侧 JSON 同步变化；
   - 取消勾选某个素材任务，右侧 `assets` 中不再包含该素材；
   - 点击 `ADD ASSET`，新增一行素材任务；
   - 点击删除按钮，移除对应素材任务；
   - 点击 `PREPARE REQUEST`，表单顶部状态提示更新。

## 依赖与来源说明

- 本 PR 新增 `vitest`，用于测试前端请求构建逻辑。
- 未接入后端 API。
- 未复用外部历史代码。
