from sklearn.linear_model import LinearRegression
from mls.model_training.models import ModelStep

class LinarRegression(ModelStep):
    def __init__(self, parameters : str) -> None:
        self.parameters = parameters
        super().__init__()

    def execute(self):
        self.outputs["model"] = LinearRegression()