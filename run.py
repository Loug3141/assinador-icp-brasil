"""
FEX Assinador em Massa
Ponto de entrada: cria diretórios necessários, abre o browser e inicia o Flask.
"""
import os
import sys
import time
import threading
import webbrowser

# Garante que o backend está no path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cria estrutura de diretórios
for d in ['temp', 'output', 'credentials']:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)


def open_browser():
    time.sleep(1.8)
    webbrowser.open('http://localhost:5050')


if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 55)
    print("  FEX Assinador em Massa")
    print("  Acesse: http://localhost:5050")
    print("  Pressione Ctrl+C para encerrar.")
    print("=" * 55)

    from app import app
    app.run(host='localhost', port=5050, debug=False)
