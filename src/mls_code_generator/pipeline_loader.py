""" PipelineLoader: Component that loads a pipeline. """

from os import link
from .types.node import Node
from .types.step import Step
from .types.pipeline import Pipeline

class PipelineLoader:
    """ PipelineLoader: Component that loads a pipeline. """
    def __init__(self, content, node_config) -> None:
        self.content = content
        self.node_config = node_config
    def load_pipeline(self, parent : Pipeline):
        """
        Loads a pipeline from the provided content and node configuration.

        This function takes a parent pipeline and loads a new pipeline into it.
        It creates all the steps and nodes from the content, adds connections between them,
        and sets the data for each step from the parent node.
        It also injects output routes and sets the parent for each node.

        Parameters:
            parent (Pipeline): The parent pipeline to load the new pipeline into.

        Returns:
            None
        """
        
        all_steps = {}
        all_nodes = {}
        available_nodes = self.node_config
        content = self.content

        ## Creating all the steps
        for step in content:
            current_step = Step(step)
            all_steps[step] = current_step
            for node in content[step]['nodes']:
                if node['nodeName'] not in available_nodes.get_all_nodes():
                    class_node = Node()
                else:
                    class_node = available_nodes.get_node(node['nodeName']).get_copy()
                
                class_node.set_data(node)
                class_node.set_parent_step(current_step)
                current_step.add_node(class_node)
                all_nodes[class_node.id] = class_node
        

        ## Adding connections to the steps
        for step in all_steps.values():
            step_id = step.id
            for connection in content[step_id]['connections']:
                step.add_connection(
                    connection['source'],
                    connection['target'],
                    connection['sourceOutput'],
                    connection['targetInput']
                )
        
        ## Add linked steps
        for linked_steps in content['root']['nodes']:
            if linked_steps['id'] in all_steps:
                continue
            current_step = Step(linked_steps['id'])
            linked_step = all_steps[linked_steps['params']['link']['value']]
            for node in linked_step.nodes:
                current_step.add_node(node)
            all_steps[linked_steps['id']] = current_step
        
        ## Adding data to the steps from the parent node
        for step in all_steps.values():
            if step.id not in all_nodes:
                continue
            step.set_data(all_nodes[step.id].data)

        ## Inject Output routes:
        for node in all_nodes.values():
            if node.node_name == 'Output':
                node.params = {
                    "key" : node.params["key"]
                }
        ## Inject Outputs into other other step inputs:
        for connection in content['root']['connections']:
            source = connection['source']
            target = connection['target']
            source_output = connection['sourceOutput']
            target_input = connection['targetInput']
            source_step = all_steps[source]
            source_output_node = source_step.get_output_node(source_output)
            target_step = all_steps[target]
            target_step.set_input_origin(target_input, source_output_node, source_step)

        
        ## Inject inputs:
        for current_step in all_steps.values():
            for node in current_step.nodes:
                if node.node_name == 'Input':
                    continue
                else:
                    node.variable_name = node.node_name.replace(" ", "_").lower()
        
        ## Add parent to each node
        for step in all_steps.values():
            for node in step.nodes:
                node.set_parent(step)
        parent.add_steps(all_steps)
        parent.add_nodes(all_nodes)
