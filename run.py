"""
FEX Assinador em Massa
Ponto de entrada: cria diretórios necessários, abre o browser e inicia o Flask.
"""
import os
import sys
import time
import threading
import webbrowser

# ─── Detecção de modo empacotado (PyInstaller) ───────────────────────────────
FROZEN = getattr(sys, 'frozen', False)

if FROZEN:
    # Diretório onde o .exe/.app está (dados persistentes ficam aqui)
    BASE_DIR = os.path.dirname(sys.executable)
    # Diretório de recursos empacotados (frontend, etc.)
    BUNDLE_DIR = sys._MEIPASS
    # Garante que o backend empacotado está no path
    sys.path.insert(0, os.path.join(BUNDLE_DIR, 'backend'))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR
    # Garante que o backend está no path
    sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

# Cria estrutura de diretórios
for d in ['temp', 'output', 'credentials']:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)


def open_browser():
    time.sleep(1.8)
    webbrowser.open('http://localhost:5050')


if __name__ == '__main__':
    # Exporta variáveis para app.py via variáveis de ambiente
    os.environ['FEX_BASE_DIR'] = BASE_DIR
    os.environ['FEX_BUNDLE_DIR'] = BUNDLE_DIR
    os.environ['FEX_FROZEN'] = '1' if FROZEN else '0'

    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 55)
    print("  FEX Assinador em Massa")
    print("  Acesse: http://localhost:5050")
    print("  Pressione Ctrl+C para encerrar.")
    print("=" * 55)

    from app import app
    app.run(host='localhost', port=5050, debug=False)
