import { describe, expect, it } from 'vitest';

import { buildPromptCompileRequest, pickInitialCandidate } from './promptCompiler.js';
import { defaultGenerationForm } from './generationRequest.js';

describe('buildPromptCompileRequest', () => {
  it('adds prompt mode and target model to the enabled asset request', () => {
    const request = buildPromptCompileRequest(defaultGenerationForm, {
      mode: 'professional',
      targetModel: 'novelai',
    });

    expect(request.mode).toBe('professional');
    expect(request.targetModel).toBe('novelai');
    expect(request.assets).toHaveLength(4);
    expect(request.assets[1]).toEqual({
      type: 'enemy',
      name: 'bamboo_slime',
      description: 'a small glowing slime monster',
    });
  });

  it('keeps disabled assets out of the prompt compiler payload', () => {
    const form = {
      ...defaultGenerationForm,
      assets: defaultGenerationForm.assets.map((asset) =>
        asset.type === 'tileset' ? { ...asset, enabled: false } : asset,
      ),
    };

    const request = buildPromptCompileRequest(form, {
      mode: 'normal',
      targetModel: 'gpt_image',
    });

    expect(request.assets.map((asset) => asset.type)).not.toContain('tileset');
    expect(request.assets).toHaveLength(3);
  });
});

describe('pickInitialCandidate', () => {
  it('selects the first candidate returned by the compiler', () => {
    expect(pickInitialCandidate([{ id: 'candidate_1' }, { id: 'candidate_2' }])).toBe(
      'candidate_1',
    );
  });

  it('returns an empty selection when no candidates exist', () => {
    expect(pickInitialCandidate([])).toBe('');
  });
});
