from mls.data_collection import DataCollectionStep
from mls.data_collection import DataFrame
from mls.data_collection.loaders import *

class LoadDataset(DataCollectionStep):
    def __init__(self, path : str, loader : str):
        super().__init__(),
        termination = path.split(".")[-1]
        self.loader = self.getLoaderFromTermination(termination)
        self.path = path
    def execute(self):
        data = DataFrame(
            loader = self.loader,
            path = self.path 
        )

        self.outputs["resulting_table"] = data

    def getLoaderFromTermination(self, termination : str):
        if termination == "csv":
            return CSVLoader
