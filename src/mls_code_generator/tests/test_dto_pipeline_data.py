import pandas as pd
import pytest

from mls_code_generator import dto_template

@pytest.fixture(scope="module")
def DTOPipelineData_cls():
    namespace = {}
    exec(dto_template.DTO_TEMPLATE, namespace)
    return namespace["DTOPipelineData"]

@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

def test_dto_roundtrip_small_dataframe(DTOPipelineData_cls, sample_df):
    payload = DTOPipelineData_cls.serialize(sample_df)
    assert isinstance(payload, dict)
    assert payload["type"] == "dataframe"
    assert payload["format"] == "parquet"
    assert "payload" in payload
    out = DTOPipelineData_cls.deserialize(payload)
    pd.testing.assert_frame_equal(sample_df.reset_index(drop=True), out.reset_index(drop=True))

def test_dto_rejects_non_dataframe(DTOPipelineData_cls):
    with pytest.raises(ValueError):
        DTOPipelineData_cls.serialize({"not": "a df"})