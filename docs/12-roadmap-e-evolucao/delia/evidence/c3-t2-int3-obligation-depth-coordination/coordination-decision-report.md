# COORDINATION DECISION REPORT — DÉLIA C3/T2 · INT3 Obligation Depth

**TASK_ID:** `DELIA-C3-T2-INT3-OBLIGATION-DEPTH-NEXT-BOUNDED-STEP-01`
**MODO:** `COORDINATION_INVENTORY / CONTRACT_REVIEW / NEXT_IMPLEMENTATION_DECISION`
**PRODUÇÃO:** não autorizada. Nenhuma alteração funcional, de banco, migration,
deploy, promoção ou avanço de fase foi executada por esta task.

## RQ-1 — Reancoragem

- **HEAD:** `d18c8158c34c06ad50bb75fdbcfcffbf3a9addc0` (`main`, = `origin/main`).
- Concorrentes preservados: working tree contém WIP de terceiros
  (`helpdesk/13-listagem-de-chamados.md` modificado, artefatos e2e não
  rastreados) — nada tocado. Nenhum `reset`/`clean`/`stash`/checkout executado.
- Fase: **C3/T2** vigente (doc 16 + ledger); sem avanço autorizado.
- NEXT do ledger: veredito oficial do verificador ainda pendente para o
  fechamento V024/DAVI (1 rodada restante; engines bloqueados — Devin sem
  login standalone, Cursor sem quota) + residuais INT3/R4 abertos.
- Decisões congeladas revalidadas: um Agent generalista em produção;
  experimento two-Agent flag-gated, sem promoção (`DO_NOT_PROMOTE` por
  custo/latência/outcome); Application é autoridade de aceitação; zero
  falso `SATISFIED` é invariante.

## RQ-2 — Inventário factual dos residuais

Fonte: `evidence/engineering-closure-residual-register.md` (entradas mais
recentes) + `evidence/execution-ledger.md`.

| Residual | Estado | Classificação |
|---|---|---|
| `INT3-OBLIGATION-DEMONSTRATION-DEPTH` | `PARTIAL_REMEDIATED / OPEN_LOW` | **Funcional, interno à DÉLIA — escolhido** |
| `R4-AUTHZ-DENY-IDENTITY` | `PENDING` | Precondição externa: oráculo de identidade restrita (owner: platform-security/Keycloak). Não implementável nesta task; nunca simular 403. |
| `R6-N6/N7` (negativos de autorização) | `PENDING` | Bloqueados por R4. |
| `R2-CONTINUITY-PAGINATION` | `PARTIAL_REMEDIATED / OPEN_LOW` | Envelope `pagination:{}` remediado (RED→GREEN + live `has_more:true`); convergência do loop de continuação do modelo não provada — residual de evidência, não de mecanismo. |
| `R5_MULTIPAGE_UNION` | `PROVEN_IN_SAMPLE` | Resolvido (40+40+29=109, `has_more=false`). Não reabrir. |
| `R6-MULTI-TURN-RECOVERY` | `PROVEN_IN_SAMPLE` | Resolvido na mesma conversa; residual OPEN_LOW de variação de âncora absorvido pelo INT3. |
| `R5-N3/N4/N5` (composition/filter/scope drift) | contract-test pass | Resolvidos. Não reabrir. |
| G2 primeira tentativa (`analyze`→claim 200→UNSATISFIED) | observado | O gate fail-closed **funcionou**; é variância de seleção do modelo, não defeito de suficiência. Não inventar correção. |
| `T2-TWO-AGENT-OUTCOME-COST-GENERALIZATION` | `INCONCLUSIVE → DO_NOT_PROMOTE` | B: ~+37% input / +67% output / ~2.07× latência / +13 MCP calls, sem ganho. Re-amostra depende de harness, não de trabalho funcional novo. |
| `T2-G2-OBLIGATION-ANCHOR-MISMATCH` | `OPEN_LOW` | Absorvido pelo INT3 — mesmo mecanismo (âncora `summary/analysis` vs prova `teo.read` filtrado). |

**Problema escolhido:** `INT3-OBLIGATION-DEMONSTRATION-DEPTH` — o residual
está exatamente em "a investigação respondeu à solicitação empresarial"
(INT-3 detém o sim/não), é interno à DÉLIA (sem precondição externa como
R4) e o modo de falha (evidência real → `INCONCLUSIVE` permanente)
enfraquece o outcome empresarial.

## RQ-3 — Owners e mecanismos (RESPONSABILIDADE → OWNER → CONTRATO → IMPL → TESTE)

Cadeia canônica em `delia-api/app/application/capability_provision/semantic_capability_support.py`:

