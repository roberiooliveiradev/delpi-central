# Documento 115 — DRE-ACCESS-019 · Acesso externo DRE ao Fechamento Mensal (execução do gate 91)

**Data:** 2026-10-27
**Execução:** `CF-PROC0072-DRE-ACCESS-019` (continuação do inventário `CF-PROC0072-DRE-ACCESS-018`)
**Produto:** Portal Controladoria & Finanças — Central de Fechamento — PROC-0072
**Autoridade de origem:** [doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) (Opção B aprovada pelo PO), [doc 113](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md) §2 itens 7–8, checkpoint 6
**Estado:** IMPLEMENTED — gate transversal resolvido pela execução governada autorizada (DOCUMENTAÇÃO → CORE/RBAC → CONTRATOS → BFF → FRONTEND → TESTES → DEPLOY GOVERNADO).

## 1. Decisões materiais resolvidas

1. **Terceira permission autorizada:** `controllership-finance.closing-documents.read`. O freeze de duas permissions (doc 91 §2) foi superado por decisão expressa do PO + gate transversal: o invariant do manifesto passa a ser **exatamente três permissions** (`access`, `manage`, `closing-documents.read`). Permanece proibida permission por página/documento/competência/filial/botão.
2. **Capability ≠ audience:** a permission é *capability*, não nome de grupo. `closing-documents.read` **não implica** `access` nem `manage`; quem tem `access` **não** recebe automaticamente a visão de destinatário. Core continua autoridade exclusiva de grants/effective permissions.
3. **Modelo de liberação documental (CP4):** a entrega é representada por **assignment `RECIPIENT` ativo** vinculado ao pacote da competência + **versão `SUBMITTED`** do pacote. A composição submetida (`closing_package_version.content.items[].document_version_id`) é o conjunto efetivamente liberado — snapshot imutável, sem etapa burocrática adicional (decisão do PO no doc 91). Um destinatário vinculado a múltiplos pacotes (ex.: `CONTABIL` + `FISCAL`) recebe a **união** dos documentos liberados.
4. **Versão corrente vs histórica:** a entrega corrente usa a versão `SUBMITTED` vigente; versões pinadas em releases anteriores permanecem visíveis ao destinatário (versões liberadas), e versões criadas **após** o `SUBMITTED` não entram na entrega nem são baixáveis até nova submissão (`create_complement` → `submit`).
5. **Rota dedicada:** `/apps/controllership-finance/closing/documents` exige `closing-documents.read` **ou** `access` no guard do Portal (resolução por prefixo mais específico). Desvio documentado do candidato `closing/accounting-documents` do doc 91: adotado `closing/documents` por alinhamento ao nome da área existente «Documentos e interações».
6. **Audiência de mensagens (CP8):** `document_message.audience` ganha `SHARED` além de `INTERNAL` (V018, aditiva). Mensagens `INTERNAL` nunca aparecem na projeção DRE; `SHARED` é o canal bidirecional.
7. **Solicitações de ajuste:** nova entidade `document_adjustment_request` (V018) com ciclo `OPEN → ANSWERED → CONFIRMED`, separada de mensagem: **responder não encerra**; somente o requerente confirma (doc 113 §2 item 8).

## 2. Contrato BFF implementado (projeção DRE)

Router `/closing/received-documents` em `received_documents_routes.py` — todo endpoint exige `closing-documents.read` efetiva + vínculo:

| Método/rota | Contrato |
|---|---|
| `GET /closing/received-documents` | Lista competências com entrega ativa ao ator |
| `GET /closing/received-documents/{period}` | Entrega da competência (documentos liberados, union multi-pacote) |
| `GET …/{period}/documents/{document_id}` | Detalhe + versões liberadas (sem `storage_key`, sem metadados internos) |
| `GET …/{period}/documents/{document_id}/download` | Download auditado (`DOCUMENT_DOWNLOADED` com `result`) |
| `GET …/{period}/documents/{document_id}/messages` | Mensagens `SHARED` somente |
| `POST …/{period}/documents/{document_id}/messages` | Mensagem do destinatário (`audience=SHARED`, idempotente) |
| `GET/POST …/adjustment-requests` | Listar próprias solicitações / criar (idempotente) |
| `POST …/adjustment-requests/{request_id}/confirm` | Confirmação pelo requerente (`ANSWERED → CONFIRMED`) |

