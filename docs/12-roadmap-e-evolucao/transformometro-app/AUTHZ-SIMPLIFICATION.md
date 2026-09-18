# Portal Transforma+ — simplificação de AuthZ multiunidade

> Inventário histórico do modelo de 21 códigos. A fatia 1 adicionou `access` e `manage` e tirou filial da autorização. Os 21 continuam. Matriz vigente em [AUTHZ-FINAL-DESIGN.md](./AUTHZ-FINAL-DESIGN.md).
> Base do inventário: `769b2a0a161af54c36eb58bd31a0d7033de412ab`.
> Hardening: ver §10.

Keycloak continua identidade. A Core API é a autoridade de permissão (`PermissionResolver` + `/me`). O Transformômetro não concede permissão. Aplica só invariantes de domínio e pode negar o que o Core autorizou. Frontend não autoriza.

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
| `transformometro.dashboard.recalculate` | SPECIAL_CAPABILITY | HTTP, MCP e GPT Actions chamam `TransformometroAuthorizationPolicy.require_dashboard_recalculate`. O recálculo interno depois de escrita ou importação não usa esse gate. |
| `transformometro.view.consolidated` | ORGANIZATIONAL_SCOPE | Abre a visão consolidada quando o usuário está em modo `scoped`. Sem código de filial, não abre as unidades. |
| `transformometro.branch.filial-01` | ORGANIZATIONAL_SCOPE | Fonte canônica atual do escopo da unidade 01. |
| `transformometro.branch.filial-02` | ORGANIZATIONAL_SCOPE | Fonte canônica atual do escopo da unidade 02. |
| `transformometro.view.filial-01` | LEGACY_ALIAS | Soma a unidade 01 em `FilialAccessScopeService`. |
| `transformometro.view.filial-02` | LEGACY_ALIAS | Soma a unidade 02. |
| `transformometro.manage.filial-01` | LEGACY_ALIAS | Escopo 01 **e** escrita naquela unidade, sem manage global. |
| `transformometro.manage.filial-02` | LEGACY_ALIAS | Igual para 02. |
| `transformometro.data.transfer` | SPECIAL_CAPABILITY | Export, preview e import na API exigem este código. O colapso para `manage` continua decisão de negócio. CLI de operador não passa por este gate. |
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
| ASSIGNMENT AUTHORITY | Core: `role_permissions`, `user_roles`, `group_roles`, `user_permissions`. Sem tabela de membership ou unit scope. |
| SOURCE | Códigos em `user.permissions` do Core `GET /me` |
| DOMAIN INTERPRETER | Transformômetro, `FilialAccessScopeService` |
| ENFORCEMENT | `check_*_access`, `filter_rows_for_access`, atas, policy de backup e recálculo |
| Contrato alvo `authorized_units` sem permission | **TO_INVENTORY**. Core público não tem tabela de scope, membership, filial ou unit. |

Regra vigente depois do hardening:

- superadmin → `unrestricted`;
- `user is None` → `denied`;
- sem código de filial, usuário autenticado → `scoped` vazio (não vê unidade);
- com `branch`/`view.filial`/`manage.filial` → `scoped` em `01` e/ou `02`;
- `view.consolidated` abre só o consolidado nesse modo;
- escrita na filial visível: `manage.filial-*` ou qualquer `GLOBAL_MANAGE_PERMISSIONS`.

Opções de alvo ainda não implementadas: membership de app com unidades, assignment de permission já escopado, IDs de unidade no `/me`, escopo organizacional transversal. Nenhuma está no schema do Core. Não criar claim JWT, tabela local nem convenção de grupo Keycloak.

Produção inventariada sem nomes de pessoas: um papel, `Transforma Mais`, com os 21 códigos, 4 usuários no papel, 1 grupo (`Supervisor Engenharia`), zero grant direto. Não há persona só de acesso, só de uma unidade, só de assinatura ou só de transferência. Remover alias ainda exige migrar esse papel. Os códigos de filial permanecem.

## 3. Onde cada camada decide

Core: `RegisterPluginUseCase` sincroniza `permissions[]` e `routes[]` por `code`. O UUID da permission permanece se o code permanecer (`PluginPermissionSyncService`). `PermissionResolver` junta papéis diretos e de grupo. Keycloak não guarda estes códigos. Se o Core cai, o middleware zera `permissions` (`_rbac_from_claims`) — fail-closed para RBAC, não fail-open.

Portal: `ProtectedRoute` exige `route.permission`. O MFE **não** chama `hasPermission`. A navegação interna não repete o gate do manifesto. `showInMenu: false` em todas as rotas atuais; o launcher abre `basePath` `/apps/transformometro`, que **não** está em `routes[]`.

MCP e GPT Actions passam pelo mesmo `dispatch_service` / serviços de domínio. Não há permission exclusiva de tool. Actions continuam `LEGACY_TRANSITIONAL_BRIDGE`.

Atribuições de produção: um papel com os 21 códigos. Ver §2. Isso não autoriza apagar código.

## 4. Rotas do manifesto

| PATH | Permissão atual | Backend | Alvo proposto (não aplicado) |
|---|---|---|---|
| `/apps/transformometro` | ausente | JWT + escopo nas APIs | `transformometro.access`, `showInMenu: true` |
| `/dashboard` | `view` | escopo de dashboard | `access` |
| `/processes` | `processes.manage` | filtro de escopo; manage só na escrita | `access` para abrir; escrita continua no domínio |
| `/meeting-minutes` | `meeting-minutes.view` | view/manage/sign + escopo | `access` |
| `/my-signature` | `meeting-minutes.view` | perfil de ata | `access` |
| `/settings/units` | `processes.manage` | catálogo: `require_unrestricted_catalog_admin` em parte das escritas | `manage` |
| `/data` | `data.transfer` | `TransformometroAuthorizationPolicy.require_data_transfer` | `manage` só se o negócio confirmar |
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
| FAIL-OPEN `user is None` | CLOSED |
| DATA TRANSFER enforcement | CLOSED no código atual |
| DASHBOARD RECALC parity HTTP/MCP/GPT | CLOSED |
| TARGET CODES | DECIDED_FOR_REVIEW, não contrato |
| UNIT SCOPE assignment authority | PROVEN (Core RBAC) |
| UNIT SCOPE interpreter | PROVEN (`FilialAccessScopeService`) |
| UNIT SCOPE TARGET sem permission | TO_INVENTORY |
| OLD→NEW | completo |
| Assignments de produção | inventariados, um papel com os 21 códigos |
| Sign / data.transfer / meeting-minutes.manage | decisão de negócio aberta |
| NEGATIVE TESTS do hardening | implementados |
| ROLLBACK | reverter o commit de hardening; papéis não foram alterados |
| Manifest migration | NOT AUTHORIZED |

**AUTHZ_MIGRATION = NOT_READY.**

## 10. Hardening

`TransformometroAuthorizationPolicy` é a policy user-facing de backup e recálculo. HTTP, MCP e GPT Actions chamam o mesmo método. O serviço `DashboardRecalcService` continua sem permission, porque importação e hooks de escrita disparam recálculo interno.

Assinatura de ata continua com permission `meeting-minutes.sign` mais signatário, unidade e estado assinável. Recomendação técnica: a regra material é a do recurso. O código global só impede tentar assinar quem não tem a capability, mesmo sendo signatário. Não remover até decisão explícita.

Raiz `/apps/transformometro` com `access` e `showInMenu: true` permanece alvo, não aplicada.

CLI `cadastro_json_cli` é contexto de operador, fora da policy HTTP. Não é fallback de `user is None`.
