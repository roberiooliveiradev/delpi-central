# 101 — Roadmap bounded: orçamento LLM 60s, até 3 tentativas e continuidade user-facing

**Data:** 2026-10-22. **Base:** doc 99 e decisão PO doc 100. **Estado:** PLANNED, sem mudança de runtime ou deploy. A execução deve seguir HEAD atual, authorities e ledger; plano não prevalece sobre fonte canônica.

## Sequência fechada: 4 tasks / 4 prompts / 4 reviews de coordenação

| Ordem | Task ID | Owner / entrega | Gate |
|---|---|---|---|
| 1 | DELIA-C3-BUDGET-CONTINUITY-CONTRACT-DECISION-01 | Arquitetura + contracts: inventário de TurnDeadline, retry, AuthZ, model stages, MCP/Domain, composition, streaming/gateway, cancel. Definir semântica 60s por tentativa LLM, até 3 tentativas, orçamento operacional separado, envelope global, reserva/guard, timeout/cancel/replay, limites da configuração dev/prod, esquema ActivityEvent e observability. Registrar ADR ou decisão pendente. NÃO alterar código. | Contrato formal com owner/consumer, erros, testes e aprovação; ARCHITECTURE_DECISION_REQUIRED se conflitar com 2/60/30 |
| 2 | DELIA-C3-SEPARATED-BUDGETS-AND-GOVERNED-RESUME-02 | Backend nos owners canônicos: implementar contrato aprovado; janela LLM 60s por tentativa, até 3 tentativas elegíveis, reserva operacional B, terminal honesto D, checkpoint sem replay de material writes, terminal único e cancel; telemetria real. Rollout dev-only/retry prod OFF. | RED/GREEN determinísticos, Ollama GPU, MCP AuthZ dev, sem paid egress, budgets e failure negatives; stop em contrato ausente |
| 3 | DELIA-UX-GOVERNED-CONTINUITY-AND-CONTEXT-03 | Frontend/plugin-ui: avisos em tempo real de análise longa e continuidade quando ActivityEvent verdadeiro; cancelamento e estados terminal/progress; contexto abre + seleciona em um clique, troca ao selecionar mensagem com painel aberto, destaque discreto, etiquetas user-facing, a11y. Reusar componentes. | Wire compat, UX regressions, typecheck/build/federation e QA real no Portal quando deploy autorizado |
| 4 | DELIA-C3-EXTENDED-BUDGETS-INTEGRATED-EVAL-AND-RELEASE-GATES-04 | Evals integradas e readiness: CPU/GPU docs 97, modelos/stages, slow LLM + fast API, fast LLM + slow API, 3 attempts, cancellation, desconexão, no material side-effect replay, multi-turn DAVI, CRI and outcome. Release gates e rollback; nenhum prod retry ON sem gate legítimo. | Independente review, evidence SHA/config, logs sanitizados, matriz PASS/FAIL/PENDING; R4 revocation deferred work but remains open security gate |

## Invariantes

- PO aprovou direção B+D e até 60s de raciocínio semântico por tentativa, até 3 tentativas governadas; não aprovou duração total, valor de reserva API ou ativação produtiva irrestrita.
- Não inventar 180s como deadline global. O contrato 1 deve decidir envelope protetor com proxy, cancellation, A/B/C budget charging e diferenças de modelos. Até lá 2/60/30 permanece ativo.
- Reuso antes de código: EXISTING_EQUIVALENT/REUSE_DECISION por owner. Não criar outro deadline/telemetry/scheduler, não substituir seleção semântica por regex/alias/keyword.
- Informação de progresso user-facing deve corresponder a eventos reais, não liberar chain-of-thought. É processamento continuado na mesma interação, não três mensagens/perguntas independentes.
- Credencial revogada intra-turno: remediação postergada pelo PO, risco permanece OPEN; não desativar Core/Domain AuthZ nem interpretar postergação como liberação de retry em produção.
- LLM real em testes locais somente Ollama GPU; uso pago produtivo somente tráfego real autorizado.
- Se etapa 1 solicitar uma decisão essencial ainda aberta, voltar à coordenação uma vez com ADR e alternativas concretas, não seguir implementando implicitamente.

## Aceite de ciclo

Task 1 CONTRACT_APPROVED; Task 2 BACKEND_DEV_VERIFIED; Task 3 UI_INTEGRATION_VERIFIED; Task 4 INTEGRATED_EVAL_ACCEPTED_WITH_RESIDUAL_OR_BETTER. Nunca fechar fase sem authorities + ledger + SHA + outcome.
