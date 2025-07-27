import pytest
import json
from ..types import Step
from ..types import Pipeline
from ..pipeline_loader import PipelineLoader
from ..configuration_loader import ConfigLoader
@pytest.fixture
def steps() -> dict:
    with open("./tests/files/mls_editor_fixed.json", "r", encoding="utf-8") as file:
        code = json.load(file)
        return code

@pytest.fixture
def step() -> Step:
    return Step("")


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

@pytest.fixture
def ready_step(ready_pipeline) -> Step:
    return ready_pipeline.get_step("0c7788842ca589f9")


def test_empty_step(step: Step):
    assert step.id == ""
    assert step.nodes == []
    assert step.data == ""
    assert step.original_name == ""
    assert step.name == ""
    assert step.r_name == ""
    assert step.outs == []
    assert step.variable_name == ""
    assert step.dependencies == []

def test_loaded_step(ready_step : Step):
    assert ready_step.id == "0c7788842ca589f9"
    assert str(ready_step.nodes) == "[Input, Output, Output, Label Encoder train, Select Columns, Select Columns]"
    assert ready_step.data == {'nodeName': 'Step', 'id': '0c7788842ca589f9', 'params': {'Stage name': {'type': 'description', 'value': 'Feature Engineering'}, 'color': {'type': 'color', 'value': 'rgba(255, 99, 132, 0.75)'}, 'link': {'type': 'link', 'value': ''}}}
    assert ready_step.original_name == "Feature Engineering"

def test_generate_code(ready_step: Step):
    with open("./tests/files/step_code.txt", "r", encoding="utf-8") as file:
        expected_code = file.read()
    assert ready_step.generate_code() == expected_code

def test_generate_main_code(ready_step: Step):
    with open("./tests/files/step_main_code.txt", "r", encoding="utf-8") as file:
        expected_code = file.read()
    assert ready_step.generate_main_code() == expected_code

def test_generate_dependencies_code(ready_step: Step):
    with open("./tests/files/step_dependencies_code.txt", "r", encoding="utf-8") as file:
        expected_code = file.read()
    assert ready_step.get_dependencies_code() == expected_code