
# RUN.md — Como rodar a AI (sem WhatsApp)

## Requisitos
- Python 3.11+
- `pip install -r requirements.txt`
- (Opcional) `agno` + `ollama` se quiser plugar LLM mais tarde.

## Pastas
- `templates/` — coloque aqui seus `.docx`
- `specs/` — será populada após `index`
- `results/` — saídas preenchidas

## Comandos

### 1) Indexar templates
Gera um *TemplateSpec* (`specs/<slug>.json`) por `.docx` encontrado em `templates/`:
```bash
python -m src.main index
```

Isso imprime logs do tipo:
```
INFO INDEX_START file=[#002]_PROC_P_Geral_PF_PF_V_1.docx
INFO INDEX_PLACEHOLDERS file=... count=48
INFO INDEX_ENTITIES file=... entities=['OUTORGANTE','OUTORGADO','GLOBAL']
INFO INDEX_MULTIPLICITY file=... multiplicity='[V-1]' casais=false
INFO INDEX_SAVE_SPEC file=... spec_path=specs/[#002]_PROC_P_Geral_PF_PF_V_1.json
```

### 2) Rodar a coleta e preencher
Lista os templates, pergunta quem é “V” e quantos, faz a coleta e preenche o documento:
```bash
python -m src.main run
```

Fluxo esperado (exemplo):
```
1. [#001]_PROC_P_Geral_PF_PF_1_1
2. [#002]_PROC_P_Geral_PF_PF_V_1
...
Escolha o número do template: 2

[info] Multiplicidade: [V-1] | Casais: False
Quais entidades são 'V'? Separe por vírgula. Opções: OUTORGADO, OUTORGANTE
> OUTORGADO
Quantos registros para 'OUTORGADO'? [default: 1]
> 2

=== G1 :: Qualificação OUTORGADO ===
NOME (OUTORGADO) #1
> João da Silva
CPF (OUTORGADO) #1  [CPF no formato 999.999.999-99]
> 123.456.789-00
...
NOME (OUTORGADO) #2
> Maria Souza
CPF (OUTORGADO) #2  [CPF no formato 999.999.999-99]
> 987.654.321-00

=== G2 :: Qualificação OUTORGANTE ===
NOME (OUTORGANTE) #1
> Escritório XYZ Ltda
CNPJ (OUTORGANTE) #1  [CNPJ no formato 99.999.999/9999-99]
> 12.345.678/0001-99

=== G3 :: Dados do Ato ===
DIA_EXTENSO (GLOBAL)
> trinta
...
[OK] Documento gerado em: results/[#002]_PROC_P_Geral_PF_PF_V_1_preenchido.docx
```

### 3) Preencher com JSON
Se você já tem os valores prontos, pode preencher direto:
```bash
python -m src.main fill --slug "[#002]_PROC_P_Geral_PF_PF_V_1" --data dados.json
```

**`dados.json`** precisa ser `{ "{PLACEHOLDER}": "valor" }`, por exemplo:
```json
{
  "{NOME_OUTORGADO}": "João da Silva",
  "{CPF_OUTORGADO}": "123.456.789-00",
  "{DIA_EXTENSO}": "trinta"
}
```

## Dicas
- Se o template tem `OU_CASAIS` no nome, o `run` sugere **2** como quantidade padrão para entidades “V”.
- Se o DOCX não tiver `{BASE_ENTIDADE_2}` e você pedir 2, o índice 2 será ignorado **com log de aviso**.
- Verifique sempre os logs — eles mostram cada mapeamento realizado (ou ignorado).

## Problemas comuns
- **Nada indexado**: verifique `templates/` e se há placeholders `{...}`.
- **Campos faltando no resultado**: provavelmente o DOCX não tem placeholder numerado para índices >1. Cheque `RUN_MAP_KEY_WARN` no log.
- **Validação travando**: revise o formato (CPF, CNPJ, DATA, UF, CEP). A dica aparece ao lado do prompt.