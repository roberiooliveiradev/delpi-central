# 84 — Proposta `presentation.v2` e Reuse/Security Review de Markdown (G1/G2)

**Status:** `G1_CONTRACT_PROPOSAL=REWORKED_R1_CANDIDATE_FOR_REVIEW / G2_REUSE_SECURITY=REWORKED_R1_CANDIDATE_FOR_REVIEW / RUNTIME_NOT_AUTHORIZED`

**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-01` → rework `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R1` (doc 85 = fonte dos achados)
**BASE_HEAD R1:** `c3e090ac70977e81fbf7bdd47a391683ab6199cd`
**CP:** `CP-333` (matriz 25 — `PLANNED`, não PASS)
**Tipo:** CONTRACT-FIRST / DOCUMENTATION ONLY — nenhum diff de runtime nesta task.

> **Histórico R1:** a revisão independente (doc 85) emitiu `REWORK` sobre a versão anterior (`d5ed426a08`) com 4 achados — RW-G1-01 (produtor sem estrutura comprovada), RW-G1-02 (links sem fonte tipada), RW-G1-03 (schema/fallback incompletos), RW-G2-01 (reuse gate insuficiente). Esta revisão corrige os quatro com inventário real, schema mecanicamente validado e probes executados. O relatório de rework é o doc 86.

> B2 aqui = Markdown conversacional da spec 82/83. **Não** confundir com `C3-STAGE-02-B2` (governança de execução PREPARE/ACT, ledger §6.183/§6.184). Nada se transfere entre as trilhas.

Este documento é a **proposta** submetida à revisão independente (G1/G2). Não é contrato ativado nem aceite: `G1_CONTRACT_DECISION` e `G2_SECURITY_REUSE` permanecem `PENDING` até Architecture/Coordination emitir verdict.

## 1. Inventário factual no HEAD (revalidado em `c3e090ac70`, R1)

| Superfície | Evidência real | Consequência |
|---|---|---|
| `delia-api/app/application/interaction/presentation.py` | `PRESENTATION_CONTRACT_VERSION="1"`; blocos `text`/`notice(role=owner_hint)`; bounds `_MAX_BLOCKS=8`, `_MAX_BLOCK_TEXT_CHARS=16384`; `message_kind` de vocab canônico derivado só de sinais estruturais, nunca de prosa; allowlist fechada de kinds | Nenhum emissor de Markdown existe; v2 estende este envelope |
| `SpecialistOutcome` (`domain/specialist_interop/model.py:124`) | `content_text: str` + **`structured: Mapping[str,object] \| None`** + `limitations` + `is_complete`; `epistemic_class` fixo `OBSERVATION` | **Fonte tipada de estrutura existe** — categoria A comprovada |
| `render_specialist_outcome` (`capability_provision/orchestration.py:~2117`) | Projeção determinística existente: sanitiza (`_sanitize_renderable` redige chaves sensíveis `_SENSITIVE_KEY_NAMES` + `_redact_text`), unwrap estrutural `_business_lines` (envelopes `data`/`result`/`payload`/`response` + `items`), projeção `_format_records`/`_format_structured` (indent determinístico, `MAX_RENDER_LIST_ITEMS`, depth ≤ 3), bounds `MAX_RENDER_CONTENT_CHARS=2000` (+ sufixo fixo de truncamento 32 chars → máx. 2032), limitação `result_truncated` declarada, resultado vazio verdadeiro (`Nenhum resultado encontrado.`), supressão de status genérico quando há payload de negócio | **Seam de projeção já existente** — o produtor governado de Markdown é uma EXTENSÃO desta projeção (ver §4), não um formatter paralelo. Probe de fidelidade: 16/16 checks (doc 86 §E) |
| `capability_attempt._success_attempt(render)` | Recebe `outcome` tipado + callable `render` injetável — seam de injeção já existe | Extensão não exige mudança de assinatura do attempt |
| `handle_interactive_turn.serialize_result` | Response = campos legados (`content`, `epistemic_class`, `limitations`, `grounding_status`, `provenance`, `confirmation_request`) + `presentation` via `compose_presentation` | Ponto único de serialização — v2 aditivo |
| `GovernedCapabilityProvenance.to_projection` | `source(s)` = `{source_id, source_system, observed_at}`; `specialist_id`, `provider_id`, `capability_group_id`, `protocol`, `remote_capability`, `action_id`, `correlation_id`, `is_complete` — **sem URLs, sem tokens, sem transporte** | Não é fonte de link navegável; provenance nunca carrega href |
| `WorkspaceEntityRef` (`interaction/workspace_context.py`) | `{entity_type, entity_id, source_system, label}` — **hint de entrada** não confiável (`grants_authorization()=False`), sem href | Não é fonte de link; é contexto inbound |
| `owner_hint` | Vocabulário literal do owner, URL-free por construção | Nunca vira link |
| Inventário de links legítimos (RW-G1-02) | **Não existe fonte tipada de destino navegável no caminho do turno** — nenhum RouteRef/EntityRef/LinkRef outbound; nenhum campo URL governado em `structured` por contrato hoje | `ARCHITECTURE_DECISION_REQUIRED=LINK_SOURCE_TYPED` mantido com pacote completo (§2.4, §6) |
| `plugins/delia/src/api/presentation.ts` | Parse-only; `version !== "1"` → `null` → fallback aos campos legados (`content`, `epistemic_class`, `limitations`); bounds espelhados; allowlist `text`/`notice` | Aderente à estratégia de coexistência v1↔v2 sem crash |
| `DeliaAssistantMessage.tsx` | `<p class="delia-turn__content">{displayContent}</p>` inerte; composição avatar→label→ActivityViewer→ConversationStatus→content→owner hint→GovernedConfirmation→EvidenceDetails→MessageActionBar; GovernedConfirmation agora distingue `pending_purpose` (§6.184) | Slot de conteúdo é o único ponto de integração; nada mais muda |
| `interactionClient.ts` | Comandos tipados `MESSAGE`/`APPLY_PREPARED`/`REJECT_PREPARED`; response traz `presentation` + campos legados | Contrato v2 é aditivo ao response, não toca request/command |
| `plugin-ui` `markdownDocumentModel.ts` + `MarkdownDocument.tsx` | `marked` GFM + `stripDangerousRichTextTags` + `dangerouslySetInnerHTML`; segmentos `code`/`mermaid`; heading anchors com `id` slug; GFM inclui tabelas | Document-grade — **não** conversacional: Mermaid, anchors globais, tabelas GFM e innerHTML estão todos fora do escopo B2 |
| `plugin-ui` `richTextHtmlFormat.ts` `stripDangerousRichTextTags` | **Denylist** (remove tags/attrs conhecidos); `isSafeUrl` permite `attachment:`, `blob:`, `mailto:`, relativos `#`/`/`/`./`/`../`; fallback regex não é prova | Política errada para saída de IA: B2 exige allowlist positiva |
| `plugin-ui` `richTextMarkdown.ts` `markdownToRichTextHtml` | `marked` GFM → HTML, com ilhas de HTML (u, span fontsize, text-align), attachment images | Semântica de colaboração/Chat — não reutilizável por DÉLIA |
| `messageThreadMarkdown.ts` | Menções/anexos/preview de thread | Mesma conclusão: específico do runtime de colaboração |
| Portal navigation (`AppHost`, `sameAppAnchorNavigation`) | MFE federado monta com props `{getAccessToken, basePath, pathname, search, alternateEntry, appRoutes, routeLabel, permissions, isSuperadmin}` — **não existe prop `navigate`**; Portal mantém listener global que converte clique em `<a>` same-origin → React Router `navigate()` **somente** se path dentro do `appBasePath` do app montado ou shell path (`/profile`, `/privacy`…); demais links same-origin seguem navegação nativa (reload) | Links internos funcionam via `<a href>` same-origin real; SPA intercept só cobre app próprio/shell — cross-app recai em reload completo (seguro, AuthZ intacta). Nenhuma API nova estritamente necessária; decisão registrada §6 |
| `DELPI_NAVIGATE` postMessage | Direção Portal→iframe embutido; não MFE→Portal | Não é mecanismo utilizável |

