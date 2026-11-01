# CF-PROC0072 — Gate 047: R09 — causa raiz do 503 produtivo e correção

Data: 2026-11-01. Incidente real reportado pela CLARA (ChatGPT):
action `read(report.billing_mod_breakdown)`, competência 2026-09,
filiais 01 e 02 → HTTP 503 «Origem de dados financeiros indisponível».

## Causa raiz — PROVEN (evidência de log de produção)

| Elo | Evidência |
|---|---|
| api-delpi (producer) | `status=200` em **149.157ms e 212.481ms** — o motor funciona e responde corretamente |
| BFF → api-delpi | `delpi_api_timeout path=/financeiro/billing-mod-breakdown` — `DELPI_API_TIMEOUT=30` aborta a espera em 30s → 503 ao cliente |
| Gateway nginx | `proxy_read_timeout 300` no upstream CF-API — suficiente |
| CLARA/MCP | Action presente no catálogo, parâmetros corretos — não é a causa |

**Classe**: configuração/timeout — não implementação, segurança ou dados.

## Correção mínima aplicada

`billing_mod_breakdown_routes.py`: `timeout_seconds=300` na chamada
`ApiDelpiSettlementsGateway.get()` — dedicada à rota R09 (relatório
genuinamente pesado ~150–210s), dentro do orçamento do proxy (300s),
sem alterar o 30s das rotas irmãs e sem mudar regras informacionais.

Commits: local `6242838fa6` ≡ prod `dd0b809ac` (diff idêntico).
Deploy: rebuild `controllership-finance-api` em srv-api; container
healthy, `timeout_seconds=300` verificado no código em execução.

## Testes executados

- 10/10 testes da rota BFF (positive/negative) — PASS.
- Negativos live: 401 sem/com token inválido (producer, BFF, gateway) — PASS.
- Producer live 200 em 149–212s — observado nos logs produtivos.

## Pendências honestas

- Consulta positiva real (Bearer de usuário) — `TEST_NOT_RUN`: o PO
  validará via CLARA/ChatGPT; a limitação de 30s removida é a única
  alteração necessária — o producer completa ~3min < 300s.
- Push do fix para `origin/main` — canal credenciado (merge de terceiro
  bloqueia rebase local; srv-api sem credencial HTTPS interativa).
- Timeout >300s para competências maiores: monitorar; se o producer
  superar 300s, avaliar otimização do motor ou `DECISION_REQUIRED`
  para processamento assíncrono.

## DoD transversal — proposta registrada

A regra FULL-FLOW VERIFICATION / END-TO-END OUTCOME GATE exigida pelo
gate fica registrada aqui e no ledger para inclusão no DoD dos
próximos relatórios (R13/R04/R14), respeitando a autoridade central
da plataforma.

## Parecer

`ACCEPT_WITH_RESIDUAL` — causa raiz comprovada, correção mínima
publicada e em produção; validação positiva pelo usuário pendente.
