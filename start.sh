#!/bin/bash
# AlquiSearch España - Script de arranque
# Uso: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "🏠 AlquiSearch España - Buscador de Alquileres"
echo "=============================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Por favor, instala Python 3.8 o superior."
    exit 1
fi

echo "✓ Python $(python3 --version | cut -d' ' -f2)"

# Instalar dependencias si es necesario
if [ ! -d "$BACKEND_DIR/__pycache__" ] || [ "$1" = "--install" ]; then
    echo "📦 Instalando dependencias..."
    cd "$BACKEND_DIR"
    python3 -m pip install -r requirements.txt --quiet
    echo "✓ Dependencias instaladas"
fi

# Ejecutar tests si se solicita
if [ "$1" = "--test" ]; then
    echo ""
    echo "🧪 Ejecutando tests..."
    cd "$BACKEND_DIR"
    python3 tests.py
    exit $?
fi

# Iniciar servidor
echo ""
echo "🚀 Iniciando servidor..."
echo "   → http://localhost:8000"
echo ""
echo "   Presiona Ctrl+C para detener"
echo ""

cd "$BACKEND_DIR"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
