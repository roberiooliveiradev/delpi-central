# Gate 058 — R04 inventory: consumption-audit de Suprimentos (2026-11-02)

## Implementação localizada no HEAD — PROVEN

| Camada | Local | Evidência |
|---|---|---|
| Produtor (api-delpi) | `app/application/use_cases/supplies/` — search/get consumption_audit_orders + comparison | código + testes SQL/router existentes |
| Consumidor BFF | `supplies-api/app/interfaces/http/routes/consumption_audit_routes.py` + MCP tools/schemas/constants | BFF própria + SURI tools |
| Contrato | `GET /consumption-audit/orders`, `GET /consumption-audit/orders/{op}`, `/comparison` | em supplies-api |

## Cadeia vigente

`Portal Suprimentos → supplies-api → api-delpi → TOTVS`

## Avaliação de boundary para R04 (Controladoria)

- O produtor canônico está em **api-delpi** — reutilizável pela
  controllership-finance-api pelo mesmo S2S existente (padrão R09).
- O `supplies-api` NÃO deve ser chamado pela Controladoria (boundary
  de outro contexto).
- **DECISION_REQUIRED**: os use cases estão no namespace `supplies`
  da api-delpi — reuso do produtor por outro domínio exige aprovação
  do owner (api-delpi) para exponê-lo ao contrato financeiro.
- Sem artefato MATR860: equivalência funcional com o relatório oficial
  NÃO comprovada — não declarar paridade.

## Lacunas conhecidas

- Semântica previsto × realizado vs movimentos por material: por verificar.
- Owner funcional da Controladoria: não confirmado.
- Contrato BFF financeiro R04: inexistente — requer decisão de boundary.
