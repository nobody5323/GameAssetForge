const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const promptModes = [
  { id: 'normal', label: '普通模式', threshold: 60 },
  { id: 'professional', label: '专业模式', threshold: 80 },
];

export const targetModels = [
  { id: 'gpt_image', label: 'GPT Image' },
  { id: 'novelai', label: 'NovelAI' },
];

export function buildPromptCompileRequest(form, options) {
  return {
    mode: options.mode,
    targetModel: options.targetModel,
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

export function pickInitialCandidate(candidates = []) {
  return candidates[0]?.id || '';
}

export async function compilePrompt(request) {
  const response = await fetch(`${API_BASE_URL}/prompts/compile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Prompt compile failed with ${response.status}`);
  }

  return response.json();
}
