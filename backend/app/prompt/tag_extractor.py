from app.models.prompt_models import PromptCompileRequest


STYLE_TAGS = {
    "pixel_art": ["pixel art", "limited palette", "crisp edges"],
    "cartoon": ["cartoon style", "bold outline", "clean shapes"],
    "dark_fantasy": ["dark fantasy", "moody lighting", "ornate silhouette"],
    "cyberpunk": ["cyberpunk", "neon accents", "high-tech details"],
}

ASSET_TAGS = {
    "character": ["playable character", "clear silhouette"],
    "enemy": ["enemy sprite", "readable threat shape"],
    "item": ["collectible item", "icon-like shape"],
    "tileset": ["tileable terrain", "seamless edges"],
    "ui": ["game ui", "clean iconography"],
    "background": ["2d background", "parallax-ready layer"],
}

KEYWORD_TAGS = {
    "竹林": ["bamboo forest"],
    "赛博": ["cyberpunk"],
    "横版": ["side-scrolling"],
    "闯关": ["platformer"],
    "像素": ["pixel art"],
    "金币": ["coin"],
    "敌人": ["enemy"],
    "主角": ["hero"],
    "地砖": ["ground tile"],
}

TECHNICAL_TAGS = [
    "centered composition",
    "clear silhouette",
    "readable at small size",
    "simple background",
    "game-ready asset",
]

NEGATIVE_TAGS = [
    "no text",
    "no watermark",
    "no blurry edges",
    "no cropped subject",
    "no complex background",
]


def extract_prompt_tags(request: PromptCompileRequest) -> dict[str, list[str]]:
    text = " ".join(
        [
            request.projectName,
            request.gameType,
            request.style,
            request.theme,
            request.description,
            " ".join(asset.description for asset in request.assets),
        ]
    )

    style_tags = STYLE_TAGS.get(request.style, [request.style.replace("_", " ")])
    subject_tags = []
    for asset in request.assets:
        subject_tags.extend(ASSET_TAGS.get(asset.type, [asset.type.replace("_", " ")]))
        subject_tags.append(asset.name.replace("_", " "))

    theme_tags = [request.theme]
    environment_tags = []
    mood_tags = []

    lowered = text.lower()
    for keyword, tags in KEYWORD_TAGS.items():
        if keyword in text or keyword.lower() in lowered:
            theme_tags.extend(tags)

    if "forest" in lowered or "竹林" in text:
        environment_tags.append("forest environment")
    if "cyber" in lowered or "赛博" in text:
        mood_tags.extend(["neon atmosphere", "futuristic mood"])

    return {
        "style": dedupe(style_tags),
        "subject": dedupe(subject_tags),
        "theme": dedupe(theme_tags),
        "environment": dedupe(environment_tags),
        "mood": dedupe(mood_tags),
        "technical": TECHNICAL_TAGS,
        "negative": NEGATIVE_TAGS,
    }


def dedupe(values: list[str]) -> list[str]:
    result = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in result:
            result.append(normalized)
    return result
