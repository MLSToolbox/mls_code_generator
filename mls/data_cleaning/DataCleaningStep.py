from mls.orchestration import Step

class DataCleaningStep(Step):
    def __init__(self, origin) -> None:
        super().__init__()
        self.origin = origin