# Alimentador de Linha — Etapa 4: interface de coleta dinâmica

**TASK_ID:** `PC-LINE-FEEDER-UI-E4`  
**Status:** implementado (MFE Production Control)  
**Depende de:** E1 PUBLISHED + E2 horizonte + E3 materials (+ rework E3)

## Decisão de negócio

Fluxo principal:

`Coletar → selecionar CTs → horas por CT → consultar materiais → lista consolidada`

- **Coletar** gera consulta operacional (fotografia), não confirma retirada física.
- Sem marcação separado/entregue, sem fechar lista, sem reserva virtual, sem escrita no Protheus.
- `to_collect = max(0, required_from_horizon − factory_available)` permanece no backend.
- Solicitações urgentes do operador continuam em painel **separado**.

## Inventário / reuso

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Modal host-contained | YES (`PpcConfirmModal` / `createHostContainedModalShell`) | REUSE (`HostContainedWideDialog`) |
| Multiseleção de CTs | YES (`createDashboardMultiSelectField`) | REUSE (`LineFeederWorkCenterMultiSelect`) |
| Tabela/cards | YES (`DataTableSection`) | REUSE |
| KPI / status badge | YES (`createDashboardKpiCard` / `StatusBadge`) | REUSE |
| Fila publicada | YES API E1 | REUSE (`GET /line-feeder/published-queue`) |
| Prévia materiais | YES API E3 | REUSE (`POST /line-feeder/materials/preview`) |
| Página principal | YES legado cutoff/pick-plans | NEW fluxo (substitui UX principal) |
| Pick-plans / requirements UI | YES legado | PRESERVE código/API; **fora** do fluxo principal |
| Urgentes operador | YES C5 | REUSE painel independente |

## Contratos consumidos

```http
GET  /line-feeder/published-queue?branch=XX
POST /line-feeder/materials/preview
Body: { "branch", "workCenters", "hoursPerWorkCenter" }
```

O frontend **não** recalcula materiais, saldos nem horas; respeita `operational_list_safe`.

## Estados

| Situação | UX |
|---|---|
| Sem consulta | Orientação para abrir Coletar |
| Sem publicação (404) | Mensagem: PCP ainda não publicou |
| Prévia incompleta | Alerta; lista não tratada como coleta confiável |
| HTTP 409 | Pedir nova consulta |
| Sem empenhos (safe + warnings) | Mensagem específica (não confundir com estoque coberto) |
| Só cobertos | “Nenhuma coleta necessária…” |
| Urgentes | Painel separado |

## Compatibilidade

- Endpoints e tabelas de pick-plans preservados.
- Links antigos com `cutoffDate`/`plan` abrem a página sem quebrar; URL canônica fica `?branch=`.
- APIs legadas não removidas.

## Testes

- Estrutural da página (fonte de dados E3; sem pick-plan no fluxo novo).
- Modal Coletar (CTs, select all, validação de horas, 404).
- Hook de prévia (request, reload, 409, race de filial).
- Painel de materiais (coleta 60, unsafe, sem empenhos).
