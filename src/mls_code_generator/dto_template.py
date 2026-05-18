# -*- coding: utf-8 -*-
DTO_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
DTOPipelineData — utilities to serialize/deserialize pandas DataFrame.

Converts pandas.DataFrame to in-memory Parquet bytes encoded with Base64 so the
result can be embedded in JSON payloads exchanged between services.
\"\"\"

import base64
import json
from io import BytesIO
from typing import Any, Dict

import pandas as pd


class DTOPipelineData:
    TYPE_DF = "dataframe"
    FORMAT_PARQUET = "parquet"

    @classmethod
    def serialize(cls, obj: Any, include_meta: bool = True) -> Dict[str, Any]:
        if not isinstance(obj, pd.DataFrame):
            raise ValueError("DTOPipelineData.serialize expects a pandas.DataFrame.")
        buf = BytesIO()
        obj.to_parquet(buf, index=False)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        out = {"type": cls.TYPE_DF, "format": cls.FORMAT_PARQUET, "payload": b64}
        if include_meta:
            out["meta"] = {"columns": list(obj.columns), "dtypes": {str(c): str(t) for c, t in obj.dtypes.items()}, "rows": int(len(obj))}
        return out

    @classmethod
    def deserialize(cls, payload: Dict[str, Any]) -> Any:
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dict.")
        t = payload.get("type"); fmt = payload.get("format"); b64 = payload.get("payload")
        if not (t and fmt and b64):
            raise ValueError("Malformed payload.")
        raw = base64.b64decode(b64.encode("utf-8"))
        if t == cls.TYPE_DF and fmt == cls.FORMAT_PARQUET:
            buf = BytesIO(raw)
            return pd.read_parquet(buf)
        raise ValueError(f"Unsupported payload type/format: {t}/{fmt}")
"""