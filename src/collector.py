from typing import Dict, Any, List
from .validators import guess_validator
from .logging_utils import setup_logger, jlog


def ask(prompt: str, default: str | None = None) -> str:
    if default is not None and default != "":
        print(f"{prompt} [default: {default}]")
    else:
        print(prompt)
    value = input("> ").strip()
    return value if value else (default or "")


def choose_entities_v(entities: List[str]) -> List[str]:
    if not entities:
        return []
    if len(entities) == 1:
        answer = ask(f"A entidade '{entities[0]}' é 'V' (vários)? (s/n)", "n").lower()
        return [entities[0]] if answer.startswith("s") else []
    print("Quais entidades são 'V' (vários)? Separe por vírgula. Opções:", ", ".join(entities))
    raw = input("> ").strip()
    if not raw:
        return []
    chosen = [item.strip().upper() for item in raw.split(",") if item.strip()]
    return [entity for entity in chosen if entity in entities]


def infer_counts_from_spec(spec: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    meta_counts = (spec.get("meta") or {}).get("inferred_counts") or {}
    for entity, value in meta_counts.items():
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            continue
        if ivalue >= 1:
            counts[entity] = max(counts.get(entity, 1), ivalue)

    if not counts:
        entities = set(spec.get("entities", []))
        for name in spec.get("all_placeholders", []):
            parts = name.split("_")
            if len(parts) >= 3 and parts[-2] in entities and parts[-1].isdigit():
                entity = parts[-2]
                try:
                    idx = int(parts[-1])
                except ValueError:
                    continue
                counts[entity] = max(counts.get(entity, 1), idx)
    return counts


def collect_counts_for_v(v_entities: List[str], casais: bool, defaults: Dict[str, int]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entity in v_entities:
        default_n = defaults.get(entity, 0)
        if default_n < 1:
            default_n = 2 if casais else 1
        while True:
            text = ask(f"Quantos registros para '{entity}'?", str(default_n))
            if text.isdigit() and int(text) >= 1:
                counts[entity] = int(text)
                break
            print("Informe um número inteiro >= 1.")
    return counts


def best_placeholder_key(base: str, entity: str, idx: int, all_names: List[str]) -> str | None:
    numbered_name = f"{base}_{entity}_{idx}"
    if numbered_name in all_names:
        return f"{{{numbered_name}}}"
    if idx == 1:
        simple_name = f"{base}_{entity}"
        if simple_name in all_names:
            return f"{{{simple_name}}}"
    return None


def collect_for_spec(spec: Dict[str, Any], use_llm: bool = False) -> Dict[str, str]:
    logger = setup_logger()
    multiplicity = spec.get("multiplicity") or "[1-1]"
    entities = [entity for entity in spec.get("entities", []) if entity != "GLOBAL"]
    casais = bool((spec.get("meta") or {}).get("casais"))
    all_names = spec.get("all_placeholders", [])
    inferred_counts = infer_counts_from_spec(spec)

    print(f"\nIniciando coleta para: {spec['name']}  | multiplicidade: {multiplicity}")

    v_entities: List[str] = []
    if "V" in multiplicity:
        auto_v = sorted([entity for entity, count in inferred_counts.items() if count > 1 and entity in entities])
        if auto_v:
            print("Detectei automaticamente entidades 'V':", ", ".join(auto_v))
            jlog(logger, "INFO", "RUN_CHOOSE_V_AUTO", v_entities=auto_v)
            v_entities.extend(auto_v)
        remaining = [entity for entity in entities if entity not in v_entities]
        if remaining:
            manual_v = choose_entities_v(remaining)
            if manual_v:
                v_entities.extend(entity for entity in manual_v if entity not in v_entities)
                jlog(logger, "INFO", "RUN_CHOOSE_V_MANUAL", v_entities=manual_v)
        jlog(logger, "INFO", "RUN_CHOOSE_V", v_entities=v_entities)
        v_counts = collect_counts_for_v(v_entities, casais, inferred_counts)
    else:
        v_counts = {}

    one_counts = {entity: 1 for entity in entities if entity not in v_entities}
    counts = {**one_counts, **v_counts}
    jlog(logger, "INFO", "RUN_COUNTS", **counts)

    mapping: Dict[str, str] = {}

    for group in spec.get("groups", []):
        print(f"\n=== {group['id']} :: {group['label']} ===")
        for field in group.get("fields", []):
            entity = field["entity"]
            field_name = field["name"]
            placeholder = field["placeholder"]

            if entity == "GLOBAL":
                validator, hint, rule = guess_validator(field_name)
                while True:
                    jlog(
                        logger,
                        "INFO",
                        "RUN_FIELD_PROMPT",
                        group=group["id"],
                        entity="GLOBAL",
                        name=field_name,
                        idx=1,
                    )
                    prompt = f"{field_name} (GLOBAL)"
                    if hint:
                        prompt += f"  [{hint}]"
                    value = ask(prompt)
                    if validator(value):
                        mapping[placeholder] = value
                        jlog(logger, "INFO", "RUN_MAP_KEY", src=f"{field_name}/GLOBAL", to=placeholder)
                        break
                    jlog(
                        logger,
                        "WARN",
                        "RUN_FIELD_VALID_FAIL",
                        entity="GLOBAL",
                        name=field_name,
                        idx=1,
                        value=value,
                        rule=rule,
                    )
                continue

            total = counts.get(entity, 1)
            for idx in range(1, total + 1):
                validator, hint, rule = guess_validator(field_name)
                while True:
                    jlog(
                        logger,
                        "INFO",
                        "RUN_FIELD_PROMPT",
                        group=group["id"],
                        entity=entity,
                        name=field_name,
                        idx=idx,
                    )
                    prompt = f"{field_name} ({entity}) #{idx}"
                    if hint:
                        prompt += f"  [{hint}]"
                    value = ask(prompt)
                    if validator(value):
                        key = best_placeholder_key(base=field_name, entity=entity, idx=idx, all_names=all_names)
                        if key is None:
                            if idx == 1:
                                mapping[placeholder] = value
                                jlog(
                                    logger,
                                    "INFO",
                                    "RUN_MAP_KEY",
                                    src=f"{field_name}/{entity}#{idx}",
                                    to=placeholder,
                                )
                            else:
                                jlog(
                                    logger,
                                    "WARN",
                                    "RUN_MAP_KEY_WARN",
                                    reason="missing_placeholder_variant",
                                    wanted=f"{{{field_name}_{entity}_{idx}}}",
                                    fallback=None,
                                )
                        else:
                            mapping[key] = value
                            jlog(logger, "INFO", "RUN_MAP_KEY", src=f"{field_name}/{entity}#{idx}", to=key)
                        break
                    jlog(
                        logger,
                        "WARN",
                        "RUN_FIELD_VALID_FAIL",
                        entity=entity,
                        name=field_name,
                        idx=idx,
                        value=value,
                        rule=rule,
                    )

    jlog(logger, "INFO", "RUN_MAPPING_SIZE", placeholders=len(mapping))
    return mapping
