from flask import Flask, request
from flask_cors import cross_origin
import os, shutil, uuid

from mls_code_generator import ConfigLoader, PipelineLoader, CodeGenerator, CodePacker
from mls_code_generator.types import Pipeline
from mls_code_generator.utils import fix_editor

app = Flask(__name__)

@app.route('/api/create_app', methods=['GET', 'POST'])
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
        mls_path = "./mls")
    
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
    return 'hello'

if __name__ == '__main__':
    from flask_cors import CORS
    CORS(app, supports_credentials=True, origins=['*'])
    app.run(host= '0.0.0.0',debug=True)
    app.config["CORS_HEADERS"] = ["Content-Type", "X-Requested-With", "X-CSRFToken"]