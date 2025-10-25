from typing import List, Dict, Any
from docx import Document
import re, os
from rapidfuzz import fuzz

PLACEHOLDER_RE = re.compile(r"\{([A-Z0-9_]+)(?::([^}]+))?\}")

ENTITY_SUFFIXES = {
    "OUTORGANTE","OUTORGADO","COMPRADOR","VENDEDOR","DOADOR","DONATARIO",
    "PF","PJ","DEVEDOR","CREDOR","OUTORGADA","OUTORGANTES","OUTORGADOS",
    "COMPRADORA","VENDEDORA"
}

def read_docx_placeholders(path: str) -> Dict[str, Any]:
    doc = Document(path)

    def iter_texts():
        for p in doc.paragraphs:
            t = p.text.strip()
            if t: yield t
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    t = cell.text.strip()
                    if t: yield t

    texts = list(iter_texts())
    placeholders = []
    titles = []
    all_names = []

    for t in texts:
        for m in PLACEHOLDER_RE.finditer(t):
            name = m.group(1)
            placeholders.append({"raw": m.group(0), "name": name, "hint": m.group(2) or ""})
            all_names.append(name)

        up = t.upper()
        if (t.endswith(":") or up.isupper()) and len(t) < 120:
            titles.append(t.strip())

    return {"texts": texts, "placeholders": placeholders, "titles": titles, "all_names": all_names}

def infer_multiplicity_from_filename(fname: str) -> str:
    base = os.path.basename(fname)
    if "_V_V" in base: return "[V-V]"
    if "_V_1" in base: return "[V-1]"
    if "_1_V" in base: return "[1-V]"
    return "[1-1]"

def build_spec_from_docx(path: str) -> Dict[str, Any]:
    data = read_docx_placeholders(path)
    placeholders = data["placeholders"]
    all_names = data["all_names"]

    ents = set()
    fields = []
    for ph in placeholders:
        name = ph["name"]
        parts = name.split("_")
        ent = None
        base = name
        if len(parts) >= 2:
            tail = parts[-1]
            # trata nomes já numerados: ..._<ENTIDADE>_<idx>
            if len(parts) >= 3 and parts[-2] in ENTITY_SUFFIXES and parts[-1].isdigit():
                ent = parts[-2]
                base = "_".join(parts[:-2])  # remove _ENTIDADE_<idx>
            elif tail in ENTITY_SUFFIXES:
                ent = tail
                base = "_".join(parts[:-1])  # remove _ENTIDADE
        if ent:
            ents.add(ent)

        fields.append({
            "entity": ent or "GLOBAL",
            "name": base,
            "placeholder": ph["raw"]
        })

    # grupos sugeridos: Qualificação por entidade + Global
    groups = []
    gid = 1
    for e in sorted(x for x in ents if x not in {"GLOBAL"}):
        gfields = [f for f in fields if f["entity"] == e]
        if gfields:
            groups.append({"id": f"G{gid}", "label": f"Qualificação {e}", "fields": gfields})
            gid += 1
    gglobals = [f for f in fields if f["entity"] == "GLOBAL"]
    if gglobals:
        groups.append({"id": f"G{gid}", "label": "Dados do Ato", "fields": gglobals})

    spec = {
        "name": os.path.splitext(os.path.basename(path))[0],
        "source": os.path.basename(path),
        "multiplicity": infer_multiplicity_from_filename(path),
        "entities": sorted(list(ents)) or ["PESSOA"],
        "groups": groups,
        "meta": {
            "casais": "_OU_CASAIS" in os.path.basename(path),
        },
        # NOVO: nomes crus de todos os placeholders para o coletor checar variantes numeradas
        "all_placeholders": all_names
    }
    return spec
