# galIMVmini

<p align="center">
  <strong>Lightweight AI Image Metadata Inspector & Viewer in the spirit of galIMV</strong><br>
  <em>High-performance prompt extraction, sleek Lobe Hub Neo aesthetics, 100% vector Tabler icons, aspect-ratio analysis, and full 20-language internationalization.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PyQt6"/>
  <img src="https://img.shields.io/badge/Design-Lobe%20Hub%20Neo-1677ff?style=flat-square" alt="Lobe Hub Neo"/>
  <img src="https://img.shields.io/badge/Icons-Tabler%20Icons-0ea5e9?style=flat-square" alt="Tabler Icons"/>
  <img src="https://img.shields.io/badge/Languages-20%20Locales-purple?style=flat-square" alt="20 Languages"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License MIT"/>
</p>

---

## 🌟 Overview

**galIMVmini** is a minimalist, ultra-responsive desktop application engineered specifically for viewing AI-generated artworks and inspecting detailed generation metadata. It brings the refined visual identity and powerful parsing capabilities of **galIMV** into a lightweight, focused tool.

Whether you are organizing Stable Diffusion outputs, exploring ComfyUI node workflows, or verifying image aspect ratios, galIMVmini delivers an instantaneous, clutter-free experience.

---

## ✨ Features

### 🔍 Comprehensive AI Metadata Parsing
- **Stable Diffusion (Automatic1111, WebUI Forge, SD.Next)**: Positive/negative prompts, model checkpoint, hash, sampler, steps, CFG scale, seed, denoise strength, and clip skip.
- **Advanced Forge / TIPO / ADetailer**: Automatically detects and structures complex extension outputs into readable badges.
- **ComfyUI**: Traverses recursive node graphs (`KSampler`, `CLIPTextEncode`, `CheckpointLoaderSimple`, latent dimensions, upscalers).
- **NovelAI & Fooocus**: Embedded JSON metadata extraction and parsing.
- **Midjourney & EXIF**: Extracts camera parameters, dimensions, megapixels, color profiles, timestamps, and PNG text chunks.
- **Sidecar Files (`.txt`)**: Seamlessly reads paired text files; automatically hides sidecar sections when not present to save vertical screen space.

### 📐 Aspect Ratio Analysis
- Real-time aspect ratio computation with smart recognition of standard photography, cinema, and display proportions:
  - `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `21:9`, `5:4`, `7:4 (~16:9)`
- Highlighted badge in Prompt Parameters, window title, and status bar.

### 🎨 galIMV Design System (Lobe Hub Neo)
- **100% Vector Tabler Icons**: Crisp, modern iconography across all pixel densities with zero emoji dependencies.
- **Aspect Ratio & 100% Real Size Icon**: Dedicated Tabler `aspect-ratio` button for resetting to 100% natural resolution.
- **Calibrated Themes & Persistence**: Seamless switching between Dark (`#18181b`) and Light (`#ffffff`) themes, with automatic saving of theme mode, accent, and language.
- **6 Lobe Accent Colors**: Lobe Blue (`#1677ff`), Lobe Purple (`#722ed1`), Emerald (`#10b981`), Orange (`#fa8c16`), Rose (`#f43f5e`), and Zinc (`#71717a`).
- **50 / 50 Balanced Layout**: Default equal proportion between image canvas and inspector with flexible draggable splitter.

### 🖥️ Fullscreen & Performance
- **Fullscreen Mode**: Toggle via `F11`, with instant `Esc` exit.
- **Compact Maximized Layout**: Card frames, prompt boxes, and tabs stay snug and proportional without bloated margins or vertical empty space.
- **Auto Canvas Refit**: Automatically recenters and scales image smoothly upon entering or exiting fullscreen mode.
- **High Responsiveness**: Optimized rendering with `SmartViewportUpdate`, resize caching on text labels, and batched table updates.

### 🌐 20 Languages Supported (i18n)
Full internationalization parity with **galIMV**. Switch instantly on the fly:
| Language | Code | Language | Code |
| :--- | :--- | :--- | :--- |
| **Русский** (Russian) | `ru_RU` | **Italiano** (Italian) | `it_IT` |
| **English** | `en_US` | **Polski** (Polish) | `pl_PL` |
| **简体中文** (Simplified Chinese) | `zh_CN` | **Türkçe** (Turkish) | `tr_TR` |
| **繁體中文** (Traditional Chinese) | `zh_TW` | **Українська** (Ukrainian) | `uk_UA` |
| **日本語** (Japanese) | `ja_JP` | **Nederlands** (Dutch) | `nl_NL` |
| **한국어** (Korean) | `ko_KR` | **Bahasa Indonesia** | `id_ID` |
| **Deutsch** (German) | `de_DE` | **Tiếng Việt** (Vietnamese) | `vi_VN` |
| **Français** (French) | `fr_FR` | **ไทย** (Thai) | `th_TH` |
| **Español** (Spanish) | `es_ES` | **العربية** (Arabic) | `ar_SA` |
| **Português (Brasil)** | `pt_BR` | **हिन्दी** (Hindi) | `hi_IN` |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **Ctrl + O** | Open image file |
| **Ctrl + H** | Open recent files history |
| **Ctrl + C** | Copy positive prompt |
| **Ctrl + E** | Export metadata (TXT, Markdown, JSON, CSV) |
| **0** | Fit image to window |
| **1** | 100% Original Size (Real Size) |
| **+** / **-** | Zoom In / Zoom Out |
| **Mouse Wheel** | Smooth zoom centered on cursor |
| **Left Click + Drag** | Pan image |
| **I** | Show / Hide Inspector panel |
| **F11** | Toggle Fullscreen mode |
| **Esc** | Exit Fullscreen mode |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Windows 10 / 11 (or Linux / macOS with Qt6)

### Installation
```bash
git clone https://github.com/your-username/galIMVmini.git
cd galIMVmini
pip install -r requirements.txt
```

### Running the App
```bash
python main.py
```
*Or simply double-click `run.bat` on Windows.*

---

## 📦 Building Standalone Executable (Windows)

You can build a standalone, portable Windows `.exe` using PyInstaller:

```bash
# Build portable distribution folder (fast startup)
python build_exe.py

# Or build single-file standalone executable
python build_exe.py --onefile
```

*Or run `build_exe.bat`.* The output will be generated inside the `dist/` directory.

---

## 📂 Project Structure

```
galIMVmini/
├── core/
│   ├── i18n.py          # 20-language internationalization engine
│   ├── icons.py         # Tabler SVG vector icon repository
│   ├── metadata.py      # AI metadata parser & aspect ratio engine
│   └── theme.py         # Lobe Hub Neo theme and palette manager
├── ui/
│   ├── image_canvas.py  # Optimized QGraphicsView canvas
│   ├── prompt_card.py   # Compact prompt & parameters inspector card
│   ├── metadata_table.py# Categorized metadata property table
│   ├── raw_view.py      # Raw text / JSON viewer
│   └── main_window.py   # Main window with galIMV toolbar & layout
├── locales/             # 20 JSON language translations
├── resources/           # Application icon (app.ico)
├── build_exe.py         # PyInstaller distribution build script
├── build_exe.bat        # Windows build helper script
├── main.py              # Application entry point
├── requirements.txt     # Python package dependencies
├── LICENSE              # MIT License
└── README.md            # Project documentation
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
