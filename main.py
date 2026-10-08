"""
galIMVmini - Lightweight AI Image Metadata Inspector & Gallery.
Entry point for the Python package.
"""

import sys
import os

# Add package directory to sys.path
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont

from core.theme import ThemeManager
from ui.main_window import MainWindow

def main():
    # Enable high DPI
    app = QApplication(sys.argv)
    app.setApplicationName("galIMVmini")
    app.setOrganizationName("galIMV")
    app.setFont(QFont("Segoe UI", 9))

    # Set icon
    icon_path = os.path.join(package_dir, "resources", "app.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    # If arguments supplied, load target file or directory
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isfile(target):
            QTimer.singleShot(50, lambda: window.load_image(target))
        elif os.path.isdir(target):
            # Find first image in directory
            for root, _, files in os.walk(target):
                for f in sorted(files):
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")):
                        first_img = os.path.join(root, f)
                        QTimer.singleShot(50, lambda: window.load_image(first_img))
                        break
                break

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
