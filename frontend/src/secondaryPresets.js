export const SECONDARY_PRESETS = {
  character: [
    { action: 'move', label: '移动 (Move)', promptHint: 'dynamic walking or running pose, motion animation frame' },
    { action: 'attack', label: '攻击 (Attack)', promptHint: 'attack animation, weapon swing or combat pose' },
    { action: 'defend', label: '防御 (Defend)', promptHint: 'defensive blocking stance, shield or guard position' },
    { action: 'skill_release', label: '技能释放 (Skill)', promptHint: 'special skill release, magical effects, dramatic pose' },
  ],
  enemy: [
    { action: 'move', label: '移动 (Move)', promptHint: 'patrol or advancing pose, movement frame' },
    { action: 'attack', label: '攻击 (Attack)', promptHint: 'attacking toward player, aggressive combat pose' },
    { action: 'defend', label: '防御 (Defend)', promptHint: 'defensive or blocking position, guarded stance' },
    { action: 'skill', label: '技能 (Skill)', promptHint: 'casting or charging a special ability, energy aura' },
  ],
  item: [
    { action: 'angle_front', label: '正面 (Front)', promptHint: 'viewed from the front, centered composition' },
    { action: 'angle_side', label: '侧面 (Side)', promptHint: 'side profile showing depth and thickness' },
    { action: 'angle_top', label: '俯视 (Top)', promptHint: 'top-down bird\'s eye perspective' },
    { action: 'upgrade', label: '升级版 (Upgraded)', promptHint: 'upgraded, ornate, more powerful, glowing appearance' },
  ],
  tileset: [
    { action: 'terrain_variant', label: '地形变体 (Terrain Variant)', promptHint: 'different terrain features, alternate ground pattern' },
    { action: 'edge', label: '边缘 (Edge)', promptHint: 'edge piece transitioning between surfaces' },
    { action: 'corner', label: '转角 (Corner)', promptHint: 'corner piece where two edges meet' },
    { action: 'pattern', label: '花纹变体 (Pattern)', promptHint: 'decorative pattern variation, ornamental details' },
  ],
  ui: [
    { action: 'state_hover', label: '悬停态 (Hover)', promptHint: 'hover state, highlighted or enlarged, subtle glow' },
    { action: 'state_click', label: '点击态 (Click)', promptHint: 'pressed or clicked state, depressed appearance' },
    { action: 'state_disabled', label: '禁用态 (Disabled)', promptHint: 'disabled or greyed out, muted colors' },
    { action: 'state_active', label: '激活态 (Active)', promptHint: 'active or selected state, highlighted with accent' },
  ],
  background: [
    { action: 'map_layout_1', label: '地图布局1 (Layout 1)', promptHint: 'first map layout with different terrain arrangement' },
    { action: 'map_layout_2', label: '地图布局2 (Layout 2)', promptHint: 'second map layout with different platform placement' },
    { action: 'time_day', label: '白天 (Daytime)', promptHint: 'bright daytime lighting, warm sunlight, blue sky' },
    { action: 'time_night', label: '夜晚 (Night)', promptHint: 'dark nighttime lighting, moonlight, dark blue tones' },
    { action: 'weather_rain', label: '雨天 (Rain)', promptHint: 'rainy weather, falling rain, wet surfaces, overcast' },
    { action: 'weather_snow', label: '雪天 (Snow)', promptHint: 'snowy weather, falling snow, cold winter atmosphere' },
  ],
};

export function getPresetsForType(assetType) {
  return SECONDARY_PRESETS[assetType] || [];
}