## 2. G1 — Proposta de contrato `presentation.v2`

### 2.1 Envelope

```jsonc
{
  "version": "2",
  "message_kind": "RESULT",                    // vocab canônico inalterado
  "semantic_status": "OBSERVATION" | null,     // inalterado
  "grounding_status": "GROUNDED" | "NON_GROUNDED",
  "blocks": [ /* §2.2 */ ],
  "allowed_interactions": ["reply"],           // inalterado
}
```

Campos `message_kind`, `semantic_status`, `grounding_status`, `allowed_interactions`, `confirmation_request`, `proposal_digest`, `preview_fingerprint`, `session_id`, `provenance`, `limitations`, `epistemic_class` são **inalterados** — v2 versiona somente a representação do conteúdo.

### 2.2 Blocos e discriminador de formato

```jsonc
// Bloco de conteúdo — format obrigatório em v2
{ "kind": "text",   "format": "plain",         "text": "…" }
{ "kind": "text",   "format": "markdown_safe", "text": "…" }
// Notice inalterado (owner hint nunca é Markdown)
{ "kind": "notice", "role": "owner_hint",      "text": "…" }
```

- `format` é **obrigatório** em todo bloco `text` de v2; ausência → bloco inválido (§2.5).
- `plain` = texto literal (semântica idêntica ao `text` de v1).
- `markdown_safe` = fonte Markdown submetida à política do subset §5. O sufixo `safe` é nome de contrato, não prova: a segurança vem do renderer + policy, não da etiqueta.
- `notice` permanece texto literal — owner hint nunca ganha markup.
- Ordem de blocos = ordem de renderização; máx. 8 blocos, `text` ≤ 16.384 chars por bloco (fonte Markdown, antes de render).
- Bloco vazio (`""`/`" "`) é omitido pelo produtor; se recebido, consumidor ignora.

### 2.3 Subset Markdown admitido (emissor)

O produtor só pode emitir os nós da política §5.1: parágrafos, `**`/`__`, `*`/`_`, `~~` (strikethrough informativo), `ul`/`ol`/`li` (nested ≤ 4), `>` blockquote, `` `code` `` inline, fenced code sem linguagem executável, `---`, headings `#`–`####` (clamp de renderização §7.3) e links `[t](url)` cuja `url` satisfaz §2.4. Emissor **nunca** produz: HTML inline, imagens `![]()`, tabelas GFM, autolink bare de scheme fora da política, task lists, footnotes, referências `[x][id]` por indireção.

