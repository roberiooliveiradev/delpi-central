# 06 — Revisão independente da Etapa 01 (architecture + evaluation + security)

**Task:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-01-INDEPENDENT-REVIEW
**Papel:** revisor independente da execução original (Architecture Reviewer + AI Evaluation Reviewer + Security Reviewer). Sem implementação funcional, sem correções, sem redesign.
**Data:** 2026-10-16
**REVIEW_BASE_HEAD:** `4ad30b5f21aebb85aee7df1122f17ba130cedf3f` (main, sync com origin/main; sem commits concorrentes)
**Objeto revisado:** commit `1f29906dc45726c778e8d133b2fbdbc41f4b9939` (ancestral de HEAD) — harness `delia-api/tests/test_conversational_intelligence_baseline.py`, relatório `04-stage-01-baseline-report.md`, ledger §6.171.
**Runtime diff 1f29906..HEAD em `delia-api/`:** NONE (somente docs e plugins/* posteriores). Evidência de testes executada neste HEAD é válida para o mesmo runtime.
**VERDICT:** `ACCEPT_WITH_RESIDUAL` — baseline suficientemente comprovado para orientar a Etapa 02 **mediante autorização da coordenação**; este parecer não autoriza implementação.
**Classificações:** PROVEN | PROVEN_PARTIAL | REPORTED | TO_INVENTORY | TEST_NOT_RUN | STALE_EVIDENCE.

## 1. Reancoragem e autoridades

- `git rev-parse HEAD` = referência; `git status` mostra alterações concorrentes do usuário em `plugins/*`, `requests-api`, arquivos untracked — preservadas, nenhuma tocada por esta revisão.
- Fase revalidada em 16/ledger: `C3_STARTED=YES; C3_EXECUTED=NO; C4_AUTHORIZED=NO; C5_AUTHORIZED=NO; PRODUCTION_READINESS=NOT_PROVEN; NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.
- Autoridades lidas na ordem obrigatória: 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02-arquitetura → 24 → specs 60/69/70 + personality/01..04 → ledger. Leitura mínima suficiente: as cláusulas vinculantes citadas por `05` foram revalidadas nas fontes primárias (24 §5/§6; 50 §6; 60 §5; 21 §4B; personality/02..04; ledger §6.126/§6.130/§6.133/§6.140/§6.141/§6.145/§6.171). CP-IDs citados em `03` (CP-055, CP-071, CP-073/074, CP-086/087, CP-094, CP-151, CP-205, CP-232/233, CP-263, CP-269, CP-270/271) existem na 25.
- Pasta de correção lida integralmente (README, 01, 02, 03, 04, 05). Relatório `04` preservado como histórico — nenhuma reescrita.

## 2. Evidência executada pelo revisor (não herdada)

- `delia-api/.venv/bin/python -m pytest tests/test_conversational_intelligence_baseline.py -v` → **15/15 PASS**.
- `delia-api/.venv/bin/python -m pytest` (suíte completa) → **1069/1069 PASS em 28.48s** no HEAD `4ad30b5`. A alegação "1069/1069" do executor é confirmada por execução própria.
- `git diff --check 1f29906^ 1f29906` → limpo. Commit contém somente teste + relatório + ledger; nenhuma alteração funcional.
- `git log` confirma BASE_HEAD reportado `57da7fac` = parent do commit de implementação.
- Inspeção direta de `orchestration.py` (6294 linhas), `handle_interactive_turn.py`, `instruction.py`, `invoke_model.py`, `presentation.py` — claims verificados no código, não aceitos por declaração.

## 3. Verificação das alegações do executor

| Alegação | Resultado da revisão |
| --- | --- |
| 15 testes novos, suite 1069/1069 | **PROVEN** — reexecutado neste HEAD (15 PASS; suíte 1069/1069 PASS). |
| 13 instruction IDs + `delia.interaction.base` v3 | **PROVEN** — 13 IDs em `orchestration.py` (SELECTION_INSTRUCTION_VERSION="7") + `delia.interaction.base` v3 (1561 chars). Contagem de chars da tabela do relatório confere exatamente para os 14 textos. |
| String sem enum não dispara discovery | **PROVEN** — `_is_open_vocabulary` cobre apenas object/array opacos; `_requires_owner_vocabulary` retorna False para campo string puro; teste demonstra `owner_vocabulary` ausente do payload. |
| Ausência de `goal_class=orient` | **PROVEN estrutural** — `_GOAL_CLASSES`={read,analyze,compare,create_or_modify,clarify}; classe desconhecida normaliza silenciosamente para `"read"` (linhas 3566–3571). **Reclassificação:** ausência literal não comprova necessidade de novo enum — os docs 02/05 já vedam a decisão prévia; Etapa 02 deve provar necessidade/impacto ou reutilizar semântica existente. |
| Pergunta de orientação pode alcançar PREPARE | **PROVEN_PARTIAL** — hazard estrutural real: `goal_class` é computado após a seleção e nunca consultado para gate de write; `_GOAL_CLASSES` só alimenta comparação/native assessment/subject; o hint "crie→prefer PREPARE" existe em `CAPABILITY_SELECTION_INSTRUCTION`. Frequência com modelo real = **TEST_NOT_RUN** (hazard demonstrado com proposta roteirizada). |
| Completude inner de `changes` não validada | **PROVEN (metade pipeline)** — única validação determinística é `_validate_instance` contra o `input_schema` externo; `changes` opaco não é rechecado contra `entity_schemas`. **Reclassificação:** a metade owner (PREPARE READY → rejeição no commit) é **REPORTED** — trace de produção reportado pelo usuário, não reproduzido ao vivo; o fake apenas o espelha. |
| "Último cadastrado" sem prova de ordenação | **PROVEN** — `_render_synthesis` renderiza seleção verbatim sem verificação de ordenação/cobertura; `items:[]` → `empty_selection` → fallback `render_specialist_outcome` despeja todos os registros. |
| Personalidade fora do caminho operacional | **PROVEN estrutural** — `DELIA_INTERACTION_INSTRUCTION` só alimenta `self._invoke` (caminho geral NON_GROUNDED); SUCCESS/denial/lifecycle usam renderers determinísticos; personality/02..04 declaram `RUNTIME_IMPLEMENTATION=NOT_PROVEN`. |
| Confirmação direct = owner-declared, não bug DÉLIA | **PROVEN** — `_effective_confirmation_policy` honra `explicit_user_confirmation` selado (§6.140); DÉLIA executou o contrato do owner. |
| Resolver same-owner existe; repair só p/ surface-change | **PROVEN** — `_repair_once` existe apenas para relist de superfície (MAX_REPLAN_ROUNDS=1, non-mutating); reuso de owner-hints de erro como evidência não existe — gap 7 classificado corretamente. |
| Orçamentos factuais (MAX_*=3/1/6000/14000/60/16/8/12000/2000/1) | **PROVEN** — todos confirmados no código; stage timeout + `TurnDeadline` por turno. |
| Model calls/turno 3–5; produção ~5 proposals/~33s/2–11s | Contagem no harness **PROVEN** (budget test = 5 purposes no write path com 2 grupos). Timings de produção = **REPORTED**, não verificáveis a partir do repo. |

## 4. Gates de review

### A. Arquitetura — PASS

O baseline respeita e reproduz corretamente as decisões congeladas: DÉLIA única orquestradora provider-neutral (24 §5, §6.130); MCP = família de providers, owner detém capabilities/schemas/vocabulário/execução (§6.126/§6.133); tools/list live como superfície primária (60 §5); resolver same-owner existente e bounded (§6.140); plano semântico ≤3 steps; ACT nunca step livre; confirmação estrutural por PREPARE (§6.140); `MODEL_AUTHORED_FACTUAL_PROSE=NONE` (§6.145). Nenhuma proposta cria planner/registry/engine/prompt por provider; nenhuma tentativa de catálogo MCP local; nenhum bypass de boundary. O diff é test-only — não pode violar runtime.

### B. Qualidade das evidências — PASS com reclassificações

Cada falha está realmente reproduzida no pipeline determinístico e os testes demonstram a causa declarada. Separação honesta mantida nos documentos: defeito estrutural (PROVEN) ≠ comportamento induzido por scripted model (PROVEN_PARTIAL) ≠ hipótese de LLM real (TEST_NOT_RUN) ≠ resultado de produção (REPORTED). Reclassificações registradas em §3 e §6 — nenhuma evidência apagada.

### C. Harness — PASS com observações

- Fakes posicionados nos seams corretos (`ModelInvocationPort` + provider `list_groups/invoke`), mesmo padrão de `test_intelligence_loop_evals.py`/`test_generic_multistep_orchestration.py`; o caminho real `InvokeModel` (validação, lineage, `guard_invocation_payload`, epistemic class) é exercido.
- Assertions significativos: status, error_code, chamadas exatas no wire, presença/ausência de `owner_vocabulary` no payload, contagem de purposes.
- Controles: positivos (CI-01 sibling, CI-03 sibling, CI-09), negativo (CI-05 NOT_READY → ACT nunca invocado), rename invariance (CI-10 ×2). Casos RED corretamente descritos como falhas comportamentais, não como sucesso.
- Observações (não bloqueantes): (i) `test_ci01_goal_class_*` contém um primeiro orchestrator construído e não usado — código morto cosmético; a proposta `"orient"` é input fora-de-contrato que um modelo real não emitiria sob a instrução vigente — prova a normalização, redundante com a inspeção de `_GOAL_CLASSES`; (ii) `FakeProposalModel._generic` pode misrotear uma proposta standalone sem chave `_PURPOSE_IDS` para o primeiro purpose chamado — fragilidade latente ao estender para purposes de resolver/clarification/native_assessment nas Etapas 02–06; (iii) `_last` repete a última proposta do purpose — mascara repetições inesperadas (mitigado pelo budget test que conta purposes); (iv) os testes exercem `attempt()` diretamente — auth/presentation de `handle_interactive_turn` ficam fora do escopo do baseline (cobertos por outras suítes); (v) em testes single-group o `capability_group_id` roteirizado nunca é consumido (short-circuit determinístico) — dado morto inócuo.

### D. Segurança — PASS

READ não se transforma implicitamente em PREPARE/ACT: o hazard exige proposta de seleção write-class; a cadeia governada permanece (PREPARE → readiness → política estrutural → WRITE_REJECTED fail-closed; CI-05 prova NOT_READY → 0 ACT). Confirmação segue o contrato estrutural selado (§6.140). Nenhuma autoridade inferida de metadata MCP; nenhum bearer/secret/prompt sensível em fixtures; nenhum model output promovido a FACT (HYPOTHESIS/allowed_keys/lineage); nenhum write real — todos os providers são fakes; `git diff --check` limpo; nenhum arquivo sensível no diff.

### E. Reuse gate — PASS

| Gap | EXISTING_EQUIVALENT | REUSE_DECISION | Etapa |
| --- | --- | --- | --- |
| 1 vocabulário string | YES (`_is_open_vocabulary`/`_requires_owner_vocabulary`, discovery) | EXTEND | 03 |
| 2 goal contract | YES (`_TurnGoal`/`GOAL_INSTRUCTION`) | EXTEND | 02 |
| 3 hint seleção write | YES (`CAPABILITY_SELECTION_INSTRUCTION`) | EXTEND | 02/03 |
| 4 completude inner | YES (`_build_arguments` + entity_schemas do catalog) | EXTEND | 04 |
| 6 suficiência/ordenação | YES (`_synthesize_content`, outcome.limitations) | EXTEND | 05 |
| 7 owner-hint reuse | TO_INVENTORY (repair existe só p/ surface-change) | EXTEND | 03/04 |
| 8 personalidade | TO_INVENTORY (instrução base + docs personality) | TO_INVENTORY | 05 |

Equivalentes confirmados no código; nenhum NEW proposto; coerente com `05` (REUSE/EXTEND por padrão; NEW exige Abstraction Gate).

## 5. Overclaims encontrados e reclassificações aplicadas

1. `test_ci04` docstring: "Full production chain reproduced" → **reclassificado**: reproduz a forma do pipeline sob propostas roteirizadas; a metade owner (READY→commit reject) é REPORTED, não demonstrada ao vivo.
2. `goal_class=orient` ausente → ausência PROVEN; **necessidade do enum NÃO comprovada** (docs 02/05: novo enum/reorder não aprovados). O teste é evidência estrutural do contrato, não prova de design futuro.
3. Hazard guidance→PREPARE → estruturalmente real; **frequência real-model = TEST_NOT_RUN**; não prova que LLMs cometem esse erro em produção.
4. Timings/custos de produção no relatório → REPORTED; exigem eval com provider real (Etapa 06).
5. "produção já mostrou os mesmos outputs" → REPORTED; consistente com §6.158 (latência real documentada), sem contradição material.

## 6. Residuais

**Não bloqueantes (registro):**
- Código morto no teste de goal; framing "production chain" no docstring; dado `capability_group_id` morto em testes single-group.
- `FakeProposalModel._generic`/`_last` — fragilidade latente do harness (ver §4.C); revisar antes de estender a purposes fora de `_PURPOSE_IDS`.
- CI-06, CI-11..CI-18 = TEST_NOT_RUN por desenho; tokens/custo/latência real-model = TEST_NOT_RUN (Etapa 06).
- Confirmação `explicit_user_confirmation=false` selada pelo owner em creates → item de governança owner-side, não bug DÉLIA (registro já feito em 04 §C-5).

**Lacuna a investigar na Etapa 02:**
- Frequência real do hazard guidance→PREPARE sob modelo real e se a semântica de orientação cabe nos contratos atuais (read/clarify/native assessment) ou exige evolução de contrato — **proibido presumir novo enum/reorder/branch por provider**.
- Efeito do hint "crie→prefer PREPARE" na instrução de seleção (baseline vs candidate, owners renomeados).

**Lacuna das Etapas 03–06:**
- Gap 1/7 (vocabulário owner legítimo, owner-hint reuse bounded) → 03/04; gap 4 (completude inner via contrato owner, sem duplicar Domain) → 04; gap 6/8 (ordenação/insuficiência, personalidade) → 05; generalização real-model + CI completo + outcome → 06.

**Condição obrigatória antes de implementar:**
- Etapa 02 só inicia com autorização bounded da coordenação após este review; preservar §6.126/§6.130/§6.133/§6.140/§6.141/§6.145; zero novos prompts por provider; alterações nos limites MAX_* exigem evidência e review; `MODEL_AUTHORED_FACTUAL_PROSE=NONE` intacto.

## 7. Impacto sobre Etapas 02–06

O baseline é utilizável como referência comparativa: mesmo SHA/config, denominadores claros, casos CI mapeados, positivo/sibling/negativo/rename. Etapa 02 pode comparar baseline↔candidate no mesmo harness, desde que estenda `FakeProposalModel` sem mascarar purposes (ver §4.C.ii–iii). Nenhum gate reaberto; nenhuma decisão congelada redesenhada.

## 8. Readiness da Etapa 02

`READY_FOR_AUTHORIZATION` — a Etapa 01 entregou o que prometeu (baseline factual + harness + diagnóstico classificado). **Esta revisão não autoriza a execução da Etapa 02**: a autorização é da coordenação de arquitetura, que deve emitir o próximo prompt bounded incorporando as condições de §6.

**ESTADO:** `STAGE_01_REVIEW=ACCEPT_WITH_RESIDUAL`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`; `C5_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.
