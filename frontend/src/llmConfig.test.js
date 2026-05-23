import { describe, expect, it } from 'vitest';

import { applyLlmConfigResponse, buildLlmConfigPayload } from './llmConfig.js';

describe('buildLlmConfigPayload', () => {
  it('normalizes empty model and key fields', () => {
    const payload = buildLlmConfigPayload({
      provider: 'openai',
      baseUrl: ' https://api.openai.com/v1/ ',
      promptModel: '   ',
      apiKey: '   ',
      clearApiKey: false,
    });

    expect(payload).toEqual({
      provider: 'openai',
      baseUrl: 'https://api.openai.com/v1',
      promptModel: 'gpt-5-mini',
      apiKey: null,
      clearApiKey: false,
    });
  });

  it('preserves explicit clear key requests', () => {
    const payload = buildLlmConfigPayload({
      provider: 'rule_fallback',
      baseUrl: 'https://gateway.example.com/v1',
      promptModel: 'gpt-5.1-mini',
      apiKey: '',
      clearApiKey: true,
    });

    expect(payload.clearApiKey).toBe(true);
    expect(payload.provider).toBe('rule_fallback');
    expect(payload.baseUrl).toBe('https://gateway.example.com/v1');
  });
});

describe('applyLlmConfigResponse', () => {
  it('never puts the api key back into the frontend form', () => {
    const form = applyLlmConfigResponse({
      provider: 'openai',
      baseUrl: 'https://api.openai.com/v1',
      promptModel: 'gpt-5-mini',
      hasApiKey: true,
    });

    expect(form.apiKey).toBe('');
    expect(form.hasApiKey).toBe(true);
    expect(form.baseUrl).toBe('https://api.openai.com/v1');
  });
});
