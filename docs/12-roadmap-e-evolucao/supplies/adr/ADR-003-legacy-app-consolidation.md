# ADR-003 — Consolidação dos apps legados de Suprimentos

| Campo | Valor |
|-------|--------|
| Status | Aceito (estratégia) · **nenhum cutover nesta etapa** |
| Data | 2026-09-08 |
| Relacionados | [INVENTARIO-ATIVOS.md](../INVENTARIO-ATIVOS.md), [HOMOLOGACAO-PARIDADE.md](../HOMOLOGACAO-PARIDADE.md), [CUTOVER-RUNBOOK.md](../CUTOVER-RUNBOOK.md) |

---

## Contexto

A experiência atual está espalhada em MFEs nativos, um BFF, KPIs SI/TV, planilha IDD e **seis apps evidentes só na RBAC do Product Owner** (sem manifesto no git).

Remover qualquer um agora quebraria favoritos, launcher e deep links.

## Decisão

Modelo obrigatório (igual F2c Comercial, adaptado):

```text
COEXISTÊNCIA
  → IMPLEMENTAR EQUIVALENTE NO PORTAL
  → VALIDAR PARIDADE
  → HOMOLOGAR (owner Suprimentos + QA)
  → REDIRECT / ALIAS
  → OCULTAR LAUNCHER LEGADO
  → PERÍODO DE SEGURANÇA
  → REMOVER SOMENTE COM ESTE ADR ATUALIZADO + RUNBOOK
```

### Destino por família

| Ativo | Decisão Portal | Cutover |
|-------|----------------|---------|
| `dashboard-supplies` | **DEPRECIAR_APOS_PARIDADE** | Após Visão Geral + páginas CPV/OTD/estoque/giro/savings |
| `purchase-requests` MFE | **DEPRECIAR_APOS_PARIDADE** | Após C3 do ADR-002 |
| `purchase-requests-api` | **DEPRECIAR_APOS_PARIDADE** | Após C3 |
| `estoque-seguranca` | **DEPRECIAR_APOS_PARIDADE** | Após Estoque de Segurança + Análise de consumo no Portal |
| `materiais-terceiros` | **FORA_DO_ESCOPO** (beneficiamento de **cliente**, não compra) | Permanece app próprio; deep link opcional |
| `inspecoes-entrada` | **INTEGRAR** (projeção no Fornecedor 360) | Processo continua na Qualidade |
| Frete (`financial/freight`) | **DEEP_LINK** | Financeiro permanece dono |
| SI departamento `supplies` | **INTEGRAR** | SI continua dono de meta/realizado |
| TV `supplies_*` | **INTEGRAR** | TV continua dono da tela nativa |
| Sheets IDD / savings | **INTEGRAR** via api-delpi já existente; meta canônica = SI | Planilha não vira segunda fonte de meta |
| 6 BIs do PO | **LEGADO_A_VALIDAR** até dump Core (ADR-005) | Sem URL no git, sem redirect inventado |

## Não fazer

- Remover plugin, Compose, manifesto ou permissão nesta documentação.
- Redirect para path que ainda não existe.
- Tratar Power BI como «inexistente» só porque não está em `plugins/`.
- Unificar `materiais-terceiros` no Portal só porque o path api-delpi é `/supplies/third-party-materials`.

## Atualização deste ADR

Quando um ativo completar paridade, registrar data, checklist e runbook executado. Remoção de código exige autorização explícita do PO + atualização deste ADR para **executado**.
