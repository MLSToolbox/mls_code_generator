from mls.data_transformation import DataTransformationStep
from sklearn.model_selection import train_test_split
from mls.data_collection import DataFrame

class SplitTrainTest(DataTransformationStep):
    def __init__(self, train_percentage : float, features, truth):
        super().__init__()
        self.train_percentage = train_percentage
        self.features = features
        self.truth = truth
        
    def execute(self):
        features_origin, port = self.features
        features_dataframe= features_origin.get(port)
        features_data = features_dataframe.getData()

        truth_origin, port = self.truth
        truth_dataframe = truth_origin.get(port)
        truth_data = truth_dataframe.getData()

        x_train, x_test, y_train, y_test = train_test_split(features_data, truth_data, train_size = self.train_percentage)

        x_train_dataframe, y_train_dataframe, x_test_dataframe, y_test_dataframe = [DataFrame(), DataFrame(), DataFrame(), DataFrame()]

        x_train_dataframe.setData(x_train)
        y_train_dataframe.setData(y_train)
        x_test_dataframe.setData(x_test)
        y_test_dataframe.setData(y_test)

        self.outputs["features_train"] = x_train_dataframe
        self.outputs["truth_train"] = y_train_dataframe
        self.outputs["features_test"] = x_test_dataframe
        self.outputs["truth_test"] = y_test_dataframe