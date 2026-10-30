# Fichas técnicas R01–R15 — conhecimento governado da CLARA

Versão 1.1 · 31/10/2026 · Execução
`CF-PROC0072-CLARA-KNOWLEDGE-R01-R15-IMPLEMENTATION-STAGE-04`
(doc 127 Etapa 4; decisão D-06 do doc 126).

Publicação produtiva: corpus `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00`
(88 fontes / 2.186 itens) no release stage-05, 30/10/2026 —
`CF-PROC0072-CONTROLLERSHIP-RELEASE-STAGE-05` (doc 127 Etapa 5).

Conjunto canônico e versionado de fichas técnicas dos relatórios do
processo de fechamento mensal (PROC-0072). Cada ficha consolida —
com classificação de evidência por afirmação
(`PROVEN | TO_INVENTORY | PLANNED | TARGET`) — identificação, fontes,
regras de seleção, interpretação, operação, limites de comparação e
governança. As fichas são a base citável da CLARA via `knowledge`;
dados reais continuam sendo obtidos por `read`/`analyze` — a ficha
**interpreta**, nunca substitui a consulta autorizada.

**Não afirmar como fato o que está `PENDING`/`TO_INVENTORY`.** Estado de
implementação ≠ paridade oficial: paridade técnica não é aceite
funcional (G6 `PENDING` em todos os relatórios).

## Matriz de inventário (GATE A)

| Ficha | Relatório | Implementação | Capability CLARA | Corpus/Help | Lacunas principais |
|---|---|---|---|---|---|
| [R01](R01-ficha.md) | Baixas a pagar | `IMPLEMENTED` (`/closing/financial-settlements*`) | `read(report.settlements_summary)` | ficha + docs 84/85 | produtor R02 compartilha dúvidas; G6 |
| [R02](R02-ficha.md) | Baixas a receber | `IMPLEMENTED` (mesmo contrato R01) | `read(report.settlements_summary)` | ficha + docs 84/85 | fonte `DLP06R01` ausente (E1); G4/G6 |
| [R03](R03-ficha.md) | P7 / Registro de Inventário | `IMPLEMENTED` (`/closing/stock-inventory`, IMP-006) | `read(report.stock_inventory)` | ficha + docs 49/84/85/119 | parâmetros MATR460 efetivos (E2); `officialP7=false`; G6 |
| [R04](R04-ficha.md) | Consumo por OP | `NOT_IMPLEMENTED` (BLOQUEADO, sem artefato) | — (nenhuma) | ficha + docs 85/118 | GAP-01; sem produtor confirmado |
| [R05](R05-ficha.md) | Entradas e Saídas (MATR320) | `IMPLEMENTED` (`/closing/stock-movements`, IMP-009) | `read(report.stock_movements)` | ficha + docs 84/85 | `officialMatr320=false`; G6 |
| [R06](R06-ficha.md) | Kardex / saídas × CPV | `IMPLEMENTED` (`/closing/kardex` + `/closing/cpv`, IMP-015) | `read(report.kardex)`, `read(report.cpv)` | ficha + docs 61/84/85/122 | RPO/E7; paridade oficial G6; CPV vivo |
| [R07](R07-ficha.md) | Inventários | `IMPLEMENTED` (`/closing/inventory-adjustments`, IMP-015) | `read(report.inventory_adjustments)` | ficha + docs 66/84/85/122 | loc de emissão; G6 |
| [R08](R08-ficha.md) | Material em Processo (MATR989/H02) | `IMPLEMENTED` (`/closing/work-in-process`, IMP-009) | `read(report.work_in_process)` | ficha + docs 63/64/84/85 | fonte MATR989 ausente (E8); `officialMatr989=false` |
| [R09](R09-ficha.md) | Faturamento × MOD (DLP204) | `TARGET_ONLY` (modelo físico PROVEN, sem contrato) | — (nenhuma) | ficha + docs 65/85 | SP `STP_DELPI_FORMA_PRECO` ausente (E9); G5 |
| [R10](R10-ficha.md) | Notas/Despesas por Centro de Custo | `IMPLEMENTED` (`/closing/cost-center-expenses`, stage-01) | `read(report.cost_center_expenses)` | ficha + docs 77/85/126/127 | E10a/E10b (classe/audit); CTT; TES 12-vs-13; G6 |
| [R11](R11-ficha.md) | NF a desconsiderar | `IMPLEMENTED` (`/closing/billing-exclusion-roster`, stage-02) | `read(report.billing_exclusion_roster)` | ficha + docs 67/85/126/127 | E11a/E11b; predicado oficial; G6 |
| [R12](R12-ficha.md) | Fechamento de custo / Reposição / Refaz | `TARGET_ONLY` (execução no ERP; estado consultável) | — (sem medida numérica) | ficha + docs 85/118 | etapa 4 do wizard (G5); writer MV_ULMES (E5) |
| [R13](R13-ficha.md) | Extratos e aplicações | `SOURCE_UNAVAILABLE` (fonte externa bancária) | — (nenhuma) | ficha + docs 85/118 | contrato de entrada externo; P2 upload TARGET |
| [R14](R14-ficha.md) | Importação / câmbio | `SOURCE_UNAVAILABLE` (sem evidência) | — (nenhuma) | ficha + docs 85/118 | `BLOQUEADO`; nenhum artefato |
| [R15](R15-ficha.md) | Cutoff / virada / SB9 | `TARGET_ONLY` (estado lido via fechamento, sem relatório) | — (sem medida numérica) | ficha + docs 85/118 | writer SB9 por timing (E5); reabertura (E12) |

Legenda de implementação: `IMPLEMENTED` (contrato em runtime),
`OPERATIONAL_VIEW` (visão auxiliar sem relatório oficial),
`TARGET_ONLY` (desenho aprovado sem runtime), `SOURCE_UNAVAILABLE`
(fonte fora do Protheus), `NOT_IMPLEMENTED`.

Capabilities transversais além do `read` por relatório:
`analyze(report_comparison)` (stage-03 — matriz de compatibilidade nas
fichas §comparação), `knowledge` (estas fichas + docs canônicos),
`get_context` (catálogo e schemas). Superfície MCP permanece com seis
tools — nenhuma tool plana por relatório.

## Índice das fichas

- [R01 — Baixas a pagar](R01-ficha.md)
- [R02 — Baixas a receber](R02-ficha.md)
- [R03 — P7 / Registro de Inventário](R03-ficha.md)
- [R04 — Consumo por OP](R04-ficha.md)
- [R05 — Entradas e Saídas (MATR320)](R05-ficha.md)
- [R06 — Kardex / CPV](R06-ficha.md)
- [R07 — Inventários](R07-ficha.md)
- [R08 — Material em Processo (MATR989/H02)](R08-ficha.md)
- [R09 — Faturamento × MOD (DLP204)](R09-ficha.md)
- [R10 — Notas/Despesas por Centro de Custo](R10-ficha.md)
- [R11 — Notas Fiscais a Desconsiderar](R11-ficha.md)
- [R12 — Fechamento de custo / Reposição / Refaz Saldos](R12-ficha.md)
- [R13 — Extratos e aplicações](R13-ficha.md)
- [R14 — Importação / câmbio](R14-ficha.md)
- [R15 — Cutoff / sacramentação / SB9](R15-ficha.md)

## Processo (conhecimento operacional)

- [PROC-0072 — ficha do processo de fechamento](processo-fechamento-ficha.md)
