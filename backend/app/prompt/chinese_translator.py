"""
Chinese-to-English game asset tag translator.

Translates Chinese game dev terms into English image generation tags
so that image generation models receive clean, usable prompts.

Falls back to Danbooru tag API for terms not in the local dictionary.
"""

import re
import time
from typing import Optional

import httpx

# ---------------------------------------------------------------------------
# Comprehensive Chinese → English game-dev dictionary (longest-key-first order)
# ---------------------------------------------------------------------------
CN_TO_EN_GAME_DICT: dict[str, str] = {
    # ── Roles / Characters ──────────────────────────────────────────
    "主角": "protagonist",
    "敌人": "enemy",
    "怪物": "monster",
    "角色": "character",
    "战士": "warrior",
    "法师": "mage",
    "弓箭手": "archer",
    "盗贼": "thief",
    "牧师": "priest",
    "骑士": "knight",
    "召唤师": "summoner",
    "村民": "villager",
    "商人": "merchant",
    "铁匠": "blacksmith",
    "守卫": "guard",
    "国王": "king",
    "公主": "princess",
    "女王": "queen",
    "精灵": "elf",
    "矮人": "dwarf",
    "兽人": "orc",
    "骷髅": "skeleton",
    "僵尸": "zombie",
    "幽灵": "ghost",
    "吸血鬼": "vampire",
    "狼人": "werewolf",
    "机器人": "robot",
    "机甲": "mecha",
    "忍者": "ninja",
    "武士": "samurai",
    "刺客": "assassin",
    "猎人": "hunter",
    "游侠": "ranger",
    "龙": "dragon",
    "巨龙": "dragon",
    "凤凰": "phoenix",
    "天使": "angel",
    "恶魔": "demon",
    "魔王": "demon lord",
    "史莱姆": "slime",
    "哥布林": "goblin",
    "巨魔": "troll",
    "女巫": "witch",
    "巫师": "wizard",
    "术士": "warlock",
    "德鲁伊": "druid",
    "圣骑士": "paladin",
    "狂战士": "berserker",
    "NPC": "npc",

    # ── Items / Equipment ───────────────────────────────────────────
    "道具": "item",
    "武器": "weapon",
    "装备": "equipment",
    "剑": "sword",
    "盾": "shield",
    "长矛": "spear",
    "斧头": "axe",
    "匕首": "dagger",
    "弓箭": "bow",
    "魔杖": "wand",
    "法杖": "staff",
    "药水": "potion",
    "宝箱": "chest",
    "金币": "coin",
    "宝石": "gem",
    "钻石": "diamond",
    "钥匙": "key",
    "卷轴": "scroll",
    "铠甲": "armor",
    "头盔": "helmet",
    "戒指": "ring",
    "项链": "necklace",
    "药草": "herb",
    "食物": "food",
    "炸弹": "bomb",
    "陷阱": "trap",
    "水晶": "crystal",
    "符文": "rune",
    "地图": "map",

    # ── Scenes / Environments ───────────────────────────────────────
    "场景": "scene",
    "背景": "background",
    "森林": "forest",
    "竹林": "bamboo forest",
    "城堡": "castle",
    "地牢": "dungeon",
    "地下城": "dungeon",
    "天空": "sky",
    "海洋": "ocean",
    "沙漠": "desert",
    "雪地": "snowfield",
    "山脉": "mountain",
    "火山": "volcano",
    "河流": "river",
    "瀑布": "waterfall",
    "洞穴": "cave",
    "村庄": "village",
    "城市": "city",
    "废墟": "ruins",
    "神庙": "temple",
    "塔楼": "tower",
    "桥梁": "bridge",
    "草原": "grassland",
    "沼泽": "swamp",
    "冰原": "tundra",
    "冰川": "glacier",
    "岛屿": "island",
    "太空": "space",
    "实验室": "laboratory",
    "工厂": "factory",
    "街道": "street",
    "市场": "market",
    "酒馆": "tavern",
    "图书馆": "library",
    "墓地": "graveyard",
    "竞技场": "arena",
    "花园": "garden",
    "王座": "throne room",
    "港湾": "harbor",
    "港口": "port",

    # ── Effects / Magic ─────────────────────────────────────────────
    "特效": "effect",
    "魔法": "magical",
    "火焰": "fire",
    "火": "fire",
    "冰": "ice",
    "雷电": "lightning",
    "暗影": "shadow",
    "光明": "light",
    "爆炸": "explosion",
    "烟雾": "smoke",
    "光芒": "glow",
    "粒子": "particle",
    "传送门": "portal",
    "光环": "aura",
    "能量": "energy",
    "冲击波": "shockwave",
    "旋风": "whirlwind",
    "护盾": "barrier",
    "毒": "poison",
    "治愈": "healing",
    "诅咒": "curse",
    "增益": "buff",
    "减益": "debuff",
    "召唤": "summon",
    "闪现": "blink",
    "瞬移": "teleport",
    "冰冻": "freeze",
    "燃烧": "burning",
    "闪电": "lightning",
    "风暴": "storm",
    "地震": "earthquake",

    # ── UI / Interface ──────────────────────────────────────────────
    "界面": "ui",
    "图标": "icon",
    "按钮": "button",
    "菜单": "menu",
    "血条": "health bar",
    "对话框": "dialog box",
    "进度条": "progress bar",
    "状态栏": "status bar",
    "技能栏": "skill bar",
    "背包": "inventory",
    "装备栏": "equipment slot",
    "小地图": "minimap",
    "十字准星": "crosshair",
    "字体": "font",
    "光标": "cursor",
    "弹窗": "popup",
    "面板": "panel",
    "标签": "tab",
    "滑动条": "slider",
    "输入框": "input field",
    "复选框": "checkbox",
    "滚动条": "scrollbar",
    "提示框": "tooltip",

    # ── Styles / Artistic ───────────────────────────────────────────
    "像素风": "pixel art style",
    "像素": "pixel art",
    "赛博": "cyberpunk",
    "水墨": "ink wash",
    "卡通": "cartoon",
    "写实": "realistic",
    "二次元": "anime",
    "低多边形": "low poly",
    "手绘": "hand-drawn",
    "暗黑": "dark",
    "奇幻": "fantasy",
    "科幻": "sci-fi",
    "蒸汽朋克": "steampunk",
    "哥特": "gothic",
    "极简": "minimalist",
    "复古": "retro",
    "霓虹": "neon",
    "Q版": "chibi",
    "日系": "japanese style",
    "欧美": "western style",
    "韩系": "korean style",
    "厚涂": "thick paint",
    "平涂": "flat color",
    "水彩": "watercolor",
    "素描": "sketch",
    "油画": "oil painting",

    # ── Gameplay / Design ───────────────────────────────────────────
    "闯关": "platformer",
    "平台跳跃": "platformer",
    "横版": "side-scrolling",
    "回合制": "turn-based",
    "即时": "real-time",
    "塔防": "tower defense",
    "开放世界": "open world",
    "沙盒": "sandbox",
    "生存": "survival",
    "竞技": "competitive",
    "合作": "cooperative",
    "单人": "single player",
    "多人": "multiplayer",
    "主线": "main quest",
    "支线": "side quest",
    "任务": "quest",
    "技能": "skill",
    "天赋": "talent",
    "等级": "level",
    "经验": "experience",
    "属性": "attribute",
    "伤害": "damage",
    "防御": "defense",
    "暴击": "critical hit",
    "闪避": "dodge",
    "命中": "accuracy",
    "速度": "speed",
    "生命": "health",
    "魔法值": "mana",
    "体力": "stamina",
    "金币": "gold coin",
    "关卡": "level",
    "主题": "theme",
    "动作": "action",
    "冒险": "adventure",
    "解谜": "puzzle",
    "射击": "shooter",
    "格斗": "fighting",
    "竞速": "racing",
    "模拟": "simulation",
    "策略": "strategy",
    "音乐": "rhythm",
    "角色扮演": "rpg",
    "Boss": "boss",
    "boss": "boss",
    "美少女": "beautiful girl",
    "少女": "girl",
    "猫耳": "cat ears",
    "貓耳": "cat ears",
    "白发": "white hair",
    "白髮": "white hair",
    "游戏": "game",
    "遊戲": "game",
    "闯关": "platformer",
    "闖關": "platformer",

    # ── Quality / Technical tags ────────────────────────────────────
    "高品质": "best quality",
    "杰作": "masterpiece",
    "精细": "high detail",
    "高清": "high resolution",
    "居中构图": "centered composition",
    "清晰轮廓": "clear silhouette",
    "简单背景": "simple background",
    "无文字": "no text",
    "无水印": "no watermark",
    "游戏就绪": "game-ready asset",
    "透明背景": "transparent background",
    "独立素材": "isolated asset",

    # ── Common adjectives / modifiers ───────────────────────────────
    "大": "large",
    "小": "small",
    "红": "red",
    "蓝": "blue",
    "绿": "green",
    "金": "golden",
    "银": "silver",
    "黑": "black",
    "白": "white",
    "紫": "purple",
    "暗": "dark",
    "亮": "bright",
    "古代": "ancient",
    "未来": "futuristic",
    "魔法": "magical",
    "传说": "legendary",
    "稀有": "rare",
    "普通": "common",
    "史诗": "epic",
    "神话": "mythic",
}

