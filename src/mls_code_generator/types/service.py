class Service:
    def __init__(self, service_id: str) -> None:
        self.service_id = service_id
        self.steps = []

    def __repr__(self):
        return str({
            "service_id": self.service_id,
            "steps": [step.name for step in self.steps]
        })

    def __str__(self):
        return str(self.__repr__())

    def add_step(self, step) -> None:
        """
        Adds a Step (Stage) to this service.

       Args:
            step (Step): The step to be added to the service.

       Returns:
            None
        """
        self.steps.append(step)

    def get_dependencies(self):
        """
        Aggregates and returns all the module dependencies required by 
        the steps assigned to this service. This is essential for 
        generating optimized Dockerfiles later.

        Returns:
            dict: A dictionary containing the aggregated dependencies.
        """
        service_dependencies = {}

        for step in self.steps:
            for node in step.nodes:
                node_dependencies = node.get_dependencies()
                for module, elements in node_dependencies.items():
                    if module not in service_dependencies:
                        service_dependencies[module] = set()
                    service_dependencies[module].update(elements)

        if "orchestration" not in service_dependencies:
            service_dependencies["orchestration"] = set()
        service_dependencies["orchestration"].add("Stage")

        return service_dependencies