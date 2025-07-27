import pytest
from unittest.mock import Mock
from ..types import CustomNode, Node, Pipeline, Step


@pytest.fixture
def example_custom_node_config():
    return {
        "node": "Split train test",
        "info": {"title": "Splits data into train and test"},
        "category": "Model Training",
        "params": [
            {"param_label": "description", "param_type": "description", "show": True},
            {"param_label": "train_percentage", "param_type": "number", "show": True},
        ],
        "inputs": [
            {"port_label": "features", "port_type": "DataFrame"},
            {"port_label": "truth", "port_type": "DataFrame"},
        ],
        "outputs": [
            {"port_label": "features_train", "port_type": "DataFrame"},
            {"port_label": "features_test", "port_type": "DataFrame"},
            {"port_label": "truth_train", "port_type": "DataFrame"},
            {"port_label": "truth_test", "port_type": "DataFrame"},
        ],
        "dependencies": {
            "model_training": {"origin": "custom", "value": "TrainTestSplitter"}
        },
        "origin": {"custom": "TrainTestSplitter"},
    }


@pytest.fixture
def example_orchestration_node_config():
    return {
        "node": "Output",
        "info": {"title": "Saves data to be used in next steps"},
        "category": "Step Managment",
        "params": [
            {"param_label": "description", "param_type": "description", "show": True},
            {"param_label": "key", "param_type": "description", "show": True},
            {
                "param_label": "Socket type",
                "param_type": "option",
                "optionId": "socket_type",
                "show": True,
            },
        ],
        "inputs": [{"port_label": "key", "port_type": "Any"}],
        "outputs": [],
        "dependencies": {},
        "origin": {"custom": ""},
    }


@pytest.fixture
def node():
    return Node()


def test_custom_node_creation(example_custom_node_config):

    node = CustomNode(example_custom_node_config)

    assert node.config == example_custom_node_config
    assert node.node_name == example_custom_node_config["node"]
    assert node.origin == example_custom_node_config["origin"]
    assert node.module_dependencies == example_custom_node_config["dependencies"]

    for param in example_custom_node_config["params"]:
        assert node.params[param["param_label"]] == {
            "value": None,
            "type": param["param_type"],
        }

    for i, input_socket in enumerate(example_custom_node_config["inputs"]):
        assert node.inputs[i] == input_socket["port_label"]

    for i, output_socket in enumerate(example_custom_node_config["outputs"]):
        assert node.outputs[i] == output_socket["port_label"]


def test_custom_node_copy(example_custom_node_config):

    node = CustomNode(example_custom_node_config)

    new_node = node.get_copy()

    assert node.config == new_node.config
    assert node.node_name == new_node.node_name
    assert node.origin == new_node.origin
    assert node.module_dependencies == new_node.module_dependencies
    assert node.params == new_node.params
    assert node.inputs == new_node.inputs
    assert node.outputs == new_node.outputs


@pytest.fixture
def example_node_data():
    return {
        "id": "b4b3f5e945f82a5c",
        "nodeName": "Split train test",
        "params": {
            "description": {
                "isParam": "custom",
                "param_label": "",
                "show": True,
                "type": "description",
            },
            "train_percentage": {
                "isParam": "custom",
                "param_label": "",
                "show": True,
                "type": "number",
                "value": "0.3",
            },
        },
    }


@pytest.fixture
def loaded_node(example_custom_node_config, example_node_data):
    c = CustomNode(example_custom_node_config)
    c.set_data(example_node_data)
    return c


@pytest.fixture
def example_orchestration_node_data():
    return {
        "id": "a64687a207c22aad",
        "nodeName": "Output",
        "params": {
            "description": {"show": True, "type": "description", "value": ""},
            "key": {"type": "description", "value": "truth test"},
            "type": {"optionId": "socket_type", "type": "option", "value": "DataFrame"},
        },
    }


@pytest.fixture
def example_node_data_with_param():
    return {
        "id": "b4b3f5e945f82a5c",
        "nodeName": "Split train test",
        "params": {
            "description": {
                "isParam": "custom",
                "param_label": "",
                "show": True,
                "type": "description",
            },
            "train_percentage": {
                "isParam": "parameter",
                "param_label": "train_percentage",
                "show": True,
                "type": "number",
                "value": "0.3",
            },
        },
    }


@pytest.fixture
def loaded_node_with_param(example_custom_node_config, example_node_data_with_param):
    c = CustomNode(example_custom_node_config)
    c.set_data(example_node_data_with_param)
    return c


def test_node_creation():
    node = Node()

    assert node.id == None
    assert node.data == None
    assert node.dependencies == []
    assert node.sources == {}
    assert node.node_name == None
    assert type(node.parent) == Pipeline
    assert node.parent_step.id == "0"
    assert type(node.parent_step) == Step
    assert node.ready == []
    assert node.params == {}
    assert node.inputs == []
    assert node.outputs == []
    assert node.origin == {}
    assert node.origin_label == ""
    assert node.module_dependencies == {}
    assert node.variable_name == ""


def test_data_assignation_random_node(example_custom_node_config, example_node_data):

    node = CustomNode(example_custom_node_config)
    node.set_data(example_node_data)

    assert node.id == example_node_data["id"]
    assert node.data == example_node_data
    assert node.node_name == example_node_data["nodeName"]
    assert node.origin_label == "TrainTestSplitter"

    for key, value in example_node_data["params"].items():
        assert (
            node.params[key]["value"] == ""
            or node.params[key]["value"] == value["value"]
        )
        assert node.params[key]["type"] == value["type"]
        assert node.params[key]["isParam"] == value["isParam"]
        assert node.params[key]["param_label"] == value["param_label"]


