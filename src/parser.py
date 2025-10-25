from typing import Dict, Any
from docx import Document
import re
import os
from .logging_utils import setup_logger, jlog

PLACEHOLDER_RE = re.compile(r"\{([A-Z0-9_]+)(?::([^}]+))?\}")
ENTITY_SUFFIXES = {
    "OUTORGANTE",
    "OUTORGADO",
    "COMPRADOR",
    "VENDEDOR",
    "DOADOR",
    "DONATARIO",
    "PF",
    "PJ",
    "DEVEDOR",
    "CREDOR",
    "OUTORGADA",
    "OUTORGANTES",
    "OUTORGADOS",
    "COMPRADORA",
    "VENDEDORA",
}


def read_docx_placeholders(path: str) -> Dict[str, Any]:
    doc = Document(path)
    texts = []

    for paragraph in doc.paragraphs:
        text = (paragraph.text or "").strip()
        if text:
            texts.append(text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = (cell.text or "").strip()
                if text:
                    texts.append(text)

    placeholders, titles, all_names = [], [], []
    for text in texts:
        for match in PLACEHOLDER_RE.finditer(text):
            name = match.group(1)
            placeholders.append({"raw": match.group(0), "name": name, "hint": match.group(2) or ""})
            all_names.append(name)
        upper = text.upper()
        if (text.endswith(":") or upper.isupper()) and len(text) < 120:
            titles.append(text.strip())

    return {"texts": texts, "placeholders": placeholders, "titles": titles, "all_names": all_names}


def infer_multiplicity_from_filename(fname: str) -> str:
    base = os.path.basename(fname)
    if "_V_V" in base:
        return "[V-V]"
    if "_V_1" in base:
        return "[V-1]"
    if "_1_V" in base:
        return "[1-V]"
    return "[1-1]"


def build_spec_from_docx(path: str) -> Dict[str, Any]:
    logger = setup_logger()
    filename = os.path.basename(path)
    jlog(logger, "INFO", "INDEX_START", file=filename)

    data = read_docx_placeholders(path)
    placeholders = data["placeholders"]
    all_names = data["all_names"]
    jlog(logger, "INFO", "INDEX_PLACEHOLDERS", file=filename, count=len(placeholders))

    entities = set()
    fields = []
    for placeholder in placeholders:
        name = placeholder["name"]
        parts = name.split("_")
        entity = None
        base = name
        if len(parts) >= 3 and parts[-2] in ENTITY_SUFFIXES and parts[-1].isdigit():
            entity = parts[-2]
            base = "_".join(parts[:-2])
        elif len(parts) >= 2 and parts[-1] in ENTITY_SUFFIXES:
            entity = parts[-1]
            base = "_".join(parts[:-1])

        if entity:
            entities.add(entity)

        fields.append({"entity": entity or "GLOBAL", "name": base, "placeholder": placeholder["raw"]})

    groups = []
    gid = 1
    for entity in sorted(x for x in entities if x != "GLOBAL"):
        entity_fields = [field for field in fields if field["entity"] == entity]
        if entity_fields:
            groups.append({"id": f"G{gid}", "label": f"Qualificação {entity}", "fields": entity_fields})
            gid += 1
    global_fields = [field for field in fields if field["entity"] == "GLOBAL"]
    if global_fields:
        groups.append({"id": f"G{gid}", "label": "Dados do Ato", "fields": global_fields})

    multiplicity = infer_multiplicity_from_filename(path)
    meta = {"casais": "_OU_CASAIS" in filename}
    spec = {
        "name": os.path.splitext(filename)[0],
        "source": filename,
        "multiplicity": multiplicity,
        "entities": sorted(list(entities)) or [],
        "groups": groups,
        "meta": meta,
        "all_placeholders": all_names,
    }
    entities_payload = list(spec["entities"])
    if global_fields:
        entities_payload.append("GLOBAL")
    jlog(logger, "INFO", "INDEX_ENTITIES", file=filename, entities=entities_payload)
    jlog(logger, "INFO", "INDEX_MULTIPLICITY", file=filename, multiplicity=multiplicity, casais=meta["casais"])

    return spec