Resposta interna a solicitações: `POST /closing/{period}/documents/{document_id}/adjustment-requests/{request_id}/answer` nas rotas internas (`access`+escopo).

**Fail-closed em camadas:** capability → assignment `RECIPIENT` ativo → pacote `SUBMITTED` → pertencimento do documento/versão ao snapshot liberado. Recursos fora do conjunto liberado retornam **404** — existência de pacote, documento, competência ou versão alheia nunca vaza.

**Projeção pública:** `document_id`, `item_key`, `item_name`, `recipient_area`, `title`, `link_kind`, `original_name`, `mime_type`, `size_bytes`, `version_no`, `released_at`. Nunca `storage_key`, `document_version_id`, `package_id`, P3/P4, decisões, required areas, `uploaded_by` ou conteúdo bruto do snapshot.

## 3. Implementação

**Backend (`controllership-finance-api`):**
- `migrations/V018__recipient_document_delivery.sql` — audiência `SHARED` em `document_message` + tabela `document_adjustment_request` (aditiva).
- `infrastructure/persistence/closing_recipient_repository.py` — read-model do destinatário (deliveries, union multi-pacote, released documents/versions, download autorizado via join `document_file`).
- `application/services/received_documents_service.py` — cadeia de autorização fail-closed, projeção, download auditado, mensagens `SHARED`, ciclo de solicitações.
- `interface/http/routes/received_documents_routes.py` — contrato HTTP acima; guard `closing-documents.read` em `authz.py`.
- `closing_document_repository.py` — filtro `audience`, CRUD de solicitações (create/answer/confirm com UPDATE condicional e auditoria).
- `closing_package_repository.py` — `RECIPIENT` exige `recipient_area` (deriva `area`), visibilidade de pacotes para destinatário.
- `viewer_context_routes.py` + `authz.py` — viewer-context admite `access` **ou** `closing-documents.read`; capabilities `{access, manage, closingDocumentsRead}`.

**MFE (`plugins/controllership-finance`):**
- `controllership-finance.manifest.json` — 3 permissions; rota `closing/documents`.
- `src/api/receivedDocumentsApi.ts` — cliente da projeção (somente BFF).
- `src/features/closing/ReceivedDocumentsPage.tsx` — N1 entregas → N2 documentos da entrega → N3 detalhe (mesmos primitivos `plugin-ui`/hero do Portal).
- `src/features/closing/ReceivedDocumentDetailPanel.tsx` + `ReceivedConversationPanel.tsx` — prévia/download, versões liberadas, conversa `SHARED`, solicitação de revisão com confirmação.
- `App.tsx`, `PluginShell.tsx`, `pluginRoutes.ts`, `ViewerContext.tsx` — modo destinatário: esconde nav interna/paleta, redirect de segurança para `closing/documents` em rota interna, sem duplicar autorização.
- `content/helpTooltips.ts` — grupo `receivedDocuments` (page, documents, requestsSummary, deliveries, detailFile, requests, detailConversation).

## 4. Evidência de testes

| Suíte | Resultado |
|---|---|
| Backend unit + PG real (`tests/`, Postgres efêmero, migrations V001–V018) | **713 passed** |
| `tests/test_pg_received_documents.py` (novo, PG) | 8 passed — union multi-pacote, isolamento sibling, detalhe/versões, download+auditoria (AUTHORIZED/DENIED), mensagens SHARED, ciclo+idempotência de solicitações, versão pós-SUBMITTED não liberada |
| `tests/test_viewer_context.py` | 20 passed — shape com `closingDocumentsRead`, cenário destinatário |
| Frontend `npm test` | **376 passed** (suíte) + **35 passed** (estruturais `.mjs`, manifesto congelado atualizado p/ 3 permissions/11 rotas) |
| Typecheck (plugin + `plugin-ui`) | limpo |

Bugs reais encontrados e corrigidos pela cobertura PG: join obrigatório em `document_file` (campos de arquivo fora de `document_version`), `state` de versão derivado de `current_version_no` (V004), parâmetro ausente em `confirm_adjustment_request`.

## 5. RQ/AC DRE-01…20 — classificação

