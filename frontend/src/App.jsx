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
  fetchAssets,
  fetchExportableGenerations,
  fetchQualityReport,
  generateAssets,
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
  novelaiImageModels,
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
  buildPromptCompileRequest,
  compilePrompt,
  pickInitialCandidate,
  promptModes,
  targetModels,
} from './promptCompiler.js';

const views = [
  { id: 'generate', label: '素材生成', icon: Play },
  { id: 'config', label: 'LLM 配置', icon: Bot },
  { id: 'imageConfig', label: 'Image API 配置', icon: Paintbrush },
  { id: 'library', label: '素材库', icon: Image },
  { id: 'quality', label: '质量报告', icon: ShieldCheck },
  { id: 'export', label: '导出交付', icon: Archive },
];

const assetTypes = ['character', 'enemy', 'item', 'tileset', 'ui', 'background'];
const gameTypes = ['platformer', 'rpg', 'roguelike', 'metroidvania'];
const styles = ['pixel_art', 'cartoon', 'dark_fantasy', 'cyberpunk'];
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
      setSubmitState(`已生成 ${response.assets.length} 个素材：${response.generationId}`);
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
              <div className="generated-thumb">
                <img src={buildAssetPreviewUrl(asset.localPath)} alt={`${asset.assetName} preview`} />
              </div>
              <div className="generated-card-head">
                <CheckCircle2 size={16} />
                <strong>{asset.assetName}</strong>
                <span>{asset.assetType}</span>
              </div>
              <p>{asset.localPath}</p>
              <small>
                {asset.provider} / {asset.providerMetadata.promptHash}
              </small>
              <pre>{asset.finalPrompt}</pre>
            </article>
          ))}
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
                  {asset.assetName} <span>{asset.assetType}</span>
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
      // Auto-switch model list when provider changes
      if (field === 'provider') {
        if (value === 'novelai') {
          next.imageModel = 'nai-diffusion-4-curated-preview';
          next.baseUrl = 'https://image.novelai.net';
        } else {
          next.imageModel = 'dall-e-3';
          next.baseUrl = 'https://api.openai.com/v1';
        }
      }
      return next;
    });
  }

  const isNovelAI = form.provider === 'novelai';
  const modelOptions = isNovelAI ? novelaiImageModels : openaiImageModels;

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
              placeholder={isNovelAI ? 'https://image.novelai.net' : 'https://api.openai.com/v1'}
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
          {!isNovelAI && (
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
          {isNovelAI ? 'NovelAI Token' : 'OpenAI API Key'}
          <input
            type="password"
            value={form.apiKey}
            onChange={(event) => updateConfig('apiKey', event.target.value)}
            placeholder={
              isNovelAI
                ? '输入 NovelAI access token...'
                : form.hasApiKey
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

        <div className="image-config-hint">
          <h4>
            <Paintbrush size={12} />
            {isNovelAI ? 'NovelAI 使用说明' : 'OpenAI DALL-E 使用说明'}
          </h4>
          {isNovelAI ? (
            <ul>
              <li>在 NovelAI 网站登录后，从浏览器 DevTools → Network 中抓取 <code>Authorization</code> header 的 token</li>
              <li>提示词将被编译为逗号分隔的 tags 格式（与 NovelAI 原生风格一致）</li>
              <li>无 token 时自动降级为 Mock Provider</li>
            </ul>
          ) : (
            <ul>
              <li>需要 <code>sk-...</code> 格式的 OpenAI API Key，需开通 DALL-E 使用权限</li>
              <li>DALL-E 3 支持 1024×1024、1024×1792、1792×1024</li>
              <li>无 Key 时自动降级为 Mock Provider</li>
            </ul>
          )}
        </div>

        <div className="config-status-grid">
          <div>
            <strong>Provider</strong>
            <span>{form.provider === 'openai' ? 'OpenAI DALL-E' : 'NovelAI'}</span>
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

function LibraryPage() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('');

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
              <div className="asset-thumb">
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
                <p>{asset.assetType}</p>
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
      setError(err instanceof Error ? err.message : 'Quality check failed');
    } finally {
      setLoading(false);
    }
  }

  function scoreColor(score) {
    if (score >= 80) return 'var(--accent)';
    if (score >= 60) return 'var(--accent-yellow)';
    return 'var(--accent-red)';
  }

  return (
    <section className="panel quality-panel">
      <div className="section-heading">
        <h3>Quality Inspector</h3>
        <span>{report ? `报告就绪` : '待检查'}</span>
      </div>

      <form className="quality-form" onSubmit={handleInspect}>
        <label>
          Generation ID
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
              INSPECT
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
          选择一个 Generation ID 并点击 INSPECT 开始质量检查。
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
                <span className="quality-asset-type">{assetReport.assetType}</span>
              </div>
              <div className="quality-checks">
                {assetReport.checks.map((check) => (
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
                      <strong>{check.label}</strong>
                      <p>{check.message}</p>
                    </div>
                    <span className="quality-check-deduction">
                      {check.passed ? '✓' : `-${check.score}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function ExportPage() {
  const [generations, setGenerations] = useState([]);
  const [selectedGen, setSelectedGen] = useState('');
  const [loadingGens, setLoadingGens] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [exportResult, setExportResult] = useState(null);
  const [genError, setGenError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState('');

  async function loadGenerations() {
    setLoadingGens(true);
    setGenError('');
    try {
      const ids = await fetchExportableGenerations();
      setGenerations(ids);
      if (ids.length > 0 && !selectedGen) {
        setSelectedGen(ids[0]);
      }
    } catch (err) {
      setGenError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoadingGens(false);
    }
  }

  useEffect(() => {
    loadGenerations();
  }, []);

  async function handleExport() {
    if (!selectedGen) return;
    setExporting(true);
    setError('');
    setExportResult(null);
    try {
      const result = await exportGeneration(selectedGen);
      setExportResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '导出失败');
    } finally {
      setExporting(false);
    }
  }

  async function handleCloudUpload() {
    if (!selectedGen) return;
    setUploading(true);
    setUploadError('');
    setUploadResult(null);
    try {
      const assets = await uploadGenerationToCloud(selectedGen);
      setUploadResult(assets);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : '云端上传失败');
    } finally {
      setUploading(false);
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <section className="panel export-panel">
      <div className="section-heading">
        <h3>素材包导出</h3>
        <span>{loadingGens ? 'LOADING' : `${generations.length} GENERATIONS`}</span>
      </div>

      {loadingGens && (
        <div className="empty-state">
          <Loader2 size={28} />
          正在从素材仓库读取 generation 列表...
        </div>
      )}

      {genError && !loadingGens && (
        <div className="empty-state">
          <p className="error-line">{genError}</p>
          <button className="secondary-button" type="button" onClick={loadGenerations}>
            <RefreshCw size={14} />
            RETRY
          </button>
        </div>
      )}

      {!loadingGens && !genError && generations.length === 0 && (
        <div className="empty-state">
          <Package size={28} />
          暂无素材记录。请先在生成页创建素材，然后返回导出。
        </div>
      )}

      {!loadingGens && !genError && generations.length > 0 && (
        <>
          <div className="export-form">
            <label>
              选择 Generation
              <select
                value={selectedGen}
                onChange={(e) => {
                  setSelectedGen(e.target.value);
                  setExportResult(null);
                  setError('');
                }}
              >
                {generations.map((genId) => (
                  <option key={genId} value={genId}>
                    {genId}
                  </option>
                ))}
              </select>
            </label>

            <div className="button-row">
              <button
                className="primary-button"
                type="button"
                onClick={handleExport}
                disabled={exporting || !selectedGen}
              >
                {exporting ? (
                  <>
                    <Loader2 size={14} />
                    EXPORTING
                  </>
                ) : (
                  <>
                    <Download size={14} />
                    EXPORT ZIP
                  </>
                )}
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={loadGenerations}
                disabled={loadingGens}
              >
                <RefreshCw size={14} />
                REFRESH
              </button>
            </div>
          </div>

          {error && <p className="error-line">{error}</p>}

          {exportResult && (
            <div className="export-result">
              <div className="export-result-icon">
                <CheckCircle2 size={32} />
              </div>
              <div className="export-result-info">
                <h4>导出成功</h4>
                <p>
                  <strong>{exportResult.zipFileName}</strong> 已下载
                </p>
                <div className="export-stats">
                  <span>
                    <FileJson size={12} />
                    {exportResult.assetCount} 个素材
                  </span>
                  <span>
                    <FileJson size={12} />
                    manifest {formatSize(exportResult.manifestSize)}
                  </span>
                  <span>
                    <Package size={12} />
                    总计 {formatSize(exportResult.totalSize)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ── 云端上传 ── */}
          <div className="export-divider" />

          <div className="export-form">
            <label>
              <Cloud size={14} />
              云端上传（模拟）
            </label>
            <p className="cloud-hint">
              将当前 generation 的所有素材上传到云端。未配置真实云存储时使用 Mock 模式，
              返回 <code>cloud://mock/...</code> 格式的模拟 URL。
            </p>
            <div className="button-row">
              <button
                className="secondary-button"
                type="button"
                onClick={handleCloudUpload}
                disabled={uploading || !selectedGen}
              >
                {uploading ? (
                  <>
                    <Loader2 size={14} />
                    UPLOADING
                  </>
                ) : (
                  <>
                    <Upload size={14} />
                    UPLOAD TO CLOUD
                  </>
                )}
              </button>
            </div>
          </div>

          {uploadError && <p className="error-line">{uploadError}</p>}

          {uploadResult && (
            <div className="export-result">
              <div className="export-result-icon">
                <Cloud size={32} />
              </div>
              <div className="export-result-info">
                <h4>上传成功</h4>
                <p>
                  <strong>{uploadResult.length}</strong> 个素材已上传至云端
                </p>
                <div className="export-stats">
                  {uploadResult.slice(0, 5).map((asset) => (
                    <span key={asset.id} title={asset.cloudUrl}>
                      {asset.assetName}: {asset.cloudUrl}
                    </span>
                  ))}
                  {uploadResult.length > 5 && (
                    <span>...另有 {uploadResult.length - 5} 个</span>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="export-hint">
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

export default App;
