"""
galIMVmini Package
Version: 1.0.0
High-Performance AI Gallery & Metadata Inspector (Lightweight Edition)
"""

import sys
import os

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

__version__ = "1.0.0"
