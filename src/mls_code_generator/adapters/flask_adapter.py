"""FlaskServiceAdapter: Concrete adapter that generates a minimal Flask app."""
import os
from typing import Any
import importlib
from .i_service_adapter import IServiceAdapter

APP_PY_TEMPLATE = """import os
from flask import Flask, request, jsonify
import json
from dto_pipeline_data import DTOPipelineData
import service_{svc_id}_main as svc_module

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "UP"}}), 200

@app.route("/execute", methods=["POST"])
def execute():
    raw = request.get_data(as_text=True) or "{{}}"
    try:
        payload_dict = json.loads(raw)
        inputs = payload_dict.get("inputs", {{}})
    except Exception as _parse_err:
        print(f"Error parsing JSON: {{_parse_err}}")
        inputs = {{}}

    try:
        outputs = svc_module.execute_service(inputs)
        response_body = {{
            "status": "success",
            "outputs": outputs,
            "error": None
        }}
        return jsonify(response_body), 200
    except Exception as _exec_err:
        print(f"Error running service: {{_exec_err}}", flush=True)
        return jsonify({{"status": "error", "outputs": {{}}, "error": str(_exec_err)}}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", {port}))
    app.run(host="0.0.0.0", port=port)
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
        svc_id_val = getattr(service, "service_id", "svc")
        port_val = getattr(service, "port", 5000)
        content = APP_PY_TEMPLATE.format(svc_id=svc_id_val, port=port_val)
        with open(app_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        src_template = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "dto_template.py"))
        dst_dto = os.path.join(output_path, "dto_pipeline_data.py")
        with open(src_template, "r", encoding="utf-8") as src_f:
            tpl = src_f.read()
        tpl_mod = importlib.import_module("mls_code_generator.dto_template")
        tpl_body = getattr(tpl_mod, "DTO_TEMPLATE")

        dst_dto = os.path.join(output_path, "dto_pipeline_data.py")
        if not tpl_body.endswith("\n"):
            tpl_body += "\n"
        with open(dst_dto, "w", encoding="utf-8") as dst_f:
            dst_f.write(tpl_body)

        service_reqs = []
        if hasattr(service, "get_dependencies"):
            deps = service.get_dependencies()
            if isinstance(deps, dict):
                service_reqs = [k for k in deps.keys() if isinstance(k, str) and k.strip()]
            elif isinstance(deps, (list, tuple, set)):
                service_reqs = list(deps)
            elif isinstance(deps, str):
                service_reqs = [deps]

        norm_reqs = [r.strip() for r in service_reqs if isinstance(r, str) and r.strip()]
        base_reqs = ["pandas", "pyarrow", "flask"]
        all_reqs = sorted(set(base_reqs) | set(norm_reqs))

        req_path = os.path.join(output_path, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as req_f:
            req_f.write("\n".join(all_reqs) + "\n")

        readme_path = os.path.join(output_path, "README.generated")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"Generated Flask app for service: {getattr(service, 'service_id', str(service))}\n")