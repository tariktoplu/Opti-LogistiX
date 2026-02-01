"""
Afet Rotalama RL Ortamı
Gymnasium tabanlı pekiştirmeli öğrenme ortamı
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import random

import numpy as np
import networkx as nx
from loguru import logger

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_AVAILABLE = True
except ImportError:
    GYM_AVAILABLE = False
    logger.warning("Gymnasium yüklü değil. RL ortamı çalışmayacak.")


@dataclass
class RouteResult:
    """Rota sonucu"""
    path: List[int]
    total_time: float
    total_risk: float
    success: bool
    steps: int


if GYM_AVAILABLE:
    class DisasterRoutingEnv(gym.Env):
        """
        Afet durumunda ambulans/yardım aracı rotalama ortamı.
        
        Durum (State):
        - Mevcut düğüm özellikleri
        - Hedef düğüm özellikleri  
        - Komşu düğümlerin hasar skorları
        - Kalan mesafe tahmini
        
        Aksiyon (Action):
        - Komşu düğümlerden birine git (discrete)
        
        Ödül (Reward):
        - Negatif süre (zaman cezası)
        - Risk cezası (hasarlı yoldan geçme)
        - Hedefe ulaşma bonusu (aciliyet çarpanı)
        """
        
        metadata = {"render_modes": ["human"]}
        
        def __init__(
            self,
            graph: nx.MultiDiGraph,
            damage_scores: Dict[str, float],
            max_neighbors: int = 8,
            time_weight: float = 1.0,
            risk_weight: float = 10.0,
            urgency_weight: float = 50.0,
            max_steps: int = 100,
            vehicle_speed_kmh: float = 50.0
        ):
            super().__init__()
            
            self.graph = graph
            self.damage_scores = damage_scores
            self.max_neighbors = max_neighbors
            self.time_weight = time_weight
            self.risk_weight = risk_weight
            self.urgency_weight = urgency_weight
            self.max_steps = max_steps
            self.vehicle_speed = vehicle_speed_kmh
            
            # Düğüm listesi
            self.nodes = list(graph.nodes())
            self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
            
            # Observation space: [mevcut_konum_feat(4), hedef_feat(4), 
            #                     komşu_hasarları(max_neighbors), mesafe(1)]
            obs_dim = 4 + 4 + max_neighbors + 1
            self.observation_space = spaces.Box(
                low=-np.inf, high=np.inf, 
                shape=(obs_dim,), 
                dtype=np.float32
            )
            
            # Action space: Komşu indeksi seç
            self.action_space = spaces.Discrete(max_neighbors)
            
            # Episode değişkenleri
            self.current_node = None
            self.goal_node = None
            self.urgency = 0.5
            self.steps = 0
            self.path = []
            self.total_time = 0.0
            self.total_risk = 0.0
        
        def reset(
            self,
            seed: Optional[int] = None,
            options: Optional[Dict] = None
        ) -> Tuple[np.ndarray, Dict]:
            """
            Yeni episode başlat.
            
            Options:
            - start: Başlangıç düğümü
            - goal: Hedef düğümü
            - urgency: Aciliyet seviyesi (0-1)
            """
            super().reset(seed=seed)
            
            options = options or {}
            
            # Başlangıç ve hedef
            if 'start' in options:
                self.current_node = options['start']
            else:
                self.current_node = random.choice(self.nodes)
            
            if 'goal' in options:
                self.goal_node = options['goal']
            else:
                # Başlangıçtan uzak bir hedef seç
                self.goal_node = self._select_distant_goal(self.current_node)
            
            self.urgency = options.get('urgency', random.uniform(0.3, 1.0))
            
            # Reset counters
            self.steps = 0
            self.path = [self.current_node]
            self.total_time = 0.0
            self.total_risk = 0.0
            
            return self._get_observation(), {}
        
        def step(
            self, 
            action: int
        ) -> Tuple[np.ndarray, float, bool, bool, Dict]:
            """
            Bir adım at.
            
            Returns:
                observation, reward, terminated, truncated, info
            """
            self.steps += 1
            
            # Komşuları al
            neighbors = self._get_neighbors(self.current_node)
            
            # Geçersiz aksiyon kontrolü
            if action >= len(neighbors):
                # Ceza ver, yerinde kal
                return (
                    self._get_observation(),
                    -5.0,  # Invalid action penalty
                    False,
                    self.steps >= self.max_steps,
                    {"action": "invalid"}
                )
            
            # Seçilen komşuya git
            next_node = neighbors[action]
            
            # Kenar hasarını al
            edge_damage = self._get_edge_damage(self.current_node, next_node)
            
            # Seyahat süresini hesapla
            travel_time = self._calculate_travel_time(
                self.current_node, next_node, edge_damage
            )
            
            # Ödül hesapla
            reward = self._calculate_reward(
                travel_time, edge_damage, next_node == self.goal_node
            )
            
            # Güncelle
            self.current_node = next_node
            self.path.append(next_node)
            self.total_time += travel_time
            self.total_risk += edge_damage
            
            # Hedefe ulaştı mı?
            terminated = (next_node == self.goal_node)
            truncated = (self.steps >= self.max_steps)
            
            info = {
                "travel_time": travel_time,
                "edge_damage": edge_damage,
                "path_length": len(self.path),
                "total_time": self.total_time,
                "total_risk": self.total_risk
            }
            
            return self._get_observation(), reward, terminated, truncated, info
        
        def _get_observation(self) -> np.ndarray:
            """Mevcut durumu gözlem vektörüne çevir."""
            obs = []
            
            # Mevcut konum özellikleri
            current_data = self.graph.nodes[self.current_node]
            obs.extend([
                current_data.get('y', 0) / 90,  # Lat normalized
                current_data.get('x', 0) / 180,  # Lon normalized
                current_data.get('street_count', 2) / 10,
                1.0  # Bias
            ])
            
            # Hedef özellikleri
            goal_data = self.graph.nodes[self.goal_node]
            obs.extend([
                goal_data.get('y', 0) / 90,
                goal_data.get('x', 0) / 180,
                goal_data.get('street_count', 2) / 10,
                self.urgency
            ])
            
            # Komşu hasarları
            neighbors = self._get_neighbors(self.current_node)
            neighbor_damages = []
            for n in neighbors[:self.max_neighbors]:
                damage = self._get_edge_damage(self.current_node, n)
                neighbor_damages.append(damage)
            
            # Padding
            while len(neighbor_damages) < self.max_neighbors:
                neighbor_damages.append(1.0)  # Yüksek hasar = geçilmez
            
            obs.extend(neighbor_damages)
            
            # Hedefe tahmini mesafe
            dist = self._estimate_distance(self.current_node, self.goal_node)
            obs.append(dist / 10)  # km, normalized
            
            return np.array(obs, dtype=np.float32)
        
        def _get_neighbors(self, node: int) -> List[int]:
            """Düğümün komşularını döndür."""
            return list(self.graph.successors(node))
        
        def _get_edge_damage(self, u: int, v: int) -> float:
            """Kenar hasar skorunu al."""
            # Tüm keyler için kontrol et
            for key in self.graph[u][v]:
                edge_id = f"{u}_{v}_{key}"
                if edge_id in self.damage_scores:
                    return self.damage_scores[edge_id]
            return 0.0
        
        def _calculate_travel_time(
            self, 
            u: int, 
            v: int, 
            damage: float
        ) -> float:
            """
            Seyahat süresini hesapla (dakika).
            Hasar yavaşlama faktörü olarak uygulanır.
            """
            # Temel süre
            edge_data = list(self.graph[u][v].values())[0]
            length_m = edge_data.get('length_m', edge_data.get('length', 100))
            base_time = (length_m / 1000) / self.vehicle_speed * 60  # dakika
            
            # Hasar etkisi (hasarlı yol = yavaş)
            damage_factor = 1.0 + damage * 3.0  # En fazla 4x yavaşlama
            
            return base_time * damage_factor
        
        def _calculate_reward(
            self,
            travel_time: float,
            edge_damage: float,
            reached_goal: bool
        ) -> float:
            """
            Ödül hesapla.
            
            R = -time_weight * t - risk_weight * damage + goal_bonus
            """
            reward = 0.0
            
            # Zaman cezası
            reward -= self.time_weight * travel_time
            
            # Risk cezası
            reward -= self.risk_weight * edge_damage
            
            # Hedefe ulaşma bonusu
            if reached_goal:
                reward += self.urgency_weight * self.urgency
            
            return reward
        
        def _estimate_distance(self, u: int, v: int) -> float:
            """İki düğüm arası tahmini mesafe (km)."""
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            
            lat_diff = u_data.get('y', 0) - v_data.get('y', 0)
            lon_diff = u_data.get('x', 0) - v_data.get('x', 0)
            
            return np.sqrt(lat_diff**2 + lon_diff**2) * 111  # ~km
        
        def _select_distant_goal(self, start: int) -> int:
            """Başlangıçtan uzak bir hedef seç."""
            max_dist = 0
            best_goal = start
            
            for node in self.nodes:
                if node != start:
                    dist = self._estimate_distance(start, node)
                    if dist > max_dist:
                        max_dist = dist
                        best_goal = node
            
            return best_goal
        
        def get_route_result(self) -> RouteResult:
            """Episode sonucu döndür."""
            return RouteResult(
                path=self.path.copy(),
                total_time=self.total_time,
                total_risk=self.total_risk,
                success=(self.current_node == self.goal_node),
                steps=self.steps
            )


else:
    # Gymnasium yoksa placeholder
    class DisasterRoutingEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("Gymnasium yüklü değil")


# Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from data.graph_loader import GraphLoader
    from data.scenario_generator import ScenarioGenerator
    
    # Graf ve senaryo oluştur
    loader = GraphLoader()
    G = loader._create_demo_graph()
    
    generator = ScenarioGenerator()
    scenario = generator.generate_earthquake_scenario(G, 6.5)
    
    # Ortam oluştur
    if GYM_AVAILABLE:
        env = DisasterRoutingEnv(G, scenario.edge_damages)
        
        # Test episode
        obs, _ = env.reset()
        print(f"Observation shape: {obs.shape}")
        print(f"Start: {env.current_node}, Goal: {env.goal_node}")
        
        for step in range(20):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            print(f"Step {step+1}: reward={reward:.2f}, info={info}")
            
            if terminated or truncated:
                break
        
        result = env.get_route_result()
        print(f"\nResult: {result}")
