from mls.feature_engineering import FeatureEngineeringStep

class TrainEncoder(FeatureEngineeringStep):
    def __init__(self, columns, data, encoder):
        super().__init__()
        self.columns = columns
        self.data = data
        self.encoder = encoder

    def execute(self):
        data_origin, port = self.data
        dataframe = data_origin.get(port)
        data = dataframe.getData()

        encoder_origin, port = self.encoder
        encoder = encoder_origin.get(port)

        encoder.fit_transform(data, self.columns)
        dataframe.setData(data)
        self.outputs["encoder"] = encoder

        self.outputs["data"] = dataframe
        