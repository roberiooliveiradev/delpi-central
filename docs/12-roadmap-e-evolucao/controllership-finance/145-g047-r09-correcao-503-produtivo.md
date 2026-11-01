# CF-PROC0072 — Gate 047: R09 — causa raiz do 503 produtivo e correção

Data: 2026-11-01. Incidente real reportado pela CLARA (ChatGPT):
 2026-09 filial 01/02 → HTTP 503
«Origem de dados financeiros indisponível».

## Causa raiz — PROVEN (evidência de log produção)

| Elo | Evidência |
|---|---|
| api-delpi (producer) |  em **149.157ms e 212.481ms** — o motor funciona e responde corretamente |
| BFF → api-delpi |  —  aborta a espera em 30s → 503 |
| Gateway nginx |  no upstream CF-API — suficiente |
| CLARA/MCP | Action no catálogo, parâmetros corretos — não é a causa |

**Classe**: configuração/timeout — não implementação, segurança ou dados.

## Correção mínima aplicada

:  na chamada
 — dedicada à rota R09 (relatório
genuinamente pesado ~150–210s), dentro do orçamento do proxy (300s),
sem alterar o 30s das rotas irmãs e sem mudar regras informacionais.

Commits: local  ≡ prod  (diff idêntico).
Deploy: rebuild controllership-finance-api em srv-api; container
healthy,  verificado no código em execução.

## Testes executados

- 10/10 testes da rota BFF (positive/negative) — PASS.
- Negativos live: 401 noauth (producer, BFF, gateway) — PASS.
- Producer live 200 em 149–212s — observado nos logs produtivos.

## Pendências honestas

- Consulta positiva real (Bearer de usuário) — : o PO
  validará via CLARA/ChatGPT; a limitação de 30s removida é a única
  alteração necessária, evidência: producer completa ~3min < 300s.
- Push do fix para origin/main — canal credenciado (merge de terceiro
  bloqueia rebase local; srv-api sem credencial HTTPS interativa).
- Timeout > 300s para competências maiores: monitorar; se o producer
  superar 300s, avaliar otimização do motor ou 
  para processamento assíncrono.

## DoD transversal — proposta registrada

A regra FULL-FLOW VERIFICATION / END-TO-END OUTCOME GATE exigida pelo
gate fica registrada aqui e no ledger para inclusão no DoD dos
próximos relatórios (R13/R04/R14), respeitando a autoridade central.

## Parecer

 — causa raiz comprovada, correção mínima
publicada e em produção; validação positiva pelo usuário pendente.
