# Portal Transforma+ — simplificação de AuthZ multiunidade

> **Status:** inventário e alvo para revisão. **IMPLEMENTATION = NOT AUTHORIZED.**  
> **AUTHZ_MIGRATION = NOT_READY.**  
> Base: `769b2a0a161af54c36eb58bd31a0d7033de412ab`.  
> Manifesto lido: `plugins/transformometro/transformometro.manifest.json`.  
> Enforcement lido: `transformometro_permissions.py`, `branch_access_scope_service.py`, `branch_access_http.py`, `meeting_minutes_service.py`, `dispatch_service.py`.

Keycloak continua identidade. Core continua dono do RBAC transversal (`PermissionResolver` + `/me`). Transformômetro aplica a regra final de domínio. Frontend não autoriza. TÉO consome o mesmo usuário.

## 1. Modelo atual

O manifesto declara **21** códigos. Sete são alias legado explícito no próprio manifesto e em `transformometro_permissions.py`.

| CODE | Classe | O que o código faz hoje |
|---|---|---|
| `transformometro.view` | PRODUCT_ACCESS | Abre o produto no portal (`/dashboard`, `/administration`). No backend, `require_transformometro_view_access` aceita também branch, consolidado ou qualquer `GLOBAL_MANAGE`. |
| `transformometro.processes.manage` | REDUNDANT como RBAC fino | Porta do portal para `/processes` e `/settings/units`. No backend entra em `GLOBAL_MANAGE_PERMISSIONS`: qualquer um desses códigos libera escrita na filial visível. Não há gate HTTP separado “só processos”. |
| `transformometro.revisions.manage` | REDUNDANT como RBAC fino | Mesmo conjunto global. GPT/MCP ainda cita o código no recálculo e no fallback de revisão sem instância. |
| `transformometro.measurements.manage` | REDUNDANT como RBAC fino | Só aparece como membro de `GLOBAL_MANAGE_PERMISSIONS`. Sem consumidor HTTP próprio. |
| `transformometro.investments.manage` | REDUNDANT como RBAC fino | Igual medições. |
| `transformometro.shared-resources.manage` | SPECIAL_CAPABILITY hoje | Além do conjunto global, `require_shared_resources_manage` barra o catálogo de recursos. |
| `transformometro.dashboard.recalculate` | SPECIAL_CAPABILITY parcial | GPT/MCP exigem este código **ou** qualquer manage global. `POST /dashboard/recalcular` **não** chama esse gate. |
| `transformometro.view.consolidated` | ORGANIZATIONAL_SCOPE | Só importa quando o usuário já está em modo `scoped`. Sem código de filial, a visão já é irrestrita. |
| `transformometro.branch.filial-01` | ORGANIZATIONAL_SCOPE | Fonte canônica atual do escopo da unidade 01. |
| `transformometro.branch.filial-02` | ORGANIZATIONAL_SCOPE | Fonte canônica atual do escopo da unidade 02. |
| `transformometro.view.filial-01` | LEGACY_ALIAS | Soma a unidade 01 em `FilialAccessScopeService`. |
| `transformometro.view.filial-02` | LEGACY_ALIAS | Soma a unidade 02. |
| `transformometro.manage.filial-01` | LEGACY_ALIAS | Escopo 01 **e** escrita naquela unidade, sem manage global. |
| `transformometro.manage.filial-02` | LEGACY_ALIAS | Igual para 02. |
| `transformometro.data.transfer` | SPECIAL_CAPABILITY só no portal | Porta `/data` no manifesto. Nenhuma checagem no `json_backup_routes.py`. |
| `transformometro.meeting-minutes.view` | PRODUCT_ACCESS de ata | Lista e leitura, com alias `atas.view`. |
| `transformometro.meeting-minutes.manage` | DOMAIN + escopo | Cria/edita/envia/finaliza. Também entra em `GLOBAL_MANAGE`. |
| `transformometro.meeting-minutes.sign` | DOMAIN_RESOURCE_AUTHZ + permissão | Exigida em `_assert(..., "sign")`. Além disso o serviço exige ser signatário e estado assinável. |
| `transformometro.atas.view` | LEGACY_ALIAS | Aceito em `MEETING_MINUTES_VIEW_PERMISSIONS`. |
| `transformometro.atas.manage` | LEGACY_ALIAS | Aceito em manage e em `GLOBAL_MANAGE`. |
| `transformometro.atas.sign` | LEGACY_ALIAS | Aceito em sign. |

