#!/usr/bin/env bash
# ============================================================
#  Build script — macOS (.app)
#  Gera: dist/FEX Assinador.app  (e dist/FEX Assinador/)
# ============================================================
set -e

echo ""
echo "=== FEX Assinador — Build macOS ==="
echo ""

# Instala PyInstaller se necessário
pip3 install pyinstaller

# Limpa builds anteriores
rm -rf build dist

# Executa o build
pyinstaller assinador.spec --noconfirm

echo ""
if [ -d "dist/FEX Assinador.app" ]; then
    echo "BUILD OK!"
    echo ""
    echo "App gerado em:"
    echo "  dist/FEX Assinador.app"
    echo ""
    echo "Para distribuir, copie 'FEX Assinador.app'"
    echo "e coloque credentials/google_oauth.json ao lado do .app."
else
    echo "BUILD OK (sem .app bundle — use a pasta dist/FEX Assinador/)"
    echo ""
    echo "Para executar:"
    echo "  cd 'dist/FEX Assinador' && './FEX Assinador'"
fi
echo ""
