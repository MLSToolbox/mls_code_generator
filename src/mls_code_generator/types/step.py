class Step:
	def __init__(self, id):
		self.id = id
		self.nodes = []
		self.data = ""
		self.name = ""
		self.outs = []

	def addNode(self, node):
		self.nodes.append(node)
	
	def addConnection(self, source, target, sourcePort, targetPort):
		# find target node
		targetNode = None
		for node in self.nodes:
			if node.id == target:
				targetNode = node
				break
		
		# find source node
		sourceNode = None
		for node in self.nodes:
			if node.id == source:
				sourceNode = node
				break
		
		# add dependency
		targetNode.addDependency(targetNode, targetPort, sourceNode, sourcePort)
		sourceNode.addSource(sourcePort, targetNode, targetPort)
	
	def setData(self, data):
		self.data = data
		self.name = data['params']['description']['value'].replace("-"," ")
		self.rName = "".join([i.capitalize() for i in self.name.split(" ")])
		self.name = self.name.lower()
		self.name = self.name.replace(' ', '_')
	
	def generateCode(self):
		print("Generating code for module: ", self.name)
		code = ""
		copy_nodes = self.nodes.copy()
		node_count = dict()
		node_dependencies = []
		while(len(copy_nodes) > 0):
			for node in copy_nodes:
				if node.nodeName == 'Parameter':
					copy_nodes.remove(node)
					continue
				if not node.isReady():
					continue
				if node_count.get(node.nodeName) is None:
					node_count[node.nodeName] = 1
				else:
					node_count[node.nodeName] += 1
				variable_name = node.nodeName.replace(" ", "_").lower()
				if node_count[node.nodeName] > 1:
					variable_name += "_" + str(node_count[node.nodeName])
				node.variable_name = variable_name
				if node.nodeName == 'Input' or node.nodeName == 'Output':
					copy_nodes.remove(node)
					for p in node.sources:
						for target, target_port in node.sources[p]:
							target.pastDependency(target, target_port)
					continue
				code += node.generateCode()
				code += "self.orchestrator.add(" + variable_name + ")\n"
				node_dependencies.append(variable_name)
				code += "\n"
				copy_nodes.remove(node)
				for p in node.sources:
					for target, target_port in node.sources[p]:
						target.pastDependency(target, target_port)
				break

		return code
	def getDependenciesCode(self):
		dependencies = dict()
		for node in self.nodes:
			node_dep = node.getDependencies()
			for dep in node_dep.keys():
				if dep not in dependencies:
					dependencies[dep] = set()
				dependencies[dep].update(node_dep[dep])

		code = ""
		if "orchestration" not in dependencies:
			dependencies["orchestration"] = set()
		dependencies["orchestration"].add("Step")
		dependencies["orchestration"].add("Orchestrator")
		for dep in dependencies.keys():
			code += "from mls_lib." + dep + " import " + ", ".join(dependencies[dep]) + "\n"
		return code

	def getOutput(self, source):
		return "NO OUTPUT IN PACKAGE: " + self.name
	
	def getOutputCode(self):
		code = ""
		for node in self.nodes:
			if node.nodeName == 'Output':
				dep, port, _, _ = node.dependencies[0]
				code += "self._setOutput('" + node.getParam('key') + "',\n"
				code += "\tself.orchestrator.getStepOutput('" + dep.variable_name + "', '" + port + "'))\n" 
		return code
	
	def setInputOrigin(self, target, origin):
		for node in self.nodes:
			if (node.nodeName == 'Input') and (node.params["key"]["value"] == target):
				node.params = {
					"key" : node.params["key"]
				}
				break