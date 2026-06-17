import pytest
from unittest.mock import MagicMock, patch
from ..utils import fix_editor
import json
import os

BASE_DIR = os.path.dirname(__file__)

def test_fix_editor():
    with open(os.path.join(BASE_DIR, "files", "mls_editor.json"), "r", encoding="utf-8") as f:
        d = json.load(f)
    out = fix_editor(d)
    with open(os.path.join(BASE_DIR, "files", "mls_editor_fixed.json"), "r", encoding="utf-8") as f:
        d2 = json.load(f)
        assert out == d2