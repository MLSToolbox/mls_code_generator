from . types import CustomNode

class ConfigLoader:
	def __init__(self, content):
		self.content = content
		self.all_nodes = dict()

		for node in self.content:
			classNode = CustomNode(node)
			self.all_nodes[node['node']] = classNode
	
	def getAllNodes(self):
		return self.all_nodes
	
	def getNode(self, nodeName):
		if nodeName not in self.all_nodes:
			raise Exception("Node not found")
		return self.all_nodes[nodeName]