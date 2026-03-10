# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None

a = Analysis(
    ['../pc_app/OsciFootswitch.py'],
    pathex=[os.path.abspath('../pc_app')],
    binaries=[],
    datas=[('../assets/icon.ico', '.')],
    hiddenimports=[
        'pyvisa_py',
        'serial.tools.list_ports',
        'PIL.Image'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OsciFootswitch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='../assets/icon.ico',
    version='../assets/version.txt'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='OsciFootswitch'
)