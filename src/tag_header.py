import argparse
from .spec_repo import load_spec
from .logging_utils import setup_logger, jlog


def render_header(spec: dict) -> str:
    parts: list[str] = [spec.get("multiplicity", "[1-1]")]
    group_tags = " ".join(f"[{group['id']}]" for group in spec.get("groups", []))
    if group_tags:
        parts.append(group_tags)
    entities = " - ".join(spec.get("entities", []))
    if entities:
        parts.append(f"// [ENTIDADES] - {entities}")

    lines: list[str] = [" ".join(parts).strip()]

    for group in spec.get("groups", []):
        label = group.get("label", "")
        if label.lower().startswith("qualificação"):
            entity = label.split()[-1]
            lines.append(f"[{group['id']}] // [ENTIDADE] - {entity}")
        else:
            lines.append(f"[{group['id']}] // [{label.upper().replace(' ', '_')}]")
        for field in group.get("fields", []):
            placeholder = field.get("placeholder", "")
            lines.append(f"[CAMPO] - [{field['name']}]  ::  {placeholder}")
        lines.append("")

    return "\n".join(line for line in lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--out", default=None, help="Opcional: caminho de saída .md")
    args = parser.parse_args()

    logger = setup_logger()
    spec = load_spec(args.slug)
    jlog(logger, "INFO", "HEADER_RENDER_START", slug=args.slug)
    markdown = render_header(spec)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handler:
            handler.write(markdown)
        jlog(logger, "INFO", "HEADER_SAVED", path=args.out)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
