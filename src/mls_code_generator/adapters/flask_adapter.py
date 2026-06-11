"""FlaskServiceAdapter: Concrete adapter that generates a minimal Flask app."""
import os
import shutil
import re
from typing import Any, Set
import importlib
from .i_service_adapter import IServiceAdapter

APP_PY_TEMPLATE = """import os
import json
import time
import logging
from flask import Flask, request, jsonify
import service_{svc_id}_main as svc_module
import pandas as pd
import requests
import joblib

SERVICE_INPUT_PATH = os.getenv("SERVICE_INPUT_PATH", "/app") 
SERVICE_PERSIST_PATH = os.getenv("SERVICE_PERSIST_PATH", "/data") # Ara usem la bustia compartida /data
SERVICE_PORT = int(os.getenv("PORT", {port}))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def _is_json_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except Exception:
        return False

def _convert_value_for_json(key, val):
    if _is_json_serializable(val):
        return val
    
    try:
        os.makedirs(SERVICE_PERSIST_PATH, exist_ok=True)
        filename = f"artifact_{int(time.time())}_{key}.pkl"
        path = os.path.join(SERVICE_PERSIST_PATH, filename)
        
        joblib.dump(val, path)
        logger.info("Complex object saved to shared volume: %s", path)
        return path
    except Exception as e:
        logger.exception("No s'ha pogut guardar l'artifact de la clau %s: %s", key, e)
        return {"error": f"unserializable for key {key}"}

def _resolve_string_input(val):
    if not isinstance(val, str):
        return val
    candidate = os.path.join(SERVICE_INPUT_PATH, val)
    if os.path.exists(candidate):
        return os.path.basename(candidate)
    return val

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP"}), 200

@app.route("/execute", methods=["POST"])
def execute():
    raw = request.get_data(as_text=True) or "{}"
    try:
        payload = json.loads(raw)
    except Exception as e:
        logger.exception("Invalid JSON payload")
        return jsonify({"status": "error", "error": "Invalid JSON payload"}), 400

    inputs = payload.get("inputs", {})
    if not isinstance(inputs, dict):
        return jsonify({"status": "error", "error": "Invalid inputs: expected dict"}), 400

    if not inputs:
        try:
            expected_f = os.path.join(os.path.dirname(__file__), "expected_inputs.json")
            if os.path.exists(expected_f):
                with open(expected_f, "r", encoding="utf-8") as ef:
                    ej = json.load(ef)
                for key in ej.get("expected_inputs", []):
                    candidate = os.path.join(SERVICE_INPUT_PATH, key)
                    if os.path.exists(candidate):
                        inputs[key] = os.path.basename(candidate)
                        continue
                    try:
                        for fn in os.listdir(SERVICE_INPUT_PATH):
                            if key in fn:
                                inputs[key] = fn
                                break
                    except Exception:
                        pass
        except Exception:
            logger.exception("Error loading expected local inputs")

    try:
        for k, v in list(inputs.items()):
            if isinstance(v, str):
                if v.startswith(SERVICE_PERSIST_PATH) and v.endswith(".pkl") and os.path.exists(v):
                    logger.info("Loading object from shared volume: %s", v)
                    inputs[k] = joblib.load(v)
                else:
                    inputs[k] = _resolve_string_input(v)
    except Exception:
        logger.exception("Error resolving string inputs/artifacts")

    try:
        if os.path.isdir(SERVICE_INPUT_PATH):
            os.chdir(SERVICE_INPUT_PATH)
    except Exception:
        logger.exception("Failed to change working directory")

    try:
        outputs = svc_module.execute_service(inputs)
    except Exception as e:
        logger.exception("Error executing service logic")
        return jsonify({"status": "error", "error": f"Execution error: {str(e)}"}), 500

    if outputs is None:
        outputs = {}
    if not isinstance(outputs, dict):
        return jsonify({"status": "error", "error": "Service returned non-dict outputs"}), 500

    outputs = {k: v for k, v in outputs.items() if v is not None}

    converted = {}
    for k, v in outputs.items():
        converted[k] = _convert_value_for_json(k, v)

    downstream_file = os.path.join(os.path.dirname(__file__), "downstream.json")
    children = []
    try:
        if os.path.exists(downstream_file):
            with open(downstream_file, "r", encoding="utf-8") as df:
                dj = json.load(df)
            children = dj.get("children", [])
    except Exception:
        logger.exception("Error reading downstream.json")

    if not children:
        if len(converted) == 0:
            logger.info("Service execution finished (No outputs to return).")
        return jsonify({"status": "success", "outputs": converted}), 200

    if len(converted) == 0:
        logger.info("No direct outputs. Propagating execution trigger downstream...")

    for child in children:
        target_url = "http://" + str(child) + ":5000/execute"
        logger.info("Triggering downstream service: %s", target_url)
        try:
            resp = requests.post(target_url, json={"inputs": converted}, timeout=30)
            if not (200 <= resp.status_code < 300):
                return jsonify({"status": "error", "error": f"Downstream {child} returned {resp.status_code}"}), 502
        except Exception as e:
            return jsonify({"status": "error", "error": f"Forwarding error to {child}: {str(e)}"}), 502

    return jsonify({"status": "success", "outputs": converted}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=SERVICE_PORT)
"""

