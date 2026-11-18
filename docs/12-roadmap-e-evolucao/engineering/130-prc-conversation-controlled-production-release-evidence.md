# 130 — PRC Conversation — Controlled Production Release Evidence

> **PRC_DOC_REANCHOR_2026_11_18 — precedencia e evidencia:** Este Doc 130 documenta o release inicial de 17/11 no SHA `372b69d118` e **nao deve ser sobrescrito com digests posteriores**. O fechamento do recorte visual/funcional de conversa e UPDATE, incluindo F-01, tres abas, modal e fix do texto, esta no documento consolidado. Residual de avatar descrito aqui e historico; pipeline Core de avatares foi reportado posteriormente nos MFEs, sem afirmar foto sempre disponivel. Fonte de reconciliacao: [Fechamento PRC conversa/UX 18-11-2026](./PRC-CONVERSATION-UX-PRODUCTION-CLOSURE-2026-11-18.md). Esta nota nao reclassifica outros fluxos ou autorizacoes. 


**TASK_ID:** `EVA-PRC-CONVERSATION-CONTROLLED-PRODUCTION-RELEASE-01`
**Data:** 2026-11-17
**Tracker:** GitHub Issue #207
**RELEASE_SHA:** `372b69d118` (contém `7585a7197a` + `9378195baa` —
FIX-03 — e todos os commits P1/P2/P3/FIX-01/FIX-02 como ancestrais)

## 1. G0 — Preflight (executado antes do deploy)

| Item | Resultado |
|---|---|
| HEAD/branch | `main` @ `372b69d118` == `origin/main` (checkout PRD) |
| Commits de referência | Todos ancestrais de HEAD (P1 `2c3ab3c709`, P2 `f7ef23e3ed`, P3 `ec40197e3b`, FIX-01 `6a7e9e9c86`, FIX-02 `75af77037a`, FIX-03 `7585a7197a`+`9378195baa`) |
| Inventário afetado | `api-delpi` (executor de migrations), `engineering-api`, `plugin-ui`, `my-requests`, `engineering` |
| Estado misto detectado | `plugin-ui`/`engineering` já serviam código FIX-03; `engineering-api` e `my-requests` estavam com imagens defasadas — **deploy corrigiu apenas os dois defasados** |
| Schema PRD | V026/V027/V028 já registrados em `engineering.schema_migrations`; CHECK `prc_comment_body_nonempty = body='' OR btrim>0` verificado ao vivo |
| Collation warning | `plugins_hub` collation version mismatch (2.41 vs 2.36) — pré-existente, sem remediação nesta release |
| Backup/rollback | Digests anteriores registrados e imagens retidas no host (`8058c06d1449`, `830882f7f285`); rollback = retag + `up -d --no-deps` |
| Disco | 198G livres (48%) |

## 2. G1 — Validação autenticada (HML, mesmo código)

Smoke autenticado executado com identidade legítima `hml-tester`
(ROPC no client público `hml-test-direct`, provisionado para
homologação). **21/21 PASS**:

- Leitura no escopo do próprio caso; histórico compartilhado.
- Imagem-only (PNG) → 201, `body=""` canônico, attachment AVAILABLE.
- PDF-only → 201, `mediaType=application/pdf`.
- Texto+anexo → 201; JSON legado texto → 201, `authorDisplayName="Hml Tester"`.
- Multipart vazio → 422; arquivo inválido → 422, zero comentário órfão.
- Idempotência: retry mesma key → 200, sem duplicar.
- Metadados + download de blob autorizado (bytes íntegros).
- IDOR: attachment via outro `request_id` → 404.
- Edição para corpo vazio com anexo → 200; sem anexo → 422.
- Delete do último anexo de mensagem vazia → 422.
- Freeze terminal (caso `rejected`) → 409.

Não executado em HML: segunda identidade analista (não provisionada),
E2E visual de bolhas nos dois portais (coberto por testes de unidade:
cronologia ASC, contraste, alinhamento — FIX-02).

