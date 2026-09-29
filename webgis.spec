# -*- mode: python ; coding: utf-8 -*-
import os
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Base directories
ROOT_DIR = os.path.abspath(SPECPATH)
APP_DIR = os.path.join(ROOT_DIR, 'app_webgis')

# Collect all geojson files
geojson_files = glob.glob(os.path.join(APP_DIR, '*.geojson'))
geojson_datas = [(f, 'app_webgis') for f in geojson_files]

# Base datas
datas = [
    (os.path.join(APP_DIR, 'templates'), 'app_webgis/templates'),
    (os.path.join(APP_DIR, 'static'), 'app_webgis/static'),
    (os.path.join(ROOT_DIR, 'app_icon.ico'), '.')
] + geojson_datas

# Bundled database if present
db_file = os.path.join(APP_DIR, 'database.db')
if os.path.exists(db_file):
    datas.append((db_file, 'app_webgis'))

# Library datas
datas += collect_data_files('geopandas')
datas += collect_data_files('pyproj')
datas += collect_data_files('shapely')

# Library binaries
binaries = []
binaries += collect_dynamic_libs('shapely')
binaries += collect_dynamic_libs('pyproj')

# Hidden imports
hiddenimports = [
    'jinja2',
    'flask',
    'flask_login',
    'werkzeug',
    'werkzeug.security',
    'werkzeug.utils',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'docx',
    'pptx',
    'sqlite3',
    'geopandas',
    'shapely',
    'shapely.geometry',
    'pyproj',
    'qrcode',
    'qrcode.image',
    'qrcode.image.pil',
    'PIL',
    'PIL.Image',
    'blockchain_engine',
    'pdf_generator',
    'app_webgis',
    'app_webgis.app',
    'app_webgis.blockchain_engine',
    'app_webgis.pdf_generator'
]
hiddenimports += collect_submodules('geopandas')
hiddenimports += collect_submodules('shapely')
hiddenimports += collect_submodules('pyproj')
hiddenimports += collect_submodules('qrcode')

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[ROOT_DIR, APP_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchaudio', 'torchvision', 'scipy', 'sklearn', 
        'matplotlib', 'spyder', 'PyQt5', 'PyQt6', 'IPython', 
        'jupyter', 'notebook', 'spacy', 'transformers', 'tables'
    ],
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
    name='WebGIS_Angra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, 'app_icon.ico')
)