# Pre-compute max key length for the segmentation algorithm
_MAX_KEY_LEN = max((len(k) for k in CN_TO_EN_GAME_DICT), default=0)

# Pre-compiled Chinese character range pattern
_CHINESE_CHAR_PATTERN = re.compile(r"[一-鿿㐀-䶿⼀-⿟　-〿＀-￯]")


# ---------------------------------------------------------------------------
# Danbooru tag API fallback
# ---------------------------------------------------------------------------

# In-memory cache: {chinese_term: english_tag} — populated by Danbooru lookups
_danbooru_cache: dict[str, str] = {}
_danbooru_misses: set[str] = set()  # terms confirmed not found on Danbooru
_danbooru_client: httpx.Client | None = None


def _get_danbooru_client() -> httpx.Client:
    """Lazy-init a shared httpx client for Danbooru API calls."""
    global _danbooru_client
    if _danbooru_client is None:
        _danbooru_client = httpx.Client(timeout=10, headers={
            "User-Agent": "GameAssetForge/1.0 (tag translator)",
            "Accept": "application/json",
        })
    return _danbooru_client


def _lookup_danbooru(term: str) -> str | None:
    """Look up a Chinese term on Danbooru and return its English tag name.

    Uses the Danbooru autocomplete API which is fast and returns
    the canonical English tag for a given search term.

    Results are cached in memory for the session lifetime.
    """
    if term in _danbooru_cache:
        return _danbooru_cache[term]
    if term in _danbooru_misses:
        return None

    try:
        client = _get_danbooru_client()
        resp = client.get(
            "https://danbooru.donmai.us/autocomplete.json",
            params={
                "search[query]": term,
                "search[type]": "tag_query",
                "limit": 1,
            },
        )
        resp.raise_for_status()
        results = resp.json()

        if results and isinstance(results, list) and len(results) > 0:
            tag_name = results[0].get("value") or results[0].get("label")
            if tag_name and isinstance(tag_name, str):
                # Normalize: replace underscores with spaces
                english = tag_name.strip().replace("_", " ")
                _danbooru_cache[term] = english
                return english
    except Exception:
        # Network errors, timeouts, rate limits — silently ignore
        pass

    _danbooru_misses.add(term)
    return None


