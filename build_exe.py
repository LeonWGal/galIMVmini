"""
galIMVmini PyInstaller Distribution Builder.
Builds standalone Windows executable distribution of galIMVmini.

Usage:
    python build_exe.py            # Builds portable folder (fast startup)
    python build_exe.py --onefile  # Builds standalone single executable
"""

import os
import sys
import shutil
import subprocess

def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    dist_dir = os.path.join(script_dir, "dist")
    build_dir = os.path.join(script_dir, "build")
    icon_path = os.path.join(script_dir, "resources", "app.ico")
    main_script = os.path.join(script_dir, "main.py")

    onefile = "--onefile" in sys.argv or "--single-file" in sys.argv

    print("=" * 60)
    print("Building galIMVmini Standalone Distribution")
    print(f"Mode: {'Single-file Portable Exe' if onefile else 'Portable Folder (Fast Startup)'}")
    print(f"Icon: {icon_path}")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=galIMVmini",
        "--windowed",
        "--noconsole",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
        "--clean",
        "--noconfirm",
    ]

    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")
    resources_dir = os.path.join(script_dir, "resources")
    if os.path.isdir(resources_dir):
        cmd.append(f"--add-data={resources_dir};resources")
    variants_dir = os.path.join(resources_dir, "lobe-variants")
    if os.path.isdir(variants_dir):
        cmd.append(f"--add-data={variants_dir};resources/lobe-variants")

    locales_dir = os.path.join(script_dir, "locales")
    if os.path.exists(locales_dir):
        cmd.append(f"--add-data={locales_dir};locales")

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    cmd.append(main_script)

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("Build SUCCESSFUL!")
        if onefile:
            exe_path = os.path.join(dist_dir, "galIMVmini.exe")
            print(f"Standalone executable: {exe_path}")
        else:
            folder_path = os.path.join(dist_dir, "galIMVmini")
            print(f"Distribution folder: {folder_path}")
            print(f"Executable: {os.path.join(folder_path, 'galIMVmini.exe')}")
        print("=" * 60)
    else:
        print("\n[ERROR] Build failed with return code:", result.returncode)

    return result.returncode

if __name__ == "__main__":
    sys.exit(build())
