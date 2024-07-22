from mls.model_evaluation import ModelEvaluationStep

class Evaluate(ModelEvaluationStep):
    def __init__(self, model, x_test, y_test):
        super().__init__()

        self.model = model
        self.x_test = x_test
        self.y_test = y_test
    
    def execute(self):
        model_origin, port = self.model
        model = model_origin.get(port)
        x_test_origin, port = self.x_test
        x_test = x_test_origin.get(port)
        y_test_origin, port = self.y_test
        y_test = y_test_origin.get(port)

        result = model.evaluate(x_test, y_test)

        self.outputs["result"] = result