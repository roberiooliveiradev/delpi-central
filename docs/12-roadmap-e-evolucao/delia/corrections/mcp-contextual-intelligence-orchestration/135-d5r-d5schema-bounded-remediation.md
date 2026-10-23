# 135 — Correção funcional bounded: D5-R e D5-schema

**TASK_ID:** `DELIA-C3-POSTDEPLOY-D5R-D5SCHEMA-BOUNDED-REMEDIATION-01`
**PLAN_ID:** `DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01`
**REFERENCE_REVIEW:** `a8a1f6c61fbc6eaee46325641a8c1845d8a2cbcf`
**Data:** 2026-10-23
**Natureza:** correção funcional bounded autorizada pelo PO. Sem deploy (gate governado). Sem R3. Sem mudança em DAVI, prompts produtivos, Policy/Decision/AuthZ ou contratos congelados de intenção.

---

## 1. Reancoragem e autoridade

| Item | Valor verificado |
|---|---|
| BASE_SHA | `eca13d1a09` (`origin/main` após rebase ff — diff final avaliado sobre esta base) |
| Baseline comportamental de referência | `6a896a695d947566cf7a7b730e836585a954e692` (pré-refatoração — doc 134 provou os dois defeitos pré-existentes) |
| Release em produção | `sha256:ee155bf5a325…` — **não redeployado** (`DEPLOY_STATUS=NOT_EXECUTED`) |
| Autorização | prompt PO desta task (TASK_ID acima); doc 133 NÃO reutilizado (escopo dele era o release R1/R2) |
| Authorities lidas | `.cursor` always-on + `delia-execution-protocol`; docs 124/126 (remediação `contract_subject`/`contract_facts`), 125, 128, 129, 130, 131, 132, 133, 134; ADR 58; roadmap 59; decisão S4/117; ledger §6.410–415 |

Decisões congeladas respeitadas: gate `contract_subject` declarado-pelo-modelo (doc 124) — o código **não** força nem infere `contract_subject`; classificação Evidence (registros vs contract_facts vs control-plane) — nenhum schema foi promovido a FACT empresarial; `DISCOVERY != APPROVAL`, `READ != PREPARE != ACT`; apresentação schema-first e provider-neutral — nenhuma blacklist de provider/entidade/vocabulário criada.

## 2. Causa raiz confirmada (doc 134 §3/§5)

- **D5-R:** `contract_subject=yes` declarado pelo modelo abre o veredito `OUTCOME_CONTRACT_FACTS`; `compose_cri_response` renderizava `leads.contract_facts` + rows `entities.*` como **conteúdo total**, deslocando a projeção guidance goal-relevante (`ProductGuide`/`block_types`) já produzida pelo terminal DISCOVERY em `truthful.content_text`.
- **D5-schema:** DISCOVERY com `candidates_present` mas sem merge de argumentos válido terminava em `return None` — o envelope (incluindo o contrato publicado do candidato) era descartado sem projeção, mesmo com `contract_subject=yes` declarado.

`FIRST_CAUSAL_DIVERGENCE`: D5-R → precedência de composição no veredito `contract_facts` (perdeu conteúdo já projetado). D5-schema → `candidates_present → return None` no terminal de `_invoke_selected` (descarte total do envelope).

## 3. Reuse-before-design

`EXISTING_EQUIVALENT=YES` para todos os mecanismos centrais — nenhum sanitizer, renderer, evidence engine, classifier ou registry novo:

