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
