from . types import Node
from . types import Step

class PipelineLoader:
	def __init__(self, content, node_config) -> None:
		self.content = content
		self.node_config = node_config
		pass
	
	def loadPipeline(self, parent):
		all_steps = dict()
		all_nodes = dict()
		available_nodes = self.node_config
		content = self.content

		## Creating all the steps
		for step in content:
			current_step = Step(step)
			all_steps[step] = current_step
			for node in content[step]['nodes']:
				if node['nodeName'] not in available_nodes.getAllNodes():
					classNode = Node()
				else:
					classNode = available_nodes.getNode(node['nodeName']).getCopy()
				classNode.setData(node)
				current_step.addNode(classNode)
				all_nodes[classNode.id] = classNode

		## Adding connections to the steps
		for step in all_steps.values():
			step_id = step.id
			for connection in content[step_id]['connections']:
				step.addConnection(connection['source'], connection['target'], connection['sourceOutput'], connection['targetInput'])
		
		## Adding data to the steps from the parent node
		for step in all_steps.values():
			if (step.id not in all_nodes):
				continue
			step.setData(all_nodes[step.id].data)

		## Inject Output routes:
		for node in all_nodes.values():
			if node.nodeName == 'Output':
				node.params = {
					"key" : node.params["key"]
				}
		
		## Inject Outputs into other other step inputs:
		for connection in content['root']['connections']:
			source = connection['source']
			target = connection['target']
			sourceOutput = connection['sourceOutput']
			targetInput = connection['targetInput']
			sourceStep = all_steps[source]
			targetStep = all_steps[target]
			targetStep.setInputOrigin(targetInput, sourceStep.getOutput(sourceOutput))

		## Add parent to each node 
		for step in all_steps.values():
			for node in step.nodes:
				node.parent = step
		
		parent.addSteps(all_steps)
		parent.addNodes(all_nodes)
