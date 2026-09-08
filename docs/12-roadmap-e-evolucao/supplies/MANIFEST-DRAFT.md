# MANIFEST-DRAFT — Portal Suprimentos

> **Status:** contrato documental pré-implementação · **E1.S4 freeze 2026-09-08**. Não registrar no Core nesta etapa.

Objetivo: congelar identidade, rotas e permissions antes do scaffold do MFE.

---

## 1. Validação contra runtime Core (E1.S4)

| Checagem | Evidência | Resultado |
|---|---|---|
| `schemaVersion` suportado | `ManifestVersionResolver.SUPPORTED_VERSIONS` = só `"1.0.0"` | **congelado `1.0.0`** (draft anterior `2.0.0` era DRIFT) |
| Schema JSON | `core-api/app/infrastructure/plugins/schemas/delpi.manifest.schema.json` — `schemaVersion` const `1.0.0` | alinhado |
| Manifest irmão | `plugins/commercial/commercial.manifest.json` | `1.0.0`, launcher + rotas internas, `ui.renderMode=federated`; **sem** bloco `backend` obrigatório |
| Catálogo permissions | ADR-007 — 7 capabilities/exceções + 2 units | sem CRUD |

`GATE-DOC-MANIFEST` documental: **PASS** para registro futuro na E3 (ainda **não** registrar agora).

---

## 2. Identidade

| Campo | Valor |
|---|---|
| schemaVersion | **`1.0.0`** |
| id | `supplies` |
| name | `Portal Suprimentos` |
| type | `microfrontend` |
| version | `0.1.0` |
| basePath | `/apps/supplies` |
| entry | `/apps/supplies/assets/remoteEntry.js` |
| icon | a definir no scaffold (ex. `package-icon`) |
| ui.renderMode | `federated` |

### Backend (opcional no schema; recomendado no draft)

Quando o registrador aceitar o objeto `backend`:

| Campo | Valor |
|---|---|
| required | `true` |
| serviceName | `supplies-api` |
| baseUrl | `/apps/supplies-api` |
| validateJwt | `true` |

Não inventar campos fora do schema 1.0.0. Se o Core de produção rejeitar `backend`, omitir no JSON de registro e manter o contrato HTTP na supplies-api / Compose.

---

## 3. Permission catalog P0/P1 (mínimo ADR-007)

| Permission | Finalidade | module | Status |
|---|---|---|---|
| `supplies.portal.access` | entrar no Portal, Home, Ajuda, busca, preferências | `supplies` | canônica |
| `supplies.purchase-requests.access` | jornada SC no escopo autorizado | `supplies` | canônica |
| `supplies.operations.access` | PC, entregas, fornecedor/produto/estoque, follow-ups/notas | `supplies` | canônica |
| `supplies.analytics.access` | Overview, KPIs e análises | `supplies` | canônica |
| `supplies.administration.manage` | admin/mappings/scopes/settings | `supplies` | canônica |
| `supplies.purchase-requests.view-all` | bypass de CC dentro da unidade | `supplies` | canônica/exceção |
| `supplies.purchase-requests.export` | exportação SC com segregação | `supplies` | canônica/exceção |
| `supplies.unit.filial-01` | unidade SC | `supplies` | canônica |
| `supplies.unit.filial-02` | unidade ES | `supplies` | canônica |

**Proibido no P0:** `tasks.view/write`, `supplier-notes.write`, `products.view`, `inventory.view`, `approvals.manage` sem evidência ADR-007.

---

## 4. Routes draft

Launcher obrigatório no manifest. Rotas internas seguem o padrão Comercial (registradas no Core com `showInMenu` conforme UX).

| UI route | Permission | showInMenu | Status |
|---|---|---:|---|
| `/apps/supplies` | `supplies.portal.access` | true | P0 |
| `/apps/supplies/overview` | `supplies.analytics.access` | false | P0 |
| `/apps/supplies/my-tasks` | `supplies.portal.access` | false | P0 |
| `/apps/supplies/purchase-requests` | `supplies.purchase-requests.access` | false | P0 |
| `/apps/supplies/purchase-orders` | `supplies.operations.access` | false | P0 |
| `/apps/supplies/deliveries` | `supplies.operations.access` | false | P0 |
| `/apps/supplies/suppliers` | `supplies.operations.access` | false | P0 |
| `/apps/supplies/products` | `supplies.operations.access` | false | P0 |
| `/apps/supplies/inventory` | `supplies.operations.access` | false | P0 |
| `/apps/supplies/safety-stock` | `supplies.operations.access` | false | P0 |
| `/apps/supplies/negotiations` | `supplies.analytics.access` | false | P0/P1 |
| `/apps/supplies/indicators` | `supplies.analytics.access` | false | P0/P1 |
| `/apps/supplies/administration` | `supplies.administration.manage` | false | P0/P1 |
| `/apps/supplies/help` | `supplies.portal.access` | false | P0 |
| `/apps/supplies/imports` | — | — | **BLOQUEADO** (E1.S1: BI sem id no Core local; sem dump prod) |
| `/apps/supplies/approvals` | — | — | **BLOQUEADO** (P-06: workflow não comprovado) |

