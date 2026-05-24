const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const cloudProviders = [
  { id: 'mock', label: 'Mock（本地模拟）' },
  { id: 'qiniu', label: '七牛云 Kodo' },
];

export const defaultCloudConfigForm = {
  provider: 'mock',
  accessKey: '',
  secretKey: '',
  bucket: '',
  domain: '',
  clearCredentials: false,
};

export function buildCloudConfigPayload(form) {
  return {
    provider: form.provider,
    accessKey: form.accessKey.trim() || null,
    secretKey: form.secretKey.trim() || null,
    bucket: form.bucket.trim() || null,
    domain: form.domain.trim() || null,
    clearCredentials: form.clearCredentials,
  };
}

export function applyCloudConfigResponse(response) {
  return {
    provider: response.provider,
    accessKey: '',
    secretKey: '',
    bucket: response.bucket || '',
    domain: response.domain || '',
    clearCredentials: false,
    hasCredentials: response.hasCredentials,
  };
}

export async function fetchCloudConfig() {
  const response = await fetch(`${API_BASE_URL}/config/cloud`);
  if (!response.ok) {
    throw new Error(`Load cloud config failed with ${response.status}`);
  }
  return response.json();
}

export async function saveCloudConfig(payload) {
  const response = await fetch(`${API_BASE_URL}/config/cloud`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Save cloud config failed with ${response.status}`);
  }

  return response.json();
}