- **PROVEN:** DRE-01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 13, 14, 15, 16, 17, 19 (evidência em §3–4).
- **PASS pendente de smoke autenticado:** DRE-04 (admin inacessível — coberto por teste de guard + unitário; smoke com identidade DRE real pendente), DRE-12 (regressão interna — suítes verdes), DRE-18 (responsivo/temas — herda primitivos; validação visual pendente).
- **TEST_NOT_RUN:** DRE-20 deploy produtivo — aguarda gate de homologação; smoke autenticado interno+DRE requer identidade provisionada no Core (grant `closing-documents.read`), não improvisada.

## 6. Provisionamento e rollback

- **Grant:** permission `closing-documents.read` provisionada pelo fluxo canônico do Core (registro do manifesto sincroniza permissions/rotas — `RegisterPluginUseCase`); grant a usuários DRE via administração Core, nunca pela BFF.
- **Vínculo:** assignment `RECIPIENT` por competência/área via rotas internas de pacote (`manage`), com `recipient_area` obrigatório.
- **Rollback:** MFE/build anteriores removem a rota; a permission pode ser revogada no Core sem migration down; V018 é aditiva e não precisa ser revertida para desligar a experiência.

## 7. Classificação final

`EXECUTION` = **PASS** nas fases implementação/testes; `DEPLOY_PROD` = **PENDING** (governado).
Revisão arquitetural externa: não autodeclarada — aguarda GATE.

## 8. Evidência de deploy — 2026-10-27

- `PROD_SHA`: `0695a1e68c` em `origin/main` (push fast-forward).
- Deploy canônico `srv-api`: `git pull --ff-only` + `up-prod-sequential.sh --build controllership-finance-api controllership-finance`.
- Migration `V018__recipient_document_delivery.sql` aplicada no startup (`migrations_startup_applied count=1`); API `healthy`.
- Bundle MFE: `remoteEntry.js` HTTP 200.
- Smoke de superfície não autenticado: `GET /closing/received-documents` → **401** (fail-closed).
- Smoke autenticado interno + DRE: **TEST_NOT_RUN** — requer grant Core `closing-documents.read` e identidade de teste autorizada (provisionamento é responsabilidade do Core/administração; não improvisado em produção).

## 9. RW01 — correção da entrada multi-público (2026-10-28)

**Sintoma (evidência PO/produção):** usuário com apenas `closing-documents.read` recebia `/unauthorized` ao abrir `/apps/controllership-finance`.

**Causa raiz:** a rota raiz do manifesto exige `controllership-finance.access`. O guard do Portal (`FederatedAppRouteGuard` → `resolveManifestRoutePermission` → `ProtectedRoute`) resolve uma única permission por rota — o catálogo `authorizationRoutes` não tem semântica OR. A BFF `/viewer-context` já aceitava a capability documental, mas o usuário era bloqueado **antes** de o MFE montar. O contrato de rotas do Core (`RouteDTO.permission_code: str | None`) não suporta permissões alternativas — evolução material não necessária.

**Solução implementada (Portal somente — `ccc8f3a235`):** convenção de entrada já estabelecida na plataforma (launcher: `visibleRoutes[0] ?? routes[0]`; `federatedAppHosts.mainRoute`) aplicada no guard: no **basePath exato**, se a permission resolvida é ausente mas o usuário possui rotas autorizadas (`app.routes` do `/me/apps`), redireciona à entrada autorizada. Rotas internas negadas continuam `/unauthorized` — a negação permanece evidência; sem rotas autorizadas o app nem aparece no catálogo. `resolveAuthorizedEntryPath` (puro) + testes `node:test` (9 casos: DRE, visibilidade, loop, negação interna, prefixos).

**Sem mudança:** Core, manifesto, BFF, MFE — contratos intactos; a proteção documental (capability → RECIPIENT → SUBMITTED → snapshot) é inalterada. Beneficia todos os apps multi-audiência (precedente latente idêntico em `production-pulse.operator`, `helpdesk.console`).

**Deploy:** `srv-api` `pull --ff-only` + `up-prod-sequential.sh --build portal`; `delpi-portal` saudável em `ccc8f3a235`.

**Pendente:** smoke autenticado end-to-end com identidade DRE provisionada (grant `closing-documents.read` no Core) — **TEST_NOT_RUN** até o grant existir; validar: entrada sem `/unauthorized`, `closing/documents` renderizado, rotas internas bloqueadas.

## 10. RW02 — `access.dre`, Home DRE e migração governada da capability (2026-10-28)

