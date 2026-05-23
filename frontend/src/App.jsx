import { useMemo, useState } from 'react';
import { Archive, FileJson, Image, Plus, Play, ShieldCheck, Trash2 } from 'lucide-react';

const views = [
  { id: 'generate', label: '素材生成', icon: Play },
  { id: 'library', label: '素材库', icon: Image },
  { id: 'quality', label: '质量报告', icon: ShieldCheck },
  { id: 'export', label: '导出交付', icon: Archive },
];

const assetTypes = ['character', 'enemy', 'item', 'tileset', 'ui', 'background'];
const gameTypes = ['platformer', 'rpg', 'roguelike', 'metroidvania'];
const styles = ['pixel_art', 'cartoon', 'dark_fantasy', 'cyberpunk'];

const defaultGenerationForm = {
  projectName: 'Cyber Bamboo Platformer',
  gameType: 'platformer',
  style: 'pixel_art',
  theme: 'cyber bamboo forest',
  description: '赛博竹林主题 2D 横版闯关游戏，需要主角、敌人、金币和地砖素材。',
  assets: [
    {
      type: 'character',
      name: 'hero',
      description: 'a brave cyber bamboo warrior',
      enabled: true,
    },
    {
      type: 'enemy',
      name: 'bamboo_slime',
      description: 'a small glowing slime monster',
      enabled: true,
    },
    {
      type: 'item',
      name: 'coin',
      description: 'a neon bamboo coin icon',
      enabled: true,
    },
    {
      type: 'tileset',
      name: 'ground_tile',
      description: 'cyber bamboo forest ground tile',
      enabled: true,
    },
  ],
};

function App() {
  const [activeView, setActiveView] = useState('generate');
  const currentView = views.find((v) => v.id === activeView) || views[0];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">GF</div>
          <div>
            <h1>GameAsset Forge</h1>
            <p>AI 2D Game Pipeline</p>
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

        <div className="sidebar-footer">
          <span className="status-badge online">MOCK</span>
          &nbsp; v0.1.0
        </div>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <p>// workspace</p>
          <h2>&gt; {currentView.label}</h2>
        </header>

        {activeView === 'generate' && <GeneratePage />}
        {activeView === 'library' && <LibraryPage />}
        {activeView === 'quality' && <QualityPage />}
        {activeView === 'export' && <ExportPage />}
      </section>
    </main>
  );
}

function NavButton({ view, active, onClick }) {
  const Icon = view.icon;
  return (
    <button className={active ? 'active' : ''} onClick={onClick}>
      <Icon size={14} />
      {view.label}
    </button>
  );
}

