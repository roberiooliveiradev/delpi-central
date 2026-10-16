# 87 — Rework R2 (decisão L1 + fallback + probes versionados) — Relatório de execução

**Status:** `REWORK_EXECUTED — CANDIDATE_FOR_INDEPENDENT_REVIEW / RUNTIME_NOT_AUTHORIZED`
**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R2`
**BASE_HEAD (reanchor real):** `5997604835a030a6873840178a31533d77bcf4b3` (= SHA de preparação = origin/main no commit)
**CP:** `CP-333` — `PLANNED_NOT_PASS` (inalterado)
**Tipo:** contrato/testes/documentação — **zero diff de runtime de produção**

> B2 = Markdown conversacional (spec 82/83), não `C3-STAGE-02-B2` (PREPARE/ACT).

## 1. Decisão L1 (vinculante, Product Master)

`LINK_SOURCE_TYPED = L1_APPROVED_CONDITIONAL` — registrada na spec 83 §0.4 e reconciliada na proposta 84 §2.4/§6.

Condições por link emitido: owner+fonte autoritativa identificáveis; campo e semântica publicados em contrato; permissão de divulgação; URL/esquema validados; política de navegação interna/externa; Core AuthZ/Domain como autoridade final; negativos para URL inventada/expirada/sem permissão. **Proibido** promover `url`/`href`/`link`/`*_url` genéricos por nome ou presença. L2/L3 não aprovadas. Sem binding governado → zero link navegável; **D1/D6/D7 não revogadas**.

## 2. R2-01 — Inventário de contratos de link (resultado factual)

| Candidato | Resultado |
|---|---|
| `api-delpi` `mural_acessos` link `url` | **Contrato governado real** — owner `app/domain/services/mural_acessos/link_url.py`; `normalize_link_url` exige `http(s)://`+netloc+max len no write; semântica publicada (destino de atalho). Binding capability→`SpecialistOutcome.structured`→conversa **não provado** |
| `api-delpi` `url` em args de capability | Proibido — `_TRANSPORT_FORBIDDEN` (`argument_validator.py`) |
| Provenance/SourceRef/WorkspaceEntityRef/owner_hint | Não são fontes (URL-free por design) |
| Demais bindings owner→capability com link tipado | `TO_INVENTORY` |

`LINK_L1_CONTRACT = SPECIFIED`; `LINK_L1_CAPABILITY_BINDINGS = TO_INVENTORY` — nenhum binding concreto demonstrado, portanto **nenhum link navegável será emitido**; política e consumidor permanecem armados. Não foi fabricado contrato para declarar conclusão.

## 3. R2-02 — Fallback `presentation.v2` corrigido

Doc 84 §2.5 reescrito como tabela de decisão de **quatro estados distintos**: `render_legacy` (versão desconhecida/ausente **e** legado provadamente seguro — legado validado antes do fallback), `neutral_error` (v2 estruturalmente inválido **ou** versão desconhecida com legado inseguro — fail-closed, sem downgrade), `inert_text` (falha de parse sobre conteúdo já admitido), `render_v2`. Executado como probe de política: 8 casos PASS.

## 4. R2-03 — Exposição da chave `token`

**Provado:** `token` (canonical key) não consta de `_SENSITIVE_KEY_NAMES` — valor `token:` renderizado sem redação em `render_specialist_outcome`. RED probe versionado: `test_render_specialist_outcome_fidelity.py::test_bare_token_key_is_redacted` = **XFAIL(strict)** — vira XPASS-FAIL quando corrigido (não apodrece).

**Brief bounded de correção (não aplicada — requer autorização específica de runtime):**

- Owner legítimo: `delia-api/app/application/capability_provision/orchestration.py` `_SENSITIVE_KEY_NAMES` (~L1861).
- Diff mínimo: adicionar `"token"` ao frozenset (1 linha).
- Efeito: qualquer chave `token`/`Token`/`token-*`/`token_x` em `structured` → `[REDACTED]`; chave permanece, valor some.
- Trade-off aceitável: campo de negócio literalmente `token` seria redigido — fail-closed correto; semântica preservada pela chave.
- Consequência para B2: **a projeção `structured`→`markdown_safe` fica bloqueada** até a correção ou isolamento provado — categoria A restrita a shapes sem chaves de risco.

