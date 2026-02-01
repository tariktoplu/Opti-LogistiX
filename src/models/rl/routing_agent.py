"""
Rotalama Ajanı
RL tabanlı ve klasik algoritma tabanlı rota hesaplama
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import heapq

import numpy as np
import networkx as nx
from loguru import logger

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    logger.warning("Stable Baselines3 yüklü değil. RL ajanı çalışmayacak.")

from .routing_env import DisasterRoutingEnv, RouteResult


@dataclass
class Route:
    """Hesaplanmış rota"""
    path: List[int]
    path_coords: List[Tuple[float, float]]
    estimated_time: float  # dakika
    risk_score: float  # 0-1
    distance_km: float
    method: str  # 'rl', 'astar', 'dijkstra'
    is_optimal: bool


class RoutingAgent:
    """
    Afet durumunda rota hesaplama ajanı.
    
    Desteklenen yöntemler:
    1. A* (heuristik tabanlı, hızlı)
    2. Dijkstra (garanti optimal)
    3. RL (PPO, öğrenilmiş)
    4. Hybrid (A* + RL refinement)
    """
    
    def __init__(
        self,
        graph: nx.MultiDiGraph,
        damage_scores: Dict[str, float],
        vehicle_speed_kmh: float = 50.0,
        risk_weight: float = 2.0  # Risk vs süre trade-off
    ):
        self.graph = graph
        self.damage_scores = damage_scores
        self.vehicle_speed = vehicle_speed_kmh
        self.risk_weight = risk_weight
        
        # RL ajanı (lazy load)
        self._rl_model = None
        self._rl_env = None
    
    def find_route(
        self,
        start: int,
        goal: int,
        method: str = "astar",
        urgency: float = 0.5
    ) -> Optional[Route]:
        """
        Verilen başlangıç ve hedef arasında rota hesapla.
        
        Args:
            start: Başlangıç düğümü
            goal: Hedef düğümü
            method: Yöntem ('astar', 'dijkstra', 'rl', 'hybrid')
            urgency: Aciliyet seviyesi (sadece RL için)
            
        Returns:
            Route veya None (rota bulunamazsa)
        """
        if method == "astar":
            return self._find_route_astar(start, goal)
        elif method == "dijkstra":
            return self._find_route_dijkstra(start, goal)
        elif method == "rl":
            return self._find_route_rl(start, goal, urgency)
        elif method == "hybrid":
            return self._find_route_hybrid(start, goal, urgency)
        else:
            raise ValueError(f"Bilinmeyen yöntem: {method}")
    
    def find_all_routes(
        self,
        start: int,
        goal: int,
        urgency: float = 0.5
    ) -> List[Route]:
        """Tüm yöntemlerle rota hesapla ve karşılaştır."""
        routes = []
        
        # A* rotası
        astar_route = self._find_route_astar(start, goal)
        if astar_route:
            routes.append(astar_route)
        
        # Dijkstra rotası
        dijkstra_route = self._find_route_dijkstra(start, goal)
        if dijkstra_route:
            routes.append(dijkstra_route)
        
        # RL rotası (model varsa)
        if self._rl_model:
            rl_route = self._find_route_rl(start, goal, urgency)
            if rl_route:
                routes.append(rl_route)
        
        # En iyi rotayı işaretle
        if routes:
            best_idx = np.argmin([
                r.estimated_time + r.risk_score * 10 
                for r in routes
            ])
            routes[best_idx].is_optimal = True
        
        return routes
    
    def _find_route_astar(self, start: int, goal: int) -> Optional[Route]:
        """
        A* algoritması ile rota bul.
        Hasar skorları kenar ağırlığına eklenir.
        """
        try:
            # Ağırlık fonksiyonu: süre + risk
            def weight_func(u, v, data):
                length = data.get('length_m', data.get('length', 100))
                damage = self._get_edge_damage(u, v)
                
                # Süre (dakika)
                time = (length / 1000) / self.vehicle_speed * 60
                
                # Toplam maliyet
                return time * (1 + damage * self.risk_weight)
            
            # Heuristik: Düz çizgi mesafesi
            def heuristic(u, v):
                u_data = self.graph.nodes[u]
                v_data = self.graph.nodes[v]
                lat_diff = u_data.get('y', 0) - v_data.get('y', 0)
                lon_diff = u_data.get('x', 0) - v_data.get('x', 0)
                dist_km = np.sqrt(lat_diff**2 + lon_diff**2) * 111
                return dist_km / self.vehicle_speed * 60  # dakika
            
            # A* çalıştır
            path = nx.astar_path(
                self.graph, start, goal,
                heuristic=heuristic,
                weight=weight_func
            )
            
            return self._create_route(path, method="astar")
            
        except nx.NetworkXNoPath:
            logger.warning(f"Rota bulunamadı: {start} -> {goal}")
            return None
    
    def _find_route_dijkstra(self, start: int, goal: int) -> Optional[Route]:
        """Dijkstra algoritması ile rota bul."""
        try:
            def weight_func(u, v, data):
                length = data.get('length_m', data.get('length', 100))
                damage = self._get_edge_damage(u, v)
                time = (length / 1000) / self.vehicle_speed * 60
                return time * (1 + damage * self.risk_weight)
            
            path = nx.dijkstra_path(
                self.graph, start, goal,
                weight=weight_func
            )
            
            return self._create_route(path, method="dijkstra")
            
        except nx.NetworkXNoPath:
            return None
    
    def _find_route_rl(
        self, 
        start: int, 
        goal: int, 
        urgency: float
    ) -> Optional[Route]:
        """RL ajanı ile rota bul."""
        if not SB3_AVAILABLE or self._rl_model is None:
            logger.warning("RL modeli yüklü değil, A* kullanılıyor")
            return self._find_route_astar(start, goal)
        
        # Ortamı hazırla
        if self._rl_env is None:
            self._rl_env = DisasterRoutingEnv(
                self.graph, self.damage_scores
            )
        
        obs, _ = self._rl_env.reset(options={
            'start': start,
            'goal': goal,
            'urgency': urgency
        })
        
        # Ajanı çalıştır
        done = False
        while not done:
            action, _ = self._rl_model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = self._rl_env.step(action)
            done = terminated or truncated
        
        result = self._rl_env.get_route_result()
        
        if result.success:
            return self._create_route(result.path, method="rl")
        else:
            return None
    
    def _find_route_hybrid(
        self, 
        start: int, 
        goal: int, 
        urgency: float
    ) -> Optional[Route]:
        """
        Hibrit yaklaşım: A* ile başla, RL ile refine et.
        """
        # Önce A* ile güvenli rota bul
        astar_route = self._find_route_astar(start, goal)
        
        if not astar_route:
            return None
        
        # RL modeli varsa alternatif dene
        if self._rl_model:
            rl_route = self._find_route_rl(start, goal, urgency)
            
            if rl_route:
                # En iyi olanı seç
                astar_cost = astar_route.estimated_time + astar_route.risk_score * 10
                rl_cost = rl_route.estimated_time + rl_route.risk_score * 10
                
                if rl_cost < astar_cost:
                    rl_route.method = "hybrid"
                    return rl_route
        
        astar_route.method = "hybrid"
        return astar_route
    
    def _create_route(self, path: List[int], method: str) -> Route:
        """Path'ten Route objesi oluştur."""
        total_time = 0.0
        total_risk = 0.0
        total_distance = 0.0
        path_coords = []
        
        for i, node in enumerate(path):
            node_data = self.graph.nodes[node]
            path_coords.append((
                node_data.get('y', 0),
                node_data.get('x', 0)
            ))
            
            if i < len(path) - 1:
                next_node = path[i + 1]
                
                # Kenar verisi
                edge_data = list(self.graph[node][next_node].values())[0]
                length = edge_data.get('length_m', edge_data.get('length', 100))
                damage = self._get_edge_damage(node, next_node)
                
                # Metrikler
                total_distance += length / 1000
                total_time += (length / 1000) / self.vehicle_speed * 60 * (1 + damage)
                total_risk += damage
        
        # Ortalama risk
        avg_risk = total_risk / max(1, len(path) - 1)
        
        return Route(
            path=path,
            path_coords=path_coords,
            estimated_time=total_time,
            risk_score=avg_risk,
            distance_km=total_distance,
            method=method,
            is_optimal=False
        )
    
    def _get_edge_damage(self, u: int, v: int) -> float:
        """Kenar hasar skorunu al."""
        for key in self.graph[u].get(v, {}):
            edge_id = f"{u}_{v}_{key}"
            if edge_id in self.damage_scores:
                return self.damage_scores[edge_id]
        return 0.0
    
    # ===== RL Model Yönetimi =====
    
    def train_rl_agent(
        self,
        total_timesteps: int = 50000,
        learning_rate: float = 3e-4,
        callback: Optional[Any] = None
    ) -> None:
        """RL ajanını eğit."""
        if not SB3_AVAILABLE:
            raise ImportError("Stable Baselines3 yüklü değil")
        
        # Ortam oluştur
        self._rl_env = DisasterRoutingEnv(
            self.graph, self.damage_scores
        )
        
        # PPO modeli
        self._rl_model = PPO(
            "MlpPolicy",
            self._rl_env,
            learning_rate=learning_rate,
            n_steps=2048,
            batch_size=64,
            verbose=1
        )
        
        logger.info(f"RL eğitimi başlıyor ({total_timesteps} timestep)...")
        self._rl_model.learn(
            total_timesteps=total_timesteps,
            callback=callback
        )
        logger.info("RL eğitimi tamamlandı")
    
    def save_rl_model(self, path: Path) -> None:
        """RL modelini kaydet."""
        if self._rl_model:
            self._rl_model.save(path)
            logger.info(f"RL modeli kaydedildi: {path}")
    
    def load_rl_model(self, path: Path) -> None:
        """RL modelini yükle."""
        if SB3_AVAILABLE:
            self._rl_model = PPO.load(path)
            logger.info(f"RL modeli yüklendi: {path}")


# Test
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from data.graph_loader import GraphLoader
    from data.scenario_generator import ScenarioGenerator
    
    # Graf ve senaryo
    loader = GraphLoader()
    G = loader._create_demo_graph()
    
    generator = ScenarioGenerator()
    scenario = generator.generate_earthquake_scenario(G, 6.5)
    
    # Ajan
    agent = RoutingAgent(G, scenario.edge_damages)
    
    # Rota hesapla
    nodes = list(G.nodes())
    start, goal = nodes[0], nodes[-1]
    
    routes = agent.find_all_routes(start, goal)
    
    for route in routes:
        print(f"\n{route.method.upper()} Rota:")
        print(f"  Süre: {route.estimated_time:.1f} dk")
        print(f"  Risk: {route.risk_score:.2f}")
        print(f"  Mesafe: {route.distance_km:.2f} km")
        print(f"  Optimal: {route.is_optimal}")