### 2.4 Contrato de links (RW-G1-02 — pacote de decisão)

**Inventário concluído (factual):** no caminho do turno **não existe fonte tipada de destino navegável**. `GovernedCapabilityProvenance` exclui URLs por design; `WorkspaceEntityRef` é hint inbound não confiável sem href; `owner_hint` é vocabulário URL-free; `SourceRef` carrega `{source_id, source_system, observed_at}` — sem URL. Logo, emitir `[t](url)` a partir de prosa de modelo ou inferência está **proibido por ausência de fonte**, não apenas por política.

**Política de renderização (inalterada e completa — pronta para quando a fonte existir):**

- **Interno:** `href` começa com `/` — caminho absoluto same-origin do Portal. Emissível somente a partir de referência tipada admitida pelo backend (ver decisão abaixo). Sem `//host`, sem `?token=`, sem URL-encoding que resolva para scheme externo.
- **Externo:** `https:` apenas, hostname presente em fonte tipada admitida (não em prosa). `http:`, `mailto:`, `javascript:`, `data:`, `blob:`, `attachment:`, `file:`, relativos (`x`, `./`, `../`), hash-only `#` são **proibidos no emissor e derrubados no consumidor**.
- Renderização: externo → `target="_blank" rel="noopener noreferrer"`; interno → `<a href>` same-origin sem `target` (Portal intercepta quando legal; caso contrário navegação nativa — ambos com AuthZ live; cross-app cai em reload completo, seguro).
- Link inválido/não admitido **degrada para o texto do rótulo sem elemento `<a>`** — nunca navega, nunca alerta.
- Falha de autorização no destino é resolvida pelo destino (AuthZ live de sempre); presença do link nunca é permissão. Link expirado/obsoleto → destino responde seu próprio estado; a conversa não tenta revalidar.
- Companion Dock: mesmos `<a>` — navegação do Portal/shell, sem mecanismo paralelo.

**`LINK_SOURCE_TYPED = L1_APPROVED_CONDITIONAL` — decisão vinculante do Product Master (2026-10-16).** L2 (`LinkRef` novo) e L3 (deferir navegável) **não** foram aprovadas.

**Condições da L1 (todas obrigatórias por link emitido):**

1. Owner e fonte autoritativa identificáveis (o especialista/capability owner que publica o destino).
2. Campo e semântica **explicitamente publicados em contrato** pelo owner — presença ou nome de campo nunca bastam.
3. Permissão de divulgação do destino declarada pelo owner.
4. URL e esquema validados (`https:` externo absoluto ou `/` interno same-origin).
5. Política de navegação interna/externa aplicada pelo consumidor (§2.4 acima).
6. Core AuthZ e Domain API permanecem a autoridade final do destino.
7. Negativos exigidos: URL inventada → inerte; expirada/obsoleta → destino resolve seu estado; ausência de permissão → falha do destino, nunca da conversa.

**Proibição explícita:** campos genéricos `url`, `href`, `link` ou `*_url` **não** são promovidos a link navegável por nome ou por presença em `structured`. Sem contrato governado do owner publicando o destino, **nenhum link navegável é emitido** — os rótulos degradam a texto. Isso **não** revoga D1/D6/D7: a política e o renderer ficam prontos; a emissão depende de bindings reais.

**Inventário de contratos governados (R2-01 — resultado factual):**

| Candidato | Estado | Detalhe |
|---|---|---|
| `api-delpi` `mural_acessos` link `url` | CONTRATO REAL GOVERNADO | Owner: `app/domain/services/mural_acessos/link_url.py` — `normalize_link_url` valida scheme `http/https`+netloc+max len no write; semântica = destino de atalho publicado. **Porém** não foi provada nenhuma capability/specialist binding que carregue esse campo em `SpecialistOutcome.structured` até a conversa — binding `TO_INVENTORY` |
| `api-delpi` external capabilities `url` arg | PROIBIDO por design | `argument_validator.py` `_TRANSPORT_FORBIDDEN` inclui `url` — transporte nunca é argumento |
| `GovernedCapabilityProvenance`/`SourceRef`/`WorkspaceEntityRef`/`owner_hint` | NÃO SÃO FONTES | URL-free por construção (R1, doc 86 §3) |
| Demais Domain APIs/specialists com campos link tipados+semântica publicada | TO_INVENTORY | Nenhum binding concreto demonstrado neste inventário |

**Estado:** `LINK_L1_CONTRACT = SPECIFIED` / `LINK_L1_CAPABILITY_BINDINGS = TO_INVENTORY` — a política está fechada e armada; zero links navegáveis serão emitidos até que um binding owner→capability→`structured` seja provado com contrato publicado. G3 permanece bloqueado nesse ponto.

### 2.5 Erros de contrato e versões (R2-02 — decisão executável)

Quatro estados **distintos** — nunca fundidos:

