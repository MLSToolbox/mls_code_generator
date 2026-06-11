""" CodeGenerator: Component that generates code. """

import os
from copy import deepcopy
import re
import yaml
import textwrap
import json
import shutil

from mls_code_generator.connection_classifier import classify_pipeline_connections, ConnectionType
from mls_code_generator.services_factory import ServicesFactory


def _create_data_tree(output_base: str, service_names: list):
    """
    Creates the shared data directory structure for the services.

    This function generates a root 'data' folder and individual subfolders for each 
    service to handle user-uploaded inputs securely.

    Parameters:
        output_base (str): The root directory where the output is generated.
        service_names (list): A list of the service names to create folders for.

    Returns:
        dict: A mapping of service names to their respective input folder names.
    """
    data_root = os.path.join(output_base, "data")
    os.makedirs(data_root, exist_ok=True)
    mapping = {}
    for svc in service_names:
        folder_name = f"inputs_{svc}"
        svc_folder = os.path.join(data_root, folder_name)
        os.makedirs(svc_folder, exist_ok=True)
        mapping[svc] = folder_name
    return mapping


def _generate_starter(output_base: str, target_container: str):
    """
    Generates the starter service responsible for orchestrating the execution.

    This function creates a Dockerfile and a Python application that waits for all 
    dependencies to be healthy before sending the initial trigger to start the pipeline.

    Parameters:
        output_base (str): The root directory where the output is generated.
        target_container (str): The name of the first container to be triggered.

    Returns:
        str: The path to the generated starter directory.
    """
    starter_dir = os.path.join(output_base, "starter")
    os.makedirs(starter_dir, exist_ok=True)

    dockerfile_content = """FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY app.py .
RUN pip install --no-cache-dir requests
CMD ["python", "app.py"]
"""
    with open(os.path.join(starter_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write(dockerfile_content)

    app_code = """import os
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_dependencies(deps):
    logger.info(f"Waiting for dependencies: {deps}")
    for dep in deps:
        ready = False
        notified = False
        while not ready:
            try:
                resp = requests.get(f"http://{dep}:5000/health", timeout=2)
                if resp.status_code == 200:
                    logger.info(f"Dependency healthy: {dep}")
                    ready = True
                else:
                    time.sleep(2)
            except Exception:
                if not notified:
                    logger.info(f"Waiting for {dep} to become reachable...")
                    notified = True
                time.sleep(2)

if __name__ == '__main__':
    target = os.environ.get("TARGET_URL")
    deps_str = os.environ.get("DEPENDENCIES", "")
    deps = [d.strip() for d in deps_str.split(",") if d.strip()]
    if deps:
        wait_for_dependencies(deps)
    
    if target:
        logger.info(f"Posting trigger to target: {target}")
        try:
            resp = requests.post(target, json={}, timeout=30)
            if 200 <= resp.status_code < 300:
                logger.info(f"Starter: Trigger sent successfully (Status: {resp.status_code}).")
            else:
                logger.error(f"Starter: Trigger returned an error (Status: {resp.status_code}).")
        except Exception as e:
            logger.error(f"Starter: Trigger failed with exception: {e}")
"""
    with open(os.path.join(starter_dir, "app.py"), "w", encoding="utf-8") as f:
        f.write(app_code)
    return starter_dir


def _write_compose_with_isolated_volumes(output_base: str, sanitized_map: dict, service_deps: dict, starter_target_container: str = None):
    """
    Generates the docker-compose file for the services architecture.

    This function configures the services, networks, health checks, and shared volume 
    mounts required to establish the choreography between containers.

    Parameters:
        output_base (str): The root directory where the output is generated.
        sanitized_map (dict): A mapping of original service names to Docker-safe names.
        service_deps (dict): A dictionary defining the dependencies between services.
        starter_target_container (str): The name of the target container for the starter.

    Returns:
        str: The file path to the generated docker-compose.yml.
    """
    compose = {"services": {}, "networks": {"ml_network": {"driver": "bridge"}}}

    for svc_name, service_key in sanitized_map.items():
        svc_entry = {
            "build": f"./{svc_name}",
            "environment": ["PORT=5000"],
            "networks": ["ml_network"],
            "restart": "unless-stopped"
        }

        vol_app = f"./{svc_name}:/app"
        vol_data = "./data:/data"
        svc_entry["volumes"] = [vol_app, vol_data]

        deps = sorted(service_deps.get(svc_name, []))
        if deps:
            svc_entry["depends_on"] = [sanitized_map[d] for d in deps if d in sanitized_map]

        svc_entry["healthcheck"] = {
            "test": ["CMD-SHELL", "exit 0"],
            "interval": "5s",
            "timeout": "3s",
            "retries": 1,
            "start_period": "1s"
        }

        compose["services"][service_key] = svc_entry

    if starter_target_container:
        deps_list = ",".join([sanitized_map[s] for s in sanitized_map.keys() if s in sanitized_map])
        starter_entry = {
            "build": "./starter",
            "networks": ["ml_network"],
            "environment": [
                f"TARGET_URL=http://{starter_target_container}:5000/execute",
                f"DEPENDENCIES={deps_list}"
            ],
            "restart": "no",
            "volumes": ["./data:/data"],
            "depends_on": {starter_target_container: {"condition": "service_healthy"}}
        }
        compose["services"]["starter"] = starter_entry

    compose_file = os.path.join(output_base, "docker-compose.yml")
    yaml_str = yaml.safe_dump(compose, sort_keys=False)

    base_port = 5000
    for original_name, safe_name in sanitized_map.items():
        search_str = f"  {safe_name}:\n"
        
        comment_block = (
            f"  {safe_name}:\n"
            f"    # Uncomment the following lines to expose the service to your host machine (e.g., for Swagger/Postman)\n"
            f"    # ports:\n"
            f"    #   - \"{base_port}:5000\"\n"
        )
        
        yaml_str = yaml_str.replace(search_str, comment_block)
        base_port += 1

    with open(compose_file, "w", encoding="utf-8") as cf:
        cf.write(yaml_str)
        
    return compose_file


class CodeGenerator:
    """ CodeGenerator component. """

    def __init__(self):
        self.modules = {}
        self.params = {}
        self.connections = None
        self.output_dir = None

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

                for p in node.sources:
                    for target, target_port in node.sources[p]:
                        target.past_dependency(target, target_port)
                break

        code += "\troot.execute()\n"
        code += "\nif __name__ == '__main__':\n\tmain()"

        self.modules["main"] = code

    def __generate_service_code(self, pipeline):
        """
        Generates the codebase for all defined services in the pipeline.

        This function creates individual service directories, assigns pipeline steps to 
        them, resolves network dependencies, and prepares the execution scripts for Docker.

        Parameters:
            pipeline (Pipeline): The pipeline instance containing the topology and services.

        Returns:
            None
        """
        def _step_id_of(obj):
            if hasattr(obj, "id"):
                return getattr(obj, "id")
            return str(obj)

        def _sanitize_container_name(name: str, maxlen: int = 10) -> str:
            s = name.lower()
            s = re.sub(r'[^a-z0-9\-_]', '_', s)
            if len(s) > maxlen:
                s = s[:maxlen]
            return s

        conn_lookup = {}
        if self.connections:
            for c in self.connections:
                key = (c.source_step_id, c.target_step_id, c.target_port)
                conn_lookup[key] = c

        step_to_service = {}
        for svc_id, svc in pipeline.services.items():
            steps_in_service = getattr(svc, "steps", [])
            for st in steps_in_service:
                sid = _step_id_of(st)
                step_to_service[sid] = getattr(svc, "service_id", svc_id)

        service_deps = { getattr(svc, "service_id", svc_id): set() for svc_id, svc in pipeline.services.items() }

        if self.connections:
            for c in self.connections:
                src_step = c.source_step_id
                tgt_step = c.target_step_id
                src_svc = step_to_service.get(src_step)
                tgt_svc = step_to_service.get(tgt_step)
                if src_svc and tgt_svc and src_svc != tgt_svc:
                    service_deps[tgt_svc].add(src_svc)

        used_containers = {}
        def _unique_sanitized(name):
            base = _sanitize_container_name(name)
            candidate = base
            i = 1
            while candidate in used_containers.values():
                candidate = f"{base}_{i}"
                i += 1
            used_containers[name] = candidate
            return candidate

        service_needs_data = {}
        service_referenced_files = {}
        service_output_paths = {}

        self._service_meta = {}

        for svc_id, svc in pipeline.services.items():
            svc_name = getattr(svc, "service_id", svc_id)

            if svc_name == "monolith":
                continue

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
                        pre_lines.append(f"\t{placeholder}_stage = _ExternalSource({placeholder}_payload)")
                        arg_items.append(f"\t\t{me_port} = ({placeholder}_stage, '{inp_port}'),")
                        service_referenced_files.setdefault(svc_name, set()).add(inp_port)

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
            code += "\troot.execute()\n\n"

            code += "\t# gather outputs declared by external connections\n"
            code += "\toutputs = {}\n"
            for step in steps_in_service:
                step_name = getattr(step, "name", "") or getattr(step, "r_name", "")
                if not step_name:
                    continue
                
                outgoing_conns = getattr(step, "external_outgoing", [])
                for conn in outgoing_conns:
                    out_key = conn.target_port
                    port_name = conn.source_port
                    
                    code += f"\ttry:\n"
                    code += f"\t\t_val = {step_name}.get_stage_output('{port_name}')\n"
                    code += f"\t\toutputs['{out_key}'] = _val\n"
                    code += f"\texcept Exception as e:\n"
                    code += f"\t\tprint(f'ERROR CRITIC LLEGINT OUTPUT {out_key}: {{e}}', flush=True)\n"
                    code += f"\t\toutputs['{out_key}'] = None\n\n"

            code += "\t# return collected outputs to caller\n"
            code += "\treturn outputs\n\n"

            code += "if __name__ == '__main__':\n"
            code += f"\tprint('Running service', '{svc_name}')\n"
            code += "\texecute_service({})\n"

            module_key = f"service_{svc_name}_main"
            self.modules[module_key] = code

            output_base = getattr(self, "output_dir", None)
            if output_base:
                service_output = os.path.join(output_base, str(svc_name))
                os.makedirs(service_output, exist_ok=True)

                module_file = os.path.join(service_output, f"{module_key}.py")
                with open(module_file, "w", encoding="utf-8") as mf:
                    mf.write(code)

                for step in steps_in_service:
                    if hasattr(step, "params") and "link" in step.params and step.params["link"]["value"] != "":
                        continue
                    if getattr(step, "id", "") == "root":
                        continue
                    step_name = getattr(step, "name", "") or getattr(step, "r_name", "")
                    if not step_name:
                        continue
                    module_code = self.modules.get(step_name)
                    if module_code:
                        step_module_path = os.path.join(service_output, f"{step_name}.py")
                        with open(step_module_path, "w", encoding="utf-8") as sf:
                            sf.write(module_code.replace("\t", "    "))
                        if re.search(r'\bmls_lib\.data_collection\b', module_code) \
                           or 'data_collection' in module_code \
                           or any(x in module_code for x in ("csv_loader", "excel_loader", "json_loader", "pickle_loader")):
                            service_needs_data[svc_name] = True

                adapter = ServicesFactory.get_instance().get_service_adapter("flask")
                adapter.generate_service_code(svc, service_output)

                service_output_paths[svc_name] = service_output
                self._service_meta[svc_name] = {
                    "output_path": service_output,
                    "needs_data": service_needs_data.get(svc_name, False),
                    "referenced_files": sorted(list(service_referenced_files.get(svc_name, [])))
                }

        output_base = getattr(self, "output_dir", None)
        if output_base:
            sanitized_map = {}
            for svc_id, svc in pipeline.services.items():
                svc_name = getattr(svc, "service_id", svc_id)
                if svc_name == "monolith":
                    continue
                cont_name = _unique_sanitized(svc_name)
                sanitized_map[svc_name] = cont_name

            readonly_flags = {svc: False for svc in sanitized_map.keys()}

            target_service = None
            for svc in sorted(sanitized_map.keys()):
                if not service_deps.get(svc):
                    target_service = svc
                    break
            if target_service is None and len(sanitized_map) > 0:
                target_service = sorted(sanitized_map.keys())[0]

            starter_target_container = sanitized_map.get(target_service)
            if starter_target_container:
                _generate_starter(output_base, starter_target_container)

            for svc, out_path in service_output_paths.items():
                expected = sorted(list(service_referenced_files.get(svc, [])))
                if expected:
                    with open(os.path.join(out_path, "expected_inputs.json"), "w", encoding="utf-8") as ef:
                        json.dump({"expected_inputs": expected}, ef)


            reverse_deps = {svc: [] for svc in sanitized_map.keys()}
            for target, sources in service_deps.items():
                for src in sources:
                    if src in reverse_deps:
                        reverse_deps[src].append(target)

            for svc_name, children in reverse_deps.items():
                sanitized_children = [sanitized_map[c] for c in sorted(children) if c in sanitized_map]
                out_path = service_output_paths.get(svc_name)
                if out_path:
                    with open(os.path.join(out_path, "downstream.json"), "w", encoding="utf-8") as df:
                        json.dump({"children": sanitized_children}, df)


            _write_compose_with_isolated_volumes(
                output_base,
                sanitized_map,
                service_deps,
                starter_target_container=starter_target_container
            )

    def __get_params_file(self, pipeline):
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