| Responsabilidade | Owner/Mecanismo | Linha aprox. |
|---|---|---|
| Compreensão / aceitação do plano | `SemanticInvestigationPlan`, `_obligation_item`, `_normalize_obligation_tuple` | ~1989, ~2374–2472 |
| Contrato de obrigação | `MaterialObligation{description, evidence_source?, operation?, required_scope}` | ~1884–1980 |
| Investigação governada | `GovernedCapabilityAttempt`, `governed_capability_orchestrator.py`, `mcp_provider.py` | — |
| Vocabulário de âncora | `_attempt_anchor_tokens` (provenance + chaves `entity`/`entity_kind`/`action_id`/`capability`/…), `_invocation_vocabulary`, `_invocation_identity` | ~2576–2650, ~3006–3040 |
| Ligação superfície↔obrigação | `_attempt_surface_anchor_match` (bind ≠ demonstração) | ~3043–3068 |
| Congruência de entidade | `_obligation_declared_entity_tokens`, `_attempt_business_entity_congruent` (só via `required_scope` `entity=`/`entity_kind=`) | ~3371–3407 |
| Compatibilidade de operação | `_consultation_operations_compatible`, `_CONSULTATION_OPERATIONS` | ~2850, ~3410–3429 |
| Demonstração | `_attempt_demonstrates_anchored`, `_attempt_satisfies_obligation` | ~3432+, ~3535 |
| Cobertura de coleção | `_joint_collection_coverage` + guards N3/N4/N5 | — |
| Finalização/publicação | projeção `obligation_states` → `InvestigationAnswer`; fail-closed | — |

Contratos relevantes já existentes: `_PRESENTATION_EVIDENCE_SOURCES`
(`summary/analysis/aggregate/aggregation/count/metric/kpi/dashboard/view`,
~2837–2849) e `_SCOPE_CONTAINER_ALIASES` (`params`↔`arguments`, ~2860).

**Consumers:** projeção de finalização/grounding, `InvestigationAnswer`,
harness live INT2. Nenhuma mudança em DAVI/TÉO/api-delpi é necessária.

## RQ-4 — Matriz de reprodução determinística

Modelo-emitted status é **sempre ignorado** como oráculo; a Application
decide. Matriz proposta (superfície de teste existente, `test_c3_t2_*`):

| # | Caso | Âncora declarada | Eco do owner | Esperado pós-correção |
|---|---|---|---|---|
| 1 | correta/suficiente | `product_structure` | `entity: product_structure` | `SATISFIED` (inalterado) |
| 2 | presentation-class | `display_format` | nenhum (nunca ecoado — vocabulário DÉLIA-side) | aceitador reclassifica → obrigação julgada sem âncora owner; não fica `INCONCLUSIVE` eterno sobre evidência real |
| 3 | entity-class | `processes` | seletor `list_processes` / `entity: process` | demonstrável via `required_scope` `entity=` ∩ anchor tokens (se compreensão emitir o par); senão `INCONCLUSIVE` honesto |
| 4 | entidade errada | `sales_order` | `entity: process` | `UNSATISFIED` — congruência proíbe entidade irmã satisfazer |
| 5 | owner incompatível | `transportadora` | eco TÉO não-DAVI | `INCONCLUSIVE`/`UNSATISFIED` conforme classe de operação |
| 6 | evidência parcial | `product_structure` | eco parcial/janela incompleta | `INCONCLUSIVE` (inalterado — regra de cobertura) |
| 7 | filtro material ausente | `processes` + `required_args` | invocação sem o filtro | `INCONCLUSIVE`/`UNSATISFIED` (guards N4 vigentes) |
| 8 | multipágina incompleta | enumeração | `has_more` não drenado | `INCONCLUSIVE` (inalterado) |
| 9 | modelo declara COMPLETE sem satisfazer | qualquer | qualquer | Application rejeita — declaração não é prova |
| 10 | grounded + concluído | correto | correto | `SATISFIED` + publicação GROUNDED |

Casos 2 e 3 reproduzem o residual hoje (`bound-not-demonstrated` →
`INCONCLUSIVE` com evidência real); casos 4/5/6 são os negativos que
garantem que a correção não abre falso `SATISFIED`.

## RQ-5 — Primeira fronteira divergente

- **Compreensão?** Não no sentido de obrigação errada — a descrição da
  obrigação pode estar correta; o defeito está na **aceitação do plano**:
  `_normalize_obligation_tuple` rejeita âncora pontilhada (superfície de
  transporte) por prever `INCONCLUSIVE` travado, mas admite **qualquer**
  token não-pontilhado sem classificá-lo (business/selector/presentation)
  nem exigir caminho mecânico de demonstração.
- **Investigação?** Não — o owner foi invocado de verdade e retornou
  evidência real e pertinente.
- **Suficiência?** O julgamento está **correto** (`_attempt_demonstrates_
  anchored` recusa satisfazer o que não foi demonstrado); o que falta é
  caminho de demonstração para âncoras válidas que o owner nunca ecoa
  (presentation-class) ou ecoa noutro vocabulário (entity-class).
- **Finalização?** Não — projeção fail-closed publica honestamente.

