"""
Opti-Logistix FastAPI Backend
Afet lojistik optimizasyonu için REST API
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.graph_loader import GraphLoader
from data.scenario_generator import ScenarioGenerator, DisasterScenario
from models.gnn.damage_predictor import DamagePredictor
from models.rl.routing_agent import RoutingAgent, Route


# =============================================================================
# Pydantic Models
# =============================================================================

class Coordinates(BaseModel):
    """Koordinat çifti"""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class RouteRequest(BaseModel):
    """Rota hesaplama isteği"""
    start: Coordinates
    end: Coordinates
    vehicle_type: str = Field(default="ambulance")
    urgency: float = Field(default=0.5, ge=0, le=1)
    method: str = Field(default="astar")


class RouteResponse(BaseModel):
    """Rota hesaplama yanıtı"""
    success: bool
    route: Optional[dict] = None
    alternatives: List[dict] = []
    message: str = ""


class ScenarioRequest(BaseModel):
    """Senaryo oluşturma isteği"""
    magnitude: float = Field(..., ge=4.0, le=9.0)
    epicenter: Optional[Coordinates] = None
    scenario_id: Optional[str] = None


class DamageMapResponse(BaseModel):
    """Hasar haritası yanıtı"""
    scenario_id: str
    edges: List[dict]
    zones: List[dict]
    stats: dict


class ResourceStatus(BaseModel):
    """Kaynak durumu"""
    resource_id: str
    resource_type: str
    status: str
    location: Coordinates
    assigned_zone: Optional[str] = None


class AIRecommendation(BaseModel):
    """AI önerisi"""
    id: str
    type: str  # route, allocation, warning
    priority: str  # high, medium, low
    message: str
    details: dict


# =============================================================================
# Application State
# =============================================================================

class AppState:
    """Uygulama durumu (in-memory)"""
    
    def __init__(self):
        self.graph = None
        self.loader = GraphLoader()
        self.predictor = DamagePredictor()
        self.agent = None
        self.current_scenario: Optional[DisasterScenario] = None
        self.resources: Dict[str, ResourceStatus] = {}
        self.recommendations: List[AIRecommendation] = []
        
        # Demo grafı yükle
        self._load_demo_graph()
    
    def _load_demo_graph(self):
        """Demo graf yükle"""
        logger.info("Demo graf yükleniyor...")
        self.graph = self.loader._create_demo_graph()
        self.agent = RoutingAgent(self.graph, {})
        self._init_demo_resources()
        logger.info(f"Graf hazır: {self.graph.number_of_nodes()} düğüm")
    
    def _init_demo_resources(self):
        """Demo kaynakları oluştur"""
        nodes = list(self.graph.nodes())
        
        resource_types = [
            ("AMB-001", "ambulance", nodes[0]),
            ("AMB-002", "ambulance", nodes[5]),
            ("AMB-003", "ambulance", nodes[12]),
            ("FIRE-001", "fire_truck", nodes[3]),
            ("FIRE-002", "fire_truck", nodes[18]),
            ("RESCUE-001", "rescue", nodes[10]),
            ("SUPPLY-001", "supply_truck", nodes[22]),
        ]
        
        for res_id, res_type, node in resource_types:
            node_data = self.graph.nodes[node]
            self.resources[res_id] = ResourceStatus(
                resource_id=res_id,
                resource_type=res_type,
                status="available",
                location=Coordinates(
                    lat=node_data.get('y', 41.0),
                    lon=node_data.get('x', 29.0)
                )
            )
    
    def apply_scenario(self, scenario: DisasterScenario):
        """Senaryoyu uygula"""
        self.current_scenario = scenario
        self.agent = RoutingAgent(self.graph, scenario.edge_damages)
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """AI önerileri oluştur"""
        self.recommendations = []
        
        if not self.current_scenario:
            return
        
        # Yüksek riskli bölge uyarısı
        for zone in self.current_scenario.damage_zones:
            if zone.damage_score > 0.7:
                self.recommendations.append(AIRecommendation(
                    id=f"WARN-{zone.zone_id}",
                    type="warning",
                    priority="high",
                    message=f"{zone.zone_id} bölgesi kritik hasar altında",
                    details={
                        "zone": zone.zone_id,
                        "damage_level": zone.damage_level,
                        "coordinates": {
                            "lat": zone.center_lat,
                            "lon": zone.center_lon
                        }
                    }
                ))
        
        # Kaynak tahsis önerisi
        available_ambulances = [
            r for r in self.resources.values()
            if r.resource_type == "ambulance" and r.status == "available"
        ]
        
        if available_ambulances:
            self.recommendations.append(AIRecommendation(
                id="ALLOC-001",
                type="allocation",
                priority="medium",
                message=f"{len(available_ambulances)} ambulans müsait. Kritik bölgelere sevk önerilir.",
                details={
                    "resources": [r.resource_id for r in available_ambulances],
                    "suggested_zones": ["Z0_CRITICAL", "Z1_SEVERE"]
                }
            ))


# Global state
state = AppState()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Opti-Logistix API",
    description="Afet Lojistik Optimizasyon Sistemi API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
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
    """API kök endpoint"""
    return {
        "name": "Opti-Logistix API",
        "version": "0.1.0",
        "status": "running",
        "graph_nodes": state.graph.number_of_nodes() if state.graph else 0,
        "active_scenario": state.current_scenario.scenario_id if state.current_scenario else None
    }


@app.get("/api/v1/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "graph": state.graph is not None,
            "predictor": state.predictor is not None,
            "agent": state.agent is not None
        }
    }


# ----- ROTA YÖNETİMİ -----

@app.post("/api/v1/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """
    Optimal rota hesapla.
    
    Desteklenen yöntemler:
    - astar: A* algoritması (hızlı)
    - dijkstra: Dijkstra algoritması (garanti optimal)
    - rl: Pekiştirmeli öğrenme (eğitilmişse)
    - hybrid: A* + RL kombinasyonu
    """
    try:
        # En yakın düğümleri bul
        start_node = _find_nearest_node(request.start)
        end_node = _find_nearest_node(request.end)
        
        if start_node == end_node:
            return RouteResponse(
                success=False,
                message="Başlangıç ve hedef aynı nokta"
            )
        
        # Rota hesapla
        route = state.agent.find_route(
            start_node, end_node,
            method=request.method,
            urgency=request.urgency
        )
        
        if not route:
            return RouteResponse(
                success=False,
                message="Rota bulunamadı"
            )
        
        # Alternatifler
        alternatives = []
        all_routes = state.agent.find_all_routes(start_node, end_node, request.urgency)
        for alt in all_routes:
            if alt.method != route.method:
                alternatives.append(_route_to_dict(alt))
        
        return RouteResponse(
            success=True,
            route=_route_to_dict(route),
            alternatives=alternatives,
            message="Rota hesaplandı"
        )
        
    except Exception as e:
        logger.error(f"Rota hesaplama hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/routes/compare")
async def compare_routes(
    start_lat: float = Query(...),
    start_lon: float = Query(...),
    end_lat: float = Query(...),
    end_lon: float = Query(...)
):
    """Tüm yöntemlerle rotaları karşılaştır"""
    start = Coordinates(lat=start_lat, lon=start_lon)
    end = Coordinates(lat=end_lat, lon=end_lon)
    
    start_node = _find_nearest_node(start)
    end_node = _find_nearest_node(end)
    
    routes = state.agent.find_all_routes(start_node, end_node)
    
    return {
        "routes": [_route_to_dict(r) for r in routes],
        "optimal": next(
            (_route_to_dict(r) for r in routes if r.is_optimal),
            None
        )
    }


# ----- SENARYO YÖNETİMİ -----

@app.get("/api/v1/scenarios")
async def list_scenarios():
    """Mevcut senaryoları listele"""
    generator = ScenarioGenerator()
    scenarios = generator.generate_preset_scenarios(state.graph)
    
    return {
        "scenarios": [
            {
                "id": s.scenario_id,
                "type": s.disaster_type,
                "magnitude": s.magnitude,
                "affected_roads": s.affected_roads,
                "affected_bridges": s.affected_bridges
            }
            for s in scenarios
        ]
    }


@app.post("/api/v1/scenarios/activate")
async def activate_scenario(request: ScenarioRequest):
    """Yeni senaryo oluştur ve aktive et"""
    generator = ScenarioGenerator()
    
    epicenter = None
    if request.epicenter:
        epicenter = (request.epicenter.lat, request.epicenter.lon)
    
    scenario = generator.generate_earthquake_scenario(
        state.graph,
        magnitude=request.magnitude,
        epicenter=epicenter,
        scenario_id=request.scenario_id
    )
    
    state.apply_scenario(scenario)
    
    return {
        "success": True,
        "scenario": {
            "id": scenario.scenario_id,
            "magnitude": scenario.magnitude,
            "affected_roads": scenario.affected_roads,
            "affected_bridges": scenario.affected_bridges,
            "damage_zones": len(scenario.damage_zones)
        }
    }


@app.post("/api/v1/scenarios/preset/{scenario_name}")
async def activate_preset_scenario(scenario_name: str):
    """Önceden tanımlı senaryo aktive et (hafif, orta, siddetli)"""
    magnitude_map = {
        "hafif": 5.5,
        "orta": 6.5,
        "siddetli": 7.2
    }
    
    if scenario_name not in magnitude_map:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz senaryo: {scenario_name}. Geçerli: hafif, orta, siddetli"
        )
    
    generator = ScenarioGenerator()
    scenario = generator.generate_earthquake_scenario(
        state.graph,
        magnitude=magnitude_map[scenario_name],
        scenario_id=f"PRESET_{scenario_name.upper()}"
    )
    
    state.apply_scenario(scenario)
    
    return {
        "success": True,
        "scenario_name": scenario_name,
        "scenario_id": scenario.scenario_id,
        "magnitude": scenario.magnitude
    }


@app.delete("/api/v1/scenarios/current")
async def clear_scenario():
    """Aktif senaryoyu temizle"""
    state.current_scenario = None
    state.agent = RoutingAgent(state.graph, {})
    state.recommendations = []
    
    return {"success": True, "message": "Senaryo temizlendi"}


# ----- HASAR HARİTASI -----

@app.get("/api/v1/damage-map", response_model=DamageMapResponse)
async def get_damage_map():
    """Mevcut hasar haritasını döndür"""
    if not state.current_scenario:
        raise HTTPException(
            status_code=404,
            detail="Aktif senaryo yok. Önce senaryo aktive edin."
        )
    
    scenario = state.current_scenario
    
    # Kenar hasarları
    edges = []
    for edge_id, damage in scenario.edge_damages.items():
        parts = edge_id.split("_")
        u, v = int(parts[0]), int(parts[1])
        
        u_data = state.graph.nodes[u]
        v_data = state.graph.nodes[v]
        
        edges.append({
            "id": edge_id,
            "from": {"lat": u_data.get('y'), "lon": u_data.get('x')},
            "to": {"lat": v_data.get('y'), "lon": v_data.get('x')},
            "damage": damage,
            "level": _get_damage_level(damage)
        })
    
    # Hasar bölgeleri
    zones = [
        {
            "id": z.zone_id,
            "center": {"lat": z.center_lat, "lon": z.center_lon},
            "radius_m": z.radius_m,
            "level": z.damage_level,
            "score": z.damage_score
        }
        for z in scenario.damage_zones
    ]
    
    # İstatistikler
    damage_values = list(scenario.edge_damages.values())
    stats = {
        "total_edges": len(edges),
        "damaged_edges": sum(1 for d in damage_values if d > 0.3),
        "critical_edges": sum(1 for d in damage_values if d > 0.7),
        "avg_damage": sum(damage_values) / len(damage_values) if damage_values else 0,
        "max_damage": max(damage_values) if damage_values else 0
    }
    
    return DamageMapResponse(
        scenario_id=scenario.scenario_id,
        edges=edges,
        zones=zones,
        stats=stats
    )


# ----- KAYNAK YÖNETİMİ -----

@app.get("/api/v1/resources")
async def list_resources():
    """Tüm kaynakları listele"""
    return {
        "resources": [r.dict() for r in state.resources.values()],
        "summary": {
            "total": len(state.resources),
            "ambulances": sum(1 for r in state.resources.values() if r.resource_type == "ambulance"),
            "fire_trucks": sum(1 for r in state.resources.values() if r.resource_type == "fire_truck"),
            "rescue": sum(1 for r in state.resources.values() if r.resource_type == "rescue"),
            "supply": sum(1 for r in state.resources.values() if r.resource_type == "supply_truck")
        }
    }


@app.get("/api/v1/resources/{resource_type}")
async def get_resources_by_type(resource_type: str):
    """Türe göre kaynakları getir"""
    resources = [
        r.dict() for r in state.resources.values()
        if r.resource_type == resource_type
    ]
    return {"resource_type": resource_type, "resources": resources}


@app.post("/api/v1/resources/{resource_id}/assign")
async def assign_resource(resource_id: str, zone_id: str):
    """Kaynağı bölgeye ata"""
    if resource_id not in state.resources:
        raise HTTPException(status_code=404, detail="Kaynak bulunamadı")
    
    resource = state.resources[resource_id]
    resource.assigned_zone = zone_id
    resource.status = "assigned"
    
    return {"success": True, "resource": resource.dict()}


# ----- AI ÖNERİLERİ -----

@app.get("/api/v1/recommendations")
async def get_recommendations():
    """AI önerilerini getir"""
    return {
        "recommendations": [r.dict() for r in state.recommendations],
        "count": len(state.recommendations)
    }


# ----- GRAFİK VERİSİ -----

@app.get("/api/v1/graph/nodes")
async def get_graph_nodes():
    """Graf düğümlerini getir"""
    nodes = []
    for node_id in state.graph.nodes():
        data = state.graph.nodes[node_id]
        nodes.append({
            "id": node_id,
            "lat": data.get('y', 0),
            "lon": data.get('x', 0),
            "street_count": data.get('street_count', 0)
        })
    return {"nodes": nodes}


@app.get("/api/v1/graph/edges")
async def get_graph_edges():
    """Graf kenarlarını getir"""
    edges = []
    for u, v, key, data in state.graph.edges(keys=True, data=True):
        u_data = state.graph.nodes[u]
        v_data = state.graph.nodes[v]
        
        edge_id = f"{u}_{v}_{key}"
        damage = 0.0
        if state.current_scenario:
            damage = state.current_scenario.edge_damages.get(edge_id, 0)
        
        edges.append({
            "id": edge_id,
            "from": {"lat": u_data.get('y'), "lon": u_data.get('x')},
            "to": {"lat": v_data.get('y'), "lon": v_data.get('x')},
            "length_m": data.get('length_m', data.get('length', 100)),
            "road_score": data.get('road_score', 0.5),
            "is_bridge": data.get('is_bridge', False),
            "damage": damage
        })
    return {"edges": edges}


@app.get("/api/v1/graph/stats")
async def get_graph_stats():
    """Graf istatistiklerini getir"""
    return state.loader.get_graph_stats(state.graph)


# =============================================================================
# Helper Functions
# =============================================================================

def _find_nearest_node(coords: Coordinates) -> int:
    """Koordinatlara en yakın düğümü bul"""
    min_dist = float('inf')
    nearest = None
    
    for node_id in state.graph.nodes():
        data = state.graph.nodes[node_id]
        lat, lon = data.get('y', 0), data.get('x', 0)
        
        dist = ((lat - coords.lat) ** 2 + (lon - coords.lon) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            nearest = node_id
    
    return nearest


def _route_to_dict(route: Route) -> dict:
    """Route'u dict'e çevir"""
    return {
        "path": route.path,
        "path_coords": [{"lat": c[0], "lon": c[1]} for c in route.path_coords],
        "estimated_time": round(route.estimated_time, 1),
        "risk_score": round(route.risk_score, 3),
        "distance_km": round(route.distance_km, 2),
        "method": route.method,
        "is_optimal": route.is_optimal
    }


def _get_damage_level(score: float) -> str:
    """Hasar skorundan seviye"""
    if score < 0.2:
        return "none"
    elif score < 0.4:
        return "mild"
    elif score < 0.7:
        return "moderate"
    else:
        return "severe"


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
