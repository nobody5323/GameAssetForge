export const defaultGenerationForm = {
  projectName: 'Cyber Bamboo Platformer',
  gameType: 'platformer',
  style: 'pixel_art',
  theme: 'cyber bamboo forest',
  description: '赛博竹林主题 2D 横版闯关游戏，需要主角、敌人、金币和地砖素材。',
  assets: [
    {
      type: 'character',
      name: 'hero',
      description: 'a brave cyber bamboo warrior',
      enabled: true,
    },
    {
      type: 'enemy',
      name: 'bamboo_slime',
      description: 'a small glowing slime monster',
      enabled: true,
    },
    {
      type: 'item',
      name: 'coin',
      description: 'a neon bamboo coin icon',
      enabled: true,
    },
    {
      type: 'tileset',
      name: 'ground_tile',
      description: 'cyber bamboo forest ground tile',
      enabled: true,
    },
  ],
};

export function buildGenerationRequest(form) {
  return {
    projectName: form.projectName,
    gameType: form.gameType,
    style: form.style,
    theme: form.theme,
    description: form.description,
    assets: form.assets
      .filter((asset) => asset.enabled)
      .map(({ type, name, description }) => ({ type, name, description })),
  };
}
