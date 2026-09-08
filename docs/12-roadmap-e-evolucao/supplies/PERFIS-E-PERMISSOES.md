# Perfis e permissões — Portal Suprimentos

> Papéis Minha DELPI **agrupam** permissions; o MFE não autoriza por nome de cargo.  
> **Unidades:** eixo próprio — [ADR-006](./adr/ADR-006-unit-permissions.md).  
> **Minimização:** não espelhar CRUD em permissions — [ADR-007](./adr/ADR-007-permission-minimization.md).

---

## 1. Princípio — capabilities mínimas + unidade + escopo de recurso

```text
usuário
  → permissions efetivas resolvidas pelo Core API
  → capability de negócio (o quê)
  → unidade (onde)
  → ownership / escopo do recurso
  → regra de negócio
  → ação autorizada
```

O JWT Keycloak identifica o usuário; **não é fonte canônica da lista completa de permissions**. O backend deve resolver as permissions efetivas pelo Core API e aplicar autorização server-side.

| Dimensão | Pergunta | Exemplo | Quando cresce |
|---|---|---|---|
| **A — capability** | Qual responsabilidade material o usuário possui? | `supplies.operations.access` | só quando nasce fronteira real de risco/segregação |
| **B — unidade** | Em quais unidades TOTVS pode operar/ver dados? | `supplies.unit.filial-01` | quando nasce uma unidade |
| **C — recurso** | Sobre quais registros pode agir? | próprio usuário, equipe, CC, fornecedor referenciado | por regra de negócio/dados, não por permission code |

```text
permitido = capability AND unit_scope AND resource_scope AND business_rule
```

**Regra central:** permission representa capacidade relevante de negócio, segurança ou governança — não botão, aba, endpoint ou verbo CRUD.

---

## 2. Eixo B — catálogo de unidades

Uma permission por unidade. Rótulo PT-BR só na UI.

| Código TOTVS | Permission | Label UI | Status |
|---|---|---|---|
| `01` | `supplies.unit.filial-01` | Santa Catarina (SC) | canônico |
| `02` | `supplies.unit.filial-02` | Espírito Santo (ES) | canônico |
| `XX` | `supplies.unit.filial-XX` | nome da unidade | quando a filial existir |

Nova unidade = 1 entrada no catálogo + 1 permission no manifest + atribuição aos papéis. Nenhuma capability funcional muda.

### Regras

| Situação | Comportamento |
|---|---|
| Capability sem nenhuma unit | Fail-closed para dado TOTVS; shell/Ajuda ainda podem abrir com `supplies.portal.access` |
| Uma unit | somente aquela filial |
| Várias units | união somente das unidades autorizadas |
| `branch` fora do conjunto | 403 no BFF |
| Administração | não concede unidade automaticamente |
| Superadmin | bypass somente conforme política canônica do Core e com auditoria |
| `purchase-requests.view-all` | bypass de centro de custo, nunca de unidade |

`allowedUnits` é derivado de **permissions efetivas do Core**, não de claims de permission no JWT.

---

## 3. Eixo A — catálogo mínimo de capabilities

Catálogo alvo P0/P1:

| Capability | Permission | Uso |
|---|---|---|
| Entrar no Portal / Home / Ajuda / busca / preferências próprias | `supplies.portal.access` | base do produto |
| Solicitações de Compras no escopo permitido | `supplies.purchase-requests.access` | lista, detalhe e jornada SC |
| Operação de compras | `supplies.operations.access` | pedidos, entregas, fornecedores, produtos, estoque, ESTSEG, follow-ups e notas operacionais |
| Análises e indicadores | `supplies.analytics.access` | Overview, KPIs, CPV, OTD gerencial, giro, savings |
| Administração | `supplies.administration.manage` | mappings, scopes, settings homologados |
| Ver todas as SC do CC dentro da unidade | `supplies.purchase-requests.view-all` | exceção de escopo já existente |
| Exportar SC | `supplies.purchase-requests.export` | saída em massa; manter separado enquanto houver risco/auditoria diferenciados |