| Necessidade | Mecanismo existente reutilizado |
|---|---|
| Projeção bounded de contrato | `_contract_fact_rows` (outcome_assessment) — reutilizada intacta no tier surface |
| Sanitize/redact/compact | `_sanitize_renderable`, `_without_control_plane`, `_compact_evidence`, `_redact_text`, `MAX_*` bounds — mesma pipeline |
| Veredito contract_facts + lead CRI | `assess_outcome` + `leads.contract_facts` — inalterados |
| Conteúdo honesto de terminal | padrão `_render_zero_candidate_discovery` (mesmo estilo PT user-facing, bounded por `MAX_RENDER_CONTENT_CHARS`) |
| Objetivo tipado declarado | `_TurnGoal.contract_subject` + `business_subject` — já validados pelo estágio goal, já disponíveis no fluxo principal |
| Fold/canonicalização de tokens | `_canonical_key` — único normalizador da pipeline de evidência (sem segundo tokenizer) |
| Sinal tipado no outcome | `contract_facts` em `SpecialistOutcome` — `projected_content` segue exatamente o mesmo precedente |

`REUSE_DECISION=EXTEND` — três extensões mínimas dentro das fronteiras existentes:

1. **`SpecialistOutcome.projected_content`** (domain DTO, opcional, default `None`): portador tipado de "projeção determinística já produzida para este outcome" — mesmo papel que `contract_facts` exerce para contrato. Sem ele, a distinção entre "conteúdo projetado" e "texto de miss/owner" não atravessa a fronteira outcome→composição. Extensão aditiva backward-compatible; não reclassifica evidência.
2. **`compose_cri_response(projected_content=...)`** (conversational_response): no veredito `contract_facts`, o conteúdo projetado **precede** o lead+rows — o scaffold do veredito suplementa, nunca desloca, evidência já projetada.
3. **`_candidate_contract_rows(candidate)`** (outcome_assessment): projeção bounded de UM candidato bonded — whitelist `action_id/entity/description/required_arguments/argument_schema`; `candidate_token` e transport jamais projetados; mesma pipeline sanitize/compact. Necessária porque `candidates` é intencionalmente excluída de `_contract_fact_rows` (transport key) — a projeção do candidato exige gate de relevância separado, não afrouxamento da exclusão.

## 4. Mudanças implementadas (menor diff correto)

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `app/domain/specialist_interop/model.py` | +`projected_content: str \| None = None` em `SpecialistOutcome` | portador tipado de projeção governada |
| `app/application/capability_provision/conversational_response.py` | `compose_cri_response` +param `projected_content`; branch `OUTCOME_CONTRACT_FACTS` antepõe-o ao lead+rows | precedência de composição (D5-R) |
| `app/application/capability_provision/outcome_assessment.py` | +`_CANDIDATE_CONTRACT_KEYS`, `_candidate_contract_rows` | projeção bounded de contrato de candidato |
| `app/application/capability_provision/orchestration.py` | terminal `candidates_present` → `_unusable_candidate_terminal`; `_invoke_selected` +`goal`; `_discover_candidate` retorna `(candidate, outcome)`; `truthful`/`terminal` outcomes carregam `projected_content`; `_compose_cri_response` propaga; helpers `_contract_subject_bond`, `_subject_bond_tokens`, `_identity_tokens_bond`, `_capability/candidate_identity_text`, `_iter_bond_candidates`, `_render_unusable_candidate_discovery` | gate de vínculo tipado + terminal honesto (D5-schema) |
| `delia-api/tests/test_c3_contextual_discovery.py` | Parte 4: 8 testes RED→GREEN + fixtures | caracterização |

### Vínculo tipado (o "não é `contract_subject=yes → exibir schemas`")

`_contract_subject_bond` só libera projeção quando **as três condições** valem:

1. `goal.contract_subject=True` — declarado pelo modelo, validado, nunca forçado/inferido por Python;
2. `goal.business_subject` tokeniza (stoplist PT/EN mínima, fold `_canonical_key` nos dois lados);
3. pelo menos um token do sujeito dá match **exato ou prefixo-bounded (≥4 chars)** com a identidade **publicada pelo owner** de (a) um candidato específico (`action_id`/`entity`/`description`) ou (b) da capability selecionada (`remote_name`/`capability_id`/`description`).

