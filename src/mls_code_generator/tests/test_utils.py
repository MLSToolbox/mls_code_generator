import pytest
from unittest.mock import MagicMock, patch
from ..utils import fix_editor
import json
import os
def test_fix_editor():
    with open("./tests/files/mls_editor.json", "r") as f:
        d = json.load(f)
    out = fix_editor(d)
    with open("./tests/files/mls_editor_fixed.json", "r") as f:
        d2 = json.load(f)
        assert out == d2