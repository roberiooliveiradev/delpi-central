# C3/T2 — Post-INT-1 Functional Requirements Inventory and Next Bounded Step Decision

**TASK:** `DELIA-C3-T2-POST-INT1-REQUIREMENTS-AND-NEXT-BOUNDED-STEP-DECISION-01`
**Data:** 2026-11-13 · **Base:** `5a6ebcc9e5` (=origin/main; REFERENCE `5667e18549` era HEAD válido no início, ff aplicado)
**Natureza:** revisão de coordenação + inventário residual dirigido + proposta de próximo passo. `CODE_CHANGED=NO` · `PRODUCTION_DEPLOY=NO` · **seleção não autoriza implementação**.

## 1. Reancoragem

- `HEAD` inicial `5667e18549` (REFERENCE_HEAD válido); `origin/main` avançou → `5a6ebcc9e5` (it-portal G1 workstations — alheio); ff-only, WIP LNF concorrente preservado.
- `PHASE_FROM_16`: C3/T2 — `INT1_CLOSED=YES` (Doc 323, aceite independente); T2 **não** concluída por consequência.
- `NEXT_FROM_LEDGER`: `COORDINATION_C3_T2_POST_INT1_NEXT_BOUNDED_STEP_DECISION` — esta task.
- Autoridades: Docs 293 (matriz T2-INT canônica, anexo §382+), 300, 305, 313–323, Doc 16, ledger, residual register.

## 2. Estrutura canônica T2 (Doc 293 anexo — fonte de verdade)

| Stage | Responsabilidade cognitiva | Estado oficial |
|---|---|---|
| INT-0 | Inventário de reuso/contratos | `ACCEPT_WITH_RESIDUAL` (histórico) |
| INT-1 | **Investigação** — Agent generalista, tools dinâmicas, progresso por evidência | **`CLOSED` (Doc 323, ACCEPT independente)** |
| INT-2 | **Compreensão** — objetivo e entrega esperada tipados (lista/aggregate/explicação) sem keywords hardcoded | `PLANNED / NOT_AUTHORIZED` |
| INT-3 | **Avaliação de suficiência** — distinta de grounding; teste de necessidade cognitiva | `TO_INVENTORY / NOT_AUTHORIZED` |
| INT-4 | **Síntese** — fiel, relevante, rastreável | `PLANNED / NOT_AUTHORIZED` |
| INT-5 | **Aceite integrado** — 3 casos PO + metamórficos + negatives | `GATED / NOT_AUTHORIZED` |

## 3. Reconciliação funcional — as quatro responsabilidades

| Responsabilidade | Requisito canônico | Owner/contrato | Implementação publicada | Evidência | Estado | Residual material |
|---|---|---|---|---|---|---|
| **Compreensão do objetivo** | objetivo+entrega tipados, sem keywords (INT-2) | DÉLIA Application; tool `declare_investigation_goal` → `_accept_semantic_investigation_plan` → `SemanticInvestigationPlan{goal,evidence_needed}` | **Sim** — tool model-visible, validação Application-side, echo do subject aceito | `plan=None` no trace prod real (or-qwen14b-49cc26d53beb) — tool nunca invocada pelo modelo; separação lista/aggregate/explicação não exercitada | `TO_INVENTORY→PARTIAL` (mecânica existe; cadeia de outcome não exercitada) | cadeia plan→obligations morta em runtime real |
| **Investigação por capabilities governadas** | tools dinâmicas + progresso por evidência (INT-1) | SpecialistInterop/MCPToolset/Core eligibility | Sim — publicada e deployada | PROVEN: Docs 317/321/323, evals e069f3b33be8 (dev) + 49cc26d53beb (prod) | **PROVEN/CLOSED** | nenhum |
| **Avaliação de suficiência e Outcome** | suficiência ≠ grounding (INT-3) | `_evaluate_material_obligations`, estados OBLIGATION_*, `_apply_declared_answer`, finalize | **Sim** — machinery publicada e consumidora ativa | nunca exercitada: `plan=None` ⇒ `coverage_unknown` em **toda** finalização | `TO_INVENTORY` (rótulo canônico) | veredito de cobertura permanece não-provável por construção |
| **Síntese fundamentada** | fiel/rastreável (INT-4) | `InvestigationAnswer`, evidence binding, hallucination guard (tokens numéricos verbatim), `declared_consistent` | Sim | proven-in-sample: respostas prod grounded + marcadores honestos (`declared_status_overridden`, `coverage_unknown`, `declared_limitation`) | `PROVEN_IN_SAMPLE` (bounded) | nenhum material — sintese depende de suficiência para status provável |

`EXISTING_EQUIVALENT=YES` para as três responsabilidades restantes — a mecânica canônica já existe publicada; nenhuma nova engine/planner/router é necessária ou proposta. `REUSE_DECISION=EXTEND` para qualquer passo futuro.

## 4. Análise de lacunas

| Item | Classificação |
|---|---|
| Enumeração integral P2 em produção | **Residual não-material aceito** — Doc 314 §8/Doc 323: `PARTIAL_HONEST` aceito, filtro `q:"transformação"` declarado; diferença de escolha cognitiva, não defeito |
| `coverage_unknown` permanente (plan nunca populado) | **Requisito funcional pendente** — INT-2 (typed goal+`evidence_needed`) alimenta INT-3 (veredito); sem ele `complete` nunca é provável — fronteira registrada canonicamente em Docs 293/2066/323 |
| Suficiência INT-3 standalone | **Bloqueada por dependência** — `_evaluate_material_obligations` exige `plan.evidence_needed` que é entregável INT-2 |
| Síntese INT-4 | **Parcialmente provada in-sample**; avanço pleno depende de INT-2/3 para status provável |
| INT-5 aceite integrado | **Fase posterior** — gate final após stages |
| Perfil Kimi×Qwen, SEC-01, DAVI non-exec caps, heavy-view timeout, eval flakes, attempt-status conflation | **Dependências externas / residuais não-materiais aceitos** com owner |

