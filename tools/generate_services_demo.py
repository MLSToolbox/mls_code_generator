#!/usr/bin/env python3
"""
Script de testing, no va a dev
Genera tres formats a ./out:
  - monolith/
  - services_one/        (tot en un unic servei)
  - services_per_stage/  (un servei per cada step)

Aquest script usa:
  - tests/files/mls_editor_single_service.json  -> services_one (single service)
  - tests/files/mls_editor_multi_service.json   -> services_per_stage (per-step services)
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from shutil import move, rmtree

# localitza src
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = None
SRC_PATH = None
for p in [THIS_FILE] + list(THIS_FILE.parents):
    candidate = p / "src"
    if (candidate / "mls_code_generator").exists():
        REPO_ROOT = p
        SRC_PATH = candidate
        break
if SRC_PATH is None:
    print("Error: no s'ha trobat src/mls_code_generator", file=sys.stderr)
    sys.exit(1)
sys.path.insert(0, str(SRC_PATH))

from mls_code_generator.configuration_loader import ConfigLoader
from mls_code_generator.pipeline_loader import PipelineLoader
from mls_code_generator.types import Pipeline
from mls_code_generator.types.service import Service
from mls_code_generator.code_generator import CodeGenerator

NODES = REPO_ROOT / "src" / "mls_code_generator" / "tests" / "files" / "nodes.json"
PIPE_MULTI = REPO_ROOT / "src" / "mls_code_generator" / "tests" / "files" / "mls_editor_multi_service.json"
PIPE_SINGLE = REPO_ROOT / "src" / "mls_code_generator" / "tests" / "files" / "mls_editor_single_service.json"

OUT = REPO_ROOT / "out"

def load_pipeline_from_file(code_path: Path) -> Pipeline:
    with open(NODES, "r", encoding="utf-8") as f:
        nodes = json.load(f)["nodes"]
    with open(code_path, "r", encoding="utf-8") as f:
        code_json = json.load(f)
    node_conf = ConfigLoader(content=nodes)
    loader = PipelineLoader(code_json, node_conf)
    p = Pipeline()
    p.load_pipeline(loader)
    return p

def ensure_clean(dirpath: Path):

    import shutil
    import time

    if dirpath.exists():
        for attempt in range(6):
            try:
                shutil.rmtree(dirpath)
                break
            except PermissionError as e:
                print(f"[warn] rmtree failed (attempt {attempt+1}/6): {e}")
                time.sleep(1)
            except Exception as e:
                print(f"[warn] rmtree failed (attempt {attempt+1}/6): {e}")
                time.sleep(1)
        else:
            print("[warn] rmtree repeatedly failed; attempting per-file cleanup")
            for child in dirpath.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                except Exception as e:
                    print(f"[warn] could not remove {child}: {e}")
            try:
                dirpath.rmdir()
            except Exception as e:
                print(f"[error] could not remove dir {dirpath}: {e}")
                raise

    dirpath.mkdir(parents=True, exist_ok=True)

def move_inner_services_up(base_dir: Path):
    inner = base_dir / "services"
    if inner.exists() and inner.is_dir():
        for child in inner.iterdir():
            target = base_dir / child.name
            if target.exists():
                if target.is_dir():
                    rmtree(target)
                else:
                    target.unlink()
            move(str(child), str(base_dir))
        if inner.exists():
            rmtree(inner)

def main() -> None:
    ensure_clean(OUT)

    # 1) Monolith (usa el multi JSON igual que abans)
    print("Generating monolith...")
    p_mon = load_pipeline_from_file(PIPE_MULTI)
    p_mon.generation_mode = "monolith"
    cg_mon = CodeGenerator()
    cg_mon.output_dir = None
    cg_mon.generate_code(p_mon)
    mon_dir = OUT / "monolith"
    mon_dir.mkdir(parents=True, exist_ok=True)
    for name, src in cg_mon.modules.items():
        if not name.startswith("service_"):
            with open(mon_dir / f"{name}.py", "w", encoding="utf-8") as f:
                f.write(src)

    # 2) Services_one: TOT els steps dins UN servei -> usar PIPE_SINGLE
    print("Generating services (single service containing all steps)...")
    p_all = load_pipeline_from_file(PIPE_SINGLE)
    svc = Service("all")
    for step in list(p_all.steps.values()):
        svc.add_step(step)
    p_all.services = {"all": svc}
    p_all.generation_mode = "services"
    cg_all = CodeGenerator()
    out_all = OUT / "services_one"
    ensure_clean(out_all)
    cg_all.output_dir = str(out_all)
    cg_all.generate_code(p_all)

    for name, src in cg_all.modules.items():
        if not name.startswith("service_"):
            with open(out_all / f"{name}.py", "w", encoding="utf-8") as f:
                f.write(src)

    move_inner_services_up(out_all)

    # 3) Services_per_stage: un servei per cada step -> usar PIPE_MULTI
    print("Generating services (one service per step)...")
    p_stage = load_pipeline_from_file(PIPE_MULTI)
    services_map = {}
    for sid, step in p_stage.steps.items():
        if sid == "root":
            continue
        svc_name = getattr(step, "name", None) or getattr(step, "r_name", None) or sid
        s = Service(svc_name)
        s.add_step(step)
        services_map[svc_name] = s
    p_stage.services = services_map

    p_stage.generation_mode = "services"
    cg_stage = CodeGenerator()
    out_stage = OUT / "services_per_stage"
    ensure_clean(out_stage)
    cg_stage.output_dir = str(out_stage)
    cg_stage.generate_code(p_stage)

    for name, src in cg_stage.modules.items():
        if not name.startswith("service_"):
            with open(out_stage / f"{name}.py", "w", encoding="utf-8") as f:
                f.write(src)

    move_inner_services_up(out_stage)

    print("Done. Inspect:", OUT)
    for d in sorted(OUT.iterdir()):
        print("-", d.name)

if __name__ == "__main__":
    main()