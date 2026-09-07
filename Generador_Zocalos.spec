# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)
assets = ROOT / 'assets'

a = Analysis(
    ['Generador_Zocalos.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(assets / 'plantilla_vacia.png'), 'assets'),
        (str(assets / 'FiraSansCondensed-Black.ttf'), 'assets'),
        (str(assets / 'FiraSansExtraCondensed-ExtraBold.ttf'), 'assets'),
        (str(ROOT / 'ejemplo_zocalos.txt'), '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Generador_Zocalos_Pipati',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
