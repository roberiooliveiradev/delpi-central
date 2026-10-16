# 86 — Rework R1 dos achados G1/G2 (doc 85) — Relatório de execução

**Status:** `REWORK_EXECUTED — CANDIDATE_FOR_INDEPENDENT_REVIEW / RUNTIME_NOT_AUTHORIZED`
**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R1`
**BASE_HEAD (reanchor real):** `c3e090ac70977e81fbf7bdd47a391683ab6199cd` (origin/main verificado)
**REVIEW_BASE:** doc `85-presentation-v2-g1-g2-independent-architecture-review.md` — candidato `d5ed426a08f0fee2aa9179a50d75f828fadd72b2`, veredito `REWORK`
**CP:** `CP-333` — `PLANNED_NOT_PASS` (inalterado)
**Tipo:** rework contratual/documental — **zero diff de runtime**

> B2 aqui = Markdown conversacional (spec 82/83), não `C3-STAGE-02-B2` (PREPARE/ACT). Trilhas independentes; nada se transfere.

## 1. Achados do doc 85 → correção aplicada

| Achado | Criticidade | Correção realizada | Evidência |
|---|---|---|---|
| `RW-G1-01` produtor sem estrutura comprovada | CRITICAL | Inventário do pipeline real provou que o seam já existe: `SpecialistOutcome.structured` (Mapping tipado) → `render_specialist_outcome` (projeção determinística, sanitizada, bounded) → `attempt.content` → `InteractiveTurnResult` → `serialize_result`/`compose_presentation`. Proposta corrigida de `NEW GovernedResponseFormatter` para **EXTEND da projeção existente** (doc 84 §4) | §E.2 — fidelity probe 16/16 |
| `RW-G1-02` links sem fonte tipada | CRITICAL | Inventário concluiu: **não existe fonte tipada de destino navegável** no caminho do turno (`provenance` é URL-free por design; `WorkspaceEntityRef` é hint inbound; `SourceRef` sem URL). Pacote de decisão completo com 3 alternativas (L1 typed field em `structured` — recomendado; L2 `LinkRef` novo; L3 deferir = exige Product Master). `ARCHITECTURE_DECISION_REQUIRED=LINK_SOURCE_TYPED` formalizado — **escopo D1/D6/D7 não reduzido silenciosamente** (doc 84 §2.4) | §D |
| `RW-G1-03` schema/fallback incompletos | HIGH | Fragmento JSONC promovido a schema real draft 2020-12: `contracts/presentation-v2.proposal.schema.json` — envelope completo, discriminadores, nulls, limites, versionamento, `additionalProperties:false` (fail-closed). Validado mecanicamente | §E.1 — 22/22 checks |
| `RW-G2-01` reuse gate insuficiente | CRITICAL | Matriz REUSE/EXTEND/NEW corrigida com vocabulário normativo (`NOT_SELECTED` por candidato), nomes reais verificados, opção EXTEND analisada com evidência (renderers existentes produzem string HTML consumida por `dangerouslySetInnerHTML` — estender exigiria trocar modelo de saída), probe do lexer executado | §E.3 — 22 casos adversariais |

## 2. Inventário do produtor governado (RW-G1-01)

Pipeline real (verificado em `c3e090ac70`):

```text
SpecialistOutcome{ content_text, structured, limitations }   # domain/specialist_interop/model.py:124
  → render_specialist_outcome()                              # capability_provision/orchestration.py ~2117
       _sanitize_renderable (redação _SENSITIVE_KEY_NAMES + _redact_text)
       _business_lines (unwrap data/result/payload/response + items)
       _format_records / _format_structured (determinístico, depth≤3, MAX_RENDER_LIST_ITEMS)
       bounds: MAX_RENDER_CONTENT_CHARS=2000 + sufixo fixo "…(resultado parcial — truncado)" (2032 máx)
  → GovernedCapabilityAttempt.content (render injetável em _success_attempt)
  → InteractiveTurnResult.content + message_kind + owner_hint + provenance + confirmation
  → serialize_result → content legado + presentation v1 (compose_presentation)