def test_data_assignation_orchestration_node(
    example_orchestration_node_config, example_orchestration_node_data
):

    node = CustomNode(example_orchestration_node_config)
    node.set_data(example_orchestration_node_data)

    assert node.id == example_orchestration_node_data["id"]
    assert node.data == example_orchestration_node_data
    assert node.node_name == example_orchestration_node_data["nodeName"]
    assert node.origin_label == ""

    for key, value in example_orchestration_node_data["params"].items():
        assert (
            node.params[key]["value"] == ""
            or node.params[key]["value"] == value["value"]
        )
        assert node.params[key]["type"] == value["type"]


def test_node_set_parent(node: Node):
    p = Mock()
    node.set_parent(p)

    assert node.parent == p


def test_node_set_parent_step(node: Node):
    p = Mock()
    node.set_parent_step(p)
    assert node.parent_step == p


def test_add_dependency(node: Node):
    node.add_dependency("dep", "port", "src", "src_port")
    assert node.dependencies == [("src", "src_port", "dep", "port")]
    assert node.ready == [False]


def test_add_source(node: Node):
    target = Node()
    node.add_source("my_port", target, "target_port")
    assert node.sources == {"my_port": [(target, "target_port")]}
    node.add_source("my_port", target, "target_port")
    assert node.sources == {
        "my_port": [(target, "target_port"), (target, "target_port")]
    }


def test_is_ready(node: Node):
    assert node.is_ready()
    node.add_dependency("dep", "port", "src", "src_port")
    assert not node.is_ready()
    node.past_dependency("dep", "port")
    assert node.is_ready()


def test_past_dependency(node: Node):
    node.add_dependency("dep", "port", "src", "src_port")
    node.past_dependency("dep", "port")
    assert node.ready == [True]


def test_get_output(loaded_node: CustomNode):
    assert loaded_node.get_output("features_train") == "features_train"
    t = "no_feature"
    assert loaded_node.get_output(t) == f"NO OUTPUT FOUND: {t} in Split train test"


def test_get_input(loaded_node: CustomNode):
    assert loaded_node._get_input("features") == [None, None]
    loaded_node.add_dependency("dep", "port", "src", "src_port")
    assert loaded_node._get_input("port") == ("src", "src_port")


def test_get_param(loaded_node: CustomNode):
    assert loaded_node.get_param("description") == ""
    assert loaded_node.get_param("train_percentage") == "0.3"
    assert (
        loaded_node.get_param("no_param")
        == "NO PARAM FOUND: no_param in Split train test"
    )


def test_get_param_type(loaded_node: CustomNode):
    assert loaded_node.get_param_type("description") == "description"
    assert loaded_node.get_param_type("train_percentage") == "number"
    assert (
        loaded_node.get_param_type("no_param")
        == "NO PARAM FOUND: no_param in Split train test"
    )


def test_generate_code(loaded_node: CustomNode, loaded_node_with_param: CustomNode):
    code = """ = TrainTestSplitter(\n\ttrain_percentage = 0.3\n)\n"""
    assert loaded_node.generate_code() == code
    code = """ = TrainTestSplitter(\n\ttrain_percentage =  ParamLoader.load('.train_percentage')\n)\n"""
    assert loaded_node_with_param.generate_code() == code


def test_get_dependencies_code(loaded_node_with_param: CustomNode):
    other_node = loaded_node_with_param.get_copy()
    loaded_node_with_param.add_dependency(other_node, "port", other_node, "src_port")
    assert loaded_node_with_param.get_dependencies_code() == ["port = None"]


def test_is_param_label(loaded_node: CustomNode, loaded_node_with_param: CustomNode):
    assert not loaded_node.is_param_label("description")
    assert not loaded_node.is_param_label("train_percentage")
    with pytest.raises(KeyError):
        loaded_node.is_param_label("no_param")
    assert not loaded_node_with_param.is_param_label("description")
    assert loaded_node_with_param.is_param_label("train_percentage")
    with pytest.raises(KeyError):
        loaded_node_with_param.is_param_label("no_param")


def test_get_param_label(loaded_node_with_param: CustomNode):
    loaded_node_with_param.get_param_label("train_percentage")
    assert (
        loaded_node_with_param.get_param_label("train_percentage")
        == ".train_percentage"
    )

    m = Mock()
    Mock.name = "test"
    loaded_node_with_param.set_parent_step(m)
    assert (
        loaded_node_with_param.get_param_label("train_percentage")
        == "test.train_percentage"
    )


def test_get_param_count(loaded_node_with_param: CustomNode):
    assert loaded_node_with_param.get_param_count() == 1


def test_get_dependencies(loaded_node: CustomNode, loaded_node_with_param: CustomNode):
    assert loaded_node.get_dependencies() == {"model_training": {"TrainTestSplitter"}}
    assert loaded_node_with_param.get_dependencies() == {
        "model_training": {"TrainTestSplitter"},
        "orchestration": {"ParamLoader"},
    }


def test_get_label_params(loaded_node_with_param: CustomNode):
    assert loaded_node_with_param.get_label_params() == [{"train_percentage": 0.3}]


def test_is_output_multiple(loaded_node_with_param: CustomNode):
    assert loaded_node_with_param.is_output_multiple("features_train") == None
    other_node = loaded_node_with_param.get_copy()
    loaded_node_with_param.add_dependency(other_node, "port", other_node, "src_port")
    other_node.add_source("src_port", loaded_node_with_param, "port")
    assert loaded_node_with_param.is_output_multiple("port") == False
    other_node.add_source("src_port", loaded_node_with_param, "port")
    assert loaded_node_with_param.is_output_multiple("port") == True

