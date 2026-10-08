"""
galIMVmini Tag Autocomplete and Danbooru Categorization Engine.
Classifies AI prompt tags into categories:
  0: General (Sky Blue)
  1: Artist (Rose/Red)
  3: Copyright/Series (Purple)
  4: Character (Emerald Green)
  5: Meta/Quality (Amber)
"""

import os
import re
from typing import Dict, List, Tuple, Optional

CATEGORY_GENERAL = 0
CATEGORY_ARTIST = 1
CATEGORY_COPYRIGHT = 3
CATEGORY_CHARACTER = 4
CATEGORY_META = 5

CATEGORY_NAMES = {
    CATEGORY_GENERAL: "General",
    CATEGORY_ARTIST: "Artist",
    CATEGORY_COPYRIGHT: "Series / Copyright",
    CATEGORY_CHARACTER: "Character",
    CATEGORY_META: "Meta / Quality",
}

CATEGORY_COLORS = {
    CATEGORY_GENERAL: "#38bdf8",   # Sky blue
    CATEGORY_ARTIST: "#f43f5e",    # Rose / Red
    CATEGORY_COPYRIGHT: "#a855f7", # Purple
    CATEGORY_CHARACTER: "#10b981", # Emerald green
    CATEGORY_META: "#f59e0b",      # Amber / Orange
}

META_KEYWORDS = {
    "masterpiece", "best quality", "best_quality", "highres", "high resolution",
    "high_resolution", "extremely detailed", "extremely_detailed", "aesthetic",
    "absurdres", "newest", "monochrome", "greyscale", "censored", "uncensored",
    "very detailed", "hdr", "4k", "8k", "raw photo", "ultra-detailed", "photorealistic",
    "hyperrealistic", "unreal engine", "octane render"
}

KNOWN_ARTISTS = {
    "shinkai", "rutkowski", "mucha", "artgerm", "wlop", "cutesexyrobutts",
    "ke-ta", "kantoku", "krenz", "range murata", "fuzichoco", "rebecca",
    "sanbonzakura", "jooho", "okumen", "ourboy83", "baalbuddy", "sunset_beach",
    "hws", "greg rutkowski", "makoto shinkai", "alphonse mucha", "kuvshinov"
}

ARTIST_PREFIXES = (
    "by ", "art by ", "artist:", "drawn by ", "illust by ", "illustration by ", "art:"
)

ARTIST_SUFFIXES = (
    "(artist)", "_(artist)", " (artist)", "(circle)", "_(circle)", " (circle)",
    "(style)", "_(style)", " (style)", " style", "(art)", "_(art)",
    "(illustrator)", "_(illustrator)", "(pixiv)", "_(pixiv)",
    "(twitter)", "_(twitter)", "(mangaka)", "_(mangaka)",
    "(doujinshi)", "_(doujinshi)"
)

