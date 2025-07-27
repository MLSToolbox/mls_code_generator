import pytest
import json
from unittest.mock import Mock
from ..types import Pipeline
from ..pipeline_loader import PipelineLoader
from ..configuration_loader import ConfigLoader

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
def ready_pipeline(pipeline, ready_pipeline_loader) -> Pipeline:
    pipeline.load_pipeline(ready_pipeline_loader)
    return pipeline

def test_create_pipeline(pipeline: Pipeline):
    """        self.nodes = {}
        self.steps = {}
        self.pipeline_id = """""
    
    assert pipeline.nodes == {}
    assert pipeline.steps == {}
    assert pipeline.pipeline_id == ""
def test_mock_load_pipeline(pipeline: Pipeline):
    m = Mock(spec=["load_pipeline"])
    pipeline.load_pipeline(m)
    m.load_pipeline.assert_called_once()

def test_load_pipeline(ready_pipeline_loader: PipelineLoader, pipeline: Pipeline):
    with pytest.raises(ValueError):
        pipeline.get_node("test")

    with pytest.raises(ValueError):
        pipeline.get_step("test")

    pipeline.load_pipeline(ready_pipeline_loader)

    assert True

def test_get_node(ready_pipeline: Pipeline):
    with pytest.raises(ValueError):
        ready_pipeline.get_node("node_that_is_not_there")
    received_node = ready_pipeline.get_node("a89f8eb5e7403cf0")
    assert received_node.node_name == "Input"

def test_get_step(ready_pipeline: Pipeline):
    with pytest.raises(ValueError):
        ready_pipeline.get_step("step_that_is_not_there")
    print(ready_pipeline.get_step("0c7788842ca589f9"))
    received_step = ready_pipeline.get_step("0c7788842ca589f9")
    assert received_step.id == "0c7788842ca589f9"
    assert str(received_step.nodes) == "[Input, Output, Output, Label Encoder train, Select Columns, Select Columns]"
    assert received_step.data == {'nodeName': 'Step', 'id': '0c7788842ca589f9', 'params': {'Stage name': {'type': 'description', 'value': 'Feature Engineering'}, 'color': {'type': 'color', 'value': 'rgba(255, 99, 132, 0.75)'}, 'link': {'type': 'link', 'value': ''}}}
    assert received_step.original_name == "Feature Engineering"