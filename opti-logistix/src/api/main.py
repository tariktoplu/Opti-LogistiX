"""
Opti-Logistix FastAPI Backend
Afet lojistik optimizasyonu için REST API
OSMnx entegrasyonu ile gerçek harita verileri
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import random

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.graph_loader import GraphLoader, OSMNX_AVAILABLE
from data.scenario_generator import ScenarioGenerator, DisasterScenario
from models.gnn.damage_predictor import DamagePredictor
from models.rl.routing_agent import RoutingAgent, Route


# =============================================================================
# Pydantic Models
# =============================================================================

class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

class RouteRequest(BaseModel):
    start: Coordinates
    end: Coordinates
    vehicle_type: str = Field(default="ambulance")
    urgency: float = Field(default=0.5, ge=0, le=1)
    method: str = Field(default="astar")

class RouteResponse(BaseModel):
    success: bool
    route: Optional[dict] = None
    alternatives: List[dict] = []
    message: str = ""

class ScenarioRequest(BaseModel):
    magnitude: float = Field(..., ge=4.0, le=9.0)
    epicenter: Optional[Coordinates] = None
    scenario_id: Optional[str] = None

class ResourceStatus(BaseModel):
    resource_id: str
    resource_type: str
    status: str
    location: Coordinates
    assigned_zone: Optional[str] = None

class AIRecommendation(BaseModel):
    id: str
    type: str
    priority: str
    message: str
    details: dict


# =============================================================================
# Application State
# =============================================================================

class AppState:
    """Uygulama durumu"""
    
    def __init__(self):
        self.graph = None
        self.loader = GraphLoader()
        self.predictor = DamagePredictor()
        self.agent = None
        self.hospitals: List[int] = []
        self.depots: List[int] = []
        self.current_scenario_name: Optional[str] = None
        self.damage_multiplier: float = 0.0
        self.resources: Dict[str, ResourceStatus] = {}
        self.recommendations: List[AIRecommendation] = []
        self.map_bounds: dict = {}
        
        # Haritayı yükle
        self._load_map()
    
    def _load_map(self, place: str = "Kadikoy, Istanbul, Turkey"):
        """Gerçek harita yükle"""
        logger.info(f"Harita yükleniyor: {place}")
        
        # OSMnx ile yükle
        self.graph = self.loader.load_from_place(place)
        
        # Hastane ve depo ekle
        self.graph, self.hospitals, self.depots = self.loader.add_disaster_data(
            self.graph, 
            damage_multiplier=0.0,  # Başlangıçta hasar yok
            num_hospitals=5,
            num_depots=5
        )
        
        # Harita sınırlarını kaydet
        self.map_bounds = self.loader.get_graph_bounds(self.graph)
        
        # Routing agent
        self.agent = RoutingAgent(self.graph, {})
        
        # Kaynakları oluştur
        self._init_resources()
        
        stats = self.loader.get_graph_stats(self.graph)
        logger.info(f"Harita hazır: {stats['nodes']} kavşak, {stats['edges']} yol")
    
    def _init_resources(self):
        """Kaynaklari hastane ve depolara yerleştir"""
        self.resources = {}
        
        # Ambulanslar hastanelerde
        for i, hospital in enumerate(self.hospitals[:3]):
            node_data = self.graph.nodes[hospital]
            self.resources[f"AMB-{i+1:03d}"] = ResourceStatus(
                resource_id=f"AMB-{i+1:03d}",
                resource_type="ambulance",
                status="available",
                location=Coordinates(
                    lat=node_data.get('y', 41.0),
                    lon=node_data.get('x', 29.0)
                )
            )
        
        # İtfaiye depolarda
        for i, depot in enumerate(self.depots[:2]):
            node_data = self.graph.nodes[depot]
            self.resources[f"FIRE-{i+1:03d}"] = ResourceStatus(
                resource_id=f"FIRE-{i+1:03d}",
                resource_type="fire_truck",
                status="available",
                location=Coordinates(
                    lat=node_data.get('y', 41.0),
                    lon=node_data.get('x', 29.0)
                )
            )
    
    def apply_scenario(self, scenario_name: str, magnitude: float):
        """Afet senaryosu uygula"""
        self.current_scenario_name = scenario_name
        
        # Hasar çarpanı
        damage_map = {"hafif": 0.3, "orta": 0.6, "siddetli": 1.0}
        self.damage_multiplier = damage_map.get(scenario_name, 0.5)
        
        # Yollara hasar ekle
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            base_damage = random.random() * self.damage_multiplier
            data['damage_prob'] = min(1.0, base_damage)
            
            base_length = data.get('length', 100)
            data['weight'] = base_length * (1 + data['damage_prob'] * 15)
            
            if data['damage_prob'] > 0.8:
                data['damage_level'] = 'critical'
            elif data['damage_prob'] > 0.5:
                data['damage_level'] = 'moderate'
            else:
                data['damage_level'] = 'safe'
        
        # Agent güncelle
        damage_scores = {
            f"{u}_{v}_{k}": data.get('damage_prob', 0)
            for u, v, k, data in self.graph.edges(keys=True, data=True)
        }
        self.agent = RoutingAgent(self.graph, damage_scores)
        
        # AI önerileri
        self._generate_recommendations()
        
        logger.info(f"Senaryo uygulandı: {scenario_name} (M{magnitude})")
    
    def clear_scenario(self):
        """Senaryoyu temizle"""
        self.current_scenario_name = None
        self.damage_multiplier = 0.0
        
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            data['damage_prob'] = 0.0
            data['damage_level'] = 'safe'
            data['weight'] = data.get('length', 100)
        
        self.agent = RoutingAgent(self.graph, {})
        self.recommendations = []
    
    def _generate_recommendations(self):
        """AI önerileri oluştur"""
        self.recommendations = []
        
        # Kritik hasar uyarısı
        critical_count = sum(
            1 for _, _, data in self.graph.edges(data=True)
            if data.get('damage_level') == 'critical'
        )
        
        if critical_count > 0:
            self.recommendations.append(AIRecommendation(
                id="WARN-CRITICAL",
                type="warning",
                priority="high",
                message=f"{critical_count} yol segmenti kritik hasar altında!",
                details={"critical_roads": critical_count}
            ))
        
        # Ambulans önerisi
        available = [r for r in self.resources.values() if r.status == "available"]
        if available and self.hospitals:
            self.recommendations.append(AIRecommendation(
                id="ALLOC-AMB",
                type="allocation",
                priority="medium",
                message=f"{len(available)} araç müsait. Kritik bölgelere sevk önerilir.",
                details={"available_resources": len(available)}
            ))


# Global state
state = AppState()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Opti-Logistix API",
    description="Afet Lojistik Optimizasyon Sistemi - OSMnx Entegrasyonu",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/")
async def root():
    return {
        "name": "Opti-Logistix API",
        "version": "0.2.0",
        "osmnx_available": OSMNX_AVAILABLE,
        "graph_nodes": state.graph.number_of_nodes() if state.graph else 0,
        "graph_edges": state.graph.number_of_edges() if state.graph else 0,
        "scenario": state.current_scenario_name,
        "map_center": state.map_bounds
    }


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "osmnx": OSMNX_AVAILABLE
    }


# ----- HARİTA YÖNETİMİ -----

@app.post("/api/v1/map/load")
async def load_map(place: str = "Kadikoy, Istanbul, Turkey"):
    """Yeni bölge haritası yükle"""
    try:
        state._load_map(place)
        return {
            "success": True,
            "place": place,
            "nodes": state.graph.number_of_nodes(),
            "edges": state.graph.number_of_edges(),
            "bounds": state.map_bounds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/map/bounds")
async def get_map_bounds():
    """Harita sınırlarını döndür"""
    return state.map_bounds


@app.get("/api/v1/map/edges")
async def get_map_edges():
    """Tüm yol segmentlerini GeoJSON formatında döndür"""
    edges = state.loader.get_edges_as_geojson(state.graph)
    return {
        "type": "FeatureCollection",
        "features": edges,
        "count": len(edges)
    }


@app.get("/api/v1/map/nodes")
async def get_map_nodes():
    """Tüm düğümleri döndür (hastane, depo, kavşak)"""
    nodes = state.loader.get_nodes_as_geojson(state.graph)
    return {
        "nodes": nodes,
        "hospitals": [n for n in nodes if n['type'] == 'hospital'],
        "depots": [n for n in nodes if n['type'] == 'depot'],
        "count": len(nodes)
    }


# ----- SENARYO YÖNETİMİ -----

@app.post("/api/v1/scenarios/preset/{scenario_name}")
async def activate_preset_scenario(scenario_name: str):
    """Senaryo aktive et (hafif, orta, siddetli)"""
    magnitude_map = {"hafif": 5.5, "orta": 6.5, "siddetli": 7.2}
    
    if scenario_name not in magnitude_map:
        raise HTTPException(400, f"Geçersiz senaryo. Geçerli: hafif, orta, siddetli")
    
    state.apply_scenario(scenario_name, magnitude_map[scenario_name])
    
    stats = state.loader.get_graph_stats(state.graph)
    
    return {
        "success": True,
        "scenario": scenario_name,
        "magnitude": magnitude_map[scenario_name],
        "damage_stats": stats.get('damage_levels', {})
    }


@app.delete("/api/v1/scenarios/current")
async def clear_scenario():
    """Senaryoyu temizle"""
    state.clear_scenario()
    return {"success": True, "message": "Senaryo temizlendi"}


@app.get("/api/v1/scenarios/current")
async def get_current_scenario():
    """Mevcut senaryo bilgisi"""
    if not state.current_scenario_name:
        return {"active": False}
    
    stats = state.loader.get_graph_stats(state.graph)
    return {
        "active": True,
        "name": state.current_scenario_name,
        "damage_multiplier": state.damage_multiplier,
        "stats": stats
    }


# ----- ROTA YÖNETİMİ -----

@app.post("/api/v1/route")
async def calculate_route(request: RouteRequest):
    """Optimal rota hesapla"""
    try:
        start_node = state.loader.find_nearest_node(
            state.graph, request.start.lat, request.start.lon
        )
        end_node = state.loader.find_nearest_node(
            state.graph, request.end.lat, request.end.lon
        )
        
        if start_node == end_node:
            return {"success": False, "message": "Başlangıç ve hedef aynı nokta"}
        
        # GraphLoader ile rota bul
        route = state.loader.find_route(state.graph, start_node, end_node, weight='weight')
        
        if not route:
            return {"success": False, "message": "Rota bulunamadı"}
        
        # Tahmini süre hesapla (50 km/h ortalama hız)
        estimated_time = route['distance_km'] / 50 * 60  # dakika
        
        return {
            "success": True,
            "route": {
                "path_coords": route['path_coords'],
                "distance_km": round(route['distance_km'], 2),
                "risk_score": round(route['risk_score'], 3),
                "estimated_time": round(estimated_time, 1),
                "segments": route['num_segments']
            },
            "message": "Rota hesaplandı"
        }
        
    except Exception as e:
        logger.error(f"Rota hatası: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/v1/route/hospital")
async def route_to_nearest_hospital(lat: float, lon: float):
    """En yakın hastaneye rota"""
    start_node = state.loader.find_nearest_node(state.graph, lat, lon)
    
    best_route = None
    best_distance = float('inf')
    
    for hospital in state.hospitals:
        route = state.loader.find_route(state.graph, start_node, hospital, weight='weight')
        if route and route['distance_km'] < best_distance:
            best_distance = route['distance_km']
            best_route = route
    
    if not best_route:
        return {"success": False, "message": "Hastaneye rota bulunamadı"}
    
    return {
        "success": True,
        "route": best_route,
        "hospital": state.graph.nodes[hospital].get('name', 'Hastane')
    }


# ----- KAYNAK YÖNETİMİ -----

@app.get("/api/v1/resources")
async def list_resources():
    return {
        "resources": [r.dict() for r in state.resources.values()],
        "hospitals": len(state.hospitals),
        "depots": len(state.depots)
    }


# ----- AI ÖNERİLERİ -----

@app.get("/api/v1/recommendations")
async def get_recommendations():
    return {
        "recommendations": [r.dict() for r in state.recommendations],
        "count": len(state.recommendations)
    }


# ----- GRAFİK İSTATİSTİKLERİ -----

@app.get("/api/v1/stats")
async def get_stats():
    return state.loader.get_graph_stats(state.graph)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
