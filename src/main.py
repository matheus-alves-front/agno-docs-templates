import argparse, os, json
from .config import settings
from . import parser as myparser
from . import spec_repo
from .collector import collect_for_spec
from .filler import fill_docx

def cmd_index():
    files = [f for f in os.listdir(settings.TEMPLATES) if f.lower().endswith(".docx")]
    if not files:
        print("Nenhum .docx encontrado em ./templates")
        return
    for fn in sorted(files):
        path = os.path.join(settings.TEMPLATES, fn)
        spec = myparser.build_spec_from_docx(path)
        out = spec_repo.save_spec(spec)
        print(f"[OK] {fn} -> spec: {out}")

def cmd_list():
    slugs = spec_repo.list_specs()
    if not slugs:
        print("Nenhum spec em ./specs. Rode: python -m src.main index")
        return
    for i, s in enumerate(slugs, 1):
        print(f"{i}. {s}")

def choose_slug():
    slugs = spec_repo.list_specs()
    if not slugs:
        print("Nenhum spec. Rode 'index' primeiro.")
        return None
    for i, s in enumerate(slugs, 1):
        print(f"{i}. {s}")
    sel = input("Escolha o número do template: ").strip()
    if not sel.isdigit():
        return None
    idx = int(sel) - 1
    if 0 <= idx < len(slugs):
        return slugs[idx]
    return None

def cmd_run():
    slug = choose_slug()
    if not slug:
        print("Seleção inválida.")
        return
    spec = spec_repo.load_spec(slug)
    mapping = collect_for_spec(spec, use_llm=False)
    template_path = os.path.join(settings.TEMPLATES, spec["source"])
    out = fill_docx(template_path, mapping, out_name=f"{slug}_preenchido.docx")
    print(f"[OK] Documento gerado em: {out}")

def cmd_fill(slug: str, data_path: str):
    spec = spec_repo.load_spec(slug)
    template_path = os.path.join(settings.TEMPLATES, spec["source"])
    with open(data_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    out = fill_docx(template_path, mapping, out_name=f"{slug}_preenchido.docx")
    print(f"[OK] Documento gerado em: {out}")

def main():
    import sys
    if __package__ is None and not hasattr(sys, 'frozen'):
        # allow "python src/main.py" too
        sys.path.append(os.path.dirname(__file__))

    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("index")
    sub.add_parser("list")
    sub.add_parser("run")

    pfill = sub.add_parser("fill")
    pfill.add_argument("--slug", required=True)
    pfill.add_argument("--data", required=True)

    args = ap.parse_args()
    if args.cmd == "index":
        cmd_index()
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "run":
        cmd_run()
    elif args.cmd == "fill":
        cmd_fill(args.slug, args.data)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
