"""
Automated functional verification test for galIMVmini.
Covers core metadata reading, WebUI Forge / TIPO / ADetailer parsing,
categorized metadata tables, responsive layout, theme switching, and zoom controls.
"""

import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add galIMVmini root to path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.abspath(os.path.join(root_dir, "..")))

from PyQt6.QtWidgets import QApplication
try:
    from ui.main_window import MainWindow
    from core.theme import ThemeManager
    from core.metadata import MetadataReader, ImageMetadata
except ImportError:
    from galIMVmini.ui.main_window import MainWindow
    from galIMVmini.core.theme import ThemeManager
    from galIMVmini.core.metadata import MetadataReader, ImageMetadata

def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    
    print("1. Initializing MainWindow...")
    window = MainWindow()
    window.show()
    assert window is not None
    print("   MainWindow initialized successfully.")

    candidates = [
        os.path.abspath("../ImageViewer/test_gallery/anime_portrait_girl.png"),
        os.path.abspath("c:/Users/User/ImageViewer/test_gallery/anime_portrait_girl.png"),
    ]
    test_img = next((p for p in candidates if os.path.exists(p)), candidates[-1])
    window.load_image(test_img)
    
    meta = window._current_meta
    assert meta is not None, "Metadata object must not be None"
    assert "1girl" in meta.prompt, f"Expected '1girl' in prompt, got '{meta.prompt}'"
    assert "worst quality" in meta.negative_prompt, f"Expected negative prompt, got '{meta.negative_prompt}'"
    assert meta.model_name == "anime_diffusion_v1.5", f"Expected model name, got '{meta.model_name}'"
    assert "Prompt" in meta.categories, "Prompt must be present in categories"
    assert "Generation Parameters" in meta.categories, "Generation Parameters must be in categories"
    assert "Model Info" in meta.categories, "Model Info must be in categories"
    print(f"   Loaded: {meta.file_name}")
    print(f"   Dimensions: {meta.width}x{meta.height}")
    print(f"   Prompt: {meta.prompt}")
    print(f"   Negative: {meta.negative_prompt}")
    print(f"   Model: {meta.model_name}")

    print("3. Testing Prompt Inspector Card Structure & Visibility...")
    pc = window._prompt_card
    assert pc._prompt_frame.isVisible(), "Prompt frame should be visible"
    assert pc._neg_frame.isVisible(), "Negative prompt frame should be visible"
    assert pc._params_frame.isVisible(), "Params frame should be visible"
    # Sidecar should be HIDDEN because no .txt file exists next to test image
    assert not pc._sidecar_frame.isVisible(), "Sidecar frame should be hidden when no .txt exists"
    print("   Prompt and Negative prompt properly displayed.")
    print("   Missing sidecar properly hidden.")

    print("4. Testing WebUI Forge / TIPO / ADetailer Advanced Parsing...")
    forge_chunk = '''SagePXL, orange_hair, long_hair, 1girl, score_9
Negative prompt: child, childish, loli
Steps: 50, Sampler: DPM++ 2S a, Schedule type: Karras, CFG scale: 7, Seed: 726097149, Size: 832x1216, Model hash: ac006fdd7e, Model: autismmixSDXL, Denoising strength: 0.75, ADetailer model: face_yolov8n.pt, ADetailer confidence: 0.3, ADetailer version: 24.9.0, TIPO Parameters: {"model": "KBlueLeaf/TIPO-500M-ft2", "temperature": 0.8, "top_p": 0.95, "top_k": 50, "typical_p": 1, "ban_tags": "", "nl_prompt": false, "invert_tags": false, "tag_length": "medium", "tag_length_min": 15, "tag_length_max": 80, "seed": 2043651167, "format": "tags", "k_split": 0, "order": "group", "mode": "format", "tags_format": "danbooru", "prompt": "SagePXL, orange_hair"}, Lora hashes: "SagePXL: 8f47d08117dc", Version: v1.9.4'''

    forge_meta = ImageMetadata()
    forge_meta.file_name = "sample_forge.png"
    forge_meta.width = 832
    forge_meta.height = 1216
    forge_meta.raw_texts["parameters"] = forge_chunk

    MetadataReader._parse_ai_generation({"parameters": forge_chunk}, forge_meta)
    MetadataReader._build_categories(forge_meta)

    assert forge_meta.prompt.startswith("SagePXL"), "Prompt should start with SagePXL"
    assert forge_meta.negative_prompt == "child, childish, loli"
    assert forge_meta.steps == "50"
    assert forge_meta.sampler == "DPM++ 2S a"
    assert forge_meta.model_name == "autismmixSDXL"
    assert "TIPO" in forge_meta.parsed_extensions, "TIPO must be extracted as structured extension"
    assert forge_meta.parsed_extensions["TIPO"]["Model"] == "KBlueLeaf/TIPO-500M-ft2"
    assert forge_meta.parsed_extensions["TIPO"]["Seed"] == "2043651167"
    assert "Extensions" in forge_meta.categories, "Extensions category must exist"
    print("   Forge, TIPO, and ADetailer metadata accurately extracted and categorized.")

    print("5. Testing 50/50 Default Proportion & Splitter...")
    sizes = window._splitter.sizes()
    assert sizes[0] > 0 and sizes[1] > 0, "Both splitter sides must be visible"
    total_w = sizes[0] + sizes[1]
    ratio = sizes[0] / total_w
    assert 0.40 <= ratio <= 0.60, f"Splitter should be approximately 50/50, got {sizes[0]}:{sizes[1]}"
    print(f"   50/50 proportion verified: Canvas={sizes[0]}px, Inspector={sizes[1]}px (ratio={ratio:.2f})")

    print("6. Testing Theme System...")
    theme = ThemeManager.get_instance()
    initial_dark = theme.is_dark
    theme.toggle_dark_light()
    assert theme.is_dark != initial_dark
    theme.set_accent("Lobe Purple")
    assert theme.accent_name == "Lobe Purple"
    theme.toggle_dark_light() # Back to dark
    theme.set_accent("Lobe Blue")
    print("   Theme switching and accent selection verified.")

    print("7. Testing Zoom controls...")
    window._canvas.zoom_in()
    window._canvas.zoom_out()
    window._canvas.fit_to_window()
    window._canvas.set_original_size()
    print("   Zoom controls verified.")

    print("8. Testing Aspect Ratio Calculations...")
    assert MetadataReader.calculate_aspect_ratio(1920, 1080) == "16:9"
    assert MetadataReader.calculate_aspect_ratio(1080, 1920) == "9:16"
    assert MetadataReader.calculate_aspect_ratio(1024, 1024) == "1:1"
    assert MetadataReader.calculate_aspect_ratio(1200, 800) == "3:2"
    assert MetadataReader.calculate_aspect_ratio(800, 1200) == "2:3"
    assert MetadataReader.calculate_aspect_ratio(1024, 768) == "4:3"
    assert MetadataReader.calculate_aspect_ratio(768, 1024) == "3:4"
    assert MetadataReader.calculate_aspect_ratio(2560, 1080) == "21:9"
    assert MetadataReader.calculate_aspect_ratio(896, 512) == "7:4 (~16:9)"
    print("   Aspect ratio calculation verified for standard and close ratios.")

    print("9. Testing 20 Languages Internationalization (i18n)...")
    from galIMVmini.core.i18n import I18nManager, LOCALES
    i18n = I18nManager.get_instance()
    assert len(LOCALES) == 20, f"Expected 20 locales, got {len(LOCALES)}"
    for code, name in LOCALES:
        i18n.set_locale(code)
        assert i18n.get_locale() == code
        # Test basic translations
        tr_prompt = i18n.tr("tabs.prompt")
        assert tr_prompt != "", f"Empty translation for tabs.prompt in {code}"
    # Reset to ru_RU
    i18n.set_locale("ru_RU")
    print(f"   Successfully tested all {len(LOCALES)} locales.")

    print("10. Testing Tabler Icons...")
    from galIMVmini.core.icons import get_tabler_icon
    for icon_name in ["multiplier-1x", "fit-window", "maximize", "minimize", "world", "palette", "sun", "moon", "copy", "search"]:
        ico = get_tabler_icon(icon_name)
        assert not ico.isNull(), f"Icon '{icon_name}' should not be null"
    print("   Tabler SVG icons verified including multiplier-1x.")

    print("11. Testing Fullscreen Toggle...")
    assert not window.isFullScreen()
    window.toggle_fullscreen()
    # In offscreen mode, isFullScreen might not switch OS-level window, but method runs without exception
    window._exit_fullscreen()
    print("   Fullscreen toggle and exit executed cleanly.")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! ✓")

if __name__ == "__main__":
    run_tests()