| Caso | Classificação | Comportamento |
|---|---|---|
| `version` ausente/`"1"` **e** legado provadamente seguro (`content` string bounded presente) | `render_legacy` | Campos legados, inalterado |
| `version` desconhecida (`"3"`, `"2x"`, número, ausente-com-blocks estranhos) **e** legado provadamente seguro | `render_legacy` | Idem — versão desconhecida **nunca** é coagida a v2; legado é validado **antes** do fallback, não presumido |
| `version` desconhecida **e** legado inseguro (sem `content` string bounded) | `neutral_error` | Erro neutro fail-closed — nada fabricado |
| `version="2"` **estruturalmente inválido** (schema-reject: `format` ausente/desconhecido, kind de bloco desconhecido, prop extra, bounds excedidos) | `neutral_error` | Erro neutro fail-closed, **sem** downgrade silencioso, sem conteúdo parcial, sem log do payload |
| `version="2"` válido, `markdown_safe` falha no parse do renderer sobre **conteúdo já admitido** | `inert_text` | `block.text` renderizado como texto literal pre-wrap — conteúdo admitido nunca se perde |
| `version="2"` válido, `plain` | `render_v2` | Texto verbatim |
| `version="2"` válido, `markdown_safe` íntegro | `render_v2` | Renderer por policy §5.1 |
| `content`/`presentation` ausente onde exigido | `neutral_error` | Estado neutro; nada fabricado |

Regra de ouro (D9): falha **de forma** sobre conteúdo **admitido** → texto inerte; falha **de admissão** (schema/estrutura/segurança) → erro neutro fail-closed. Conteúdo adversarial nunca é apresentado como resposta legitimamente governada. Tabela executada como probe de política em `delia-api/tests/test_presentation_v2_proposal.py` (R2-04).

### 2.6 Campo legado `content` (compatibilidade)

O backend v2 continua populando `content` com o **texto legível plain** (renderização canônica §2.7 da própria resposta). Isso garante que clientes v1 (aba antiga aberta durante deploy) leiam conteúdo correto sem markup cru. `content` nunca carrega fonte Markdown.

### 2.7 Copy contract (D8)

`copiar resposta` produz texto plano **determinístico**, derivado do mesmo modelo de tokens (não do DOM, não da fonte Markdown):

- Parágrafos separados por `\n\n`; itens `- ` / `1.` com ordem preservada; blockquote com `> ` por linha.
- Headings viram a linha de texto pura; `**`/`~~` removidos; code inline/fenced copiado **verbatim**; links viram `texto (url)` apenas se href admitido, senão só o texto.
- IDs, códigos, quantidades, unidades e pontuação nunca alterados.
- Falha de clipboard (`navigator.clipboard` ausente/denegado) = falha honesta: sem feedback de "copiado", botão mantém estado neutro (comportamento já implementado).

### 2.8 Compatibilidade e rollout

| Backend | Frontend | Resultado |
|---|---|---|
| v1 | v1 | Atual — inalterado |
| v1 | v2 | `version "1"` parse normal — inalterado |
| v2 | v1 | `version "2"` → `null` → fallback `content` plain legível — correto |
| v2 | v2 | Markdown renderizado por policy |
| Sessão/aba antiga + deploy | misto | Sem histórico persistido; turnos novos seguem a matriz; sem migração |

**Ordem de deploy:** (1) MFE reader v2 tolerante primeiro; (2) backend emissor v2 depois; (3) rollback = backend volta a emitir só `format:"plain"`/v1 — custo zero, sem estado durável. Nenhuma feature flag inventada; se flag for necessária, inventariar mecanismo de config Core primeiro.

**Observabilidade (proposta):** contadores sanitizados `presentation.version`, `format`, `fallback_reason` (códigos fixos), correlation id existente; **jamais** fonte Markdown, hrefs ou payload nos logs.

### 2.9 JSON Schema — artefato canônico + validação mecânica (RW-G1-03)

O fragmento JSONC anterior foi promovido a artefato canônico versionado:

**`docs/12-roadmap-e-evolucao/delia/contracts/presentation-v2.proposal.schema.json`** (JSON Schema draft 2020-12 — proposta, não publicada no OpenAPI, não ativada em runtime).

Cobre: envelope completo (`version:"2"` const, `message_kind` enum canônico, `semantic_status` EpistemicClass|null, `grounding_status`, `allowed_interactions`, `blocks`), discriminadores de bloco (`text` exige `format`; `notice` exige `role:"owner_hint"`), campos obrigatórios/opcionais, semântica de null (`semantic_status` admite `null` explícito), limites (≤8 blocos, `text` ≤16.384 chars), e versões.

**Mudança deliberada vs. fragmento anterior:** `additionalProperties: false` em todos os níveis — o contrato v2 é **fechado** (fail-closed). Propriedades desconhecidas invalidam o payload inteiro → fallback ao campo legado `content` (§2.5), nunca coerção silenciosa. Extensibilidade se dá por versão nova, não por campos extras tolerados. (Decisão reversível no freeze se o Coordination preferir tolerância aditiva — registrado em §6.)

**Validação mecânica executada** (`python3 jsonschema 4.10.3`, Draft 2020-12, sobre `c3e090ac70`): **22/22 checks** — 4 positivos (plain, markdown_safe, text+notice, confirmation interactions) + 18 negativos (versão ausente/v1/desconhecida, `format` ausente/inválido, kind de bloco desconhecido, prop extra em bloco/envelope, blocos vazios/excedentes, texto oversize, `message_kind`/`interaction`/`notice.role` inválidos, payload não-objeto, bloco sem `text`). Probe reproduzível registrado no doc 86 §E.

