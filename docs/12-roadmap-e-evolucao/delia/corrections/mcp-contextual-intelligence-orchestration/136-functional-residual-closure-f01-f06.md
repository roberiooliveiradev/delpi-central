# 136 — Fechamento finito dos resíduos funcionais F01–F06

**TASK_ID:** `DELIA-C3-POSTDEPLOY-FUNCTIONAL-RESIDUAL-CLOSURE-01`
**PLAN_ID:** `DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01`
**REFERENCE_HEAD:** `aa0a195c0fe7ca054ecdf372a0617b8d8f952dbb` (revisão independente do hotfix 135 — veredito `ACCEPT_WITH_RESIDUAL`)
**Data:** 2026-10-23
**Natureza:** pacote finito de fechamento dos seis resíduos formais F01–F06. Sem deploy (gate governado). Sem R3. DAVI/api-delpi modificado somente no vocabulário governado do owner, sob gates satisfeitos.

---

## 1. Reancoragem e autoridade

| Item | Valor verificado |
|---|---|
| BASE_SHA | `e6a7f22c41` (`origin/main` no início do trabalho — apenas commits docs sobre `aa0a195c`; zero mudança `delia-api` no intervalo, verificado por diff) |
| Worktree isolada | `/home/analistaptd/delia-fclose-wt` — checkout principal e trabalho concorrente preservados |
| Autorização | prompt PO desta task; doc 133 **não** reutilizado (escopo era release R1/R2); deploy produtivo **não** autorizado por este prompt |
| Authorities lidas | `.cursor` always-on + `delia-execution-protocol`; reancoragem 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25; specs 03/60; ADR 58; roadmap 59; S4/117; docs 124–135; ledger vigente |

Decisões congeladas respeitadas: gate `contract_subject` declarado-pelo-modelo (doc 124) — nenhum classificador lexical criado; `DISCOVERY != APPROVAL`, `READ != PREPARE != ACT`; provider-neutral — zero blacklist/phrase-table/provider routing; `candidate_token` nunca exposto nem enviado ao modelo; sanitizer/redação únicos.

## 2. Inventário finito e reuse gate

`EXISTING_EQUIVALENT=YES` para todos os itens — `REUSE_DECISION=EXTEND`:

| Residual | RESPONSIBILITY → OWNER → CONTRACT → DEFECT → CHANGE |
|---|---|
| F01 | Bond de relevância contratual → DÉLIA orchestration (gate de **apresentação**, não autorização) → vínculo só sobre identidade tipada owner-published → match por prefixo ≥4 + texto livre (`description`) admitiam falsos positivos → tokens canônicos accent-folded, match exato + fold singular bounded |
| F02/F04 | Precedência guidance × contract facts + variância `contract_subject` → CRI compose + terminal → guidance projetada precede facts; ausência de declaração mantém bounds → **nenhum defeito novo** — caracterizado |
| F03 | Terminal candidates → DÉLIA orchestration → nunca executar sem argumentos válidos → `required_arguments` declarados eram ignorados quando `argument_schema` não era Mapping → enforcement incondicional de required tipado |
| F05 | Propagação de `goal` → chamadas internas `_invoke_selected` → contrato da interação ≠ escopo de page-walk/foreign/repair → **decisão: não propagar** — caracterizado |
| F06 | Vocabulário retrieval → DAVI owner (`davi_external_read_allowlist.json` `semanticAliases`) → `search_products` deve cobrir domínio `material` (canônico SB1) → família material ausente → aliases adicionados |

## 3. F01 — eliminação de falsos positivos no bond

**Defeito:** `_identity_tokens_bond` aceitava (a) match exato ou (b) prefixo compartilhado ≥4 chars, sobre identidade que incluía `description` em prosa livre. Colisão real observada: `produtividade`/`produção` bondava `search_products`/`production` — falso positivo apresentacional.

**Remediação** (`orchestration.py`):

- `_bond_token` — canonicalização determinística (NFKD → ASCII → alnum minúsculo); nunca inferência semântica.
- `_bond_forms` — formas de comparação = token literal + fold singular bounded (`s` final em tokens ≥5) dentro do mesmo vocabulário. Sem prefixo, sem substring.
- `_identity_tokens_bond` — somente match exato entre formas expandidas; prefixo compartilhado eliminado.
- `_capability_identity_text` — apenas `remote_name`/`capability_id`; `description` removido da superfície de bond.
- `_candidate_identity_text` — apenas `action_id`/`name`/`entity` + `semantic_hints.entity`/`semantic_hints.tags` (estrutura real do payload DAVI); `description` removido.

