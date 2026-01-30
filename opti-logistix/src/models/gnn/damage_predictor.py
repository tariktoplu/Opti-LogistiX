"""
GNN Hasar Tahmin Modeli
Graf Sinir Ağları ile yol hasar olasılığı tahmini
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import numpy as np
import networkx as nx
from loguru import logger

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import SAGEConv, GCNConv
    from torch_geometric.data import Data
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch/PyTorch Geometric yüklü değil. Basit model kullanılacak.")


class SimpleDamagePredictor:
    """
    PyTorch olmadan basit hasar tahmini.
    Rule-based yaklaşım kullanır.
    """
    
    def __init__(self):
        self.weights = {
            'distance': 0.4,
            'bridge': 0.3,
            'road_type': 0.2,
            'lanes': 0.1
        }
    
    def predict(
        self,
        graph: nx.MultiDiGraph,
        epicenter: Tuple[float, float],
        magnitude: float
    ) -> Dict[str, float]:
        """
        Her kenar için hasar olasılığı tahmin et.
        """
        damages = {}
        base_rate = min(1.0, magnitude / 10)
        
        for u, v, key, data in graph.edges(keys=True, data=True):
            # Kenar merkezi
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            lat = (u_data.get('y', 0) + v_data.get('y', 0)) / 2
            lon = (u_data.get('x', 0) + v_data.get('x', 0)) / 2
            
            # Uzaklık faktörü
            dist = np.sqrt(
                (lat - epicenter[0])**2 + (lon - epicenter[1])**2
            ) * 111  # ~km
            distance_factor = 1.0 / (1.0 + dist)
            
            # Köprü faktörü
            bridge_factor = 1.5 if data.get('is_bridge', False) else 1.0
            
            # Yol tipi faktörü
            road_score = data.get('road_score', 0.5)
            road_factor = 1.0 - road_score * 0.3
            
            # Toplam
            damage = base_rate * distance_factor * bridge_factor * road_factor
            damages[f"{u}_{v}_{key}"] = min(1.0, damage)
        
        return damages


if TORCH_AVAILABLE:
    class GNNDamagePredictor(nn.Module):
        """
        GraphSAGE tabanlı hasar tahmin modeli.
        
        Özellikler:
        - 2 katmanlı GraphSAGE
        - Kenar seviyesi tahmin (link prediction variant)
        - Dropout ile regularization
        """
        
        def __init__(
            self,
            in_channels: int = 8,
            hidden_channels: int = 64,
            out_channels: int = 1,
            num_layers: int = 2,
            dropout: float = 0.3
        ):
            super().__init__()
            
            self.num_layers = num_layers
            self.dropout = dropout
            
            # GraphSAGE katmanları
            self.convs = nn.ModuleList()
            self.convs.append(SAGEConv(in_channels, hidden_channels))
            
            for _ in range(num_layers - 1):
                self.convs.append(SAGEConv(hidden_channels, hidden_channels))
            
            # Kenar tahmini için MLP
            self.edge_mlp = nn.Sequential(
                nn.Linear(hidden_channels * 2, hidden_channels),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_channels, out_channels),
                nn.Sigmoid()
            )
        
        def forward(
            self, 
            x: torch.Tensor, 
            edge_index: torch.Tensor
        ) -> torch.Tensor:
            """
            Düğüm embedding'lerini hesapla.
            """
            for i, conv in enumerate(self.convs):
                x = conv(x, edge_index)
                if i < self.num_layers - 1:
                    x = F.relu(x)
                    x = F.dropout(x, p=self.dropout, training=self.training)
            return x
        
        def predict_edge_damage(
            self,
            x: torch.Tensor,
            edge_index: torch.Tensor
        ) -> torch.Tensor:
            """
            Her kenar için hasar olasılığı tahmin et.
            """
            # Düğüm embedding'leri
            node_emb = self(x, edge_index)
            
            # Kenar embedding'leri (kaynak + hedef concat)
            src = node_emb[edge_index[0]]
            dst = node_emb[edge_index[1]]
            edge_emb = torch.cat([src, dst], dim=1)
            
            # Hasar tahmini
            return self.edge_mlp(edge_emb).squeeze()


class DamagePredictor:
    """
    Yüksek seviye hasar tahmin arayüzü.
    PyTorch varsa GNN, yoksa basit model kullanır.
    """
    
    def __init__(
        self,
        hidden_channels: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
        model_path: Optional[Path] = None
    ):
        self.use_gnn = TORCH_AVAILABLE
        
        if self.use_gnn:
            self.model = GNNDamagePredictor(
                hidden_channels=hidden_channels,
                num_layers=num_layers,
                dropout=dropout
            )
            
            if model_path and model_path.exists():
                self.load_model(model_path)
            
            logger.info("GNN hasar tahmin modeli yüklendi")
        else:
            self.model = SimpleDamagePredictor()
            logger.info("Basit hasar tahmin modeli yüklendi")
    
    def predict(
        self,
        graph: nx.MultiDiGraph,
        epicenter: Tuple[float, float],
        magnitude: float
    ) -> Dict[str, float]:
        """
        Graf üzerinde hasar tahmini yap.
        
        Args:
            graph: Yol ağı grafı
            epicenter: Deprem merkezi (lat, lon)
            magnitude: Deprem şiddeti
            
        Returns:
            Dict[edge_id, damage_score]
        """
        if not self.use_gnn:
            return self.model.predict(graph, epicenter, magnitude)
        
        # Graf verisini PyTorch Geometric formatına çevir
        data = self._graph_to_pyg(graph, epicenter, magnitude)
        
        # Tahmin
        self.model.eval()
        with torch.no_grad():
            damage_scores = self.model.predict_edge_damage(
                data.x, data.edge_index
            )
        
        # Dict formatına çevir
        damages = {}
        edge_list = list(graph.edges(keys=True))
        for i, (u, v, key) in enumerate(edge_list):
            damages[f"{u}_{v}_{key}"] = float(damage_scores[i])
        
        return damages
    
    def _graph_to_pyg(
        self,
        graph: nx.MultiDiGraph,
        epicenter: Tuple[float, float],
        magnitude: float
    ) -> 'Data':
        """
        NetworkX grafını PyTorch Geometric Data'ya çevir.
        """
        # Düğüm özellikleri
        node_features = []
        node_list = list(graph.nodes())
        node_to_idx = {n: i for i, n in enumerate(node_list)}
        
        for node in node_list:
            data = graph.nodes[node]
            lat = data.get('y', 0)
            lon = data.get('x', 0)
            
            # Merkeze uzaklık
            dist = np.sqrt(
                (lat - epicenter[0])**2 + (lon - epicenter[1])**2
            ) * 111
            
            features = [
                lat / 90,  # Normalize
                lon / 180,
                dist / 10,  # km
                magnitude / 10,
                data.get('street_count', 2) / 10,
                1.0,  # Bias
                0.0,  # Padding
                0.0
            ]
            node_features.append(features)
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        # Kenar listesi
        edge_index = []
        for u, v, _ in graph.edges(keys=True):
            edge_index.append([node_to_idx[u], node_to_idx[v]])
        
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        
        return Data(x=x, edge_index=edge_index)
    
    def train_model(
        self,
        train_data: List[Tuple[nx.MultiDiGraph, Dict[str, float]]],
        epochs: int = 100,
        lr: float = 0.001
    ) -> List[float]:
        """
        Modeli sentetik veri ile eğit.
        """
        if not self.use_gnn:
            logger.warning("Basit model eğitilemez")
            return []
        
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.BCELoss()
        
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            for graph, true_damages in train_data:
                # Rastgele merkez ve şiddet
                epicenter = (41.0, 29.0)  # Placeholder
                magnitude = 6.5
                
                data = self._graph_to_pyg(graph, epicenter, magnitude)
                
                # Forward pass
                pred_damages = self.model.predict_edge_damage(
                    data.x, data.edge_index
                )
                
                # True labels
                true_labels = torch.tensor([
                    true_damages.get(f"{u}_{v}_{k}", 0.0)
                    for u, v, k in graph.edges(keys=True)
                ], dtype=torch.float)
                
                # Loss
                loss = criterion(pred_damages, true_labels)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(train_data)
            losses.append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        return losses
    
    def save_model(self, path: Path) -> None:
        """Modeli kaydet"""
        if self.use_gnn:
            torch.save(self.model.state_dict(), path)
            logger.info(f"Model kaydedildi: {path}")
    
    def load_model(self, path: Path) -> None:
        """Modeli yükle"""
        if self.use_gnn:
            self.model.load_state_dict(torch.load(path))
            logger.info(f"Model yüklendi: {path}")


# Test
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from data.graph_loader import GraphLoader
    
    # Demo graf
    loader = GraphLoader()
    G = loader._create_demo_graph()
    
    # Predictor
    predictor = DamagePredictor()
    
    # Tahmin
    damages = predictor.predict(G, (41.02, 29.02), 6.5)
    
    print(f"\nToplam kenar: {len(damages)}")
    print(f"Hasarlı kenar (>0.5): {sum(1 for v in damages.values() if v > 0.5)}")
    print(f"Ortalama hasar: {np.mean(list(damages.values())):.3f}")
