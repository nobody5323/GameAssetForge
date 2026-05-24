const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const imageGenProviders = [
  { id: 'openai', label: 'OpenAI DALL-E' },
  { id: 'novelai', label: 'NovelAI Diffusion' },
];

export const imageGenSizes = [
  { id: '256x256', label: '256 × 256' },
  { id: '512x512', label: '512 × 512' },
  { id: '1024x1024', label: '1024 × 1024' },
  { id: '1024x1792', label: '1024 × 1792 (DALL-E 3)' },
  { id: '1792x1024', label: '1792 × 1024 (DALL-E 3)' },
];

export const imageGenQualities = [
  { id: 'standard', label: '标准' },
  { id: 'hd', label: 'HD (高清)' },
];

export const openaiImageModels = [
  { id: 'dall-e-3', label: 'DALL-E 3' },
  { id: 'dall-e-2', label: 'DALL-E 2' },
];

export const novelaiImageModels = [
  { id: 'nai-diffusion-4-full', label: 'NAI Diffusion V4 Full' },
  { id: 'nai-diffusion-4-curated-preview', label: 'NAI Diffusion V4 Curated' },
  { id: 'nai-diffusion-4.5-full', label: 'NAI Diffusion V4.5 Full' },
  { id: 'nai-diffusion-4.5-curated-preview', label: 'NAI Diffusion V4.5 Curated' },
  { id: 'nai-diffusion-3', label: 'NAI Diffusion 3' },
  { id: 'nai-diffusion-furry-3', label: 'NAI Diffusion Furry 3' },
];

export const defaultImageConfigForm = {
  provider: 'openai',
  baseUrl: 'https://api.openai.com/v1',
  imageModel: 'dall-e-3',
  imageSize: '1024x1024',
  imageQuality: 'standard',
  apiKey: '',
  clearApiKey: false,
};

export function buildImageConfigPayload(form) {
  return {
    provider: form.provider,
    baseUrl: form.baseUrl.trim().replace(/\/+$/, '') || 'https://api.openai.com/v1',
    imageModel: form.imageModel.trim() || 'dall-e-3',
    imageSize: form.imageSize || '1024x1024',
    imageQuality: form.imageQuality || 'standard',
    apiKey: form.apiKey.trim() || null,
    clearApiKey: form.clearApiKey,
  };
}

export function applyImageConfigResponse(response) {
  return {
    provider: response.provider,
    baseUrl: response.baseUrl,
    imageModel: response.imageModel,
    imageSize: response.imageSize,
    imageQuality: response.imageQuality,
    apiKey: '',
    clearApiKey: false,
    hasApiKey: response.hasApiKey,
  };
}

export async function fetchImageConfig() {
  const response = await fetch(`${API_BASE_URL}/config/image`);
  if (!response.ok) {
    throw new Error(`Load image config failed with ${response.status}`);
  }
  return response.json();
}

export async function saveImageConfig(payload) {
  const response = await fetch(`${API_BASE_URL}/config/image`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Save image config failed with ${response.status}`);
  }

  return response.json();
}
