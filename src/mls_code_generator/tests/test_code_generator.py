# -*- coding: utf-8 -*-
import pytest
from ..code_generator import CodeGenerator
from ..pipeline_loader import PipelineLoader
from ..configuration_loader import ConfigLoader
from ..types import Pipeline, Service
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

BASE_DIR = os.path.dirname(__file__)

@pytest.fixture
def pipeline() -> Pipeline:
    return Pipeline()

@pytest.fixture
def ready_pipeline_loader() -> PipelineLoader:
    with open(os.path.join(BASE_DIR, "files", "nodes.json"), "r", encoding="utf-8") as file:
        nodes = json.load(file)["nodes"]
    with open(os.path.join(BASE_DIR, "files", "mls_editor_fixed.json"), "r", encoding="utf-8") as file:
        code = json.load(file)

    node_configuration = ConfigLoader(content=nodes)
    pipeline_loader = PipelineLoader(code, node_configuration)

    return pipeline_loader

@pytest.fixture
def ready_pipeline(pipeline: Pipeline, ready_pipeline_loader) -> Pipeline:
    pipeline.load_pipeline(ready_pipeline_loader)
    return pipeline

@pytest.fixture
def ready_pipeline_single_service(pipeline: Pipeline, ready_pipeline_loader) -> Pipeline:
    pipeline.load_pipeline(ready_pipeline_loader)
    with open(os.path.join(BASE_DIR, "files", "nodes.json"), "r", encoding="utf-8") as f:
        pass 
    pipeline.generation_mode = "monolith"
    return pipeline

@pytest.fixture
def ready_pipeline_multi_service(pipeline: Pipeline, ready_pipeline_loader) -> Pipeline:
    pipeline.load_pipeline(ready_pipeline_loader)
    with open(os.path.join(BASE_DIR, "files", "nodes.json"), "r", encoding="utf-8") as f:
        pass
    pipeline.generation_mode = "services"
    return pipeline

def test_code_generator_instantiation():
    cg = CodeGenerator()
    assert hasattr(cg, "output_dir")
    assert cg.output_dir is None

def test_generate_code(tmp_path, ready_pipeline):
    pipeline = ready_pipeline
    cg = CodeGenerator()
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    cg.output_dir = str(out)
    cg.generate_code(pipeline)

    modules = cg.get_modules()
    assert isinstance(modules, dict)
    assert len(modules) > 0
    assert "main" in modules

def test_generate_code_single_service_e2e(tmp_path, ready_pipeline_single_service):
    pipeline = ready_pipeline_single_service
    cg = CodeGenerator()
    out = tmp_path / "out_single"
    out.mkdir(parents=True, exist_ok=True)
    cg.output_dir = str(out)
    cg.generate_code(pipeline)

    modules = cg.get_modules()
    assert isinstance(modules, dict)
    assert len(modules) > 0
    assert "main" in modules

def test_generate_code_multi_service_e2e(tmp_path, ready_pipeline_multi_service):
    pipeline = ready_pipeline_multi_service
    cg = CodeGenerator()
    out = tmp_path / "out_multi"
    out.mkdir(parents=True, exist_ok=True)
    cg.output_dir = str(out)
    cg.generate_code(pipeline)

    assert out.exists()
    assert (out / "docker-compose.yml").exists()

def test_flask_adapter_is_default():
    from ..services_factory import ServicesFactory

    factory = ServicesFactory.get_instance()
    adapter = factory.get_service_adapter("flask")

    assert adapter.__class__.__name__ == "FlaskServiceAdapter"
    assert hasattr(adapter, "generate_service_code") and callable(getattr(adapter, "generate_service_code"))

def test_flask_adapter_writes_app_and_readme(tmp_path):
    from ..adapters.flask_adapter import FlaskServiceAdapter

    adapter = FlaskServiceAdapter()
    svc_dummy = type("SVC", (), {"service_id": "svc_test"})()
    out = tmp_path / "svc_test"
    out.mkdir(parents=True, exist_ok=True)
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
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    cg.output_dir = str(out)
    cg.generate_code(pipeline)

    assert (out / "docker-compose.yml").exists()

def test_service_joblib_implementation(tmp_path, ready_pipeline):
    pipeline = ready_pipeline
    pipeline.generation_mode = "services"

    step_ids = [s for s in pipeline.steps.keys() if s != "root"]
    if step_ids:
        svc = Service("SvcA")
        svc.add_step(pipeline.get_step(step_ids[0]))
        pipeline.add_services({"SvcA": svc})

    cg = CodeGenerator()
    out_dir = tmp_path / "out_joblib"
    out_dir.mkdir(parents=True, exist_ok=True)
    cg.output_dir = str(out_dir)
    cg.generate_code(pipeline)
    
    compose_file = out_dir / "docker-compose.yml"
    assert compose_file.exists()
    compose_content = compose_file.read_text(encoding="utf-8")
    
    assert "volumes:" in compose_content or "volumes:" in compose_content.replace(" ", "")
    assert "/data" in compose_content