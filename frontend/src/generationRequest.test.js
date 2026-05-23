import { describe, expect, it } from 'vitest';

import { buildGenerationRequest, defaultGenerationForm } from './generationRequest.js';

describe('buildGenerationRequest', () => {
  it('maps enabled asset rows into the API request payload', () => {
    const request = buildGenerationRequest(defaultGenerationForm, {
      mode: 'professional',
      targetModel: 'mock_seed',
    });

    expect(request.projectName).toBe('Cyber Bamboo Platformer');
    expect(request.gameType).toBe('platformer');
    expect(request.style).toBe('pixel_art');
    expect(request.promptMode).toBe('professional');
    expect(request.targetModel).toBe('mock_seed');
    expect(request.assets).toHaveLength(4);
    expect(request.assets[0]).toEqual({
      type: 'character',
      name: 'hero',
      description: 'a brave cyber bamboo warrior',
    });
  });

  it('excludes disabled assets from the generated request payload', () => {
    const form = {
      ...defaultGenerationForm,
      assets: defaultGenerationForm.assets.map((asset) =>
        asset.name === 'coin' ? { ...asset, enabled: false } : asset,
      ),
    };

    const request = buildGenerationRequest(form);

    expect(request.assets.map((asset) => asset.name)).not.toContain('coin');
    expect(request.assets).toHaveLength(3);
    expect(request.promptMode).toBe('normal');
    expect(request.targetModel).toBe('mock_seed');
  });
});
