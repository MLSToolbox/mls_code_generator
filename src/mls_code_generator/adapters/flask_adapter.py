"""FlaskServiceAdapter: Concrete adapter that generates a minimal Flask app."""
import os
from typing import Any
from .i_service_adapter import IServiceAdapter

APP_PY_TEMPLATE = """from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP"}), 200

@app.route("/execute", methods=["POST"])
def execute():
    # TODO: quan hi hagi els dokers cal arreglar aixo per tal que no sigui en local
    payload = request.get_json(force=True, silent=True) or {}
    return jsonify({"status": "success", "outputs": {}}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
"""


class FlaskServiceAdapter(IServiceAdapter):
    """Flask adapter that writes `app.py` and a marker file to the output path."""

    def generate_service_code(self, service: Any, output_path: str) -> None:
        """
        Create output directory and write `app.py` and `README.generated`.

        Args:
            service: Service instance (used for marker content).
            output_path (str): Filesystem directory to create and populate.

        Returns:
            None
        """

        os.makedirs(output_path, exist_ok=True)

        app_py_path = os.path.join(output_path, "app.py")
        with open(app_py_path, "w", encoding="utf-8") as f:
            f.write(APP_PY_TEMPLATE)

        readme_path = os.path.join(output_path, "README.generated")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"Generated Flask app for service: {getattr(service, 'service_id', str(service))}\n")