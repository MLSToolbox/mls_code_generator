import json
from src.mls_code_generator import ConfigLoader, PipelineLoader, CodeGenerator, CodePacker
from src.mls_code_generator.types import Pipeline

def main():
	editor_path = 'fixed_editor.json'
	nodes_config_path = './src/config/nodes.json'
	
	content_json = json.load(open(editor_path))
	nodes_config_json = json.load(open(nodes_config_path))
	
	node_configuration = ConfigLoader(content = nodes_config_json['nodes'])
	pipeline_loader = PipelineLoader(content_json, node_configuration)

	pipeline = Pipeline()
	pipeline.loadPipeline(pipeline_loader)
	
	code_generator = CodeGenerator()
	code_generator.generateCode(pipeline)

	code_packer = CodePacker()
	code_packer.generatePackage(
		code = code_generator.getModules(),
		write_path = "./output/src/",
		mls_path = "./src/mls")
	
	pass


if __name__ == '__main__':
	main()