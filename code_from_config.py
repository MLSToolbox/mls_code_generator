import json

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

class Module:
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
			code += "from mls." + dep + " import " + ", ".join(dependencies[dep]) + "\n"
		return code

	def getOutput(self, source):
		return "NO OUTPUT IN PACKAGE: " + self.name

	def setInputOrigin(self, target, origin):
		for node in self.nodes:
			if (node.nodeName == 'Input') and (node.params["key"]["value"] == target):
				node.params = {
					"key" : node.params["key"]
				}
				break
	
	def getDvcConfig(self):
		dvc_config = dict()
		dvc_config['cmd'] = "python3 src/"+self.name+".py"
		dvc_config['deps'] = ["src/"+self.name+".py"]
		dvc_config['outs'] = []
		for node in self.nodes:
			dvc_config['deps'].append(node.getDvcDeps())
			dvc_config['outs'].append(node.getDvcOuts())
		return dvc_config

class ModuleHandler:
	def __init__(self, content, nodes ):
		self.content = content
		self.all_modules = dict()
		self.all_nodes = dict()
		self.available_nodes = nodes

		## Creating all the modules
		for module in self.content:
			currentModule = Module(module)
			self.all_modules[module] = currentModule
			for node in self.content[module]['nodes']:
				if node['nodeName'] not in self.available_nodes:
					classNode = Node()
				else:
					classNode = self.available_nodes[node['nodeName']].getCopy()
				classNode.setData(node)
				currentModule.addNode(classNode)
				self.all_nodes[classNode.id] = classNode

		## Adding connections to the modules
		for module in self.all_modules.values():
			module_id = module.id
			for connection in self.content[module_id]['connections']:
				module.addConnection(connection['source'], connection['target'], connection['sourceOutput'], connection['targetInput'])
		
		## Adding data to the modules from the parent node
		for module in self.all_modules.values():
			if (module.id not in self.all_nodes):
				continue
			module.setData(self.all_nodes[module.id].data)

		## Inject Output routes:
		for node in self.all_nodes.values():
			if node.nodeName == 'Output':
				node.params = {
					"key" : node.params["key"]
				}
		
		## Inject Outputs into other other module inputs:
		for connection in self.content['root']['connections']:
			source = connection['source']
			target = connection['target']
			sourceOutput = connection['sourceOutput']
			targetInput = connection['targetInput']
			sourceModule = self.all_modules[source]
			targetModule = self.all_modules[target]
			targetModule.setInputOrigin(targetInput, sourceModule.getOutput(sourceOutput))

		## Add parent to each node 
		for module in self.all_modules.values():
			for node in module.nodes:
				node.parent = module

	def generatePackageCode(self, write_path  = "./output/src"):
		root = self.all_modules['root']
		packages = root.nodes

		for package in packages:
			c_package = self.all_modules[package.id]

			code = c_package.getDependenciesCode()
			code += "\n"
			code += "class " + c_package.rName +"(Step):\n"
			code += "\tdef __init__(self, **kwargs):\n"
			code += "\t\tsuper().__init__(**kwargs)\n"
			
			code += "\t\tself.orchestrator = Orchestrator()\n"

			package_code = c_package.generateCode() 
			for j in package_code.split("\n"):
				code += "\t\t" + j + "\n"

			code += "\tdef execute(self):\n"
			code += "\t\tself.orchestrator.execute()\n"

			file_path = write_path + "/" + c_package.rName + ".py"
			file = open(file_path, "w")
			file.write(code)
			file.close()
			
			this_package_node = self.all_nodes[package.id]
			modules_id_i_depend_on = set()
			
			for source in this_package_node.dependencies:
				modules_id_i_depend_on.add(source[0].id)

	def generateMainCode(self, write_path  = "./output/src"):
		root = self.all_modules['root']
		packages = root.nodes
		code = "from mls.orchestration import Orchestrator\n"


		for package in packages:
			c_package = self.all_modules[package.id]
			code += "from . " + c_package.rName + " import " + c_package.rName + "\n"

		code += "\n"
		code += "def main():\n"
		code += "\troot = Orchestrator()\n"

		copy_nodes = packages.copy()
		node_dependencies = []
		while(len(copy_nodes) > 0):
			for node in copy_nodes:
				c_package = self.all_modules[node.id]
				if not node.isReady():
					continue
				variable_name = c_package.name
				node.variable_name = variable_name
				node.origin_label = c_package.rName
				node.params = dict()
				code += "\t" + "\n\t".join(node.generateCode().split("\n"))
				code += "root.add(" + variable_name + ")\n"
				node_dependencies.append(variable_name)
				code += "\n"
				copy_nodes.remove(node)
				for p in node.sources:
					for target, target_port in node.sources[p]:
						target.pastDependency(target, target_port)
				break

		code += "\troot.execute()\n"

		file_path = write_path + "/main.py"

		file = open(file_path, "w")
		file.write(code)
		file.close()

	def generateCode(self, write_path  = "./output/src"):
		self.generatePackageCode(write_path)
		self.generateMainCode(write_path)

class NodesLoader:
	def __init__(self, content):
		self.content = content
		self.all_nodes = dict()

		for node in self.content:
			classNode = CustomNode(node)
			self.all_nodes[node['node']] = classNode
	
	def getNodes(self):
		return self.all_nodes
			
def main():
	editor_path = 'fixed_editor.json'
	nodes_config_path = 'nodes.json'
	content = json.load(open(editor_path))
	nodes_config = json.load(open(nodes_config_path))
	availableNodes = NodesLoader(content = nodes_config['nodes'])
	moduleArray = ModuleHandler(content = content, nodes = availableNodes.getNodes())
	moduleArray.generateCode()
	pass



if __name__ == '__main__':
	main()