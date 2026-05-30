import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Archive,
  Bot,
  CheckCircle2,
  Cloud,
  Download,
  FileJson,
  Image,
  ImageOff,
  Loader2,
  Package,
  Paintbrush,
  Plus,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  XCircle,
} from 'lucide-react';
import {
  buildAssetPreviewUrl,
  exportGeneration,
  exportSelectedAssets,
  fetchAssets,
  fetchExportableGenerations,
  fetchQualityReport,
  generateAssets,
  regenerateBatch,
  summarizeGeneratedAssets,
  uploadGenerationToCloud,
} from './assetGeneration.js';
import { buildGenerationRequest, defaultGenerationForm } from './generationRequest.js';
import {
  applyImageConfigResponse,
  buildImageConfigPayload,
  defaultImageConfigForm,
  fetchImageConfig,
  imageGenProviders,
  imageGenQualities,
  imageGenSizes,
  openaiImageModels,
  saveImageConfig,
} from './imageConfig.js';
import {
  applyLlmConfigResponse,
  buildLlmConfigPayload,
  defaultLlmConfigForm,
  fetchLlmConfig,
  providerOptions,
  saveLlmConfig,
} from './llmConfig.js';
import {
  applyCloudConfigResponse,
  buildCloudConfigPayload,
  cloudProviders,
  defaultCloudConfigForm,
  fetchCloudConfig,
  saveCloudConfig,
} from './cloudConfig.js';
import {
  buildPromptCompileRequest,
  compilePrompt,
  pickInitialCandidate,
  promptModes,
  targetModels,
} from './promptCompiler.js';
import { getPresetsForType } from './secondaryPresets.js';

const views = [
  { id: 'generate', label: '素材生成', icon: Play },
  { id: 'regenerate', label: '二次生成', icon: RefreshCw },
  { id: 'config', label: 'LLM 配置', icon: Bot },
  { id: 'imageConfig', label: 'Image API 配置', icon: Paintbrush },
  { id: 'cloudConfig', label: '云存储配置', icon: Cloud },
  { id: 'library', label: '素材库', icon: Image },
  { id: 'quality', label: '质量报告', icon: ShieldCheck },
  { id: 'export', label: '导出交付', icon: Archive },
];

const assetTypes = ['character', 'enemy', 'item', 'tileset', 'ui', 'background'];
const assetTypeLabels = {
  character: '角色',
  enemy: '敌人',
  item: '物品',
  tileset: '地砖',
  ui: 'UI',
  background: '背景',
};
const gameTypeLabels = {
  '': '无',
  platformer: '横版闯关',
  rpg: '角色扮演',
  roguelike: 'Roguelike',
  metroidvania: '银河城',
};
const styleLabels = {
  '': '无',
  pixel_art: '像素风',
  cartoon: '卡通',
  dark_fantasy: '黑暗奇幻',
  cyberpunk: '赛博朋克',
};
const defaultGameType = 'platformer';
const defaultStyle = 'pixel_art';
const directionLabels = {
  quick_start: '快速起步',
  production_safe: '稳定生产',
  style_exploration: '风格探索',
  high_detail: '高细节展示',
};

const defaultPromptOptions = {
  mode: 'normal',
  targetModel: 'mock_seed',
};

const defaultCompileState = {
  loading: false,
  error: '',
  response: null,
  selectedCandidateId: '',
};

const defaultGenerationState = {
  loading: false,
  error: '',
  response: null,
};

