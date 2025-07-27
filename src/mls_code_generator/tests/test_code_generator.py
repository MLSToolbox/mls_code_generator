import pytest
from ..code_generator import CodeGenerator
from ..pipeline_loader import PipelineLoader
from ..configuration_loader import ConfigLoader
from ..types import Pipeline
import json
import os

"""
content = request.json
code_json = fix_editor(content["code"])

node_configuration = ConfigLoader(content=content["nodes"])
pipeline_loader = PipelineLoader(code_json, node_configuration)

pipeline = Pipeline()
pipeline.load_pipeline(pipeline_loader)
code_generator = CodeGenerator()
code_generator.generate_code(pipeline)
"""

@pytest.fixture
def pipeline() -> Pipeline:
    return Pipeline()

@pytest.fixture
def ready_pipeline_loader() -> PipelineLoader:
    with open("./tests/files/nodes.json", "r", encoding="utf-8") as file:
        nodes = json.load(file)["nodes"]
    with open("./tests/files/mls_editor_fixed.json", "r", encoding="utf-8") as file:
        code = json.load(file)

    node_configuration = ConfigLoader(content=nodes)
    pipeline_loader = PipelineLoader(code, node_configuration)

    return pipeline_loader

@pytest.fixture
def ready_pipeline(pipeline: Pipeline, ready_pipeline_loader) -> Pipeline:
    pipeline.load_pipeline(ready_pipeline_loader)
    return pipeline

def test_empty_code_generator():
    code_generator = CodeGenerator()
    assert code_generator.modules == {}
    assert code_generator.params == {}

def test_generate_code(ready_pipeline: Pipeline):
    code_generator = CodeGenerator()
    code_generator.generate_code(ready_pipeline)

    assert code_generator.modules != {}
    assert code_generator.params != {}

    with open("./tests/files/modules.json", "r") as file:
        expected_modules = json.load(file)
        assert expected_modules == code_generator.modules
    
    with open("./tests/files/params.json", "r", encoding="utf-8") as file:
        excepted_params = json.load(file)
        assert excepted_params == code_generator.params