**Decisão do PO:** a entrada documental `closing-documents.read` é substituída por uma permission de acesso ao Portal específica da DRE — `controllership-finance.access.dre` — separando acesso interno DELPI, gestão e acesso externo DRE. O usuário DRE passa a entrar pela raiz do Portal, ver uma **Home DRE** restrita, abrir «Fechamento Mensal» e chegar à mesma experiência de Documentos e interações. Nenhum segundo Portal/MFE/BFF criado.

**Contrato de migração (compat transitória, sem big bang):**

| Camada | Antes (RW01) | Depois (RW02) |
|---|---|---|
| Manifesto | 3 permissions, 11 rotas | 4 permissions, 13 rotas |
| `closing/documents` | `closing-documents.read` | `access.dre` (canônico) |
| `received-documents` | — | `closing-documents.read` (alias compat, fora do menu) |
| `home` | — | `access.dre`, `showInMenu` (Home DRE — entrada do público) |
| BFF `authorized_documents_reader` | read apenas | `access.dre` OR read |
| `/viewer-context` | access OR read | access OR `access.dre` OR read; capabilities `+accessDre` |
| MFE | recipient-only → `closing/documents` | `access.dre` → `dre_home`+`received_documents`; legada read → `received_documents` via alias |

**Mecânica de entrada:** a correção RW01 do Portal (`resolveAuthorizedEntryPath`, convenção do launcher `visibleRoutes[0] ?? routes[0]`) resolve o resto sem evolução de contrato do Core: `/home` é a única rota DRE visível no menu, então no basePath o usuário `access.dre` é redirecionado à Home DRE e o usuário legado à rota `received-documents`. Rotas internas negadas seguem `/unauthorized`. `DECISION_REQUIRED` não acionado — o modelo de rotas existente comporta os três públicos.

**Implementação:**

- `authz.py`: `DRE_ACCESS_PERMISSION` adicionada; `authorized_documents_reader` aceita `access.dre` OR legada — somente no boundary DRE; `authorized_user`/`authorized_admin` inalterados (testado: `access.dre` não abre rota interna).
- `viewer-context`: gate `access OR access.dre OR read`; capabilities `{access, manage, accessDre, closingDocumentsRead}` distintas.
- MFE: view `dre_home` (`/home`) + `DreHomePage` (mesmos primitivos da Home interna — `CfSectionCard`/`CfSectionRouteCard` — saudação honesta + card «Fechamento Mensal» → Documentos e interações; nenhuma rota interna, relatório ou métrica). `resolvePluginRoute` aceita `received-documents` (+ deep routes) como alias da mesma view; `receivedDocumentsBase()` mantém deep links dentro do entrypoint autorizado. Redirect de segurança por capability: `access.dre` sem `access` → apenas `dre_home`/`received_documents`; legada sem `access`/`access.dre` → `received_documents`.
- Proteção documental inalterada: capability → `RECIPIENT` → `SUBMITTED` → snapshot, 404 anti-vazamento, download auditado, mensagens `SHARED`, OPEN→ANSWERED→CONFIRMED.

**Testes:** `manifestContract` (4 permissions/13 rotas, DEPRECATED marcado na legada), `pluginRoutes` (dre_home, alias, deep links, `receivedDocumentsBase`), `viewerContextApi` (+`accessDre`, legada e nova isoladas), `test_viewer_context` (`access.dre` only, read only, ambas — 28 casos), `test_dre_authz` novo (boundary: aceita dre/legada, nega access/manage/vazio, `access.dre` ≠ access/manage, fail-closed 503, service principal, bypass superadmin). Vitest 379/380 (1 flake de timing pré-existente, passa isolado); backend 492 passed.

**Ordem de rollout (governada):** (1) deploy BFF+MFE — compat já ativa, nada muda para usuários existentes; (2) **PO importa o manifesto** no Core (`plugins/controllership-finance/controllership-finance.manifest.json`); (3) PO atribui `access.dre` ao papel DRE; (4) homologar com identidade somente `access.dre`: entrada → Home DRE → Fechamento Mensal → Documentos e interações, áreas internas bloqueadas; (5) grants legados `closing-documents.read` **permanecem** até homologação explícita; remoção da compat = gate posterior próprio.

**Rollback:** manifesto anterior no Core cobre legado; revert do commit restaura BFF/MFE. A remoção da permission legada do manifesto exige nova execução — não fazer inline.

