const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const providerOptions = [
  { id: 'openai', label: 'OpenAI LLM' },
  { id: 'rule_fallback', label: 'Rule Fallback' },
];

export const defaultLlmConfigForm = {
  provider: 'openai',
  baseUrl: 'https://api.openai.com/v1',
  promptModel: 'gpt-5-mini',
  apiKey: '',
  clearApiKey: false,
};

export function buildLlmConfigPayload(form) {
  return {
    provider: form.provider,
    baseUrl: form.baseUrl.trim().replace(/\/+$/, '') || 'https://api.openai.com/v1',
    promptModel: form.promptModel.trim() || 'gpt-5-mini',
    apiKey: form.apiKey.trim() || null,
    clearApiKey: form.clearApiKey,
  };
}

export function applyLlmConfigResponse(response) {
  return {
    provider: response.provider,
    baseUrl: response.baseUrl,
    promptModel: response.promptModel,
    apiKey: '',
    clearApiKey: false,
    hasApiKey: response.hasApiKey,
  };
}

export async function fetchLlmConfig() {
  const response = await fetch(`${API_BASE_URL}/config/llm`);
  if (!response.ok) {
    throw new Error(`Load LLM config failed with ${response.status}`);
  }
  return response.json();
}

export async function saveLlmConfig(payload) {
  const response = await fetch(`${API_BASE_URL}/config/llm`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Save LLM config failed with ${response.status}`);
  }

  return response.json();
}
