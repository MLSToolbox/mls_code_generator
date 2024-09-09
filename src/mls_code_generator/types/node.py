""" Node: Component that represents a node in a pipeline. """
from . pipeline import Pipeline


class Node:
    """ Node: Component that represents a node in a pipeline. """
    def __init__(self):
        self.id = None
        self.data = None
        self.dependencies = []
        self.sources = {}
        self.node_name = None
        self.parent = Pipeline()
        self.ready = []
        self.params = {}
        self.inputs = []
        self.outputs = []
        self.origin = {}
        self.origin_label = ""
        self.module_dependencies = {}
        self.variable_name = ""
    def set_data(self, data : dict):
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
        self.origin_label = ""
        if "custom" in self.origin:
            self.origin_label = self.origin["custom"]
        elif "parameter" in self.origin:
            self.origin_label = self.get_param(self.origin["parameter"])

    def set_parent(self, parent : Pipeline):
        self.parent = parent

    def add_dependency(self, dep : str , port : str, src : str, src_port : str) -> None:
        self.dependencies.append((src, src_port, dep, port))
        self.ready.append(False)
    def add_source(self, my_port : str, target, target_port : str):
        if my_port in self.sources:
            self.sources[my_port].append((target, target_port))
        else:
            self.sources[my_port] = [(target, target_port)]
    def is_ready(self) -> bool:
        for i in self.ready:
            if not i:
                return False
        return True
    def past_dependency(self, src : str, src_port : str) -> None :
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
        final_code += self.variable_name + " = " + self.origin_label + "(\n"
        for param in self.params:
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
        for dependency in self.dependencies:
            inp, inp_port, _, me_port = dependency
            if inp.node_name == "Input":
                final_code += "\t" + me_port + " = self._get_input_step('" + inp.get_param('key')+"'),\n"
            else:
                final_code += "\t" + me_port + " = (" + inp.variable_name + \
                            ", '" + inp_port + "'),\n"
        final_code += ")\n"
        return final_code
    
    def port_is_multiple(self, port):
        if port in self.sources:
            return len(self.sources[port]) > 1
        
    def is_output_multiple(self, port):
        for dep in self.dependencies:
            if dep[3] == port:
                return dep[0].port_is_multiple(dep[1])
        return None
    
    def get_dependencies(self) -> dict:
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
        return final_dependencies

    def get_parameter(self, node_id):
        if self.parent is None:
            return "'NONE'"
        parameter_node = self.parent.get_node(node_id)
        if parameter_node is None:
            return "'NONE'"

        return parameter_node.get_param("description")
