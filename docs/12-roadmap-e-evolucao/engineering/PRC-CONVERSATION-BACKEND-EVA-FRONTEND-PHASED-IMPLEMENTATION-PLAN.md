# PRC — Conversa da solicitação: plano sequencial Backend → EVA → Frontends

**TASK_ID:** EVA-PRC-CONVERSATION-BACKEND-EVA-PLUGIN-UI-PHASED-PLAN-01  
**Data:** 2026-11-16  
**Status:** TARGET / PLANNED — planejamento aprovado pelo PO, nenhuma etapa executada por este documento.  
**Owner:** Engineering API (caso, comentários, anexos, política, auditoria); Plugin UI (primitivos de apresentação); My Requests e Portal Engenharia (composição/adapters); EVA (interface semântica governada).  
**Coordination:** EVA Architecture / Coordination.  
**Ordem obrigatória:** P0 inventário/contrato → P1 backend → P2 EVA → P3 frontends → P4 validação integrada/aceite → eventual release autorizado.  
**Escopo:** conversação entre solicitante e equipe de Engenharia no **mesmo caso PRC**, tanto para solicitação de criação quanto alteração de matéria-prima/produto. Sem nova tool MCP.

## 0. Decisão do PO e boundaries

1. Reutilizar toda a experiência já disponível na seção **Conversa sobre a solicitação** do My Requests: fio de mensagens, editor, formatação, imagens inline, anexos, edição autorizada, estados de leitura, horários, identidade de autor, avatar e navegação acessível; não duplicar primitivas visuais.
2. A mesma conversa deve ser vista em **My Requests → detalhe do PRC** (solicitante) e **Portal Engenharia → detalhe da solicitação PRC** (equipe técnica), com os mesmos IDs, conteúdos, ordem, autores e anexos autorizados. **Nunca** criar um segundo request em requests-api como espelho do PRC.
3. Engenharia permanece autoridade: case/request, comentário, anexo, autorização por objeto e workflow = Engineering API; o componente é somente UI. Keycloak identifica, Core governa RBAC; foto de perfil pertence ao Core. Não confiar em ator, avatar, role ou permissões enviados pelo browser/modelo.
4. EVA: expandir **ações semânticas em tools existentes** `get_context`, `read`, `execute` (e demais apenas se justificadas); sem nova tool, novo servidor MCP, broker genérico, SQL/URL arbitrário, import de código de outro domínio ou permissão implícita. REST, EVA e UI compartilham os mesmos use cases de Engineering API. Tool availability não concede AuthZ.
5. Comentários são **conversação**; não são por si só resposta formal a `return_for_correction`, `save_returned_fields` ou `resubmit_correction`, nem alteram BOM, SB1/SA5, versão técnica publicada, bandeiras ou status de atendimento. Eventos de comentário podem aparecer na timeline como referência, mas a timeline não duplica o texto da conversa.
6. Nenhum deploy PRD, grant, migração, escrita de negócio ou mudança de authority está autorizado por este plano. Cada fase exige evidência própria e handoff à Coordination.

### Fontes de código INVENTARIADAS (main, 2026-11-16)