OPENAPI_YAML_TEMPLATE = """openapi: 3.0.3
info:
  title: Service {svc_name} API
  version: 1.0.0
  description: Auto-generated OpenAPI documentation for the '{svc_name}' REST service within the Machine Learning pipeline.
servers:
  - url: http://localhost:5000
    description: >
      Default local development server. 
      [IMPORTANT] To use this API with Swagger UI or Postman:
      1. Go to the generated 'docker-compose.yml'.
      2. Uncomment the 'ports' section for this service.
      3. If your external port is different from 5000, or you are on a remote server, update this URL accordingly (e.g., http://YOUR_IP:YOUR_PORT).
paths:
  /health:
    get:
      summary: Health check endpoint
      description: Returns the status of the service to verify it is running and ready to accept requests.
      responses:
        '200':
          description: Service is healthy and operational.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: UP
  /execute:
    post:
      summary: Execute service logic
      description: Receives input data or artifact references, runs the assigned pipeline stage using the core library, and registers outputs to the shared volume choreography.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                inputs:
                  type: object
                  description: Dictionary containing expected input keys and their corresponding values or file paths.
                  example: {{"features": "/data/artifact_123_features.pkl"}}
      responses:
        '200':
          description: Stage execution completed successfully.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: success
                  outputs:
                    type: object
                    description: Dictionary containing generated results or downstream artifact paths.
        '400':
          description: Invalid JSON payload format or missing required inputs structure.
        '500':
          description: Internal error triggered during Machine Learning logic execution.
        '502':
          description: Bad gateway error when notifying the next downstream service in the choreography chain.
"""

def _copy_mls_subpackages(selected: Set[str], global_mls_path: str, service_output: str):
    """
    Copies only the required mls_lib subpackages into the service's directory.

    Parameters:
        selected (Set[str]): Required subpackage names.
        global_mls_path (str): Root path to the global mls_lib.
        service_output (str): Destination service directory.

    Returns:
        None
    """
    dest_root = os.path.join(service_output, "mls_lib")
    os.makedirs(dest_root, exist_ok=True)
    for name in selected:
        src_dir = os.path.join(global_mls_path, name)
        src_file = os.path.join(global_mls_path, name + ".py")
        dst_dir = os.path.join(dest_root, name)
        dst_file = os.path.join(dest_root, name + ".py")
        if os.path.isdir(src_dir):
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
        elif os.path.isfile(src_file):
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.copyfile(src_file, dst_file)

def _collect_transitive_mls_deps(initial_roots: Set[str], global_mls_root: str) -> Set[str]:
    """
    Recursively finds all internal mls_lib dependencies required by the initial subpackages.

    Parameters:
        initial_roots (Set[str]): Starting set of mls_lib subpackages.
        global_mls_root (str): Root path to the global mls_lib.

    Returns:
        Set[str]: Complete set of required mls_lib subpackages.
    """
    to_process = set(initial_roots)
    collected = set(initial_roots)
    import_re = re.compile(r'(?:from|import)\s+mls_lib\.([A-Za-z0-9_\.]+)')
    while to_process:
        root = to_process.pop()
        candidate_path_dir = os.path.join(global_mls_root, root)
        candidate_path_file = os.path.join(global_mls_root, root + ".py")
        files = []
        if os.path.isdir(candidate_path_dir):
            for dirpath, _, filenames in os.walk(candidate_path_dir):
                for fn in filenames:
                    if fn.endswith(".py"):
                        files.append(os.path.join(dirpath, fn))
        elif os.path.isfile(candidate_path_file):
            files.append(candidate_path_file)
        for fp in files:
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception:
                continue
            for m in import_re.finditer(content):
                imported = m.group(1)
                imported_root = imported.split(".")[0]
                candidate = os.path.join(global_mls_root, imported_root)
                candidate_file = os.path.join(global_mls_root, imported_root + ".py")
                if (os.path.isdir(candidate) or os.path.isfile(candidate_file)) and imported_root not in collected:
                    collected.add(imported_root)
                    to_process.add(imported_root)
    return collected