```

**Categorias formais (doc 84 §4.2):**

- **A — estruturado tipado:** `SpecialistOutcome.structured` → única fonte para `markdown_safe` estruturado; mapeamento determinístico idêntico ao das linhas já emitidas hoje.
- **B — texto pré-estruturado pela fonte:** `content_text` do owner → verbatim, `plain`.
- **C — prosa:** respostas de modelo/status → `plain` inerte; proibido inferir estrutura.

`EXISTING_EQUIVALENT = YES` para a função de projeção — `render_specialist_outcome` já recebe o outcome tipado e produz projeção bounded; o callable `render` em `_success_attempt` já é injetável. Nenhum formatter paralelo é necessário.

## 3. Inventário de links (RW-G1-02)

| Fonte | Existe? | Navegável? |
|---|---|---|
| `GovernedCapabilityProvenance`/`SourceRef` | SIM | NÃO — `{source_id, source_system, observed_at}`; URL-free por design |
| `WorkspaceEntityRef` | SIM (inbound) | NÃO — hint não confiável, sem href, `grants_authorization()=False` |
| `owner_hint` | SIM | NÃO — vocabulário literal URL-free |
| Campos URL em `structured` | POSSÍVEL (payload do owner) | NÃO tipado hoje — requer allowlist de chaves (opção L1) |
| `RouteRef`/`EntityRef`/`LinkRef` outbound | NÃO EXISTE | — |
| Portal `sameAppAnchorNavigation` | SIM | `<a href>` same-origin funciona; SPA intercept dentro do app/shell, reload cross-app — seguro |

Decisão pendente registrada no doc 84 §2.4 (L1/L2/L3). **G3 permanece bloqueado** até `LINK_SOURCE_TYPED` ser decidido por Architecture Coordination / Product Master.

## 4. Schema `presentation.v2` (RW-G1-03)

Artefato: `docs/12-roadmap-e-evolucao/delia/contracts/presentation-v2.proposal.schema.json`

- `version:"2"` (const — versões desconhecidas/ausentes caem fora do schema → fallback legado §2.5)
- bloco `text`: `format` obrigatório ∈ `{plain, markdown_safe}`; `text` ≤ 16.384
- bloco `notice`: `role:"owner_hint"` único
- envelope: `message_kind` ∈ 7 valores canônicos; `semantic_status` ∈ EpistemicClass ∪ `null`; `grounding_status` ∈ {GROUNDED, NON_GROUNDED}; `allowed_interactions` ⊆ {reply, confirm, reject}; `blocks` 1–8
- `additionalProperties:false` em todos os níveis — contrato fechado, fail-closed (decisão registrada §6 do doc 84; reversível no freeze)

## 5. Segurança e reuse (RW-G2-01)

- **REUSE:** `marked` ^18.0.9 (`marked.lexer` apenas) — dep existente do plugin-ui, homologado.
- **EXTEND:** `render_specialist_outcome` (produtor) + `compose_presentation` (envelope v2 aditivo) — seams existentes, sem componente paralelo.
- **NEW:** `ConversationMarkdown` em plugin-ui — justificada por modelo de saída incompatível: todos os renderers existentes emitem **string HTML** para `dangerouslySetInnerHTML` (`MarkdownDocumentView` linha 176, `MessageThread` bodyMode=markdown via `markdownToRichTextHtml`+DOMParser sanitize). Permitir qualquer um deles em DÉLIA reintroduziria innerHTML/URL política errada (`attachment:`/`blob:`/`mailto:`/relativos permitidos pelo denylist atual).
- **NOT_SELECTED** com justificativa: `MarkdownDocumentView`/`buildMarkdownDocumentModel`, `markdownToRichTextHtml`, `messageThreadMarkdown`, `stripDangerousRichTextTags`, `ChatMermaidBlock`, `markdownImageTokens`/`richTextInlineImage`, turndown-like p/ copy.

## E. Evidência de execução

### E.1 Contract/schema tests — 22/22 PASS

`python3` + `jsonschema 4.10.3` (Draft 2020-12) sobre o artefato real:

- Positivos (4): `v2_plain`, `v2_markdown_safe`, `v2_text_plus_notice`, `v2_confirmation_interactions`.
- Negativos (18): `version` "1"/ausente/"9"; `format` ausente/`"html"`; `kind` desconhecido; prop extra em bloco (`href`) e envelope; `blocks` vazio/9 itens; `text` 16.385 chars; `message_kind`/`allowed_interactions`/`notice.role` inválidos; `notice` com `format`; payload não-objeto; bloco `text` sem `text`.

### E.2 Fidelity tests do produtor existente — 16/16 PASS

`.venv/bin/python` sobre `render_specialist_outcome` (delia-api, HEAD `c3e090ac70`):

- `A.ids_verbatim`, `A.qty_units_verbatim` (`150.5 KG`, `3 UN`), `A.order_preserved`, `A.list_shape` — registros `OP-10293`/`OP-10294` projetados verbatim e ordenados.
- `B.verbatim`, `B.linebreaks_preserved` — texto owner com quebras preservado byte-a-byte.
- `C.literal_preserved` — `**não**` e `[x](y)` inertes (fonte nunca interpretada).
- `SECRET.access_token_redacted`, `SECRET.client_secret_redacted`, `SECRET.business_kept`.
- `SECRET.residual_bare_token_key` — **gap documentado**: chave bare `token` não consta de `_SENSITIVE_KEY_NAMES` (cobre `accesstoken`/`refreshtoken`/`sessiontoken`/`bearertoken`/`candidatetoken`/`clientsecret`/`password`/`apikey`/…). Residual do runtime atual registrado para decisão de segurança dedicada.
- `EMPTY.truthful` — `Nenhum resultado encontrado.`
- `GENERIC.business_shown` — status genérico suprimido quando há payload.
- `TRUNC.bounded` (≤2000+sufixo fixo=2032), `TRUNC.suffix_marked`, `TRUNC.declared` (`result_truncated`).

### E.3 Security probes do lexer `marked` — 22 casos executados

`marked.lexer` (v18, plugin-ui) classifica como tokens discretos: `html` (inline `<b>`/bloco `<script>`), `image`, `link` (incl. `javascript:`, `data:`, relativo `../`, `#`, `/apps/…`, `https:`, `JaVaScRiPt:` ofuscado, `java%73cript:` encodado, autolink), `table` GFM, `code` (mermaid → code inerte), `checkbox` em `list_item`, `heading` depth≥1, `del`, `blockquote`/`list` aninhados sem cap próprio. Conclusão: negação-por-construção é exequível — cada tipo decide antes de materializar; renderer deve impor depth/node caps (lexer não limita). **Isto prova a política sobre o parser; não prova um renderer ainda não implementado.**

