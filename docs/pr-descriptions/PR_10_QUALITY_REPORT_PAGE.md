# PR 10: Quality Report Page 质量报告页

## 新增/修改内容

- 前端 `assetGeneration.js` 新增 `fetchQualityReport(generationId)` helper
- 前端 `QualityPage` 完全重写：
  - 自动从素材库加载已有 generation ID 列表
  - 下拉框选择 generation ID，或手动输入
  - **总览卡片**：大号分数环 + 素材总数/通过数/未通过数统计
  - **单素材报告卡片**：逐一展示每个素材的质量报告
  - 每项检查展开显示：通过/失败图标、检查详情、扣分数额
  - 加载态 / 空素材报错 / 无素材提示
- 新增质量报告页 CSS：分数环、统计卡片、检查行样式（通过绿色 / 失败红色）
- 前端 `App.jsx` 新增 `AlertTriangle`、`XCircle` 图标导入
- 前端测试新增 `fetchQualityReport` 导出验证

## 功能描述

PR10 将 PR9 后端质量检查器的结果以可视化方式呈现在前端质量报告页。

### 页面交互流程

1. 页面自动加载所有已有 generation ID 到下拉框
2. 用户选择（或手动输入）要检查的 generation ID
3. 点击 `INSPECT` 按钮，调用 `GET /api/quality/report/{generationId}`
4. 展示报告：

```
┌─────────────────────────────────┐
│  ┌──────┐  3 素材总数           │
│  │  45  │  2 通过 (≥60)        │
│  │ /100 │  1 未通过 (<60)      │
│  └──────┘                       │
├─────────────────────────────────┤
│ 45/100  hero  character         │
│  ✓ PNG 合规  有效PNG格式     ✓  │
│  ✗ 尺寸规格  64x64<128px   -25  │
│  ✓ 命名规范  snake_case     ✓  │
│  ...                            │
├─────────────────────────────────┤
│ 35/100  slime  enemy            │
│  ...                            │
└─────────────────────────────────┘
```

### 得分颜色编码

| 分数区间 | 颜色 | 含义 |
|---------|------|------|
| ≥ 80 | 绿色 `#00e436` | 高质量 |
| 60–79 | 黄色 `#ffec27` | 待改进 |
| < 60 | 红色 `#ff004d` | 不合格 |

## 实现思路

- 复用 PR9 的 `GET /api/quality/report/{generationId}` 接口，无需新增后端代码
- `QualityPage` 挂载时通过 `fetchAssets()` 获取所有素材，提取去重的 generationId 列表
- 使用 `useState` 管理 generationId、loading、error、report 四个状态
- 检查项按 `passed` 字段区分样式：绿色 `CheckCircle2` vs 红色 `XCircle`
- CSS 保持像素风暗色主题，分数环用 4px 实色边框，无圆角

## 测试方式

后端：

```bash
cd backend
python -m pytest  # 34 passed
```

前端：

```bash
cd frontend
npx vitest run   # 4 files, 15 tests passed
npm run build    # vite build completed
```

人工验证：

```bash
# 1. 先生成素材
curl -X POST http://127.0.0.1:8000/api/assets/generate \
  -H "Content-Type: application/json" \
  -d '{"projectName":"Test","gameType":"platformer","style":"pixel_art","theme":"test","description":"test","targetModel":"mock_seed","promptMode":"normal","assets":[{"type":"character","name":"hero","description":"hero"},{"type":"enemy","name":"bad_slime","description":"slime"}]}'

# 2. 打开前端质量报告页
# http://127.0.0.1:4174/ → 切换到"质量报告"
# → 下拉框选择 generation ID → 点击 INSPECT
# → 查看总览分数、各素材检查详情
```

验证要点：
- 分数环显示正确的 overallScore
- 通过/未通过数量与 passCount/failCount 一致
- 检查行通过项绿色 ✓、失败项红色 ✗ 并显示扣分
- mock 素材因尺寸+纯色+mock+cloudUrl 扣分在 35-55 分区间

## 依赖与来源说明

- 不新增第三方依赖
- 前端复用 PR2/PR4/PR8 的 React、Vite、lucide-react、Vitest
- 后端接口依赖 PR9 的 `GET /api/quality/report/{generationId}`
