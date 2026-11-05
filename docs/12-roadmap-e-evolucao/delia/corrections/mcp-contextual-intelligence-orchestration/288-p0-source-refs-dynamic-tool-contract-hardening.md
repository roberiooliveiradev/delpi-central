# 288 — DÉLIA · P0/P1: SourceRefs, contratos dinâmicos de tools e generalização real

**DATA:** 2026-11-05
**TASK_ID:** `DELIA-C3-P0-SOURCE-REFS-AND-DYNAMIC-TOOL-CONTRACT-HARDENING-01`
**BASE_HEAD:** `745ae26ae69f4bc51e168e9f21e638bcab02e88c`
**PRODUCTION_DEPLOY:** `NOT_AUTHORIZED`

## 1. SourceRefs — falso residual, proveniência completa

O residual reportado na task anterior era erro de **leitura do contrato
de resposta**, não perda de proveniência. Matriz boundary→cliente:

| BOUNDARY | OWNER | CONTRACT_FIELD | VALUE_PRESENT | VALUE_PROPAGATED | EVIDENCE |
|---|---|---|---|---|---|
| MCP DAVI execute | api-delpi | `outcome.provenance` | YES | YES | provider_invoke ok |
| `_invoke` → `_outcome_attempt` | delia-api | `attempt.provenance.source_refs` | YES | YES | `_provenance` (orchestration.py) |
| `_finalize_agent_collected_attempts` | delia-api | `terminal.provenance` | YES | YES | `return business[0]` / `provenance=last.provenance` |
| `_grounded_read_result` | delia-api | `result.provenance.sources` | YES | YES | handle_interactive_turn.py |
| HTTP response | cliente | `provenance.sources[]` | YES | YES | JSON real capturado |

Contrato emite **identidade do owner** (`source_id=davi`,
`source_system=mcp`, `action_id`, `observed_at`) — proveniência
autoritativa canônica, sem refs fabricadas de código de produto nem de
resposta de modelo. `P0_SOURCE_REFS=PASS` corrigido a partir da leitura
correta do contrato (`provenance.sources`, não `source_refs` top-level).

## 2. Dynamic tool signature — defeitos reais corrigidos

`_capability_tool_signature` (module-level, testável) constrói a
assinatura nativa a partir do `input_schema` do owner:

- **Ordem opcional→obrigatório** (`inspect.Signature` quebraria com
  `POSITIONAL_OR_KEYWORD`): todos os parâmetros derivados do schema são
  `KEYWORD_ONLY` — JSON Schema não tem contrato de ordem e o modelo
  sempre passa named args; `required` é preservado.
- **Nomes inseguros**: `keyword.iskeyword`, não-identificadores e
  denylist (`ctx`, `kwargs`) são descartados — schema MCP é dado externo
  não confiável.
- **`enum` não propagado** (defeito observado: `teo.read` falhava
  `owner_argument_rejected` porque o modelo adivinhava `entity`):
  `enum`/`const` com até 64 opções vira `Literal[...]` → o JSON schema
  entregue ao modelo carrega os valores válidos do owner. Confirmado em
  runtime: `teo.get_context(entity,section)` → SUCCESS.
- Bound: máx. 24 propriedades (coerente com slim_props do catálogo);
  `arguments` permanece como escape hatch opcional apenas quando não
  declarado — o gate revalida contra o schema vivo a cada chamada.

## 3. `candidate_token` — boundary fail-closed preservado

- `validate_arguments` continua negando `ORCHESTRATED_FIELDS` no top
  level (teste existente mantido, sem alteração de semântica).
- O gate extrai `candidate_token` **apenas** para descriptors
  `_is_candidate_bound` (schema do owner declara o campo), valida como
  string bounded (não-vazio, ≤4 KiB), e devolve verbatim ao
  `_invoke_selected` — contrato agent-supplied projetado (doc 256),
  owner valida o token downstream. Não autentica, não autoriza, não
  vira fato.
