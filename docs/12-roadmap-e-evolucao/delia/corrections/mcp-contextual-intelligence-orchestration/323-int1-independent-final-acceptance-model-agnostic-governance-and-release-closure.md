# 323 — INT-1 | Decisão independente final de coordenação e encerramento delimitado

**Data:** 2026-11-13  
**Tipo:** COORDINATION / INDEPENDENT ACCEPTANCE — não é execução de código nem novo deploy.  
**TASK_ID:** `DELIA-C3-T2-INT1-INDEPENDENT-FINAL-ACCEPTANCE-DECISION-01`  
**BASE_HEAD revisado:** `a15f72813594d8cc351806d35a4b1f9ce421c842` (revalidar qualquer avanço concorrente; Doc 322 publicado em `19891d8309bf943c4de46cf8aeafb08d1e104936`).  
**Autoridades:** Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura/product spec → 293/314 → Docs 317–322 → ledger. Decisões de fase superiores não alteradas por este review.

## 1. Decisão explícita da coordenação

```text
INT1_ENGINEERING_ACCEPTANCE=ACCEPT
L_GATE=PASS
A_GATE=PASS
O_GATE=PASS
R_GATE=PASS
INT1_FINAL_ACCEPTANCE=ACCEPT
INT1_CLOSED=YES
PHASE_FROM_16=C3/T2
PHASE_ADVANCEMENT=NO
INT2_IMPLEMENTATION_AUTHORIZED=NO
INT3_IMPLEMENTATION_AUTHORIZED=NO
T3_AUTHORIZED=NO
NEW_PRODUCTION_DEPLOY=NOT_AUTHORIZED
```

**Escopo exato do aceite:** fechamento de engenharia INT-1 e operação já implantada dos serviços/protocolos governados, com Outcomes baseados em evidências e comunicação honesta de cobertura. **Não** é afirmação de sucesso universal de qualquer modelo, completude de todas as respostas ou conclusão antecipada de outras INTs. Esta é uma decisão de coordenação distinta do reporte do executor; reviews independentes anteriores validaram código da remediação TÉO e evidências dos documentos 319–322.

## 2. Evidência analisada

- **ENG:** Documento 317 comprova P1/P2/P3 na mesma configuração de Qwen em DEV, P2 sem filtro (`process.search params:{}`, total 109 naquela fonte); Documento 319 comprova DÉLIA 1601 pass, TÉO 2127 pass/62 skip, VISTA 2535 pass, DAVI 5970 pass/10 skip; Documento 320 comprova correção fail-closed de `_same_filial`, `_share_setor` e âncora não resolvida, 13 testes novos, TÉO 2140 pass/62 skip, sem alteração model-visible.
- **RELEASE:** Documento 321 registra deploy sequencial DAVI→TÉO→VISTA→DÉLIA (árvore `b8a31f8c12` equivalente para os quatro serviços à árvore congelada; imagens por serviço e rollback registrado), MCP tools/list com delegação, health e avaliações READ em owners produtivos.
- **PROD:** Documento 322 identifica runtime ativo `openrouter_kimi`/`moonshotai/kimi-k3`, Pydantic AI 2.50.0, registry Core, 3 owners MCP live e policy/evidence/outcome invariantes. O eval `or-qwen14b-49cc26d53beb` usou **container isolado Qwen** com owners produtivos, **não** o Agent Kimi efetivamente em produção. Essa distinção permanece explícita: configurações verificadas no container ativo, não igualdade de outcome cognitivo dos modelos.
- **P2:** trace `teo.read process.search params:{q:"transformação"}` resultou em um item (`PROC-0001`, total=1 **da query filtrada**). Grounding correto, porém enumeração geral não demonstrada nessa execução. O modelo declarou `complete`; a camada de Outcome anotou `declared_status_overridden`, `coverage_unknown` e `declared_limitation`. Resultado **PARTIAL/HONEST**, jamais `FULL_ENUMERATION_PROVEN`.
- **P1/P3:** GROUNDED com evidência real na avaliação isolada; P3 truncation declarada, sem afirmar exaustividade.
- **Arquitetura:** troca de modelo ocorre por config/adapters; sem segundo Agent/router/engine, sem RBAC mutation; autorização Core/Domain não depende do modelo. Não é necessário benchmark competitivo Qwen×Kimi.

