import { useState } from 'react';

const views = [
  { id: 'generate', label: '素材生成' },
  { id: 'library', label: '素材库' },
  { id: 'quality', label: '质量报告' },
  { id: 'export', label: '导出交付' },
];

function App() {
  const [activeView, setActiveView] = useState('generate');

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
            <button
              key={view.id}
              className={activeView === view.id ? 'active' : ''}
              onClick={() => setActiveView(view.id)}
            >
              {view.label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <p>PR 2 前端基础界面</p>
          <h2>{views.find((view) => view.id === activeView)?.label}</h2>
        </header>

        <section className="placeholder-panel">
          <h3>{views.find((view) => view.id === activeView)?.label}</h3>
          <p>该页面将在后续 PR 中接入具体功能。</p>
        </section>
      </section>
    </main>
  );
}

export default App;
