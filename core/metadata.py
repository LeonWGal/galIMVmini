"""
galIMVmini High-Performance Image Metadata Reader.
Parses Stable Diffusion (A1111/Forge/WebUI), ComfyUI, NovelAI, Fooocus,
InvokeAI, EXIF (Camera, Lens, GPS), and sidecar .txt files.
"""

import os
import zlib
import struct
import json
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any

from PIL import Image, ExifTags
try:
    from core.tags import TagClassifier, get_tag_classifier
except ImportError:
    from galIMVmini.core.tags import TagClassifier, get_tag_classifier

@dataclass
class ImageMetadata:
    file_path: str = ""
    file_name: str = ""
    dir_path: str = ""
    file_size_bytes: int = 0
    file_size_str: str = ""
    created_time: str = ""
    modified_time: str = ""
    
    # Image properties
    width: int = 0
    height: int = 0
    aspect_ratio: float = 1.0
    aspect_ratio_str: str = ""
    image_format: str = ""
    color_mode: str = ""
    megapixels: str = ""
    
    # AI Generation properties
    prompt: str = ""
    negative_prompt: str = ""
    model_name: str = ""
    model_hash: str = ""
    sampler: str = ""
    steps: str = ""
    cfg_scale: str = ""
    seed: str = ""
    denoise: str = ""
    clip_skip: str = ""
    loras: List[Tuple[str, str]] = field(default_factory=list)
    tags: List[Tuple[str, int]] = field(default_factory=list) # (tag_name, category_id)
    
    # Sidecar file info
    sidecar_path: Optional[str] = None
    sidecar_text: Optional[str] = None
    
    # Parameter breakdown & categorized tables
    generation_params: Dict[str, str] = field(default_factory=dict)
    parsed_extensions: Dict[str, Dict[str, str]] = field(default_factory=dict)
    categories: Dict[str, Dict[str, str]] = field(default_factory=dict)
    raw_texts: Dict[str, str] = field(default_factory=dict)
    has_ai_metadata: bool = False


