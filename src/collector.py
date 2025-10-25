from typing import Dict, Any, List, Tuple
from .validators import guess_validator

def ask(prompt: str, default: str | None = None) -> str:
    if default is not None:
        print(f"{prompt} [default: {default}]")
    else:
        print(prompt)
    v = input("> ").strip()
    return v if v else (default or "")

def choose_entities_v(entities: List[str]) -> List[str]:
    if not entities:
        return []
    if len(entities) == 1:
        # única entidade pode ser 1 ou V; pergunta
        ans = ask(f"A entidade '{entities[0]}' é 'V' (vários)? (s/n)", "n").lower()
        return [entities[0]] if ans.startswith("s") else []
    # lista opções
    print("Quais entidades são 'V' (vários)? Separe por vírgula. Opções:", ", ".join(entities))
    raw = input("> ").strip()
    if not raw:
        return []
    chosen = [x.strip().upper() for x in raw.split(",") if x.strip()]
    chosen = [e for e in chosen if e in entities]
    return chosen

def collect_counts_for_v(v_entities: List[str], casais: bool) -> Dict[str, int]:
    counts = {}
    for e in v_entities:
        default_n = 2 if casais else 1
        while True:
            txt = ask(f"Quantos registros para '{e}'?", str(default_n))
            if txt.isdigit() and int(txt) >= 1:
                counts[e] = int(txt)
                break
            print("Informe um número inteiro >= 1.")
    return counts

def placeholder_variant_exists(all_names: List[str], base: str, entity: str, idx: int) -> bool:
    return f"{base}_{entity}_{idx}" in all_names

def best_placeholder_key(raw_placeholder: str, base: str, entity: str, idx: int, all_names: List[str]) -> str:
    """
    Decide qual chave usar no mapping:
    - Se o DOCX tem {BASE_ENTIDADE_#}, usa esse.
    - Senão, para idx==1 tenta {BASE_ENTIDADE}; demais índices serão ignorados (sem variante).
    """
    # 1) existe numerada?
    numbered = f"{{{base}_{entity}_{idx}}}"
    if f"{base}_{entity}_{idx}" in all_names:
        return numbered
    # 2) fallback para o primeiro: sem índice
    if idx == 1:
        simple = f"{{{base}_{entity}}}"
        return simple
    # 3) não há placeholder para esse índice
    return None  # sinaliza que não dá para preencher esse índice

def collect_for_spec(spec: Dict[str, Any], use_llm: bool = False) -> Dict[str, str]:
    """
    Retorna mapping { "{PLACEHOLDER}": "valor" } já respeitando multiplicidade.
    """
    mapping: Dict[str, str] = {}
    mult = spec.get("multiplicity") or "[1-1]"
    entities = [e for e in spec.get("entities", []) if e != "GLOBAL"]
    casais = bool((spec.get("meta") or {}).get("casais"))
    all_names = spec.get("all_placeholders", [])

    print(f"\nIniciando coleta para: {spec['name']}  | multiplicidade: {mult}")
    print("Dica: pressione Enter para usar o default quando existir.\n")

    # --- 1) Descobrir quem é 'V' e quantos ---
    v_entities: List[str] = []
    if "V" in mult:
        v_entities = choose_entities_v(entities)
        v_counts = collect_counts_for_v(v_entities, casais)
    else:
        v_counts = {}

    # '1' para as demais
    one_counts = {e: 1 for e in entities if e not in v_entities}
    counts = {**one_counts, **v_counts}  # entidade -> quantos

    # --- 2) Loop por grupos/campos ---
    for g in spec.get("groups", []):
        print(f"\n=== {g['id']} :: {g['label']} ===")
        for f in g.get("fields", []):
            entity = f["entity"]
            field_name = f["name"]
            raw_ph = f["placeholder"]

            # Campos globais ignoram multiplicidade
            if entity == "GLOBAL":
                validator, hint = guess_validator(field_name)
                while True:
                    prompt = f"{field_name} (GLOBAL)"
                    if hint: prompt += f"  [{hint}]"
                    val = ask(prompt)
                    if validator(val):
                        mapping[raw_ph] = val
                        break
                    print("Valor inválido. Tente novamente.")
                continue

            n = counts.get(entity, 1)

            # Coletar n vezes
            for idx in range(1, n + 1):
                validator, hint = guess_validator(field_name)
                while True:
                    prompt = f"{field_name} ({entity}) #{idx}"
                    if hint: prompt += f"  [{hint}]"
                    val = ask(prompt)
                    if validator(val):
                        # decidir qual placeholder usar para este índice
                        # detectar base e forma do raw placeholder
                        # pode ser {BASE_ENTIDADE} ou {BASE_ENTIDADE_#}
                        parts = field_name.split("_")
                        base = field_name  # por padrão
                        # base segura: pegar a 'name' já é a BASE
                        base = f["name"]
                        key = best_placeholder_key(raw_placeholder=raw_ph, base=base, entity=entity, idx=idx, all_names=all_names)
                        if key is None:
                            if idx == 1:
                                # fallback extra de segurança
                                mapping[raw_ph] = val
                            else:
                                print(f"[aviso] Não existe placeholder para {base}_{entity}_{idx}. Ignorando este índice.")
                        else:
                            mapping[key] = val
                        break
                    print("Valor inválido. Tente novamente.")

    print("\nColeta concluída.\n")
    return mapping
