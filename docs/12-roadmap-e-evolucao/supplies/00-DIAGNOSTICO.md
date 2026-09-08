# 00 — Diagnóstico: Suprimentos na Minha DELPI hoje

> **Data:** 2026-09-08 · **Escopo:** monorepo + evidência do Product Owner  
> **Implementação:** nenhuma

---

## Como Suprimentos trabalha hoje

Não existe um portal unificado. O usuário entra na Minha DELPI e escolhe vários apps no launcher, com filtros, filiais e vocabulários diferentes.

```text
Usuário de Suprimentos
  ├── Dashboard Suprimentos
  ├── Solicitações de Compras
  ├── Estoque de Segurança
  ├── Análise - Importações                  (evidência PO)
  ├── Onde o item é usado - BI              (evidência PO)
  ├── Atraso de Fornecedores - SC - BI      (evidência PO)
  ├── Alçada de Compras - BI                (evidência PO)
  ├── Controle de Estoques - SC - BI        (evidência PO)
  ├── Indicadores de Suprimentos - Sheets   (evidência PO)
  ├── Strategic Indicators
  ├── Chat Minha DELPI
  └── Apps adjacentes: Qualidade, Financeiro, PCP
```

Os três MFEs nativos, SI, chat e integrações adjacentes estão confirmados no código. Os seis apps/BIs externos foram confirmados por evidência do Product Owner, mas ainda precisam de dump do Core para contrato técnico.

---

## Personas

Papéis são dinâmicos e não devem ser usados como regra de autorização no MFE.

| Persona | Evidência | Uso atual |
|---|---|---|
| Analista de Suprimentos | SC e ES | Dashboard + Importações |
| Comprador | SC evidenciado; ES a validar | BIs operacionais + ESTSEG |
| Solicitante/gestor CC | inferido pelo módulo SC | Solicitações dentro do escopo |
| Admin compras | inferido pelo módulo SC | mapping/scopes/notificações |
| Gestor | inferido | dashboard/SI/TV |

O Portal alvo será capability-driven, com unit scope independente.

---

## Apps nativos

| App | basePath | Permission atual | Backend atual |
|---|---|---|---|
| Dashboard Suprimentos | `/apps/dashboard-supplies` | `dashboard-supplies.view` | api-delpi direto |
| Solicitações de Compras | `/apps/purchase-requests` | `purchase-requests.access` | purchase-requests-api → api-delpi |
| Estoque de Segurança | `/apps/estoque-seguranca` | `estoque-seguranca.access` + filial | api-delpi safety-stock direto |
| Materiais de Terceiros | `/apps/materiais-terceiros` | legado próprio | fora do escopo de compras |

---

## BIs / iframe / Sheets

| Nome | No git? | Equivalente parcial |
|---|---:|---|
| Análise - Importações | não | nenhum MFE nativo identificado |
| Onde o item é usado - BI | não | `get_product_parents` |
| Atraso de Fornecedores - SC | não | OTD/panel/ranking existentes |
| Alçada de Compras | não | campos TOTVS; workflow não comprovado |
| Controle de Estoques - SC | não | dashboard stock + ESTSEG + stock-balances |
| Indicadores Sheets | integração parcial | savings via Sheets + SI |

Nenhum desses seis pode ser depreciado apenas por existir equivalente parcial.

---

## APIs

| API | Papel atual/alvo |
|---|---|
| api-delpi | SQL/regra canônica TOTVS |
| purchase-requests-api | SC, escopo CC e jobs até C2 |
| strategic-indicators-api | metas/indicadores |
| financial-api | frete/financeiro |
| Qualidade | inspeções e rejeições |
| minha-delpi-ai-api | chat/tools |
| supplies-api | ainda inexistente; futura API do Portal |

---

## Dores principais

1. Trabalho fragmentado em vários apps/BIs.
2. Filtros e nomenclaturas de filial inconsistentes.
3. Conceitos sobrepostos: atraso/OTD, estoque/ESTSEG/giro, Sheets/SI.
4. Item e fornecedor sem visão 360.
5. Ausência de worklist/follow-up nativo.
6. MFEs legados chamam api-delpi direto, incompatível com novo Portal com API própria.
7. BIs externos não estão documentados no monorepo.
8. Catálogos históricos de permission são heterogêneos e podem induzir inflação de RBAC.
9. Há drift entre a regra oficial de authz Core-first e implementações legadas que podem confiar em claims JWT.
10. Há drift de framework: instrução oficial Flask × APIs departamentais recentes em FastAPI.

---

## Decisões corretivas para o Portal

### Authz

```text
JWT = identidade
Core /me = effective permissions
backend = autorização real
```

Nenhuma decisão nova de acesso deve depender de `claims.permissions` ou `claims.is_superadmin` como fonte final.

### RBAC

Aplicar ADR-007:

```text
menor catálogo suficiente
+ unit scope
+ resource scope / ownership
+ regra de negócio
```

Não criar permission por botão, endpoint ou verbo CRUD.

### Unidade

Eixo B único:

```text
supplies.unit.filial-01
supplies.unit.filial-02
```

Nova filial não replica permissions por feature.

### Framework

`supplies-api` = Flask enquanto a instrução oficial vigente assim determinar.

### Purchase Requests

```text
C0 coexistência
→ C1 composição
→ C2 ownership/jobs + reconciliação
→ paridade final
→ C3 cutover
```

---

## Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Depreciar BI sem paridade | ADR-005 + dump Core + homologação mensurável |
| C3 antes de C2 | IMPLEMENTATION-PLAN + ADR-002 |
| Authz por JWT claims ou fallback FastAPI sem Core | GATE-AUTHZ + ADR-001 DRIFT-AUTHZ-01 |
| Inflar permissions | ADR-007 |
| Alias BFF sem acesso no launcher | provisionamento RBAC + `/me/apps`/`/me/routes` |
| CSS colidir com dashboard legado | `.dashboard-supplies-portal` |
| Copiar TOTVS para Postgres | DATA-MODEL: somente estado Minha DELPI |
| Acoplar contextos irmãos | MATRIZ-BOUNDARIES |
| Inventar KPI | KPI-FICHAS + homologação |
| Cutover apontar para target instável | target-first / redirect-last |

---

## Oportunidade

Unificar necessidade → SC → PC → entrega → estoque → fornecedor em uma experiência única, preservando ownership dos contextos e reduzindo a fragmentação sem criar um novo monólito departamental.