**Risco residual:** link antigo `/closing/documents` salvo por usuário *somente-legado* nega após a importação (rota passa a exigir `access.dre`) — mitigado pela entrada do app, que redireciona à rota autorizada `received-documents`; janela fecha quando o papel recebe `access.dre`.

**Pendente:** importação do manifesto + grant `access.dre` pelo PO; smoke autenticado end-to-end — **TEST_NOT_RUN** até a identidade/grant existir.

## 11. RW03 — Home compartilhada, top bar DRE e remoção definitiva da legada (2026-10-28)

**Decisão do PO:** a Home DRE passa a usar o **mesmo padrão da Home interna** (hero, top bar, «Caminhos e funcionalidades», busca, últimos acessos) e a capability `closing-documents.read` é **descontinuada** — removida do manifesto, do BFF, do MFE e dos aliases.

**Evidência de migração no Core (PROVEN, consulta produtiva antes da remoção):**

- `controllership-finance.access.dre` **importada** — registrada na versão 0.1.3 do app (13 rotas, incluindo `/home` e `/closing/documents` sob `access.dre`);
- papel «Acesso ao Portal Controladoria e Finanças — DRE» existente com a permission;
- 1 usuário real provisionado (`contabilidade@teste.com.br`);
- `closing-documents.read` com **zero grants** (roles, grants diretos e grupos).

A descontinuação usa o mecanismo oficial: `PluginPermissionSyncService.sync_module` remove permissions ausentes do manifesto no próximo registro de versão (0.1.4) — sem SQL direto, sem apagar auditoria.

| Camada | Antes (RW02) | Depois (RW03) |
|---|---|---|
| Manifesto | 4 permissions/13 rotas (legada DEPRECATED + alias `received-documents`) | **3 permissions/12 rotas** — `access`, `manage`, `access.dre` |
| Home DRE | `DreHomePage` dedicada | **`HomePage` compartilhada** (`homeView="dre_home"`) — catálogo único `HUB_SECTIONS` projetado por capability |
| Top bar | somente interna | dinâmica por capability: «Início» → `home` (`access`) ou `dre_home` (`access.dre`) |
| Paleta/busca | restrita a `access` | projetada por capability — DRE busca apenas suas rotas |
| BFF reader | `access.dre` OR legada | **somente `access.dre`** |
| `/viewer-context` | capabilities `{access, manage, accessDre, closingDocumentsRead}` | `{access, manage, accessDre}` |
| Rota `received-documents` | alias compat | **descontinuada → `not_found`** |
| Usuário só-legado | experiência preservada | **negado** (403/404) — migração comprovada |

**Arquitetura da Home compartilhada:** o catálogo `pluginRouteCatalog.ts` tipa `HubCapability = "access" | "manage" | "accessDre"`; a seção `closing_dre` («Central de Fechamento» → «Fechamento Mensal» → `received_documents`) só aparece para `access.dre`. Usuário com `access` + `access.dre` navega sempre pela experiência interna (supressão `dreViewer` no shell e na Home — sem Início/seções duplicados). `DreHomePage.tsx` removido — não há duplicação estrutural.

**Testes:** manifestContract 3 permissions/12 rotas + legada proibida; `pluginRoutes` — `received-documents` → `not_found`; `pluginRouteCatalog` — projeção access/manage/access.dre/vazio; `HomePage`/`PluginShell` — DRE-only vê só «Fechamento Mensal», dual-cap sem duplicata; `test_dre_authz` — legada agora negada no reader; `test_viewer_context` — legada-only → 403. Vitest 382/382 (2 flakes de timing pré-existentes passam isolados); backend 491 passed; structural 15/15; Portal `manifestRoutePermission` 9/9.

**Ordem de rollout:** (1) deploy BFF+MFE neste commit; (2) **PO registra a versão 0.1.4** do manifesto no Core — o sync remove `closing-documents.read` e a rota `received-documents`; (3) homologar com identidade somente `access.dre`.

**Rollback:** BFF/MFE revertem pelo commit; a permission legada só volta por novo manifesto governado (o sync é destrutivo por design) — mitigado pela evidência de zero grants.

**Pendente:** registro produtivo da v0.1.4 pelo PO + smoke autenticado pós-import — **TEST_NOT_RUN** até a execução do PO.

## 12. RW04 — Home única no basePath e entrada canônica compartilhada (2026-10-28, REWORK da RW03)

