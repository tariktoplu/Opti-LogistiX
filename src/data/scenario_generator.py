"""
Sentetik Afet Senaryo Üreticisi
Deprem/sel senaryoları oluşturur ve yol hasarlarını simüle eder
"""

import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import networkx as nx
import numpy as np
from loguru import logger


@dataclass
class DamageZone:
    """Hasar bölgesi"""
    zone_id: str
    center_lat: float
    center_lon: float
    radius_m: float
    damage_level: str  # mild, moderate, severe, critical
    damage_score: float  # 0-1


@dataclass
class DisasterScenario:
    """Afet senaryosu"""
    scenario_id: str
    disaster_type: str  # earthquake, flood
    magnitude: float
    epicenter_lat: float
    epicenter_lon: float
    timestamp: str
    damage_zones: List[DamageZone]
    edge_damages: Dict[str, float]  # edge_id -> damage_score
    affected_roads: int
    affected_bridges: int
    
    def to_dict(self) -> dict:
        """Dict'e dönüştür"""
        data = asdict(self)
        data['damage_zones'] = [asdict(z) for z in self.damage_zones]
        return data
    
    def save(self, path: Path) -> None:
        """JSON olarak kaydet"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Senaryo kaydedildi: {path}")
    
    @classmethod
    def load(cls, path: Path) -> 'DisasterScenario':
        """JSON'dan yükle"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['damage_zones'] = [DamageZone(**z) for z in data['damage_zones']]
        return cls(**data)