- UI atual: `plugins/my-requests/src/components/CommentsPanel.tsx`, `plugins/my-requests/src/ui/mrUi.tsx`, `plugins/my-requests/src/hooks/useParticipantAvatarUrls.ts`, `plugins/my-requests/src/pages/RequestDetailPage.tsx`.
- Cliente REST geral: `plugins/my-requests/src/api/requestsApi.ts` — `GET/POST/PATCH /apps/requests-api/v1/requests/{id}/comments`; GET/POST/DELETE/download de `/comments/{commentId}/attachments`; `/participants/{userId}/avatar`.
- Owner das rotas gerais: `requests-api/requests_app/interface/http/routes/requests_routes.py`, `application/use_cases/timeline_use_cases.py`, `domain/services/request_capabilities_service.py`, `domain/ports/file_repository_port.py`, `migrations/V010__comment_attachments.sql`.
- My Requests já consome o caso PRC diretamente em `plugins/my-requests/src/features/product-registration/{prcApi.ts,PrcCasePage.tsx}` sob `/apps/engineering-api/v1/product-registration`; não há cliente de comentários PRC nesse adapter inventariado.
- EVA existente: `engineering-api/engineering_app/application/eva/semantic_registry.py`, `interface/mcp/{semantic_bridge.py,prc_semantic.py}`, `engineering-api/tests/test_prc_eva_parity.py`; plano `PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md` e documento mestre `54-engineering-eva-semantic-mcp-six-tools-master-refactoring-plan.md`.
- `SEMANTIC_TOOL_NAMES` = `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`. O registry inclui `product_registration.*` com status individuais `planned/proven`: não presumir que toda ação esteja executável em runtime. Nenhuma capacidade de conversa PRC identificada no inventário inicial; revalidar contra HEAD antes de implementar.
- `CommentsPanel` **não é integralmente desacoplado**: contém chamadas ao requests-api, gestão de anexos e estado. Reutilizar o visual do Plugin UI, extrair adapter/controller neutro se necessário, sem empurrar regra de negócio ou REST para o kit.
- O comportamento atual no requests-api impede mutação de conversa após status terminal, verifica acesso ao request/filial, permite editar pelo autor ou manage, usa outbox para notificação e realtime best-effort. São **referências comprovadas, não política automaticamente aprovada para PRC**.
- Avatar atual: `requests-api` fornece proxy autorizado para Core person-profile; frontend transforma foto em blob URL e usa fallback quando ausente. Para PRC escolher contrato oficial Core ou adapter Engineering-owned permitido, sem fazer Engineering API depender runtime de requests-api.
- Anexos atuais do CommentsPanel: imagens PNG/JPEG/WebP/GIF e limite frontend de 20 MiB por imagem; qualquer PDF ou arquivo genérico exige contrato/política específicos (não presumir).
- Requests-api armazena anexos de comentários em `my_requests.request_comment_attachments` (V010). Engineering **não** deve ler essa tabela nem compartilhar repository com outro bounded context.

## 1. P0 — Inventário de implementação e contrato antes do diff

**RQ-P0:** mapear o fluxo real completo, incluindo `CommentsPanel` → requestsApi → routes → use case → port → repositório/storage; IDs e participantes; autorização, paginação/ordem, editor e upload; notificações, realtime, moderação e retenção. Verificar os componentes exportados pelo Plugin UI e seu grau de desacoplamento, rotas e entidades PRC atuais, convenções Engineering de migration/ports/adapters/eventos e convenções EVA semantic registry/dispatch.

**Decisões de contrato a fechar pelo owner de Engenharia**:
- Mensagens após conclusão/rejeição: somente leitura ou política específica de reabertura; nunca copiar cegamente política de requests-api.
- Quem lê/escreve/edita/exclui anexo: solicitante autorizado, atendente responsável, gerente; branch/object AuthZ; tratamento de casos delegados e transições. Autor de comentário imutável, calculado do principal autenticado.
- Texto rico/Markdown: sanitização, allowlist, imagens inline vs anexos de clipe, limites de quantidade/tamanho/MIME, storage isolado e processo de limpeza. Erros tipados e sem vazamento de dados.
- Paginação, ordem, unread, `hasMore`, temporalidade; edição e `updatedAt` auditável, idempotência e read-back.
- Notificações ao solicitante/atendente e realtime: usar interfaces existentes apenas quando houver owner, evento/outbox e destinatário autorizado; não prometer entrega sem prova.
- Avatares: `authorUserId`, `authorDisplayName`, identidade estável do Keycloak/Core; foto por fonte autorizada Core ou contrato/adapter conhecido, fallback iniciais. Nunca guardar cópia persistente da fotografia na mensagem.
- Compensação: falha parcial no upload de imagens após criação de mensagem; comportamento de retry/idempotência e limpeza de orphan anexos.
- Separar mensagens do workflow de devolução formal, flags, documentos da solicitação e desenhos.

**AC-P0:** matriz `owner → canônico → consumer → contrato → testes`, inventário de exports Plugin UI e endpoints existentes, matriz AuthZ READ/WRITE por perfil/estado, documento de schema/error response, decisão de semântica terminal e de avatar; `TO_INVENTORY` para ausência de evidência. Nenhum código antes de aprovação do contrato.

## 2. P1 — Backend Engineering API (PRIMEIRA implementação)

**Owner:** Engineering API / PRC. **Pré-condição:** P0 ratificado. **Não alterar requests-api nem banco do My Requests.**

Rotas REST candidatas sob `/v1/product-registration` (TARGET; validar nomenclatura e envelope oficial antes do código):