## 3. Exemplos de response (extractos)

```jsonc
// RESULT com Markdown admitido (v2)
{ "user_turn_id":"t-u1","result_turn_id":"t-d2",
  "content":"A OP-2026-0481 tem 3 apontamentos:\n- solda 87%\n- montagem 40%\n\nLote L-8841 em quarentena.",
  "epistemic_class":"OBSERVATION","grounding_status":"GROUNDED",
  "presentation":{ "version":"2","message_kind":"RESULT",
    "semantic_status":"OBSERVATION","grounding_status":"GROUNDED",
    "blocks":[{"kind":"text","format":"markdown_safe",
      "text":"A OP-2026-0481 tem 3 apontamentos:\n\n- solda **87%**\n- montagem **40%**\n\nLote L-8841 em quarentena."}],
    "allowed_interactions":["reply"] } }

// CONFIRMATION_REQUIRED — confirmação nunca depende de formato
{ "content":"Preparei o bloqueio do lote L-8841.",
  "presentation":{ "version":"2","message_kind":"CONFIRMATION_REQUIRED",
    "semantic_status":null,"grounding_status":"NON_GROUNDED",
    "blocks":[{"kind":"text","format":"plain","text":"Preparei o bloqueio do lote L-8841."}],
    "allowed_interactions":["reply","confirm","reject"] },
  "confirmation_request":{"session_id":"…","proposal_digest":"…","preview_fingerprint":"…"} }
```

## 4. Produtor governado (D3/D5) — RW-G1-01 corrigido

### 4.1 Inventário do pipeline real

```text
SpecialistOutcome{ content_text, structured, limitations, is_complete }
  → render_specialist_outcome(outcome)          # projeção determinística existente
       _sanitize_renderable → _business_lines → _format_records/_format_structured
  → GovernedCapabilityAttempt.content (str) + limitations   # render injetável em _success_attempt
  → InteractiveTurnResult.content + message_kind/owner_hint/provenance/confirmation/grounding
  → serialize_result → content (legado) + presentation v1 (compose_presentation)
```

### 4.2 Categorias de entrada (formalizadas)

| Categoria | Fonte real | Regra v2 |
|---|---|---|
| **A — estruturado tipado comprovado** | `SpecialistOutcome.structured` (Mapping admitido na fronteira de interop; sanitizado por `_sanitize_renderable`) | **Única fonte para blocos `markdown_safe` com estrutura** — listas/registros mapeados deterministicamente (mesma semântica de `_format_records`: item→linha, chave→rótulo, sem renomeação semântica, sem valores computados) |
| **B — texto pré-estruturado pela fonte** | `content_text` do owner (quebras/ênfases autoradas pela fonte) | Preservado verbatim; emitido como `plain` — estrutura textual pertence à fonte, nunca é reinterpretada como Markdown sem declaração tipada |
| **C — prosa sem estrutura confiável** | Respostas de modelo, status genéricos, textos sem `structured` | `plain` inerte — proibido inferir listas/negritos/títulos de prosa |

### 4.3 Contract Gate do produtor

- **Responsabilidade:** projetar dados admitidos em blocos v2; nunca acrescentar fatos/URLs/instruções.
- **Owner:** `delia-api` `application/capability_provision` (projeção) + `application/interaction` (envelope).
- **Seam:** **EXTEND** `render_specialist_outcome` — o mesmo projetor determinístico emite, além do `str` canônico (inalterado para v1/content), a projeção tipada de blocos quando `structured` admite forma reconhecida. `compose_presentation` serializa fail-closed. Nenhum `GovernedResponseFormatter` paralelo — a revisão apontou e o inventário provou o equivalente existente.
- **Inputs:** `SpecialistOutcome` tipado (nunca payload wire cru — já sanitizado), limitations do attempt.
- **Outputs:** `blocks[]` conforme schema §2.9 + `content` plain canônico derivado da **mesma** projeção (display e cópia nunca divergem).
- **Constraints:** bounds existentes (`MAX_RENDER_CONTENT_CHARS=2000`+sufixo fixo, `MAX_RENDER_LIST_ITEMS`, depth≤3, `_MAX_BLOCKS=8`, bloco ≤16.384); ordem e valores verbatim; falha de projeção → `plain`.
- **Source authority:** o owner especialista (categoria A/B) ou o próprio modelo para prosa não-factual (categoria C) — nunca o frontend.
- **Erros/observabilidade:** contadores sanitizados `presentation.version/format/fallback_reason`; nunca conteúdo nem href em log.
- **Fidelity:** probe executado — 16/16 checks (IDs/quantidades/unidades/ordem verbatim; texto literal com `**`/`[x](y)` inerte; `access_token`/`client_secret` redigidos; resultado vazio verdadeiro; status genérico suprimido; truncamento bounded+declarado). **Residual documentado:** chave `token` bare não consta de `_SENSITIVE_KEY_NAMES` — valor passa sem redação hoje (fato do runtime atual; decisão de ampliar o conjunto pertence a outro slice de segurança).
- **Modelo-assistido (LLM sugerindo estrutura):** fora da proposta — `DECISION_OPTION_DEFERRED`.

## 5. G2 — Reuse & Security Decision Report

### 5.1 Política positiva de nós (proposta de allowlist)

