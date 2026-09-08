# ADR-003 — Consolidação dos apps legados de Suprimentos

| Campo | Valor |
|-------|--------|
| Status | Aceito (estratégia) · nenhum cutover nesta etapa |
| Data | 2026-09-08 |
| Relacionados | [ADR-002](./ADR-002-purchase-requests-api.md), [ADR-005](./ADR-005-external-bi-core-dump.md), [HOMOLOGACAO-PARIDADE.md](../HOMOLOGACAO-PARIDADE.md), [CUTOVER-RUNBOOK.md](../CUTOVER-RUNBOOK.md) |

---

## Contexto

A experiência atual está espalhada em MFEs nativos, BFF próprio de Solicitações, KPIs SI/TV, planilha IDD e seis apps/BIs evidenciados pelo Product Owner que ainda precisam de dump do Core.

Remover qualquer ativo sem paridade pode quebrar launcher, favoritos, deep links, filtros e processos não visíveis no git.

## Decisão

Modelo obrigatório:

```text
COEXISTÊNCIA
→ IMPLEMENTAR EQUIVALENTE / INTEGRAR
→ VALIDAR DADOS E FUNCIONALIDADE
→ HOMOLOGAR
→ TARGET NOVO SAUDÁVEL
→ RBAC CANÔNICO VALIDADO
→ REDIRECT / ALIAS
→ OCULTAR LAUNCHER LEGADO
→ OBSERVAR TELEMETRIA
→ REMOVER SOMENTE COM CRITÉRIOS COMPROVADOS
```

Para Purchase Requests há uma restrição adicional:

```text
C1 composição
→ C2 ownership do schema/jobs + reconciliação
→ paridade final
→ C3 cutover/desligamento
```

C3 nunca ocorre antes de C2.

### Destino por família

| Ativo | Decisão Portal | Condição de cutover |
|---|---|---|
| `dashboard-supplies` | DEPRECIAR_APOS_PARIDADE | Overview + focos + dados/performance homologados |
| `purchase-requests` MFE | DEPRECIAR_APOS_PARIDADE | C2 concluído + paridade final + C3 |
| `purchase-requests-api` | DEPRECIAR_APOS_PARIDADE | supplies-api assume estado/jobs e reconcilia antes do desligamento |
| `estoque-seguranca` | DEPRECIAR_APOS_PARIDADE | estoque segurança + consumo homologados |
| `materiais-terceiros` | FORA_DO_ESCOPO | permanece contexto próprio |
| `inspecoes-entrada` | INTEGRAR | Qualidade continua owner |
| Financeiro/frete | DEEP_LINK / projeção controlada | Financeiro continua owner |
| Strategic Indicators | INTEGRAR | SI continua owner de metas |
| TV `supplies_*` | INTEGRAR | TV continua owner da superfície |
| Sheets IDD/savings | INTEGRAR leitura | edição/origem permanece até decisão funcional |
| 6 BIs do PO | LEGADO_A_VALIDAR apenas durante E1 | antes do GO deve virar estado final permitido |

## Estados permitidos dos BIs no GO

```text
PARIDADE_HOMOLOGADA
MANTER_EXTERNO
DEEP_LINK
FORA_DO_ESCOPO_COM_ACEITE
```

`LEGADO_A_VALIDAR` não é permitido no `GATE-CUTOVER`.

## Redirect e launcher

Redirect só é ativado depois de:

- target novo saudável;
- manifest registrado;
- permissions canônicas provisionadas;
- `/me/apps` e `/me/routes` validados;
- smoke pela URL nova;
- paridade assinada.

Alias no BFF não substitui provisionamento de acesso no Core.

## Remoção

Não remover código apenas por decurso de tempo. Cada legado precisa declarar:

```text
owner
replacement
startDate
knownConsumers
telemetry
removalCriteria
rollback
```

A remoção exige atualização deste ADR para estado executado + evidência de critérios cumpridos.

## Não fazer

- redirect para path ainda não congelado;
- remover permission legada no mesmo instante do primeiro flip;
- tratar ausência no git como ausência operacional;
- deprecar app sem comparação quantitativa quando houver dado equivalente;
- chegar ao GO com BI ainda `LEGADO_A_VALIDAR`.