- bond com candidato → projeta o contrato daquele candidato (`candidates.<action>` rows);
- bond com a capability → projeta fatos de superfície via `_contract_fact_rows` (candidatos excluídos — o schema do candidato inadequado **não** vira "o contrato geral");
- sem bond → `None` → silêncio honesto (NOT_APPLICABLE) — mesmo resultado de antes do fix para perguntas não-contratuais.

`search_protheus_columns_in_table` sob a pergunta "contrato de informações da DELPI": sujeito `{informaes, delpi}` não bonda a identidade `protheus_column` → negativo exigido pelo prompt — verificado em fixture e em provider real.

## 5. Matriz RED → GREEN

| Cenário | RED (antes) | GREEN (depois) |
|---|---|---|
| `compose` contract_facts com `projected_content` | TypeError (param inexistente) | conteúdo projetado precede lead+rows |
| `compose` contract_facts sem `projected_content` | — | inalterado (lead+rows) — pin de controle |
| guided catalog + `contract_subject=yes` (e2e, CRI on) | `entities.playlist` como conteúdo total | guidance primeiro + facts como suplemento |
| contract question sem guidance (e2e) | — | fatos permanecem a resposta — controle positivo |
| candidates não-executáveis + sujeito bonda capability | NOT_APPLICABLE (envelope descartado) | SUCCESS, `entities.*` rows, `table_name` ausente |
| idem, sujeito bonda candidato | NOT_APPLICABLE | SUCCESS, `candidates.search_products` row |
| idem, sujeito sem bond | NOT_APPLICABLE | NOT_APPLICABLE — preservado |
| idem, `contract_subject=False` | NOT_APPLICABLE | NOT_APPLICABLE — guarda |

## 6. Regressão e verificações

| Verificação | Resultado |
|---|---|
| Suíte backend completa (`tests/`, container isolado, `/app`+`/docs`+`/plugins`) | **2191 collected, 100% exit=0, zero falhas** |
| Testes focados D5-R/D5-schema | 8/8 GREEN |
| R1 fail-closed (recurso de instruções ausente/corrompido → `orchestration=None`) | coberto por `test_c3_pre_refactor_stabilization`/`test_config` — suite verde |
| R2 projection/redaction (credenciais, `agent_directives`, control-plane) | testes Parte 3 do arquivo — verde; `_candidate_contract_rows` usa a mesma pipeline + whitelist |
| CRI ON/OFF | `projected_content` é opcional com default `None`; CRI off renderiza `content_text` (inalterado) |
| D8-R controle de regressão | caminho zero-candidatos intacto (`candidates_present=False` → render existente); nenhum código DAVI/retrieval/aliases tocado |
| Import DAG | `model.py` (domain) sem imports app; `outcome_assessment` → só domain; `conversational_response`/`orchestration` — acíclico, sem leaf→orchestration |
| AP-01…AP-20 | reconciliados: sanitizer único preservado, zero ciclo, owner de projeção continua `outcome_assessment`, zero registry/engine novo |

Caminhos não afetados: `_invoke_selected` em pagination/foreign/repair recebe `goal=None` → comportamento idêntico ao anterior (silêncio honesto); outcomes não-terminais carregam `projected_content=None` por default.

## 7. Avaliação com modelo e providers reais

**Runtime composto real** (container dedicado `infra-delia-api`, worktree montada, rede dev, CRI ativo com `cri_presentation.delpi.json` + `orchestration_instructions.delpi.json`, `DELIA_RESPONSE_INTELLIGENCE_ENABLED=true`, `delia-json`/qwen2.5:3b):