Tokens `marked` admitidos e seu mapeamento (renderer React, sem HTML):

| Token | Render | Observação |
|---|---|---|
| `paragraph`, `text`, `escape` | `p`/texto | — |
| `strong`, `em`, `del` | `strong`/`em`/`del` | — |
| `list`+`list_item` | `ul`/`ol`/`li` | profundidade máx. 4; demais → texto |
| `blockquote` | `blockquote` | aninhado ≤ 2 |
| `codespan`, `code` | `code`/`pre>code` | inerte; fence sem lang executável; lang exibido só como label de texto |
| `hr` | `hr` | — |
| `heading` | `h4`–`h6` clamped | nunca h1/h2 (hierarquia da conversa); sem anchors/`id` |
| `link` | `a` **somente** se `href` passa na policy §2.4 | senão: texto do rótulo |
| `br`, `space` | `\n`/ignorado | — |
| **todos os demais** (`html`, `image`, `table`, `def`, `checkbox`,…) | **derrubado → texto literal do token** ou omitido conforme tipo | nunca HTML |

### 5.2 Matriz de reutilização (RW-G2-01 — corrigida, evidência real)

Vocabulário normativo: `REUSE` | `EXTEND` | `NEW`; candidatos não escolhidos registram `NOT_SELECTED` + justificativa.

**Inventário real (verificado em `c3e090ac70`):**

| CANDIDATE | EXISTING_EQUIVALENT | REUSE_DECISION | JUSTIFICATIVA |
|---|---|---|---|
| `marked` ^18.0.9 (dep. plugin-ui) — `marked.lexer` | YES | **REUSE** | Probe adversarial executado (doc 86 §E): lexer emite tipos discretos — `html`/`image`/`table`/`link`(href cru, incl. `javascript:`)/`code`/`checkbox` — permitindo negação-por-construção no renderer |
| `MarkdownDocumentView`+`buildMarkdownDocumentModel` (`components/markdown/`) | YES (documental) | NOT_SELECTED | Saída = **HTML sanitizado via `dangerouslySetInnerHTML`** (linha 176); escopo documental (GFM tables, Mermaid via `DiagramMermaidPreview`, anchors `id` globais). Modelo de segurança pós-parse incompatível com token→React |
| `markdownToRichTextHtml` (`rich-text/richTextMarkdown.ts`) | YES | NOT_SELECTED | `marked.parse` → **string HTML** + DOMParser (`enhanceAttachmentImagesInHtml`); consumidores renderizam via `dangerouslySetInnerHTML` — produzir React exigiria substituir o modelo de saída, não estendê-lo |
| `messageThreadMarkdown` (`collaboration/`) | YES | NOT_SELECTED | Compõe `markdownToRichTextHtml`+`stripDangerousRichTextTags`+menções/attachment:uuid; semântica de rooms; `markdownToPlainPreview` é preview por regex — adequado ao seu escopo, não a cópia canônica DÉLIA |
| `stripDangerousRichTextTags` (`rich-text/richTextHtmlFormat.ts:115`) | YES (sanitizer) | NOT_SELECTED para DÉLIA | Denylist DOMParser parse→mutate→serialize; permite `attachment:`/`blob:`/`mailto:`/relativos; política alvo B2 é allowlist positiva sem HTML intermediário |
| `ChatMermaidBlock` (minha-delpi-chat) | YES | NOT_SELECTED | Mermaid fora do escopo B2; runtime Chat não é dependência |
| `markdownImageTokens`/`richTextInlineImage` | YES (editor) | NOT_SELECTED | Mecânica de imagem/attachment — `image` fora do allowlist B2 |
| Turndown/strip p/ copy | YES | NOT_SELECTED | Copy deriva do modelo de tokens admitido (§2.7), nunca de reparse HTML→texto |
| **`ConversationMarkdown` (plugin-ui) — novo** | NO | **NEW** | token→React, allowlist positiva, zero `dangerouslySetInnerHTML`/DOMParser; emite também a serialização plain-text do copy da mesma árvore |

**Opção B — EXTEND analisada e rejeitada com evidência:** todos os renderers existentes produzem **string HTML** consumida por `dangerouslySetInnerHTML`. Estender qualquer um para emitir React exigiria trocar seu modelo de saída (quebra consumidores: `MessageThread` bodyMode=markdown, previews Docx/artigos, editor) — o custo arquitetural é duplo: duas máquinas de render no mesmo util ou regressão nos consumers. `EXTEND` se aplica corretamente ao **produtor** (§4.3: extensão de `render_specialist_outcome`, seam já injetável) e ao **envelope** (v2 aditivo sobre `presentation.py`).

**`NEW` justificada (Abstraction Gate):** consumer real único (DÉLIA), owner legítimo `plugin-ui` (renderers/read-models do kit — mesmo dono dos renderers existentes), boundary claro (read-only conversacional), REUSE/EXTEND provados insuficientes acima, bundle mínimo (`marked.lexer` + tipos; `marked` já é dep do kit).

### 5.3 Threat model → mitigação por construção

