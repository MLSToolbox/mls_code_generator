""" CodeGenerator: Component that generates code. """

from copy import deepcopy

class CodeGenerator:
    """ CodeGenerator: Component that generates code. """
    def __init__(self):
        self.modules = {}
    def __generate_step_code(self, pipeline):
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
            c_step = pipeline.get_step(step.id)

            code = c_step.get_dependencies_code()
            code += "\n"
            code += "class " + c_step.r_name +"(Step):\n"
            code += "\tdef __init__(self, **inputs):\n"
            code += "\t\tsuper().__init__(**inputs)\n"
            code += "\t\tself.orchestrator = Orchestrator()\n"

            for j in c_step.generate_code().split("\n"):
                code += "\t\t" + j + "\n"

            code += "\tdef execute(self):\n"
            code += "\t\tself.orchestrator.execute()\n"

            for j in c_step.get_output_code().split("\n"):
                code += "\t\t" + j + "\n"

            code += "\n\t\tself.finishExecution()"

            self.modules[c_step.r_name] = code
            this_step_node = pipeline.get_node(step.id)
            steps_id_i_depend_on = set()
            for source in this_step_node.dependencies:
                steps_id_i_depend_on.add(source[0].id)

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
        code = "from mls_lib.orchestration import Orchestrator\n"


        for step in steps:
            c_step = pipeline.get_step(step.id)
            code += "from " + c_step.r_name + " import " + c_step.r_name + "\n"

        code += "\n"
        code += "def main():\n"
        code += "\troot = Orchestrator()\n"

        copy_nodes = steps.copy()
        node_dependencies = []
        while len(copy_nodes) > 0:
            for node in copy_nodes:
                c_step = pipeline.get_step(node.id)
                if not node.is_ready():
                    continue
                variable_name = c_step.name
                node.variable_name = variable_name
                node.origin_label = c_step.r_name
                node.params = {}
                code += "\t" + "\n\t".join(node.generate_code().split("\n"))
                code += "root.add(" + "'" + variable_name + "', " + variable_name + ")\n"
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

    def generate_code(self, pipeline):
        """
        Generates code for a given pipeline.

        This function takes a pipeline as input, generates code for each step in the pipeline,
        and generates the main code that orchestrates the steps.

        Parameters:
            pipeline (Pipeline): The pipeline for which to generate code.

        Returns:
            None
        """
        self.__generate_step_code(pipeline)
        self.__generate_main_code(pipeline)
    def get_modules(self):
        """
        Returns a deep copy of the modules dictionary.
        
        Parameters:
            None
        
        Returns:
            dict: A deep copy of the modules dictionary.
        """
        return deepcopy(self.modules)