- Testes: relay positivo (token chega verbatim ao provider), token
  ausente → binding determinístico (sem inventar), vazio/whitespace,
  não-string, oversized, cap não-candidate-bound, outros campos
  orquestrados (`proposal_handle`, `confirmation`, `idempotency_key`,
  `commit_now`), `arguments` não-objeto — todos fail-closed sem call.

## 4. `InvestigationAnswer.schema_version = Literal["1"]`

`const:"1"` no JSON schema — o modelo que emite `"1.0"` recebe retry de
validação nativo em vez de rejeição silenciosa downstream
(`declared_schema_rejected` anterior derrubava refs do declare). Sem
normalização, sem parser paralelo. Consumidores (`!= "1"` no
`_apply_declared_answer`) continuam corretos.

## 5. Matriz de eval real (owner-autorizado, sem mocks)

| CASO | PERGUNTA | CAPS CHAMADAS | RESULT |
|---|---|---|---|
| A | produto 50220013 | davi.discover→execute(code) | PASS — GROUNDED, `CB18BRAN-00368/06/15-3100-0000`, prov.sources |
| B | estrutura 50220013 | davi.execute(code,max_depth) | PASS — GROUNDED, componentes reais root=50220013 |
| C | atas reunião transformômetro | teo.get_context(entity,section), vista.knowledge | PASS — TÉO SUCCESS; resposta via vista |
| D | indicadores dashboard | vista.get_context, vista.knowledge | PARCIAL — VISTA SUCCESS; `vista.read`/`vista.analyze` = `mcp_protocol_error` (owner tv-dashboard) |
| E | "esse mesmo produto" + context | davi.discover, vista.knowledge | PASS — referência resolvida (50220013), GROUNDED |
| F | produto 99999999 | davi.execute | INCONCLUSIVE — owner TEM registro ("PRODUTO UTILIZADO GENERICO"), coverage não vinculou → NON_GROUNDED honesto (sem fabricação) |
| G | "qual é o código do produto?" | — | PASS — clarificação honesta, sem inventar identificador |

## 6. Residuais registrados

- `vista.read`/`vista.analyze` → `mcp_protocol_error` no owner
  tv-dashboard-api (fora do contrato DÉLIA — dependência owner-side).
- Coverage-binding de registro detalhado único (caso F): identificador
  retornado mas não reconhecido pelo `_uncovered_named_identifiers` →
  NON_GROUNDED honesto; candidato a task de coverage.
- `davi.discover` falhou `semantic_tool_invoke_failed` uma vez em E —
  transitória, sem recorrência observada.
- `declared_status_overridden`/`coverage_unknown`: limitações declaradas
  pelo modelo corrigidas pelo acceptor determinístico — honestidade
  preservada.

## 7. Testes e regressão

- 41 testes novos: `test_dynamic_tool_signature.py` (18),
  `test_candidate_token_boundary.py` (13),
  `test_investigation_answer_contract.py` (10).
- Suíte `delia-api` completa: PASS (exit 0).
- Residual search: sem parser/fallback/planner paralelo introduzido;
  diagnósticos tipados (keys apenas) mantidos bounded.

## 8. Aceite

```
P0-1 produto 50220013 = PASS        P0-2 owner match = PASS
P0-3 entregue ao cliente = PASS     P0-4 structured output = PASS
P0-5 proveniência autoritativa = PASS (provenance.sources, sem refs fabricadas)
P0-6 grounding coerente = PASS      P0-7 AuthZ/policy preservados = PASS
P0-8 contratos dinâmicos robustos = PASS (matriz de schemas)
P0-9 testes/regressão = PASS        P0-10 sem legado remanescente = PASS
P1 generalização = PARCIAL — DAVI+TÉO+VISTA executam READ real;
                   vista.read/analyze dependem de fix owner-side
PRODUCTION_DEPLOY = NOT_AUTHORIZED
```