Não existem outros códigos `transformometro.*` no manifesto além destes 21.

## 2. Escopo de unidade

| Campo | Valor |
|---|---|
| UNIT_SCOPE_OWNER | Transformômetro, `FilialAccessScopeService` |
| UNIT_SCOPE_SOURCE | Códigos no `user.permissions` devolvido pelo Core `GET /me` |
| UNIT_SCOPE_CONTRACT | PROVEN para o modelo atual: `branch.filial-*`, com alias `view.filial-*` e `manage.filial-*` |
| UNIT_SCOPE_BACKEND_ENFORCEMENT | PROVEN em `check_*_access`, `filter_rows_for_access` e atas |
| Contrato alvo `authorized_units` sem permission | **TO_INVENTORY** |

Regra provada:

- superadmin → `unrestricted`;
- sem nenhum código de filial → `unrestricted` (vê todas as unidades);
- com `branch`/`view.filial`/`manage.filial` → `scoped` às unidades `01` e/ou `02`;
- `view.consolidated` só abre o consolidado **dentro** do modo scoped;
- escrita na filial: `manage.filial-*` **ou** qualquer código de `GLOBAL_MANAGE_PERMISSIONS`, e a filial precisa ser visível;
- `user is None` em `resolve()` também cai em `unrestricted`. Isso é fail-open se o request chegar sem usuário. Não corrigir neste passe.

Não há claim JWT, grupo Keycloak nem tabela local de unidades autorizadas. Cargo não entra.

Por isso `branch.filial-03` não é a direção futura: cada unidade nova vira código, papel, teste e alias. Mas **não dá para apagar** `branch.filial-01/02` enquanto não existir outra fonte de escopo. Remover agora abriria todas as unidades para quem só tinha uma.

## 3. Onde cada camada decide

Core: `RegisterPluginUseCase` sincroniza `permissions[]` e `routes[]` por `code`. O UUID da permission permanece se o code permanecer (`PluginPermissionSyncService`). `PermissionResolver` junta papéis diretos e de grupo. Keycloak não guarda estes códigos. Se o Core cai, o middleware zera `permissions` (`_rbac_from_claims`) — fail-closed para RBAC, não fail-open.

Portal: `ProtectedRoute` exige `route.permission`. O MFE **não** chama `hasPermission`. A navegação interna não repete o gate do manifesto. `showInMenu: false` em todas as rotas atuais; o launcher abre `basePath` `/apps/transformometro`, que **não** está em `routes[]`.

MCP e GPT Actions passam pelo mesmo `dispatch_service` / serviços de domínio. Não há permission exclusiva de tool. Actions continuam `LEGACY_TRANSITIONAL_BRIDGE`.

Atribuições reais de papéis/usuários em produção: **não provadas neste repositório**. Isso bloqueia remoção.

## 4. Rotas do manifesto

| PATH | Permissão atual | Backend | Alvo proposto (não aplicado) |
|---|---|---|---|
| `/apps/transformometro` | ausente | JWT + escopo nas APIs | `transformometro.access`, `showInMenu: true` |
| `/dashboard` | `view` | escopo de dashboard | `access` |
| `/processes` | `processes.manage` | filtro de escopo; manage só na escrita | `access` para abrir; escrita continua no domínio |
| `/meeting-minutes` | `meeting-minutes.view` | view/manage/sign + escopo | `access` |
| `/my-signature` | `meeting-minutes.view` | perfil de ata | `access` |
| `/settings/units` | `processes.manage` | catálogo: `require_unrestricted_catalog_admin` em parte das escritas | `manage` |
| `/data` | `data.transfer` | **não checado na API** | `manage`, e a API precisa passar a checar |
| `/administration` | `view` | página só de links | `manage` |

## 5. Alvo para revisão

Códigos candidatos, ainda não contrato:

- `transformometro.access` — uso normal dentro do escopo: Início, Visão geral, Meus processos, workspace, atas, assinatura **se** a regra de signatário passar.
- `transformometro.manage` — Administração, configurações, exportar/importar, recálculo administrativo. Não significa, por si, editar processo de qualquer unidade.

Manter até existir contrato de escopo que não seja permission:

- `transformometro.branch.filial-01`
- `transformometro.branch.filial-02`
- `transformometro.view.consolidated`

`meeting-minutes.sign` não colapsa neste desenho. A regra material já é “é signatário + ata assinável + ainda não assinou”, mas o código também exige a permission. Tirar a permission muda quem pode tentar assinar. Isso é decisão de negócio.