## 3. G2 — Migrations

| Migration | Conteúdo | Estado PRD |
|---|---|---|
| V026 | `prc_conversation` (comments + attachments) | Aplicada 2026-11-17 08:20 |
| V027 | `prc_conversation_grants` | Aplicada 2026-11-17 08:20 |
| V028 | `prc_comment_body_attachment_only` — CHECK `body='' OR btrim>0` | Aplicada 2026-11-17 08:53, constraint viva verificada |

Nenhuma migration pendente. Rollback de schema: **forward-fix apenas**
— reverter V028 invalidaria comentários válidos só-anexo já
persistidos; não revertida nesta release.

## 4. G3 — Deploy (backend-first)

Ordem executada: `engineering-api` → `my-requests` (únicos defasados);
`api-delpi` intacto (migrations já aplicadas); `plugin-ui`/`engineering`
já serviam código do release.

| Serviço | Digest antes | Digest depois |
|---|---|---|
| api-delpi | `0ce745837007` | `0ce745837007` (inalterado) |
| engineering-api | `8058c06d1449` | `1e66b99c8ce7` — healthy, `create_comment_with_attachments` presente |
| plugin-ui | `b29b4327ee7c` | `b29b4327ee7c` (já no release) |
| my-requests | `830882f7f285` | `5d5f350e0eaa` — running, `client_ref` no bundle |
| engineering MFE | `2184f248f738` | `2184f248f738` (já no release) |

Health: todos running/healthy; gateway 200 em `/apps/my-requests/`,
`/apps/engineering/`, `/apps/plugin-ui/assets/remoteEntry.js`,
`/apps/engineering-api/health`. Rotas protegidas sem token → 401.

## 5. G4 — Smoke PRD

`PRD_AUTHENTICATED_SMOKE: TEST_NOT_RUN` — o mecanismo canônico de PRD
(runbook `keycloak-prod-delia-mcp-provision`) exige **login humano real
no Portal** (token exchange via sessão); `grant_type=password` é
proibido em produção; cirurgia de senha Keycloak não é autorizada.
Usuários eval (`devin-smoke-g16`, `devin-smoke-r4`) existem no realm,
mas credenciais estão em cofre indisponível ao agente. Nenhuma mutação
em solicitações produtivas reais foi executada.

Verificação estrutural executada: auth enforced (401), código novo
servido nos 2 containers rebuildados, bundles com marcadores do
release, zero 5xx novo nos endpoints verificados.

## 6. EVA / MCP

- Tools públicas: **6** (`get_context`, `read`, `analyze`,
  `knowledge`, `execute`, `delete`) — inalterado.
- `product_registration.comment_*` permanecem ações semânticas nas
  tools existentes; **zero tools MCP novas**, zero capacidade binária.
- `comment_create` semântico segue exigindo texto (use case estrito).
- TOTVS: zero writes — escopo respeitado.

## 7. Riscos residuais

- `inspection: 'structural'` — validação por magic bytes/tipo/tamanho;
  varredura AV não implementada (residual conhecido, DTO honesto).
- Smoke autenticado PRD pendente de login humano autorizado — o gate
  funcional foi provado em HML contra código idêntico (`9378195baa`).
- Avatar corporativo no Portal Engenharia segue residual (fallback de
  iniciais, não foto validada).
- Collation mismatch `plugins_hub` — pré-existente, fora do escopo.
- Multipart parsing manual na rota (mitigado por guardas de tipo +
  testes, hardening `9378195baa`).

## 8. Rollback

- Imagens anteriores retidas no host: `infra-engineering-api
  @8058c06d1449`, `infra-my-requests @830882f7f285`.
- Procedimento: retag para `infra-<svc>:latest` + `docker compose up -d
  --no-deps <svc>`; schema permanece (V028 é compatível — código antigo
  continua rejeitando `body=''`, apenas o path novo deixa de existir).
- Rollback não remove mensagens/anexos criados após o deploy.