| Método | Rota alvo | Operação |
| --- | --- | --- |
| GET | `/requests/{requestId}/comments` | Lista paginada, escopo por objeto, ordem estável |
| POST | `/requests/{requestId}/comments` | Criar mensagem, identidade server-side, idempotência |
| PATCH | `/requests/{requestId}/comments/{commentId}` | Editar mensagem segundo política aprovada |
| GET | `/requests/{requestId}/comments/{commentId}/attachments` | Lista de anexos da mensagem |
| POST | `/requests/{requestId}/comments/{commentId}/attachments` | Upload validado/persistido |
| GET | `/requests/{requestId}/comments/{commentId}/attachments/{attachmentId}` | Download autenticado e escopado |
| DELETE | `/requests/{requestId}/comments/{commentId}/attachments/{attachmentId}` | Remoção segundo política/auditoria |

**Contrato mínimo de leitura:** `id, requestId, authorUserId, authorDisplayName, body, createdAt, updatedAt, isMine, attachments metadata` e `capabilities` resolvidas pelo backend (ex.: `canReadConversation`, `canSendMessage`, `canEditOwnMessage`, `canUpload`). Identificadores de autor estáveis; nenhum `isMine` aceito do cliente. Campos de avatar podem ser `avatarRef` autorizado, nunca foto embutida ou URL não confiável. Versionar schema de payload e compatibilidade.

**Implementação técnica:** novas entidades/casos de uso/repos Engineering via Clean Architecture+Ports & Adapters; migration restrita ao schema Engineering se necessária; autorização backend-first com acesso ao caso/filial, status live, actor, row binding `commentId → requestId` e `attachmentId → commentId`; proteção contra IDOR; persistência e índice por caso/data/id; auditoria e read-back; eventos/outbox idempotentes quando aplicável. Nenhuma integração SQL no DB `my_requests`, nenhuma dependência runtime do requests-api. O download não deve expor paths internos nem bytes de caso alheio.

**Testes obrigatórios:** contrato REST + port+pg/in-memory, ordenação/paginação, create/edit/upload/download/delete, MIME/tamanho/escaping, idempotência/retries/falhas parciais, 401/403/404/409/422, isolamento solicitante×outro solicitante×analista×outro caso/filial, status terminal, avatar fallback/provenance, no TOTVS write, nenhum update de revisão/status. Migração reversível e plano de rollback antes de HML.

**AC-P1:** API efetiva em HML com usuário autorizado e usuário negado, resultados comprovados por HTTP, migration checksum e backup/rollback; publicar docs OpenAPI. Nenhuma UI nova antes de backend pronto. `PROVEN` só no SHA testado.

## 3. P2 — EVA semantic capability parity (SEGUNDA implementação)

**Pré-condição:** P1 backend e AuthZ comprovados, sem bypass. **Regra do PO: zero novas MCP tools.**

Usar o mesmo `PRC Conversation Application UseCase` que atende REST. Expandir o **registry existente** de `product_registration.*` e os dispatches em `semantic_bridge.py`/`prc_semantic.py`, preservando as **6 tools** e o restante do catálogo:

| Tool existente | Ação semântica TARGET | Papel |
| --- | --- | --- |
| `read` | `product_registration.comment_list` (ou `conversation_list` após inventário) | Listar conversa com escopo, paginação e metadados autorizados |
| `read` | `product_registration.comment_detail` apenas se houver consumer real | Detalhe sob demanda; evitar duplicar payload de lista |
| `execute` | `product_registration.comment_create` | Enviar mensagem no caso certo, com intenção inequívoca, idempotência e actor delegado |
| `execute` | `product_registration.comment_update` | Editar comentário permitido, com alvo exato e controle de concorrência/autor |
| `read` | `product_registration.comment_attachment_list` se útil | Consultar metadados, sem expor arquivo/URL arbitrária |
| `execute` | `product_registration.comment_attachment_add` **somente** se existir transporte seguro suportado | Anexar arquivo por mecanismo suportado; não fingir upload binário via JSON |
| `execute`/`delete` | Remoção de anexo **somente após avaliação de risco e contrato de confirmação** | Adoção explícita da tool apropriada; nunca remoção silenciosa |

Nomes são **candidatos TARGET**; aplicar Abstraction Gate antes de ampliar catálogo. `get_context` deve anunciar `planned/not_implemented` até fechar dispatch, auth, testes e paridade. Evitar capability duplicada se `product_registration.timeline` já servir algum resumo, mas mensagens completas exigem leitura própria. Não usar `knowledge` como banco de conversa; não usar `analyze` como autor de comentários. A EVA pode resumir informações que leu com acesso autorizado **sem afirmar que publicou ou enviou mensagem**.

