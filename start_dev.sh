#!/bin/bash
# Opti-Logistix Development Server Startup Script

echo "🚀 Opti-Logistix başlatılıyor..."

# Check Python environment
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment oluşturuluyor..."
    python3 -m venv venv
fi

# Activate environment
source venv/bin/activate

# Install dependencies
echo "📥 Bağımlılıklar kontrol ediliyor..."
pip install -q -r requirements.txt

# Start API server
echo "🌐 API sunucusu başlatılıyor (port 8000)..."
cd src
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Start dashboard server
echo "📊 Dashboard sunucusu başlatılıyor (port 3000)..."
cd dashboard
python3 -m http.server 3000 &
DASHBOARD_PID=$!

echo ""
echo "✅ Sunucular çalışıyor:"
echo "   🔧 API: http://localhost:8000"
echo "   📄 API Docs: http://localhost:8000/docs"
echo "   📊 Dashboard: http://localhost:3000"
echo ""
echo "Durdurmak için Ctrl+C tuşlayın"

# Wait for interrupt
trap "echo '⏹️ Durduruluyor...'; kill $API_PID $DASHBOARD_PID 2>/dev/null; exit" INT
wait
