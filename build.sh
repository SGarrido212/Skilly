#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# build.sh — Script de build para Render.com
# Se ejecuta automáticamente en cada deploy.
# ─────────────────────────────────────────────────────────
set -o errexit   # Detiene el script si algún comando falla

echo "▶ Instalando dependencias..."
pip install -r requirements.txt

echo "▶ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "▶ Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

echo "✅ Build completado con éxito."