- Eval integrado `scripts/r1r2_integrated_eval.py` (matriz HTTP D4/D5/D5-R/D5-schema/D8/D8-R/N1 + 3 negativos): **verdict PASS, `blocking_failures=[]`**. D8 GROUNDED via `delpi.get_product_summary` (registro real verbatim + labels PT-BR). D5/D5-R/D5-schema/D8-R responderam `capability_surface_listing` — o modelo 3B não alcança a seleção de grupo (variância dev já documentada na baseline; não exercita o caminho corrigido).
- **Probe live provider** (orquestrador composto com `McpCapabilityProvider` real + credencial delegada; `tools/list` real → `['davi','teo','vista']`, zero failures; `_invoke_selected` dirigido com `_TurnGoal` tipado — bypassa apenas a variância de seleção do 3B, todo o resto é o caminho produtivo):
  - `vista.get_catalog` + `contract_subject=yes` + subject "tipos de visualização": `projected_content` = render `ProductGuide` (seções + tópicos `block_types` — a resposta funcional real), `contract_facts` = `entities.playlist`; veredito `contract_facts` → **CRI = guidance primeiro, contract row como suplemento** (antes: row como conteúdo total).
  - `davi.discover_delpi_information` + subject "informações delpi": candidato real `search_protheus_columns_in_table` → sem bond → **`None`, silêncio honesto** (negativo exigido).
  - idem + subject "produtos": bond com `search_products` → terminal honesto + `candidates.search_products` com o schema real publicado (`code`, `group_code`, `description`, `page`, `page_size`) → veredito `contract_facts` → CRI = texto honesto + lead + row bounded.
  - guarda `contract_subject=False` com sujeito bondável: **`None`** — nenhum schema apresentado sem intenção contratual declarada.
- Credencial delegada: dev KC não registra audiences URL-form; probe usou token exchange para os clients de recurso dev (`mcp-*`) — **nenhuma credencial criada/alterada**, apenas mint de tokens da identidade sancionada no ambiente dev. Keycloak dev estava parado; reiniciado (`delpi-keycloak`), estado restaurado.

`MODEL_EVAL=EXECUTED` (dev 3B + live providers). Generalização com modelo forte (`kimi-k3`) é material e fica **TEST_NOT_RUN localmente** — o modelo forte existe apenas em prod; deploy requer gate próprio.

## 8. Segurança

- `DISCOVERY != APPROVAL`: o terminal apresenta contrato publicado; nenhum candidato executa sem argumentos válidos (o caminho `merged=None` continua impeditivo — apenas projeta).
- `candidate_token` nunca projetado (whitelist `_CANDIDATE_CONTRACT_KEYS`).
- Injeção/metadata maliciosa: rows passam por `_sanitize_renderable`/`_without_control_plane`/`_redact_text` — `agent_directives`, secrets e control-plane continuam fora (testes Parte 3 verdes).
- Bond é gate de **apresentação** apenas — não autoriza execução, não altera classificação de evidência, não lê a pergunta do usuário (só o sujeito tipado já validado).
- Sem provider/nome/vocabulário hardcoded: o bond deriva exclusivamente da identidade publicada pelo owner.

## 9. Generalização

- Provider-neutro: VISTA/DAVI aparecem apenas como dados de owner; a regra vale para qualquer especialista que publique candidatos ou surface guidance-shaped.
- Capability renomeada/reordenada: bond usa `remote_name`/`capability_id`/`description` vigentes — renomear não quebra nem fabrica bond.
- Provider ausente: `_invoke` falha antes do terminal — inalterado.
- Envelope sem candidatos: caminho zero-candidatos preservado (D8-R intacto).
- Irmão do D5-schema (capability selecionada ela própria candidate-bound): coberto — `_discover_candidate` agora devolve o envelope e o mesmo terminal se aplica; antes descartava identicamente.

## 10. Rollback, resíduos e limites

- `ROLLBACK=git revert` do commit desta task (sem deploy — imagem prod inalterada).
- Resíduos documentados: (a) `contract_subject` permanece hipótese do modelo — declarações erradas continuam possíveis na fronteira de intenção (variância, não defeito; a precedência agora preserva conteúdo relevante em ambos os casos); (b) token bond por prefixo pode produzir falsos positivos de relevância — consequência bounded: mostra contrato publicado bounded de candidato relacionado, nunca executa; (c) `goal` não propagado para pagination/foreign/repair — nesses caminhos o comportamento é idêntico ao anterior (residual bounded, documentado); (d) modelo forte não reavaliado localmente (TEST_NOT_RUN — requer homologação produtiva pós-gate).
- D8-R permanece CONTRACT_LIMITATION do owner DAVI (vocabulário lexical material↔produto) — **fora de escopo por instrução explícita do prompt**; recomendação owner-side mantida do doc 134.
- `AUTO_REWORK_USED=NO`; `EXECUTION_DRIFT=NONE`.

