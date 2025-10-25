
# instructions.md — Especificação do Agente (sem WhatsApp)

Este documento define **exatamente** o que o agente deve fazer para **indexar**, **reescrever (tags inteligentes)**, **coletar dados** e **preencher** documentos `.docx` do repositório **templates/**, salvando resultados em **results/**. O objetivo é funcionar para **documentos gerais**, com foco nos placeholders existentes e nas regras de multiplicidade (1-1, V-1, 1-V, V-V).

> Tecnologias alvo: Python 3.11+, `python-docx`, `pydantic`, `rapidfuzz`, `python-dotenv`. Sem WhatsApp. Fluxo interativo no console (ou pluggable com LLM depois).

---

## 1) Estrutura de diretórios

- `templates/` — arquivos `.docx` originais (entrada).
- `specs/` — *TemplateSpecs* gerados (JSON), um por `.docx`.
- `results/` — documentos preenchidos (saída).
- `src/` — código do agente.

---

## 2) Conceitos e vocabulário

- **Placeholder**: padrões do tipo `{CHAVE}` ou `{CHAVE_ENTIDADE}` ou `{CHAVE_ENTIDADE_ÍNDICE}` presentes no `.docx`.
- **Entidade**: sufixos que indicam a “pessoa/parte”, por exemplo: `OUTORGANTE`, `OUTORGADO`, `COMPRADOR`, `VENDEDOR`, `DOADOR`, `DONATARIO`, `PF`, `PJ`, etc.
- **Multiplicidade**: relação cardinal entre entidades (1-1, V-1, 1-V, V-V).
  - `[1-1]` — uma entidade de cada lado.
  - `[V-1]` — vários do primeiro lado, um do segundo.
  - `[1-V]` — um do primeiro lado, vários do segundo.
  - `[V-V]` — vários de ambos.
- **GLOBAL**: campos sem entidade (datas, valores gerais, termos fixos) — ex.: `{DIA_EXTENSO}`, `{ANO_NUMERAL}`.

---

## 3) Tags inteligentes (padrão canônico)

### 3.1 Cabeçalho sugerido humano
Ao indexar um `.docx`, o agente deve ser capaz de gerar um cabeçalho de leitura humana como:

```
[V-1]  [G1] [G2] [G3]   // [ENTIDADES] - OUTORGANTE - OUTORGADO
[G1] // [ENTIDADE] - OUTORGANTE
[CAMPO] - [NOME]         :: {NOME_OUTORGANTE}
[CAMPO] - [CPF]          :: {CPF_OUTORGANTE}
...
[G2] // [ENTIDADE] - OUTORGADO
[CAMPO] - [NOME]         :: {NOME_OUTORGADO}
...
[G3] // [DADOS_DO_ATO]
[CAMPO] - [DIA_EXTENSO]  :: {DIA_EXTENSO}
[CAMPO] - [ANO_NUMERAL]  :: {ANO_NUMERAL}
```

> **Obs.:** Este cabeçalho é **derivado** do *TemplateSpec* (JSON) descrito abaixo. Não altera o `.docx`; serve para revisão/QA.

### 3.2 Esquema *TemplateSpec* (JSON máquina)
Cada template terá um JSON com o shape abaixo, salvo em `specs/<slug>.json`:

```jsonc
{
  "name": "NOME_DO_ARQUIVO_SEM_EXT",
  "source": "NOME_DO_ARQUIVO_COM_EXT.docx",
  "multiplicity": "[1-1] | [V-1] | [1-V] | [V-V]",
  "entities": ["OUTORGANTE", "OUTORGADO"],
  "groups": [
    {
      "id": "G1",
      "label": "Qualificação OUTORGANTE",
      "fields": [
        { "entity": "OUTORGANTE", "name": "NOME", "placeholder": "{NOME_OUTORGANTE}" },
        { "entity": "OUTORGANTE", "name": "CPF",  "placeholder": "{CPF_OUTORGANTE}" }
      ]
    },
    {
      "id": "G2",
      "label": "Qualificação OUTORGADO",
      "fields": [
        { "entity": "OUTORGADO", "name": "NOME", "placeholder": "{NOME_OUTORGADO}" }
      ]
    },
    {
      "id": "G3",
      "label": "Dados do Ato",
      "fields": [
        { "entity": "GLOBAL", "name": "DIA_EXTENSO", "placeholder": "{DIA_EXTENSO}" },
        { "entity": "GLOBAL", "name": "ANO_NUMERAL", "placeholder": "{ANO_NUMERAL}" }
      ]
    }
  ],
  "meta": {
    "casais": true
  },
  "all_placeholders": [
    "NOME_OUTORGANTE", "CPF_OUTORGANTE", "NOME_OUTORGADO", "DIA_EXTENSO", "ANO_NUMERAL",
    "NOME_OUTORGADO_1", "NOME_OUTORGADO_2"
  ]
}
```

---

## 4) Indexação (geração do TemplateSpec)

### 4.1 Leitura do `.docx`
- Usar `python-docx` e iterar **parágrafos e células de tabela**.
- Extrair placeholders com regex: `\{([A-Z0-9_]+)(?::([^}]+))?\}`
  - `name` = grupo 1 (ex.: `NOME_OUTORGADO_2`)
  - `hint` = grupo 2 (após `:`), se existir.

### 4.2 Inferência de entidade e base do campo
Para cada `name`:
- `parts = name.split("_")`.
- Casos:
  1. **Numerado**: `BASE_ENTIDADE_ÍNDICE` (`parts[-2]` ∈ ENTIDADES; `parts[-1]` dígito) → `entity = parts[-2]`, `base = "_".join(parts[:-2])`
  2. **Simples**: `BASE_ENTIDADE` (`parts[-1]` ∈ ENTIDADES) → `entity = parts[-1]`, `base = "_".join(parts[:-1])`
  3. **GLOBAL**: caso contrário → `entity = "GLOBAL"`, `base = name`.

### 4.3 Grupos
- Um grupo por entidade: `G1: Qualificação {ENTIDADE}`, …
- Um grupo “Dados do Ato” para `GLOBAL`.
- Campo → `{ "entity": ENTIDADE|GLOBAL, "name": BASE, "placeholder": "{raw}" }`.

### 4.4 Multiplicidade
- Do **nome do arquivo**:
  - `_V_V` → `[V-V]`
  - `_V_1` → `[V-1]`
  - `_1_V` → `[1-V]`
  - senão → `[1-1]`
- Se nome contiver `OU_CASAIS` → `meta.casais = true`.

### 4.5 Salvar Spec
- `specs/<slug>.json`
- Incluir `all_placeholders` (nomes crus sem `{}`) para checagem de variantes numeradas.

---

## 5) Coleta de dados (console)

### 5.1 Quem é “V” e quantos
- Se `multiplicity` contém `"V"`:
  - Mostrar entidades (excluindo `GLOBAL`).
  - Perguntar **quais** são “V” (pode ser 1 ou mais).
  - Perguntar **quantos** para cada “V`. Defaults:
    - `meta.casais == true` → 2
    - senão → 1
- Demais entidades → 1.

### 5.2 Perguntas por grupo/campo
- Iterar `G1..Gn`.
- **GLOBAL**: pergunta única → valida → `mapping["{PLACEHOLDER}"]=valor`.
- **Com entidade**:
  - Para `idx = 1..n` (n = quantidade pedida para aquela entidade):
    - Prompt: `"{BASE} ({ENTIDADE}) #idx"` com dica (quando houver).
    - Validar; em caso de erro, repetir.
    - **Mapeamento da chave**:
      - Se existir `{BASE_ENTIDADE_idx}` (verificando em `all_placeholders`), usar essa.
      - Senão, se `idx == 1`, usar `{BASE_ENTIDADE}`.
      - Senão (idx>1 e inexistente), **ignorar** com **log WARN**.

### 5.3 Saída da coleta
- `mapping: Dict[str, str]` com **as chaves exatas** do DOCX (incluindo `{}`), por exemplo:
  ```json
  {
    "{NOME_OUTORGADO}": "Alice",
    "{NOME_OUTORGADO_2}": "Bob",
    "{DIA_EXTENSO}": "trinta"
  }
  ```

---

## 6) Validações mínimas

- Por nome do campo (BASE, case-insensitive):
  - `CPF` → `999.999.999-99`
  - `CNPJ` → `99.999.999/9999-99`
  - `DATA` / `NASC` → `dd/mm/aaaa`
  - `UF` → 2 letras
  - `CEP` → `99999-999`
  - `EMAIL` → regex comum
  - `TELEFONE` / `CELULAR` / `WHATS` → `+DDDN...` (10–15 dígitos)
- Em erro: mensagem específica e re-prompt.

---

## 7) Preenchimento

- Abrir `.docx` de `templates/`.
- Substituir placeholders em **runs** (parágrafos e tabelas).
- Salvar em `results/<slug>_preenchido.docx`.

---

## 8) Logs detalhados

### 8.1 Níveis
- `INFO` — operações ok
- `WARN` — faltou placeholder numerado, valor ignorado, etc.
- `ERROR` — exceções/erros de IO

### 8.2 Eventos
- **INDEX_START** `{"file": "<nome.docx>"}`
- **INDEX_PLACEHOLDERS** `{"file": "...", "count": 57}`
- **INDEX_ENTITIES** `{"file": "...", "entities": ["OUTORGANTE","OUTORGADO","GLOBAL"]}`
- **INDEX_MULTIPLICITY** `{"file": "...", "multiplicity": "[V-1]", "casais": true}`
- **INDEX_SAVE_SPEC** `{"file": "...", "spec_path": "specs/<slug>.json"}`

- **RUN_LOAD_SPEC** `{"slug": "...", "multiplicity": "...", "entities": [...]}`
- **RUN_CHOOSE_V** `{"v_entities": ["OUTORGADO"]}`
- **RUN_COUNTS** `{"OUTORGADO": 2, "OUTORGANTE": 1}`
- **RUN_FIELD_PROMPT** `{"group":"G1","entity":"OUTORGADO","name":"NOME","idx":1}`
- **RUN_FIELD_VALID_FAIL** `{"entity":"OUTORGADO","name":"CPF","idx":1,"value":"...","rule":"cpf"}`
- **RUN_MAP_KEY** `{"from":"NOME_OUTORGADO/#1","to":"{NOME_OUTORGADO}"}`
- **RUN_MAP_KEY_WARN** `{"reason":"missing_placeholder_variant","wanted":"{NOME_OUTORGADO_2}","fallback":null}`
- **RUN_MAPPING_SIZE** `{"placeholders": 42}`
- **FILL_START** `{"template":"templates/<file>","out":"results/<slug>_preenchido.docx"}`
- **FILL_DONE** `{"out":"results/<slug>_preenchido.docx"}`

> Formato recomendado: uma linha JSON por log (fácil de grepar).

---

## 9) Casos de borda

- `OU_CASAIS` → default 2 para entidades “V”.
- Sem entidades detectadas → tudo em `GLOBAL`.
- Se o documento possui `BASE_ENTIDADE_1` **mas não** `BASE_ENTIDADE` simples: use **sempre** a forma numerada.
- Se a forma simples e numerada coexistirem para `idx==1`, **prefira a numerada** quando estiver presente no `all_placeholders`.

---

## 10) Critérios de aceitação

- `index` cria um JSON por docx com os campos descritos e `all_placeholders` preenchido.
- `run` pergunta **quem é V** (se aplicável) e **quantos**, respeitando `OU_CASAIS`.
- `run` mapeia corretamente: usa `{BASE_ENTIDADE_idx}` quando existir; caso contrário `{BASE_ENTIDADE}` somente para `idx==1`; índices excedentes geram `WARN`.
- `fill` gera `results/<slug>_preenchido.docx` com substitutions.
- Logs emitidos conforme a seção 8.