# MANIFEST-DRAFT — Portal Suprimentos

> **Status:** contrato documental pré-implementação. Não registrar no Core nesta etapa.

Objetivo: congelar identidade, rotas e permissions antes do scaffold do MFE.

---

## 1. Identidade

| Campo | Valor |
|---|---|
| schemaVersion | `2.0.0` |
| id | `supplies` |
| name | `Portal Suprimentos` |
| type | `microfrontend` |
| version inicial | `0.1.0` proposta |
| basePath | `/apps/supplies` |
| entry | `/apps/supplies/assets/remoteEntry.js` proposta |
| backend.required | `true` |
| backend.serviceName | `supplies-api` |
| backend.baseUrl | `/apps/supplies-api` |

A versão/path final deve ser validada contra o schema/runtime real do Core antes da implementação.

---

## 2. Permission catalog P0/P1

Catálogo deliberadamente mínimo conforme ADR-007.

| Permission | Finalidade | Status |
|---|---|---|
| `supplies.portal.access` | entrar no Portal, Home, Ajuda, busca, preferências | canônica |
| `supplies.purchase-requests.access` | jornada SC dentro do escopo autorizado | canônica |
| `supplies.operations.access` | compras operacionais, pedidos, fornecedor/produto/estoque, follow-ups/notas | canônica |
| `supplies.analytics.access` | Overview, KPIs e análises | canônica |
| `supplies.administration.manage` | administração/configurações/mappings/scopes | canônica |
| `supplies.purchase-requests.view-all` | bypass de CC dentro da unidade | canônica/exceção |
| `supplies.purchase-requests.export` | exportação de SC enquanto risco/auditoria justificar segregação | canônica/exceção |
| `supplies.unit.filial-01` | unidade SC | canônica |
| `supplies.unit.filial-02` | unidade ES | canônica |

Não declarar no manifest P0 permissions CRUD como `tasks.view/write`, `supplier-notes.write`, `products.view`, `inventory.view` etc. sem nova decisão fundamentada.

---

## 3. Routes draft

O Portal possui uma rota launcher principal. Rotas internas são controladas pelo MFE/capabilities; se o schema/Core exigir rotas adicionais registradas, congelar a matriz abaixo antes do registro.

| UI route | Permission funcional | Menu | Status |
|---|---|---:|---|
| `/apps/supplies` | `supplies.portal.access` | sim | P0 |
| `/apps/supplies/overview` | `supplies.analytics.access` | interno | P0 |
| `/apps/supplies/my-tasks` | `supplies.portal.access` + authz por recurso | interno | P0 |
| `/apps/supplies/purchase-requests` | `supplies.purchase-requests.access` | interno | P0 |
| `/apps/supplies/purchase-orders` | `supplies.operations.access` | interno | P0 |
| `/apps/supplies/deliveries` | `supplies.operations.access` | interno | P0 |
| `/apps/supplies/suppliers` | `supplies.operations.access` | interno | P0 |
| `/apps/supplies/products` | `supplies.operations.access` | interno | P0 |
| `/apps/supplies/inventory` | `supplies.operations.access` | interno | P0 |
| `/apps/supplies/safety-stock` | `supplies.operations.access` | interno | P0 |
| `/apps/supplies/negotiations` | `supplies.analytics.access` | interno | P0/P1 |
| `/apps/supplies/indicators` | `supplies.analytics.access` | interno | P0/P1 |
| `/apps/supplies/administration` | `supplies.administration.manage` | interno | P0/P1 |
| `/apps/supplies/help` | `supplies.portal.access` | interno | P0 |
| `/apps/supplies/imports` | a decidir após E1.S1 | não antes do dump | BLOQUEADO |
| `/apps/supplies/approvals` | a decidir após prova de workflow/segregação | não antes da validação | BLOQUEADO |

---

## 4. Aliases legados

Aliases não são permissions canônicas do manifest novo. Servem para coexistência e migração:

- `dashboard-supplies.view` → analytics;
- `purchase-requests.access` → purchase-requests;
- `purchase-requests.view-all` → view-all;
- `purchase-requests.export` → export;
- `purchase-requests.admin` → administration;
- `purchase-requests.unit.filial-01/02` → units;
- `estoque-seguranca.access` → operations;
- `estoque-seguranca.view.filial-sc/es` → units.

Aliases no BFF **não fazem o Portal aparecer em `/me/apps`**. A fase de coexistência deve provisionar as permissions canônicas nos papéis/grupos corretos do Core.

---

## 5. Backend/authz

- JWT validado para identidade;
- effective permissions resolvidas pelo Core API;
- unit scope pelo ADR-006;
- permission minimization pelo ADR-007;
- backend é a barreira real de segurança;
- MFE só usa capabilities para UX.

---

## 6. Segurança e observabilidade

Draft deve declarar, conforme schema real vigente:

- JWT validation;
- HTTPS/gateway;
- CSP/iframe conforme contrato;
- health/ready;
- log estruturado;
- request/correlation id;
- métricas do serviço.

Não copiar campos de exemplo do manifesto oficial se o Core runtime não os suporta. Antes do E3, validar draft contra schema/registrador real.

---

## 7. Gate

`GATE-DOC-MANIFEST` passa quando:

- schema runtime real foi verificado;
- nenhuma permission canônica redundante/CRUD permanece;
- rota launcher e permissions não colidem;
- `/me/apps` e `/me/routes` de coexistência estão planejados;
- aliases têm estratégia de remoção.
