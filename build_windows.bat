@echo off
REM ============================================================
REM  Build script — Windows (.exe)
REM  Gera: dist\FEX Assinador\FEX Assinador.exe
REM ============================================================
echo.
echo === FEX Assinador — Build Windows ===
echo.

REM Instala PyInstaller se necessário
pip install pyinstaller

REM Limpa builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Executa o build
pyinstaller assinador.spec --noconfirm

echo.
if exist "dist\FEX Assinador\FEX Assinador.exe" (
    echo BUILD OK!
    echo.
    echo Executavel gerado em:
    echo   dist\FEX Assinador\FEX Assinador.exe
    echo.
    echo Para distribuir, copie a pasta inteira "dist\FEX Assinador"
    echo e coloque credentials\google_oauth.json ao lado do .exe.
) else (
    echo BUILD FALHOU. Verifique os erros acima.
)
echo.
pause