**Segurança:** resolve `(entity,action)` em allowlist; `read` aplica objeto+filial; `execute` exige principal delegado, idempotência, targetRef explícito, policy status/autor live e postcondition de persistência. Não invocar requests-api com token de serviço substituto, nunca permitir id arbitrário de remetente, nunca converter uma instrução extraída de mensagem em comando/autorização (prompt injection). Respeitar `ENG_EVA_ACT_ENABLED` e outros gates reais; distinguir `PREPARE` e `ACT` quando exigido pelo risco. Não criar uma tool para cada endpoint.

**Testes:** matriz REST×EVA (mesmo ator/caso/estado/permissão), authorized/sibling/forbidden, comentário de outro autor, timeout, idempotent retry, canary negativa, tool count = 6, status planned rejeitado, exact target binding e resultado confirmado por read-back. Sem conteúdo de mensagens privado em logs ou contexto desnecessário.

**AC-P2:** ação(s) semântica(s) efetivamente executáveis, documentadas e provadas em HML com identidade delegada, sem nova tool, sem aumento de permissão; se upload não suportado, declarar `not_implemented` e oferecer handoff via UI.

## 4. P3 — Frontends em paridade (TERCEIRA implementação)

**Pré-condição:** P1/P2 aceitos no recorte correspondente. **Ordem interna:** Plugin UI first → My Requests PRC → Portal Engenharia PRC.

- Inventariar `MyRequestsMessageThread`, `MyRequestsMentionComposer`, `MyRequestsRoomConversationChatColumn`, `MyRequestsAttachmentPreviewStrip` e os exports reais do Plugin UI. **Não** mover arbitrariamente o `CommentsPanel` que hoje chama requests-api; criar adapter/controller/provider de dados PRC por contrato, de modo que `CommentsPanel` de solicitação geral continue apontando requests-api e o PRC aponte Engineering API.
- Componentes visuais compartilhados exclusivamente via `@delpi/plugin-ui`; sem cópia de CSS, editor, chat ou avatar específico em cada MFE. Extensão do kit só quando faltar primitivo reutilizável e houver Abstraction Gate aprovado.
- `plugins/my-requests/src/features/product-registration/PrcCasePage.tsx`: conversa na solicitação PRC; preservar detalhes técnicos, formulário/correções, timeline e documentos existentes.
- `plugins/engineering/src/features/product-registration/`: mesma conversa no detalhe da solicitação para analista; sem segundo feed; os dois MFEs consomem a mesma Engineering API.
- Avatar/nome exibidos conforme **usuário real autor** (solicitante ou colaborador Engenharia), via subject estável e fonte oficial Core autorizada; próprio autor alinhado visualmente como no componente existente; fallback a iniciais, sem avatar fictício ou associação por papel presumido.
- Editor deve preservar formatação, colagem de imagens, clipe, visualização/zoom, edição autorizada e estados de erro/recuperação conforme P1. Realtime/refetch conforme contrato real, sem inventar sincronização.
- Read-only após terminal segundo política P0, não simplesmente por regra local de UI. Esconder desabilitação não substitui 403 backend.
- Não tratar mensagens livres como alterações oficiais da ficha nem como respostas estruturadas de correção.

**AC-P3:** a mesma mensagem enviada em uma superfície aparece na outra com conteúdo, timestamp, autor, foto/fallback e anexo idênticos após refetch; editar preserva autoria e auditoria; 403 em caso alheio; acessibilidade de teclado/ARIA; mobile 320/390, tablet 768, desktop 1440, zoom 200%, light/dark; zero duplicação de componente/código de negócio.

## 5. P4 — Matriz de aceitação, verificador e release

**G0 reanchor:** authorities, HEAD/origin/main, git status, worktree concorrente, RQ/AC/contratos e equivalentes.
**G1 backend:** P1 com migrations, object AuthZ, API e smoke HML.
**G2 EVA:** P2 six-tools preserved + catalog honesty + testes semânticos com delegated identity.
**G3 frontend:** P3 Visual E2E My Requests e Portal Engenharia; mesma mensagem cross-app.
**G4 integração:** criação/edição/anexo/erro/terminal em HML com usuários reais autorizados e negativos sem grant artificial; métricas e logs seguros.
**G5 independência:** agente verificador no SHA exato, findings → ordens de correção → correção mínima → rerun até fechar; `INCONCLUSIVE` não pode virar `PASS`. Arquivar evidências versionadas sem PII/secrets.
**G6 release:** predeploy separado, delta e dependências mapeados, backups e rollback para migration, aprovação explícita do PO/Coordination antes de PRD. Deploy backend → EVA capabilities/config → Plugin UI (se alterado) → My Requests → Engineering; smoke autenticado e read-back. Nenhuma implantação por este plano.

