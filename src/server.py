from flask import Flask, json, request
from flask_cors import cross_origin
import os, shutil, uuid

from mls_code_generator import ConfigLoader, PipelineLoader, CodeGenerator, CodePacker
from mls_code_generator.types import Pipeline
from mls_code_generator.utils import fix_editor

app = Flask(__name__)

@app.route('/api/create_app', methods=['GET','POST'])
@cross_origin()
def create_app():
    content = request.json
    
    code_json = fix_editor(content["code"])

    node_configuration = ConfigLoader(content = content['nodes'])
    pipeline_loader = PipelineLoader(code_json, node_configuration)

    pipeline = Pipeline()
    pipeline.loadPipeline(pipeline_loader)
    
    code_generator = CodeGenerator()
    code_generator.generateCode(pipeline)

    path_head = './'+ str(uuid.uuid4())
    path = path_head + '/src/'
    os.mkdir(path_head)
    os.mkdir(path)

    code_packer = CodePacker()
    code_packer.generatePackage(
        code = code_generator.getModules(),
        write_path = path,
        mls_path = "./mls_lib/mls_lib")
    
    shutil.make_archive(path_head, 'zip', path_head)

    file = open(path_head+'.zip', 'rb')
    data = file.read()
    file.close()
    
    os.remove(path_head+'.zip')
    shutil.rmtree(path_head)

    return data

@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def home():
    return 'hello from mls_code_generator'


@app.route('/api/get_config', methods=['GET', 'POST'])
@cross_origin()
def get_config():
    node_config_path = './mls_code_generator_config/nodes.json'
    options_config_path = './mls_code_generator_config/options.json'
    socket_config_path = './mls_code_generator_config/sockets.json'

    with open(node_config_path, 'r') as file:
        node_config = json.load(file)

    with open(options_config_path, 'r') as file:
        options_config = json.load(file)

    with open(socket_config_path, 'r') as file:
        socket_config = json.load(file)

    return {
        'nodes' : node_config,
        'options' : options_config,
        'sockets' : socket_config
    }

if __name__ == '__main__':
    from waitress import serve
    from flask_cors import CORS
    CORS(app, supports_credentials=True, origins=['*'])
    app.config["CORS_HEADERS"] = ["Content-Type", "X-Requested-With", "X-CSRFToken"]
    app.run(host= '0.0.0.0', port= 5050, debug=True)
    #serve(app, host="0.0.0.0", port=5050)