`data.transfer` pode ir para `manage` se não houver pessoa que exporta e não administra. O repositório não prova esse persona. A API hoje não aplica o código.

`shared-resources.manage` e `dashboard.recalculate` são os únicos gates nomeados além do conjunto global. O alvo os absorve em `manage`, desde que o HTTP de recálculo e o backup passem a usar o mesmo gate. Hoje o HTTP de recálculo não usa.

Referência Comercial: `commercial.access`, `commercial.manage` e uma capability excepcional (`commercial.billing.notify`). Não é fonte de regra do Transformômetro.

Contagem alvo mínima, se sign e data forem absorvidos e o escopo continuar em permission: **5** (`access`, `manage`, dois `branch`, `consolidated`). Não é 2.

## 6. OLD → NEW

| OLD | Legado? | Alvo | Remover já? | Bloqueio |
|---|---|---|---|---|
| `view` | não | `access` | não | papéis no Core não inventariados |
| `processes.manage` | não | `access` para abrir; escrita = escopo + domínio | não | portal usa o código como porta de processos e configurações |
| `revisions.manage` | não | colapsar no conjunto de escrita / `manage` no recálculo | não | fallback GPT de revisão |
| `measurements.manage` | não | colapsar | não | mesmo conjunto global |
| `investments.manage` | não | colapsar | não | mesmo conjunto global |
| `shared-resources.manage` | não | `manage` | não | gate próprio do catálogo |
| `dashboard.recalculate` | não | `manage` | não | HTTP `/recalcular` sem gate |
| `view.consolidated` | não | permanecer como escopo | não | não há outro contrato |
| `branch.filial-01/02` | não | permanecer | não | é a fonte de escopo |
| `view.filial-*` | sim | alias de `branch` | não | ainda entra no resolver |
| `manage.filial-*` | sim | alias de escopo + escrita local | não | ainda entra no resolver |
| `data.transfer` | não | `manage` se o negócio confirmar | não | API não enforce |
| `meeting-minutes.view` | não | `access` | não | decisão junto com sign |
| `meeting-minutes.manage` | não | `access` + regra de domínio, ou `manage` se for só admin de ata | não | também é manage global |
| `meeting-minutes.sign` | não | KEEP até decisão | não | permission + signatário |
| `atas.*` | sim | alias dos três acima | não | tuplas ainda aceitam |

Nenhum código é SAFE TO REMOVE neste passe.

## 7. Migração futura

Ordem: decidir sign e data transfer; inventariar papéis no Core sem apagar; introduzir `access` e `manage` como aliases de leitura dos códigos atuais; backend passa a entender os novos códigos **sem** deixar ausência virar allow; portal e manifesto de rotas; MCP/Actions no mesmo serviço; migrar assignments; aceitar runtime; só então retirar alias. Sync do manifesto que apaga `code` derruba a permission e pode quebrar `role_permissions`. Primeiro migrar assignments, depois retirar o code.

Rollback: manter os códigos antigos até o fim da janela. Não resetar Keycloak. Não apagar papéis. Reverter o manifesto para os 21 códigos restaura o catálogo se os UUIDs ainda existirem; por isso a janela é curta e explícita, não um OR eterno.

Fail-closed: usuário sem `access` e sem código legado equivalente → 403. Compatibilidade é “código novo **ou** código antigo mapeado”, nunca “sem código → liberado”.

## 8. Testes futuros

- sem access → 403;
- access abre portal e lista do próprio escopo, administração 403;
- manage abre administração e backup;
- filial A não lê filial B;
- signatário que não está na ata → 403 mesmo com permission de sign;
- menu oculto no MFE não substitui o backend;
- cargo/JWT sem permission de filial não abre unidade.

## 9. Definition of Ready

| Gate | Estado |
|---|---|
| TARGET CODES | DECIDED_FOR_REVIEW, não contrato |
| UNIT SCOPE OWNER | PROVEN (`FilialAccessScopeService`) |
| UNIT SCOPE CONTRACT alvo sem permission | TO_INVENTORY |
| OLD→NEW | completo acima |
| Assignments Core | não provado |
| API backup e HTTP recalcular | gap |
| Sign | decisão de negócio aberta |
| NEGATIVE TEST PLAN | escrito, não implementado |
| ROLLBACK | escrito |

**AUTHZ_MIGRATION = NOT_READY. IMPLEMENTATION = NOT AUTHORIZED.**