### Outcomes por fase
| Fase | Estado agora | Dependência |
| --- | --- | --- |
| P0 contrato | TO_INVENTORY / TARGET | owner Engenharia ratifica semântica terminal/identidade/notificações |
| P1 backend Engineering API | PLANNED | P0 |
| P2 EVA ações semânticas existentes | PLANNED | P1 |
| P3 Plugin UI + 2 MFEs | PLANNED | P1/P2 |
| P4 E2E/aceite/release | PLANNED | P3 + autorização separada |

**Handoff imediatamente seguinte:** abrir task de execução exclusivamente **P0 + P1**; atualizar este arquivo com contratos e evidências. Não misturar backend, EVA e frontend no mesmo diff antes dos gates.

## 6. Padrão de relatório exigido por fase

`TASK_ID | BASE_HEAD | FINAL_SHA | OWNER | RQ/AC | REST_CONTRACT | AUTHZ_MATRIX | MIGRATIONS | SOURCE_OF_TRUTH | EVA_TOOL_COUNT | SEMANTIC_ACTION_STATUS | TESTS | HML_RUNTIME_SHA | CROSS_APP_EVIDENCE | VERIFIER_VERDICT | FAIL/PASS/INCONCLUSIVE/TEST_NOT_RUN | RESIDUAL_RISKS | PRD_DEPLOY | ROLLBACK | NEXT_ACTION`.

**Arquitetura:** mudança de owner/SoT, novo contexto ou autoridade = `ARCHITECTURE_DECISION_REQUIRED` e devolver à Coordination. MCP, UI, modelos e documentação nunca concedem permissão ou authority.

## 7. P0+P1 executado — registro de implementação (commit `203b4b6cd3`)

**Executor:** Devin · **TASK_ID:** `EVA-PRC-CONVERSATION-P0-P1-BACKEND-CONTRACT-AND-IMPLEMENTATION-01`

### Contrato ratificado (autoridade existente, sem `ARCHITECTURE_DECISION_REQUIRED`)

**Modelo (schema `engineering`, V026/V027):** `product_registration_comments`
(id, request_id FK, author_subject, author_display_name snapshot, body CHECK
non-empty, row_version CAS, created_at/updated_at; índice
`(request_id, created_at, id)`) e `product_registration_comment_attachments`
(id, request_id FK, comment_id FK, original_file_name, media_type, size_bytes,
sha256, storage_key privado, state `PENDING_SCAN|AVAILABLE|REJECTED|QUARANTINED|DELETED`,
uploaded_by_*, correlation_id). Grants `eng_prc` SELECT/INSERT/UPDATE — sem
DELETE (remoção = `DELETED` lógico + purge de bytes).

**AuthZ (fail-closed):** sem principal → 401; sem permissão do módulo → 403;
object AuthZ via `_scope_check` (analista `engineering.access` com fila
global, ou requester/assignee do caso). Editar/anexar/remover: autor da
mensagem ou analista. Caso terminal (`completed`/`rejected`) → conversa
frozen (409 para mutações; leitura permanece). `authorSubject` sempre do JWT.

**Rotas (`/v1/product-registration/requests/{request_id}`):** `GET /comments`
(page, pageSize≤200, ASC+id) · `POST /comments` (`Idempotency-Key`: replay
200 mesmo payload / 409 divergente) · `PATCH /comments/{id}`
(`expectedVersion` CAS→409) · `GET/POST /comments/{id}/attachments` (10MB,
PDF/PNG/JPEG/WebP por magic bytes, dedup sha256) · `GET|DELETE
…/attachments/{attId}` (nosniff+no-store; delete lógico).

**Avatar:** sem cópia persistida; frontend futuro resolve via contrato de
perfil Core (`/me/directory/users/lookup`, já governado) + fallback iniciais.