function GeneratePage() {
  const [form, setForm] = useState(defaultGenerationForm);
  const [submitState, setSubmitState] = useState('等待输入');

  const requestPreview = useMemo(() => buildGenerationRequest(form), [form]);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setSubmitState('请求预览已更新');
  }

  function updateAsset(index, field, value) {
    setForm((current) => ({
      ...current,
      assets: current.assets.map((asset, assetIndex) =>
        assetIndex === index ? { ...asset, [field]: value } : asset,
      ),
    }));
    setSubmitState('素材任务已更新');
  }

  function addAsset() {
    setForm((current) => ({
      ...current,
      assets: [
        ...current.assets,
        {
          type: 'item',
          name: 'new_asset',
          description: 'a game-ready 2D asset',
          enabled: true,
        },
      ],
    }));
    setSubmitState('已新增素材任务');
  }

  function removeAsset(index) {
    setForm((current) => ({
      ...current,
      assets: current.assets.filter((_, assetIndex) => assetIndex !== index),
    }));
    setSubmitState('已移除素材任务');
  }

  function handleSubmit(event) {
    event.preventDefault();
    setSubmitState(`已准备 ${requestPreview.assets.length} 个素材任务，后续 PR 接入 API`);
  }

  return (
    <div className="content-grid">
      <form className="panel" onSubmit={handleSubmit}>
        <div className="section-heading">
          <h3>生成任务</h3>
          <span>{submitState}</span>
        </div>
        <div className="field-grid">
          <label>
            项目名称
            <input
              value={form.projectName}
              onChange={(event) => updateField('projectName', event.target.value)}
            />
          </label>
          <label>
            游戏类型
            <select
              value={form.gameType}
              onChange={(event) => updateField('gameType', event.target.value)}
            >
              {gameTypes.map((gameType) => (
                <option key={gameType} value={gameType}>
                  {gameType}
                </option>
              ))}
            </select>
          </label>
          <label>
            视觉风格
            <select value={form.style} onChange={(event) => updateField('style', event.target.value)}>
              {styles.map((style) => (
                <option key={style} value={style}>
                  {style}
                </option>
              ))}
            </select>
          </label>
          <label>
            主题
            <input value={form.theme} onChange={(event) => updateField('theme', event.target.value)} />
          </label>
        </div>
        <label>
          描述
          <textarea
            value={form.description}
            onChange={(event) => updateField('description', event.target.value)}
          />
        </label>

        <div className="section-heading compact-heading">
          <h3>素材任务</h3>
          <button className="secondary-button" type="button" onClick={addAsset}>
            <Plus size={14} />
            ADD ASSET
          </button>
        </div>

        <div className="asset-form-list">
          {form.assets.map((asset, index) => (
            <div className="asset-form-row" key={`${asset.type}-${asset.name}-${index}`}>
              <label className="checkbox-label">
                启用
                <input
                  type="checkbox"
                  checked={asset.enabled}
                  onChange={(event) => updateAsset(index, 'enabled', event.target.checked)}
                />
              </label>
              <label>
                类型
                <select value={asset.type} onChange={(event) => updateAsset(index, 'type', event.target.value)}>
                  {assetTypes.map((assetType) => (
                    <option key={assetType} value={assetType}>
                      {assetType}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                名称
                <input value={asset.name} onChange={(event) => updateAsset(index, 'name', event.target.value)} />
              </label>
              <label>
                描述
                <input
                  value={asset.description}
                  onChange={(event) => updateAsset(index, 'description', event.target.value)}
                />
              </label>
              <button
                className="icon-button danger"
                type="button"
                onClick={() => removeAsset(index)}
                aria-label={`删除 ${asset.name}`}
                title="删除素材任务"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <button className="primary-button" type="submit">
          <Play size={14} />
          PREPARE REQUEST
        </button>
      </form>

      <section className="panel preview-panel">
        <div className="section-heading">
          <h3>Prompt Preview</h3>
          <FileJson size={14} />
        </div>
        <pre>{JSON.stringify(requestPreview, null, 2)}</pre>
      </section>
    </div>
  );
}

function buildGenerationRequest(form) {
  return {
    projectName: form.projectName,
    gameType: form.gameType,
    style: form.style,
    theme: form.theme,
    description: form.description,
    assets: form.assets
      .filter((asset) => asset.enabled)
      .map(({ type, name, description }) => ({ type, name, description })),
  };
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
        <span>{samples.length} ASSETS</span>
      </div>
      <div className="asset-grid">
        {samples.map((asset) => (
          <article className="asset-card" key={asset.name}>
            <div className="asset-thumb">
              <Image size={28} />
            </div>
            <div className="asset-card-info">
              <h4>{asset.name}</h4>
              <p>{asset.type}</p>
              <span className="score">QS {asset.score}/100</span>
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
        <ShieldCheck size={36} className="quality-icon" />
        <div>
          <h3>Quality Inspector</h3>
          <p>后续 PR 接入评分数据</p>
        </div>
      </div>
      <div className="check-list">
        {checks.map((check) => (
          <div className="check-row" key={check}>
            <strong>{check}</strong>
            <span>--/--</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ExportPage() {
  return (
    <section className="panel export-panel">
      <Archive size={36} className="export-icon" />
      <h3>素材包导出</h3>
      <p>生成 manifest.json 并打包 zip 素材包，后续 PR 接入。</p>
      <button className="primary-button" type="button">
        <Archive size={14} />
        EXPORT ZIP
      </button>
    </section>
  );
}

export default App;
