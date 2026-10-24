"""Application storage under the LeonWGal publisher directory."""
import os
import tempfile
from pathlib import Path
from PyQt6.QtCore import QSettings, QStandardPaths

def data_directory():
    override = os.environ.get("GALIMVMINI_DATA_DIR")
    if override:
        return Path(override)
    root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)
    return Path(root) / "LeonWGal" / "galIMVmini"

def configure_temporary_files():
    root = Path(tempfile.gettempdir())
    suffix = Path("LeonWGal") / "galIMVmini"
    path = root if tuple(p.lower() for p in root.parts[-2:]) == ("leonwgal", "galimvmini") else root / suffix
    path.mkdir(parents=True, exist_ok=True)
    for key in ("TEMP", "TMP", "TMPDIR"):
        os.environ[key] = str(path)
    tempfile.tempdir = str(path)

def application_settings():
    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    settings = QSettings(str(directory / "settings.ini"), QSettings.Format.IniFormat)
    if not os.environ.get("GALIMVMINI_DATA_DIR") and not settings.value("storage/migrated", False, type=bool):
        previous = QSettings("galIMV", "galIMVmini")
        for key in previous.allKeys():
            if not settings.contains(key):
                settings.setValue(key, previous.value(key))
        settings.setValue("storage/migrated", True)
        settings.sync()
        if settings.status() != QSettings.Status.NoError:
            raise OSError("Cannot migrate galIMVmini settings")
    return settings
