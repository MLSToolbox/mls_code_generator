import pytest

from mls_code_generator.types.step import Step
from mls_code_generator.types.service import Service
from mls_code_generator.types.pipeline import Pipeline
from mls_code_generator.connection_classifier import (
    classify_pipeline_connections,
    ConnectionType,
)

@pytest.fixture
def pipeline_abc_services():
    a = Step("a")
    b = Step("b")
    c = Step("c")

    s1 = Service("svc1")
    s1.add_step(a)
    s1.add_step(b)

    s2 = Service("svc2")
    s2.add_step(c)

    pipeline = Pipeline()
    pipeline.add_steps({"a": a, "b": b, "c": c})
    pipeline.add_services({"svc1": s1, "svc2": s2})
    return pipeline


@pytest.fixture
def pipeline_abcd_mixed():
    a = Step("a")
    b = Step("b")
    c = Step("c")
    d = Step("d")

    s1 = Service("svc1")
    s1.add_step(a)
    s1.add_step(b)

    s2 = Service("svc2")
    s2.add_step(c)
    s2.add_step(d)

    pipeline = Pipeline()
    pipeline.add_steps({"a": a, "b": b, "c": c, "d": d})
    pipeline.add_services({"svc1": s1, "svc2": s2})
    return pipeline


@pytest.fixture
def pipeline_ab_monolith_with_c_service():
    a = Step("a")
    b = Step("b")
    c = Step("c")

    s2 = Service("svc2")
    s2.add_step(c)

    pipeline = Pipeline()
    pipeline.add_steps({"a": a, "b": b, "c": c})
    pipeline.add_services({"svc2": s2})
    return pipeline

def test_classify_internal_and_external_connections(pipeline_abc_services):
    pipeline = pipeline_abc_services

    pipeline.steps["b"].add_main_connection(pipeline.steps["a"], "out_a", "in_b")
    pipeline.steps["c"].add_main_connection(pipeline.steps["b"], "out_b", "in_c")

    connections = classify_pipeline_connections(pipeline)

    assert len(connections) == 2

    types = {(ci.source_step_id, ci.target_step_id): ci.conn_type for ci in connections}
    assert types[("a", "b")] == ConnectionType.INTERNAL
    assert types[("b", "c")] == ConnectionType.EXTERNAL

    assert hasattr(pipeline.steps["b"], "external_outgoing")
    assert len(pipeline.steps["b"].external_outgoing) == 1
    assert pipeline.steps["b"].external_outgoing[0].target_step_id == "c"

    assert hasattr(pipeline.steps["c"], "external_incoming")
    assert len(pipeline.steps["c"].external_incoming) == 1
    assert pipeline.steps["c"].external_incoming[0].source_step_id == "b"


def test_source_as_string_id(pipeline_abc_services):
    pipeline = pipeline_abc_services

    pipeline.steps["b"].add_main_connection("a", "out_a", "in_b")

    conns = classify_pipeline_connections(pipeline)
    assert len(conns) == 1
    assert conns[0].source_step_id == "a"
    assert conns[0].target_step_id == "b"
    assert conns[0].conn_type == ConnectionType.INTERNAL


def test_multiple_external_connections_and_annotations(pipeline_abcd_mixed):
    pipeline = pipeline_abcd_mixed

    pipeline.steps["c"].add_main_connection(pipeline.steps["a"], "out_a", "in_c")
    pipeline.steps["d"].add_main_connection(pipeline.steps["a"], "out_a", "in_d")
    pipeline.steps["c"].add_main_connection(pipeline.steps["b"], "out_b", "in_c")

    conns = classify_pipeline_connections(pipeline)
    external = [c for c in conns if c.conn_type == ConnectionType.EXTERNAL]
    assert len(external) == 3

    assert hasattr(pipeline.steps["a"], "external_outgoing")
    targets = {ci.target_step_id for ci in pipeline.steps["a"].external_outgoing}
    assert targets == {"c", "d"}

    sources = {ci.source_step_id for ci in pipeline.steps["c"].external_incoming}
    assert sources == {"a", "b"}


def test_malformed_dependency_is_skipped(pipeline_abc_services):
    pipeline = pipeline_abc_services

    pipeline.steps["b"].dependencies.append(("a",))
    pipeline.steps["b"].add_main_connection(pipeline.steps["a"], "out", "in")

    conns = classify_pipeline_connections(pipeline)
    assert len(conns) == 1
    assert conns[0].source_step_id == "a"
    assert conns[0].target_step_id == "b"


def test_monolith_fallback_behavior(pipeline_ab_monolith_with_c_service):
    pipeline = pipeline_ab_monolith_with_c_service

    pipeline.steps["b"].add_main_connection(pipeline.steps["a"], "out_a", "in_b")
    pipeline.steps["c"].add_main_connection(pipeline.steps["b"], "out_b", "in_c")

    conns = classify_pipeline_connections(pipeline)
    types = {(ci.source_step_id, ci.target_step_id): ci.conn_type for ci in conns}
    assert types[("a", "b")] == ConnectionType.INTERNAL
    assert types[("b", "c")] == ConnectionType.EXTERNAL