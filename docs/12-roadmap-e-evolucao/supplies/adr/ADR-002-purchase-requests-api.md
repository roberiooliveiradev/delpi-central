# ADR-002 — Destino da purchase-requests-api

| Campo | Valor |
|-------|--------|
| Status | Aceito (documentação) · **não implementado** |
| Data | 2026-09-08 |
| Contexto | Painel Solicitações de Compras já é BC próprio; o Portal precisa de uma API de produto |
| Relacionados | [ADR-001](./ADR-001-supplies-api.md), [ADR-003](./ADR-003-legacy-app-consolidation.md), contrato [01-contrato-api.md](../../solicitacoes-compras/01-contrato-api.md) |

---

## Contexto

`purchase-requests-api` **já é** o bounded context correto para:

- escopo por centro de custo (schema `purchase_requests.visibility_scopes*`);
- mapping usuário Minha DELPI ↔ Protheus;
- agregação de linhas SC (grão `C1_FILIAL+C1_NUM+C1_ITEM`);
- notificações de PC vinculado e recebimento;
- fail-closed (`.access` sem CC e sem `.view-all` = zero registros).

Evidência: **CONFIRMADO_NO_CODIGO** (`purchase-requests-api/migrations/V001`–`V004`, `purchase_requests_permissions.py`, contrato Fase 0.2).

O Portal Comercial enfrentou caso irmão: estado Delpi nasceu no lugar errado (api-delpi / PVA) e foi **migrado** para `commercial-api`, depois o MFE legado foi removido (F2c). Aqui o estado Delpi **já está no lugar certo** — só não é a API do produto-portal.

Permanecer para sempre com duas APIs de produto no mesmo departamento geraria:

- MFE do Portal falando com dois backends, **ou** hop eterno `supplies-api → purchase-requests-api`;
- dois OpenAPI, dois JWT middlewares, duas receitas de deploy para uma UX única;
- risco de duplicar escopo CC se a supplies-api «reimplementar» SC.

## Decisão

**Absorção progressiva pela `supplies-api`.** Não é BC irmão permanente do Portal. Não é big-bang.

### Fases

| Fase | Comportamento | Owner do estado CC |
|------|---------------|--------------------|
| **C0 coexistência** | MFE `purchase-requests` inalterado. Portal faz **deep link** `/apps/purchase-requests` até paridade de lista. `supplies-api` **não** duplica escopo CC. | `purchase-requests-api` |
| **C1 composição** | `supplies-api` expõe BFF `/purchase-requests*` que **gateway HTTP** para `purchase-requests-api` (não para api-delpi). MFE Portal consome só supplies-api. | `purchase-requests-api` |
| **C2 migração de schema** | Mover schema `purchase_requests` para ownership da `supplies-api` (mesmo Postgres; **não** copiar TOTVS). Jobs de notificação passam a rodar na supplies-api Flask. **Um único writer** no schema: desligar jobs/gravações da `purchase-requests-api` antes dos da Flask. Dual-read + reconciliação de contagens. | transição |
| **C3 cutover** | MFE `purchase-requests` oculto + redirects. `purchase-requests-api` desligada após smoke. Permissões antigas viram **aliases**. | `supplies-api` |

Critério para avançar C1→C2: paridade da lista/detalhe/export/admin no Portal + testes de fail-closed + filial.

Critério para C3: [HOMOLOGACAO-PARIDADE.md](../HOMOLOGACAO-PARIDADE.md) seção purchase-requests 100% + ADR-003.

### O que NÃO muda

- SQL SC1/SC7/SD1 permanece na **api-delpi**.
- Princípios do contrato Fase 0.2 (grão item, autorização antes da agregação, fail-closed, filial obrigatória, comprador ≠ `C7_USER`).
- Permissões `purchase-requests.*` e `unit.filial-01/02` como **aliases** até limpeza de papéis.

## Por que não as outras opções

| Opção | Veredito | Motivo |
|-------|----------|--------|
| Permanência eterna como BC independente | **Rejeitada** | Dois produtos no mesmo departamento; MFE único exigiria dois clientes HTTP ou BFF oco para sempre |
| Absorção imediata (C2 no dia 1) | **Rejeitada** | Schema + jobs + fail-closed já estão em produção; big-bang viola coexistência |
| Mover SQL TOTVS para supplies-api | **Rejeitada** | Missão da api-delpi |
| Nova API `purchase-requests-bff` extra | **Rejeitada** | Infla superfície sem dono de produto |

## Hipótese a validar na C2 (não bloqueia C0/C1)

`HIPOTESE_A_VALIDAR`: volume e janela de downtime aceitáveis para trocar o dono do schema sem dual-write longo. Subetapa E6.S4 do [IMPLEMENTATION-PLAN.md](../IMPLEMENTATION-PLAN.md) obtém essa evidência (contagem de rows, jobs, subscribers) **antes** de migrar.

## Consequências

- Features novas de SC (aging, worklist do comprador) nascem na **supplies-api** a partir de C1, mesmo que o dado TOTVS venha via api-delpi.
- `purchase-requests-api` entra em **freeze de produto** após C1: só correção de bug / segurança.
- Consumidores irmãos (`production-control` → `open-coverage` na **api-delpi**) **não** passam pela supplies-api.

## Referências

- Contrato: `docs/12-roadmap-e-evolucao/solicitacoes-compras/01-contrato-api.md`
- Analogia: `docs/12-roadmap-e-evolucao/commercial/adr/ADR-002-deprecar-pedidos-venda-abertos.md`