### Capabilities que NÃO serão criadas por padrão

Não criar automaticamente:

```text
supplies.tasks.view
supplies.tasks.write
supplies.tasks.create
supplies.tasks.complete
supplies.suppliers.notes.write
supplies.inventory.view
supplies.products.view
supplies.suppliers.view
```

se a mesma segurança puder ser obtida com `operations.access` + unidade + ownership/escopo de recurso.

Uma nova permission só é criada se houver diferença comprovada de público, risco, segregação de função, administração, exportação sensível, operação em massa ou delegação independente.

---

## 4. Tasks e follow-ups

P0 não separa leitura/escrita de tasks por permission.

```text
supplies.portal.access
+ acesso à capability do recurso referenciado
+ unit permitida
+ ownership/regra de equipe
→ listar/criar/editar/concluir follow-up permitido
```

Exemplo: uma task ligada a PC da filial 02 não pode ser criada/concluída por usuário sem acesso à filial 02 ou sem acesso operacional ao PC, mesmo que a task esteja atribuída a ele.

Se no futuro existir necessidade real de usuário consultar tasks sem poder operá-las, reavaliar via ADR-007.

---

## 5. Notas de fornecedor

Na P0, nota interna faz parte da jornada operacional do fornecedor:

```text
supplies.operations.access
AND unidade autorizada
AND fornecedor no escopo
```

Não criar `supplies.suppliers.notes.write` apenas porque existe POST/PATCH.

Separar a permission somente se a homologação provar que o público que consulta fornecedor é materialmente maior que o público autorizado a registrar notas.

---

## 6. Administração e segregação de função

`supplies.administration.manage` permanece separada porque altera configuração/escopo e possui risco diferente do uso normal.

A futura jornada de alçadas só ganhará permission própria, por exemplo `supplies.approvals.manage`, se executar aprovação/rejeição ou outra ação de risco segregado. Apenas consultar informação de alçada não justifica novo code.

---

## 7. Matriz de decisão para permission nova

Antes de criar qualquer permission, preencher:

| Capability candidata | Operações | Mesmo público? | Mesmo risco? | Ownership resolve? | Unit scope resolve? | Permission nova? | Justificativa |
|---|---|---:|---:|---:|---:|---:|---|

Se uma capability existente + unidade + ownership preservar a segurança, a nova permission é redundante e não deve ser criada.

---

## 8. Papéis exemplificativos

| Papel | Capabilities | Eixo B |
|---|---|---|
| Comprador SC | portal + operations + purchase-requests + view-all | `filial-01` |
| Analista SC/ES | portal + analytics; operations somente se necessário | `filial-01` + `filial-02` |
| Solicitante ES | portal + purchase-requests, sem view-all | `filial-02` |
| Gestor multi | portal + analytics + operations | units atribuídas |
| Admin | portal + administration + capabilities necessárias | units administradas |

### E1.S2 — Evidência Core (2026-09-08)

| Fonte | Resultado |
|---|---|
| Core local `delpi-postgres-core` (após E3.S4/S5) | papéis `Portal Suprimentos - *` + app `supplies` registrado; `Portal Comercial - Full` **sem** codes `supplies.*` |
| Smokes `/me` / `/me/apps` | superadmin local vê Portal Suprimentos (14 rotas); persona negativa user-level **BLOQUEADO** sem user Keycloak não-superadmin — ver `evidence/e3-s5-rbac-smoke-local.json` |
| Manifests no monorepo | codes canônicos em `plugins/supplies/supplies.manifest.json`; legados de produto permanecem até cutover |

**P-02 Comprador ES:** `N/A_LOCAL` — sem usuário operacional ES. O modelo RBAC **não** exige capability nova para ES: só composição + `supplies.unit.filial-02`. Hipótese operacional permanece até smoke HML/prod.

### Matriz legado observado (código) → alvo ADR-007