| Ameaça | Mitigação no design proposto |
|---|---|
| XSS / HTML inline | Sem parse HTML: token `html`/`tag` do lexer vira texto; nenhum `dangerouslySetInnerHTML` no caminho |
| `dangerouslySetInnerHTML` | Ausente por construção (render = elementos React) |
| Event handlers (`on*`) | Impossível — atributos não são materializados; renderer só cria `href/target/rel` |
| `script`/`iframe`/`object`/`embed`/`form` | Tokens nunca geram essas tags |
| SVG/MathML | Fora do allowlist de elementos |
| `javascript:`/`data:`/`blob:`/`attachment:`/`file:` | Policy de link §2.4 derruba href → rótulo vira texto |
| URL obfuscation/encoding | href validado por `new URL` + comparação de scheme/hostname; unicode confusável não passa a policy de host |
| Nav relativa/hash fora do contrato | Somente `/…` interno ou `https:` verificado; `#`, `//`, `./`, `../` rejeitados |
| DOM clobbering | Sem `id`/`name` gerados (anchors de heading desligados) |
| Links falsificados | Emissor só escreve href de RouteRef/EntityRef/verificado; consumidor revalida — dois pontos de controle |
| Imagens/fetch remoto | `image` fora do allowlist — zero fetch por render |
| Markdown aninhado profundo | Profundidade limitada (listas ≤4, quote ≤2); recursão com depth cap |
| Payload gigante / DoS | Bounds: 16.384 chars/bloco, 8 blocos, ≤ 64 nós renderizados, ≤ 16 links/bloco; excedente → degrade/texto |
| Mermaid/extras | Não chegam ao renderer; `code lang=mermaid` renderiza como code inerte |
| Provider/modelo introduzindo ações | Formato nunca cria `allowed_interactions`; markup é dado |
| Dados sensíveis em logs | Somente códigos de motivo/versão — nunca conteúdo |

**Evidência de probe (executada, doc 86 §E):** `marked.lexer` verificado contra 22 casos adversariais — `html` (inline e bloco `<script>`), `image`, `link` com `javascript:`/`data:`/relativo/hash/ofuscado `JaVaScRiPt:`/encoded `java%73cript:`, `table` GFM, `code` mermaid, lista aninhada >4, `checkbox`, autolink `https:` — todos chegam como tokens discretos e distinguíveis; a política do renderer decide cada tipo antes de materializar qualquer elemento. Um probe de parser **não** prova segurança de um renderer ainda não implementado — prova que o modelo token→allowlist é exequível sobre o lexer homologado.

**Gap honesto (corrigido em §2.4):** não existe fonte tipada de destino navegável no caminho do turno. A política de links está completa e pronta; a emissão depende da decisão `LINK_SOURCE_TYPED` (§2.4/§6) — escopo de links **não** foi reduzido silenciosamente.

**Residual de segurança (R2-03 — brief bounded preparado):** `_SENSITIVE_KEY_NAMES` cobre `access_token`/`refresh_token`/`session_token`/`bearer_token`/`candidate_token`/`client_secret`/… mas **não** a chave canonical `token` — probe provou valor `token:` renderizado sem redação (`test_render_specialist_outcome_fidelity.py::test_bare_token_key_is_redacted` = `xfail(strict=True)`, RED probe versionado).

**Correção proposta (não aplicada — task não autoriza runtime):** adicionar `"token"` a `_SENSITIVE_KEY_NAMES` em `delia-api/app/application/capability_provision/orchestration.py` (~L1861) — diff de 1 linha no owner legítimo (`capability_provision`). Trade-off: um campo de negócio literalmente nomeado `token` seria redigido — aceitável e fail-closed (valor ambíguo com nome credencial não deve vazar; semântica de negócio preservada pela chave). A correção exige **autorização bounded específica** (altera runtime de produção); brief entregue nesta task via doc 87 §R2-03. Até lá, **a projeção de `structured` não deve alimentar `markdown_safe`** — categoria A fica restrita a shapes sem chaves de risco, ou `markdown_safe` permanece emissor-vazio.

### 5.4 Critérios de a11y/apresentação (a implementar, não agora)

- Headings clamped `h4`+ sob `role="log"` da timeline; sem `aria-live` novo.
- Listas reais `ul/ol/li`; `code` com `font-mono` do kit; blockquote discreto.
- Links: foco visível, `rel` nos externos, texto descritivo (rótulo nunca só "clique aqui" — regra de emissor).
- Tema claro/escuro por tokens existentes; 320/420px e zoom 200% sem overflow (`overflow-wrap` já cobre); reduced-motion mantido.
- `MessageActionBar`/copy keyboard-friendly inalterado.

## 6. Decisões, drifts e pendências (Decision/Drift Register)