**Limite honesto documentado:** subject em vocabulário diferente do publicado (ex.: PT `produtos` vs EN `search_products`) não prova vínculo → insuficiência honesta, conforme a task permite. O bond é gate de apresentação — nunca seleção, AuthZ ou execução.

**RED→GREEN:** 3 casos adversariais falhavam no código antigo (prefixo colidente, prosa de descrição, vocabulário cruzado); todos verdes no novo. Positivos: identificador tipado exato, plural/singular, `semantic_hints.entity`, rename de action via `entity`.

## 4. F02/F04 — precedência e variância `contract_subject`

Caracterização com testes novos — **nenhum defeito encontrado**, `NO_CHANGE_REQUIRED`:

- `contract_subject=False` + payload guiado: guidance permanece a resposta; rows contratuais fora da composição.
- Pergunta contratual com declaração ausente: a resposta composta é o conteúdo projetado do owner — nunca rows de schema como substituto.
- Matriz guidance-leads / facts-supplement / facts-primary-sem-guidance já coberta pelos testes do doc 135, mantida verde.

## 5. F03 — matriz D5-schema

Defeito real encontrado e corrigido: `_candidate_arguments` só aplicava `required_arguments` quando `argument_schema` era Mapping; schema malformado caía na validação sem tipos e invocava com `{}` ignorando os required declarados pelo owner. Correção: required declarados são contrato tipado — enforcement incondicional sobre schema efetivo. Candidato com required não satisfeito nunca executa.

Matriz coberta por testes: executável (chain determinístico), não-executável mas bonded (projeção `candidates.<action>`), inadequado/sem bond (silêncio), múltiplos (só o bonded atribuído), vazio, malformado (bounded rows, sem crash), `contract_subject=False` (silêncio). `candidate_token` nunca projetado.

## 6. F05 — `goal` em pagination/foreign/repair/recovery

Inspeção dos call-sites de `_invoke_selected`:

| Caminho | `goal` | Decisão |
|---|---|---|
| Seleção principal do turno | propagado | inalterado |
| Evidência foreign | `None` | `CLOSED_PROVEN_NO_CHANGE` — o subject declarado pertence à seleção do turno; atribuí-lo a uma chamada auxiliar de outro owner apresentaria o contrato alheio como resposta |
| Paginação | `None` | `CLOSED_PROVEN_NO_CHANGE` — page-walk é continuação da mesma invocação; reafirmar escopo contratual em falha de página seria atribuição indevida |
| Repair/reseleção | `None` | `CLOSED_PROVEN_NO_CHANGE` — re-seleção não carrega o subject declarado anterior; comportamento preservado |
| Owner-contract recovery | `None` | `CLOSED_PROVEN_NO_CHANGE` — recuperação de contrato não é a interação declarada |

Garantia estrutural: `_unusable_candidate_terminal` lê `getattr(goal, "contract_subject", False)` — `goal=None` ⇒ `False` ⇒ bond `None` ⇒ silêncio honesto. Teste de caracterização novo prova que invocação sem goal não atribui contrato mesmo com candidato bondável.

## 7. F06 — DAVI `material` × `produto` (owner-side)

**Gates satisfeitos:** owner = `api-delpi/app/content/davi_external_read_allowlist.json` (`semanticAliases`, vocabulário governado); procedimento praticado (commits `275c8a72aa`, `2432c9390a` — adição de aliases sem bump de versão); `material` não consta na quarentena de retrieval; zero mudança de AuthZ, campos de resposta ou contagem de operações.

**Mudança:** família material adicionada aos aliases de `search_products` (`material`, `materiais`, `buscar/consultar material(es)`, `codigo/código do material`, `descricao/descrição do material`, `qual a descrição…`, `material code/description/search`).

**RED→GREEN:** 6 queries material falhavam no allowlist antigo (`candidate_count=0` ou candidato errado); verdes após. Guard: `consumo de materiais por ordem de produção` não promove `search_products` sobre ação especializada. Retrieval é phrase-matching ordenado sobre `searchable_text` — sem fuzzy solto.

