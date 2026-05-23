import { describe, expect, it } from 'vitest';

import { buildAssetPreviewUrl, summarizeGeneratedAssets } from './assetGeneration.js';

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

describe('buildAssetPreviewUrl', () => {
  it('converts backend localPath into a browser image URL', () => {
    expect(
      buildAssetPreviewUrl('runtime/storage/generated-assets/gen_demo/enemy/bamboo_slime.png'),
    ).toBe('http://127.0.0.1:8000/runtime/storage/generated-assets/gen_demo/enemy/bamboo_slime.png');
  });
});
