import { describe, expect, it } from 'vitest';

import { summarizeGeneratedAssets } from './assetGeneration.js';

describe('summarizeGeneratedAssets', () => {
  it('summarizes a generation response for the UI status line', () => {
    expect(
      summarizeGeneratedAssets({
        generationId: 'gen_demo_001',
        provider: 'mock',
        assets: [{ id: 'asset_1' }, { id: 'asset_2' }],
      }),
    ).toBe('gen_demo_001 / 2 个素材 / mock');
  });

  it('shows a waiting label before generation starts', () => {
    expect(summarizeGeneratedAssets(null)).toBe('等待生成');
  });
});