**Primeira fronteira divergente: aceitação do plano (seam
compreensão↔suficiência)** — obrigações são admitidas num estado
estruturalmente indemonstrável. Evidência: register linha ~1888 (G1/P3
`get_product_structure`/`display_format` bound-not-demonstrated) e
~2027 (`processes`, `process_document`, `transportadora`, zero eco em
48 cenários, zero falso SATISFIED).

## RQ-6 — Decisão

```yaml
PHASE_FROM_16: C3/T2 (sem avanço)
NEXT_FROM_LEDGER: veredito oficial pendente + residuais INT3/R4

PROBLEM: âncoras evidence_source aceitas sem classificação podem ser
  estruturalmente indemonstráveis → evidência real trava em INCONCLUSIVE.
FIRST_DIVERGENT_BOUNDARY: aceitação do plano (_normalize_obligation_tuple)
  — admite âncora fora do vocabulário demonstrável sem classificação.
ROOT_CAUSE: ausência de classificação de âncora (business/selector/
  presentation) e de caminho mecânico de congruência exigido por classe.
EVIDENCE: register ~1888/~2027; código 2410–2472, 2837–2849, 3371–3485.

OWNER: DÉLIA Application — capability_provision/semantic_capability_support.py
CONTRACT: MaterialObligation.evidence_source "âncora ao vocabulário vivo
  do owner"; vocabulário indemonstrável viola a intenção do contrato.
CONSUMERS: finalização/grounding, InvestigationAnswer, harness INT2 live.

EXISTING_EQUIVALENT: YES — _PRESENTATION_EVIDENCE_SOURCES,
  _attempt_business_entity_congruent, required_scope entity= pairs,
  precedente de rejeição de âncora pontilhada.
REUSE_DECISION: EXTEND — classificar âncora na aceitação usando maquinário
  existente; NÃO criar engine/catálogo novo, NÃO usar substring matching.

RECOMMENDED_BOUNDED_TASK:
  DELIA-C3-T2-INT3-ANCHOR-CLASSIFICATION-AND-DEMONSTRABLE-VOCABULARY-01
FILES_EXPECTED:
  - delia-api/app/application/capability_provision/semantic_capability_support.py
  - delia-api/tests/ (suítes material-obligation/sufficiency existentes)
TESTS_REQUIRED: RED×≥6 (âncora presentation, âncora entity-class,
  entidade-irmã negativa, regressão âncora pontilhada, janela parcial,
  string legado sem âncora, modelo-declara-COMPLETE) → GREEN +
  regressão completa delia-api.
REAL_EVAL_REQUIRED: YES — bateria INT2 live (G2/R5/C2/D/R6) em container
  isolado, flag two-agent ligada, OpenRouter qwen3-14b; cenário classe
  G1/P3 com âncora tipo display_format deve resolver demonstrado-ou-
  parcial-honesto — nunca INCONCLUSIVE travado sobre evidência real.
SAFETY_GATES: invariante zero falso SATISFIED (48+ cenários); READ nunca
  demonstra ACT; congruência só via required_scope entity= ∩ anchor
  tokens — nunca substring; âncora pontilhada continua rejeitando o plano.
EXPECTED_BUSINESS_OUTCOME: obrigações ancoradas em vocabulário
  presentation/entity-class resolvem para estado verdadeiro na primeira
  tentativa — evidência real pertinente não fica presa em INCONCLUSIVE.

DEPENDENCIES: nenhuma externa (R4 segue trilha separada — owner:
  platform-security/Keycloak deve provisionar identidade restrita real;
  R6-N6/N7 permanecem bloqueados até lá).
RESIDUALS: eco do owner pode continuar não cobrindo todo vocabulário
  entity-class → INCONCLUSIVE honesto residual permanece correto por
  design para âncoras genuinamente indemonstráveis.
ARCHITECTURE_DECISION_REQUIRED: menor — classificar na aceitação
  (recomendado: feedback barato ao modelo, espelha precedente de âncora
  pontilhada) vs classificar na suficiência. Decisão proposta:
  classificação na aceitação + julgamento na suficiência com maquinário
  existente.
```

## Alternativas descartadas

1. **"Corrigir" a 1ª tentativa G2** — o fail-closed já funcionou;
   demonstrar claims via `MCP:analyze` enfraqueceria o gate, não o
   fortaleceria.
2. **Oráculo R4 agora** — precondição externa (identidade restrita real);
   simular 403 não é evidência.
3. **Re-amostra A/B two-Agent** — depende de harness; sem gap funcional.
4. **Engine/catálogo novo de suficiência** — viola REUSE; maquinário
   existente cobre com extensão pontual.
5. **Normalização por substring/prefix-strip (`get_`/`list_`)** — viola o
   contrato explícito "exact tokens, never substring" e abre falso
   positivo.

## Verificação (delpi-verifier)

Pedido gravado em `.git/delpi-verifier/requests/` contendo exatamente os
RQ-1..RQ-6 e AC-1..AC-10 desta task. Resultado das rodadas: ver relatório
de execução no encerramento da task.
