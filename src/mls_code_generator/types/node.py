class Node:
	def __init__(self):
		self.id = None
		self.data = None
		self.dependencies = []
		self.sources = dict()
		self.nodeName = None
		self.parent = None
		self.ready = []
		self.params = dict()
		self.inputs = []
		self.outputs = []
		self.origin = ""
		self.origin_label = ""
		self.module_dependencies = dict()
		self.variable_name = ""
			
	def setData(self, data):
		self.id = data['id']
		self.data = data
		if self.nodeName is None:
			self.nodeName = data['nodeName']
		for params in data['params']:
			self.params[params] = dict()
			try:
				param_val = data['params'][params]['value']
				self.params[params]['value'] = param_val
			except KeyError:
				self.params[params]['value'] = ""
			self.params[params]['type'] = data['params'][params]['type']
		self.origin_label = ""
		if "custom" in self.origin:
			self.origin_label = self.origin["custom"]
		elif "parameter" in self.origin:
			self.origin_label = self.params[self.origin["parameter"]]["value"]

	def setParent(self, parent):
		self.parent = parent

	def addDependency(self, dep, port, src, srcPort):
		self.dependencies.append((src, srcPort, dep, port))
		self.ready.append(False)
	
	def addSource(self, my_port, target, target_port):
		if my_port in self.sources:
			self.sources[my_port].append((target, target_port))
		else:
			self.sources[my_port] = [(target, target_port)]
	
	def isReady(self):
		for i in self.ready:
			if not i: return False
		return True
	
	def pastDependency(self,src, srcPort):
		for i, dep in enumerate(self.dependencies):
			if dep[2] == src and dep[3] == srcPort:
				self.ready[i] = True
				return None
			
	def _getInput(self, side):
		for dep in self.dependencies:
			if dep[3] == side:
				return dep[0], dep[1]
		return [None, None]
			
	def getOutput(self, port):
		if port not in self.outputs:
			return "NO OUTPUT FOUND: " + port + " in " + self.nodeName
		
		return port
	
	def getParam(self, label):
		if label not in self.params:
			return "NO PARAM FOUND: " + label + " in " + self.nodeName

		return self.params[label]['value']

	def __repr__(self) -> str:
		return self.nodeName

	def __str__(self) -> str:
		return self.nodeName
	
	def generateCode(self):
		if self.origin is None:
			return "# " + self.nodeName + " not implemented yet\n"
		
		final_code = ""
		if "description" in self.params:
			description = self.getParam("description")
			if description is not None and len(description) > 0:
				final_code += "# " + str(self.getParam("description")) + "\n"
		final_code += self.variable_name + " = " + self.origin_label + "(\n"
		for param in self.params:
			if param == "description":
				continue
			if ( "parameter" in self.origin ) and ( param == self.origin["parameter"] ):
				continue
			final_code += "\t" + param + " = '" + str(self.getParam(param)) + "',\n"
		for dependency in self.dependencies:
			inp, inp_port, me, me_port = dependency
			if inp.nodeName == "Input":
				final_code += "\t" + me_port + " = self._getInputStep('" + inp.getParam('key')+"'),\n"
			else:
				final_code += "\t" + me_port + " = (" + inp.variable_name + \
							", '" + inp_port + "'),\n"
		final_code += ")\n"
		return final_code
	
	def portIsMultiple(self, port):
		if port in self.sources:
			return len(self.sources[port]) > 1
		
	def isOutputMultiple(self, port):
		for dep in self.dependencies:
			if dep[3] == port:
				return dep[0].portIsMultiple(dep[1])
		return None
	
	def getDependencies(self) -> dict:
		final_dependencies = dict()
		for dep in self.module_dependencies:
			if dep not in final_dependencies:
				final_dependencies[dep] = set()
			mid_dependencies = self.module_dependencies[dep]
			for mid_dep in mid_dependencies:
				dep_origin = mid_dependencies[mid_dep]
				if dep_origin == "custom":
					final_dependencies[dep].add(mid_dependencies["value"])
				elif dep_origin == "parameter":
					final_dependencies[dep].add(self.getParam(mid_dependencies["value"]))
		return final_dependencies

	def getParameter(self, nodeID):
		if self.parent is None:
			return "'NONE'"
		parameterNode = self.parent.getNode(nodeID)
		if parameterNode is None:
			return "'NONE'"

		return parameterNode.getParam("description")
