from mls.orchestration import Step

class In(Step):
    def __init__(self, key):
        super().__init__()
        self.key = key

    def execute(self):
        pass
        
