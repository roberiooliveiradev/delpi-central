# ADR-006 — Permissão de unidade ortogonal (SC, ES e futuras)

| Campo | Valor |
|-------|--------|
| Status | Aceito (PO, 2026-09-08) |
| Contexto | Portal Suprimentos é multi-unidade |
| Relacionados | [PERFIS-E-PERMISSOES.md](../PERFIS-E-PERMISSOES.md), [ADR-004](./ADR-004-plugin-identity-and-css-root.md) |

---

## Contexto

O departamento opera em **mais de uma unidade TOTVS** (hoje SC `01` e ES `02`; outras podem nascer). O legado mistura dois modelos:

| Padrão | Exemplo | Problema |
|--------|---------|----------|
| Capability **sem** unidade | `dashboard-supplies.view` | Não direciona site |
| Unidade **colada na feature** | `estoque-seguranca.view.filial-sc` | Cada tela nova × cada site = explosão de codes |
| Unidade **separada** | `purchase-requests.unit.filial-01` | Escala: 1 code por site, reutilizado |

O Product Owner definiu: haverá **um tipo de permissão para direcionar unidades**, sem inflar as demais permissões.

`english-code-identifiers.mdc` já congela o sufixo `filial-01` / `filial-02` (não `branch-01`, não `filial-sc` em code **novo**).

## Decisão

Dois eixos independentes. **AND** para qualquer dado TOTVS.

```text
eixo A — o que a pessoa pode fazer     supplies.{recurso}.{ação}
eixo B — em quais unidades vê dado     supplies.unit.filial-{TOTVS}
```

1. **Uma permissão por unidade**, no prefixo `supplies.unit.filial-{codigo_totvs}`.
   - SC → `supplies.unit.filial-01`
   - ES → `supplies.unit.filial-02`
   - Futura filial TOTVS `03` → **somente** `supplies.unit.filial-03` (mais o rótulo PT no catálogo). Sem `supplies.inventory.view.filial-03`.
2. Capabilities de produto (`access`, `analytics.view`, `inventory.view`, `purchase-requests.view`, …) **não** ganham variante por unidade.
3. Catálogo de unidades é **uma lista** (código TOTVS + permission + label UI). Nova unidade = 1 linha + 1 permission no manifest. Zero alteração nas outras permissions.
4. Fail-closed: capability sem **nenhuma** unit → sem dado operacional/analítico de TOTVS (shell/Ajuda com `access` continuam).
5. `supplies.manage` **não** significa «todas as unidades». O papel Admin recebe `manage` **e** as unit perms necessárias. Bypass de unidade = só `is_superadmin` (auditado).
6. `purchase-requests.view-all` continua sendo bypass de **centro de custo**, não de unidade.
7. Aliases de coexistência (`purchase-requests.unit.filial-01`, `estoque-seguranca.view.filial-sc`, …) resolvem para o eixo B — não criam eixo duplicado no Portal.

## Autorização (BFF)

```text
pode_ver_recurso  = has(capability) OR has(alias_legado)
pode_ver_unidade  = has(supplies.unit.filial-XX) OR has(alias_unit_legado)
pode_ler_dado     = pode_ver_recurso AND pode_ver_unidade
```

Query `branch` fora das unidades do JWT → 403.  
`branch` omitido → recorte = **união das unidades do usuário** (não a empresa inteira). Consolidado SI/dashboard só nesse recorte.

## O que é proibido

- `supplies.{feature}.view.filial-sc` / `.filial-es` / `.filial-01` em code **novo**
- `if unit == "SC"` no MFE; o filtro usa o catálogo + caps
- Inflar `analytics.view` (ou qualquer cap) cada vez que nascer um site
- Permission nova com nome de cidade em português (`filial-joinville`)

## Alternativas rejeitadas

| Alternativa | Motivo |
|-------------|--------|
| Uma perm por tela × site | Inflaciona o catálogo a cada feature e cada unidade |
| Só `access` + filtro UX | Backend não validaria; viola RBAC |
| `manage` = todas as unidades | Infla `manage`; gestor de um site viraria dono do outro |
| `filial-sc` como canônico novo | Viola identificadores EN; DRIFT com SC já em `filial-01` |

## Consequência

Papel «Comprador SC»: capabilities de comprador **+** `supplies.unit.filial-01`.  
Papel «Analista SC e ES»: capabilities de analista **+** `filial-01` **e** `filial-02`.  
Nova unidade no TOTVS: registrar no catálogo, criar **um** code `supplies.unit.filial-XX`, atribuir nos papéis — as telas já existentes passam a respeitar sem permissão extra.
