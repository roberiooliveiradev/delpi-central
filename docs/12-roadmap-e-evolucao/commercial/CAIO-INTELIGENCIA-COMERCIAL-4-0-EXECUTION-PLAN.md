# CAIO 4.0 — Inteligência Comercial Orientada a Resultados | Plano executivo e trilha de evidências

**Status inicial:** PROPOSED / IN_EXECUTION. **Data:** 2026-10-31.
**Referências:** [Visão CAIO 3.0](CAIO-INTELIGENCIA-COMERCIAL-3-0.md), [Trilha 3.0](CAIO-3-0-EXECUTION-TRAIL.md), [Plano Aplicada W0–W8](CAIO-INTELIGENCIA-COMERCIAL-APLICADA-EXECUTION-PLAN.md), [Paridade](../../initiatives/caio-mcp/CAIO_PARITY_MATRIX.md), [Homologação](../../initiatives/caio-mcp/CAIO_HOMOLOGATION_MATRIX.md).
**Baseline observado (F1):** HEAD `9cca21d92b`; catálogo **127 operações** (6 tools); corpus **v3.2** — 17 tópicos, 16 métodos, 8 roteiros com contrato §5, glossário 17 termos estruturados, `products.guide` + 4 reads `product.*`, seleção contextual com precision floor. Deploy produtivo verificado (srv-api). Smoke autenticado amostral PASS; composição integral A–J autenticada = pendente.

## 1. Missão e limites de verdade

CAIO como **consultor comercial especializado DELPI**: investigar problemas, detectar riscos e oportunidades, preparar vendedores (briefing/negociação), simular cenários e medir a qualidade das recomendações. Não transforma recomendação em ação produtiva; não cria indicador oficial sem owner; metodologias externas seguem `pending_business_validation`.

## 2. Arquitetura e segurança (inalterados)

`commercial-api` = autoridade comercial; api-delpi/Engenharia = produto; 6 tools MCP; autorização backend por usuário/carteira/filial; writes/deletes só com contrato e aprovação — homologação = read/analyze/knowledge. Abstraction Gate antes de qualquer nova estrutura.

## 3. Fases e critérios de aceite

| Fase | Entrega | Aceite | Status |
|---|---|---|---|
| F1 Inventário | Baseline verificado em HEAD | Números reproduzíveis | TESTED |
| F2 Investigação | Contrato §5 já existente nos playbooks (reuso) | Seleção + composição demonstrada | TESTED |
| F3 Riscos | Risco vs confirmado explícito nos roteiros | failure_states distinguem RISK/CONFIRMED/UNKNOWN | TESTED |
| F4 Oportunidades | `expansion_opportunities` aprofundado | Evidência+justificativa+investigação+KPI | TESTED |
| F5 Reunião/visita | **Novo playbook `meeting_prep`** | Briefing completo + orientação pós-visita | IMPLEMENTED |
| F6 Cenários | `forecast_scenarios` com template de simulação | premissas/fórmulas/cenários/incerteza | TESTED |
| F7 Técnico-comercial | `products.guide` aplicações documentadas | Engenharia owner; `PENDING_BUSINESS_VALIDATION` onde não confirmado | TESTED |
| F8 Metodologias venda | SPIN/MEDDPICC/negociação via métodos + meeting_prep | externo ≠ regra DELPI | TESTED |
| F9 Qualidade | Rubrica reproduzível (matriz + teste) | baseline vs depois; segurança eliminatória | TESTED |
| F10 Homologação | Jornadas A–J | contrato=PASS; autenticado=ver evidência | PARTIAL |

## 4. Diário de progresso

| Data | Fase | HEAD | Arquivos | Provas | Limitações | Status |
|---|---|---|---|---|---|---|
| 2026-10-31 | F1–F10 | `9cca21d92b`→corpus4.0 | knowledge JSON v4.0 (9 playbooks: +meeting_prep), riscos CONFIRMED/RISK/WATCH/UNKNOWN, simulações SIMULATED, expansão F4, forecast F6, testes homologação (E/F/G/I + contract), matriz/plan/docs | suíte CAIO verde; cenários A–J contrato | autenticado integral = TEST_NOT_RUN | ver matriz |

## 5. Matriz de execução contínua

Preenchida por fase conforme `plan-execution.mdc` — resultados consolidados em `CAIO_HOMOLOGATION_MATRIX.md` e na seção de diário acima. Nenhuma promessa sem evidência de código+teste+deploy.

## 6. CAIO 4.1 — Dossiê inteligente de cliente (2026-10-31)

- **F1 identidade/carteira:** meeting_prep v4.1 exige resolução de carteira oficial, owner e participantes via customer.enrichment + portfolio.get/list; divergência (participante ≠ owner, ex. caso WANKE/Camilo↔Cássio) declarada, nunca presumida. Defeito real corrigido: portfolio.customer_coverage retornava 502 — adapter passava SellerCustomerAssignment enquanto o use case espera tuplas (code,store); tradução na fronteira + teste de regressão; fallback autorizado portfolio.get/list + customer.list documentado.
- **F3 tarefas:** activity.list (vinculada ao cliente) + task.list (worklist do próprio vendedor); tarefa registrada ≠ compromisso mencionado.
- **F4 salas:** interaction_room.list/get/members/messages/pins/shared_items — somente salas com vínculo estruturado ao cliente e acesso do usuário; menção textual ≠ vínculo.
- **F5–F7:** rótulos OBSERVED/CALCULATED/INFERRED/UNKNOWN/SIMULATED; estrutura de saída A–I (identificação→resumo→relacionamento→desempenho→riscos→pauta→preparação interna→pós-reunião→fontes/limitações).
- **F8 pós-reunião:** rascunho de decisões/tarefas; gravação só via execute com permissão + pedido explícito.
- **Evidências:** corpus v4.1 (9 playbooks); suíte CAIO 654 passed; homologação A–L em contrato = PASS; autenticado integral = TEST_NOT_RUN.

### Adendo 4.1.1 — semântica de `customer_coverage` (2026-10-31)
Diagnóstico definitivo: `portfolio.customer_coverage` é detector de cobertura **compartilhada** (2+ carteiras); `items:[]` para WANKE = resultado válido (1 carteira), não defeito. Resolução de identidade permanece via portfolio.get/list + customer.list. Corpus v4.1.1; suíte 660 passed.
