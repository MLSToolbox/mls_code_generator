from mls.feature_engineering.encoders import Encoder
from category_encoders import OneHotEncoder
class OneHotEncoder(Encoder):
    def __init__(self) -> None:
        super().__init__(OneHotEncoder())