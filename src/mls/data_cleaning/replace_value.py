from mls.data_cleaning import DataCleaningStep

class ReplaceValue(DataCleaningStep):
    def __init__(self, value_from, value_to, origin):
        super().__init__(
            origin = origin
        )
        
        self.value_from = value_from
        self.value_to = value_to

    def execute(self):
        origin, port = self.origin
        data = origin.get(port).data
        ## FIXME: data = data.fillna(self.value)
        self.outputs["result"] = data