function App() {
  const [activeView, setActiveView] = useState('generate');
  const [generationForm, setGenerationForm] = useState(defaultGenerationForm);
  const [submitState, setSubmitState] = useState('等待输入');
  const [promptOptions, setPromptOptions] = useState(defaultPromptOptions);
  const [compileState, setCompileState] = useState(defaultCompileState);
  const [assetGenerationState, setAssetGenerationState] = useState(defaultGenerationState);
  const [llmConfigForm, setLlmConfigForm] = useState(defaultLlmConfigForm);
  const [llmConfigStatus, setLlmConfigStatus] = useState('尚未读取后端配置');
  const [llmConfigLoading, setLlmConfigLoading] = useState(false);
  const [imageConfigForm, setImageConfigForm] = useState(defaultImageConfigForm);
  const [imageConfigStatus, setImageConfigStatus] = useState('尚未读取后端配置');
  const [imageConfigLoading, setImageConfigLoading] = useState(false);
  const [cloudConfigForm, setCloudConfigForm] = useState(defaultCloudConfigForm);
  const [cloudConfigStatus, setCloudConfigStatus] = useState('尚未读取后端配置');
  const [cloudConfigLoading, setCloudConfigLoading] = useState(false);
  const currentView = views.find((view) => view.id === activeView) || views[0];

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

        {activeView === 'generate' && (
          <GeneratePage
            form={generationForm}
            setForm={setGenerationForm}
            submitState={submitState}
            setSubmitState={setSubmitState}
            promptOptions={promptOptions}
            setPromptOptions={setPromptOptions}
            compileState={compileState}
            setCompileState={setCompileState}
            assetGenerationState={assetGenerationState}
            setAssetGenerationState={setAssetGenerationState}
          />
        )}
        {activeView === 'regenerate' && <RegeneratePage />}
        {activeView === 'config' && (
          <ConfigPage
            form={llmConfigForm}
            setForm={setLlmConfigForm}
            status={llmConfigStatus}
            setStatus={setLlmConfigStatus}
            loading={llmConfigLoading}
            setLoading={setLlmConfigLoading}
          />
        )}
        {activeView === 'imageConfig' && (
          <ImageConfigPage
            form={imageConfigForm}
            setForm={setImageConfigForm}
            status={imageConfigStatus}
            setStatus={setImageConfigStatus}
            loading={imageConfigLoading}
            setLoading={setImageConfigLoading}
          />
        )}
        {activeView === 'cloudConfig' && (
          <CloudConfigPage
            form={cloudConfigForm}
            setForm={setCloudConfigForm}
            status={cloudConfigStatus}
            setStatus={setCloudConfigStatus}
            loading={cloudConfigLoading}
            setLoading={setCloudConfigLoading}
          />
        )}
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

function GeneratePage({
  form,
  setForm,
  submitState,
  setSubmitState,
  promptOptions,
  setPromptOptions,
  compileState,
  setCompileState,
  assetGenerationState,
  setAssetGenerationState,
}) {
  const requestPreview = useMemo(
    () => buildGenerationRequest(form, promptOptions),
    [form, promptOptions],
  );
  const promptRequestPreview = useMemo(
    () => buildPromptCompileRequest(form, promptOptions),
    [form, promptOptions],
  );

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

  async function handleCompilePrompt() {
    setCompileState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const response = await compilePrompt(promptRequestPreview);
      setCompileState({
        loading: false,
        error: '',
        response,
        selectedCandidateId: pickInitialCandidate(response.candidates),
      });
      setSubmitState(`提示词已编译，返回 ${response.candidates.length} 套候选`);
    } catch (error) {
      setCompileState((current) => ({
        ...current,
        loading: false,
        error: error instanceof Error ? error.message : 'Prompt compile failed',
      }));
    }
  }

  async function handleGenerateAssets(event) {
    event.preventDefault();
    setAssetGenerationState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const response = await generateAssets(requestPreview);
      setAssetGenerationState({ loading: false, error: '', response });
      const errorCount = response.errors?.length || 0;
      const errorSuffix = errorCount > 0 ? `，${errorCount} 个失败` : '';
      setSubmitState(`已生成 ${response.assets.length} 个素材${errorSuffix}：${response.generationId}`);
    } catch (error) {
      setAssetGenerationState((current) => ({
        ...current,
        loading: false,
        error: error instanceof Error ? error.message : 'Asset generation failed',
      }));
    }
  }

  return (
    <div className="content-grid">
      <form className="panel" onSubmit={handleGenerateAssets}>
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
              {Object.keys(gameTypeLabels).map((key) => (
                <option key={key} value={key}>
                  {gameTypeLabels[key]}
                </option>
              ))}
            </select>
          </label>
          <label>
            视觉风格
            <select value={form.style} onChange={(event) => updateField('style', event.target.value)}>
              {Object.keys(styleLabels).map((key) => (
                <option key={key} value={key}>
                  {styleLabels[key]}
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
            <div className="asset-form-row" key={`asset-${index}`}>
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
                      {assetTypeLabels[assetType] || assetType}
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

        <div className="prompt-control-block">
          <div className="section-heading compact-heading">
            <h3>Prompt Compiler</h3>
            <Sparkles size={14} />
          </div>
          <div className="field-grid">
            <label>
              编译模式
              <select
                value={promptOptions.mode}
                onChange={(event) =>
                  setPromptOptions((current) => ({ ...current, mode: event.target.value }))
                }
              >
                {promptModes.map((mode) => (
                  <option key={mode.id} value={mode.id}>
                    {mode.label} / {mode.threshold}+
                  </option>
                ))}
              </select>
            </label>
            <label>
              目标模型
              <select
                value={promptOptions.targetModel}
                onChange={(event) =>
                  setPromptOptions((current) => ({ ...current, targetModel: event.target.value }))
                }
              >
                {targetModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="button-row">
            <button
              className="secondary-button"
              type="button"
              onClick={handleCompilePrompt}
              disabled={compileState.loading || promptRequestPreview.assets.length === 0}
            >
              <Sparkles size={14} />
              COMPILE PROMPT
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={handleCompilePrompt}
              disabled={compileState.loading || !compileState.response}
            >
              <RefreshCw size={14} />
              REGENERATE
            </button>
          </div>
          {compileState.error && <p className="error-line">{compileState.error}</p>}
        </div>

        <button
          className="primary-button"
          type="submit"
          disabled={assetGenerationState.loading || requestPreview.assets.length === 0}
        >
          <Play size={14} />
          GENERATE ASSETS
        </button>
        {assetGenerationState.error && <p className="error-line">{assetGenerationState.error}</p>}
      </form>

      <section className="panel preview-panel">
        <div className="section-heading">
          <h3>Request Preview</h3>
          <FileJson size={14} />
        </div>
        <pre>{JSON.stringify(requestPreview, null, 2)}</pre>
      </section>

      <GeneratedAssetsPanel state={assetGenerationState} />

      <PromptResultPanel
        response={compileState.response}
        loading={compileState.loading}
        selectedCandidateId={compileState.selectedCandidateId}
        onSelect={(candidateId) =>
          setCompileState((current) => ({ ...current, selectedCandidateId: candidateId }))
        }
      />
    </div>
  );
}

function GeneratedAssetsPanel({ state }) {
  const [lightbox, setLightbox] = useState(null);

  return (
    <section className="panel generated-results">
      <div className="section-heading">
        <h3>生成结果</h3>
        <span>{state.loading ? 'GENERATING' : summarizeGeneratedAssets(state.response)}</span>
      </div>
      {!state.response && !state.loading && (
        <div className="empty-state">点击 GENERATE ASSETS 后会写入本地 mock 素材并返回路径。</div>
      )}
      {state.loading && <div className="empty-state">正在串联 Prompt Compiler、Mock Provider 和素材仓库。</div>}
      {state.response && (
        <div className="generated-grid">
          {state.response.assets.map((asset) => (
            <article className="generated-card" key={asset.id}>
              <div
                className="generated-thumb"
                onClick={() => setLightbox({ url: buildAssetPreviewUrl(asset.localPath), name: asset.assetName, type: asset.assetType, provider: asset.provider, prompt: asset.finalPrompt })}
              >
                <img src={buildAssetPreviewUrl(asset.localPath)} alt={`${asset.assetName} preview`} />
              </div>
              <div className="generated-card-head">
                <CheckCircle2 size={16} />
                <strong>{asset.assetName}</strong>
                <span>{assetTypeLabels[asset.assetType] || asset.assetType}</span>
              </div>
              <p>{asset.localPath}</p>
              <small>
                {asset.provider} / {asset.providerMetadata.promptHash}
              </small>
              <pre>{asset.finalPrompt}</pre>
            </article>
          ))}
          {state.response.errors?.length > 0 && (
            <div className="empty-state" style={{ color: '#e06c75', gridColumn: '1 / -1', border: '1px solid #e06c7544', borderRadius: 6, padding: 12, marginTop: 8 }}>
              <strong>生成失败的素材：</strong>
              {state.response.errors.map((err, i) => (
                <div key={i} style={{ marginTop: 4 }}>{err}</div>
              ))}
            </div>
          )}
        </div>
      )}
      {lightbox && (
        <div className="lightbox-backdrop" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>X</button>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <img src={lightbox.url} alt={lightbox.name} />
            <div className="lightbox-info">
              <strong>{lightbox.name}</strong>
              <span>{lightbox.type}</span>
              <span>{lightbox.provider}</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function PromptResultPanel({ response, loading, selectedCandidateId, onSelect }) {
  if (loading) {
    return (
      <section className="panel prompt-results">
        <div className="section-heading">
          <h3>候选提示词</h3>
          <span>COMPILING</span>
        </div>
      </section>
    );
  }

  if (!response) {
    return (
      <section className="panel prompt-results">
        <div className="section-heading">
          <h3>候选提示词</h3>
          <span>WAITING</span>
        </div>
        <div className="empty-state">选择模式和目标模型后，可以先编译提示词，也可以直接生成素材。</div>
      </section>
    );
  }

  return (
    <section className="panel prompt-results">
      <div className="section-heading">
        <h3>候选提示词</h3>
        <span>
          {response.provider} / {response.fallback ? 'FALLBACK' : 'LLM'}
        </span>
      </div>
      <div className="candidate-list">
        {response.candidates.map((candidate) => (
          <article
            className={`candidate-card ${selectedCandidateId === candidate.id ? 'selected' : ''}`}
            key={candidate.id}
          >
            <button className="candidate-head" type="button" onClick={() => onSelect(candidate.id)}>
              <span>{directionLabels[candidate.direction] || candidate.direction}</span>
              <strong>{candidate.score}/100</strong>
            </button>
            <TagGrid tags={candidate.tags} />
            {candidate.assets.map((asset) => (
              <div className="prompt-asset" key={`${candidate.id}-${asset.assetName}`}>
                <h4>
                  {asset.assetName} <span>{assetTypeLabels[asset.assetType] || asset.assetType}</span>
                </h4>
                <pre>{asset.finalPrompt}</pre>
                {asset.negativePrompt && (
                  <p>
                    <strong>Negative:</strong> {asset.negativePrompt}
                  </p>
                )}
              </div>
            ))}
            {candidate.warnings.map((warning) => (
              <p className="warning-line" key={warning}>
                {warning}
              </p>
            ))}
          </article>
        ))}
      </div>
    </section>
  );
}

function TagGrid({ tags }) {
  return (
    <div className="tag-grid">
      {Object.entries(tags).map(([group, values]) => (
        <div className="tag-group" key={group}>
          <strong>{group}</strong>
          <p>{values.join(', ') || '-'}</p>
        </div>
      ))}
    </div>
  );
}

function ConfigPage({ form, setForm, status, setStatus, loading, setLoading }) {
  async function loadConfig() {
    setLoading(true);
    setStatus('正在读取配置');
    try {
      const response = await fetchLlmConfig();
      setForm((current) => ({ ...current, ...applyLlmConfigResponse(response) }));
      setStatus(response.hasApiKey ? '后端已有 API Key' : '后端暂无 API Key');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '读取配置失败');
    } finally {
      setLoading(false);
    }
  }

  async function saveConfig(event) {
    event.preventDefault();
    setLoading(true);
    setStatus('正在保存配置');
    try {
      const response = await saveLlmConfig(buildLlmConfigPayload(form));
      setForm((current) => ({ ...current, ...applyLlmConfigResponse(response) }));
      setStatus(response.hasApiKey ? '配置已保存，LLM 已启用' : '配置已保存，将使用规则降级');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '保存配置失败');
    } finally {
      setLoading(false);
    }
  }

  function updateConfig(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <section className="panel config-panel">
      <div className="section-heading">
        <h3>LLM 配置</h3>
        <span>{status}</span>
      </div>
      <form onSubmit={saveConfig}>
        <div className="field-grid">
          <label>
            Provider
            <select
              value={form.provider}
              onChange={(event) => updateConfig('provider', event.target.value)}
            >
              {providerOptions.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Base URL
            <input
              value={form.baseUrl}
              onChange={(event) => updateConfig('baseUrl', event.target.value)}
              placeholder="https://api.openai.com/v1"
            />
          </label>
          <label>
            文本模型
            <input
              value={form.promptModel}
              onChange={(event) => updateConfig('promptModel', event.target.value)}
              placeholder="gpt-5-mini"
            />
          </label>
        </div>
        <label>
          OpenAI API Key
          <input
            type="password"
            value={form.apiKey}
            onChange={(event) => updateConfig('apiKey', event.target.value)}
            placeholder={form.hasApiKey ? '后端已有 Key，留空表示不修改' : '输入 sk-...'}
          />
        </label>
        <label className="inline-checkbox">
          <input
            type="checkbox"
            checked={form.clearApiKey}
            onChange={(event) => updateConfig('clearApiKey', event.target.checked)}
          />
          清空当前 API Key
        </label>
        <div className="config-status-grid">
          <div>
            <strong>Provider</strong>
            <span>{form.provider}</span>
          </div>
          <div>
            <strong>Base URL</strong>
            <span>{form.baseUrl || 'https://api.openai.com/v1'}</span>
          </div>
          <div>
            <strong>Model</strong>
            <span>{form.promptModel || 'gpt-5-mini'}</span>
          </div>
          <div>
            <strong>Key</strong>
            <span>{form.hasApiKey ? '已配置' : '未配置'}</span>
          </div>
        </div>
        <div className="button-row">
          <button className="primary-button" type="submit" disabled={loading}>
            <Bot size={14} />
            SAVE CONFIG
          </button>
          <button className="secondary-button" type="button" onClick={loadConfig} disabled={loading}>
            <RefreshCw size={14} />
            LOAD CONFIG
          </button>
        </div>
      </form>
    </section>
  );
}

function ImageConfigPage({ form, setForm, status, setStatus, loading, setLoading }) {
  async function loadConfig() {
    setLoading(true);
    setStatus('正在读取配置');
    try {
      const response = await fetchImageConfig();
      setForm((current) => ({ ...current, ...applyImageConfigResponse(response) }));
      setStatus(response.hasApiKey ? '后端已配置 API Key/Token' : '后端暂无 API Key/Token');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '读取配置失败');
    } finally {
      setLoading(false);
    }
  }

  async function saveConfig(event) {
    event.preventDefault();
    setLoading(true);
    setStatus('正在保存配置');
    try {
      const response = await saveImageConfig(buildImageConfigPayload(form));
      setForm((current) => ({ ...current, ...applyImageConfigResponse(response) }));
      setStatus(response.hasApiKey ? '配置已保存，真实生图已就绪' : '配置已保存，将使用 Mock 降级');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '保存配置失败');
    } finally {
      setLoading(false);
    }
  }

  function updateConfig(field, value) {
    setForm((current) => {
      const next = { ...current, [field]: value };
      // Auto-switch model when provider changes
      if (field === 'provider') {
        next.imageModel = 'gpt-image-2';
        next.baseUrl = 'https://api.openai.com/v1';
      }
      return next;
    });
  }

  const isDallE = form.imageModel.startsWith('dall-e');
  const modelOptions = openaiImageModels;

  return (
    <section className="panel config-panel">
      <div className="section-heading">
        <h3>Image API 配置</h3>
        <span>{status}</span>
      </div>
      <form onSubmit={saveConfig}>
        <div className="field-grid">
          <label>
            生图 Provider
            <select
              value={form.provider}
              onChange={(event) => updateConfig('provider', event.target.value)}
            >
              {imageGenProviders.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            API Endpoint
            <input
              value={form.baseUrl}
              onChange={(event) => updateConfig('baseUrl', event.target.value)}
              placeholder="https://api.openai.com/v1"
            />
          </label>
          <label>
            图片模型
            <select
              value={form.imageModel}
              onChange={(event) => updateConfig('imageModel', event.target.value)}
            >
              {modelOptions.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            输出尺寸
            <select
              value={form.imageSize}
              onChange={(event) => updateConfig('imageSize', event.target.value)}
            >
              {imageGenSizes.map((size) => (
                <option key={size.id} value={size.id}>
                  {size.label}
                </option>
              ))}
            </select>
          </label>
          {isDallE && (
            <label>
              画质
              <select
                value={form.imageQuality}
                onChange={(event) => updateConfig('imageQuality', event.target.value)}
              >
                {imageGenQualities.map((quality) => (
                  <option key={quality.id} value={quality.id}>
                    {quality.label}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        <label>
          OpenAI API Key
          <input
            type="password"
            value={form.apiKey}
            onChange={(event) => updateConfig('apiKey', event.target.value)}
            placeholder={
              form.hasApiKey
                ? '后端已有 Key，留空表示不修改'
                : '输入 sk-...'
            }
          />
        </label>

        <label className="inline-checkbox">
          <input
            type="checkbox"
            checked={form.clearApiKey}
            onChange={(event) => updateConfig('clearApiKey', event.target.checked)}
          />
          清空当前 API Key / Token
        </label>

        <label>
          HTTP 代理（可选）
          <input
            value={form.proxyUrl}
            onChange={(event) => updateConfig('proxyUrl', event.target.value)}
            placeholder="http://127.0.0.1:7890 或 socks5://127.0.0.1:1080"
          />
        </label>
        {form.proxyUrl && (
          <label className="inline-checkbox">
            <input
              type="checkbox"
              checked={form.clearProxy}
              onChange={(event) => updateConfig('clearProxy', event.target.checked)}
            />
            清空代理设置
          </label>
        )}

        <div className="image-config-hint">
          <h4>
            <Paintbrush size={12} />
            OpenAI 图像生成使用说明
          </h4>
          <ul>
            <li>需要 <code>sk-...</code> 格式的 OpenAI API Key，需开通图像生成使用权限</li>
            <li>GPT Image 2 是最新模型，DALL-E 3/2 为旧版</li>
            <li>GPT Image 2 支持 1024×1024、1024×1536、1536×1024 等多种尺寸</li>
            <li>无 Key 时自动降级为 Mock Provider</li>
          </ul>
        </div>

        <div className="config-status-grid">
          <div>
            <strong>Provider</strong>
            <span>OpenAI</span>
          </div>
          <div>
            <strong>Model</strong>
            <span>{form.imageModel}</span>
          </div>
          <div>
            <strong>Size</strong>
            <span>{form.imageSize}</span>
          </div>
          <div>
            <strong>Key/Token</strong>
            <span>{form.hasApiKey ? '已配置' : '未配置'}</span>
          </div>
        </div>

        <div className="button-row">
          <button className="primary-button" type="submit" disabled={loading}>
            <Paintbrush size={14} />
            SAVE CONFIG
          </button>
          <button className="secondary-button" type="button" onClick={loadConfig} disabled={loading}>
            <RefreshCw size={14} />
            LOAD CONFIG
          </button>
        </div>
      </form>
    </section>
  );
}

function CloudConfigPage({ form, setForm, status, setStatus, loading, setLoading }) {
  async function loadConfig() {
    setLoading(true);
    setStatus('正在读取配置');
    try {
      const response = await fetchCloudConfig();
      setForm((current) => ({ ...current, ...applyCloudConfigResponse(response) }));
      setStatus(response.hasCredentials ? '后端已配置云存储凭证' : '后端暂无云存储凭证，使用 Mock');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '读取配置失败');
    } finally {
      setLoading(false);
    }
  }

  async function saveConfig(event) {
    event.preventDefault();
    setLoading(true);
    setStatus('正在保存配置');
    try {
      const response = await saveCloudConfig(buildCloudConfigPayload(form));
      setForm((current) => ({ ...current, ...applyCloudConfigResponse(response) }));
      setStatus(response.hasCredentials ? '配置已保存，云上传已就绪' : '配置已保存，将使用 Mock 降级');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '保存配置失败');
    } finally {
      setLoading(false);
    }
  }

  function updateConfig(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  const isQiniu = form.provider === 'qiniu';

  return (
    <section className="panel config-panel">
      <div className="section-heading">
        <h3>云存储配置</h3>
        <span>{status}</span>
      </div>
      <form onSubmit={saveConfig}>
        <div className="field-grid">
          <label>
            云存储 Provider
            <select
              value={form.provider}
              onChange={(event) => updateConfig('provider', event.target.value)}
            >
              {cloudProviders.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {isQiniu && (
          <>
            <label>
              Access Key
              <input
                value={form.accessKey}
                onChange={(event) => updateConfig('accessKey', event.target.value)}
                placeholder={form.hasCredentials ? '后端已有 Key，留空表示不修改' : '输入七牛云 Access Key'}
              />
            </label>
            <label>
              Secret Key
              <input
                type="password"
                value={form.secretKey}
                onChange={(event) => updateConfig('secretKey', event.target.value)}
                placeholder={form.hasCredentials ? '后端已有 Key，留空表示不修改' : '输入七牛云 Secret Key'}
              />
            </label>
            <label>
              Bucket 名称
              <input
                value={form.bucket}
                onChange={(event) => updateConfig('bucket', event.target.value)}
                placeholder="例如：my-game-assets"
              />
            </label>
            <label>
              CDN 加速域名（可选）
              <input
                value={form.domain}
                onChange={(event) => updateConfig('domain', event.target.value)}
                placeholder="例如：https://cdn.example.com"
              />
            </label>

            {form.hasCredentials && (
              <label className="inline-checkbox">
                <input
                  type="checkbox"
                  checked={form.clearCredentials}
                  onChange={(event) => updateConfig('clearCredentials', event.target.checked)}
                />
                清空当前凭证
              </label>
            )}
          </>
        )}

        {isQiniu && (
          <div className="image-config-hint">
            <h4>
              <Cloud size={12} />
              七牛云 Kodo 使用说明
            </h4>
            <ul>
              <li>需要注册七牛云账号并开通对象存储 Kodo 服务</li>
              <li>在七牛云控制台获取 <code>Access Key</code> 和 <code>Secret Key</code></li>
              <li>CDN 域名可选，不配置则使用七牛云 30 天测试域名自动生成</li>
              <li>上传后素材 public URL 将持久化到素材记录中</li>
            </ul>
          </div>
        )}

        <div className="config-status-grid">
          <div>
            <strong>Provider</strong>
            <span>{form.provider === 'qiniu' ? '七牛云 Kodo' : 'Mock 模拟'}</span>
          </div>
          {isQiniu && (
            <>
              <div>
                <strong>Bucket</strong>
                <span>{form.bucket || '未设置'}</span>
              </div>
              <div>
                <strong>域名</strong>
                <span>{form.domain || '自动生成测试域名'}</span>
              </div>
            </>
          )}
          <div>
            <strong>凭证</strong>
            <span>{form.hasCredentials ? '已配置' : '未配置'}</span>
          </div>
        </div>

        <div className="button-row">
          <button className="primary-button" type="submit" disabled={loading}>
            <Cloud size={14} />
            SAVE CONFIG
          </button>
          <button className="secondary-button" type="button" onClick={loadConfig} disabled={loading}>
            <RefreshCw size={14} />
            LOAD CONFIG
          </button>
        </div>
      </form>
    </section>
  );
}

function LibraryPage() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('');
  const [lightbox, setLightbox] = useState(null);

  async function loadAssets(selectedCategory) {
    setLoading(true);
    setError('');
    try {
      const data = await fetchAssets(selectedCategory || undefined);
      setAssets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assets');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAssets(category);
  }, [category]);

  const categoryCounts = assets.reduce(
    (counts, asset) => {
      counts[asset.assetType] = (counts[asset.assetType] || 0) + 1;
      return counts;
    },
    { all: assets.length },
  );

  const filterButtons = [
    { id: '', label: '全部', icon: Image },
    ...assetTypes.map((type) => ({
      id: type,
      label: type,
      icon: Image,
    })),
  ];

  return (
    <section className="panel library-panel">
      <div className="section-heading">
        <h3>素材库</h3>
        <span>
          {loading ? 'LOADING' : `${assets.length} ASSETS`}
        </span>
      </div>

      <div className="library-filter-bar">
        {filterButtons.map((btn) => (
          <button
            key={btn.id}
            className={`filter-chip ${category === btn.id ? 'active' : ''}`}
            type="button"
            onClick={() => setCategory(btn.id)}
          >
            <btn.icon size={12} />
            {btn.label}
            {categoryCounts[btn.id] !== undefined && (
              <span className="filter-count">{categoryCounts[btn.id]}</span>
            )}
          </button>
        ))}
        <button
          className="secondary-button"
          type="button"
          onClick={() => loadAssets(category)}
          disabled={loading}
        >
          <RefreshCw size={14} />
          REFRESH
        </button>
      </div>

      {loading && (
        <div className="empty-state">
          <Loader2 size={28} />
          正在从素材仓库加载...
        </div>
      )}

      {error && !loading && (
        <div className="empty-state">
          <p className="error-line">{error}</p>
        </div>
      )}

      {!loading && !error && assets.length === 0 && (
        <div className="empty-state">
          <ImageOff size={28} />
          {category
            ? `暂无 "${category}" 类型的素材，请先生成素材。`
            : '素材库为空，请先在生成页创建素材。'}
        </div>
      )}

      {!loading && !error && assets.length > 0 && (
        <div className="asset-grid">
          {assets.map((asset) => (
            <article className="asset-card" key={asset.id}>
              <div
                className="asset-thumb"
                onClick={() => asset.localPath && setLightbox({ url: buildAssetPreviewUrl(asset.localPath), name: asset.assetName, type: asset.assetType, provider: asset.provider })}
              >
                {asset.localPath ? (
                  <img
                    src={buildAssetPreviewUrl(asset.localPath)}
                    alt={`${asset.assetName} preview`}
                  />
                ) : (
                  <Image size={28} />
                )}
              </div>
              <div className="asset-card-info">
                <h4>{asset.assetName}</h4>
                <p>{assetTypeLabels[asset.assetType] || asset.assetType}</p>
                <span className="score">
                  QS {asset.qualityScore != null ? `${asset.qualityScore}/100` : '--'}
                </span>
                <small className="asset-gen-id">{asset.generationId}</small>
                <small className="asset-provider">{asset.provider}</small>
              </div>
            </article>
          ))}
        </div>
      )}
      {lightbox && (
        <div className="lightbox-backdrop" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>X</button>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <img src={lightbox.url} alt={lightbox.name} />
            <div className="lightbox-info">
              <strong>{lightbox.name}</strong>
              <span>{lightbox.type}</span>
              <span>{lightbox.provider}</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function QualityPage() {
  const [generationId, setGenerationId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState(null);
  const [generationIds, setGenerationIds] = useState([]);
  const [loadingIds, setLoadingIds] = useState(true);

  useEffect(() => {
    async function loadIds() {
      try {
        const assets = await fetchAssets();
        const ids = [...new Set(assets.map((a) => a.generationId))];
        setGenerationIds(ids);
        if (ids.length > 0 && !generationId) {
          setGenerationId(ids[0]);
        }
      } catch {
        // 素材库不可用时静默处理
      } finally {
        setLoadingIds(false);
      }
    }
    loadIds();
  }, []);

  async function handleInspect(event) {
    event.preventDefault();
    if (!generationId.trim()) return;
    setLoading(true);
    setError('');
    setReport(null);
    try {
      const data = await fetchQualityReport(generationId.trim());
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '质量检查失败');
    } finally {
      setLoading(false);
    }
  }

  function scoreColor(score) {
    if (score >= 80) return 'var(--accent)';
    if (score >= 60) return 'var(--accent-yellow)';
    return 'var(--accent-red)';
  }

  function normalizeDimensions(assetReport) {
    return (assetReport.dimensions || assetReport.checks || []).map((dimension) => ({
      name: dimension.name,
      label: dimension.label,
      passed: dimension.passed,
      dimensionScore: dimension.dimensionScore ?? dimension.score ?? 0,
      weightPct: dimension.weightPct ?? dimension.weight ?? 0,
      weightedScore: dimension.weightedScore ?? 0,
      passedCount: dimension.passedCount ?? 0,
      totalCount: dimension.totalCount ?? (dimension.subChecks || dimension.criteria || []).length,
      subChecks: (dimension.subChecks || dimension.criteria || []).map((subCheck) => ({
        name: subCheck.name || subCheck.label,
        label: subCheck.label,
        passed: subCheck.passed,
        message: subCheck.message,
        deductionPct: subCheck.deductionPct ?? subCheck.deduction ?? 0,
        optimizationHint: subCheck.optimizationHint || subCheck.suggestion || '',
      })),
    }));
  }

  return (
    <section className="panel quality-panel">
      <div className="section-heading">
        <h3>质量检查器</h3>
        <span>{report ? `报告就绪` : '待检查'}</span>
      </div>

      <form className="quality-form" onSubmit={handleInspect}>
        <label>
          生成任务 ID
          <div className="quality-input-row">
            {generationIds.length > 0 ? (
              <select
                value={generationId}
                onChange={(e) => setGenerationId(e.target.value)}
              >
                {generationIds.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            ) : (
              <input
                value={generationId}
                onChange={(e) => setGenerationId(e.target.value)}
                placeholder="输入 generation ID，例如 gen_abc123..."
              />
            )}
            <button className="primary-button" type="submit" disabled={loading || !generationId.trim()}>
              <ShieldCheck size={14} />
              开始检查
            </button>
          </div>
        </label>
        {loadingIds && <small>正在加载已有的 generation 列表...</small>}
      </form>

      {loading && (
        <div className="empty-state">
          <Loader2 size={28} />
          正在执行质量检查...
        </div>
      )}

      {error && !loading && (
        <div className="empty-state">
          <XCircle size={28} color="var(--accent-red)" />
          <p className="error-line">{error}</p>
        </div>
      )}

      {!loading && !error && !report && (
        <div className="empty-state">
          <ShieldCheck size={28} />
          选择一个生成任务 ID 并点击“开始检查”。
        </div>
      )}

      {report && report.assetCount === 0 && (
        <div className="empty-state">
          <AlertTriangle size={28} color="var(--accent-yellow)" />
          该 generation 下没有找到素材记录。
        </div>
      )}

      {report && report.assetCount > 0 && (
        <div className="quality-report-body">
          {/* 总览卡片 */}
          <div className="quality-overview">
            <div className="quality-score-ring" style={{ borderColor: scoreColor(report.overallScore) }}>
              <span className="quality-score-num" style={{ color: scoreColor(report.overallScore) }}>
                {report.overallScore}
              </span>
              <span className="quality-score-label">/ {report.maxScore}</span>
            </div>
            <div className="quality-stats">
              <div className="quality-stat">
                <strong>{report.assetCount}</strong>
                <span>素材总数</span>
              </div>
              <div className="quality-stat pass">
                <strong>{report.passCount}</strong>
                <span>通过 (≥60)</span>
              </div>
              <div className="quality-stat fail">
                <strong>{report.failCount}</strong>
                <span>未通过 (&lt;60)</span>
              </div>
            </div>
          </div>

          {/* 每个素材的报告 */}
          {report.assets.map((assetReport) => (
            <div className="quality-asset-card" key={assetReport.assetId}>
              <div className="quality-asset-head">
                <span className="quality-asset-score" style={{ color: scoreColor(assetReport.totalScore) }}>
                  {assetReport.totalScore}/100
                </span>
                <strong>{assetReport.assetName}</strong>
                <span className="quality-asset-type">{assetTypeLabels[assetReport.assetType] || assetReport.assetType}</span>
                <span className="quality-asset-type">{assetReport.grade}</span>
              </div>
              <div className="quality-checks">
                {normalizeDimensions(assetReport).map((check) => (
                  <div
                    className={`quality-check-row ${check.passed ? 'passed' : 'failed'}`}
                    key={check.name}
                  >
                    <span className="quality-check-icon">
                      {check.passed ? (
                        <CheckCircle2 size={16} />
                      ) : (
                        <XCircle size={16} />
                      )}
                    </span>
                    <div className="quality-check-info">
                      <strong>
                        {check.label} · {check.dimensionScore}/100 · 权重 {check.weightPct}%
                      </strong>
                      <p>加权得分：{check.weightedScore}，通过 {check.passedCount}/{check.totalCount} 个检查点</p>
                      <ul className="quality-criteria">
                        {check.subChecks.map((subCheck) => (
                          <li className={subCheck.passed ? 'passed' : 'failed'} key={subCheck.name}>
                            <span>{subCheck.passed ? '通过' : `扣 ${subCheck.deductionPct}%`}</span>
                            <div>
                              <strong>{subCheck.label}</strong>
                              <p>{subCheck.message}</p>
                              {!subCheck.passed && subCheck.optimizationHint && (
                                <small>优化建议：{subCheck.optimizationHint}</small>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <span className="quality-check-deduction">
                      {check.weightedScore}
                    </span>
                  </div>
                ))}
              </div>
              {assetReport.overallHint && (
                <p className="quality-check-tip">{assetReport.overallHint}</p>
              )}
              {assetReport.promptOptimizationTips?.length > 0 && (
                <div className="quality-tips">
                  <strong>提示词优化建议</strong>
                  <ul>
                    {assetReport.promptOptimizationTips.map((tip) => (
                      <li key={tip}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function ExportPage() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);

  async function loadAssets() {
    setLoading(true);
    setError('');
    try {
      const data = await fetchAssets();
      setAssets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAssets();
  }, []);

  function toggleAsset(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectAll() {
    setSelectedIds(new Set(assets.map((a) => a.id)));
  }

  function deselectAll() {
    setSelectedIds(new Set());
  }

  async function handleExport() {
    if (selectedIds.size === 0) return;
    setExporting(true);
    setError('');
    setExportResult(null);
    try {
      const result = await exportSelectedAssets([...selectedIds]);
      setExportResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '导出失败');
    } finally {
      setExporting(false);
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const assetsByType = {};
  assets.forEach((a) => {
    if (!assetsByType[a.assetType]) assetsByType[a.assetType] = [];
    assetsByType[a.assetType].push(a);
  });

  return (
    <section className="panel export-panel">
      <div className="section-heading">
        <h3>素材包导出</h3>
        <span>{loading ? 'LOADING' : `${assets.length} ASSETS / ${selectedIds.size} SELECTED`}</span>
      </div>

      {loading && (
        <div className="empty-state">
          <Loader2 size={28} />
          正在从素材仓库读取素材列表...
        </div>
      )}

      {error && !loading && (
        <div className="empty-state">
          <p className="error-line">{error}</p>
          <button className="secondary-button" type="button" onClick={loadAssets}>
            <RefreshCw size={14} />
            RETRY
          </button>
        </div>
      )}

      {!loading && !error && assets.length === 0 && (
        <div className="empty-state">
          <Package size={28} />
          暂无素材记录。请先在生成页创建素材，然后返回导出。
        </div>
      )}

      {!loading && !error && assets.length > 0 && (
        <>
          <div className="button-row">
            <button className="secondary-button" type="button" onClick={selectAll}>
              全选
            </button>
            <button className="secondary-button" type="button" onClick={deselectAll}>
              取消全选
            </button>
            <button className="secondary-button" type="button" onClick={loadAssets} disabled={loading}>
              <RefreshCw size={14} />
              刷新
            </button>
          </div>

          <div className="export-asset-list">
            {Object.keys(assetsByType).map((type) => (
              <div key={type} className="export-type-group">
                <h4 className="export-type-head">
                  {assetTypeLabels[type] || type}
                  <span>{assetsByType[type].length} 个</span>
                </h4>
                {assetsByType[type].map((asset) => (
                  <label key={asset.id} className="export-asset-row">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(asset.id)}
                      onChange={() => toggleAsset(asset.id)}
                    />
                    <div className="export-asset-thumb">
                      {asset.localPath ? (
                        <img src={buildAssetPreviewUrl(asset.localPath)} alt={asset.assetName} />
                      ) : (
                        <Image size={20} />
                      )}
                    </div>
                    <span className="export-asset-name">{asset.assetName}</span>
                    <small className="export-asset-gen">{asset.generationId}</small>
                  </label>
                ))}
              </div>
            ))}
          </div>

          <button
            className="primary-button"
            type="button"
            onClick={handleExport}
            disabled={exporting || selectedIds.size === 0}
            style={{ marginTop: 16 }}
          >
            {exporting ? (
              <>
                <Loader2 size={14} />
                EXPORTING
              </>
            ) : (
              <>
                <Download size={14} />
                导出选中素材 ({selectedIds.size})
              </>
            )}
          </button>

          {exportResult && (
            <div className="export-result" style={{ marginTop: 16 }}>
              <div className="export-result-icon">
                <CheckCircle2 size={32} />
              </div>
              <div className="export-result-info">
                <h4>导出成功</h4>
                <p>已下载包含 {exportResult.assetCount} 个素材的 zip 包</p>
                <div className="export-stats">
                  <span>
                    <FileJson size={12} />
                    {exportResult.assetCount} 个素材
                  </span>
                  <span>
                    <Package size={12} />
                    总计 {formatSize(exportResult.totalSize)}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="export-hint" style={{ marginTop: 16 }}>
            <h4>导出内容说明</h4>
            <p>
              zip 包内含 <code>manifest.json</code> 元数据清单和按类型分目录的 PNG
              素材文件。manifest 中包含素材名称、类型、风格、提示词、质量评分等信息，可直接交付给游戏引擎或后续管线使用。
            </p>
          </div>
        </>
      )}
    </section>
  );
}

function RegeneratePage() {
  const [assets, setAssets] = useState([]);
  const [loadingAssets, setLoadingAssets] = useState(true);
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [checkedActions, setCheckedActions] = useState({});
  const [customPrompt, setCustomPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState([]);
  const [lightbox, setLightbox] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchAssets();
        setAssets(data);
        if (data.length > 0 && !selectedAssetId) {
          setSelectedAssetId(data[0].id);
        }
      } catch {
        // ignore
      } finally {
        setLoadingAssets(false);
      }
    }
    load();
  }, []);

  const selectedAsset = assets.find((a) => a.id === selectedAssetId);
  const presets = selectedAsset ? getPresetsForType(selectedAsset.assetType) : [];

  useEffect(() => {
    const initial = {};
    presets.forEach((p) => {
      initial[p.action] = true;
    });
    setCheckedActions(initial);
  }, [selectedAssetId]);

  function toggleAction(action) {
    setCheckedActions((prev) => ({ ...prev, [action]: !prev[action] }));
  }

  async function handleBatchGenerate() {
    const actions = Object.entries(checkedActions)
      .filter(([, checked]) => checked)
      .map(([action]) => action);
    if (actions.length === 0) {
      setError('请至少选择一个动作。');
      return;
    }
    setGenerating(true);
    setError('');
    setResults([]);
    try {
      const data = await regenerateBatch(selectedAssetId, actions, customPrompt || null);
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Batch regeneration failed');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="content-grid">
      <section className="panel regenerate-page">
        <div className="section-heading">
          <h3>选择原型素材</h3>
          <span>{loadingAssets ? 'LOADING' : `${assets.length} ASSETS`}</span>
        </div>

        {loadingAssets ? (
          <div className="empty-state">
            <Loader2 size={28} />
            正在加载素材库...
          </div>
        ) : assets.length === 0 ? (
          <div className="empty-state">
            <ImageOff size={28} />
            素材库为空，请先在生成页创建素材。
          </div>
        ) : (
          <>
            <label>
              原型素材
              <select
                value={selectedAssetId}
                onChange={(e) => {
                  setSelectedAssetId(e.target.value);
                  setResults([]);
                  setError('');
                }}
              >
                {assets.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    [{assetTypeLabels[asset.assetType] || asset.assetType}] {asset.assetName} — {asset.style}
                  </option>
                ))}
              </select>
            </label>

            {selectedAsset && (
              <div className="prototype-preview">
                <div className="prototype-thumb">
                  {selectedAsset.localPath ? (
                    <img
                      src={buildAssetPreviewUrl(selectedAsset.localPath)}
                      alt={selectedAsset.assetName}
                    />
                  ) : (
                    <Image size={40} />
                  )}
                </div>
                <div className="prototype-info">
                  <strong>{selectedAsset.assetName}</strong>
                  <span>{assetTypeLabels[selectedAsset.assetType] || selectedAsset.assetType}</span>
                  <span>{selectedAsset.style} / {selectedAsset.theme}</span>
                  <small>{selectedAsset.provider}</small>
                </div>
              </div>
            )}

            <div className="section-heading compact-heading">
              <h3>动作预设</h3>
              <span>{presets.length} 个可选</span>
            </div>

            {presets.length === 0 ? (
              <div className="empty-state">该素材类型暂不支持二次生成。</div>
            ) : (
              <div className="action-checkboxes">
                {presets.map((p) => (
                  <label key={p.action} className="action-checkbox">
                    <input
                      type="checkbox"
                      checked={checkedActions[p.action] || false}
                      onChange={() => toggleAction(p.action)}
                    />
                    <span>
                      <strong>{p.label}</strong>
                      <small>{p.promptHint}</small>
                    </span>
                  </label>
                ))}
              </div>
            )}

            <label style={{ marginTop: 16 }}>
              自定义提示词（可选，应用于所有选中动作）
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="输入额外的提示词要求..."
                rows={3}
              />
            </label>

            {error && <p className="error-line">{error}</p>}

            <button
              className="primary-button"
              type="button"
              onClick={handleBatchGenerate}
              disabled={generating || presets.length === 0}
              style={{ marginTop: 12 }}
            >
              {generating ? (
                <>
                  <Loader2 size={14} />
                  GENERATING
                </>
              ) : (
                <>
                  <RefreshCw size={14} />
                  批量生成选中动作
                </>
              )}
            </button>
          </>
        )}

        {results.length > 0 && (
          <>
            <div className="section-heading compact-heading" style={{ marginTop: 24 }}>
              <h3>生成结果</h3>
              <span>{results.length} 个变体</span>
            </div>
            <div className="generated-grid">
              {results.map((asset) => (
                <article className="generated-card" key={asset.id}>
                  <div
                    className="generated-thumb"
                    onClick={() => setLightbox({ url: buildAssetPreviewUrl(asset.localPath), name: asset.assetName, type: asset.assetType, provider: asset.provider })}
                  >
                    <img
                      src={buildAssetPreviewUrl(asset.localPath)}
                      alt={`${asset.assetName} preview`}
                    />
                  </div>
                  <div className="generated-card-head">
                    <CheckCircle2 size={16} />
                    <strong>{asset.assetName}</strong>
                    <span>{assetTypeLabels[asset.assetType] || asset.assetType}</span>
                  </div>
                  <p>{asset.localPath}</p>
                  <small>
                    {asset.provider} / {asset.providerMetadata.promptHash}
                  </small>
                  <pre>{asset.finalPrompt}</pre>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
      {lightbox && (
        <div className="lightbox-backdrop" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>X</button>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <img src={lightbox.url} alt={lightbox.name} />
            <div className="lightbox-info">
              <strong>{lightbox.name}</strong>
              <span>{lightbox.type}</span>
              <span>{lightbox.provider}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
