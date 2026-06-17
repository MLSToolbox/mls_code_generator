import os
import joblib
import pandas as pd
import pytest
import tempfile
import time


@pytest.fixture(scope="module")
def DTOPipelineData_cls():

    class DTOPipelineData:
        @staticmethod
        def serialize(df: pd.DataFrame):
            if not isinstance(df, pd.DataFrame):
                raise ValueError("serialize expects a pandas DataFrame")
            ts = int(time.time() * 1000)
            fname = f"dto_df_{ts}.pkl"
            path = os.path.join(tempfile.gettempdir(), fname)
            joblib.dump(df, path)
            return {"payload": path}

        @staticmethod
        def deserialize(payload: dict):
            path = payload.get("payload")
            if not path or not os.path.exists(path):
                raise ValueError("Payload file not found")
            return joblib.load(path)

    return DTOPipelineData


@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_dto_roundtrip_small_dataframe(DTOPipelineData_cls, sample_df):
    payload = DTOPipelineData_cls.serialize(sample_df)
    assert isinstance(payload, dict)
    assert "payload" in payload
    out = DTOPipelineData_cls.deserialize(payload)
    pd.testing.assert_frame_equal(sample_df.reset_index(drop=True), out.reset_index(drop=True))


def test_dto_rejects_non_dataframe(DTOPipelineData_cls):
    with pytest.raises(ValueError):
        DTOPipelineData_cls.serialize({"not": "a df"})