from mls.orchestration import Out, In

class Orchestrator:
    def __init__(self, **inputs):
        super().__init__()
        self.steps = []
        self.inputs = inputs
    
    def set(self, port, value):
        self.inputs[port] = value
    
    def get(self, port):
        return self.outuputs[port]
    
    def add(self, step):
        self.steps.append(step)
    
    def clear(self):
        self.steps = []
    
    def execute(self):
        for step in self.steps:
            if (type(step) == In):
                origin, port = self.inputs[step.key]
                step.set(step.key, origin.get(port))

            step.execute()
            if (type(step) == Out):
                val = step.get(step.key)
                self.outputs[step.key] = val