**Decisão do PO:** não existe «Home DRE» como produto — existe **UMA HomePage** no Portal Controladoria & Finanças, no **mesmo basePath** `/apps/controllership-finance`, com conteúdo projetado por capability. A RW03 foi classificada como REWORK porque manteve uma entrada paralela (`dre_home` em `/home` com render próprio da Home).

**Causa raiz da divergência:** a RW02/RW03 resolveu a entrada multi-público no nível de ROTA — uma rota `/home` exclusiva DRE renderizava a Home — em vez de resolver a entrada no nível do APP (basePath único, capability decide o conteúdo). A top bar também diferenciava «Início» por audiência (dois itens, dois ids).

**Contrato de entrada final (Portal, sem mudança de Core/manifesto):**

- O mecanismo governado da RW01 evoluiu: `resolveAuthorizedEntryPath` (redirect à primeira rota autorizada) → **`hasAuthorizedAppEntry`** — no basePath exato, quem detém **≥1 rota autorizada** no app monta o MFE e a Home única resolve a view por capability.
- **Não é bypass genérico:** o predicado é o mesmo do launcher (o usuário já detinha uma rota autorizada e o MFE já era montado de qualquer forma — só mudava a URL). Rotas internas negadas continuam `/unauthorized`; a BFF permanece autoridade final; `ProtectedRoute` continua avaliando cada rota por permission.
- Manifesto continua com **uma permission por rota** — nenhum contrato material alterado: `DECISION_REQUIRED` não acionado.
- `/home` permanece no manifesto (`access.dre`, `showInMenu`) **somente** porque o launcher exige uma rota visível autorizada para compor a entrada do público DRE — o MFE **canonicaliza `/home` → `/`** (redirect replace, nunca renderiza página). Não há segunda Home em nenhum código.

| Camada | Antes (RW03) | Depois (RW04) |
|---|---|---|
| Entrada DRE | `/home` → view `dre_home` (render de Home em URL paralela) | `/home` → **redirect canônico** → `/` → view `home` |
| Home | `HomePage` com `homeView` branch | `HomePage` única, sem modo — catálogo por capability |
| Top bar | dois itens «Início» (`home`/`dre_home`) | **um** item «Início» (`requiredCaps: [access, accessDre]`) → basePath |
| Portal guard | redirect à primeira rota autorizada | **mount no basePath** (`hasAuthorizedAppEntry`) — mesma entrada, URL canônica |
| Redirect interno→DRE | para `dre_home` | para `home` (rede de segurança mantida para mounts obsoletos) |
| View `dre_home` | existia | **removida** (tipo, rotas, nav, hero-branch por view) |
| BFF/manifesto permissions | inalterado | inalterado — `access`/`manage`/`access.dre` |

**Matriz de autorização (inalterada):** `access.dre` autoriza Home compartilhada + `closing/documents` (projeção recipient); rotas internas (`monthly-closing`, relatórios, administração) seguem negadas no guard e na BFF; usuário sem nenhuma rota autorizada segue `/unauthorized`.

**Testes:** portal `manifestRoutePermission` reescrito para `hasAuthorizedAppEntry` (mount no basePath, sem rotas → false, rota interna → false); `pluginRoutes` — `/home` → view `home` (canonicaliza); `PluginShell` — somente-DRE na MESMA top bar, um «Início», hero «Acesso DRE»; `HomePage` — DRE vê apenas «Central de Fechamento» → «Fechamento Mensal»; dual-cap sem duplicata; vitest 382 (1 flake timing pré-existente, passa isolado); estruturais verdes; `tsc -b` plugin e portal limpos; builds ok.

**Ordem de rollout:** (1) commit/push; (2) deploy `portal` + `controllership-finance` (BFF inalterada); (3) PO pode registrar a v0.1.5 (substitui a pendente v0.1.4 — rotas iguais, só o label de `/home` mudou); (4) homologação: interno no basePath (inalterado), DRE no launcher → `/home` → `/` → mesma Home com só «Fechamento Mensal»; deep link `/home` canonicaliza; rotas internas → `/unauthorized`.

**Rollback:** revert do commit restaura guard + MFE; a permission/rota `/home` não mudam semanticamente — rollback seguro.

**Pendente:** registro da v0.1.5 no Core pelo PO + smoke autenticado interno/DRE — **TEST_NOT_RUN** até identidade autorizada.