class ScenarioGenerator:
    """
    Sentetik afet senaryoları üretir.
    
    Hasar olasılığı şu faktörlere bağlıdır:
    - Deprem şiddeti (magnitude)
    - Merkez noktasına uzaklık
    - Yol tipi (köprüler riskli)
    - Zemin tipi (simüle edilir)
    """
    
    # Şiddet -> Temel hasar oranı
    MAGNITUDE_DAMAGE_MAP = {
        5.0: 0.05,
        5.5: 0.10,
        6.0: 0.20,
        6.5: 0.35,
        7.0: 0.50,
        7.5: 0.70,
        8.0: 0.85
    }
    
    # Hasar seviyeleri
    DAMAGE_LEVELS = {
        (0.0, 0.2): "mild",
        (0.2, 0.4): "moderate", 
        (0.4, 0.7): "severe",
        (0.7, 1.0): "critical"
    }
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("data/scenarios")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_earthquake_scenario(
        self,
        graph: nx.MultiDiGraph,
        magnitude: float,
        epicenter: Optional[Tuple[float, float]] = None,
        scenario_id: Optional[str] = None
    ) -> DisasterScenario:
        """
        Deprem senaryosu üret.
        
        Args:
            graph: Yol ağı grafı
            magnitude: Deprem şiddeti (Richter)
            epicenter: Merkez noktası (lat, lon). None ise rastgele seçilir.
            scenario_id: Senaryo kimliği
            
        Returns:
            DisasterScenario
        """
        # Senaryo ID
        if scenario_id is None:
            scenario_id = f"EQ_{magnitude}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Merkez noktası
        if epicenter is None:
            epicenter = self._get_random_epicenter(graph)
        
        logger.info(f"Deprem senaryosu oluşturuluyor: M{magnitude} @ {epicenter}")
        
        # Temel hasar oranını hesapla
        base_damage_rate = self._get_base_damage_rate(magnitude)
        
        # Her kenar için hasar hesapla
        edge_damages = {}
        affected_roads = 0
        affected_bridges = 0
        
        for u, v, key, data in graph.edges(keys=True, data=True):
            # Kenar merkez noktasını al
            edge_center = self._get_edge_center(graph, u, v)
            
            # Merkeze uzaklık
            distance = self._haversine_distance(epicenter, edge_center)
            
            # Hasar olasılığı hesapla
            damage_prob = self._calculate_damage_probability(
                base_damage_rate, distance, data
            )
            
            # Hasar var mı?
            if random.random() < damage_prob:
                # Hasar seviyesi
                damage_score = min(1.0, damage_prob * random.uniform(0.8, 1.5))
                edge_id = f"{u}_{v}_{key}"
                edge_damages[edge_id] = damage_score
                affected_roads += 1
                
                if data.get('is_bridge', False):
                    affected_bridges += 1
        
        # Hasar bölgeleri oluştur
        damage_zones = self._create_damage_zones(graph, epicenter, edge_damages)
        
        scenario = DisasterScenario(
            scenario_id=scenario_id,
            disaster_type="earthquake",
            magnitude=magnitude,
            epicenter_lat=epicenter[0],
            epicenter_lon=epicenter[1],
            timestamp=datetime.now().isoformat(),
            damage_zones=damage_zones,
            edge_damages=edge_damages,
            affected_roads=affected_roads,
            affected_bridges=affected_bridges
        )
        
        logger.info(
            f"Senaryo oluşturuldu: {affected_roads} hasarlı yol, "
            f"{affected_bridges} hasarlı köprü"
        )
        
        return scenario
    
    def generate_preset_scenarios(
        self, 
        graph: nx.MultiDiGraph
    ) -> List[DisasterScenario]:
        """
        3 önceden tanımlı senaryo üret.
        """
        scenarios = []
        
        # Merkez noktası (graf ortası)
        center = self._get_graph_center(graph)
        
        # Senaryo 1: Hafif deprem
        s1 = self.generate_earthquake_scenario(
            graph, 
            magnitude=5.5,
            epicenter=center,
            scenario_id="S1_HAFIF_5.5"
        )
        scenarios.append(s1)
        
        # Senaryo 2: Orta şiddetli
        s2 = self.generate_earthquake_scenario(
            graph,
            magnitude=6.5,
            epicenter=(center[0] + 0.005, center[1] - 0.003),
            scenario_id="S2_ORTA_6.5"
        )
        scenarios.append(s2)
        
        # Senaryo 3: Şiddetli
        s3 = self.generate_earthquake_scenario(
            graph,
            magnitude=7.2,
            epicenter=(center[0] - 0.002, center[1] + 0.005),
            scenario_id="S3_SIDDETLI_7.2"
        )
        scenarios.append(s3)
        
        return scenarios
    
    def _get_base_damage_rate(self, magnitude: float) -> float:
        """Şiddete göre temel hasar oranı"""
        for mag, rate in sorted(self.MAGNITUDE_DAMAGE_MAP.items()):
            if magnitude <= mag:
                return rate
        return 0.9
    
    def _calculate_damage_probability(
        self,
        base_rate: float,
        distance_km: float,
        edge_data: dict
    ) -> float:
        """
        Kenar hasar olasılığını hesapla.
        
        Faktörler:
        - Temel oran (şiddet)
        - Uzaklık azalması (1/d²)
        - Köprü çarpanı (x2)
        - Yol skoru (ana yollar daha dayanıklı)
        """
        # Uzaklık etkisi (0-5km en yoğun)
        distance_factor = 1.0 / (1.0 + (distance_km / 2.0) ** 2)
        
        # Köprü çarpanı
        bridge_factor = 2.0 if edge_data.get('is_bridge', False) else 1.0
        
        # Yol dayanıklılığı (ana yollar daha iyi)
        road_score = edge_data.get('road_score', 0.5)
        durability_factor = 1.0 - (road_score * 0.3)
        
        # Toplam olasılık
        prob = base_rate * distance_factor * bridge_factor * durability_factor
        
        # 0-1 arasında sınırla
        return min(1.0, max(0.0, prob))
    
    def _get_edge_center(
        self, 
        graph: nx.MultiDiGraph, 
        u: int, 
        v: int
    ) -> Tuple[float, float]:
        """Kenarın merkez noktasını hesapla"""
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        
        lat = (u_data.get('y', 0) + v_data.get('y', 0)) / 2
        lon = (u_data.get('x', 0) + v_data.get('x', 0)) / 2
        
        return (lat, lon)
    
    def _get_random_epicenter(
        self, 
        graph: nx.MultiDiGraph
    ) -> Tuple[float, float]:
        """Rastgele merkez noktası seç"""
        nodes = list(graph.nodes(data=True))
        node = random.choice(nodes)
        return (node[1].get('y', 41.0), node[1].get('x', 29.0))
    
    def _get_graph_center(
        self, 
        graph: nx.MultiDiGraph
    ) -> Tuple[float, float]:
        """Graf merkez noktasını hesapla"""
        lats = [data.get('y', 0) for _, data in graph.nodes(data=True)]
        lons = [data.get('x', 0) for _, data in graph.nodes(data=True)]
        return (np.mean(lats), np.mean(lons))
    
    def _haversine_distance(
        self, 
        p1: Tuple[float, float], 
        p2: Tuple[float, float]
    ) -> float:
        """İki nokta arası mesafe (km)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Dünya yarıçapı (km)
        
        lat1, lon1 = radians(p1[0]), radians(p1[1])
        lat2, lon2 = radians(p2[0]), radians(p2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _create_damage_zones(
        self,
        graph: nx.MultiDiGraph,
        epicenter: Tuple[float, float],
        edge_damages: Dict[str, float]
    ) -> List[DamageZone]:
        """Hasar bölgeleri oluştur"""
        zones = []
        
        # Merkez bölge (kritik)
        zones.append(DamageZone(
            zone_id="Z0_CRITICAL",
            center_lat=epicenter[0],
            center_lon=epicenter[1],
            radius_m=500,
            damage_level="critical",
            damage_score=0.9
        ))
        
        # Orta bölge (şiddetli)
        zones.append(DamageZone(
            zone_id="Z1_SEVERE",
            center_lat=epicenter[0],
            center_lon=epicenter[1],
            radius_m=1500,
            damage_level="severe",
            damage_score=0.6
        ))
        
        # Dış bölge (orta)
        zones.append(DamageZone(
            zone_id="Z2_MODERATE",
            center_lat=epicenter[0],
            center_lon=epicenter[1],
            radius_m=3000,
            damage_level="moderate",
            damage_score=0.3
        ))
        
        return zones
    
    def get_damage_level(self, score: float) -> str:
        """Hasar skorundan seviye döndür"""
        for (low, high), level in self.DAMAGE_LEVELS.items():
            if low <= score < high:
                return level
        return "critical"


# Test
if __name__ == "__main__":
    from graph_loader import GraphLoader
    
    loader = GraphLoader()
    G = loader._create_demo_graph()
    
    generator = ScenarioGenerator()
    scenarios = generator.generate_preset_scenarios(G)
    
    for s in scenarios:
        print(f"\n{s.scenario_id}:")
        print(f"  Şiddet: {s.magnitude}")
        print(f"  Hasarlı yol: {s.affected_roads}")
        print(f"  Hasarlı köprü: {s.affected_bridges}")