### E.4 Regressões executadas

| Suíte | Resultado | Comando |
|---|---|---|
| delia-api presentation/orchestration/runtime | **195/195 PASS** | `pytest tests/test_interaction_presentation.py tests/test_specialist_capability_orchestration.py tests/test_interaction_runtime.py` |
| plugins/delia vitest | **191/191 PASS** (16 files) | `npx vitest run` |
| plugin-ui markdown+rich-text | **149/149 PASS** (16 files) | `npx vitest run src/components/markdown src/components/rich-text` |
| plugins/delia typecheck | 3 erros **pré-existentes** em plugin-ui (`InitialsAvatar:198`, `layout/index:274` `PublishedAvatarProfile`, `TaskDetailCard:136`) — baseline idêntico ao B1 e §6.194; outro owner, fora do escopo | `npm run typecheck` |
| build/federation | `TEST_NOT_RUN` | docs-only task; nenhum artefato de build afetado |

### E.5 SSH validation (executada)

- `SSH_ENVIRONMENT`: `srv-api` (homolog/dev autorizado, mecanismo existente `ssh operador@…`, key auth — sem credenciais no relatório).
- `SSH_ACCESS_STATUS`: OK (BatchMode, read-only).
- `REMOTE_CHECKOUT_HEAD`: `4af3d656c6` (= origin/main no momento da inspeção; checkout limpo). Observado antes do push do commit concorrente `c3e090ac70` — diferença é docs-only, sem impacto de runtime.
- `DEPLOYED_RUNTIME`: `delpi-delia-api` Up healthy, `delpi-delia` Up, `delpi-portal` Up 9 days (docker ps).
- `CONTRACT_AVAILABILITY`: `presentation.py` presente com `PRESENTATION_CONTRACT_VERSION` (v1 ativo); `orchestration.py` e `plugin-ui/package.json` presentes.
- `GIT_HEAD_MATCH`: remoto ≠ HEAD candidato local na hora da inspeção → testes remotos **não** tratados como evidência deste commit (regra §6.4 respeitada).
- `READ_ONLY_INSPECTION`: SIM — nenhuma escrita, restart, migração ou PREPARE/ACT.

## 6. Limitações declaradas

- Runtime B2 **não** implementado — propostas são contrato/design; `ConversationMarkdown` não existe em código.
- `LINK_SOURCE_TYPED` pendente — decisão material requerida antes de G3.
- Residual `_SENSITIVE_KEY_NAMES` (bare `token`) é do runtime vigente — não corrigido aqui (fora de escopo; decisão security dedicada).
- Typecheck: 3 erros plugin-ui pré-existentes não são desta task.
- Todos os probes rodam em `/tmp` — nenhum artefato de teste entrou no repo (probes são evidência descrita + reproduzível; fixtures inline sem dados sensíveis).

## 7. Estado preservado

`G1=REWORK→CANDIDATE_REWORKED` / `G2=REWORK→CANDIDATE_REWORKED` (nova revisão independente pendente) / `G3=BLOCKED` / `G4=TEST_NOT_RUN` / `CP-333=PLANNED_NOT_PASS` / `PRESENTATION_V1=CURRENT_RUNTIME` / `PRESENTATION_V2=CONTRACT_TARGET` / `C3_EXECUTED=NO` / `C4_AUTHORIZED=NO` / `C5_AUTHORIZED=NO` / `RUNTIME_B2_IMPLEMENTATION_AUTHORIZED=NO` / `PHASE_PROGRESSION=NONE` / `INDEPENDENT_REVIEW=PENDING`.

**Próximo bounded recomendado:** revisão independente do doc 84 reworked + decisão `LINK_SOURCE_TYPED` → `DELIA-UX-CONVERSATION-MARKDOWN-B2-G3-BRIEF` (somente após ACCEPT).
