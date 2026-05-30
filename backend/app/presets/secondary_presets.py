SECONDARY_GENERATION_PRESETS = {
    "character": [
        {
            "action": "move",
            "label": "移动 (Move)",
            "prompt": "the character in a dynamic walking or running pose, motion lines or step animation frame, same art style and character design as the original",
        },
        {
            "action": "attack",
            "label": "攻击 (Attack)",
            "prompt": "the character performing an attack animation, weapon swing or combat pose, action frame with impact emphasis, same art style and character design as the original",
        },
        {
            "action": "defend",
            "label": "防御 (Defend)",
            "prompt": "the character in a defensive blocking stance, shield up or guard position, braced for impact, same art style and character design as the original",
        },
        {
            "action": "skill_release",
            "label": "技能释放 (Skill Release)",
            "prompt": "the character releasing a special skill or ultimate ability, magical or energy effects around them, dramatic pose, same art style and character design as the original",
        },
    ],
    "enemy": [
        {
            "action": "move",
            "label": "移动 (Move)",
            "prompt": "the enemy in a patrol or advancing pose, movement animation frame, same art style and design as the original",
        },
        {
            "action": "attack",
            "label": "攻击 (Attack)",
            "prompt": "the enemy attacking toward the player, aggressive combat pose, attack animation frame, same art style and design as the original",
        },
        {
            "action": "defend",
            "label": "防御 (Defend)",
            "prompt": "the enemy in a defensive or blocking position, guarded stance, same art style and design as the original",
        },
        {
            "action": "skill",
            "label": "技能 (Skill)",
            "prompt": "the enemy casting or charging a special ability, magical or energy aura, dramatic effect, same art style and design as the original",
        },
    ],
    "item": [
        {
            "action": "angle_front",
            "label": "正面 (Front)",
            "prompt": "the item viewed directly from the front, centered composition, same art style as the original",
        },
        {
            "action": "angle_side",
            "label": "侧面 (Side)",
            "prompt": "the item viewed from the side profile, showing depth and thickness, same art style as the original",
        },
        {
            "action": "angle_top",
            "label": "俯视 (Top)",
            "prompt": "the item viewed from a top-down angle, bird's eye perspective, same art style as the original",
        },
        {
            "action": "upgrade",
            "label": "升级版 (Upgraded)",
            "prompt": "an upgraded, more ornate or powerful version of the item, enhanced visual quality, glowing or premium appearance, same art style as the original",
        },
    ],
    "tileset": [
        {
            "action": "terrain_variant",
            "label": "地形变体 (Terrain Variant)",
            "prompt": "a variant of the tile with different terrain features, alternate ground pattern, seamless tiling, same art style as the original",
        },
        {
            "action": "edge",
            "label": "边缘 (Edge)",
            "prompt": "an edge piece that transitions between two surfaces, border tile, seamless tiling, same art style as the original",
        },
        {
            "action": "corner",
            "label": "转角 (Corner)",
            "prompt": "a corner piece where two edges meet, L-shaped transition, seamless tiling, same art style as the original",
        },
        {
            "action": "pattern",
            "label": "花纹变体 (Pattern Variant)",
            "prompt": "a decorative pattern variation of the tile, ornamental details, seamless tiling, same art style as the original",
        },
    ],
    "ui": [
        {
            "action": "state_hover",
            "label": "悬停态 (Hover)",
            "prompt": "the UI element in hover state, slightly highlighted or enlarged, subtle glow or color change, same design style as the original",
        },
        {
            "action": "state_click",
            "label": "点击态 (Click)",
            "prompt": "the UI element in pressed or clicked state, depressed appearance, darker or inset look, same design style as the original",
        },
        {
            "action": "state_disabled",
            "label": "禁用态 (Disabled)",
            "prompt": "the UI element in disabled or greyed out state, muted colors, reduced opacity appearance, same design style as the original",
        },
        {
            "action": "state_active",
            "label": "激活态 (Active)",
            "prompt": "the UI element in active or selected state, highlighted with accent color, prominent appearance, same design style as the original",
        },
    ],
    "background": [
        {
            "action": "map_layout_1",
            "label": "地图布局1 (Layout 1)",
            "prompt": "first map layout variation with different terrain arrangement, alternative level design, same art style and theme as the original",
        },
        {
            "action": "map_layout_2",
            "label": "地图布局2 (Layout 2)",
            "prompt": "second map layout variation with different platform placement, alternative level design, same art style and theme as the original",
        },
        {
            "action": "time_day",
            "label": "白天 (Daytime)",
            "prompt": "the background scene in bright daytime lighting, warm sunlight, clear visibility, blue sky tones, same art style and theme as the original",
        },
        {
            "action": "time_night",
            "label": "夜晚 (Night)",
            "prompt": "the background scene in dark nighttime lighting, moonlight, stars, dark blue/purple tones, same art style and theme as the original",
        },
        {
            "action": "weather_rain",
            "label": "雨天 (Rain)",
            "prompt": "the background scene with rainy weather, falling rain particles, wet surfaces, grey overcast atmosphere, same art style and theme as the original",
        },
        {
            "action": "weather_snow",
            "label": "雪天 (Snow)",
            "prompt": "the background scene with snowy weather, falling snowflakes, white snow accumulation, cold winter atmosphere, same art style and theme as the original",
        },
    ],
}


def get_presets_for_type(asset_type: str) -> list[dict]:
    """Return the preset list for the given asset type, or empty list if unknown."""
    return SECONDARY_GENERATION_PRESETS.get(asset_type, [])


def get_action_label(asset_type: str, action: str) -> str:
    """Return the human-readable label for a given asset_type + action combo."""
    for preset in get_presets_for_type(asset_type):
        if preset["action"] == action:
            return preset["label"]
    return action


def build_action_prompt(asset_type: str, action: str) -> str:
    """Return the prompt fragment for a given asset_type + action combo."""
    for preset in get_presets_for_type(asset_type):
        if preset["action"] == action:
            return preset["prompt"]
    return ""
