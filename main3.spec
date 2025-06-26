# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['app/main3.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('images', 'images'),
        ('test_mediapipe_dlls.py', '.'),
    ],
    hiddenimports=[],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'transformers', 'torchaudio', 'torchvision', 'sentencepiece', 'huggingface_hub'],
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
    name='main3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='images/application_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main3',
    destdir='packaged_app/main3',
)
