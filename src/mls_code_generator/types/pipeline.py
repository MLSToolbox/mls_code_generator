
class Pipeline:
    def __init__(self):
        self.nodes = {}
        self.steps = {}
        self.pipeline_id = ""

    def load_pipeline(self, loader):
        """
        Loads a pipeline into the current pipeline instance.

        Parameters:
            loader (PipelineLoader): The pipeline loader to use for loading the pipeline.

        Returns:
            None
        """
        loader.load_pipeline(self)
    def get_step(self, step_id : str):
        """
        Retrieves a step from the pipeline by its ID.

        Parameters:
            step_id (str): The ID of the step to retrieve.

        Returns:
            The step object associated with the given step ID.

        Raises:
            ValueError: If the step ID is not found in the pipeline.
        """
        if step_id not in self.steps:
            raise ValueError("Step not found")
        return self.steps[step_id]
    def get_node(self, node_id : str):
        """
        Retrieves a node from the pipeline by its ID.

        Parameters:
            node_id (str): The ID of the node to retrieve.

        Returns:
            The node object associated with the given node ID.

        Raises:
            ValueError: If the node ID is not found in the pipeline.
        """
        if node_id not in self.nodes:
            raise ValueError("Node not found")
        return self.nodes[node_id]
    def add_steps(self, steps):
        """
        Adds a collection of steps to the pipeline.

        Parameters:
            steps (dict): A dictionary of steps to add to the pipeline.

        Returns:
            None
        """
        self.steps.update(steps)
    def add_nodes(self, nodes):
        """
        Adds a collection of nodes to the pipeline.

        Parameters:
            nodes (dict): A dictionary of nodes to add to the pipeline.

        Returns:
            None
        """
        self.nodes.update(nodes)