## 11. Conclusão

Duas correções funcionais justificadas por contrato, implementação mínima (5 arquivos, ~+750 linhas incl. testes), testes reproduzíveis RED→GREEN + suíte completa verde + prova live em providers reais. Nenhuma autoridade ampliada: gate de intenção tipado preservado, projeção bounded reutilizada, silêncio honesto quando o vínculo contratual não é provável.

`DEPLOY_STATUS=NOT_EXECUTED` — congelar `EVALUATED_SHA`, revisão independente e autorização operacional específica precedem qualquer deploy.

`COORDINATION_REVIEW_REQUIRED=YES` · `R3_AUTHORIZED=NO` · `PLAN_COMPLETE=NO`


## 12. Revisão independente da coordenação — 2026-10-23

**REVIEWED_SHA:** `0b9220fa64abe8f569eb3b4336a5f10cdf29a409`  
**REVIEW_VERDICT:** `ACCEPT_WITH_RESIDUAL` (código e testes reportados; sem homologação prod no SHA).  
**DEPLOY_AUTHORIZED_BY_THIS_REVIEW:** `NO`. **R3_AUTHORIZED:** `NO`.

**Inspeção GitHub:** commit da task contém cinco arquivos de aplicação/testes mais doc 135, README e ledger; foram lidos o documento, os DTOs `SpecialistOutcome.projected_content`, a composição CRI e os helpers de vínculo no orquestrador. Extensões mantêm os owners existentes e não identificamos engine/registry/sanitizer paralelo nem execução de candidato sem argumentos válidos no caminho revisado. O campo projetado é opcional e documentado. Os resultados `RED→GREEN 8/8`, `2191` testes, eval Ollama e probes MCP são **reportados pelo executor**, não reexecutados independentemente nesta revisão.

**Resíduo técnico principal (não ignorar):** `_identity_tokens_bond` aceita correspondência por prefixo compartilhado de 4 caracteres entre `business_subject` proposto pelo modelo e `action_id/entity/description` providos pelo owner. Este é um gate determinístico **de apresentação contratual**, não uma decisão de capability nem AuthZ, mas pode aceitar candidato semanticamente inadequado. Por isso `D5_SCHEMA_OUTCOME=FIXED_IN_TESTED_SCOPE`, não prova de generalização irrestrita. Antes de release, executar testes adversariais com descrições genéricas, prefixos colidentes, múltiplos candidatos, subject ambíguo, metadata maliciosa e consultas contratuais positivas; verificar que nenhuma identidade apenas textual é apresentada como 'contrato da DELPI' sem vínculo legítimo.

**D5-R:** a precedência de `projected_content` sobre `contract_facts` corrige o deslocamento demonstrado, mas precisa de avaliação com modelo produtivo e casos em que guidance não responde à pergunta contratual. `D5_R_OUTCOME=FIXED_IN_TESTED_SCOPE`. **D8-R:** continua limitação do owner DAVI; nenhuma mudança DAVI autorizada ou implementada.

**Decisão:** aceitar com resíduos como entrega bounded de implementação. Não classificar como homologação geral, não autorizar reuso do doc 133 para este hotfix, nem iniciar R3. Gate antes de deploy: independente readiness com testes adversariais de bond e CRI, evidência de regressão/generalização e autorização operacional explícita para o release específico. Se falsos positivos apresentarem risco material, `REWORK` bounded antes de promoção; não inserir correção lexical específica de provider. `GLOBAL_BUSINESS_OUTCOME=INCONCLUSIVE` até homologação com modelo produtivo.
