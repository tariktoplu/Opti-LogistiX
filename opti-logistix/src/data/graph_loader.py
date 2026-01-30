"""
Yol Ağı Graf Yükleyici
OpenStreetMap verilerini NetworkX grafına dönüştürür
"""

import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import networkx as nx
import numpy as np
from loguru import logger

try:
    import osmnx as ox
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False
    logger.warning("OSMnx yüklü değil. Harita verisi çekilemeyecek.")


class GraphLoader:
    """
    OpenStreetMap'ten yol ağı verisi çeker ve graf yapısına dönüştürür.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Args:
            cache_dir: Graf verilerinin cache'leneceği dizin
        """
        self.cache_dir = cache_dir or Path("data/maps")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if OSMNX_AVAILABLE:
            # OSMnx ayarları
            ox.settings.use_cache = True
            ox.settings.cache_folder = str(self.cache_dir / "osmnx_cache")
    
    def load_graph(
        self,
        place: str,
        network_type: str = "drive",
        simplify: bool = True,
        use_cache: bool = True
    ) -> nx.MultiDiGraph:
        """
        Belirtilen bölge için yol ağı grafını yükler.
        
        Args:
            place: Bölge ismi (örn: "Kadıköy, Istanbul, Turkey")
            network_type: Ağ tipi ('drive', 'walk', 'bike', 'all')
            simplify: Grafı sadeleştir (ara düğümleri kaldır)
            use_cache: Önbellek kullan
            
        Returns:
            NetworkX MultiDiGraph
        """
        cache_file = self._get_cache_path(place, network_type)
        
        # Önbellekte var mı?
        if use_cache and cache_file.exists():
            logger.info(f"Graf önbellekten yükleniyor: {cache_file}")
            return self._load_from_cache(cache_file)
        
        if not OSMNX_AVAILABLE:
            logger.warning("OSMnx yüklü değil, demo graf oluşturuluyor...")
            return self._create_demo_graph()
        
        # OSM'den çek
        logger.info(f"Graf OSM'den çekiliyor: {place}")
        G = ox.graph_from_place(
            place,
            network_type=network_type,
            simplify=simplify
        )
        
        # Kenar özelliklerini zenginleştir
        G = self._enrich_edge_features(G)
        
        # Önbelleğe kaydet
        if use_cache:
            self._save_to_cache(G, cache_file)
        
        logger.info(f"Graf yüklendi: {G.number_of_nodes()} düğüm, {G.number_of_edges()} kenar")
        return G
    
    def load_by_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        network_type: str = "drive"
    ) -> nx.MultiDiGraph:
        """
        Bounding box ile yol ağı yükle.
        """
        if not OSMNX_AVAILABLE:
            return self._create_demo_graph()
        
        G = ox.graph_from_bbox(
            north=north,
            south=south,
            east=east,
            west=west,
            network_type=network_type
        )
        return self._enrich_edge_features(G)
    
    def _enrich_edge_features(self, G: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """
        Kenar özelliklerini zenginleştir (hasar tahmini için).
        """
        for u, v, key, data in G.edges(keys=True, data=True):
            # Yol uzunluğu (metre)
            length = data.get('length', 100)
            
            # Yol tipi skoru
            highway = data.get('highway', 'residential')
            if isinstance(highway, list):
                highway = highway[0]
            
            road_type_scores = {
                'motorway': 1.0,
                'trunk': 0.9,
                'primary': 0.8,
                'secondary': 0.7,
                'tertiary': 0.6,
                'residential': 0.4,
                'unclassified': 0.3
            }
            road_score = road_type_scores.get(highway, 0.5)
            
            # Köprü mü?
            is_bridge = data.get('bridge', 'no') == 'yes'
            
            # Şerit sayısı
            lanes = data.get('lanes', 1)
            if isinstance(lanes, list):
                lanes = int(lanes[0])
            elif isinstance(lanes, str):
                try:
                    lanes = int(lanes)
                except ValueError:
                    lanes = 1
            
            # Özellikleri ekle
            G[u][v][key]['length_m'] = length
            G[u][v][key]['road_score'] = road_score
            G[u][v][key]['is_bridge'] = is_bridge
            G[u][v][key]['lanes'] = lanes
            G[u][v][key]['base_travel_time'] = length / 1000 / 50 * 60  # dakika
            
        return G
    
    def _create_demo_graph(self) -> nx.MultiDiGraph:
        """
        Demo amaçlı basit bir graf oluştur.
        """
        G = nx.MultiDiGraph()
        
        # 5x5 grid oluştur
        grid_size = 5
        node_id = 0
        
        for i in range(grid_size):
            for j in range(grid_size):
                G.add_node(
                    node_id,
                    x=29.0 + i * 0.01,  # Longitude
                    y=41.0 + j * 0.01,  # Latitude
                    street_count=4
                )
                node_id += 1
        
        # Kenarları ekle (grid bağlantıları)
        for i in range(grid_size):
            for j in range(grid_size):
                current = i * grid_size + j
                
                # Sağa bağla
                if j < grid_size - 1:
                    right = current + 1
                    length = np.random.uniform(200, 500)
                    G.add_edge(current, right, 0, 
                              length=length, highway='secondary',
                              length_m=length, road_score=0.7,
                              is_bridge=False, lanes=2,
                              base_travel_time=length/1000/50*60)
                    G.add_edge(right, current, 0,
                              length=length, highway='secondary',
                              length_m=length, road_score=0.7,
                              is_bridge=False, lanes=2,
                              base_travel_time=length/1000/50*60)
                
                # Aşağı bağla
                if i < grid_size - 1:
                    down = current + grid_size
                    length = np.random.uniform(200, 500)
                    G.add_edge(current, down, 0,
                              length=length, highway='residential',
                              length_m=length, road_score=0.4,
                              is_bridge=(i == 2 and j == 2),  # Ortada köprü
                              lanes=1,
                              base_travel_time=length/1000/50*60)
                    G.add_edge(down, current, 0,
                              length=length, highway='residential',
                              length_m=length, road_score=0.4,
                              is_bridge=(i == 2 and j == 2),
                              lanes=1,
                              base_travel_time=length/1000/50*60)
        
        logger.info(f"Demo graf oluşturuldu: {G.number_of_nodes()} düğüm, {G.number_of_edges()} kenar")
        return G
    
    def _get_cache_path(self, place: str, network_type: str) -> Path:
        """Önbellek dosya yolunu oluştur."""
        safe_name = place.replace(" ", "_").replace(",", "").lower()
        return self.cache_dir / f"{safe_name}_{network_type}.graphml"
    
    def _save_to_cache(self, G: nx.MultiDiGraph, path: Path) -> None:
        """Grafı dosyaya kaydet."""
        if OSMNX_AVAILABLE:
            ox.save_graphml(G, path)
            logger.info(f"Graf kaydedildi: {path}")
    
    def _load_from_cache(self, path: Path) -> nx.MultiDiGraph:
        """Grafı dosyadan yükle."""
        if OSMNX_AVAILABLE:
            return ox.load_graphml(path)
        return self._create_demo_graph()
    
    def get_graph_stats(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """Graf istatistiklerini döndür."""
        total_length = sum(
            data.get('length_m', 0) 
            for _, _, data in G.edges(data=True)
        )
        
        bridge_count = sum(
            1 for _, _, data in G.edges(data=True)
            if data.get('is_bridge', False)
        )
        
        return {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "total_length_km": total_length / 1000,
            "bridges": bridge_count,
            "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes()
        }


# Test
if __name__ == "__main__":
    loader = GraphLoader()
    
    # Demo graf test
    G = loader._create_demo_graph()
    stats = loader.get_graph_stats(G)
    print(f"Graf İstatistikleri: {stats}")
