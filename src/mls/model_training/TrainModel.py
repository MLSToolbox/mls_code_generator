from mls.model_training import ModelTrainingStep

class TrainModel(ModelTrainingStep):
    def __init__(self, epochs : int, bach_size : int, features, truth, optimizer, model) -> None:
        super().__init__()

        self.epochs = epochs
        self.bach_size = bach_size
        self.features = features
        self.truth = truth
        self.optimizer = optimizer
        self.model = model

    def execute(self):
        model_origin, port = self.model
        model = model_origin.get(port)
        optimizer_origin, port = self.optimizer
        optimizer = optimizer_origin.get(port)

        features_origin, port = self.features
        features = features_origin.get(port)

        truth_origin, port = self.truth
        truth = truth_origin.get(port)

        model.fit(features, truth, epochs=self.epochs, batch_size=self.bach_size, optimizer=optimizer)

        self.outputs["model"] = model
