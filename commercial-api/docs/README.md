# commercial-api — documentação

API dona do estado Delpi do **Portal Comercial** (carteiras, worklist, contatos locais, enrichment BFF). Reads TOTVS via gateway para **api-delpi** — o MFE não chama api-delpi direto.

## Roadmap / atas

| Doc | Uso |
|-----|-----|
| [ATA-ALINHAMENTO-AGO2026-2.md](../../docs/12-roadmap-e-evolucao/commercial/ATA-ALINHAMENTO-AGO2026-2.md) | Ata alinhamento 2 — backlog P0–P2; confirmação de pedidos / sala / Diretoria / MyVEG = **futuro** (não implementar nesta onda) |
| [API-ROUTES.md](../../docs/12-roadmap-e-evolucao/commercial/API-ROUTES.md) | Contrato alvo de rotas (placeholders F7 §3.13 confirmação) |
| [SCOPE-OWNERSHIP.md](../../docs/12-roadmap-e-evolucao/commercial/SCOPE-OWNERSHIP.md) | Ownership Portal × PVA |

## Architecture (neste pacote)

| Doc | Tema |
|-----|------|
| [architecture/realtime-worklist.md](./architecture/realtime-worklist.md) | WS worklist / presença |

Confirmação de pedidos, sala de interação e realtime ampliado para esses fluxos entram como epicos **após** a spec da ATA-2 — não inventar rotas/contratos aqui antes do epico.
