from mls.data_transformation import DataTransformationStep

class DropColumns(DataTransformationStep):
    def __init__(self, columns, origin):
        super().__init__()
        self.columns = columns
        self.origin = origin

    def execute(self):
        origin, port = self.origin
        dataframe = origin.get(port)
        data = dataframe.getData()
        data = data.drop(self.columns, axis=1)
        dataframe.setData(data)
        self.outputs["resulting_table"] = dataframe