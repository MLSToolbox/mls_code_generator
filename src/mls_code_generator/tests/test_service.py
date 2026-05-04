import pytest
from unittest.mock import Mock
from ..types.service import Service

@pytest.fixture
def empty_service() -> Service:
    return Service("test_service_id")

@pytest.fixture
def mock_node_data_processing() -> Mock:
    node = Mock()
    node.get_dependencies.return_value = {"data_processing": {"SelectColumns"}}
    return node

@pytest.fixture
def mock_node_mixed() -> Mock:
    node = Mock()
    node.get_dependencies.return_value = {
        "data_processing": {"FillNulls"}, 
        "model_training": {"RandomForest"}
    }
    return node

@pytest.fixture
def mock_step(mock_node_data_processing, mock_node_mixed) -> Mock:
    step = Mock()
    step.nodes = [mock_node_data_processing, mock_node_mixed]
    return step

def test_service_creation(empty_service: Service):
    assert empty_service.service_id == "test_service_id"
    assert empty_service.steps == []

def test_add_step(empty_service: Service, mock_step: Mock):
    empty_service.add_step(mock_step)
    
    assert len(empty_service.steps) == 1
    assert empty_service.steps[0] == mock_step

def test_get_dependencies(empty_service: Service, mock_step: Mock):
    empty_service.add_step(mock_step)
    
    deps = empty_service.get_dependencies()
    
    assert "data_processing" in deps
    assert deps["data_processing"] == {"SelectColumns", "FillNulls"}  
    
    assert "model_training" in deps
    assert deps["model_training"] == {"RandomForest"}
    
    assert "orchestration" in deps
    assert "Stage" in deps["orchestration"]