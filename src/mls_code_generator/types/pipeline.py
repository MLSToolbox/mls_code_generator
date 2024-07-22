
class Pipeline:
    def __init__(self):
        self.nodes = dict()
        self.steps = dict()
        self.pipeline_id = ""

    def loadPipeline(self, loader):
        loader.loadPipeline(self)
    
    def getStep(self, stepID):
        if stepID not in self.steps:
            raise Exception("Step not found")
        return self.steps[stepID]
    
    def getNode(self, nodeID):
        if nodeID not in self.nodes:
            raise Exception("Node not found")
        return self.nodes[nodeID]
    
    def addSteps(self, steps):
        self.steps.update(steps)
    
    def addNodes(self, nodes):
        self.nodes.update(nodes)