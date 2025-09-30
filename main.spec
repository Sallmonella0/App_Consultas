# -*- mode: python ; coding: utf-8 -*-
import os

# Define a raiz do projeto (C:\App_Consultas)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

a = Analysis(
    ['main.py'],  # CORREÇÃO: Colocamos SÓ o nome do script (sem o "src/")
    pathex=[os.path.join(ROOT_DIR, 'src')], # CORREÇÃO: Dizemos ao PyInstaller que procure em 'C:\App_Consultas\src'
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)