**Primeira divergência comprovada (não hipótese):** trace prod real — tool `declare_investigation_goal` disponível no toolset (15 tools) e **não invocada** → `plan=None` → `declared_status_overridden`+`coverage_unknown` no outcome de P2. O Outcome layer se comporta corretamente (declara não-provado); a lacuna é a **não-população da tipagem de objetivo/obrigações**, requisito INT-2.

## 5. Matriz de decisão — próximo passo

| REQUISITO | OWNER | EVIDÊNCIA | ESTADO | BLOQUEIA T2? | AÇÃO NECESSÁRIA |
|---|---|---|---|---|---|
| INT-1 investigação | DÉLIA | Docs 317–323 | CLOSED | não | nenhuma |
| INT-2 compreensão tipada (goal/evidence_needed/delivery) | DÉLIA Application | tool existe; plan=None em prod real | PARTIAL/TO_INVENTORY | **SIM** — alimenta INT-3 e prova de satisfação | bounded step proposto (abaixo) |
| INT-3 suficiência | DÉLIA Application Outcome | machinery existe, nunca exercitada | TO_INVENTORY | SIM — dependente de INT-2 | após INT-2 |
| INT-4 síntese | DÉLIA | proven-in-sample | PARTIAL | não (avaliação final junto a INT-3/5) | nenhuma agora |
| INT-5 aceite integrado | Coordenação | — | GATED | posterior | aguardar stages |
| Residuais menores/externos | owners vários | register atualizado | NON_BLOCKING | não | owner-local |

## 6. Decisão proposta

```text
NEXT_STEP_DECISION=T2_ONE_BOUNDED_RESIDUAL_STEP_REQUIRED
```

**Próximo passo delimitado — `T2_INT2_TYPED_OBJECTIVE_DELIVERY_AND_OBLIGATION_POPULATION` (proposta; requer autorização da coordenação):**

- **Objetivo:** tornar a tipagem de objetivo + entrega esperada (lista/aggregate/explicação — sem keywords hardcoded) e a população de `evidence_needed` efetivas em inferência real, de modo que o veredito de cobertura deixe de ser `coverage_unknown` permanente.
- **Contrato:** extensão dos contratos existentes — `declare_investigation_goal`, `_accept_semantic_investigation_plan`, `SemanticInvestigationPlan`, `_TurnGoal`, guidance de instrução domain-neutral. **Zero** novo Agent/planner/router; `AGENT_COUNT=1`; `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND`.
- **Arquivos candidatos (inventário, não edição):** `delia-api/app/application/capability_provision/semantic_capability_support.py` (plan/obligations), `app/infrastructure/orchestration/pydantic_ai_investigation.py` (tool surface/finalize `plan=`), instruction registry (goal-declaration guidance).
- **Testes necessários:** unitários de aceitação do plan/veredito de cobertura; metamórficos de objective-kind; **eval real isolado** bounded (perfil homologado) provando: (a) modelo declara goal+obrigações sem keywords, (b) outcome classifica `satisfied`/`unsatisfied` provável — incluindo um controle de não-enumeração e um caso honestamente insuficiente.
- **Critérios de conclusão:** evidência de inferência real com plan populado e veredito de cobertura não-`unknown`; invariância dos contratos de governança; suíte sem regressão; revisão independente para aceite do stage (executor não autoaceita).
- **Dependências:** autorização expressa da coordenação; mesmas regras de isolamento de eval; nenhum deploy implícito.

Nenhuma outra ação é necessária antes disso: INT-3 não pode ser provada sem o entregável INT-2; INT-4/INT-5 aguardam os stages.

## 7. Estado

```text
INT1_CLOSED=YES (Doc 323)
T2_FUNCTIONAL_ACCEPTANCE=NOT_COMPLETE — INT-2..INT-5 pendentes
NEXT_STEP_DECISION=T2_ONE_BOUNDED_RESIDUAL_STEP_REQUIRED
NEXT_STEP=T2_INT2_TYPED_OBJECTIVE_DELIVERY_AND_OBLIGATION_POPULATION (proposta)
SELECTION_DOES_NOT_AUTHORIZE_IMPLEMENTATION=YES
PHASE_ADVANCEMENT=NO · CODE_CHANGED=NO · PRODUCTION_DEPLOY=NO
INT2_IMPLEMENTATION_AUTHORIZED=NO · INT3/T3=NOT_AUTHORIZED
NEXT=COORDINATION_INT2_BOUNDED_STEP_AUTHORIZATION_DECISION
```

### Adendo de direção PO posterior — 2026-11-14 (Doc 335)

A matriz INT-1..INT-5 desta decisão histórica permanece correta quanto às **responsabilidades cognitivas e aos critérios do estágio**. Posteriormente, o PO confirmou uma **arquitetura-alvo com quatro Agents cognitivos especialistas** (compreensão, investigação, suficiência, síntese) trocando contratos tipados. **Não** interpretar este adendo como implementação ou aprovação automática da separação; o único Agent Pydantic AI existente continua baseline, e o Doc 293 exige prova comparativa e gate arquitetural. INT-1 CLOSED (Doc323); INT-2 implementação avançada (Docs325–334), aceite final pendente; INT-3 e novos Agents não autorizados. Ver [Doc 335](./335-c3t2-four-cognitive-specialist-agents-po-product-direction-and-int2-resumption.md).
