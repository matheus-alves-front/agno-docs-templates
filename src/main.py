import argparse
import json
import os
from .config import settings
from . import parser as myparser
from . import spec_repo
from .collector import collect_for_spec
from .filler import fill_docx
from .logging_utils import setup_logger, jlog


def cmd_index() -> None:
    logger = setup_logger()
    files = [name for name in os.listdir(settings.TEMPLATES) if name.lower().endswith(".docx")]
    if not files:
        print("Nenhum .docx encontrado em ./templates")
        return
    for filename in sorted(files):
        path = os.path.join(settings.TEMPLATES, filename)
        spec = myparser.build_spec_from_docx(path)
        out_path = spec_repo.save_spec(spec)
        jlog(logger, "INFO", "INDEX_SAVE_SPEC", file=filename, spec_path=out_path)
        print(f"[OK] {filename} -> spec: {out_path}")


def cmd_list() -> None:
    slugs = spec_repo.list_specs()
    if not slugs:
        print("Nenhum spec em ./specs. Rode: python -m src.main index")
        return
    for idx, slug in enumerate(slugs, 1):
        print(f"{idx}. {slug}")


def choose_slug() -> str | None:
    slugs = spec_repo.list_specs()
    if not slugs:
        print("Nenhum spec. Rode 'index' primeiro.")
        return None
    for idx, slug in enumerate(slugs, 1):
        print(f"{idx}. {slug}")
    selection = input("Escolha o número do template: ").strip()
    if not selection.isdigit():
        return None
    index = int(selection) - 1
    if 0 <= index < len(slugs):
        return slugs[index]
    return None


def cmd_run() -> None:
    logger = setup_logger()
    slug = choose_slug()
    if not slug:
        print("Seleção inválida.")
        return
    spec = spec_repo.load_spec(slug)
    jlog(
        logger,
        "INFO",
        "RUN_LOAD_SPEC",
        slug=slug,
        multiplicity=spec.get("multiplicity"),
        entities=spec.get("entities"),
        casais=(spec.get("meta") or {}).get("casais"),
    )
    mapping = collect_for_spec(spec, use_llm=False)
    template_path = os.path.join(settings.TEMPLATES, spec["source"])
    out_path = os.path.join(settings.RESULTS, f"{slug}_preenchido.docx")
    jlog(logger, "INFO", "FILL_START", template=template_path, out=out_path)
    final_path = fill_docx(template_path, mapping, out_name=f"{slug}_preenchido.docx")
    jlog(logger, "INFO", "FILL_DONE", out=final_path)
    print(f"[OK] Documento gerado em: {final_path}")


def cmd_fill(slug: str, data_path: str) -> None:
    logger = setup_logger()
    spec = spec_repo.load_spec(slug)
    template_path = os.path.join(settings.TEMPLATES, spec["source"])
    with open(data_path, "r", encoding="utf-8") as handler:
        mapping = json.load(handler)
    out_path = os.path.join(settings.RESULTS, f"{slug}_preenchido.docx")
    jlog(logger, "INFO", "FILL_START", template=template_path, out=out_path)
    final_path = fill_docx(template_path, mapping, out_name=f"{slug}_preenchido.docx")
    jlog(logger, "INFO", "FILL_DONE", out=final_path)
    print(f"[OK] Documento gerado em: {final_path}")


def main() -> None:
    import sys

    if __package__ is None and not hasattr(sys, "frozen"):
        sys.path.append(os.path.dirname(__file__))

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("index")
    sub.add_parser("list")
    sub.add_parser("run")

    fill_parser = sub.add_parser("fill")
    fill_parser.add_argument("--slug", required=True)
    fill_parser.add_argument("--data", required=True)

    args = parser.parse_args()
    if args.cmd == "index":
        cmd_index()
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "run":
        cmd_run()
    elif args.cmd == "fill":
        cmd_fill(args.slug, args.data)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
