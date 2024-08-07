from copy import deepcopy

class CodeGenerator:
	def __init__(self):
		self.modules = dict()
	
	def __generateStepCode(self, pipeline):
		root = pipeline.getStep('root')
		steps = root.nodes

		for step in steps:
			c_step = pipeline.getStep(step.id)

			code = c_step.getDependenciesCode()
			code += "\n"
			code += "class " + c_step.rName +"(Step):\n"
			code += "\tdef __init__(self, **inputs):\n"
			code += "\t\tsuper().__init__(**inputs)\n"
			
			code += "\t\tself.orchestrator = Orchestrator()\n"
 
			for j in c_step.generateCode().split("\n"):
				code += "\t\t" + j + "\n"

			code += "\tdef execute(self):\n"
			code += "\t\tself.orchestrator.execute()\n"

			for j in c_step.getOutputCode().split("\n"):
				code += "\t\t" + j + "\n"

			code += "\n\t\tself.finishExecution()"

			self.modules[c_step.rName] = code
			
			this_step_node = pipeline.getNode(step.id)
			steps_id_i_depend_on = set()
			
			for source in this_step_node.dependencies:
				steps_id_i_depend_on.add(source[0].id)

	def __generateMainCode(self, pipeline):
		root = pipeline.getStep('root')
		steps = root.nodes
		code = "from mls_lib.orchestration import Orchestrator\n"


		for step in steps:
			c_step = pipeline.getStep(step.id)
			code += "from " + c_step.rName + " import " + c_step.rName + "\n"

		code += "\n"
		code += "def main():\n"
		code += "\troot = Orchestrator()\n"

		copy_nodes = steps.copy()
		node_dependencies = []
		while(len(copy_nodes) > 0):
			for node in copy_nodes:
				c_step = pipeline.getStep(node.id)
				if not node.isReady():
					continue
				variable_name = c_step.name
				node.variable_name = variable_name
				node.origin_label = c_step.rName
				node.params = dict()
				code += "\t" + "\n\t".join(node.generateCode().split("\n"))
				code += "root.add(" + "'" + variable_name + "', " + variable_name + ")\n"
				node_dependencies.append(variable_name)
				code += "\n"
				copy_nodes.remove(node)
				for p in node.sources:
					for target, target_port in node.sources[p]:
						target.pastDependency(target, target_port)
				break

		code += "\troot.execute()\n"
		code += "\nif __name__ == '__main__':\n\tmain()"

		self.modules["main"] = code

	def generateCode(self, pipeline):
		self.__generateStepCode(pipeline)
		self.__generateMainCode(pipeline)
	
	def getModules(self):
		return deepcopy(self.modules)