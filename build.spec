# build.spec — PyInstaller build configuration for Scryptian

import os
import pathlib

block_cipher = None
base_dir = os.path.dirname(os.path.abspath(SPEC))

# ── Collect llama_cpp native DLLs ──
llama_binaries = []
try:
    import llama_cpp as _lc
    _lc_dir = pathlib.Path(os.path.dirname(_lc.__file__))
    _lc_lib = _lc_dir / "lib"
    for dll in _lc_lib.glob("*.dll"):
        llama_binaries.append((str(dll), "llama_cpp/lib"))
except ImportError:
    # llama_cpp not importable at build time; scan common install locations
    for site in ["Lib/site-packages", "Lib/site-packages/llama_cpp"]:
        candidate = pathlib.Path(base_dir) / ".venv" / site
        if candidate.is_dir():
            lib_dir = candidate / "lib" if "llama_cpp" in site else candidate / "llama_cpp" / "lib"
            if lib_dir.is_dir():
                for dll in lib_dir.glob("*.dll"):
                    llama_binaries.append((str(dll), "llama_cpp/lib"))
                break

a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=llama_binaries,
    datas=[
        ('icon.ico', '.'),
        ('config.py', '.'),
        ('bridge.py', '.'),
        ('editor.py', '.'),
        ('telemetry.py', '.'),
        ('tray.py', '.'),
        ('autostart.py', '.'),
        ('bootstrap.py', '.'),
        ('themes.py', '.'),
        ('settings.py', '.'),
        ('skills/*.py', 'skills'),
    ],
    hiddenimports=[
        'keyboard',
        'pyperclip',
        'themes',
        'settings',
        'pystray._win32',
        'llama_cpp',
        'certifi',
        'pygments',
        'pygments.lexers',
        'pygments.lexers.python',
        'pygments.lexers.javascript',
        'pygments.lexers.typescript',
        'pygments.lexers.csharp',
        'pygments.lexers.go',
        'pygments.lexers.rust',
        'pygments.lexers.java',
        'pygments.lexers.c_cpp',
        'pygments.lexers.html',
        'pygments.lexers.css',
        'pygments.lexers.json',
        'pygments.lexers.yaml',
        'pygments.lexers.markdown',
        'pygments.lexers.shell',
        'pygments.lexers.sql',
        'pygments.lexers.ruby',
        'pygments.lexers.php',
        'pygments.lexers.swift',
        'pygments.lexers.kotlin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'transformers',
        'torch',
        'tensorflow',
        'scipy',
        'pandas',
        'matplotlib',
        'pytest',
        'IPython',
        'notebook',
        'sphinx',
        'docutils',
        'setuptools',
        'wheel',
        'pip',
        'pkg_resources',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Scryptian',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='icon.ico',
)
