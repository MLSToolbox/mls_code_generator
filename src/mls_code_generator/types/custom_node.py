from . node import Node

class CustomNode(Node):
    def __init__(self, config):
        super().__init__()
        self.config = config
        for param in config['params']:
            self.params[param['param_label']] = {
                "value" : None,
                "type" : param['param_type']
            }
        for input_socket in config['inputs']:
            self.inputs.append(input_socket['port_label'])
        for output in config['outputs']:
            self.outputs.append(output['port_label'])
        self.node_name = config['node']
        self.origin = config['origin']
        self.module_dependencies = config['dependencies']
    def get_copy(self):
        """
        Returns a deep copy of the CustomNode object.

        This method creates a new instance of the CustomNode
        class with the same configuration as the current object.
        It copies all the attributes and values from the current object to the new object.

        Returns:
            CustomNode: A new CustomNode object with the same configuration as the current object.
        """
        return CustomNode(self.config)