**Artefatos P1:** `domain/product_registration/conversation.py`; port +9
métodos; service +7 métodos (`_assert_conversation_open`, `_get_scoped_comment`,
idempotência, CAS, dedup, purge de órfãos, `_emit_change` comment_* pós-commit);
3 adapters (postgres/in-memory/unavailable); 7 rotas; migrations V026/V027;
`tests/test_prc_conversation.py` (17 casos HTTP).

**Testes executados:** `test_prc_conversation.py` 17/17 PASS (positivo, irmão,
negativo: 401/403/404/409/413/422, não-autor upload 403, IDOR cross-request
404, frozen 409, CAS 409, idempotência replay); regressão
`test_product_registration + prc_attachments + ref023*` 127 PASS / 10 skip
(postgres real: SKIPPED no dev local — executado em HML).

**Verificador:** round 1 `INCONCLUSIVE` — engine `devin` sem login no executor
(restrição de ambiente registrada em `verdicts.jsonl`; não é aprovação).

**Pendências:** smoke HML autenticado; OpenAPI/doc Engineering API;
ledger Engineering + Issue #207.

## 8. P2 executado — integração semântica EVA (commit `f7ef23e3ed`)

**Executor:** Devin · **TASK_ID:** `EVA-PRC-CONVERSATION-P2-SEMANTIC-MCP-INTEGRATION-01`

**Catálogo:** `SEMANTIC_TOOL_NAMES` = 6 (intocado). Três actions
`product_registration.*` adicionadas ao registry com `status=proven`:

| Action | Tool | Risk | Phases | Requires |
|---|---|---|---|---|
| `comment_list` | `read` | read | — | `request_id` (+page/page_size) |
| `comment_create` | `execute` | moderate | act, prepare | `request_id` + `body` |
| `comment_update` | `execute` | moderate | act, prepare | `request_id` + `comment_id` + `body` + `expected_version` |

**Dispatch:** `_READ_DISPATCH` + `_EXECUTE_DISPATCH` →
`prc_semantic.read_action`/`execute_action` → MESMOS use cases REST
(`list_comments`, `create_comment`, `update_comment`). Autor sempre
`prc_actor_from_principal(context.user)` — `authorUserId` do payload
ignorado (testado). PREPARE valida sem persistir. Update exige CAS
`expected_version` no caminho semântico.

**Fronteira de injeção:** corpos de mensagem são dados — registrado
nas notes do catálogo; nenhum conteúdo lido é promovido a instrução,
permissão ou confirmação (boundary do modelo, não do transporte).

**Anexos:** `ATTACHMENT_WRITE_CAPABILITY=NOT_IMPLEMENTED` — sem
transporte binário MCP aprovado; metadados de anexos já chegam via
`comment_list`. Nenhuma sétima tool criada.

**Testes (38/38):** `test_prc_eva_parity.py` +`TestConversationParity`
8 casos — dispatch+tool count, list paridade, escopo negado espelhado,
create→readback REST (autor=delegado), PREPARE não-persiste,
idempotência replay, update autor+CAS stale, não-autor 403, IDOR
cross-request, frozen terminal. Regressão eva/prc: 618 pass, 1 falha
pré-existente ortogonal (`test_eva_val01_structure_table_roundtrip`,
módulo drawing — sem interseção com o diff).

**HML:** engineering-api rebuilt (mesma imagem base + SHA f7ef23e3ed);
catálogo in-container: 6 tools, 3 actions `proven` com dispatch
registrado. Integração semântica exercida in-container contra Postgres
real: list (comentário P1 visível), create (autor=subject delegado,
spoof ignorado), update CAS, replay idempotente mesmo commentId,
readback total=2. **Smoke MCP-over-HTTP autenticado: TEST_NOT_RUN**
— sem identidade legítima: sessão-fixture contém placeholders
(`hml-fixture-unreachable-glpi`, não JWT), senha hml-tester desconhecida
e P2 proíbe nova cirurgia manual no KC. Reencaminhado ao owner de
infra: provisionar `infra/.env.hml` no checkout HML (resolve issuer +
credenciais de teste pelo bootstrap canônico).

**Verificador:** r1 `INCONCLUSIVE` (engine sem login — registrado em
`verdicts.jsonl`). **Issue #207:** `gh` sem auth e sem conector
disponível — atualização bloqueada, evidência versionada neste doc.

**NEXT_ACTION:** P3 — Plugin UI + adapters My Requests/Engenharia.

