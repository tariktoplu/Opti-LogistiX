# 🗺️ Opti-Logistix MVP Yol Haritası

> **Hedef:** 48 saatte çalışan bir prototip oluşturmak
> **Tarih:** 30 Ocak 2026

---

## 📋 İçindekiler

1. [Proje Vizyonu](#-proje-vizyonu)
2. [MVP Kapsamı](#-mvp-kapsamı)
3. [Teknik Mimari](#-teknik-mimari)
4. [Geliştirme Aşamaları](#-geliştirme-aşamaları)
5. [Veri Stratejisi](#-veri-stratejisi)
6. [Model Tasarımı](#-model-tasarımı)
7. [Demo Senaryosu](#-demo-senaryosu)

---

## 🎯 Proje Vizyonu

### Problem

```
┌─────────────────────────────────────────────────────────────────┐
│  🌍 AFET DURUMU                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ Hasarlı yollar nedeniyle ambulanslar hedefe ulaşamıyor     │
│  ❌ Sınırlı kaynaklar yanlış noktalara sevk ediliyor           │
│  ❌ Yöneticiler karmaşık veriler arasında boğuluyor            │
│  ❌ Reaktif (olay sonrası) yaklaşım zaman kaybettiriyor        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Çözüm

```
┌─────────────────────────────────────────────────────────────────┐
│  🚀 OPTI-LOGISTIX                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ GNN ile yol hasar tahmini yapıyor                          │
│  ✅ RL ile optimal rota hesaplıyor                             │
│  ✅ Kaynak önceliklendirmesi yapıyor                           │
│  ✅ Görsel dashboard ile karar desteği sunuyor                 │
│                                                                 │
│  📍 AFAD'a "Karar Destek Katmanı" olarak entegre olur          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 MVP Kapsamı

### ✅ MVP'de OLACAKLAR (Must Have)

| # | Özellik | Öncelik | Süre |
|---|---------|---------|------|
| 1 | İstanbul pilot bölgesi harita verisi | P0 | 2 saat |
| 2 | Sentetik afet senaryoları (3 adet) | P0 | 4 saat |
| 3 | Basit GNN hasar tahmin modeli | P0 | 8 saat |
| 4 | A* + RL hibrit rota algoritması | P0 | 8 saat |
| 5 | REST API (FastAPI) | P0 | 4 saat |
| 6 | Web Dashboard (React + Harita) | P0 | 12 saat |
| 7 | Demo senaryosu ve sunum | P0 | 6 saat |

**Toplam:** ~44 saat (4 saat buffer)

### ⚠️ SONRAYA BIRAKILACAKLAR (Nice to Have)

- Gerçek zamanlı trafik entegrasyonu
- SUMO tam simülasyon
- Hastane kapasite API entegrasyonu
- Mobil uygulama
- Çoklu şehir desteği
- GAN ile gelişmiş sentetik veri

---

## 🏗️ Teknik Mimari

### Sistem Bileşenleri

```
┌─────────────────────────────────────────────────────────────────┐
│                      OPTI-LOGISTIX MİMARİSİ                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   VERİ       │    │    MODEL     │    │   SUNUM      │      │
│  │   KATMANI    │───▶│    KATMANI   │───▶│   KATMANI    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ • OSM Harita │    │ • GNN Hasar  │    │ • REST API   │      │
│  │ • Sentetik   │    │   Tahmin     │    │ • Dashboard  │      │
│  │   Senaryolar │    │ • RL Rota    │    │ • Isı Harita │      │
│  │ • Yol Ağı    │    │   Optimiz.   │    │ • Öneriler   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Veri Akışı

```
                    ┌────────────────┐
                    │  AFET OLUŞTU   │
                    │  (Senaryo)     │
                    └───────┬────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     VERİ TOPLAMA                            │
│  • Yol ağı graf yapısına dönüştürülür                      │
│  • Düğümler (nodes) = Kavşaklar                            │
│  • Kenarlar (edges) = Yollar                               │
│  • Her kenar: uzunluk, genişlik, trafik, hasar skoru       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     GNN HASAR TAHMİNİ                       │
│  • Her kenar için hasar olasılığı hesaplanır               │
│  • Komşu kenarların durumu da değerlendirilir              │
│  • Çıktı: Kenar ağırlıkları (0-1 hasar skoru)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     RL ROTA OPTİMİZASYONU                   │
│  • Ajan: Ambulans/yardım aracı                             │
│  • Durum: Mevcut konum + hedef + yol durumları             │
│  • Aksiyon: Bir sonraki kavşağa git                        │
│  • Ödül: -süre + aciliyet - risk                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     KARAR DESTEK PANELİ                     │
│  • Isı haritası: Hasar yoğunluğu                           │
│  • Önerilen rotalar: Yeşil çizgiler                        │
│  • Acil bölgeler: Kırmızı işaretler                        │
│  • Kaynak durumu: Progress barlar                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 Geliştirme Aşamaları

### AŞAMA 1: Temel Kurulum (0-4 saat)

```bash
# Görevler
□ Proje yapısı oluşturma
□ Git repository başlatma  
□ Python sanal ortam kurulumu
□ Temel bağımlılıkların yüklenmesi
□ Docker yapılandırması
```

**Çıktı:** Çalışan bir geliştirme ortamı

---

### AŞAMA 2: Veri Katmanı (4-10 saat)

#### 2.1 Harita Verisi (OSMnx)

```python
# İstanbul Kadıköy bölgesi için örnek
import osmnx as ox

# Bölgeyi tanımla
place = "Kadıköy, Istanbul, Turkey"

# Yol ağını çek
G = ox.graph_from_place(place, network_type='drive')

# Graf istatistikleri
print(f"Düğüm sayısı: {G.number_of_nodes()}")
print(f"Kenar sayısı: {G.number_of_edges()}")
```

#### 2.2 Sentetik Afet Senaryoları

| Senaryo | Deprem Şiddeti | Etkilenen Alan | Hasarlı Yol % |
|---------|----------------|----------------|---------------|
| S1: Hafif | 5.5 Mw | Merkez | %15 |
| S2: Orta | 6.5 Mw | Geniş alan | %35 |
| S3: Şiddetli | 7.2 Mw | Tüm bölge | %60 |

```python
# Senaryo üretim mantığı
def generate_scenario(graph, severity):
    """
    Deprem şiddetine göre yol hasarı senaryosu üret
    
    Hasar olasılığı = f(şiddet, yol yaşı, zemin tipi, köprü mü?)
    """
    damaged_edges = []
    for u, v, data in graph.edges(data=True):
        # Basit hasar modeli
        base_prob = severity / 10  # 0-1 arası
        
        # Köprüler daha riskli
        if data.get('bridge') == 'yes':
            base_prob *= 1.5
            
        # Hasar kararı
        if random.random() < base_prob:
            damage_level = random.uniform(0.3, 1.0)
            damaged_edges.append((u, v, damage_level))
    
    return damaged_edges
```

**Çıktı:** 3 adet sentetik afet senaryosu JSON dosyaları

---

### AŞAMA 3: GNN Hasar Tahmin Modeli (10-18 saat)

#### 3.1 Model Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                     GNN HASAR TAHMİN MODELİ                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Giriş Özellikleri (Edge Features):                        │
│  • Yol uzunluğu (metre)                                    │
│  • Yol genişliği (şerit sayısı)                           │
│  • Yol tipi (ana arter, sokak, köprü)                     │
│  • Zemin sınıfı (kaya, alüvyon, dolgu)                    │
│  • Bina yoğunluğu (çevre 100m)                            │
│                                                             │
│  Model:                                                     │
│  GraphSAGE (2 katman) → ReLU → Dropout → Linear → Sigmoid  │
│                                                             │
│  Çıkış:                                                     │
│  Her kenar için hasar olasılığı (0-1)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2 PyTorch Geometric Implementasyonu

```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

class DamagePredictor(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        self.classifier = torch.nn.Linear(hidden_channels, out_channels)
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.classifier(x)
        return torch.sigmoid(x)
```

**Çıktı:** Eğitilmiş GNN modeli (`damage_predictor.pt`)

---

### AŞAMA 4: RL Rota Optimizasyonu (18-26 saat)

#### 4.1 RL Ortamı Tasarımı

```python
import gymnasium as gym
import numpy as np

class DisasterRoutingEnv(gym.Env):
    """
    Afet durumunda ambulans rotalama ortamı
    """
    
    def __init__(self, graph, damage_scores, start, goal, urgency):
        super().__init__()
        self.graph = graph
        self.damage_scores = damage_scores
        self.start = start
        self.goal = goal
        self.urgency = urgency
        self.current_node = start
        
        # Aksiyon: Komşu düğümlerden birine git
        self.action_space = gym.spaces.Discrete(max_neighbors)
        
        # Durum: Mevcut konum embedding + hedef + çevre hasarları
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(feature_dim,)
        )
    
    def step(self, action):
        # Seçilen komşuya git
        neighbors = list(self.graph.neighbors(self.current_node))
        next_node = neighbors[action]
        
        # Yol hasarını al
        edge_damage = self.damage_scores.get(
            (self.current_node, next_node), 0
        )
        
        # Seyahat süresini hesapla (hasar = yavaşlama)
        base_time = self.graph[self.current_node][next_node]['length'] / 50
        actual_time = base_time * (1 + edge_damage * 2)
        
        # Ödül hesapla
        reward = -actual_time  # Zaman cezası
        reward -= edge_damage * 10  # Risk cezası
        
        # Hedefe ulaştı mı?
        self.current_node = next_node
        done = (next_node == self.goal)
        
        if done:
            reward += self.urgency * 50  # Aciliyet bonusu
        
        return self._get_obs(), reward, done, False, {}
    
    def reset(self):
        self.current_node = self.start
        return self._get_obs(), {}
```

#### 4.2 PPO ile Eğitim

```python
from stable_baselines3 import PPO

# Ortamı oluştur
env = DisasterRoutingEnv(graph, damage_scores, start, goal, urgency=0.8)

# PPO modeli
model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64
)

# Eğit
model.learn(total_timesteps=50000)

# Kaydet
model.save("routing_agent.zip")
```

**Çıktı:** Eğitilmiş RL ajanı (`routing_agent.zip`)

---

### AŞAMA 5: Backend API (26-30 saat)

#### 5.1 FastAPI Endpoints

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Opti-Logistix API")

# Veri modelleri
class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    vehicle_type: str = "ambulance"
    urgency: float = 0.5

class RouteResponse(BaseModel):
    route: list[tuple[float, float]]
    estimated_time: float
    risk_score: float
    alternative_routes: list

# Endpoints
@app.post("/api/v1/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Optimal rota hesapla"""
    pass

@app.get("/api/v1/damage-map")
async def get_damage_map(scenario_id: str):
    """Hasar haritası döndür"""
    pass

@app.get("/api/v1/resources/{resource_type}")
async def get_resource_status(resource_type: str):
    """Kaynak durumunu döndür"""
    pass

@app.post("/api/v1/allocate")
async def allocate_resource(resource_id: str, target_zone: str):
    """Kaynak tahsis et"""
    pass
```

**Çıktı:** Çalışan REST API

---

### AŞAMA 6: Web Dashboard (30-42 saat)

#### 6.1 Dashboard Bileşenleri

```
┌─────────────────────────────────────────────────────────────────┐
│  🎛️ OPTI-LOGISTIX KARAR DESTEK PANELİ                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────┐ ┌──────────────────────────┐ │
│  │                              │ │  📊 DURUM PANELİ         │ │
│  │                              │ ├──────────────────────────┤ │
│  │       🗺️ HARİTA             │ │  Aktif Ambulans: 12      │ │
│  │                              │ │  Bekleyen Çağrı: 8       │ │
│  │   • Hasar ısı haritası       │ │  Hasarlı Yol: %23        │ │
│  │   • Araç konumları           │ │  ━━━━━━━━━━━━━━━━━━━━━   │ │
│  │   • Önerilen rotalar         │ │                          │ │
│  │   • Acil bölgeler            │ │  🏥 Hastane Kapasitesi   │ │
│  │                              │ │  Merkez: ████████░░ 80%  │ │
│  │                              │ │  Doğu:   ██████████ 100% │ │
│  │                              │ │  Batı:   ████░░░░░░ 40%  │ │
│  └──────────────────────────────┘ └──────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  💡 AI ÖNERİLERİ                                         │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ⚠️ A-12 Ambulansını Batı Hastanesi'ne yönlendirin       │  │
│  │     → Merkez Hastane'ye göre 8 dk daha hızlı             │  │
│  │                                                          │  │
│  │  🚧 D-400 karayolu %65 hasarlı, alternatif rota önerisi  │  │
│  │     → Sahil yolu üzerinden devam edin                    │  │
│  │                                                          │  │
│  │  📦 Kadıköy bölgesi acil su ihtiyacı (Öncelik: YÜKSEK)  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.2 React + Deck.gl Harita

```jsx
import React from 'react';
import DeckGL from '@deck.gl/react';
import { PathLayer, ScatterplotLayer, HeatmapLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl';

function DisasterMap({ damageData, routes, vehicles }) {
  const layers = [
    // Hasar ısı haritası
    new HeatmapLayer({
      id: 'damage-heatmap',
      data: damageData,
      getPosition: d => [d.lon, d.lat],
      getWeight: d => d.damage_score,
      radiusPixels: 60,
      colorRange: [
        [0, 255, 0, 100],    // Yeşil = Güvenli
        [255, 255, 0, 150],  // Sarı = Dikkat
        [255, 0, 0, 200]     // Kırmızı = Hasarlı
      ]
    }),
    
    // Önerilen rotalar
    new PathLayer({
      id: 'routes',
      data: routes,
      getPath: d => d.path,
      getColor: d => d.is_optimal ? [0, 200, 100] : [100, 100, 100],
      getWidth: d => d.is_optimal ? 8 : 4
    }),
    
    // Araç konumları
    new ScatterplotLayer({
      id: 'vehicles',
      data: vehicles,
      getPosition: d => [d.lon, d.lat],
      getRadius: 200,
      getFillColor: d => getVehicleColor(d.type),
      pickable: true
    })
  ];
  
  return (
    <DeckGL
      initialViewState={ISTANBUL_VIEW}
      controller={true}
      layers={layers}
    >
      <Map mapStyle="mapbox://styles/mapbox/dark-v11" />
    </DeckGL>
  );
}
```

**Çıktı:** Çalışan web dashboard

---

### AŞAMA 7: Demo Hazırlığı (42-48 saat)

#### Demo Senaryosu

```
┌─────────────────────────────────────────────────────────────────┐
│  🎬 DEMO AKIŞI (5 DAKİKA)                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. BAŞLANGIÇ DURUMU (0:00 - 0:30)                             │
│     "İstanbul Kadıköy bölgesinde 6.5 şiddetinde deprem oldu"   │
│     → Dashboard normal görünümde                                │
│                                                                 │
│  2. DEPREM TETİKLENİR (0:30 - 1:00)                            │
│     → "Deprem Senaryosu" butonuna tıkla                        │
│     → Hasar ısı haritası belirir                               │
│     → Hasarlı yollar kırmızıya döner                           │
│                                                                 │
│  3. ROTA HESAPLAMA (1:00 - 2:30)                               │
│     → Ambulans konumu seç                                       │
│     → Hedef (yaralı bölge) seç                                 │
│     → "Rota Hesapla" tıkla                                     │
│     → Sistem 2 rota önerir:                                    │
│       - Standart (25 dk, %45 risk)                             │
│       - Optimal (18 dk, %12 risk)                              │
│                                                                 │
│  4. KAYNAK TAHSİSİ (2:30 - 3:30)                               │
│     → Farklı bölgelerdeki ihtiyaçlar gösterilir               │
│     → AI: "B bölgesine su kamyonu yönlendirin"                 │
│     → Tahsis onaylandığında güncellenir                        │
│                                                                 │
│  5. SONUÇ (3:30 - 5:00)                                        │
│     → "Bu sistem AFAD'a karar destek katmanı olarak eklenir"  │
│     → "Reaktiften proaktif yönetime geçiş"                     │
│     → "Lojistik gecikmeleri %40 azaltma potansiyeli"           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Veri Stratejisi

### Sentetik Veri Üretimi

| Veri Tipi | Kaynak | Format |
|-----------|--------|--------|
| Yol ağı | OSMnx | NetworkX Graph |
| Zemin sınıfı | Jeo-portal (mock) | GeoJSON |
| Bina yoğunluğu | OSM buildings | Polygon count |
| Deprem senaryoları | Hesaplanmış | JSON |
| Araç konumları | Simüle | Real-time stream |

### Örnek Senaryo JSON

```json
{
  "scenario_id": "IST_EQ_6.5_001",
  "earthquake": {
    "magnitude": 6.5,
    "epicenter": [29.0238, 40.9876],
    "depth_km": 12,
    "timestamp": "2026-01-30T14:30:00Z"
  },
  "damage_zones": [
    {
      "zone_id": "Z1",
      "center": [29.0312, 40.9901],
      "radius_m": 2000,
      "damage_level": "severe",
      "affected_roads": 45
    }
  ],
  "resource_status": {
    "ambulances": 12,
    "fire_trucks": 8,
    "water_trucks": 5,
    "rescue_teams": 6
  }
}
```

---

## 🧠 Model Tasarımı

### GNN Hasar Tahmin Detayları

| Hiperparametre | Değer | Açıklama |
|----------------|-------|----------|
| Hidden channels | 64 | Ara katman boyutu |
| Layers | 2 | GraphSAGE katman sayısı |
| Dropout | 0.3 | Overfitting önlemi |
| Learning rate | 0.001 | Adam optimizer |
| Epochs | 100 | Eğitim döngüsü |

### RL Ajan Detayları

| Hiperparametre | Değer | Açıklama |
|----------------|-------|----------|
| Algoritma | PPO | Policy Gradient |
| Policy | MlpPolicy | Fully connected |
| Learning rate | 3e-4 | Adam optimizer |
| Steps | 2048 | Güncelleme adımları |
| Batch size | 64 | Mini-batch |
| Total timesteps | 50000 | Toplam eğitim |

### Ödül Fonksiyonu

```
R = w1 × (-t) + w2 × (urgency) - w3 × (risk)

Burada:
- t: Seyahat süresi (dakika)
- urgency: Hedef bölgenin aciliyet skoru (0-1)
- risk: Geçilen yolların hasar skoru toplamı

Ağırlıklar (varsayılan):
- w1 = 1.0 (zaman)
- w2 = 50.0 (aciliyet bonusu)
- w3 = 10.0 (risk cezası)
```

---

## 🎤 Jüri Sunum Notları

### Problem (30 saniye)
> "2023 Kahramanmaraş depreminde ambulansların %30'u hasarlı yollar nedeniyle hedefe zamanında ulaşamadı. Yardım malzemeleri yanlış bölgelere gönderildi. Koordinasyon kaosuna dönüştü."

### Çözüm (30 saniye)
> "Opti-Logistix, yapay zeka ile afet lojistiğini optimize eder. GNN ile hangi yolların hasarlı olacağını tahmin eder, RL ile en optimal rotayı hesaplar. AFAD'a 'karar destek katmanı' olarak entegre olur."

### Demo (3 dakika)
> Canlı dashboard gösterimi

### Etki (30 saniye)
> "Lojistik gecikmeleri %40 azaltma, kaynak israfını %50 düşürme potansiyeli. 6 Akdeniz ülkesinde uygulanabilir."

### Human-in-the-Loop (15 saniye)
> "Sistem tamamen otonom değil. AI öneri verir, son karar her zaman operatörde. Bu güvenilirlik ve etik sorumluluk sağlar."

---

## ✅ Başarı Kriterleri

| Metrik | Hedef |
|--------|-------|
| Demo çalışıyor | ✓ |
| Harita görselleştirme | Real-time güncelleme |
| Rota hesaplama süresi | < 2 saniye |
| Hasar tahmini doğruluğu | > %70 (sentetik veri) |
| Jüri "wow" anı | Dashboard + AI önerileri |

---

**Bir sonraki adım:** `AŞAMA 1: Temel Kurulum` ile başlayalım mı? 🚀
