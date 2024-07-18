import json

def fix_editor(content):
    modules = content['modules']
    new_content = dict()

    for module in modules:
        new_content[module] = dict()
        new_module = new_content[module]
        new_module['nodes'] = list()
        new_module['connections'] = list()

        for node in modules[module]['nodes']:
            new_node = dict()
            new_node['nodeName'] = node['nodeName']
            new_node['id'] = node['id']
            new_node['params'] = node['data']['params']
            new_content[module]['nodes'].append(new_node)

        for connection in modules[module]['connections']:
            new_content[module]['connections'].append(connection)
        
    return new_content

if __name__ == '__main__':

    file_path = 'editor.json'
    out_path = 'fixed_editor.json'


    content = json.load(open(file_path))

    new_content = fix_editor(content)

    json.dump(new_content, open(out_path, 'w'), indent=4)

