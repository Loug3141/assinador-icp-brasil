#!/usr/bin/env python3
"""
build_zip.py — Gera o pacote ZIP de distribuição do FEX Assinador em Massa.

Uso:
    python build_zip.py

Gera em dist/:
  Assinador FEX v1.0.zip
  ├── Iniciar (Windows).bat
  ├── Iniciar (Mac).command
  ├── Iniciar (Linux).sh
  ├── LEIA-ME.txt
  └── assinador/
      ├── run.py
      ├── requirements.txt
      ├── backend/
      ├── frontend/
      ├── credentials/
      ├── temp/
      └── output/
"""

import os
import stat
import zipfile
from pathlib import Path

# ─── Configurações ────────────────────────────────────────────────────────────

APP_NAME   = "Assinador FEX"
VERSION    = "1.0"
APP_FOLDER = "assinador"  # nome da pasta dentro do ZIP

ROOT     = Path(__file__).parent
DIST_DIR = ROOT / "dist"
OUTPUT_ZIP = DIST_DIR / f"{APP_NAME} v{VERSION}.zip"

# Arquivos do app a empacotar (caminhos relativos à raiz do projeto)
APP_FILES = [
    "run.py",
    "requirements.txt",
    "backend/app.py",
    "backend/drive.py",
    "backend/log_page.py",
    "backend/signer.py",
    "frontend/index.html",
]

# Pastas que devem existir mas começam vazias
EMPTY_DIRS = ["credentials", "temp", "output"]


# ─── Conteúdo dos launchers ───────────────────────────────────────────────────

WINDOWS_LAUNCHER = r"""@echo off
title FEX Assinador em Massa
chcp 65001 >nul
echo ================================================
echo   FEX Assinador em Massa
echo   Iniciando...
echo ================================================
echo.

:: Muda para a pasta do app (ao lado do .bat)
cd /d "%~dp0assinador"

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado!
    echo  Instale em: https://www.python.org/downloads/
    echo  Marque "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

:: Cria o ambiente virtual na primeira execucao
if not exist ".venv" (
    echo  Primeira execucao: instalando dependencias, aguarde...
    echo  (isso pode levar alguns minutos)
    echo.
    python -m venv .venv
    if errorlevel 1 (
        echo  ERRO ao criar ambiente virtual.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo  ERRO ao instalar dependencias.
        pause
        exit /b 1
    )
    echo  Dependencias instaladas com sucesso!
    echo.
) else (
    call .venv\Scripts\activate.bat
)

:: Inicia o app
echo  Abrindo navegador em http://localhost:5050 ...
python run.py
echo.
pause
"""

MAC_LAUNCHER = """#!/bin/bash
# FEX Assinador em Massa — Launcher para macOS
# Clique duas vezes neste arquivo no Finder para iniciar o app.

# Garante que estamos na pasta correta (o .command abre no $HOME por padrão)
cd "$(dirname "$0")/assinador"

echo "================================================"
echo "  FEX Assinador em Massa"
echo "  Iniciando..."
echo "================================================"
echo ""

# Verifica se o Python 3 está instalado
if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python não encontrado" message "Instale o Python 3 em:\\nhttps://www.python.org/downloads/\\n\\nDepois abra este arquivo novamente." as critical buttons {"OK"} default button "OK"'
    exit 1
fi

# Cria o ambiente virtual na primeira execução
if [ ! -d ".venv" ]; then
    echo "  Primeira execução: instalando dependências, aguarde..."
    echo "  (isso pode levar alguns minutos)"
    echo ""
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "  ERRO ao criar ambiente virtual."
        read -p "Pressione Enter para fechar..."
        exit 1
    fi
    source .venv/bin/activate
    pip install --quiet -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "  ERRO ao instalar dependências."
        read -p "Pressione Enter para fechar..."
        exit 1
    fi
    echo "  Dependências instaladas com sucesso!"
    echo ""
else
    source .venv/bin/activate
fi

# Inicia o app
echo "  Abrindo navegador em http://localhost:5050 ..."
python3 run.py
"""

LINUX_LAUNCHER = """#!/bin/bash
# FEX Assinador em Massa — Launcher para Linux

cd "$(dirname "$0")/assinador"

echo "================================================"
echo "  FEX Assinador em Massa"
echo "  Iniciando..."
echo "================================================"
echo ""

# Verifica se o Python 3 está instalado
if ! command -v python3 &>/dev/null; then
    echo "  ERRO: Python 3 não encontrado!"
    echo "  Instale com: sudo apt install python3 python3-venv"
    read -p "Pressione Enter para fechar..."
    exit 1
fi

# Cria o ambiente virtual na primeira execução
if [ ! -d ".venv" ]; then
    echo "  Primeira execução: instalando dependências, aguarde..."
    echo "  (isso pode levar alguns minutos)"
    echo ""
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "  ERRO ao criar ambiente virtual."
        echo "  Tente: sudo apt install python3-venv"
        read -p "Pressione Enter para fechar..."
        exit 1
    fi
    source .venv/bin/activate
    pip install --quiet -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "  ERRO ao instalar dependências."
        read -p "Pressione Enter para fechar..."
        exit 1
    fi
    echo "  Dependências instaladas com sucesso!"
    echo ""
else
    source .venv/bin/activate
fi

# Inicia o app
echo "  Abrindo navegador em http://localhost:5050 ..."
python3 run.py
"""

