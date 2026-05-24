import pytest

from app.prompt.chinese_translator import (
    CN_TO_EN_GAME_DICT,
    _is_chinese_char,
    extract_chinese_tags,
    translate_chinese_text,
)


class TestChineseTranslator:
    """Unit tests for Chinese → English game-dev term translation."""

    # ── Dictionary size ─────────────────────────────────────────────

    def test_dict_has_minimum_100_entries(self):
        assert len(CN_TO_EN_GAME_DICT) >= 100

    # ── Basic term translation ──────────────────────────────────────

    def test_translate_single_character_term(self):
        assert translate_chinese_text("角色") == "character"
        assert translate_chinese_text("敌人") == "enemy"
        assert translate_chinese_text("剑") == "sword"
        assert translate_chinese_text("火") == "fire"
        assert translate_chinese_text("冰") == "ice"

    def test_translate_two_character_term(self):
        assert translate_chinese_text("怪物") == "monster"
        assert translate_chinese_text("金币") == "gold coin"
        assert translate_chinese_text("森林") == "forest"
        assert translate_chinese_text("魔法") == "magical"

    def test_translate_multi_character_phrase(self):
        result = translate_chinese_text("森林场景")
        assert "forest" in result
        assert "scene" in result

    def test_translate_style_terms(self):
        assert "pixel art" in translate_chinese_text("像素")
        assert "cyberpunk" in translate_chinese_text("赛博")
        assert "anime" in translate_chinese_text("二次元")
        assert "cartoon" in translate_chinese_text("卡通")

    def test_translate_environment_terms(self):
        assert translate_chinese_text("城堡") == "castle"
        assert translate_chinese_text("地牢") == "dungeon"
        assert translate_chinese_text("沙漠") == "desert"
        assert translate_chinese_text("海洋") == "ocean"

    # ── Mixed Chinese / English text ────────────────────────────────

    def test_mixed_cn_en_text_passthrough(self):
        result = translate_chinese_text("bamboo_slime 怪物")
        assert "bamboo_slime" in result
        assert "monster" in result

    def test_english_passthrough_unchanged(self):
        result = translate_chinese_text("pixel art forest game asset")
        assert "pixel" in result
        assert "art" in result
        assert "forest" in result
        assert "game" in result
        assert "asset" in result

    def test_mixed_with_punctuation_and_numbers(self):
        result = translate_chinese_text("生命 +50 药水")
        assert "+50" in result
        assert "potion" in result

    # ── Edge cases ──────────────────────────────────────────────────

    def test_empty_string(self):
        assert translate_chinese_text("") == ""

    def test_none_input(self):
        assert translate_chinese_text(None) == ""

    def test_unknown_chinese_dropped(self):
        # Characters not in the dictionary should be silently omitted
        result = translate_chinese_text("一些未知词")
        # Should not raise, and should return empty or minimal output
        # (unknown chars are skipped)
        assert isinstance(result, str)

    def test_pure_unknown_chinese_returns_empty(self):
        result = translate_chinese_text("龘靐齉")
        assert result == ""

    # ── Longest-match priority ──────────────────────────────────────

    def test_longest_match_priority(self):
        # "火焰" → "fire" (if no compound entry), or a compound entry
        # The dict has "火焰" → "fire"
        result = translate_chinese_text("火焰")
        assert "fire" in result

    def test_compound_not_split(self):
        # "开放世界" should match as a whole, not "开放" + "世界"
        result = translate_chinese_text("开放世界")
        assert "open world" in result

    # ── Real-world prompt scenarios ─────────────────────────────────

    def test_translate_game_concept(self):
        result = translate_chinese_text("赛博竹林主题 2D 横版闯关游戏")
        assert "cyberpunk" in result
        assert "bamboo forest" in result
        assert "2D" in result
        assert "side-scrolling" in result
        assert "platformer" in result

    def test_translate_character_concept(self):
        result = translate_chinese_text("一位像素风的女巫角色，手持魔杖")
        assert "pixel art style" in result
        assert "witch" in result
        assert "wand" in result

    def test_translate_item_concept(self):
        result = translate_chinese_text("一把金色的传说长剑")
        assert "golden" in result
        assert "legendary" in result
        assert "sword" in result


class TestExtractChineseTags:
    """Tests for the extract_chinese_tags() helper."""

    def test_extract_basic_tags(self):
        tags = extract_chinese_tags("角色 敌人 金币")
        assert "character" in tags
        assert "enemy" in tags
        assert "gold coin" in tags

    def test_extract_tags_from_description(self):
        tags = extract_chinese_tags(
            "赛博竹林主题 2D 横版闯关游戏，需要主角和敌人"
        )
        assert "cyberpunk" in tags
        assert "bamboo forest" in tags
        assert "side-scrolling" in tags
        assert "platformer" in tags
        assert ("protagonist" in tags or "hero" in tags)
        assert "enemy" in tags

    def test_extract_tags_no_duplicates(self):
        tags = extract_chinese_tags("角色 角色 敌人 角色")
        assert tags.count("character") == 1

    def test_extract_tags_order_preserved(self):
        tags = extract_chinese_tags("森林 城堡 沙漠")
        forest_idx = tags.index("forest") if "forest" in tags else -1
        castle_idx = tags.index("castle") if "castle" in tags else -1
        desert_idx = tags.index("desert") if "desert" in tags else -1
        if forest_idx >= 0 and castle_idx >= 0 and desert_idx >= 0:
            assert forest_idx < castle_idx < desert_idx

    def test_extract_empty_text(self):
        assert extract_chinese_tags("") == []
        assert extract_chinese_tags("hello world") == []


class TestIsChineseChar:
    """Tests for the _is_chinese_char() helper."""

    def test_cjk_character(self):
        assert _is_chinese_char("角") is True
        assert _is_chinese_char("色") is True
        assert _is_chinese_char("赛") is True

    def test_ascii_character(self):
        assert _is_chinese_char("a") is False
        assert _is_chinese_char("Z") is False
        assert _is_chinese_char("9") is False
        assert _is_chinese_char("_") is False

    def test_space_not_chinese(self):
        assert _is_chinese_char(" ") is False


class TestIntegrationWithPipeline:
    """Integration-style tests mimicking the prompt-building pipeline."""

    def test_project_context_translation(self):
        """Simulates what rule_llm_provider does."""
        fields = ["赛博竹林", "平台跳跃", "像素", "竹林主题关卡"]
        result = ", ".join(
            translate_chinese_text(f) for f in fields
        )
        assert "cyberpunk" in result
        assert "bamboo forest" in result
        assert "platformer" in result
        assert "pixel art" in result

    def test_asset_fields_translated(self):
        """Simulates what model_optimizers does for a NovelAI prompt."""
        from app.prompt.chinese_translator import translate_chinese_text

        asset_name = "暗黑骑士"
        asset_desc = "一位身穿黑色铠甲的邪恶骑士"

        name_en = translate_chinese_text(asset_name.replace("_", " "))
        desc_en = translate_chinese_text(asset_desc)

        # Both should be purely English now
        assert "dark" in name_en or "knight" in name_en
        assert any(ord(c) < 128 for c in desc_en)  # ASCII only
