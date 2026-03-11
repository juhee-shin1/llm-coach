import os, yaml, subprocess
from app.core.config import settings

def list_scenarios():
    base = settings.scenarios_dir
    result = []
    if not os.path.isdir(base):
        return result
    for name in sorted(os.listdir(base)):
        meta_path = os.path.join(base, name, "meta.yaml")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                result.append(yaml.safe_load(f))
    return result

def get_scenario_meta(scenario_id):
    for s in list_scenarios():
        if s.get("id") == scenario_id:
            return s
    return None

def _apply_path(scenario_id):
    base = settings.scenarios_dir
    for name in os.listdir(base):
        meta_path = os.path.join(base, name, "meta.yaml")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                meta = yaml.safe_load(f)
            if meta.get("id") == scenario_id:
                return os.path.join(base, name, "apply.yaml")
    return None

def apply_scenario(scenario_id):
    path = _apply_path(scenario_id)
    if not path:
        return False, "apply.yaml not found"
    proc = subprocess.run(["kubectl","apply","-f",path], capture_output=True, text=True, timeout=30)
    return proc.returncode == 0, proc.stdout + proc.stderr

def delete_scenario(scenario_id):
    path = _apply_path(scenario_id)
    if not path:
        return False, "apply.yaml not found"
    proc = subprocess.run(["kubectl","delete","-f",path,"--ignore-not-found"], capture_output=True, text=True, timeout=30)
    return proc.returncode == 0, proc.stdout + proc.stderr