| Item | Estado | Decisão requerida |
|---|---|---|
| `PORTAL_MFE_NAVIGATE_PROP` | NOT_PRESENT | Não bloqueante: `<a href>` same-origin já navega (SPA intercept dentro do app/shell; reload fora). Se produto exigir SPA-nav cross-app, abrir bounded slice Portal; **sem** inventar API agora |
| `LINK_SOURCE_TYPED` | **L1_APPROVED_CONDITIONAL** (Product Master, 2026-10-16) | Condições e inventário em §2.4. `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY` — zero links navegáveis até binding owner→capability→`structured` provado. G3 segue bloqueado neste ponto |
| `TOKEN_KEY_EXPOSURE` | RED_PROBE_RECORDED, fix não autorizado | R2-03: `"token"` deve entrar em `_SENSITIVE_KEY_NAMES` — brief bounded pendente de autorização (doc 87 §R2-03). Projeção `structured`→`markdown_safe` bloqueada até resolução ou isolamento provado |
| `GOVERNED_FORMATTER` | RESOLVIDO — não é componente novo | RW-G1-01: o seam é `render_specialist_outcome` existente; proposta = **EXTEND** a projeção para emitir blocos tipados (§4). Freeze confirma nome/assinatura final |
| `SCHEMA_ADDITIONAL_PROPERTIES` | DECIDIDO nesta proposta | v2 fechado (`additionalProperties:false`, fail-closed → fallback legado). Reversível no freeze se preferirem tolerância aditiva |
| `MODEL_ASSISTED_FORMATTING` | DEFERRED | Fora do slice inicial; requer prova de fidelidade |
| `CONVERSATION_MARKDOWN` (plugin-ui token→React) | NEW componente proposto | Aprovação G2 de owner/equivalence |
| Spec 82 TRACEABILITY_GAP tabelas/gráficos | OPEN, inalterado | B2 não cobre C/D/E |
| Live-region `role=status`/`alert` do ActivityViewer dentro do turno | kit-owned, pré-existente | Sem ação em B2 |
| Drift entre spec 83 baseline e HEAD | Nenhum encontrado nos arquivos inspecionados | — |

## 7. Matriz de aceite G1/G2 (CP-333)

| Gate | RQ/AC cobertos | Evidência | Status |
|---|---|---|---|
| G1 envelope/discriminator | B2-RQ01,02,05; AC01,08,23 | §2.1–2.2, §2.5 + schema validado 22/22 | `CANDIDATE_REWORKED` |
| G1 producer | B2-RQ03,19,20; AC18,21,22,24 | §4 seam existente + fidelity probe 16/16 | `CANDIDATE_REWORKED` |
| G1 links | B2-RQ14,21; AC25,26 | §2.4 pacote completo + decisão pendente | `CANDIDATE_REWORKED_WITH_DECISION` |
| G1 copy | B2-RQ12,22; AC14,27 | §2.7 | `CANDIDATE_REWORKED` |
| G1 fallback/compat | B2-RQ05,09,18,23,25; AC08,17,28,30 | §2.5–2.8 + schema negatives | `CANDIDATE_REWORKED` |
| G1 bounds | B2-RQ13; AC07,19 | §2.2, §5.3 + schema limits validados | `CANDIDATE_REWORKED` |
| G2 reuse | B2-RQ10,17 | §5.2 REUSE/EXTEND/NEW comparados + probe lexer | `CANDIDATE_REWORKED` |
| G2 threat model | B2-RQ04; AC05,06,12 | §5.3 + probe adversarial 22 casos | `CANDIDATE_REWORKED` |
| G2 a11y criteria | B2-RQ08,11; AC03,15,16 | §5.4 | `CANDIDATE_REWORKED` |
| Evidence separation | B2-RQ06,24; AC11,29 | §2 (inalterados), §5 | `CANDIDATE_REWORKED` |
| No authority drift | B2-RQ07,15 | §2.1, §2.8 obs | `CANDIDATE_REWORKED` |
| Conformance/outcome | B2-RQ16; AC02,04,09,10,13,20 | testes de runtime — slice futuro | `TEST_NOT_RUN` (probes executados não são testes de runtime) |

## 8. Implementation readiness

- **I1** (backend): extensão da projeção `render_specialist_outcome` (blocos tipados) + serializer v2 em `compose_presentation` + `content` plain canônico + OpenAPI v2 (não ativado). Depende de: freeze de §2 e decisão de links §6.
- **I2** (plugin-ui): `ConversationMarkdown` token→React + link policy + copy serializer. Depende de: aprovação G2 §5.
- **I3** (delia MFE): `parsePresentation` aceitar v2 + slot de conteúdo em `DeliaAssistantMessage` + fallback. Depende de: I1/I2.
- **Q1**: matriz adversarial AC01–30 + browser QA full/dock/temas/zoom/teclado.
- **R1**: revisão independente (ACCEPT/REWORK/DRIFT).

Ordem física I1↔I2 pode inverter; contrato congelado antes de ambos.

## 9. Handoff para revisão independente

- Revisar §2 (schema/semântica/compat — artefato `contracts/presentation-v2.proposal.schema.json`, validado 22/22), §4 (produtor = EXTEND `render_specialist_outcome`) e §5 (allowlist/threat/reuse corrigidos).
- Decidir `LINK_SOURCE_TYPED` (§2.4/§6) — recomendação L1 (typed link field em `structured`); L3 só com aprovação explícita do Product Master.
- Relatório de rework R1 com evidências completas: doc 86.
- Se aprovado: próxima task bounded = `DELIA-UX-CONVERSATION-MARKDOWN-B2-G3-BRIEF` (brief de implementação por slice, sem código).
- Estados que este documento **não** altera: `G1_CONTRACT_DECISION=PENDING`, `G2_SECURITY_REUSE=PENDING`, `G3/G4=PENDING`, `RUNTIME_IMPLEMENTATION=BLOCKED_UNTIL_GATES`, `C_D_E_TRACEABILITY_GAP=OPEN`, `CP-333=PLANNED`, `PHASE_PROGRESSION=NONE`.