## 9. P3 executado — conversa compartilhada nos dois MFEs (commit `ec40197e3b`)

**Executor:** Devin · **TASK_ID:** `EVA-PRC-CONVERSATION-P3-SHARED-UI-HML-DEPLOY-01`

**Abstraction Gate:** `ConversationPanel` único em
`plugins/plugin-ui/src/components/conversation-panel/` — port do
orquestrador do `CommentsPanel` desacoplado de bounded context via
`ConversationApi` injetado (7 operações) + `loadAvatar` opcional +
prefixo `delpi-ui` (mesmo kit MessageThread/MentionComposer/
AttachmentPreviewStrip/RoomShell/FilePreviewModal → visual idêntico).
`CommentsPanel` legado (requests-api) intocado — zero regressão.

**Adapters (mesmo requestId, mesmo histórico):**
- `plugins/my-requests/.../prcConversationApi.ts` — envelope PRC
  (`commentId/authorSubject/isMine/version/edited`, `attachments`,
  `attachmentId/state`), Idempotency-Key no create, `expectedVersion`
  no PATCH, multipart autenticado, download bearer.
- `plugins/engineering/.../api/prcConversationApi.ts` — idem via
  httpClient do MFE.

**Montagem:** aba **Histórico** — `PrcCasePage` (MR) e `PrcDetailPage`
(ENG), seção "Conversa sobre a solicitação". `conversationFrozen` em
`completed|rejected` (espelha `TERMINAL_STATUSES`); `canComment` é
affordance visual — autorização efetiva sempre backend.

**Avatar:** MR usa `downloadParticipantAvatarBlob` (requests-api→Core
`/integrations/person-profiles/{id}/photo` S2S) — foto real de
solicitante e analista. ENG: **iniciais** — engineering-api não possui
rota governada de foto por usuário (Core expõe foto terceira só via
S2S); acoplar à requests-api violaria bounded context.
`ARCHITECTURE_DECISION_REQUIRED`: adicionar rota de avatar por-usuário
à engineering-api (espelho do BFF da requests-api) é decisão da
Coordination — registrado como residual.

**Testes:** adapters (envelope/idem/CAS/erros) 8+6, mount estrutural
2+2 — 14 novos, todos verdes. Regressão: plugin-ui 322, engineering
PRC 249, my-requests 235 (2 falhas pré-existentes em `process-issue`,
fora do diff). Builds vite OK nos 3.

**HML:** checkout `~/projetos-teste/delpi-central` (stack real;
`~/projetos/delpi-central` é só código) — pull + compose
`delpi-hml/plugin-ui|my-requests|engineering` rebuilt na ordem
remote→MFE. Healthy 3/3; `ConversationPanel` presente no
`remoteEntry` servido. Digests: plugin-ui 42424f94c82f,
my-requests 742ef4dabee1, engineering b7f6b83fe4d4.

**E2E autenticado cruzado:** `INCONCLUSIVE` — sem identidade legítima
(mesmo bloqueio P1/P2: hml-tester sem senha conhecida, fixture com
placeholders, proibida nova cirurgia KC). Não declarado PASS.
**Verificador:** r1 `INCONCLUSIVE` (engine sem login — registrado).
**Issue #207:** gh sem auth — evidência versionada aqui.

**NEXT_ACTION:** P4 — E2E cruzado com 2 identidades + aceite visual PO.

## 10. P3-FIX executado — correção visual/funcional pós-aceite PO (commit `6a7e9e9c86`)

**Executor:** Devin · **TASK_ID:** `EVA-PRC-CONVERSATION-P3-UX-FUNCTIONAL-CORRECTION-HML-01`
**Base:** `c1d904b8cc` (origin/main revalidado).

