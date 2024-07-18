class Step:
    def __init__(self) -> None:
        self.inputs = dict()
        self.outuputs = dict()
        pass

    def execute(self):
        print("Executed abstract Step")
        pass

    def set(self, port, value):
        self.inputs[port] = value
    
    def get(self, port):
        return self.outuputs[port]