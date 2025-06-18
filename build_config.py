"""
Build configuration for creating standalone executables
"""

import os
import sys
import platform
from pathlib import Path

# Build configuration
APP_NAME = "PRDY"
APP_VERSION = "0.1.0"
APP_AUTHOR = "PRDY Team"
APP_DESCRIPTION = "AI-powered Product Requirements Document Generator"

# Get platform-specific settings
PLATFORM = platform.system().lower()
ARCH = platform.machine().lower()

# Output directory
BUILD_DIR = Path("dist")
WORK_DIR = Path("build")

# PyInstaller configuration
PYINSTALLER_CONFIG = {
    "name": "prdy",
    "entry_point": "prdy/__main__.py",
    "icon": "assets/icon.ico" if PLATFORM == "windows" else "assets/icon.icns" if PLATFORM == "darwin" else None,
    "add_data": [
        ("prdy/templates", "templates"),
        ("assets", "assets") if Path("assets").exists() else None,
    ],
    "hidden_imports": [
        "prdy.models",
        "prdy.engines", 
        "prdy.utils",
        "prdy.cli",
        "prdy.gui",
        "flet",
        "flet.fastapi",
        "uvicorn",
        "sqlalchemy.dialects.sqlite",
        "alembic.runtime.migration",
        "reportlab.pdfgen",
        "reportlab.platypus",
        "markdown",
        "jinja2",
        "requests",
        "psutil",
    ],
    "exclude_modules": [
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
    ],
    "onefile": True,
    "windowed": False,  # Keep console for now
    "clean": True,
    "strip": False,
    "upx": False,  # Disable UPX compression (can cause issues)
}

# Platform-specific adjustments
if PLATFORM == "windows":
    PYINSTALLER_CONFIG.update({
        "console": True,  # Keep console on Windows
        "uac_admin": False,
    })
elif PLATFORM == "darwin":  # macOS
    PYINSTALLER_CONFIG.update({
        "target_arch": "universal2",  # Universal binary for Intel and Apple Silicon
        "bundle_identifier": "com.prdgenerator.app",
    })
elif PLATFORM == "linux":
    PYINSTALLER_CONFIG.update({
        "strip": True,  # Strip symbols on Linux
    })