class MetadataReader:
    MAX_CHUNK_BYTES = 25 * 1024 * 1024  # 25 MB max metadata payload

    @staticmethod
    def calculate_aspect_ratio(w: int, h: int) -> str:
        if not w or not h:
            return ""
        import math
        g = math.gcd(w, h)
        rw = w // g
        rh = h // g
        ratio = w / h
        standards = [
            (1.0, "1:1"),
            (16/9, "16:9"),
            (9/16, "9:16"),
            (4/3, "4:3"),
            (3/4, "3:4"),
            (3/2, "3:2"),
            (2/3, "2:3"),
            (21/9, "21:9"),
            (9/21, "9:21"),
            (5/4, "5:4"),
            (4/5, "4:5"),
        ]
        for r_val, r_str in standards:
            if abs(ratio - r_val) < 0.04:
                if rw < 25 and rh < 25 and f"{rw}:{rh}" != r_str:
                    return f"{rw}:{rh} (~{r_str})"
                return r_str
        if rw < 25 and rh < 25:
            return f"{rw}:{rh}"
        return f"{ratio:.2f}:1"

    @classmethod
    def read_metadata(cls, file_path: str) -> ImageMetadata:
        meta = ImageMetadata()
        meta.file_path = os.path.abspath(file_path)
        meta.file_name = os.path.basename(file_path)
        meta.dir_path = os.path.dirname(meta.file_path)

        if not os.path.exists(file_path):
            return meta

        # 1. File system stats
        try:
            stat = os.stat(file_path)
            meta.file_size_bytes = stat.st_size
            meta.file_size_str = cls._format_file_size(stat.st_size)
            meta.created_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            meta.modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        # 2. Check for sidecar .txt file
        cls._check_sidecar_txt(file_path, meta)

        # 3. Direct binary PNG chunk reading (handles compressed zTXt/iTXt without Pillow truncation)
        ext = os.path.splitext(file_path)[1].lower()
        png_texts: Dict[str, str] = {}
        if ext == ".png":
            png_texts = cls._parse_png_chunks(file_path, meta)

        # 4. Pillow inspection for dimensions, format, EXIF, and non-PNG files
        pillow_info = cls._read_with_pillow(file_path, meta)

        # Combine text dictionaries
        all_texts = {**png_texts, **pillow_info}
        meta.raw_texts = all_texts

        # 5. Parse AI generation metadata
        cls._parse_ai_generation(all_texts, meta)

        # 6. If no prompt in metadata, check sidecar text
        if not meta.prompt and meta.sidecar_text:
            meta.prompt = meta.sidecar_text
            meta.has_ai_metadata = True

        # 7. Extract Tags and LoRAs from prompt
        if meta.prompt:
            meta.tags = TagClassifier.extract_tags(meta.prompt)
            meta.loras = TagClassifier.extract_loras(meta.prompt)

        # 8. Build structured categories for table inspector
        cls._build_categories(meta)

        return meta

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        if size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        return f"{size_bytes} Bytes"

    @classmethod
    def _check_sidecar_txt(cls, file_path: str, meta: ImageMetadata):
        base, _ = os.path.splitext(file_path)
        txt_path = base + ".txt"
        if os.path.exists(txt_path):
            try:
                meta.sidecar_path = txt_path
                with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                if content:
                    meta.sidecar_text = content
            except Exception:
                pass

    @classmethod
    def _parse_png_chunks(cls, file_path: str, meta: ImageMetadata) -> Dict[str, str]:
        texts: Dict[str, str] = {}
        try:
            with open(file_path, "rb") as f:
                sig = f.read(8)
                if sig != b"\x89PNG\r\n\x1a\n":
                    return texts

                while True:
                    header = f.read(8)
                    if len(header) < 8:
                        break
                    length, chunk_type = struct.unpack(">I4s", header)
                    chunk_name = chunk_type.decode("latin1", errors="ignore")

                    if chunk_name == "IEND":
                        break

                    if chunk_name == "IHDR" and length >= 8:
                        data = f.read(length)
                        f.read(4)  # CRC
                        w, h = struct.unpack(">II", data[:8])
                        if w > 0 and h > 0:
                            meta.width = w
                            meta.height = h
                            meta.aspect_ratio = round(w / h, 4)
                            meta.aspect_ratio_str = cls.calculate_aspect_ratio(w, h)
                            meta.megapixels = f"{round((w * h) / 1000000.0, 2)} MP"
                        continue

                    if chunk_name in ("tEXt", "zTXt", "iTXt"):
                        if length > cls.MAX_CHUNK_BYTES:
                            f.seek(length + 4, os.SEEK_CUR)
                            continue
                        data = f.read(length)
                        f.read(4)  # CRC

                        parsed_key, parsed_val = cls._decode_png_text_chunk(chunk_name, data)
                        if parsed_key:
                            texts[parsed_key.lower()] = parsed_val
                    else:
                        f.seek(length + 4, os.SEEK_CUR)
        except Exception:
            pass
        return texts

    @classmethod
    def _decode_png_text_chunk(cls, chunk_type: str, data: bytes) -> Tuple[Optional[str], str]:
        try:
            sep = data.find(b"\x00")
            if sep <= 0:
                return None, ""
            keyword = data[:sep].decode("latin1", errors="ignore")
            payload = data[sep + 1:]

            if chunk_type == "tEXt":
                # A1111 commonly writes utf-8 into tEXt chunks
                try:
                    text = payload.decode("utf-8")
                except UnicodeDecodeError:
                    text = payload.decode("latin1", errors="ignore")
                return keyword, text

            elif chunk_type == "zTXt":
                if len(payload) < 2 or payload[0] != 0:
                    return keyword, ""
                decompressed = zlib.decompress(payload[1:])
                try:
                    text = decompressed.decode("utf-8")
                except UnicodeDecodeError:
                    text = decompressed.decode("latin1", errors="ignore")
                return keyword, text

            elif chunk_type == "iTXt":
                if len(payload) < 2:
                    return keyword, ""
                comp_flag = payload[0]
                comp_method = payload[1]
                idx = 2
                # Skip language tag
                lang_end = payload.find(b"\x00", idx)
                if lang_end < 0:
                    return keyword, ""
                idx = lang_end + 1
                # Skip translated keyword
                trans_end = payload.find(b"\x00", idx)
                if trans_end < 0:
                    return keyword, ""
                raw_content = payload[trans_end + 1:]
                if comp_flag == 1:
                    raw_content = zlib.decompress(raw_content)
                text = raw_content.decode("utf-8", errors="ignore")
                return keyword, text

        except Exception:
            pass
        return None, ""

    @classmethod
    def _read_with_pillow(cls, file_path: str, meta: ImageMetadata) -> Dict[str, str]:
        info_texts: Dict[str, str] = {}
        try:
            with Image.open(file_path) as img:
                if meta.width == 0 or meta.height == 0:
                    meta.width, meta.height = img.size
                    meta.aspect_ratio = round(meta.width / max(1, meta.height), 4)
                    meta.aspect_ratio_str = cls.calculate_aspect_ratio(meta.width, meta.height)
                    meta.megapixels = f"{round((meta.width * meta.height) / 1000000.0, 2)} MP"
                elif not meta.aspect_ratio_str and meta.width and meta.height:
                    meta.aspect_ratio_str = cls.calculate_aspect_ratio(meta.width, meta.height)
                meta.image_format = img.format or os.path.splitext(file_path)[1].upper().replace(".", "")
                meta.color_mode = img.mode

                # Read img.info
                for k, v in img.info.items():
                    if isinstance(v, (str, int, float, bool)):
                        info_texts[str(k).lower()] = str(v)
                    elif isinstance(v, bytes):
                        try:
                            info_texts[str(k).lower()] = v.decode("utf-8")
                        except Exception:
                            info_texts[str(k).lower()] = f"<binary data: {len(v)} bytes>"

                # Read EXIF
                try:
                    exif = img.getexif()
                    if exif:
                        for tag_id, val in exif.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            if tag_name == "UserComment" and isinstance(val, (str, bytes)):
                                comment_str = val.decode("utf-8", errors="ignore") if isinstance(val, bytes) else str(val)
                                if comment_str.startswith("UNICODE\x00"):
                                    comment_str = comment_str[8:]
                                info_texts["usercomment"] = comment_str.strip()
                            else:
                                if isinstance(val, bytes):
                                    val_str = f"<binary: {len(val)} bytes>"
                                else:
                                    val_str = str(val)
                                info_texts[f"exif_{tag_name.lower()}"] = val_str
                except Exception:
                    pass
        except Exception:
            pass
        return info_texts

    @classmethod
    def _parse_ai_generation(cls, texts: Dict[str, str], meta: ImageMetadata):
        # 1. ComfyUI check in "prompt" or "workflow"
        if "prompt" in texts:
            val = texts["prompt"].strip()
            if cls._parse_comfy_json(val, meta):
                meta.has_ai_metadata = True
                return

        # 2. NovelAI check in "comment"
        if "comment" in texts:
            val = texts["comment"].strip()
            if cls._parse_novelai_json(val, meta):
                meta.has_ai_metadata = True
                return

        # 3. Automatic1111 / WebUI / Forge in "parameters"
        param_text = texts.get("parameters") or texts.get("usercomment") or texts.get("description")
        if param_text and param_text.strip():
            # Sometimes JSON is placed in parameters
            stripped = param_text.strip()
            if stripped.startswith("{") and (cls._parse_comfy_json(stripped, meta) or cls._parse_novelai_json(stripped, meta)):
                meta.has_ai_metadata = True
                return

            if cls._parse_a1111_text(stripped, meta):
                meta.has_ai_metadata = True
                return

        # 4. Check other keys for SD prompt format
        for k in ("prompt", "workflow", "sd-metadata"):
            if k in texts and texts[k].strip():
                if cls._parse_a1111_text(texts[k].strip(), meta):
                    meta.has_ai_metadata = True
                    return

    @classmethod
    def _parse_comfy_json(cls, json_str: str, meta: ImageMetadata) -> bool:
        if not (json_str.startswith("{") and json_str.endswith("}")):
            return False
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return False

            # Check if NovelAI graph embedded inside
            if "prompt" in data and "uc" in data:
                meta.prompt = str(data.get("prompt", "")).strip()
                meta.negative_prompt = str(data.get("uc", "")).strip()
                meta.steps = str(data.get("steps", ""))
                meta.sampler = str(data.get("sampler", ""))
                meta.seed = str(data.get("seed", ""))
                meta.cfg_scale = str(data.get("scale", ""))
                return True

            positives: List[str] = []
            negatives: List[str] = []
            is_comfy = False

            def collect_text(node_id: str, visited: set) -> List[str]:
                if node_id in visited or len(visited) > 200:
                    return []
                visited.add(node_id)
                node = data.get(node_id, {})
                if not isinstance(node, dict):
                    return []
                inputs = node.get("inputs", {})
                if not isinstance(inputs, dict):
                    return []
                res = []
                for key in ("text", "text_g", "text_l", "prompt"):
                    val = inputs.get(key)
                    if isinstance(val, str) and val.strip():
                        res.append(val.strip())
                    elif isinstance(val, list) and val:
                        res.extend(collect_text(str(val[0]), visited))
                for k, v in inputs.items():
                    if isinstance(v, list) and v and str(v[0]) not in visited:
                        res.extend(collect_text(str(v[0]), visited))
                return res

            for node_id, node in data.items():
                if not isinstance(node, dict):
                    continue
                class_type = node.get("class_type", "")
                inputs = node.get("inputs", {})
                if not isinstance(inputs, dict):
                    continue

                if "KSampler" in class_type or "Sampler" in class_type:
                    is_comfy = True
                    # Seed, Steps, CFG, Sampler
                    if "seed" in inputs:
                        meta.seed = str(inputs["seed"])
                    if "steps" in inputs:
                        meta.steps = str(inputs["steps"])
                    if "cfg" in inputs:
                        meta.cfg_scale = str(inputs["cfg"])
                    if "sampler_name" in inputs:
                        meta.sampler = str(inputs["sampler_name"])
                    if "denoise" in inputs:
                        meta.denoise = str(inputs["denoise"])

                    # Positive link
                    pos_link = inputs.get("positive")
                    if isinstance(pos_link, list) and pos_link:
                        positives.extend(collect_text(str(pos_link[0]), set()))

                    # Negative link
                    neg_link = inputs.get("negative")
                    if isinstance(neg_link, list) and neg_link:
                        negatives.extend(collect_text(str(neg_link[0]), set()))

                elif "CheckpointLoader" in class_type or "model" in class_type.lower():
                    ckpt = inputs.get("ckpt_name") or inputs.get("model_name")
                    if ckpt and isinstance(ckpt, str):
                        meta.model_name = cls.clean_model_name(ckpt)

                elif "EmptyLatentImage" in class_type:
                    w = inputs.get("width")
                    h = inputs.get("height")
                    if w and h:
                        meta.generation_params["Latent Size"] = f"{w}x{h}"

            if is_comfy:
                # Deduplicate
                pos_unique = []
                for p in positives:
                    if p not in pos_unique:
                        pos_unique.append(p)
                neg_unique = []
                for n in negatives:
                    if n not in neg_unique:
                        neg_unique.append(n)

                meta.prompt = "\n".join(pos_unique)
                meta.negative_prompt = "\n".join(neg_unique)
                meta.generation_params["System"] = "ComfyUI"
                if meta.model_name:
                    meta.generation_params["Model"] = meta.model_name
                if meta.seed:
                    meta.generation_params["Seed"] = meta.seed
                if meta.steps:
                    meta.generation_params["Steps"] = meta.steps
                if meta.sampler:
                    meta.generation_params["Sampler"] = meta.sampler
                if meta.cfg_scale:
                    meta.generation_params["CFG scale"] = meta.cfg_scale
                return True

        except Exception:
            pass
        return False

    @classmethod
    def _parse_novelai_json(cls, json_str: str, meta: ImageMetadata) -> bool:
        if not (json_str.startswith("{") and json_str.endswith("}")):
            return False
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return False
            if "prompt" in data or "uc" in data:
                meta.prompt = str(data.get("prompt", "")).strip()
                meta.negative_prompt = str(data.get("uc", "")).strip()
                meta.steps = str(data.get("steps", ""))
                meta.sampler = str(data.get("sampler", ""))
                meta.seed = str(data.get("seed", ""))
                meta.cfg_scale = str(data.get("scale", ""))
                meta.generation_params["System"] = "NovelAI"
                if meta.steps:
                    meta.generation_params["Steps"] = meta.steps
                if meta.seed:
                    meta.generation_params["Seed"] = meta.seed
                if meta.sampler:
                    meta.generation_params["Sampler"] = meta.sampler
                if meta.cfg_scale:
                    meta.generation_params["Scale"] = meta.cfg_scale
                return True
        except Exception:
            pass
        return False

    @classmethod
    def _parse_parameter_string(cls, text: str) -> List[Tuple[str, str]]:
        """
        Tokenizes parameter text into (key, value) pairs.
        Accurately respects:
        - Commas and newlines as delimiters
        - JSON braces { ... } without splitting inside them
        - Brackets [ ... ]
        - Quotes " ... "
        """
        pairs: List[Tuple[str, str]] = []
        if not text:
            return pairs

        in_quotes = False
        brace_depth = 0
        bracket_depth = 0
        current_key: List[str] = []
        current_val: List[str] = []
        reading_key = True

        i = 0
        n = len(text)

        while i < n:
            ch = text[i]

            # Quote toggling (accounting for escaped quotes)
            if ch == '"' and (i == 0 or text[i - 1] != '\\'):
                in_quotes = not in_quotes
                if reading_key:
                    current_key.append(ch)
                else:
                    current_val.append(ch)
                i += 1
                continue

            if in_quotes:
                if reading_key:
                    current_key.append(ch)
                else:
                    current_val.append(ch)
                i += 1
                continue

            # Nested scopes
            if ch == '{':
                brace_depth += 1
                current_val.append(ch)
                i += 1
                continue
            elif ch == '}':
                if brace_depth > 0:
                    brace_depth -= 1
                current_val.append(ch)
                i += 1
                continue
            elif ch == '[':
                bracket_depth += 1
                current_val.append(ch)
                i += 1
                continue
            elif ch == ']':
                if bracket_depth > 0:
                    bracket_depth -= 1
                current_val.append(ch)
                i += 1
                continue

            # At top level outside any quotes/braces
            if brace_depth == 0 and bracket_depth == 0:
                if reading_key:
                    if ch == ':':
                        reading_key = False
                        i += 1
                        if i < n and text[i] == ' ':
                            i += 1
                        continue
                    elif ch == '\n':
                        current_key = []
                        i += 1
                        continue
                    else:
                        current_key.append(ch)
                        i += 1
                        continue
                else:
                    # Reading value: check if delimiter marks next key
                    if ch in (',', '\n'):
                        rest = text[i + 1:]
                        # Look ahead for a ':' indicating the next key
                        colon_pos = -1
                        quote_ahead = False
                        for j, c in enumerate(rest):
                            if c == '"':
                                quote_ahead = not quote_ahead
                            if quote_ahead:
                                continue
                            if c == ':':
                                colon_pos = j
                                break
                            if c == '\n':
                                break

                        if colon_pos != -1:
                            k_str = "".join(current_key).strip().strip(',').strip()
                            v_str = "".join(current_val).strip().strip(',').strip()
                            if k_str:
                                pairs.append((k_str, v_str))
                            current_key = []
                            current_val = []
                            reading_key = True
                            i += 1
                            continue
                        else:
                            current_val.append(ch)
                            i += 1
                            continue

            if reading_key:
                current_key.append(ch)
            else:
                current_val.append(ch)
            i += 1

        k_str = "".join(current_key).strip().strip(',').strip()
        v_str = "".join(current_val).strip().strip(',').strip()
        if k_str:
            pairs.append((k_str, v_str))

        return pairs

    @classmethod
    def _parse_a1111_text(cls, text: str, meta: ImageMetadata) -> bool:
        if not text:
            return False

        neg_marker = "Negative prompt:"
        neg_pos = text.find(neg_marker)

        # Locate parameter block (starts with Steps: or Steps:\s*\d+)
        steps_match = re.search(r'(?:^|\n)\s*(Steps:\s*\d+.*)', text, re.DOTALL)

        if neg_pos != -1:
            meta.prompt = text[:neg_pos].strip()
            if steps_match and steps_match.start(1) > neg_pos:
                steps_pos = steps_match.start(1)
                meta.negative_prompt = text[neg_pos + len(neg_marker):steps_pos].strip()
                params_part = text[steps_pos:].strip()
            else:
                meta.negative_prompt = text[neg_pos + len(neg_marker):].strip()
                params_part = ""
        else:
            if steps_match:
                steps_pos = steps_match.start(1)
                meta.prompt = text[:steps_pos].strip()
                meta.negative_prompt = ""
                params_part = text[steps_pos:].strip()
            else:
                meta.prompt = text.strip()
                meta.negative_prompt = ""
                params_part = ""

        if params_part:
            pairs = cls._parse_parameter_string(params_part)
            for k_str, v_str in pairs:
                meta.generation_params[k_str] = v_str

                k_lower = k_str.lower()
                if k_lower == "steps":
                    meta.steps = v_str
                elif k_lower == "sampler":
                    meta.sampler = v_str
                elif k_lower in ("cfg scale", "cfg"):
                    meta.cfg_scale = v_str
                elif k_lower == "seed":
                    meta.seed = v_str
                elif k_lower == "model":
                    meta.model_name = cls.clean_model_name(v_str)
                elif k_lower == "model hash":
                    meta.model_hash = v_str
                elif k_lower in ("denoising strength", "denoise"):
                    meta.denoise = v_str
                elif k_lower == "clip skip":
                    meta.clip_skip = v_str

                # Parse JSON if detected (such as TIPO Parameters)
                if "tipo" in k_lower or (v_str.startswith("{") and v_str.endswith("}")):
                    try:
                        data = json.loads(v_str)
                        if isinstance(data, dict):
                            tipo_dict = {}
                            if "model" in data: tipo_dict["Model"] = str(data["model"])
                            if "temperature" in data: tipo_dict["Temperature"] = str(data["temperature"])
                            if "top_p" in data: tipo_dict["Top P"] = str(data["top_p"])
                            if "top_k" in data: tipo_dict["Top K"] = str(data["top_k"])
                            if "typical_p" in data and str(data["typical_p"]) != "1": tipo_dict["Typical P"] = str(data["typical_p"])
                            if "seed" in data: tipo_dict["Seed"] = str(data["seed"])
                            if "tag_length" in data:
                                min_len = data.get("tag_length_min", "")
                                max_len = data.get("tag_length_max", "")
                                if min_len or max_len:
                                    tipo_dict["Tag Length"] = f"{data['tag_length']} ({min_len}–{max_len})"
                                else:
                                    tipo_dict["Tag Length"] = str(data["tag_length"])
                            if "format" in data or "tags_format" in data:
                                tipo_dict["Format"] = str(data.get("tags_format") or data.get("format"))
                            if "mode" in data: tipo_dict["Mode"] = str(data["mode"])
                            if data.get("ban_tags"): tipo_dict["Ban Tags"] = str(data["ban_tags"])
                            if data.get("nl_prompt"): tipo_dict["NL Prompt"] = str(data["nl_prompt"])
                            meta.parsed_extensions["TIPO"] = tipo_dict
                    except Exception:
                        pass

            return True

        return bool(meta.prompt)

    @classmethod
    def clean_model_name(cls, model: str) -> str:
        base = os.path.basename(model.replace("\\", "/"))
        for ext in (".safetensors", ".ckpt", ".pt", ".bin"):
            if base.lower().endswith(ext):
                base = base[:-len(ext)]
        return base

    @classmethod
    def _build_categories(cls, meta: ImageMetadata):
        # 1. Prompt (Positive)
        if meta.prompt:
            meta.categories["Prompt"] = {"Positive Prompt": meta.prompt}

        # 2. Negative Prompt
        if meta.negative_prompt:
            meta.categories["Negative Prompt"] = {"Negative Prompt": meta.negative_prompt}

        # 3. Core Generation Parameters
        if meta.generation_params or meta.steps or meta.sampler or meta.seed:
            gen_params: Dict[str, str] = {}
            if meta.steps:
                gen_params["Steps"] = meta.steps
            if meta.sampler:
                sampler_display = meta.sampler
                sched = meta.generation_params.get("Schedule type", "")
                if sched and sched.lower() not in sampler_display.lower():
                    sampler_display = f"{sampler_display} ({sched})"
                gen_params["Sampler"] = sampler_display
            if meta.cfg_scale:
                gen_params["CFG scale"] = meta.cfg_scale
            if meta.seed:
                gen_params["Seed"] = meta.seed
            size_val = meta.generation_params.get("Size") or (f"{meta.width} × {meta.height}" if meta.width else "")
            if size_val:
                gen_params["Size"] = size_val
            if meta.denoise:
                gen_params["Denoising strength"] = meta.denoise
            if meta.clip_skip:
                gen_params["Clip skip"] = meta.clip_skip
            for hk in ("Hires upscale", "Hires steps", "Hires upscaler", "RNG", "ENSD", "Schedule type"):
                if hk in meta.generation_params and hk not in gen_params:
                    gen_params[hk] = meta.generation_params[hk]

            if gen_params:
                meta.categories["Generation Parameters"] = gen_params

        # 4. Model Info
        model_info: Dict[str, str] = {}
        if meta.model_name:
            model_info["Model"] = meta.model_name
        if meta.model_hash:
            model_info["Model hash"] = meta.model_hash
        for mk in ("VAE", "VAE hash", "Lora hashes", "TI hashes", "Version"):
            if mk in meta.generation_params:
                model_info[mk] = meta.generation_params[mk]
        if model_info:
            meta.categories["Model Info"] = model_info

        # 5. Extensions (ADetailer, TIPO, ControlNet, etc.)
        ext_info: Dict[str, str] = {}
        # Structured TIPO
        if "TIPO" in meta.parsed_extensions:
            for tk, tv in meta.parsed_extensions["TIPO"].items():
                if tv:
                    ext_info[f"TIPO {tk}"] = tv
        # ADetailer & other extensions
        for k, v in meta.generation_params.items():
            k_low = k.lower()
            if "adetailer" in k_low:
                ext_info[k] = v
            elif "tipo" in k_low and "TIPO" not in meta.parsed_extensions:
                ext_info[k] = v
            elif "controlnet" in k_low or "freeu" in k_low:
                ext_info[k] = v
        if ext_info:
            meta.categories["Extensions"] = ext_info

        # 6. Other / Extra Parameters
        handled_keys = {
            "steps", "sampler", "schedule type", "cfg scale", "cfg", "seed", "size",
            "denoising strength", "denoise", "clip skip", "model", "model hash",
            "vae", "vae hash", "lora hashes", "ti hashes", "version", "hires upscale",
            "hires steps", "hires upscaler", "rng", "ensd", "system"
        }
        other_params: Dict[str, str] = {}
        for k, v in meta.generation_params.items():
            k_low = k.lower()
            if k_low not in handled_keys and not any(x in k_low for x in ("adetailer", "tipo", "controlnet", "freeu")):
                other_params[k] = v
        if other_params:
            meta.categories["Other Parameters"] = other_params

        # 7. File Info
        file_info: Dict[str, str] = {
            "Filename": meta.file_name,
            "Folder": meta.dir_path,
            "File size": meta.file_size_str,
            "Created": meta.created_time,
            "Modified": meta.modified_time,
        }
        if meta.sidecar_path:
            file_info["Sidecar .txt"] = os.path.basename(meta.sidecar_path)
        meta.categories["File Info"] = file_info

        # 8. Image Properties
        props: Dict[str, str] = {
            "Dimensions": f"{meta.width} × {meta.height} px" if meta.width and meta.height else "Unknown",
            "Aspect Ratio": meta.aspect_ratio_str or (f"{meta.aspect_ratio}:1" if meta.aspect_ratio else "1:1"),
            "Megapixels": meta.megapixels or "Unknown",
            "Format": meta.image_format or "Unknown",
            "Color Mode": meta.color_mode or "Unknown",
        }
        meta.categories["Image Properties"] = props

        # 9. Camera EXIF
        camera_info: Dict[str, str] = {}
        gps_info: Dict[str, str] = {}
        other_exif: Dict[str, str] = {}

        for k, v in meta.raw_texts.items():
            if k.startswith("exif_"):
                tag = k[5:]
                if tag in ("make", "model", "lensmodel", "lensinfo", "focal_length", "focallength",
                           "fnumber", "exposuretime", "isospeedratings", "software", "flash", "whitebalance"):
                    camera_info[tag.title()] = v
                elif "gps" in tag:
                    gps_info[tag.title()] = v
                else:
                    other_exif[tag.title()] = v

        if camera_info:
            meta.categories["Camera Info"] = camera_info
        if gps_info:
            meta.categories["GPS Data"] = gps_info
        if other_exif:
            meta.categories["Other EXIF"] = other_exif
