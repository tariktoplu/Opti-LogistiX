"""
Yol Ağı Graf Yükleyici - OSMnx Entegrasyonu
OpenStreetMap verilerini NetworkX grafına dönüştürür
Gerçek harita verileri ile çalışır
"""

import json
import random
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import networkx as nx
import numpy as np
from loguru import logger

try:
    import osmnx as ox
    OSMNX_AVAILABLE = True
    # OSMnx ayarları
    ox.settings.use_cache = True
    ox.settings.log_console = False
except ImportError:
    OSMNX_AVAILABLE = False
    logger.warning("OSMnx yüklü değil. pip install osmnx ile yükleyin.")


class GraphLoader:
    """
    OpenStreetMap'ten yol ağı verisi çeker ve graf yapısına dönüştürür.
    Arkadaşının Opti-Logistix koduyla entegre edilmiş versiyon.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/maps")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if OSMNX_AVAILABLE:
            ox.settings.cache_folder = str(self.cache_dir / "osmnx_cache")
    
    def load_from_place(
        self,
        place: str = "Kadikoy, Istanbul, Turkey",
        network_type: str = "drive"
    ) -> nx.MultiDiGraph:
        """
        Bölge adına göre yol ağı yükle (OSMnx kullanarak).
        
        Args:
            place: Bölge adı (örn: "Kadikoy, Istanbul, Turkey")
            network_type: Ağ tipi ('drive', 'walk', 'bike')
            
        Returns:
            NetworkX MultiDiGraph
        """
        if not OSMNX_AVAILABLE:
            logger.warning("OSMnx yüklü değil, demo graf oluşturuluyor...")
            return self._create_demo_graph()
        
        logger.info(f"Harita verileri indiriliyor: {place}")
        
        try:
            # OSMnx ile grafı indir
            G = ox.graph_from_place(place, network_type=network_type)
            
            # Graf bilgilerini logla
            nodes_count = G.number_of_nodes()
            edges_count = G.number_of_edges()
            logger.info(f"Başarılı! {nodes_count} kavşak ve {edges_count} yol segmenti yüklendi.")
            
            return G
            
        except Exception as e:
            logger.error(f"Harita yüklenemedi: {e}")
            return self._create_demo_graph()
    
    def add_disaster_data(
        self,
        G: nx.MultiDiGraph,
        damage_multiplier: float = 1.0,
        num_hospitals: int = 5,
        num_depots: int = 5
    ) -> Tuple[nx.MultiDiGraph, List[int], List[int]]:
        """
        Grafa afet verileri ekle: hasar olasılıkları, hastaneler, depolar.
        
        Args:
            G: OSMnx grafı
            damage_multiplier: Hasar çarpanı (1.0 = normal, 2.0 = şiddetli)
            num_hospitals: Hastane sayısı
            num_depots: Depo sayısı
            
        Returns:
            (Güncellenmiş graf, hastane düğümleri, depo düğümleri)
        """
        logger.info("Hastane, Depo ve Hasar verileri işleniyor...")
        
        nodes_list = list(G.nodes())
        
        # Hastane ve Depo noktaları belirle
        hospitals = random.sample(nodes_list, min(num_hospitals, len(nodes_list) // 10))
        remaining_nodes = [n for n in nodes_list if n not in hospitals]
        depots = random.sample(remaining_nodes, min(num_depots, len(remaining_nodes) // 10))
        
        # Düğümlere rol ata
        for node in G.nodes():
            if node in hospitals:
                G.nodes[node]['type'] = 'hospital'
                G.nodes[node]['name'] = f'Hastane-{hospitals.index(node)+1}'
            elif node in depots:
                G.nodes[node]['type'] = 'depot'
                G.nodes[node]['name'] = f'Depo-{depots.index(node)+1}'
            else:
                G.nodes[node]['type'] = 'junction'
        
        # Yollara hasar ve ağırlık ekle
        for u, v, k, data in G.edges(keys=True, data=True):
            # Sentetik hasar olasılığı (0-1 arası)
            base_damage = random.random() * damage_multiplier
            data['damage_prob'] = min(1.0, base_damage)
            
            # Temel uzunluk
            base_length = data.get('length', 100)
            
            # Hasar seviyesi ve ağırlık cezası
            if data['damage_prob'] > 0.8:
                data['damage_level'] = 'critical'
                weight_factor = 1000000  # Kırmızı yollardan kaçın
            elif data['damage_prob'] > 0.5:
                data['damage_level'] = 'moderate'
                weight_factor = 50
            else:
                data['damage_level'] = 'safe'
                weight_factor = 1
            
            data['weight'] = base_length * weight_factor
        
        logger.info(f"Veri işlendi: {len(hospitals)} hastane, {len(depots)} depo")
        return G, hospitals, depots
    
    def get_edges_as_geojson(self, G: nx.MultiDiGraph) -> List[Dict]:
        """
        Graf kenarlarını GeoJSON formatında döndür (dashboard için).
        """
        edges = []
        
        for u, v, k, data in G.edges(keys=True, data=True):
            # Başlangıç ve bitiş koordinatları
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            
            # Geometry varsa kullan, yoksa düz çizgi
            if 'geometry' in data:
                coords = list(data['geometry'].coords)
                path = [[lat, lon] for lon, lat in coords]
            else:
                path = [
                    [u_data.get('y', 0), u_data.get('x', 0)],
                    [v_data.get('y', 0), v_data.get('x', 0)]
                ]
            
            edges.append({
                'id': f"{u}_{v}_{k}",
                'from_node': u,
                'to_node': v,
                'path': path,
                'length': data.get('length', 100),
                'damage_prob': data.get('damage_prob', 0),
                'damage_level': data.get('damage_level', 'safe'),
                'weight': data.get('weight', 100),
                'highway': data.get('highway', 'road'),
                'name': data.get('name', '')
            })
        
        return edges
    
    def get_nodes_as_geojson(self, G: nx.MultiDiGraph) -> List[Dict]:
        """
        Graf düğümlerini GeoJSON formatında döndür.
        """
        nodes = []
        
        for node_id, data in G.nodes(data=True):
            nodes.append({
                'id': node_id,
                'lat': data.get('y', 0),
                'lon': data.get('x', 0),
                'type': data.get('type', 'junction'),
                'name': data.get('name', ''),
                'street_count': data.get('street_count', 0)
            })
        
        return nodes
    
    def find_route(
        self,
        G: nx.MultiDiGraph,
        start_node: int,
        end_node: int,
        weight: str = 'weight'
    ) -> Optional[Dict]:
        """
        İki düğüm arasında en kısa yolu bul.
        
        Args:
            G: Graf
            start_node: Başlangıç düğümü
            end_node: Hedef düğümü
            weight: Ağırlık alanı ('weight' veya 'length')
            
        Returns:
            Rota bilgileri veya None
        """
        try:
            path = nx.shortest_path(G, source=start_node, target=end_node, weight=weight)
            
            # Rota koordinatlarını çıkar
            path_coords = []
            total_length = 0
            total_damage = 0
            
            # İlk noktayı ekle
            start_node_data = G.nodes[path[0]]
            path_coords.append({
                'lat': start_node_data.get('y', 0),
                'lon': start_node_data.get('x', 0)
            })
            
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]
                
                # Kenar verisini al (en iyi kenarı seç)
                edge_data = min(G[u][v].values(), key=lambda x: x.get(weight, x.get('length', 0)))
                
                total_length += edge_data.get('length', 0)
                total_damage += edge_data.get('damage_prob', 0)
                
                if 'geometry' in edge_data:
                    # Geometri varsa ara noktaları kullan ((lon, lat) formatında gelir)
                    # İlk nokta u ile aynıdır, atlıyoruz
                    for lon, lat in list(edge_data['geometry'].coords)[1:]:
                        path_coords.append({'lat': lat, 'lon': lon})
                else:
                    # Geometri yoksa düz çizgi, hedef düğümü ekle
                    v_data = G.nodes[v]
                    path_coords.append({
                        'lat': v_data.get('y', 0),
                        'lon': v_data.get('x', 0)
                    })
            
            avg_damage = total_damage / max(1, len(path) - 1)
            
            return {
                'path': path,
                'path_coords': path_coords,
                'distance_m': total_length,
                'distance_km': total_length / 1000,
                'risk_score': avg_damage,
                'num_segments': len(path) - 1
            }
            
        except nx.NetworkXNoPath:
            logger.warning(f"Rota bulunamadı: {start_node} -> {end_node}")
            return None
    
    def find_nearest_node(
        self,
        G: nx.MultiDiGraph,
        lat: float,
        lon: float
    ) -> int:
        """Koordinatlara en yakın düğümü bul."""
        if OSMNX_AVAILABLE:
            return ox.nearest_nodes(G, lon, lat)
        
        # Manuel hesaplama
        min_dist = float('inf')
        nearest = None
        
        for node_id, data in G.nodes(data=True):
            node_lat = data.get('y', 0)
            node_lon = data.get('x', 0)
            dist = ((lat - node_lat) ** 2 + (lon - node_lon) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = node_id
        
        return nearest
    
    def get_graph_bounds(self, G: nx.MultiDiGraph) -> Dict:
        """Graf sınırlarını döndür (harita merkezi için)."""
        lats = [data.get('y', 0) for _, data in G.nodes(data=True)]
        lons = [data.get('x', 0) for _, data in G.nodes(data=True)]
        
        return {
            'north': max(lats),
            'south': min(lats),
            'east': max(lons),
            'west': min(lons),
            'center_lat': sum(lats) / len(lats),
            'center_lon': sum(lons) / len(lons)
        }
    
    def get_graph_stats(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """Graf istatistiklerini döndür."""
        total_length = sum(
            data.get('length', 0) 
            for _, _, data in G.edges(data=True)
        )
        
        damage_levels = {'critical': 0, 'moderate': 0, 'safe': 0}
        for _, _, data in G.edges(data=True):
            level = data.get('damage_level', 'safe')
            if level in damage_levels:
                damage_levels[level] += 1
        
        hospitals = sum(1 for _, data in G.nodes(data=True) if data.get('type') == 'hospital')
        depots = sum(1 for _, data in G.nodes(data=True) if data.get('type') == 'depot')
        
        return {
            'nodes': G.number_of_nodes(),
            'edges': G.number_of_edges(),
            'total_length_km': total_length / 1000,
            'hospitals': hospitals,
            'depots': depots,
            'damage_levels': damage_levels
        }
    
    def _create_demo_graph(self) -> nx.MultiDiGraph:
        """Demo amaçlı basit graf oluştur (OSMnx yoksa)."""
        G = nx.MultiDiGraph()
        
        # 5x5 grid - Kadıköy bölgesi koordinatları
        grid_size = 5
        base_lat, base_lon = 40.9907, 29.0230
        
        node_id = 0
        for i in range(grid_size):
            for j in range(grid_size):
                G.add_node(
                    node_id,
                    x=base_lon + j * 0.005,
                    y=base_lat + i * 0.004,
                    street_count=4,
                    type='junction'
                )
                node_id += 1
        
        # Kenarları ekle
        for i in range(grid_size):
            for j in range(grid_size):
                current = i * grid_size + j
                
                if j < grid_size - 1:
                    right = current + 1
                    length = random.uniform(200, 400)
                    G.add_edge(current, right, 0, 
                              length=length, highway='secondary',
                              damage_prob=0, damage_level='safe',
                              weight=length)
                    G.add_edge(right, current, 0,
                              length=length, highway='secondary',
                              damage_prob=0, damage_level='safe',
                              weight=length)
                
                if i < grid_size - 1:
                    down = current + grid_size
                    length = random.uniform(200, 400)
                    G.add_edge(current, down, 0,
                              length=length, highway='residential',
                              damage_prob=0, damage_level='safe',
                              weight=length)
                    G.add_edge(down, current, 0,
                              length=length, highway='residential',
                              damage_prob=0, damage_level='safe',
                              weight=length)
        
        logger.info(f"Demo graf oluşturuldu: {G.number_of_nodes()} düğüm, {G.number_of_edges()} kenar")
        return G


# Test
if __name__ == "__main__":
    loader = GraphLoader()
    
    if OSMNX_AVAILABLE:
        print("OSMnx ile gerçek harita yükleniyor...")
        G = loader.load_from_place("Kadikoy, Istanbul, Turkey")
        G, hospitals, depots = loader.add_disaster_data(G, damage_multiplier=0.5)
        
        stats = loader.get_graph_stats(G)
        print(f"\nGraf İstatistikleri: {stats}")
        
        bounds = loader.get_graph_bounds(G)
        print(f"Harita Merkezi: {bounds['center_lat']:.4f}, {bounds['center_lon']:.4f}")
        
        # Rota testi
        if hospitals and depots:
            route = loader.find_route(G, depots[0], hospitals[0])
            if route:
                print(f"\nRota: {route['distance_km']:.2f} km, Risk: {route['risk_score']:.2f}")
    else:
        print("OSMnx yüklü değil, demo graf kullanılıyor...")
        G = loader._create_demo_graph()
        print(f"Demo graf: {G.number_of_nodes()} düğüm")