Authz de rota no MFE é UX; barreira real = supplies-api + Core effective permissions.

---

## 5. Aliases legados

Aliases **não** são permissions canônicas do manifest novo. Servem para coexistência BFF:

- `dashboard-supplies.view` → `supplies.analytics.access`
- `purchase-requests.access` → `supplies.purchase-requests.access`
- `purchase-requests.view-all` → `supplies.purchase-requests.view-all`
- `purchase-requests.export` → `supplies.purchase-requests.export`
- `purchase-requests.admin` → `supplies.administration.manage`
- `purchase-requests.unit.filial-01/02` → `supplies.unit.filial-01/02`
- `estoque-seguranca.access` → `supplies.operations.access`
- `estoque-seguranca.view.filial-sc/es` → units

Aliases no BFF **não** fazem o Portal aparecer em `/me/apps`. Coexistência (E3.S5) **deve** provisionar as permissions canônicas nos papéis/grupos.

---

## 6. JSON mínimo alinhado ao schema 1.0.0

Documento de referência para E3 (não registrar agora):

```json
{
  "schemaVersion": "1.0.0",
  "id": "supplies",
  "name": "Portal Suprimentos",
  "description": "Hub operacional e analítico de Suprimentos.",
  "icon": "package-icon",
  "version": "0.1.0",
  "type": "microfrontend",
  "basePath": "/apps/supplies",
  "entry": "/apps/supplies/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "supplies.portal.access",
      "name": "Acessar Portal Suprimentos",
      "description": "Entrar no Portal, Home, Ajuda, busca e preferências próprias.",
      "module": "supplies"
    },
    {
      "code": "supplies.purchase-requests.access",
      "name": "Solicitações de Compras",
      "description": "Jornada SC no escopo autorizado.",
      "module": "supplies"
    },
    {
      "code": "supplies.operations.access",
      "name": "Operações de compras",
      "description": "Pedidos, entregas, fornecedores, produtos e estoques.",
      "module": "supplies"
    },
    {
      "code": "supplies.analytics.access",
      "name": "Analytics de Suprimentos",
      "description": "Overview, KPIs e análises.",
      "module": "supplies"
    },
    {
      "code": "supplies.administration.manage",
      "name": "Administrar Portal Suprimentos",
      "description": "Mappings, scopes e settings.",
      "module": "supplies"
    },
    {
      "code": "supplies.purchase-requests.view-all",
      "name": "Ver todas as SC da unidade",
      "description": "Bypass de CC dentro das units autorizadas.",
      "module": "supplies"
    },
    {
      "code": "supplies.purchase-requests.export",
      "name": "Exportar Solicitações de Compras",
      "description": "Exportação em massa com auditoria.",
      "module": "supplies"
    },
    {
      "code": "supplies.unit.filial-01",
      "name": "Suprimentos — Filial 01",
      "description": "Unidade SC (01).",
      "module": "supplies"
    },
    {
      "code": "supplies.unit.filial-02",
      "name": "Suprimentos — Filial 02",
      "description": "Unidade ES (02).",
      "module": "supplies"
    }
  ],
  "routes": [
    {
      "path": "/apps/supplies",
      "label": "Portal Suprimentos",
      "permission": "supplies.portal.access",
      "icon": "package-icon",
      "order": 30,
      "showInMenu": true
    }
  ],
  "backend": {
    "required": true,
    "serviceName": "supplies-api",
    "baseUrl": "/apps/supplies-api",
    "validateJwt": true
  },
  "ui": {
    "renderMode": "federated"
  }
}
```

Rotas internas adicionais entram no mesmo array na E3 conforme §4.

---

## 7. Backend/authz (comportamento, não só manifest)

- JWT = identidade;
- effective permissions = Core `/me`;
- unit scope = ADR-006;
- minimization = ADR-007;
- backend = barreira real; MFE só UX de capabilities;
- não copiar `flask_auth.py` nem fallback FastAPI (ADR-001).

---

## 8. Gate

`GATE-DOC-MANIFEST` passa quando:

- [x] schema runtime real verificado (`1.0.0`);
- [x] nenhuma permission CRUD no catálogo canônico;
- [x] rota launcher + permissions sem colisão;
- [x] `/me/apps` e `/me/routes` de coexistência planejados (E3.S5 + aliases §5);
- [x] aliases têm estratégia de remoção pós-cutover;

Registro live no Core = **E3.S4**, não E1.
