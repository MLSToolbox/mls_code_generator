""" 
This module contains utility functions for the code generator.
"""

def fix_editor(content):
    """
    Fixes the editor content by reorganizing its modules, nodes, and connections.

    Args:
        content (dict): The editor content to be fixed.

    Returns:
        dict: The fixed editor content.
    """
    modules = content['modules']
    new_content = {}

    for module in modules:
        new_content[module] = {}
        new_module = new_content[module]
        new_module['nodes'] = []
        new_module['connections'] = []

        for node in modules[module]['nodes']:
            new_node = {}
            new_node['nodeName'] = node['nodeName']
            new_node['id'] = node['id']
            new_node['params'] = node['data']['params']
            new_content[module]['nodes'].append(new_node)

        for connection in modules[module]['connections']:
            new_content[module]['connections'].append(connection)
    return new_content