def create_pyinstaller_spec():
    """Create PyInstaller spec file"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{PYINSTALLER_CONFIG["entry_point"]}'],
    pathex=[],
    binaries=[],
    datas={[item for item in PYINSTALLER_CONFIG["add_data"] if item is not None]},
    hiddenimports={PYINSTALLER_CONFIG["hidden_imports"]},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={PYINSTALLER_CONFIG["exclude_modules"]},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{PYINSTALLER_CONFIG["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip={PYINSTALLER_CONFIG["strip"]},
    upx={PYINSTALLER_CONFIG["upx"]},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={PYINSTALLER_CONFIG.get("console", True)},
    disable_windowed_traceback=False,
    target_arch='{PYINSTALLER_CONFIG.get("target_arch", None)}',
    codesign_identity=None,
    entitlements_file=None,
    {"icon='" + PYINSTALLER_CONFIG["icon"] + "'," if PYINSTALLER_CONFIG.get("icon") else ""}
)

{"app = BUNDLE(exe, name='" + APP_NAME + ".app', icon='" + PYINSTALLER_CONFIG.get("icon", "") + "', bundle_identifier='" + PYINSTALLER_CONFIG.get("bundle_identifier", "") + "')" if PLATFORM == "darwin" else ""}
'''
    
    spec_file = Path(f"{PYINSTALLER_CONFIG['name']}.spec")
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    return spec_file


def create_requirements_build():
    """Create requirements file for building"""
    build_requirements = [
        "pyinstaller>=5.13.0",
        "setuptools>=68.0.0",
        "wheel>=0.41.0",
    ]
    
    # Read main requirements
    with open("requirements.txt", "r") as f:
        main_requirements = f.read().strip().split('\n')
    
    # Combine
    all_requirements = main_requirements + build_requirements
    
    with open("requirements-build.txt", "w") as f:
        f.write('\n'.join(all_requirements))


def create_build_script():
    """Create platform-specific build script"""
    
    if PLATFORM == "windows":
        script_content = f'''@echo off
echo Building PRD Generator for Windows...

echo Installing build dependencies...
python -m pip install -r requirements-build.txt

echo Creating executable...
pyinstaller --clean {PYINSTALLER_CONFIG["name"]}.spec

echo Build completed!
echo Executable location: dist\\{PYINSTALLER_CONFIG["name"]}.exe

pause
'''
        script_file = "build.bat"
    
    else:  # Unix-like (macOS, Linux)
        script_content = f'''#!/bin/bash
set -e

echo "Building PRD Generator for {PLATFORM}..."

echo "Installing build dependencies..."
python3 -m pip install -r requirements-build.txt

echo "Creating executable..."
pyinstaller --clean {PYINSTALLER_CONFIG["name"]}.spec

echo "Build completed!"
echo "Executable location: dist/{PYINSTALLER_CONFIG["name"]}"

# Make executable if on Linux
if [ "$(uname)" = "Linux" ]; then
    chmod +x dist/{PYINSTALLER_CONFIG["name"]}
fi
'''
        script_file = "build.sh"
    
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Make executable on Unix-like systems
    if PLATFORM != "windows":
        os.chmod(script_file, 0o755)
    
    return script_file


def create_installer_config():
    """Create installer configuration"""
    
    if PLATFORM == "windows":
        # Create NSIS installer script
        nsis_content = f'''!define APP_NAME "{APP_NAME}"
!define APP_VERSION "{APP_VERSION}"
!define APP_PUBLISHER "{APP_AUTHOR}"
!define APP_EXE "{PYINSTALLER_CONFIG["name"]}.exe"

SetCompressor /SOLID lzma

!include "MUI2.nsh"

Name "${{APP_NAME}}"
OutFile "setup-prd-generator-{APP_VERSION}-windows.exe"
InstallDir "$PROGRAMFILES64\\${{APP_NAME}}"
InstallDirRegKey HKLM "Software\\${{APP_NAME}}" "Install_Dir"

RequestExecutionLevel admin

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Main Application"
  SetOutPath $INSTDIR
  File "dist\\${{APP_EXE}}"
  
  WriteRegStr HKLM SOFTWARE\\${{APP_NAME}} "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
  WriteUninstaller "uninstall.exe"
  
  CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
  CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
  CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
SectionEnd

Section "Uninstall"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
  DeleteRegKey HKLM SOFTWARE\\${{APP_NAME}}
  
  Delete $INSTDIR\\${{APP_EXE}}
  Delete $INSTDIR\\uninstall.exe
  
  Delete "$SMPROGRAMS\\${{APP_NAME}}\\*.*"
  RMDir "$SMPROGRAMS\\${{APP_NAME}}"
  Delete "$DESKTOP\\${{APP_NAME}}.lnk"
  
  RMDir "$INSTDIR"
SectionEnd
'''
        
        with open("installer.nsi", "w") as f:
            f.write(nsis_content)
    
    elif PLATFORM == "darwin":  # macOS
        # Create DMG creation script
        dmg_script = f'''#!/bin/bash
set -e

APP_NAME="{APP_NAME}"
APP_VERSION="{APP_VERSION}"
DMG_NAME="$APP_NAME-$APP_VERSION-macOS.dmg"

echo "Creating macOS DMG installer..."

# Create temporary directory
TMP_DIR=$(mktemp -d)
APP_DIR="$TMP_DIR/$APP_NAME"
mkdir -p "$APP_DIR"

# Copy application
cp -R "dist/$APP_NAME.app" "$APP_DIR/"

# Create DMG
hdiutil create -volname "$APP_NAME" -srcfolder "$TMP_DIR" -ov -format UDZO "$DMG_NAME"

# Cleanup
rm -rf "$TMP_DIR"

echo "DMG created: $DMG_NAME"
'''
        
        with open("create_dmg.sh", "w") as f:
            f.write(dmg_script)
        os.chmod("create_dmg.sh", 0o755)
    
    else:  # Linux
        # Create AppImage configuration
        appimage_config = f'''[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={PYINSTALLER_CONFIG["name"]}
Icon={PYINSTALLER_CONFIG["name"]}
Categories=Office;Development;
Comment={APP_DESCRIPTION}
Terminal=false
'''
        
        with open("prd-generator.desktop", "w") as f:
            f.write(appimage_config)


def main():
    """Main build configuration setup"""
    print(f"🔧 Setting up build configuration for {PLATFORM}...")
    
    # Create directories
    BUILD_DIR.mkdir(exist_ok=True)
    WORK_DIR.mkdir(exist_ok=True)
    
    # Create assets directory if it doesn't exist
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    # Create build files
    spec_file = create_pyinstaller_spec()
    print(f"✅ Created PyInstaller spec: {spec_file}")
    
    create_requirements_build()
    print("✅ Created build requirements")
    
    build_script = create_build_script()
    print(f"✅ Created build script: {build_script}")
    
    create_installer_config()
    print("✅ Created installer configuration")
    
    print(f"\n🚀 Build configuration complete!")
    print(f"Platform: {PLATFORM}")
    print(f"Architecture: {ARCH}")
    print(f"\nTo build the application:")
    if PLATFORM == "windows":
        print(f"   Run: {build_script}")
    else:
        print(f"   Run: ./{build_script}")
    
    print(f"\nOutput will be in: {BUILD_DIR}/")


if __name__ == "__main__":
    main()