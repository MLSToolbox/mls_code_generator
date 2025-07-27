""" Configuration Loader """

from . types import CustomNode
class ConfigLoader:
    """ Configuration Loader """
    def __init__(self, content) -> None:
        self.content = content
        self.all_nodes = {}

        for node in self.content:
            class_node = CustomNode(node)
            self.all_nodes[node['node']] = class_node
    def get_all_nodes(self) -> dict:
        """
        Returns a dictionary containing all the nodes loaded in the configuration.

        :return: A dictionary with node names as keys and CustomNode objects as values.
        :rtype: dict
        """
        return self.all_nodes
    def get_node(self, node_name : str) -> CustomNode:
        """
        Retrieves a node from the configuration by its name.

        Args:
            node_name (str): The name of the node to retrieve.

        Returns:
            CustomNode: The node with the given name, or raises a ValueError if not found.
        """
        if node_name not in self.all_nodes:
            raise ValueError("Node not found")
        return self.all_nodes[node_name]