**Prova live** (container `api-delpi` com código da worktree, rede dev): `descrição do material 10080043` → candidato `search_products` (entity `product_search`, tags `products`, score 0.9125) → chain executa → dados reais retornados. Antes: D8-R retornava `[]`.

## 8. Evidência completa

| Verificação | Resultado |
|---|---|
| RED→GREEN | F01: 3 adversariais RED→GREEN + 9 novos testes de bond; F03: malformed-schema defect RED→GREEN; F06: 6 queries RED→GREEN no allowlist antigo; F02/F04/F05: caracterização verde |
| Suite delia-api completa | **2202 passed, 3 skipped** (2191 baseline + 11 net novos), exit=0, container isolado `/app`+`/docs`+`/plugins` |
| Suite api-delpi (blast radius DAVI/retrieval) | conjunto de falhas **idêntico ao baseline** (13 falhas pré-existentes, incl. pin stale `version==22` vs allowlist v23); zero falha nova pelo diff |
| Import DAG / AP-01…AP-20 | acíclico; projeção permanece em `outcome_assessment`; sanitizer único; zero leaf→orchestration |
| Eval integrado HTTP | `verdict: PASS`, `blocking_failures=[]`, D5-R/D5-schema/D8/D8-R PASS sob critérios do eval; variância 3B (seleção não alcança grupos MCP → listings de superfície) documentada como variância de modelo dev, não defeito |
| Live provider probe | VISTA: guidance `ProductGuide`/`block_types` lidera + `entities.playlist` suplemento. DAVI: material→`search_products`→execução com dados reais; subject não-relacionado + candidatos múltiplos → silêncio honesto; `contract_subject=False` → sem contract facts; `produtividade` → silêncio (F01) |
| `kimi-k3` (modelo produtivo) | **TEST_NOT_RUN** — só existe em produção; requer gate governado pós-deploy |
| Deploy / homologação produtiva | **NOT_EXECUTED** — `DEPLOY_AUTHORIZATION=NO` para este release; rollback = `git revert` do SHA final |

## 9. Matriz de fechamento F01–F06

| Residual | Fix status | Tests | Outcome | Closure | Residual risk |
|---|---|---|---|---|---|
| F01 | IMPLEMENTED | PASS | VERIFIED | CLOSED_PROVEN | subjects fora do vocabulário owner → insuficiência honesta (by design) |
| F02 | NO_CHANGE_REQUIRED | PASS | VERIFIED | CLOSED_PROVEN | nenhum |
| F03 | IMPLEMENTED | PASS | VERIFIED | CLOSED_PROVEN | nenhum |
| F04 | NO_CHANGE_REQUIRED | PASS | VERIFIED | CLOSED_PROVEN | variância do modelo na declaração (hipótese, não autoridade) |
| F05 | NO_CHANGE_REQUIRED | PASS | VERIFIED | CLOSED_PROVEN | nenhum — decisão registrada por caminho |
| F06 | IMPLEMENTED (owner DAVI) | PASS | VERIFIED | CLOSED_PROVEN | novo vocabulário de domínio exige mesma via governada |

`BUSINESS_OUTCOME_STATUS=PARTIAL` — todos os resíduos fechados com evidência unitária + live dev; homologação com modelo produtivo (`kimi-k3`) permanece pendente do gate de deploy.

## 10. Arquivos alterados

- `delia-api/app/application/capability_provision/orchestration.py` — bond tipado estrito; enforcement de `required_arguments` independente da forma do schema.
- `delia-api/tests/test_c3_contextual_discovery.py` — +14 testes (F01 adversarial/positivo/sibling, F03 matriz, F02/F04 estados, F05 caracterização).
- `api-delpi/app/content/davi_external_read_allowlist.json` — aliases material em `search_products` (adição cirúrgica, sem reformatação).
- `api-delpi/tests/test_davi_dynamic_read.py` — parametrização positiva material + guard de não-promoção.
- Documentação: este doc, README da trilha, ledger §6.417.

`AUTO_REWORK_USED=NO` · `EXECUTION_DRIFT=NONE` · `COORDINATION_REVIEW_REQUIRED=YES` · `R3_AUTHORIZED=NO` · `PLAN_COMPLETE=NO`