class TagClassifier:
    def __init__(self):
        self._csv_map: Dict[str, int] = {}
        self._is_loaded = False
        self._csv_path = ""
        self._auto_load()

    def _auto_load(self):
        candidate_paths = [
            "T:/StabilityMatrix/Packages/Forge-Neo/extensions/a1111-sd-webui-tagcomplete/tags/danbooru.csv",
            "T:/StabilityMatrix/Tags/danbooru.csv",
            "T:/StabilityMatrix/Tags/danbooru_e621_merged.csv",
            "T:/StabilityMatrix/Packages/Forge Neo/extensions/a1111-sd-webui-tagcomplete/tags/danbooru.csv",
            "T:/StabilityMatrix/Packages/ForgeNeo/extensions/a1111-sd-webui-tagcomplete/tags/danbooru.csv",
            os.path.join(os.path.dirname(__file__), "..", "resources", "danbooru.csv"),
            os.path.join(os.getcwd(), "danbooru.csv"),
        ]
        for path in candidate_paths:
            if os.path.exists(path):
                self.load_csv(path)
                break

    def load_csv(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False
        try:
            mapping: Dict[str, int] = {}
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(",")
                    if len(parts) >= 2:
                        name = parts[0].strip().lower()
                        try:
                            cat = int(parts[1].strip())
                            mapping[name] = cat
                        except ValueError:
                            continue
            self._csv_map = mapping
            self._is_loaded = True
            self._csv_path = file_path
            return True
        except Exception:
            return False

    def classify_tag(self, raw_tag: str) -> int:
        tag = raw_tag.strip().lower()
        if not tag:
            return CATEGORY_GENERAL

        # 1. Direct CSV match
        if tag in self._csv_map:
            return self._csv_map[tag]

        # 2. Match with spaces converted to underscores or vice versa
        tag_under = tag.replace(" ", "_")
        if tag_under in self._csv_map:
            return self._csv_map[tag_under]

        tag_space = tag.replace("_", " ")
        if tag_space in self._csv_map:
            return self._csv_map[tag_space]

        # 3. Meta / Quality check
        if tag in META_KEYWORDS or tag_space in META_KEYWORDS or tag_under in META_KEYWORDS:
            return CATEGORY_META

        # 4. Artist prefixes
        for prefix in ARTIST_PREFIXES:
            if tag.startswith(prefix):
                return CATEGORY_ARTIST

        # 5. Artist suffixes
        for suffix in ARTIST_SUFFIXES:
            if tag.endswith(suffix):
                return CATEGORY_ARTIST

        # 6. Known artists
        for ka in KNOWN_ARTISTS:
            if ka in tag:
                return CATEGORY_ARTIST

        # 7. Disambiguation in parentheses
        if "(" in tag and ")" in tag:
            match = re.search(r"\(([^)]+)\)", tag)
            if match:
                inside = match.group(1).strip().lower()
                inside_under = inside.replace(" ", "_")
                # Artist indicators inside parentheses
                if inside in ("artist", "circle", "style", "art", "illustrator", "pixiv", "twitter", "mangaka", "studio"):
                    return CATEGORY_ARTIST
                # Series / Copyright indicates Character
                if self._csv_map.get(inside) == CATEGORY_COPYRIGHT or self._csv_map.get(inside_under) == CATEGORY_COPYRIGHT:
                    return CATEGORY_CHARACTER
                if inside.endswith(("series", "anime", "game", "franchise", "project", "manga")):
                    return CATEGORY_CHARACTER

        # 8. Character indicators
        if tag.startswith("1girl") or tag.startswith("1boy") or tag.startswith("2girls") or tag.startswith("multiple girls"):
            return CATEGORY_GENERAL

        return CATEGORY_GENERAL

    @staticmethod
    def clean_token(token: str) -> str:
        t = token.strip()
        # Unescape SD WebUI backslashes
        t = t.replace(r"\(", "(").replace(r"\)", ")")
        t = t.replace(r"\[", "[").replace(r"\]", "]")
        t = t.replace(r"\{", "{").replace(r"\}", "}")
        # Remove SD weight suffix :1.2
        t = re.sub(r":\s*[-+]?[0-9]*\.?[0-9]+\s*([)\]}]*)$", r"\1", t).strip()
        # Remove outer balancing brackets ((...)) [[...]] {{...}}
        changed = True
        while changed and len(t) >= 2:
            changed = False
            for open_b, close_b in [("(", ")"), ("[", "]"), ("{", "}")]:
                if t.startswith(open_b) and t.endswith(close_b):
                    # Check if balanced across whole string
                    depth = 0
                    is_outer = True
                    for i in range(len(t) - 1):
                        if t[i] == open_b:
                            depth += 1
                        elif t[i] == close_b:
                            depth -= 1
                            if depth == 0:
                                is_outer = False
                                break
                    if is_outer:
                        t = t[1:-1].strip()
                        changed = True
                        break
        return t.strip()

    @classmethod
    def extract_tags(cls, prompt: str) -> List[Tuple[str, int]]:
        if not prompt:
            return []
        
        raw_tokens = prompt.split(",")
        classifier = get_tag_classifier()
        seen = set()
        results: List[Tuple[str, int]] = []

        for token in raw_tokens:
            cleaned = cls.clean_token(token)
            # Skip empty or LoRA tags in tag cloud (they get dedicated LoRA badges)
            if not cleaned or cleaned.startswith("<lora:") or cleaned.startswith("<hypernet:"):
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                category = classifier.classify_tag(cleaned)
                results.append((cleaned, category))

        return results

    @classmethod
    def extract_loras(cls, prompt: str) -> List[Tuple[str, str]]:
        if not prompt:
            return []
        loras = []
        for match in re.finditer(r"<lora:([^:>]+)(?::([^>]+))?>", prompt, re.IGNORECASE):
            name = match.group(1).strip()
            weight = match.group(2).strip() if match.group(2) else "1.0"
            loras.append((name, weight))
        return loras

_global_classifier: Optional[TagClassifier] = None

def get_tag_classifier() -> TagClassifier:
    global _global_classifier
    if _global_classifier is None:
        _global_classifier = TagClassifier()
    return _global_classifier