## 5. R2-04 — Testes reproduzíveis versionados

| Arquivo | Owner | Conteúdo | Resultado |
|---|---|---|---|
| `delia-api/tests/test_presentation_v2_proposal.py` | delia-api | 18 casos schema (4 pos + 14 neg) via avaliador subset stdlib **+** 8 casos da tabela de decisão de fallback (probe de política) | **37 PASS** |
| `delia-api/tests/test_render_specialist_outcome_fidelity.py` | delia-api | 8 testes caracterização do seam existente + RED `token` | **7 PASS + 1 XFAIL(strict)** |
| `plugins/plugin-ui/src/components/markdown/conversationMarkdownLexer.probe.test.ts` | plugin-ui | 26 casos adversariais do `marked.lexer` (html/script/image/table/mermaid/checkbox/nesting/del/autolink + 13 hrefs rejeitados + 5 aceitos pela política proposta) | **26 PASS** |

Observações: o avaliador subset é bounded e documentado — a validação autoritativa com `jsonschema` real (Draft 2020-12, 22/22) consta do doc 86 §E.1; este arquivo torna os checks reproduzíveis no repo sem adicionar dependência. Os probes de política provam o contrato proposto; **não** provam renderer/consumer inexistente.

## 6. Regressões

| Suíte | Resultado | Comando |
|---|---|---|
| delia-api (novos probes) | 37+1xfail PASS | `pytest tests/test_presentation_v2_proposal.py tests/test_render_specialist_outcome_fidelity.py` |
| plugin-ui (novo probe) | 26/26 PASS | `npx vitest run src/components/markdown/conversationMarkdownLexer.probe.test.ts` |
| plugin-ui markdown+rich-text | 149+26 = **175/175 PASS** | `npx vitest run src/components/markdown src/components/rich-text` |
| plugins/delia vitest | **191/191 PASS** | `npx vitest run` |
| delia-api presentation/orchestration/runtime | **195/195 PASS** | `pytest tests/test_interaction_presentation.py test_specialist_capability_orchestration.py test_interaction_runtime.py` |

Typecheck/build/federation: `TEST_NOT_RUN` (nenhum runtime afetado; baseline tsc §6.194 inalterada — 3 erros pré-existentes plugin-ui de outro owner).

## 7. SSH (read-only, srv-api — mecanismo autorizado)

Executado na R2: remote checkout e containers re-verificados; nenhuma escrita/deploy/migração/ACT. Detalhes e SHA registrados no ledger §6.196 e no relatório final.

## 8. Gates — estado factual (o executor não declara conclusão)

| Gate exigido antes de G3 | Estado |
|---|---|
| `G1_CONTRACT = REVIEWED_AND_APPROVED` | `PENDING` — revisão independente necessária |
| `G2_SECURITY_REUSE = REVIEWED_AND_APPROVED` | `PENDING` |
| `LINK_L1_CONTRACT = PROVEN_AND_REVIEWED` | `SPECIFIED` + `BINDINGS=TO_INVENTORY` — **não provado** (bloqueante) |
| `TOKEN_EXPOSURE = RESOLVED_OR_PROVEN_ISOLATED` | `RED_PROBE_RECORDED` — fix aguarda autorização bounded (bloqueante) |
| `REPRODUCIBLE_TESTS = EVIDENCE_RECORDED` | `DONE` — testes versionados neste commit |

`G1=G2=CANDIDATE_REWORKED` / `G3=BLOCKED` / `G4=TEST_NOT_RUN` / `CP-333=PLANNED` / `PHASE_PROGRESSION=NONE` / `INDEPENDENT_REVIEW=PENDING`.
