""" Node: Component that represents a node in a pipeline. """
from operator import is_
from typing import final
from . pipeline import Pipeline
from . step import Step

class Node:
    """ Node: Component that represents a node in a pipeline. """
    def __init__(self):
        """
        Initializes a Node object with the given parameters.

        Parameters:
            None

        Attributes:
            id (str): The unique identifier for this node.
            data (dict): The data associated with this node.
            dependencies (list): A list of tuples where each tuple is a dependency of this node.
            sources (dict): A dictionary where the keys are the ports of this node and the values are lists of tuples where each tuple is a source of this node.
            node_name (str): The name of this node.
            parent (Pipeline): The parent pipeline of this node.
            parent_step (Step): The parent step of this node.
            ready (list): A list of booleans indicating whether the node is ready to be executed.
            params (dict): A dictionary of the parameters of this node.
            inputs (list): A list of strings representing the inputs of this node.
            outputs (list): A list of strings representing the outputs of this node.
            origin (dict): A dictionary containing the origin of the parameters of this node.
            origin_label (str): A string representing the origin of the parameters of this node.
            module_dependencies (dict): A dictionary of the module dependencies of this node.
            variable_name (str): A string representing the variable name of this node.
        """
        self.id = None
        self.data = None
        self.dependencies = []
        self.sources = {}
        self.node_name = None
        self.parent = Pipeline()
        self.parent_step = Step("0")
        self.ready = []
        self.params = {}
        self.inputs = []
        self.outputs = []
        self.origin = {}
        self.origin_label = ""
        self.module_dependencies = {}
        self.variable_name = ""

    def set_data(self, data : dict):
        """
        Sets the data of the node.

        This function sets the data of the node based on the given dictionary.
        The given dictionary should contain the id, data, and params of the node.
        The function also sets the node_name of the node if it is not already set.
        The function also sets the origin_label of the node.

        Parameters:
            data (dict): The dictionary containing the data of the node.

        Returns:
            None
        """
        self.id = data['id']
        self.data = data
        if self.node_name is None:
            self.node_name = data['nodeName']
        for param in data['params']:
            self.params[param] = {}
            try:
                param_val = data['params'][param]['value']
                self.params[param]['value'] = param_val
            except KeyError:
                self.params[param]['value'] = ""
            self.params[param]['type'] = data['params'][param]['type']

            self.params[param]["isParam"] = "custom"
            self.params[param]["param_label"] = ""
            if self.node_name in ["Input", "Output", "Step"]:
                continue
            if "isParam" in data['params'][param]:
                self.params[param]["isParam"] = data['params'][param]["isParam"]
            if "param_label" in data['params'][param]:
                self.params[param]["param_label"] = data['params'][param]["param_label"]
                
        self.origin_label = ""
        if "custom" in self.origin:
            self.origin_label = self.origin["custom"]
        elif "parameter" in self.origin:
            self.origin_label = self.get_param(self.origin["parameter"])

    def set_parent(self, parent : Pipeline):
        """
        Sets the parent pipeline of the node.

        This function sets the parent pipeline of the node. The parent pipeline is the pipeline that contains the node.

        Parameters:
            parent (Pipeline): The parent pipeline of the node.

        Returns:
            None
        """
        self.parent = parent
    
    def set_parent_step(self, parent_step : Step):
        """
        Sets the parent step of the node.

        This function sets the parent step of the node. The parent step is the step that contains the node.

        Parameters:
            parent_step (Step): The parent step of the node.

        Returns:
            None
        """
        self.parent_step = parent_step

    def add_dependency(self, dep , port : str, src, src_port : str) -> None:
        """
        Adds a dependency to the node.

        This function appends a tuple representing a dependency to the node's 
        list of dependencies and marks it as not ready. Each dependency is 
        represented by the source node, source port, destination node, and 
        destination port.

        Parameters:
            dep (Node): The destination node of the dependency.
            port (str): The port on the destination node.
            src (Node): The source node of the dependency.
            src_port (str): The port on the source node.

        Returns:
            None
        """

        self.dependencies.append((src, src_port, dep, port))
        self.ready.append(False)
    
    def add_source(self, my_port : str, target, target_port : str):
        """
        Adds a source to the node.

        This function adds a source connection to the specified port of the node. 
        If the port already has sources, the new source is appended to the list of 
        existing sources. Otherwise, a new list is created for the port.

        Parameters:
            my_port (str): The port on this node to which the source is connected.
            target: The target node that is the source of the connection.
            target_port (str): The port on the target node that is connected.

        Returns:
            None
        """

        if my_port in self.sources:
            self.sources[my_port].append((target, target_port))
        else:
            self.sources[my_port] = [(target, target_port)]
    
    def is_ready(self) -> bool:
        """
        Checks if the node is ready.

        This function checks if all the dependencies of the node have been
        resolved. If all the dependencies have been resolved, the function
        returns True, otherwise it returns False.

        Returns:
            bool: True if the node is ready, False otherwise.
        """
        for i in self.ready:
            if not i:
                return False
        return True
    
    def past_dependency(self, src : str, src_port : str) -> None :
        """
        Marks a dependency as resolved.

        This function iterates through the dependencies of the node and checks if
        there is a dependency with the specified source node and source port. If
        such a dependency is found, it marks the corresponding entry in the ready
        list as True, indicating that the dependency is resolved.

        Parameters:
            src (str): The source node of the dependency.
            src_port (str): The source port of the dependency.

        Returns:
            None
        """
        
        for i, dep in enumerate(self.dependencies):
            if dep[2] == src and dep[3] == src_port:
                self.ready[i] = True
                return None            
    
    def _get_input(self, side):
        for dep in self.dependencies:
            if dep[3] == side:
                return dep[0], dep[1]
        return [None, None]      
    
    def get_output(self, port):
        if port not in self.outputs:
            return "NO OUTPUT FOUND: " + port + " in " + self.node_name
        
        return port
    def get_param(self, label):
        if label not in self.params:
            return "NO PARAM FOUND: " + label + " in " + self.node_name

        return self.params[label]['value']
    
    def get_param_type(self, label):
        if label not in self.params:
            return "NO PARAM FOUND: " + label + " in " + self.node_name
        return self.params[label]['type']
    
    def __repr__(self) -> str:
        return self.node_name
    
    def __str__(self) -> str:
        return self.node_name  
    
    def generate_code(self):
        if self.origin is None:
            return "# " + self.node_name + " not implemented yet\n"
        
        final_code = ""
        if "description" in self.params:
            description = self.get_param("description")
            if description is not None and len(description) > 0:
                final_code += "# " + str(self.get_param("description")) + "\n"
        final_code += self.variable_name + " = " + self.origin_label + "("
        if self.get_param_count() > 0:
            final_code += "\n"
        for param in self.params:
            if self.is_param_label(param):
                final_code += "\t" + param + " =  ParamLoader.load('" + self.get_param_label(param) + "'),\n"
                continue
            if self.get_param_type(param) == "description":
                continue
            if ( "parameter" in self.origin ) and ( param == self.origin["parameter"] ):
                continue
            if (self.get_param_type(param) in ["string", "option", "option_of_options"]):
                final_code += "\t" + param + " = '" + str(self.get_param(param)) + "',\n"
            elif (self.get_param_type(param) == "number"):
                final_code += "\t" + param + " = " + str(self.get_param(param)) + ",\n"
            elif (self.get_param_type(param) == "boolean"):
                final_code += "\t" + param + " = " + str(self.get_param(param)).lower() + ",\n"
            elif (self.get_param_type(param) == "list"):
                param_list = self.get_param(param)
                final_code += "\t" + param + " = [\n"
                for value in param_list[:-1]:
                    final_code += "\t\t'" + str(value) + "',\n"
                if len(param_list) > 0:
                    final_code += "\t\t'" + str(param_list[-1]) + "'\n\t],\n"
                else:
                    final_code += "\t],\n"
            elif (self.get_param_type(param) == "map"):
                param_map = self.get_param(param)
                final_code += "\t" + param + " = {\n"
                for sub_map in param_map[:-1]:
                    final_code += "\t\t'" + str(sub_map['key']) + "': '" + str(sub_map['value']) + "',\n"
                if len(param_map) > 0:
                    final_code += "\t\t'" + str(param_map[-1]['key']) + "': '" + str(param_map[-1]['value']) + "'\n"
                final_code += "\t},\n"
            else:
                raise ValueError("Unknown param type: " + self.get_param_type(param))
        if self.get_param_count() > 0:
            final_code = final_code[:-2]
            final_code += "\n"
        final_code += ")\n"
        return final_code
    
    def get_dependencies_code(self):
        code_parts = []
        for dependency in self.dependencies:
            inp, inp_port, _, me_port = dependency
            if inp.node_name == "Input":
                inp_port = inp.get_param('key')
            if inp.variable_name == "":
                code = me_port + " = None"
            else:
                code = me_port + " = (" + inp.variable_name + ", '" + inp_port + "')"
            code_parts.append(code)
        return code_parts
    
    def is_param_label(self, param):
        if "isParam" in self.params[param] and self.params[param]["isParam"] != "custom":
            return True
        return False
    
    def get_param_label(self, param):
        return ".".join([self.parent_step.name,self.params[param]["param_label"]])
    
    def get_param_count(self):
        """
        Gets the number of parameters in the current node that are available for code generation.

        This function counts the number of parameters in the current node that are of a type that can be used in the code generation process.

        Returns:
            int: The number of parameters that are available for code generation.
        """
        count = 0
        for param in self.params:
            if (self.get_param_type(param) in self.__get_available_param_types()):
                count += 1
        return count

    def __get_available_param_types(self):
        """
        Gets a list of the available parameter types that can be used in the code generation process.

        This function returns a list of strings where each string is a type of parameter that can be used in the code generation process.
        The available parameter types are: string, number, boolean, list, map, option, and option_of_options.

        Returns:
            list: A list of strings of the available parameter types.
        """
        return ["string", "number", "boolean", "list", "map", "option", "option_of_options"]
    
    def port_is_multiple(self, port):
        """
        Checks if the given port is a multiple input port.

        This function checks if the given port is connected to multiple dependencies.
        If it is, it returns True, otherwise it returns False.
        If the port is not connected to any dependencies, it returns None.
        """
        if port in self.sources:
            return len(self.sources[port]) > 1
        return False
        
    def is_output_multiple(self, port):
        """
        Checks if the given port is a multiple output port.

        This function checks if there are multiple dependencies connected to the given port.
        If there are, it checks if the port of the dependency is a multiple output port.
        If the port is a multiple output port, it returns True, otherwise it returns False.
        If the port is not connected to any dependencies, it returns None.
        """
        for dep in self.dependencies:
            if dep[3] == port:
                return dep[0].port_is_multiple(dep[1])
        return None
    
    def get_dependencies(self) -> dict:
        """
        Gets the dependencies of the current node, including those of its parameters
        if they are labels.

        Returns:
            dict: A dictionary where the keys are the module names and the values are
            sets of the dependencies required by the module.
        """
        final_dependencies = {}
        for dep, _ in self.module_dependencies.items():
            if dep not in final_dependencies:
                final_dependencies[dep] = set()
            mid_dependencies = self.module_dependencies[dep]
            for mid_dep in mid_dependencies:
                dep_origin = mid_dependencies[mid_dep]
                if dep_origin == "custom":
                    final_dependencies[dep].add(mid_dependencies["value"])
                elif dep_origin == "parameter":
                    final_dependencies[dep].add(self.get_param(mid_dependencies["value"]))
        for param in self.params:
            if not self.is_param_label(param):
                continue
            if "orchestration" not in final_dependencies:
                final_dependencies["orchestration"] = set()
            final_dependencies["orchestration"].add("ParamLoader")
        return final_dependencies

    def get_label_params(self) -> list[dict]:
        """
        Gets a list of parameters that are label parameters for the current node.

        Label parameters are parameters that are used to label the node in the
        pipeline and are used to generate code that is specific to the node.

        The returned list contains dictionaries where the key is the label and
        the value is the value of the parameter.
        """
        result = []
        for param in self.params:
            if not self.is_param_label(param):
                continue
            param_value = None
            param_type = self.get_param_type(param)
            if param_type in ["string", "option", "option_of_options"]:
                param_value = self.get_param(param)
            elif param_type == "number":
                param_value = float(self.get_param(param))
            elif param_type == "boolean":
                param_value = bool(self.get_param(param).lower())
            elif param_type == "list":
                param_value = self.get_param(param)
            elif param_type == "map":
                param_value = {}
                for sub_map in self.get_param(param):
                    param_value[sub_map['key']] = sub_map['value']
            result.append({self.params[param]["param_label"] : param_value})
        return result
    