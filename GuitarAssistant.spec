# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: Windows onefile, macOS .app bundle, Linux onedir (for AppImage / tarball)."""
import os
import sys

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Icons: place icon/guitarassistant.{png,ico,icns} (see RELEASE_SETUP.md)
_spec_root = os.path.dirname(os.path.abspath(SPEC))
_icon_dir = os.path.join(_spec_root, "icon")
_icon_png = os.path.join(_icon_dir, "guitarassistant.png")
_icon_ico = os.path.join(_icon_dir, "guitarassistant.ico")
_icon_icns = os.path.join(_icon_dir, "guitarassistant.icns")

datas, binaries, hiddenimports = [], [], []
for pkg in ("PyQt6", "sounddevice", "numpy"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

if os.path.isfile(_icon_png):
    datas.append((_icon_png, "icon"))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

is_win = sys.platform == "win32"
is_mac = sys.platform == "darwin"

if is_mac:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GuitarAssistant",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="GuitarAssistant",
    )
    app = BUNDLE(
        coll,
        name="GuitarAssistant.app",
        icon=_icon_icns if os.path.isfile(_icon_icns) else None,
        bundle_identifier="com.guitarhelper.guitarassistant",
        info_plist={
            "NSMicrophoneUsageDescription": "Guitar Assistant uses the microphone for the tuner.",
            "NSHighResolutionCapable": True,
        },
    )
elif is_win:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="GuitarAssistant",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_icon_ico if os.path.isfile(_icon_ico) else None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GuitarAssistant",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="GuitarAssistant",
    )
