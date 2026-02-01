# 🚀 Opti-Logistix: Afet Lojistik Optimizasyon Sistemi

> **"Doğru kaynak, doğru zamanda, doğru yere"**

## 🎯 Proje Özeti

Opti-Logistix, deprem ve sel gibi geniş çaplı afetlerde:
- 🚑 Ambulans ve yardım araçlarının **en hızlı rotayı** bulmasını
- 📦 Sınırlı kaynakların (su, ilaç, iş makinesi) **doğru noktalara** sevk edilmesini
- 📊 Yöneticilerin **görsel paneller** ile hızlı karar vermesini sağlar

## 🧠 Teknoloji Stack

| Katman | Teknoloji | Amaç |
|--------|-----------|------|
| **Simülasyon** | SUMO + OSMnx | Trafik ve yol ağı simülasyonu |
| **Graph AI** | PyTorch Geometric (GNN) | Hasar öngörüsü ve durum analizi |
| **Karar** | Stable Baselines3 (RL) | Dinamik rota optimizasyonu |
| **Backend** | FastAPI + PostgreSQL | API ve veri yönetimi |
| **Frontend** | React + Deck.gl | Görsel karar destek paneli |

## 📁 Proje Yapısı

```
opti-logistix/
├── README.md
├── docs/
│   └── MVP_ROADMAP.md           # Detaylı yol haritası
├── data/
│   ├── synthetic/               # Sentetik afet verileri
│   ├── maps/                    # OSM harita verileri
│   └── scenarios/               # Afet senaryoları
├── src/
│   ├── simulation/              # SUMO simülasyon modülleri
│   ├── models/
│   │   ├── gnn/                 # Graf Sinir Ağları
│   │   └── rl/                  # Pekiştirmeli Öğrenme
│   ├── api/                     # FastAPI backend
│   └── dashboard/               # React frontend
├── notebooks/                   # Jupyter araştırma notebookları
├── tests/                       # Test dosyaları
└── docker/                      # Container yapılandırmaları
```

## 🚀 Hızlı Başlangıç

```bash
# Repoyu klonla
cd opti-logistix

# Python ortamını kur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Development sunucusunu başlat
uvicorn src.api.main:app --reload
```

## 📊 MVP Hedefleri (48 Saat)

- [x] Proje yapısı oluşturma
- [ ] Sentetik veri üretimi (İstanbul bölgesi)
- [ ] Basit GNN hasar tahmin modeli
- [ ] RL tabanlı rota optimizasyonu
- [ ] Web dashboard (harita + grafikler)
- [ ] Demo senaryosu hazırlama

## 📄 Lisans

MIT License

---

**Geliştirici:** Hackathon Takımı
**Tarih:** Ocak 2026
