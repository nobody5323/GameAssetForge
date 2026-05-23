import { useState } from 'react';
import { Archive, FileJson, Image, Play, ShieldCheck } from 'lucide-react';

const views = [
  { id: 'generate', label: '素材生成', icon: Play },
  { id: 'library', label: '素材库', icon: Image },
  { id: 'quality', label: '质量报告', icon: ShieldCheck },
  { id: 'export', label: '导出交付', icon: Archive },
];

function App() {
  const [activeView, setActiveView] = useState('generate');
  const currentView = views.find((view) => view.id === activeView) || views[0];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">GF</div>
          <div>
            <h1>GameAsset Forge</h1>
            <p>AI 2D 游戏素材流水线</p>
          </div>
        </div>

        <nav className="nav-list" aria-label="主导航">
          {views.map((view) => (
            <NavButton
              key={view.id}
              view={view}
              active={activeView === view.id}
              onClick={() => setActiveView(view.id)}
            />
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <p>PR 2 前端基础界面</p>
          <h2>{currentView.label}</h2>
        </header>

        {activeView === 'generate' ? <GeneratePage /> : null}
        {activeView === 'library' ? <LibraryPage /> : null}
        {activeView === 'quality' ? <QualityPage /> : null}
        {activeView === 'export' ? <ExportPage /> : null}
      </section>
    </main>
  );
}

function NavButton({ view, active, onClick }) {
  const Icon = view.icon;

  return (
    <button className={active ? 'active' : ''} onClick={onClick}>
      <Icon size={18} />
      {view.label}
    </button>
  );
}

function GeneratePage() {
  return (
    <div className="content-grid">
      <section className="panel">
        <div className="section-heading">
          <h3>生成任务</h3>
          <span>表单预览</span>
        </div>
        <div className="field-grid">
          <label>
            项目名称
            <input value="Cyber Bamboo Platformer" readOnly />
          </label>
          <label>
            游戏类型
            <select value="platformer" readOnly>
              <option value="platformer">platformer</option>
            </select>
          </label>
          <label>
            视觉风格
            <select value="pixel_art" readOnly>
              <option value="pixel_art">pixel_art</option>
            </select>
          </label>
          <label>
            主题
            <input value="cyber bamboo forest" readOnly />
          </label>
        </div>
        <label>
          描述
          <textarea
            value="一个赛博竹林主题的 2D 横版闯关游戏，需要主角、敌人、金币和地砖素材。"
            readOnly
          />
        </label>
        <button className="primary-button" type="button">
          <Play size={18} />
          后续 PR 接入生成
        </button>
      </section>

      <section className="panel preview-panel">
        <div className="section-heading">
          <h3>Prompt Preview</h3>
          <FileJson size={18} />
        </div>
        <pre>{`{
  "projectName": "Cyber Bamboo Platformer",
  "style": "pixel_art",
  "assets": ["hero", "enemy", "coin", "tileset"]
}`}</pre>
      </section>
    </div>
  );
}

function LibraryPage() {
  const samples = [
    { name: 'hero', type: 'character', score: 0 },
    { name: 'bamboo_slime', type: 'enemy', score: 0 },
    { name: 'coin', type: 'item', score: 0 },
    { name: 'ground_tile', type: 'tileset', score: 0 },
  ];

  return (
    <section className="panel">
      <div className="section-heading">
        <h3>素材库</h3>
        <span>静态布局</span>
      </div>
      <div className="asset-grid">
        {samples.map((asset) => (
          <article className="asset-card" key={asset.name}>
            <div className="asset-thumb">
              <Image size={32} />
            </div>
            <div>
              <h4>{asset.name}</h4>
              <p>{asset.type}</p>
              <span>Quality {asset.score}/100</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function QualityPage() {
  const checks = ['图片格式', '图片尺寸', '命名规范', '分类目录', 'Prompt 记录'];

  return (
    <section className="panel">
      <div className="quality-summary">
        <ShieldCheck size={44} />
        <div>
          <h3>Asset Quality Inspector</h3>
          <p>后续 PR 将接入真实评分数据。</p>
        </div>
      </div>
      <div className="check-list">
        {checks.map((check) => (
          <div className="check-row" key={check}>
            <strong>{check}</strong>
            <span>待接入</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ExportPage() {
  return (
    <section className="panel export-panel">
      <Archive size={44} />
      <h3>素材包导出</h3>
      <p>后续 PR 将生成 `manifest.json` 并打包 zip 素材包。</p>
      <button className="primary-button" type="button">
        <Archive size={18} />
        后续 PR 接入导出
      </button>
    </section>
  );
}

export default App;
