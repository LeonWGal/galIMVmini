# galIMVmini 1.2.0

Windows x64 release · 2026-10-25

Inspect an image, its prompts, and its metadata in one window with a compact interface that matches galIMV.

## Downloads

- **galIMVmini-1.2.0-Windows-x64.exe** — standalone executable with Python, PyQt6, resources, and translations included. Run it directly.
- **galIMVmini-1.2.0-Windows-x64-Portable.zip** — extract the whole archive and run `galIMVmini.exe`. This folder build avoids unpacking the runtime at every launch.
- **SHA256SUMS.txt** — SHA-256 checksums for the downloadable files.

## Added

- Twelve Lobe accents and window/taskbar icons that follow the selected accent.
- Shared contour branding and Tabler icons with galIMV, with opaque surfaces and a compact layout.
- Localized metadata categories, field names, export headings, and file filters.

## Changed

- Selected JSON translations take priority over compatibility dictionaries.
- Settings and temporary data use LeonWGal application folders.
- English and Russian READMEs include interface screenshots and launch instructions.

## Fixed

- All 20 catalogs have matching keys and preserved format parameters.
- Language changes update tabs, tooltips, counters, and metadata headings.
- Shortcut tooltips no longer repeat key combinations; word/parameter counts use localized labels.

## Проверка и запуск

Тесты интерфейса и локализации проходят; переключение всех 20 языков проверено с загруженным изображением. Запустите отдельный EXE либо распакуйте ZIP и откройте `galIMVmini.exe`. Устанавливать Python и PyQt6 отдельно не требуется.