def _is_chinese_char(ch: str) -> bool:
    """Return True if the character is a CJK character or fullwidth form."""
    return bool(_CHINESE_CHAR_PATTERN.match(ch))


def translate_chinese_text(text: str | None) -> str:
    """Convert Chinese text to English using the game-dev dictionary.

    Uses greedy longest-match-first segmentation.  Non-Chinese characters
    (ASCII, digits, punctuation) pass through unchanged.  Chinese characters
    not found in the dictionary are silently dropped.

    Returns the original text unchanged when it is empty / None.
    """
    if not text:
        return text or ""

    result_parts: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Group consecutive non-Chinese characters into a single chunk
        if not _is_chinese_char(ch):
            buf: list[str] = []
            while i < n and not _is_chinese_char(text[i]):
                buf.append(text[i])
                i += 1
            result_parts.append("".join(buf))
            continue

        # Try longest match first for Chinese characters
        matched = False
        max_look = min(_MAX_KEY_LEN, n - i)
        for look in range(max_look, 0, -1):
            candidate = text[i : i + look]
            if candidate in CN_TO_EN_GAME_DICT:
                result_parts.append(CN_TO_EN_GAME_DICT[candidate])
                i += look
                matched = True
                break

        if not matched:
            # Unknown Chinese character — try Danbooru with lookahead
            lookahead_end = min(i + 6, n)
            found_danbooru = False
            # Try progressively shorter lookahead clusters (up to 6 chars)
            for end in range(lookahead_end, i + 1, -1):
                cluster = text[i:end]
                if len(cluster) >= 2:
                    danbooru_result = _lookup_danbooru(cluster)
                    if danbooru_result:
                        result_parts.append(danbooru_result)
                        i = end
                        found_danbooru = True
                        break
            if not found_danbooru:
                i += 1  # skip single unknown char

    return " ".join(result_parts).strip()


def sanitize_prompt(prompt: str) -> str:
    """Final safety net — translate any remaining Chinese in a generated prompt.

    All tagged fields should already be translated before assembly, but this
    catches leaks so no Chinese ever reaches an image generation API.
    """
    if not prompt:
        return prompt
    return translate_chinese_text(prompt)


def extract_chinese_tags(text: str) -> list[str]:
    """Extract and translate known Chinese terms from *text*.

    Returns a deduplicated, order-preserving list of English tags.
    Use this to supplement theme / subject tag lists in
    :func:`app.prompt.tag_extractor.extract_prompt_tags`.
    """
    if not text:
        return []

    tags: list[str] = []
    seen: set[str] = set()
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if not _is_chinese_char(ch):
            i += 1
            continue

        matched = False
        max_look = min(_MAX_KEY_LEN, n - i)
        for look in range(max_look, 0, -1):
            candidate = text[i : i + look]
            if candidate in CN_TO_EN_GAME_DICT:
                tag = CN_TO_EN_GAME_DICT[candidate]
                if tag not in seen:
                    tags.append(tag)
                    seen.add(tag)
                i += look
                matched = True
                break

        if not matched:
                # Unknown Chinese character — try Danbooru with lookahead
                lookahead_end = min(i + 6, n)
                found_danbooru = False
                for end in range(lookahead_end, i + 1, -1):
                    cluster = text[i:end]
                    if len(cluster) >= 2:
                        danbooru_result = _lookup_danbooru(cluster)
                        if danbooru_result and danbooru_result not in seen:
                            tags.append(danbooru_result)
                            seen.add(danbooru_result)
                            i = end
                            found_danbooru = True
                            break
                if not found_danbooru:
                    i += 1  # skip single unknown char

    return tags
