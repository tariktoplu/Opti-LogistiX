@echo off
setlocal
title Opti-Logistix Baslatiliyor...

echo ===================================================
echo 🚀 Opti-Logistix Gelistirme Ortami Baslatiliyor...
echo ===================================================

:: Python Kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadi! Lutfen Python'u yukleyin ve PATH'e ekleyin.
    pause
    exit /b
)

:: Sanal Ortam (venv) Kontrolü ve Oluşturma
if not exist venv (
    echo 📦 Sanal ortam (venv) olusturuluyor...
    python -m venv venv
)

:: venv Aktivasyonu
call venv\Scripts\activate

:: Bağımlılıkları Yükleme
echo 📥 Bagimliliklar kontrol ediliyor...
pip install -q -r requirements.txt

:: API Sunucusunu Başlatma (Yeni Pencerede)
echo 🌐 API sunucusu baslatiliyor (port 8000)...
start "Opti-Logistix API" cmd /k "call venv\Scripts\activate && cd src && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Dashboard Sunucusunu Başlatma (Yeni Pencerede)
echo 📊 Dashboard sunucusu baslatiliyor (port 3000)...
start "Opti-Logistix Dashboard" cmd /k "cd src\dashboard && python -m http.server 3000"

echo.
echo ✅ İslemler tamamlandi!
echo    🔧 API: http://localhost:8000
echo    📄 API Docs: http://localhost:8000/docs
echo    📊 Dashboard: http://localhost:3000
echo.
echo Pencereleri kapatarak sunuculari durdurabilirsiniz.
pause
