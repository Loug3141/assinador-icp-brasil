# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para FEX Assinador em Massa.
Gera executável --onedir com frontend empacotado.

Uso:
  Windows:  pyinstaller assinador.spec
  macOS:    pyinstaller assinador.spec
"""
import sys
import os

block_cipher = None

# ─── Dados a empacotar (frontend como recurso estático) ──────────────────────

datas = [
    ('frontend', 'frontend'),          # index.html e assets
]

# ─── Hidden imports (libs que o PyInstaller não detecta automaticamente) ──────
# O backend é importado dinamicamente via sys.path; precisamos declarar aqui.

hiddenimports = [
    # Backend modules (importados via sys.path.insert + from app import app)
    'app',
    'signer',
    'drive',
    'log_page',
    # Flask
    'flask',
    'flask_cors',
    # pyhanko e dependências
    'pyhanko',
    'pyhanko.sign',
    'pyhanko.sign.fields',
    'pyhanko.sign.signers',
    'pyhanko.sign.signers.pdf_signer',
    'pyhanko.pdf_utils',
    'pyhanko.pdf_utils.reader',
    'pyhanko.pdf_utils.writer',
    'pyhanko.pdf_utils.incremental_writer',
    'pyhanko_certvalidator',
    # cryptography
    'cryptography',
    'cryptography.hazmat.primitives.serialization.pkcs12',
    'cryptography.x509',
    # reportlab
    'reportlab',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.colors',
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.pdfbase._fontdata',
    'reportlab.graphics',
    # pypdf
    'pypdf',
    # Google API
    'google.oauth2.credentials',
    'google_auth_oauthlib.flow',
    'google.auth.transport.requests',
    'googleapiclient.discovery',
    'googleapiclient.http',
    'googleapiclient._helpers',
    'google.auth.transport._http_client',
    # qrcode / PIL
    'qrcode',
    'qrcode.image.pil',
    'PIL',
    'PIL.Image',
    # tkinter (file picker)
    'tkinter',
    'tkinter.filedialog',
    # stdlib extras
    'json',
    'email.mime.text',
    'http.server',
]

# ─── Analysis ─────────────────────────────────────────────────────────────────

a = Analysis(
    ['run.py'],
    pathex=['backend'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'notebook',
        'jupyter',
        'IPython',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

# ─── EXE (Windows / Linux) ───────────────────────────────────────────────────

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FEX Assinador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # True para ver logs no terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ─── COLLECT (--onedir) ──────────────────────────────────────────────────────

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FEX Assinador',
)

# ─── BUNDLE (macOS .app) ─────────────────────────────────────────────────────

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='FEX Assinador.app',
        icon=None,
        bundle_identifier='com.fex.assinador',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'FEX Assinador',
            'NSHighResolutionCapable': True,
        },
    )
