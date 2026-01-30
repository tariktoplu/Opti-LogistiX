"""
Opti-Logistix Konfigürasyon Ayarları
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # Proje Yolları
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    
    # API Ayarları
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    
    # Harita Ayarları
    DEFAULT_CITY: str = "Kadıköy, Istanbul, Turkey"
    MAP_NETWORK_TYPE: str = "drive"  # drive, walk, bike
    
    # Model Hiperparametreleri - GNN
    GNN_HIDDEN_CHANNELS: int = 64
    GNN_NUM_LAYERS: int = 2
    GNN_DROPOUT: float = 0.3
    GNN_LEARNING_RATE: float = 0.001
    GNN_EPOCHS: int = 100
    
    # Model Hiperparametreleri - RL
    RL_LEARNING_RATE: float = 3e-4
    RL_N_STEPS: int = 2048
    RL_BATCH_SIZE: int = 64
    RL_TOTAL_TIMESTEPS: int = 50000
    
    # Ödül Fonksiyonu Ağırlıkları
    REWARD_TIME_WEIGHT: float = 1.0
    REWARD_URGENCY_WEIGHT: float = 50.0
    REWARD_RISK_WEIGHT: float = 10.0
    
    # Araç Hızları (km/h)
    VEHICLE_SPEEDS: dict = Field(default={
        "ambulance": 60,
        "fire_truck": 50,
        "rescue": 45,
        "supply_truck": 40
    })
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
