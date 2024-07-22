from mls.feature_engineering.scalers import Scaler
from sklearn.preprocessing import StandardScaler

class Standard(Scaler):
    def __init__(self) -> None:
        super().__init__(StandardScaler())