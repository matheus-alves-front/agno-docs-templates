## Indexação
- [ ] `python -m src.main index` cria `specs/<slug>.json` para todos os `.docx`.
- [ ] Cada spec contém `all_placeholders` com nomes crus (sem `{}`).

## Multiplicidade
- [ ] Em um template `[V-1]` ou `[1-V]` ou `[V-V]`, o `run` pergunta:
  - [ ] Quais entidades são “V”.
  - [ ] Quantos registros para cada “V” (default=2 se `casais`).
- [ ] Para placeholders numerados (`{BASE_ENTIDADE_1}`, `{BASE_ENTIDADE_2}...`), o mapeamento cobre **todos** os índices informados.
- [ ] Se o DOCX **não** possui `{..._2}` e foi informado `2`, o índice 2 é ignorado **com log WARN**.

## Validações
- [ ] CPF/CNPJ/DATA/UF/CEP/EMAIL/TELEFONE: ao errar, o prompt reaparece com a dica.

## Preenchimento
- [ ] Gera `results/<slug>_preenchido.docx`.
- [ ] Campos substituídos preservando formatação do documento.

## Logs
- [ ] INDEX_* e RUN_* e FILL_* aparecem conforme o `instructions.md` (seção 8.2).
