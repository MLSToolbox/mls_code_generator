from mls.orchestration import Step

class Out(Step):
    def __init__(self, key, value):
        super().__init__()
        self.key = key
        self.origin, self.port = value
    
    def execute(self):
        self.outputs[self.key] = self.origin.get(self.port)