# ADR-006 — Permissão de unidade ortogonal (SC, ES e futuras)

| Campo | Valor |
|-------|--------|
| Status | Aceito (PO, 2026-09-08) |
| Contexto | Portal Suprimentos é multi-unidade |
| Relacionados | [PERFIS-E-PERMISSOES.md](../PERFIS-E-PERMISSOES.md), [ADR-004](./ADR-004-plugin-identity-and-css-root.md), [ADR-007](./ADR-007-permission-minimization.md) |

---

## Contexto

O departamento opera em mais de uma unidade TOTVS (hoje SC `01` e ES `02`; outras podem nascer). O legado mistura capability sem unidade, unidade colada na feature e unidade separada.

O Product Owner definiu que haverá **um único eixo de permission para direcionar unidades**, sem inflar as demais capabilities.

## Decisão

Dois eixos independentes, complementados por escopo de recurso:

```text
eixo A — capability de negócio mínima
  AND
eixo B — unidade autorizada
  AND
resource scope / ownership
  → ação autorizada
```

1. Uma permission por unidade: `supplies.unit.filial-{codigo_totvs}`.
   - SC → `supplies.unit.filial-01`
   - ES → `supplies.unit.filial-02`
   - futura filial `03` → somente `supplies.unit.filial-03`
2. Capabilities funcionais não ganham variante por unidade.
3. Nova unidade = 1 entrada no catálogo + 1 permission no manifest + atribuição aos papéis.
4. Capability sem nenhuma unit = fail-closed para dado TOTVS.
5. Administração não significa todas as unidades.
6. `purchase-requests.view-all` continua bypass de centro de custo, não de unidade.
7. Aliases legados resolvem para o eixo B durante coexistência.
8. A lista de unidades autorizadas é derivada das **permissions efetivas resolvidas pelo Core API**, não da lista de permissions nos claims JWT.

## Authz Core-first

O JWT Keycloak serve para identidade/contexto e deve ser validado normalmente. A autorização efetiva usa o resultado canônico do Core API (`/me` ou mecanismo compartilhado equivalente).

```text
JWT válido
  ↓
resolver permissions efetivas no Core
  ↓
allowedUnits = permissions efetivas ∩ catálogo de unidades
  ↓
validar branch
```

Query `branch` fora de `allowedUnits` → 403.  
`branch` omitido → recorte = união das unidades efetivamente autorizadas; nunca empresa inteira por default.

## Catálogo

| Código TOTVS | Permission | Label UI |
|---|---|---|
| `01` | `supplies.unit.filial-01` | Santa Catarina (SC) |
| `02` | `supplies.unit.filial-02` | Espírito Santo (ES) |
| `XX` | `supplies.unit.filial-XX` | nome da unidade |

## O que é proibido

- `supplies.{feature}.{action}.filial-*` novo;
- `if unit == "SC"` no MFE;
- criar uma nova permission funcional a cada unidade;
- usar `manage` como bypass automático de unidade;
- confiar em `claims.permissions` ou `claims.is_superadmin` como autorização final;
- interpretar branch omitido como acesso corporativo irrestrito.

## Consequências

Papel «Comprador SC» = capabilities necessárias + `supplies.unit.filial-01`.  
Papel «Analista SC e ES» = capabilities necessárias + `filial-01` + `filial-02`.  
Nova unidade não altera permissions funcionais.
