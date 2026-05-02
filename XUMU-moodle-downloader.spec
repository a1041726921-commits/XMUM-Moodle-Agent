# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\xmum_moodle_downloader\\gui.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src\\xmum_moodle_downloader\\assets', 'xmum_moodle_downloader\\assets')],
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
    name='XUMU-moodle-downloader',
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
    icon='src\\xmum_moodle_downloader\\assets\\xmum.ico',
)
