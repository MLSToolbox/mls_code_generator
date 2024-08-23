""" Local code generator """

import json
from src.mls_code_generator import ConfigLoader, PipelineLoader, CodeGenerator, CodePacker
from src.mls_code_generator.types import Pipeline

EDITOR_PATH = 'fixed_editor.json'

NODES_CONFIG_PATH = './src/mls_code_generator_config/nodes.json'

def main():
    """ 
    Main function
    """
    content_json = {}
    nodes_config_json = {}
    with open(EDITOR_PATH, 'r', encoding='utf-8') as f:
        content_json = json.load(f)
    with open(NODES_CONFIG_PATH, 'r', encoding='utf-8') as f:
        nodes_config_json = json.load(f)
    
    node_configuration = ConfigLoader(content = nodes_config_json['nodes'])
    pipeline_loader = PipelineLoader(content_json, node_configuration)

    pipeline = Pipeline()
    pipeline.load_pipeline(pipeline_loader)
    
    code_generator = CodeGenerator()
    code_generator.generate_code(pipeline)

    code_packer = CodePacker()
    code_packer.generate_package(
        code = code_generator.get_modules(),
        write_path = "./output/src/",
        mls_path = "./src/mls_lib/mls_lib/"
    )

if __name__ == '__main__':
    main()
