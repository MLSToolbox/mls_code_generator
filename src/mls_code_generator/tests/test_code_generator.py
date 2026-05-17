import pytest
from ..code_generator import CodeGenerator
from ..pipeline_loader import PipelineLoader
from ..configuration_loader import ConfigLoader
from ..types import Pipeline
from ..connection_classifier import classify_pipeline_connections
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

@pytest.fixture
def ready_pipeline_single_service():
    with open("./tests/files/nodes.json", "r", encoding="utf-8") as f:
        nodes = json.load(f)["nodes"]
    with open("./tests/files/mls_editor_single_service.json", "r", encoding="utf-8") as f:
        code = json.load(f)

    node_configuration = ConfigLoader(content=nodes)
    pipeline_loader = PipelineLoader(code, node_configuration)
    pipeline = Pipeline()
    pipeline.load_pipeline(pipeline_loader)
    return pipeline

@pytest.fixture
def ready_pipeline_multi_service():
    with open("./tests/files/nodes.json", "r", encoding="utf-8") as f:
        nodes = json.load(f)["nodes"]
    with open("./tests/files/mls_editor_multi_service.json", "r", encoding="utf-8") as f:
        code = json.load(f)

    node_configuration = ConfigLoader(content=nodes)
    pipeline_loader = PipelineLoader(code, node_configuration)
    pipeline = Pipeline()
    pipeline.load_pipeline(pipeline_loader)
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

def test_generate_code_single_service_e2e(ready_pipeline_single_service):
    pipeline = ready_pipeline_single_service
    pipeline.generation_mode = "services"

    cg = CodeGenerator()
    cg.generate_code(pipeline)

    svc_ids = list(pipeline.services.keys())
    assert len(svc_ids) >= 1
    for svc_id in svc_ids:
        assert f"service_{svc_id}_main" in cg.modules

    if len(svc_ids) == 1:
        module_text = cg.modules[f"service_{svc_ids[0]}_main"]
        assert "TODO (IB5/IB6)" not in module_text

def test_generate_code_multi_service_e2e(ready_pipeline_multi_service):
    pipeline = ready_pipeline_multi_service
    pipeline.generation_mode = "services"

    cg = CodeGenerator()
    cg.generate_code(pipeline)

    for svc_id in pipeline.services.keys():
        assert f"service_{svc_id}_main" in cg.modules

    conns = classify_pipeline_connections(pipeline)
    externals = [c for c in conns if getattr(c.conn_type, "value", None) == "external" or getattr(c.conn_type, "name", None) == "EXTERNAL"]
    if externals:
        ci = externals[0]
        target_step = pipeline.steps[ci.target_step_id]
        placeholder = f"external_{ci.source_step_id}_to_{target_step.name}"
        module_text = cg.modules[f"service_{ci.target_service_id}_main"]
        assert "TODO (IB5/IB6)" in module_text
        assert placeholder in module_text

def test_services_factory_returns_flask_adapter():
    from mls_code_generator.services_factory import ServicesFactory
    from mls_code_generator.adapters.flask_adapter import FlaskServiceAdapter

    factory = ServicesFactory.get_instance()
    adapter = factory.get_service_adapter("flask")
    assert isinstance(adapter, FlaskServiceAdapter)

def test_flask_adapter_writes_app_and_readme(tmp_path):
    from mls_code_generator.adapters.flask_adapter import FlaskServiceAdapter

    adapter = FlaskServiceAdapter()
    svc_dummy = type("SVC", (), {"service_id": "svc_test"})()
    out = tmp_path / "svc_test"
    adapter.generate_service_code(svc_dummy, str(out))

    app_file = out / "app.py"
    readme = out / "README.generated"
    assert app_file.exists()
    assert readme.exists()
    content = app_file.read_text(encoding="utf-8")
    assert "def health()" in content
    assert "def execute()" in content

def test_generate_code_writes_service_entrypoints(tmp_path, ready_pipeline):
    pipeline = ready_pipeline
    pipeline.generation_mode = "services"
    cg = CodeGenerator()
    cg.output_dir = str(tmp_path / "out")
    cg.generate_code(pipeline)

    for svc_id in pipeline.services.keys():
        svc_path = tmp_path / "out" / "services" / str(svc_id)
        assert svc_path.exists()
        assert (svc_path / "app.py").exists()