def _collect_external_imports(root_path: str, excluded_roots: Set[str], local_names: Set[str]) -> Set[str]:
    """
    Scans Python files to identify external third-party dependencies for requirements.txt.

    Parameters:
        root_path (str): Directory containing the Python files to scan.
        excluded_roots (Set[str]): Directories/modules to ignore.
        local_names (Set[str]): Local file names to exclude.

    Returns:
        Set[str]: A set of external third-party package names.
    """
    stdlib_roots = {
        "os","sys","re","json","math","io","time","datetime","base64","logging","uuid",
        "collections","itertools","functools","subprocess","argparse","pathlib","unittest",
        "typing","threading","multiprocessing","hashlib","gzip","bz2","lzma","shutil","glob",
        "csv","http","socket","ssl","inspect","types","importlib","pkgutil","contextlib",
        "enum","traceback","statistics","heapq","copy","warnings"
    }

    PACKAGE_ALIASES = {
        "yaml": "pyyaml",
        "sklearn": "scikit-learn",
    }

    import_re_from = re.compile(r'^\s*from\s+([\w\.\s]+?)\s+import', re.MULTILINE)
    import_re_imp = re.compile(r'^\s*import\s+(.+)$', re.MULTILINE)

    externals = set()
    queue = []
    processed = set()

    for fn in os.listdir(root_path):
        if fn.endswith(".py"):
            queue.append(os.path.join(root_path, fn))

    while queue:
        current_file = os.path.normpath(queue.pop(0))
        if current_file in processed:
            continue
        processed.add(current_file)

        if not os.path.exists(current_file):
            continue

        try:
            with open(current_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        current_dir = os.path.dirname(current_file)

        for m in import_re_from.finditer(content):
            module_path = m.group(1).replace(" ", "")
            if module_path.startswith("."):
                dots = len(module_path) - len(module_path.lstrip("."))
                rel_module = module_path.lstrip(".")
                target_dir = current_dir
                for _ in range(dots - 1):
                    target_dir = os.path.dirname(target_dir)
                
                if rel_module:
                    parts = rel_module.split(".")
                    file_cand = os.path.join(target_dir, *parts) + ".py"
                    dir_cand = os.path.join(target_dir, *parts, "__init__.py")
                    if os.path.exists(file_cand): queue.append(file_cand)
                    if os.path.exists(dir_cand): queue.append(dir_cand)
                continue

            root = module_path.split(".")[0]
            if root == "mls_lib":
                parts = module_path.split(".")
                file_cand = os.path.join(root_path, *parts) + ".py"
                dir_cand = os.path.join(root_path, *parts, "__init__.py")
                if os.path.exists(file_cand): queue.append(file_cand)
                if os.path.exists(dir_cand): queue.append(dir_cand)
            else:
                root_mapped = PACKAGE_ALIASES.get(root, root)
                if root_mapped and root_mapped not in stdlib_roots and root_mapped not in local_names:
                    externals.add(root_mapped)

        for m in import_re_imp.finditer(content):
            groups = m.group(1)
            parts = [p.strip().split()[0] for p in groups.split(",") if p.strip()]
            for module_path in parts:
                root = module_path.split(".")[0]
                if root == "mls_lib":
                    sub_parts = module_path.split(".")
                    file_cand = os.path.join(root_path, *sub_parts) + ".py"
                    dir_cand = os.path.join(root_path, *sub_parts, "__init__.py")
                    if os.path.exists(file_cand): queue.append(file_cand)
                    if os.path.exists(dir_cand): queue.append(dir_cand)
                else:
                    root_mapped = PACKAGE_ALIASES.get(root, root)
                    if root_mapped and root_mapped not in stdlib_roots and root_mapped not in local_names:
                        externals.add(root_mapped)

    return externals

class FlaskServiceAdapter(IServiceAdapter):
    """Flask adapter that writes `app.py`, `requirements.txt` and `Dockerfile` to the output path."""

    def generate_service_code(self, service: Any, output_path: str) -> None:
        """
        Generates the Flask server codebase for a specific service.

        This function creates the app.py, Dockerfile, and requirements.txt, enabling 
        the service to receive HTTP requests, execute its stage, and serialize artifacts.

        Parameters:
            service (Service): The service object containing the execution logic.
            output_path (str): The directory where the Flask app files will be written.

        Returns:
            None
        """

        os.makedirs(output_path, exist_ok=True)

        app_py_path = os.path.join(output_path, "app.py")
        svc_id_val = getattr(service, "service_id", "svc")
        port_val = getattr(service, "port", 5000)
        content = APP_PY_TEMPLATE.replace("{svc_id}", svc_id_val).replace("{port}", str(port_val))
        with open(app_py_path, "w", encoding="utf-8") as f:
            f.write(content)

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

        local_names = set()
        try:
            for entry in os.listdir(output_path):
                if entry.endswith(".py"):
                    local_names.add(entry[:-3])
                elif os.path.isdir(os.path.join(output_path, entry)):
                    local_names.add(entry)
        except Exception:
            local_names = set()

        global_mls_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "mls_lib", "mls_lib"))

        req_roots = {orig: orig.split(".")[0] for orig in norm_reqs}

        initial_mls_local = set()
        for root in set(req_roots.values()):
            if os.path.isdir(os.path.join(global_mls_root, root)) or os.path.isfile(os.path.join(global_mls_root, root + ".py")):
                initial_mls_local.add(root)

        initial_mls_local.add("orchestration")

        mls_local_deps = _collect_transitive_mls_deps(initial_mls_local, global_mls_root)

        if mls_local_deps:
            _copy_mls_subpackages(mls_local_deps, global_mls_root, output_path)

        try:
            for entry in os.listdir(os.path.join(output_path, "mls_lib")):
                local_names.add(entry)
        except Exception:
            pass

        externals = _collect_external_imports(output_path, excluded_roots=mls_local_deps | {"mls_lib"}, local_names=local_names)

        filtered_reqs = []
        for orig in norm_reqs:
            root = req_roots.get(orig, orig)
            root_mapped = {"yaml": "pyyaml", "sklearn": "scikit-learn"}.get(root, root)
            if root in mls_local_deps or root in local_names:
                continue
            if root_mapped in local_names:
                continue
            filtered_reqs.append(root_mapped)

        for ext in sorted(externals):
            if ext not in filtered_reqs:
                filtered_reqs.append(ext)

        mvp_reqs = ["flask", "requests", "pyyaml", "joblib"]
        all_reqs = sorted(set(filtered_reqs) | set(mvp_reqs))

        req_path = os.path.join(output_path, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as req_f:
            req_f.write("\n".join(all_reqs) + "\n")

        system_pkgs = []
        needs_opencv = any(x in externals for x in ("ultralytics", "cv2", "opencv-python"))
        needs_ffmpeg = "ultralytics" in externals or "ffmpeg" in externals

        if needs_opencv:
            system_pkgs += [
                "libxcb1", "libgl1", "libglib2.0-0", "libxrender1",
                "libxext6", "libsm6", "libx11-6", "libxrandr2"
            ]
        if needs_ffmpeg:
            system_pkgs.append("ffmpeg")

        system_pkgs = sorted(set(system_pkgs))

        if system_pkgs:
            apt_line = (
                "RUN apt-get update && "
                "apt-get install -y --no-install-recommends " + " ".join(system_pkgs) + " && "
                "rm -rf /var/lib/apt/lists/*"
            )
        else:
            apt_line = ""

        dockerfile_content = f"""FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
ENV YOLO_CONFIG_DIR=/tmp/Ultralytics
WORKDIR /app
{apt_line}
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
"""
        dockerfile_path = os.path.join(output_path, "Dockerfile")
        with open(dockerfile_path, "w", encoding="utf-8") as df:
            df.write(dockerfile_content)

        svc_name = getattr(service, "service_id", "unknown")
        openapi_content = OPENAPI_YAML_TEMPLATE.format(svc_name=svc_name)
        with open(os.path.join(output_path, "openapi.yaml"), "w", encoding="utf-8") as f:
            f.write(openapi_content)

        readme_path = os.path.join(output_path, "README.generated")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"Generated Flask app for service: {getattr(service, 'service_id', str(service))}\n")