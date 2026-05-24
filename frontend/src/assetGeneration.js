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

export async function fetchAssets(category) {
  const url = category
    ? `${API_BASE_URL}/assets?category=${encodeURIComponent(category)}`
    : `${API_BASE_URL}/assets`;

  const response = await fetch(url);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Asset list failed with ${response.status}`);
  }

  return response.json();
}

export async function fetchQualityReport(generationId) {
  const response = await fetch(`${API_BASE_URL}/quality/report/${encodeURIComponent(generationId)}`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Quality report failed with ${response.status}`);
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
  const errorCount = response.errors?.length || 0;
  const errorSuffix = errorCount > 0 ? ` (${errorCount} 失败)` : '';
  return `${response.generationId} / ${response.assets.length} 个素材${errorSuffix} / ${response.provider}`;
}

export async function fetchExportableGenerations() {
  const response = await fetch(`${API_BASE_URL}/exports`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to list generations: ${response.status}`);
  }

  return response.json();
}

export async function exportGeneration(generationId) {
  const response = await fetch(`${API_BASE_URL}/exports/${encodeURIComponent(generationId)}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Export failed with ${response.status}`);
  }

  // 读取 zip 为 blob 并触发浏览器下载
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${generationId}.zip`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);

  return {
    generationId: response.headers.get('X-Generation-Id') || generationId,
    zipFileName: `${generationId}.zip`,
    assetCount: parseInt(response.headers.get('X-Asset-Count') || '0', 10),
    manifestSize: parseInt(response.headers.get('X-Manifest-Size') || '0', 10),
    totalSize: parseInt(response.headers.get('X-Total-Size') || '0', 10),
  };
}

export async function uploadAssetToCloud(assetId) {
  const response = await fetch(`${API_BASE_URL}/cloud/upload/${encodeURIComponent(assetId)}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Cloud upload failed with ${response.status}`);
  }

  return response.json();
}

export async function uploadGenerationToCloud(generationId) {
  const response = await fetch(
    `${API_BASE_URL}/cloud/upload-generation/${encodeURIComponent(generationId)}`,
    { method: 'POST' },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Cloud upload failed with ${response.status}`);
  }

  return response.json();
}