**Diagnóstico (evidência no código):**
- RQ-01 real: `PrcCasePage` usava `CaseTab`/`mode="tabs"` Ficha técnica|Histórico — divergente do padrão do módulo. **Corrigido:** página única de seções verticais (ficha → documentos → conversa → linha do tempo).
- RQ-02/03 pipeline íntegro: backend `isMine = author_subject == actor.user_id` (mesma fonte) → adapter → `mine` → `item--mine` → `flex-end`; bolhas sempre `article.delpi-ui-message-thread__bubble` com fundos distintos (7%/18%); CSS canônico dual-class presente no bundle. Causa mais provável do sintoma HML: dados de smoke P1/P2 (identidade sintética única → tudo à esquerda + agrupamento `continues` ocultando identidade) combinado à ausência de identidade nas mensagens próprias. **Corrigido:** `showMineIdentity` no thread do painel — autor+avatar também nas mensagens próprias (layout esperado pelo PO).
- RQ-04 íntegro: upload multipart `AVAILABLE`→dedup→storage, inline `attachment:{id}` reescrito `pending:`→uuid + PATCH, reload lista metas e baixa blob autenticado → object URL; `PENDING_SCAN` sem preview. Sem evidência de defeito de código; persistência só comprovável com E2E autenticado.
- Engenharia mantém abas operacionais (draft/verificação/histórico/revisões — workspace de analista, não o padrão de acompanhamento reportado); conversa já é seção vertical na área de histórico. Divergência intencional documentada.

**Testes:** `ConversationPanel.alignment.test.tsx` novo (2) — `isMine`→`item--mine`/bolha-mine, recebida→bolha comum+autor+avatar+time, inversão por identidade. Módulo PRC my-requests 18/18; plugin-ui 65/65 nos módulos tocados; my-requests total 243 (mesmas 2 falhas pré-existentes `process-issue`). Builds vite OK.

**HML:** push `6a7e9e9c86` → pull em `operador@srv-api:~/projetos-teste/delpi-central` → `hml-compose.sh up --scenario plugin-ui|my-requests`. Healthy; bundle servido sem `prc-case-tab`, `showMineIdentity` presente no remoteEntry. Digests: plugin-ui `e8e72315fb45`, my-requests `22a4c093b77f`, engineering `b7f6b83fe4d4` (inalterado — consome o panel via federação).

**E2E autenticado:** `TEST_NOT_RUN` — segue sem identidade legítima (mesmo bloqueio P1–P3). Não declarado PASS; aceite visual pendente do PO.
**Issue #207:** `gh` sem auth nesta sessão — evidência versionada aqui.

**NEXT_ACTION:** aceite visual do PO em HML.

## 11. P3-FIX-02 executado — cronologia e contraste das bolhas (commit `75af77037a`)

**Executor:** Devin · **TASK_ID:** `EVA-PRC-CONVERSATION-P3-CHRONOLOGY-BUBBLE-CONTRAST-HML-02`
**Base:** `911ff0f7da` (origin/main revalidado; rebase sobre 62 commits concorrentes, WIP preservado).

**Causas-raiz confirmadas no código:**
- Ordem invertida: `threadItems` fazia `[...items].reverse()` herdado
  do `CommentsPanel` (cuja requests-api retorna DESC). A Engineering
  API retorna `ORDER BY created_at ASC, id ASC` — o reverse produzia
  DESC, recentes no topo. Corrigido: ordenação explícita única por
  `createdAt`/`id` ASC no painel; nunca por autor/isMine.
- "Grupos separados": efeito combinado da ordem invertida (mensagens
  por autor caíam juntas por coincidência temporal dos smokes) +
  bolha recebida invisível — não havia `space-between` nem
  distribuição de altura no CSS (verificado).
- Contraste: bolha recebida usava `color-mix(text 7%, surface)`
  sobre container `--delpi-ui-surface-muted` (≈ text 8%) — quase
  idênticos. Corrigido: superfície canônica + borda
  `var(--delpi-ui-border)`; própria mantém accent 18%. CSS canônico
  do kit — melhora também o `CommentsPanel` legado (mesmo container
  muted), sem divergência de identidade visual.
- Scroll já era correto: `stickToBottom` inicial true + tracking
  onScroll (AC-05 herdado).

**Testes:** +1 cronologia (entrada DESC/intercalada → DOM ASC por
id, lados alternando); contrato CSS atualizado (borda 1px, sem
7%). 30/30 nos módulos tocados. Build vite OK.

**HML:** push → pull em `operador@srv-api` → `hml-compose.sh up
--scenario plugin-ui` (único componente afetado; MFEs consomem via
federação). Healthy; CSS servido com a regra nova. Digests:
plugin-ui `cf413fa75564`, my-requests `22a4c093b77f`,
engineering `b7f6b83fe4d4` (ambos inalterados — correto).

**E2E autenticado:** `TEST_NOT_RUN` — bloqueio de identidade
persiste. **Verificador:** INCONCLUSIVE (engine sem login).
**Issue #207:** `gh` sem auth — evidência versionada aqui.

**NEXT_ACTION:** aceite visual do PO em HML.
