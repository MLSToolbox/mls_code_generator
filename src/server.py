""" server.py: Server for the mls_code_generator. """

import os
import shutil
import uuid

from flask import Flask, json, request
from flask_cors import cross_origin, CORS
from waitress import serve

from mls_code_generator.configuration_loader import ConfigLoader
from mls_code_generator.code_generator import CodeGenerator
from mls_code_generator.code_packer import CodePacker
from mls_code_generator.pipeline_loader import PipelineLoader
from mls_code_generator.types import Pipeline
from mls_code_generator.utils import fix_editor

app = Flask(__name__)

@app.route('/api/create_app', methods=['GET','POST'])
@cross_origin()
def create_app():
    """
    Creates a new application by generating code from the provided configuration.

    This function takes a JSON payload containing the application configuration and code,
    generates the necessary code files, packages them into a ZIP archive, and returns the archive.

    Parameters:
        content (dict): A dictionary containing the application configuration and code.

    Returns:
        bytes: The ZIP archive containing the generated code files.
    """
    content = request.json
    code_json = fix_editor(content["code"])

    node_configuration = ConfigLoader(content = content['nodes'])
    pipeline_loader = PipelineLoader(code_json, node_configuration)

    pipeline = Pipeline()
    pipeline.load_pipeline(pipeline_loader)
    code_generator = CodeGenerator()
    code_generator.generate_code(pipeline)

    path_head = './'+ str(uuid.uuid4())
    path = path_head + '/src/'
    os.mkdir(path_head)
    os.mkdir(path)

    code_packer = CodePacker()
    code_packer.generate_package(
        code = code_generator.get_modules(),
        params = code_generator.get_params(),
        write_path = path,
        mls_path = "./mls_lib/mls_lib/"
    )
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
    """
    Handles HTTP requests to the root URL ('/').

    Parameters:
        None

    Returns:
        str: A greeting message from the mls_code_generator application.
    """
    return 'hello from mls_code_generator'


@app.route('/api/get_config', methods=['GET', 'POST'])
@cross_origin()
def get_config():
    """
    Handles HTTP requests to retrieve the configuration for the mls_code_generator application.

    This function loads the configuration from three JSON files:
    nodes.json, options.json, and sockets.json.
    It returns a dictionary containing the loaded configurations.

    Parameters:
        None

    Returns:
        dict: A dictionary containing the node, option, and socket configurations.
    """
    node_config_path = './mls_code_generator_config/nodes.json'
    options_config_path = './mls_code_generator_config/options.json'
    socket_config_path = './mls_code_generator_config/sockets.json'

    with open(node_config_path, 'r', encoding='utf-8') as file:
        node_config = json.load(file)

    with open(options_config_path, 'r', encoding='utf-8') as file:
        options_config = json.load(file)

    with open(socket_config_path, 'r', encoding='utf-8') as file:
        socket_config = json.load(file)

    return {
        'nodes' : node_config,
        'options' : options_config,
        'sockets' : socket_config
    }


@app.route('/api/get_base_editor', methods=['GET', 'POST'])
@cross_origin()
def get_base_editor():
    path_to_editors = "./mls_code_generator_config/templates/"
    return json.load(open(path_to_editors + "base_editor.json", 'r', encoding='utf-8'))

@app.route('/api/get_editor', methods=['GET', 'POST'])
@cross_origin()
def get_editor():
    path_to_editors = "./mls_code_generator_config/templates/"
    editor_path = str(request.data.decode('utf-8'))
    print(editor_path)
    return json.load(open(path_to_editors + editor_path, 'r', encoding='utf-8'))

@app.route('/api/get_available_editor', methods=['GET', 'POST'])
@cross_origin()
def get_available_editor():
    path_to_editors = "./mls_code_generator_config/templates/"
    return json.load(open(path_to_editors + "available_editors.json", 'r', encoding='utf-8'))

if __name__ == '__main__':
    CORS(app, supports_credentials=True, origins=['*'])
    app.config["CORS_HEADERS"] = ["Content-Type", "X-Requested-With", "X-CSRFToken"]

    execution_mode = os.getenv("EXECUTION_MODE", "debug")

    HOST = '0.0.0.0'
    PORT = 5050

    if execution_mode == "prod":
        serve(app, host = HOST, port = PORT )
    else:
        app.run(host = HOST, port = PORT, debug = True)