| Papel alvo (UX) | Permissions legadas (manifest/código) | Units legadas | Capabilities canônicas | Units canônicas | Gap E3.S5 |
|---|---|---|---|---|---|
| Analista SC/ES | `dashboard-supplies.view` | — (app sem eixo unit no manifest) | `portal.access` + `analytics.access` | `filial-01` e/ou `filial-02` conforme papel | **ATENDIDO** — papel `Portal Suprimentos - Analista` |
| Comprador SC | `estoque-seguranca.access` + `view.filial-sc`; BIs PO ainda sem id Core | `filial-sc` → 01 | `portal` + `operations` (+ analytics se usar OTD gerencial) | `filial-01` | **ATENDIDO** no papel canônico; BIs só após dump prod |
| Comprador ES | **não observado** no Core local nem evidência PO | — | mesmas capabilities do SC se o papel existir | `filial-02` | **N/A_LOCAL** |
| Solicitante CC | `purchase-requests.access` + unit 01/02 | `unit.filial-01/02` | `portal` + `purchase-requests.access` | mesma unit | **ATENDIDO** — `Portal Suprimentos - Solicitante SC` |
| Comprador visão ampla SC | `purchase-requests.access` + `view-all` + unit | unit | + `view-all` | unit | alias + grant pontual `view-all` |
| Admin compras | `purchase-requests.admin` | não implica todas units | `administration.manage` + units administradas | units explícitas | **ATENDIDO** — `Portal Suprimentos - Admin` |
| Exportador SC | `purchase-requests.export` | — | `export` | herda units do access | manter segregação |
| Usuário sem supplies | (nenhuma) | — | nenhuma `supplies.*` | — | sibling: Comercial Full sem `supplies.*`; user negativo pendente HML |

Comprador ES no Core continua **HIPOTESE_A_VALIDAR** operacionalmente; para o catálogo de permissions, P-02 está **fechado como não bloqueante do desenho** (sem code novo).

Script: `plugins/supplies/scripts/provision-rbac-coexistence.sh`.

---

## 9. Aliases de coexistência

Aliases preservam compatibilidade no BFF, mas **não substituem provisionamento do novo app no Core**. Para o Portal aparecer em `/me/apps` (com `routes[]` filtradas), os papéis precisam receber as permissions canônicas do `supplies` durante a coexistência. O Core vigente **não** expõe `GET /me/routes`.

| Legado | Compatibilidade alvo |
|---|---|
| `dashboard-supplies.view` | `supplies.analytics.access` |
| `purchase-requests.access` | `supplies.purchase-requests.access` |
| `purchase-requests.view-all` | `supplies.purchase-requests.view-all` |
| `purchase-requests.export` | `supplies.purchase-requests.export` |
| `purchase-requests.admin` | `supplies.administration.manage` |
| `purchase-requests.unit.filial-01` | `supplies.unit.filial-01` |
| `purchase-requests.unit.filial-02` | `supplies.unit.filial-02` |
| `estoque-seguranca.access` | `supplies.operations.access` |
| `estoque-seguranca.view.filial-sc` | `supplies.unit.filial-01` |
| `estoque-seguranca.view.filial-es` | `supplies.unit.filial-02` |
| `idd-suprimentos.access` | `supplies.analytics.access` somente após confirmação no Core |

Os códigos evidenciados pelo Product Owner (`importados.access`, `onde-e-usado.access`, `matriz_atraso-fornecedores.access`, `alcada-compras.access`, `controle-estoque-sc.access`, `idd-suprimentos.access`) permanecem **CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER** até dump do Core.

---

## 10. Proibido

- espelhar CRUD em permission codes;
- criar permission por botão, modal, aba ou endpoint;
- `supplies.{feature}.{action}.filial-*` novo;
- recriar `filial-sc` / `filial-es` como canônico;
- `if role == comprador` ou `if unidade == SC` no MFE;
- tratar administração como acesso automático a todas as unidades;
- confiar em permissions/is_superadmin do JWT como autorização final;
- usar alias no BFF como substituto de provisionamento RBAC no Core.
