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
		for input in config['inputs']:
			self.inputs.append(input['port_label'])
		for output in config['outputs']:
			self.outputs.append(output['port_label'])
		self.nodeName = config['node']
		self.origin = config['origin']
		
		self.module_dependencies = config['dependencies']
	def getCopy(self):
		return CustomNode(self.config)
