import os, json
from typing import Dict, Any, List
from .config import settings

def spec_path(slug: str) -> str:
    return os.path.join(settings.SPECS, f"{slug}.json")

def save_spec(spec: Dict[str, Any]) -> str:
    slug = spec["name"]
    path = spec_path(slug)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    return path

def load_spec(slug: str) -> Dict[str, Any]:
    with open(spec_path(slug), "r", encoding="utf-8") as f:
        return json.load(f)

def list_specs() -> List[str]:
    return [fn[:-5] for fn in sorted(os.listdir(settings.SPECS)) if fn.endswith(".json")]