README = f"""{APP_NAME}
{"=" * len(APP_NAME)}

REQUISITOS
----------
Python 3.10 ou superior instalado no computador.
Download gratuito: https://www.python.org/downloads/

No Windows: durante a instalação, marque "Add Python to PATH".


COMO INICIAR
------------
  Windows  → duplo-clique em "Iniciar (Windows).bat"

  macOS    → duplo-clique em "Iniciar (Mac).command"
             Na primeira vez, o macOS pode pedir confirmação:
             clique com botão direito no arquivo → Abrir → Abrir

  Linux    → abra um terminal nesta pasta e execute:
               chmod +x "Iniciar (Linux).sh" && ./"Iniciar (Linux).sh"


PRIMEIRA EXECUÇÃO
-----------------
O app instala as dependências automaticamente num ambiente isolado.
Isso pode levar alguns minutos. Nas execuções seguintes, inicia na hora.


ESTRUTURA DO PACOTE
-------------------
  assinador/    → arquivos do app (não mova esta pasta)
  Iniciar *.bat / *.command / *.sh  → executáveis por sistema
  LEIA-ME.txt   → este arquivo


SUPORTE
-------
FEX Automações
"""


# ─── Funções auxiliares ───────────────────────────────────────────────────────

def add_text_to_zip(
    zf: zipfile.ZipFile,
    arcname: str,
    content: str,
    executable: bool = False,
) -> None:
    """Adiciona um arquivo de texto ao ZIP preservando permissões Unix."""
    info = zipfile.ZipInfo(arcname)
    info.compress_type = zipfile.ZIP_DEFLATED

    if executable:
        unix_perms = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH  # 0o755
    else:
        unix_perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH  # 0o644

    info.external_attr = unix_perms << 16
    zf.writestr(info, content.encode("utf-8"))


def add_binary_to_zip(
    zf: zipfile.ZipFile,
    arcname: str,
    data: bytes,
) -> None:
    """Adiciona um arquivo binário ao ZIP."""
    info = zipfile.ZipInfo(arcname)
    info.compress_type = zipfile.ZIP_DEFLATED
    unix_perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH  # 0o644
    info.external_attr = unix_perms << 16
    zf.writestr(info, data)


# ─── Build principal ──────────────────────────────────────────────────────────

def build_zip() -> None:
    DIST_DIR.mkdir(exist_ok=True)

    print(f"Gerando: {OUTPUT_ZIP}")
    print("-" * 50)

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:

        # Launchers na raiz do ZIP
        add_text_to_zip(zf, "Iniciar (Windows).bat", WINDOWS_LAUNCHER)
        print("  + Iniciar (Windows).bat")

        add_text_to_zip(zf, "Iniciar (Mac).command", MAC_LAUNCHER, executable=True)
        print("  + Iniciar (Mac).command  [executable]")

        add_text_to_zip(zf, "Iniciar (Linux).sh", LINUX_LAUNCHER, executable=True)
        print("  + Iniciar (Linux).sh  [executable]")

        add_text_to_zip(zf, "LEIA-ME.txt", README)
        print("  + LEIA-ME.txt")

        # Arquivos do app dentro de assinador/
        for rel_path in APP_FILES:
            src = ROOT / rel_path
            if not src.exists():
                print(f"  AVISO: {rel_path} não encontrado, ignorando.")
                continue
            with open(src, "rb") as f:
                data = f.read()
            arcname = f"{APP_FOLDER}/{rel_path}"
            add_binary_to_zip(zf, arcname, data)
            print(f"  + {arcname}")

        # Pastas vazias com .gitkeep para que sejam criadas ao extrair
        for d in EMPTY_DIRS:
            add_text_to_zip(zf, f"{APP_FOLDER}/{d}/.gitkeep", "")
            print(f"  + {APP_FOLDER}/{d}/  (vazia)")

    size_kb = OUTPUT_ZIP.stat().st_size / 1024
    print("-" * 50)
    print(f"Concluído! {OUTPUT_ZIP.name} ({size_kb:.0f} KB)")
    print(f"Localização: {OUTPUT_ZIP}")


if __name__ == "__main__":
    build_zip()
