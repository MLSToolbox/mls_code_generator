from mls.feature_engineering import FeatureEngineeringStep

class TrainScaler(FeatureEngineeringStep):
    def __init__(self, columns, data, scaler):
        super().__init__()
        self.columns = columns
        self.data = data
        self.scaler = scaler

    def execute(self):
        data_origin, port = self.data
        dataframe = data_origin.get(port)
        data = dataframe.getData()

        scaler_origin, port = self.scaler
        scaler = scaler_origin.get(port)

        scaler.fit_transform(data, self.columns)
        dataframe.setData(data)
        self.outputs["scaler"] = scaler

        self.outputs["data"] = dataframe
        