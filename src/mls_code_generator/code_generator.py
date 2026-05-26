""" CodeGenerator: Component that generates code. """

import os
from copy import deepcopy

from mls_code_generator.connection_classifier import classify_pipeline_connections, ConnectionType
from mls_code_generator.services_factory import ServicesFactory

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
            svc_name = getattr(svc, "service_id", svc_id)

            steps_in_service = getattr(svc, "steps", [])
            svc_step_ids = {_step_id_of(s) for s in steps_in_service}

            create_lines = []
            for step in steps_in_service:
                if hasattr(step, "params") and "link" in step.params and step.params["link"]["value"] != "":
                    continue
                if getattr(step, "id", "") == "root":
                    continue
                step_name = getattr(step, "name", "") or getattr(step, "r_name", "")
                if not step_name:
                    continue
                create_lines.append(f"from {step_name} import create_{step_name}")

            code = ""
            code += f'""" service_{svc_name}_main.py """\n\n'
            code += "import warnings\n"
            code += "warnings.filterwarnings('ignore')\n\n"
            code += "from mls_lib.orchestration import Pipeline\n"
            code += "from dto_pipeline_data import DTOPipelineData\n"
            for line in sorted(set(create_lines)):
                code += line + "\n"

            code += "\n"
            code += "class _ExternalSource:\n"
            code += "\tdef __init__(self, data):\n"
            code += "\t\tself._data = data\n\n"
            code += "\tdef is_finished(self):\n"
            code += "\t\treturn True\n\n"
            code += "\tdef get_stage_output(self, port):\n"
            code += "\t\treturn self._data\n\n"

            code += "def execute_service(inputs: dict):\n"
            code += "\troot = Pipeline()\n\n"

            for step in steps_in_service:
                c_step = step
                if hasattr(c_step, "params") and "link" in c_step.params and c_step.params["link"]["value"] != "":
                    continue
                if getattr(c_step, "id", "") == "root":
                    continue
                step_name = getattr(c_step, "name", "") or getattr(c_step, "r_name", "")
                if not step_name:
                    continue
                code += f"\t{step_name} = create_{step_name}()\n"
            code += "\n"

            for step in steps_in_service:
                c_step = step
                if hasattr(c_step, "params") and "link" in c_step.params and c_step.params["link"]["value"] != "":
                    continue
                step_name = getattr(c_step, "name", None)
                var_name = step_name if step_name else getattr(c_step, "r_name", None)
                if not var_name:
                    continue

                pre_lines = []
                arg_items = []

                for dependency in c_step.dependencies:
                    inp_obj, inp_port, me_port = dependency
                    src_id = _step_id_of(inp_obj)

                    conn_info = conn_lookup.get((src_id, _step_id_of(c_step), me_port))
                    if conn_info is not None:
                        is_internal = (conn_info.conn_type is ConnectionType.INTERNAL)
                    else:
                        is_internal = (src_id in svc_step_ids)

                    if is_internal:
                        src_name = getattr(inp_obj, "name", str(src_id))
                        arg_items.append(f"\t\t{me_port} = ({src_name}, '{inp_port}'),")
                    else:
                        placeholder = f"external_{src_id}_to_{c_step.name}_{inp_port}"
                        pre_lines.append(f"\t{placeholder}_payload = inputs.get('{inp_port}')")
                        pre_lines.append(f"\tif {placeholder}_payload:")
                        pre_lines.append(f"\t\t{placeholder} = DTOPipelineData.deserialize({placeholder}_payload)")
                        pre_lines.append(f"\telse:")
                        pre_lines.append(f"\t\t{placeholder} = None")
                        pre_lines.append(f"\t{placeholder}_stage = _ExternalSource({placeholder})")
                        arg_items.append(f"\t\t{me_port} = ({placeholder}_stage, '{inp_port}'),")

                if pre_lines:
                    for pl in pre_lines:
                        code += pl + "\n"

                if arg_items:
                    code += f"\troot.add_stage({c_step.name}, \n"
                    for ai in arg_items:
                        code += ai + "\n"
                    code += "\t)\n\n"
                else:
                    code += f"\troot.add_stage({c_step.name})\n\n"

            code += "\t# execute the local pipeline\n"
            code += "\troot.execute()\n"
            code += "\treturn {}\n\n"

            code += "if __name__ == '__main__':\n"
            code += f"\tprint('Running service', '{svc_name}')\n"
            code += "\texecute_service({})\n"

            module_key = f"service_{svc_name}_main"
            self.modules[module_key] = code

            output_base = getattr(self, "output_dir", None)
            if output_base:
                service_output = os.path.join(output_base, "services", str(svc_name))
                os.makedirs(service_output, exist_ok=True)
                module_file = os.path.join(service_output, f"{module_key}.py")
                content = code
                with open(module_file, "w", encoding="utf-8") as mf:
                    mf.write(content)
                adapter = ServicesFactory.get_instance().get_service_adapter("flask")
                adapter.generate_service_code(svc, service_output)

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
