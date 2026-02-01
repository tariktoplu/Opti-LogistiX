# 🚀 Opti-Logistix: Afet Lojistik Optimizasyon Sistemi

> **"Doğru kaynak, doğru zamanda, doğru yere"** — Afet yönetiminde yapay zeka ile operasyonel mükemmellik

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-red)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 İçindekiler

- [Proje Özeti](#proje-özeti)
- [Teknoloji Stack](#teknoloji-stack)
- [Proje Yapısı](#proje-yapısı)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Mimari](#mimari)
- [API Endpoints](#api-endpoints)
- [Katkıda Bulunma](#katkıda-bulunma)
- [Lisans](#lisans)

---

## 🎯 Proje Özeti

**Opti-Logistix**, deprem, sel ve diğer geniş çaplı afetlerde kritik kaynakların optimal dağıtımını ve rota optimizasyonunu sağlayan **Yapay Zeka destekli karar destek sistemidir**.

### 🎖️ Çözülen Sorunlar

| Sorun | Çözüm |
|-------|-------|
| 🚑 Ambulans & yardım araçlarının hasarlı yollarda kaybolması | **GNN-tabanlı hasar öngörüsü** ile en güvenli rota |
| 📦 Kaynakların yanlış lokasyonlara sevk edilmesi | **RL ajanı** ile dinamik önceliklendirme |
| 👨‍💼 Yöneticilerin karmaşık veriyi anlayamaması | **İnteraktif dashboard** ile görsel karar desteği |
| ⚠️ Reaktif (olay sonrası) yönetim | **Proaktif öngörü** ile hasardan önce hazırlık |

---

## 🧠 Teknoloji Stack

```
┌─────────────────────────────────────────────────────┐
│                   KATMANLAR                          │
├─────────────────────────────────────────────────────┤
│ Frontend    │ React + Deck.gl + Mapbox              │
│ Backend     │ FastAPI + Uvicorn                     │
│ AI Models   │ PyTorch Geometric (GNN)               │
│ RL Engine   │ Stable Baselines3 (PPO/DQN)          │
│ Simulation  │ SUMO + OSMnx                          │
│ Data        │ PostgreSQL + GeoJSON                  │
└─────────────────────────────────────────────────────┘
```

| Bileşen | Teknoloji | Versiyon | Amaç |
|---------|-----------|---------|------|
| **Backend Framework** | FastAPI | 0.109.0 | RESTful API |
| **Graph AI** | PyTorch Geometric | 2.4.0 | Hasar öngörüsü (GNN) |
| **Reinforcement Learning** | Stable Baselines3 | 2.2.1 | Dinamik rotalama |
| **Geospatial** | OSMnx + GeoPandas | 1.9.1 + 0.14.2 | Harita verileri |
| **Web Server** | Uvicorn | 0.25.0 | ASGI sunucusu |
| **Dashboard** | HTML5 + Vanilla JS | - | Statik frontend |

---

## 📁 Proje Yapısı

```
opti-logistix/
│
├── 📄 README.md                          # Bu dosya
├── 📄 requirements.txt                   # Python bağımlılıkları
├── 🐳 Dockerfile                         # Container yapılandırması
├── 🐳 docker-compose.yml                 # Multi-container setup
├── 🔧 .env.example                       # Ortam değişkenleri şablonu
│
├── 📚 docs/
│   └── MVP_ROADMAP.md                    # Detaylı yol haritası
│
├── 🔬 src/
│   ├── __init__.py
│   ├── config.py                         # Proje konfigürasyonu
│   │
│   ├── 🌐 api/
│   │   ├── __init__.py
│   │   └── main.py                       # FastAPI uygulaması
│   │
│   ├── 🧠 models/
│   │   ├── gnn/
│   │   │   ├── __init__.py
│   │   │   └── damage_predictor.py       # GNN hasar tahmin modeli
│   │   └── rl/
│   │       ├── __init__.py
│   │       ├── routing_agent.py          # RL ajanı
│   │       └── routing_env.py            # RL ortamı (Gymnasium)
│   │
│   ├── 📊 data/
│   │   ├── __init__.py
│   │   ├── graph_loader.py               # OSM verilerini yükleme
│   │   ├── scenario_generator.py         # Sentetik senaryo üretimi
│   │   └── 🗺️ maps/
│   │       └── osmnx_cache/              # Harita cache'i
│   │
│   └── 🎨 dashboard/
│       ├── index.html                    # Ana sayfa
│       ├── 🎭 css/
│       │   └── style.css                 # Stiller
│       └── 📜 js/
│           └── app.js                    # Frontend mantığı
│
└── 🧪 tests/                             # Unit testler (yakında)
```

---

## 🚀 Hızlı Başlangıç

### Gereksinimler

- **Python** 3.9 veya üzeri
- **Git**
- **Docker** & **Docker Compose** (isteğe bağlı)
- Minimum **4GB RAM**

### 5 Dakikalık Kurulum

#### Seçenek 1: Native (Lokal Python)

```bash
# 1. Repoyu klonla
git clone https://github.com/yourusername/opti-logistix.git
cd opti-logistix

# 2. Sanal ortam oluştur
python3 -m venv venv

# 3. Sanal ortamı aktifleştir
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Bağımlılıkları yükle
pip install -r requirements.txt

# 5. .env dosyasını oluştur
cp .env.example .env

# 6. Development sunucularını başlat
# Linux/Mac:
chmod +x start_dev.sh
./start_dev.sh

# Windows:
start_dev.bat
```

#### Seçenek 2: Docker

```bash
# Docker Compose ile başlat
docker-compose up

# Konteynerler çalışmaya başlayacak:
# - API:       http://localhost:8000
# - Dashboard: http://localhost:3000
```

### ✅ Başarılı Kurulum Kontrolü

Tarayıcında aşağıdaki adresleri ziyaret edin:

| URL | Açıklama |
|-----|----------|
| `http://localhost:8000` | API health check |
| `http://localhost:8000/docs` | Swagger API dokümantasyonu |
| `http://localhost:3000` | Dashboard |

---

## 💻 Kurulum

### Adım 1: Ortam Yapılandırması

```bash
# .env dosyasını düzenle
nano .env  # veya kendi editörünüzü kullanın
```

**Örnek `.env` dosyası:**

```env
# API Ayarları
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Harita Ayarları
DEFAULT_CITY=Kadıköy, Istanbul, Turkey
MAP_NETWORK_TYPE=drive  # drive, walk, bike

# Model Hiperparametreleri
GNN_HIDDEN_CHANNELS=64
GNN_NUM_LAYERS=2
RL_TOTAL_TIMESTEPS=50000
```

### Adım 2: Bağımlılıkları Yükleme

```bash
# Pip'i güncelle
pip install --upgrade pip setuptools wheel

# Gerekli paketleri yükle
pip install -r requirements.txt

# GPU desteği için (isteğe bağlı)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Adım 3: Harita Verilerini İndirme

```bash
python3 -c "
from src.data.graph_loader import load_osm_graph
# İstanbul için verileeri indir ve cache'le
graph = load_osm_graph('Kadıköy, Istanbul, Turkey')
print('✅ Harita verileteri hazır!')
"
```

---

## 🎮 Kullanım

### API Başlatma

```bash
cd src
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**API ulaşılabilir:** `http://localhost:8000`  
**Swagger Docs:** `http://localhost:8000/docs`

### Dashboard Başlatma

```bash
cd src/dashboard
python3 -m http.server 3000
```

**Dashboard:** `http://localhost:3000`

### Model Eğitimi

#### GNN Hasar Tahmin Modeli

```python
from src.models.gnn.damage_predictor import DamagePredictor
from src.data.graph_loader import load_osm_graph

# Harita verilerini yükle
graph = load_osm_graph('Istanbul')

# Modeli oluştur ve eğit
predictor = DamagePredictor(hidden_channels=64, num_layers=2)
predictor.train(graph, epochs=100, batch_size=32)

# Hasar tahminleri yap
damage_predictions = predictor.predict(graph)
```

#### RL Rota Optimizasyonu

```python
from src.models.rl.routing_agent import RoutingAgent
from src.models.rl.routing_env import RoutingEnv
from src.data.scenario_generator import generate_scenario

# Afet senaryosu oluştur
scenario = generate_scenario(disaster_type='earthquake', severity=7.5)

# RL ortamını ve ajanı başlat
env = RoutingEnv(scenario)
agent = RoutingAgent(env)

# Ajanı eğit
agent.learn(total_timesteps=50000)

# Optimal rotayı öner
optimal_route = agent.predict(env.observation)
```

---

## 🏗️ Mimari

### Sistem Akışı

```
┌──────────────────┐
│  AFET VERİSİ    │ (Deprem, sel, vb.)
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│   GNN DAMAGE PREDICTOR       │ ← Hasar öngörüsü
│  (PyTorch Geometric)         │   Yol ağında tahmin
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   RL ROUTING AGENT           │ ← Rota optimizasyonu
│  (Stable Baselines3)         │   Dinamik karar
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   FASTAPI BACKEND            │ ← API endpoint'leri
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   REACT DASHBOARD            │ ← Görsel sunuş
│  (Harita + Grafikler)        │   İnsan kararı
└──────────────────────────────┘
```

### Veri Akışı

```
OSM Harita Verileri
        │
        ▼
   Graph Loader
        │
        ├─→ Nodes (kavşaklar)
        ├─→ Edges (yollar)
        └─→ Attributes (özellikleri)
        │
        ▼
  GNN Model
        │
        ├─→ Damage Scores
        └─→ Risk Heatmap
        │
        ▼
  RL Environment
        │
        ├─→ State Space
        ├─→ Action Space
        └─→ Reward Function
        │
        ▼
  Optimal Routes & Priorities
        │
        ▼
   API Response → Dashboard
```

---

## 📡 API Endpoints

### Health Check

```http
GET /
```

**Response:**
```json
{
  "status": "online",
  "version": "0.1.0",
  "models": {
    "gnn": "damage_predictor_v1",
    "rl": "routing_agent_v1"
  }
}
```

### Hasar Tahminleri Alma

```http
POST /predict-damage
Content-Type: application/json

{
  "city": "Istanbul",
  "disaster_type": "earthquake",
  "severity": 7.5
}
```

**Response:**
```json
{
  "request_id": "uuid-here",
  "damage_map": {...},
  "affected_roads": [
    {
      "road_id": "1",
      "damage_level": 0.85,
      "blocked": true
    }
  ]
}
```

### Optimal Rota Bulma

```http
POST /find-route
Content-Type: application/json

{
  "origin": {"lat": 40.7128, "lon": 29.0131},
  "destination": {"lat": 40.7580, "lon": 29.0855},
  "vehicle_type": "ambulance",
  "scenario_id": "uuid-here"
}
```

**Response:**
```json
{
  "route": [
    {"lat": 40.7128, "lon": 29.0131},
    ...
  ],
  "estimated_time": 12.5,
  "risk_score": 0.3,
  "alternative_routes": [...]
}
```

### Kaynakları Önceliklendirme

```http
POST /prioritize-resources
Content-Type: application/json

{
  "available_resources": ["ambulance_1", "ambulance_2", "supply_truck_1"],
  "affected_areas": [
    {"lat": 40.7128, "lon": 29.0131, "severity": 9},
    {"lat": 40.7580, "lon": 29.0855, "severity": 7}
  ]
}
```

**Response:**
```json
{
  "allocations": [
    {
      "resource": "ambulance_1",
      "target_area": {"lat": 40.7128, "lon": 29.0131},
      "priority": 1,
      "route": [...]
    }
  ]
}
```

👉 **Tüm API endpoint'lerini görmek için:** `http://localhost:8000/docs`

---

## 🧪 Testing

### Unit Testleri Çalıştırma

```bash
# Tüm testleri çalıştır
pytest

# Belirli bir test dosyasını çalıştır
pytest tests/test_gnn.py -v

# Coverage raporu oluştur
pytest --cov=src tests/
```

---

## 📊 MVP Roadmap

- [x] Proje yapısı ve GitHub setup
- [x] FastAPI backend scaffold
- [x] Dashboard UI şablonu
- [ ] **Faz 1:** Sentetik veri üretimi (GAN-tabanlı)
- [ ] **Faz 2:** GNN hasar tahmin modeli eğitimi
- [ ] **Faz 3:** RL rota optimizasyonu implementasyonu
- [ ] **Faz 4:** Dashboard entegrasyonu
- [ ] **Faz 5:** İstanbul pilot senaryosu
- [ ] **Faz 6:** AFAD entegrasyonu

📖 Detaylı yol haritası: [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)

---

## 🤝 Katkıda Bulunma

Proje açıktır ve katkılara açığız! 

### Adımlar:

1. **Fork** et
2. Feature branch oluştur (`git checkout -b feature/AmazingFeature`)
3. Değişiklikleri commit et (`git commit -m 'Add AmazingFeature'`)
4. Branch'ı push et (`git push origin feature/AmazingFeature`)
5. **Pull Request** aç

### Kod Standartları:

```bash
# Kodu formatla
black src/

# Import sırasını düzenle
isort src/

# Type checking
mypy src/

# Linting
pylint src/
```

---

## 📝 Lisans

Bu proje **MIT License** altında lisanslanmıştır. Detaylar için [`LICENSE`](LICENSE) dosyasına bakın.

---

## 👥 Geliştirici Ekibi

- **Takım Adı:** Opti-Logistix Dev Team
- **Proje Yöneticisi:** [Tarik Özküçük]
- **AI/ML Lead:** [Takım Üyesi]
- **Backend Lead:** [Takım Üyesi]

---

## 💬 İletişim & Destek

- 📧 Email: [project@example.com]
- 💬 Discord: [Sunucu Linki]
- 📌 Issues: [GitHub Issues](https://github.com/yourusername/opti-logistix/issues)

---

## 🌟 Teşekkürler

- **OSMnx** ve **OpenStreetMap** topluluğu
- **PyTorch Geometric** takımı
- **Stable Baselines3** geliştiricileri

---

**Son Güncelleme:** Ocak 2026  
**Versiyon:** 0.1.0 (MVP)

```
Made with ❤️ for disaster resilience
```
