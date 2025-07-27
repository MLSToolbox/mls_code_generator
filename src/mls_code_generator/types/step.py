

class Step:
    def __init__(self, id : str) -> None:
        self.id = id
        self.nodes = []
        self.data = ""
        self.original_name = ""
        self.name = ""
        self.r_name = ""
        self.outs = []
        self.variable_name = ""
        self.dependencies = []

    def __repr__(self):
        return str({
            "id" : self.id,
            "nodes" : self.nodes,
            "data" : self.data,
            "original_name" : self.original_name,
            "name" : self.name,
            "r_name" : self.r_name,
            "outs" : self.outs,
            "dependencies" : self.dependencies,
            "variable_name" : self.variable_name,
        })
    def __str__(self):
        return str(self.__repr__())

    def add_node(self, node) -> None:
        """
        Adds a new node to the step's collection of nodes.

        Args:
            node (Node): The node to be added to the step.

        Returns:
            None
        """
        self.nodes.append(node)
    def add_connection(self, source : str, target : str,
                       source_port : str, target_port : str) -> None:
        """
        Establishes a connection between two nodes within the step.

        Args:
            source (str): The ID of the source node.
            target (str): The ID of the target node.
            source_port (str): The port of the source node.
            target_port (str): The port of the target node.

        Returns:
            None
        """
        # find target node
        target_node = None
        for node in self.nodes:
            if node.id == target:
                target_node = node
                break
        # find source node
        source_node = None
        for node in self.nodes:
            if node.id == source:
                source_node = node
                break
        # add dependency
        if target_node is not None:
            target_node.add_dependency(target_node, target_port, source_node, source_port)
        if source_node is not None:
            source_node.add_source(source_port, target_node, target_port)
    def set_data(self, data):
        """
        Sets the data for the current step.

        Args:
            data (dict): The data to be set.

        Returns:
            None
        """
        self.data = data
        if data['params']['link']['value'] != "":
            data['params']['Stage name']['value'] = data['params']['Stage name']['value'][:-1]
        self.name = data['params']['Stage name']['value'].replace("-"," ")
        self.original_name = data['params']['Stage name']['value']
        self.r_name = "".join([i.lower()[0] for i in self.name.split(" ")])
        self.variable_name = self.r_name
        self.name = self.name.lower()
        self.name = self.name.replace(' ', '_')
    def generate_code(self):
        """
        Generates the code for the current step by iterating over its nodes, 
        resolving dependencies, and generating code for each node.

        Parameters:
            None

        Returns:
            str: The generated code for the current step.
        """
        print("Generating code for module: ", self.name)
        code = ""
        copy_nodes = self.nodes.copy()
        node_count = dict()
        node_dependencies = []

        while(len(copy_nodes) > 0):
            for node in copy_nodes:
                # Gross exploration of the graph
                if not node.is_ready():
                    continue
                # Pass ready dependencies to next nodes as these ones don't need to be generated
                if node.node_name in ['Input', 'Output']:
                    copy_nodes.remove(node)
                    for p in node.sources:
                        for target, target_port in node.sources[p]:
                            target.past_dependency(target, target_port)
                    continue
                node_name = node.node_name
                variable_name = node.variable_name
                if node_count.get(node_name) is None:
                    node_count[node_name] = 1
                else:
                    node_count[node_name] += 1
                if node_count[node_name] > 1:
                    variable_name += "_" + str(node_count[node_name])
                    node.variable_name = variable_name
                variable_name = node.variable_name
                code += node.generate_code()
                code += self.r_name + ".add_task(\n\t"

                code += variable_name 
                if len(node.dependencies) > 0:
                    code += ",\n"
                    for port_code in node.get_dependencies_code():
                        code += "\t" + port_code + ",\n"
                    code = code[:-2]
                code += "\n)\n"
                node_dependencies.append(variable_name)
                code += "\n"
                copy_nodes.remove(node)
                for p in node.sources:
                    for target, target_port in node.sources[p]:
                        target.past_dependency(target, target_port)
                break
        return code
    
    def generate_main_code(self):
        code = ""
        copy_nodes = self.nodes.copy()
        step_dependencies = []
        for node in copy_nodes:
            if node.node_name == 'Input':
                if len(node.dependencies) > 0:
                    step_dependencies.append(node.dependencies[0].name)
        code += "("
        if len(step_dependencies) > 0:
            code += "\n"
        for dep in step_dependencies:
            code += "\t" + dep + ",\n"
        if len(step_dependencies) > 0:
            code = code[:-2]
            code += "\n"
        code += ")\n"
        return code

    def get_dependencies_code(self):
        """
        Generates the import statements for the dependencies of the current step.

        This function iterates over each node in the step and retrieves its dependencies.
        It then collects the dependencies into a dictionary, where the keys are the module names
        and the values are sets of the specific dependencies for each module.

        If the "orchestration" module is not present in the dependencies dictionary, it is added
        with the "Step" and "Orchestrator" dependencies.

        Finally, the function constructs the import statements by iterating over the keys of the
        dependencies dictionary and constructing the import statement for each module. The import
        statement includes the module name and the specific dependencies for that module.

        Returns:
            str: The import statements for the dependencies of the current step.
        """
        dependencies = {}
        for node in self.nodes:
            node_dep = node.get_dependencies()
            for dep in node_dep.keys():
                if dep not in dependencies:
                    dependencies[dep] = set()
                dependencies[dep].update(node_dep[dep])

        code = ""
        if "orchestration" not in dependencies:
            dependencies["orchestration"] = set()
        dependencies["orchestration"].add("Stage")
        for dep, val in dependencies.items():
            code += "from mls_lib." + dep + " import " + ", ".join(sorted(val)) + "\n"
        return code

    def get_output(self, source):
        return "NO OUTPUT IN PACKAGE: " + self.name
    def get_output_code(self):
        """
        Generates the code for setting the output of the current step.

        This function iterates over each node in the step and checks if the node is an 'Output' node.
        If it is, the function generates the code for setting the output of the step using the 
        'get_step_output' method of the orchestrator.

        Returns:
            str: The generated code for setting the output of the step.
        """
        code = ""
        for node in self.nodes:
            if node.node_name == 'Output':
                if len(node.dependencies) > 0:
                    dep, port, _, _ = node.dependencies[0]
                    code += self.r_name + ".add_output('" + node.get_param('key') + "', "
                    code += "(" + \
                        dep.variable_name + ", '" + port + "'))\n"
        return code
        
    def get_node(self, note_id):
        for node in self.nodes:
            if node.node_id == note_id:
                return node
        return None

    def add_main_connection(self, source, source_port, target_port):
        self.dependencies.append((source, source_port, target_port))