## 3. Disposição explícita da tensão P2

Documento 314 §8 autoriza à coordenação **decidir explicitamente** se aceita `PARTIALLY_SATISFIED` para P2/P3 ou se exige nova evidência. A coordenação **aceita a cobertura parcial honesta de P2 para o fechamento delimitado da INT-1**, porque: (a) enumeração não filtrada foi comprovada em amostra no Doc 317; (b) em owners produtivos o filtro model-authored estreitou a cobertura mas não inventou dados nem permissões; (c) a camada de Outcome impediu promoção silenciosa de completude. Não converter este aceite em `P2_FULL_PRODUCTION_ENUMERATION=PASS`. Qualidade de seleção em diferentes formulações/modelos permanece assunto de eval contínua orientada a objetivos, não de condicionamento a provider específico.

```text
P2_PRODUCTION_GROUNDING=GROUNDED
P2_PRODUCTION_COVERAGE=PARTIAL
P2_PRODUCTION_OBJECTIVE=PARTIAL
P2_OUTCOME_HONEST=YES
P2_FULL_PRODUCTION_ENUMERATION=NOT_PROVEN
P2_ACCEPTANCE_DISPOSITION=ACCEPT_PARTIAL_HONEST_AS_BOUNDED_INT1_OUTCOME
```

Este aceite não relaxa `read!=write`, Core/Domain authority, evidence-policy, proibição de factualização de model output, nem os gates de ações. Uma futura exigência de enumeração produtiva integral deverá ter DoD próprio e evidência independente, sem reabrir silenciosamente a INT-1.

## 4. Residuais e limites

`INT1-ATTEMPT-STATUS-CONFLATION` OPEN_MINOR (observability); `INT1-MCP-HEAVY-VIEW-TIMEOUT` OPEN_MINOR (reliability); `INT1-DAVI-NONEXECUTABLE-CAPS` OPEN (owner DAVI; fora da superfície read aceita); `INT1-EVAL-ENV-FLAKES` OPEN_OPERATIONAL. `INT1-PROD-RUNTIME-PROFILE` OPEN_EXTERNAL documenta Kimi ativo e Qwen usado no eval — diferença não bloqueia aceite de contratos model-agnostic; não autoriza mudança de modelo. `INT1-SEC01-API-DELPI` OPEN_EXTERNAL: fix `ef2ea358f2` não implantado, owner/tarefa própria. **ZERO_OPEN_MATERIAL_WITHIN_ACCEPTED_INT1_SCOPE=YES**; não marcar residuais externos como CLOSED.

## 5. Limite da revisão independente

A coordenação inspecionou remotamente fontes e documentação publicadas no GitHub e comparou reports/contratos. **Não** houve rerun de pytest, inspeção direta do servidor produtivo nem nova chamada ao modelo neste ato. Os resultados de deploy/testes/telemetria são **evidências reportadas pelo executor**, corroboradas por documentação versionada e pelo review do código publicado. Aceite formal é decisão de governança baseada nesse conjunto, e não nova evidência experimental.

## 6. Próxima etapa

Fechamento **não** altera a fase: `C3/T2` permanece até decisão superior explicitamente registrada no Documento 16 e no ledger. **NEXT=COORDINATION_C3_T2_POST_INT1_NEXT_BOUNDED_STEP_DECISION**. Antes de qualquer implementação subsequente: reancorar HEAD, Doc 16/ledger, CP/RQ, owners/contratos e gates. Não iniciar INT-2/INT-3/T3 automaticamente e não usar este registro como nova autorização de produção.
