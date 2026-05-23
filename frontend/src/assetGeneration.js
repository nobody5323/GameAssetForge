const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';
const API_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, '');

export async function generateAssets(request) {
  const response = await fetch(`${API_BASE_URL}/assets/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Asset generation failed with ${response.status}`);
  }

  return response.json();
}

export function buildAssetPreviewUrl(localPath) {
  if (!localPath) {
    return '';
  }
  return `${API_ORIGIN}/${localPath.replace(/^\/+/, '')}`;
}

export function summarizeGeneratedAssets(response) {
  if (!response) {
    return '等待生成';
  }
  return `${response.generationId} / ${response.assets.length} 个素材 / ${response.provider}`;
}
