""" CodeGenerator: Component that generates code. """

from copy import deepcopy

from mls_code_generator.connection_classifier import classify_pipeline_connections, ConnectionType

class CodeGenerator:
    """ CodeGenerator: Component that generates code. """
    def __init__(self):
        self.modules = {}
        self.params = {}
        self.connections = None

    def __generate_stage_code(self, pipeline):
        """
        Generates code for a step in a pipeline.

        This function takes a pipeline as input, generates code for each step in the pipeline,
        and stores the generated code in the self.modules dictionary.

        Parameters:
            pipeline (Pipeline): The pipeline for which to generate code.

        Returns:
            None
        """
        root = pipeline.get_step('root')
        steps = root.nodes

        for step in steps:
            
            if "link" in step.params and step.params["link"]["value"] != "":
                continue
            this_step_node = pipeline.get_node(step.id)
            steps_name_i_depend_on = set()
            count_steps = {}
            for source in this_step_node.dependencies:
                dep_name = source[-1]
                if dep_name not in count_steps:
                    count_steps[dep_name] = 1
                else:
                    count_steps[dep_name] += 1
                if count_steps[dep_name] > 1:
                    steps_name_i_depend_on.add(dep_name + "_" + str(count_steps[dep_name]))
                else:
                    steps_name_i_depend_on.add(dep_name)

            c_step = pipeline.get_step(step.id)

            code = ""
            code += '""" ' + c_step.name + '.py """\n\n'
            code += c_step.get_dependencies_code()
            code += "\n"
            code += "def create_" + c_step.name +"():\n"
            code += "\t" + c_step.r_name + " =  Stage('" + c_step.original_name +  "')\n\n"

            for j in c_step.generate_code().split("\n")[:-1]:
                code += "\t" + j + "\n"
            
            for j in c_step.get_output_code().split("\n"):
                code += "\t" + j + "\n"
            
            code += "\treturn " + c_step.r_name + "\n\n"

            self.modules[c_step.name] = code

    def __generate_main_code(self, pipeline):
        """
        Generates the main code for the given pipeline.
        
        This function takes a pipeline as input, extracts its steps, and generates the main 
        code by importing the necessary modules, 
        defining the main function, and adding the steps to the orchestrator.
        
        Parameters:
            pipeline (Pipeline): The pipeline for which the main code is to be generated.
        
        Returns:
            None
        """
        root = pipeline.get_step('root')
        steps = root.nodes
        code  = "import warnings\n"
        code += "warnings.filterwarnings('ignore')\n\n"
        code += "from mls_lib.orchestration import Pipeline\n"


        for step in steps:
            c_step = pipeline.get_step(step.id)
            # Linked stages do not need new modules
            if "link" in step.params and step.params["link"]["value"] != "":
                continue
            code += "from " + c_step.name + " import create_" + c_step.name + "\n"

        code += "\n"
        code += "def main():\n"
        code += "\troot = Pipeline()\n"

        copy_nodes = steps.copy()
        node_dependencies = []
        appearence_count = {}
        while len(copy_nodes) > 0:
            for node in copy_nodes:
                if not node.is_ready():
                    continue
                try:
                    c_step = pipeline.get_step(node.id)
                except ValueError:
                    the_step_i_want = ""
                    for temp in steps:
                        if temp.id == node.id:
                            the_step_i_want = temp.params["link"]["value"]
                    c_step = pipeline.get_step(the_step_i_want)
                original_c_step_name = c_step.name
                if c_step.name in appearence_count:
                    appearence_count[c_step.name] += 1
                else:
                    appearence_count[c_step.name] = 1
                if appearence_count[c_step.name] > 1:
                    c_step.name = c_step.name + "_" + str(appearence_count[c_step.name])
                
                variable_name = c_step.name
                
                code += "\t" + variable_name + " = create_" + original_c_step_name + "()\n"
                code += "\troot.add_stage(" + variable_name + ", \n"
                for dependency in c_step.dependencies:
                    inp, inp_port, me_port = dependency
                    code += "\t\t" + me_port + " = (" + inp.name + ", '" + inp_port + "'),\n"
                code += "\t)\n"
                node_dependencies.append(variable_name)
                code += "\n"
                copy_nodes.remove(node)

                # Update next nodes so they now they can be added to the code now
                for p in node.sources:
                    for target, target_port in node.sources[p]:
                        target.past_dependency(target, target_port)
                break

        code += "\troot.execute()\n"
        code += "\nif __name__ == '__main__':\n\tmain()"

        self.modules["main"] = code

    def __generate_service_code(self, pipeline):
        """
        Generates a service main file for each service in the pipeline. 

        This function iterates over `pipeline.services` and, for each Service,
        composes the source of a standalone module named `service_<service_id>_main.py`.
        Each generated module includes the minimal imports required to construct the
        service's stages, a `main()` function that instantiates those stages and wires
        them into a local `Pipeline()` instance, and the final invocation that executes
        the local pipeline. The generated source is stored in `self.modules` so that a
        subsequent packaging step can write the modules to disk.
    
        Parameters:
            pipeline (Pipeline): The pipeline for which per-service mains are generated.

        Returns:
            None        
        """
        def _step_id_of(obj):
            if hasattr(obj, "id"):
                return getattr(obj, "id")
            return str(obj)

        conn_lookup = {}
        if self.connections:
            for c in self.connections:
                key = (c.source_step_id, c.target_step_id, c.target_port)
                conn_lookup[key] = c

        for svc_id, svc in pipeline.services.items():
            steps_in_service = getattr(svc, "steps", [])
            svc_step_ids = {_step_id_of(s) for s in steps_in_service}

        create_lines = []
        for step in steps_in_service:
            if hasattr(step, "params") and "link" in step.params and step.params["link"]["value"] != "":
                continue
            create_lines.append(f"from {step.name} import create_{step.name}")

        code = ""
        code += f'""" service_{svc_id}_main.py """\n\n'
        code += "import warnings\n"
        code += "warnings.filterwarnings('ignore')\n\n"
        code += "from mls_lib.orchestration import Pipeline\n"
        for line in sorted(set(create_lines)):
            code += line + "\n"
        code += "\n"
        code += "def main():\n"
        code += "\troot = Pipeline()\n\n"

        for step in steps_in_service:
            c_step = step
            if hasattr(c_step, "params") and "link" in c_step.params and c_step.params["link"]["value"] != "":
                continue
            code += f"\t{c_step.name} = create_{c_step.name}()\n"
        code += "\n"

        for step in steps_in_service:
            c_step = step
            if hasattr(c_step, "params") and "link" in c_step.params and c_step.params["link"]["value"] != "":
                continue
            code += f"\troot.add_stage({c_step.name}, \n"
            for dependency in c_step.dependencies:
                inp_obj, inp_port, me_port = dependency
                src_id = _step_id_of(inp_obj)
                target_id = _step_id_of(c_step)

                conn_info = conn_lookup.get((src_id, target_id, me_port))
                if conn_info is not None:
                    is_internal = (conn_info.conn_type is ConnectionType.INTERNAL)    
                else:
                    is_internal = (src_id in svc_step_ids)

                if is_internal:
                    src_name = getattr(inp_obj, "name", str(src_id))
                    code += f"\t\t{me_port} = ({src_name}, '{inp_port}'),\n"
                else:
                    #TODO
                    placeholder = f"external_{src_id}_to_{c_step.name}"
                    code += f"\t\t# TODO (IB5/IB6): Inject REST adapter and deserialize into '{placeholder}'\n"
                    code += f"\t\t{me_port} = ({placeholder}, '{inp_port}'),\n"
            code += "\t)\n\n"

        code += "\troot.execute()\n"
        code += "\nif __name__ == '__main__':\n"
        code += "\tmain()\n"
        module_key = f"service_{svc_id}_main"
        self.modules[module_key] = code       

    def __get_params_file(self, pipeline):
        """
        Generates the code for the parameters file.

        This function takes a pipeline as input, 
        and generates the code for the parameters file.

        Parameters:
            pipeline (Pipeline): The pipeline for which the parameters file is to be generated.

        Returns:
            None
        """
        root = pipeline.get_step('root')
        steps = root.nodes
        
        self.params = {}


        for step in steps:
            try:
                c_step = pipeline.get_step(step.id)
                node_params = {}
                for node in c_step.nodes:
                    label_params = node.get_label_params()
                    for j in label_params:
                        node_params.update(j)
                if len(node_params.keys()) > 0:
                    self.params[c_step.name] = node_params
            except ValueError:
                continue
        
    def generate_code(self, pipeline):
        """
        Generates code for a given pipeline.

        This function takes a pipeline as input, generates code for each step in the pipeline,
        and generates the main code that orchestrates the steps. It classifies pipeline
        connections before generation and supports two generation modes: 'services' and 'monolith'.
        When the mode is 'services' it generates one service-specific module per Service;
        otherwise it generates a single orchestrator module that instantiates and executes
        all stages together.

        Parameters:
            pipeline (Pipeline): The pipeline for which to generate code.

        Returns:
            None
        """
        self.connections = classify_pipeline_connections(pipeline)
        self.__generate_stage_code(pipeline)
        mode = getattr(pipeline, "generation_mode", "monolith")
        if mode == "services":
            self.__generate_service_code(pipeline)
        else:
            self.__generate_main_code(pipeline)
        self.__get_params_file(pipeline)

    def get_modules(self):
        """
        Returns a deep copy of the modules dictionary.
        
        Parameters:
            None
        
        Returns:
            dict: A deep copy of the modules dictionary.
        """
        return deepcopy(self.modules)
    def get_params(self):
        """
        Returns a deep copy of the params dictionary.
        
        Parameters:
            None
        
        Returns:
            dict: A deep copy of the params dictionary.
        """
        return deepcopy(self.params)
