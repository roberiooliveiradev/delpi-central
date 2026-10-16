# 84 — Proposta `presentation.v2` e Reuse/Security Review de Markdown (G1/G2)

**Status:** `G1_CONTRACT_PROPOSAL=CANDIDATE_FOR_REVIEW / G2_REUSE_SECURITY=CANDIDATE_FOR_REVIEW / RUNTIME_NOT_AUTHORIZED`

**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-01`
**BASE_HEAD:** `bbdd3a4f4de09097e7f80aef426e9366de601b8c`
**CP:** `CP-333` (matriz 25 — `PLANNED`, não PASS)
**Tipo:** CONTRACT-FIRST / DOCUMENTATION ONLY — nenhum diff de runtime nesta task.

> B2 aqui = Markdown conversacional da spec 82/83. **Não** confundir com `C3-STAGE-02-B2` (governança de execução PREPARE/ACT, ledger §6.183/§6.184). Nada se transfere entre as trilhas.

Este documento é a **proposta** submetida à revisão independente (G1/G2). Não é contrato ativado nem aceite: `G1_CONTRACT_DECISION` e `G2_SECURITY_REUSE` permanecem `PENDING` até Architecture/Coordination emitir verdict.

## 1. Inventário factual no HEAD (revalidado)

| Superfície | Evidência real (`bbdd3a4f4d`) | Consequência |
|---|---|---|
| `delia-api/app/application/interaction/presentation.py` | `PRESENTATION_CONTRACT_VERSION="1"`; blocos `text`/`notice(role=owner_hint)`; bounds `_MAX_BLOCKS=8`, `_MAX_BLOCK_TEXT_CHARS=16384`; `message_kind` de vocab canônico derivado só de sinais estruturais, nunca de prosa; allowlist fechada de kinds | Nenhum emissor de Markdown existe |
| `delia-api` producer de `result.content` | `InteractiveTurnResult` já governado; conteúdo vem de dados admitidos — não há formatter de estrutura | Produtor de Markdown é componente **novo** na boundary DÉLIA (`TO_INVENTORY` → proposta §4) |
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

### 2.4 Contrato de links

```jsonc
// o produtor só emite href nestas formas; origem é campo governed
{ "kind": "text", "format": "markdown_safe",
  "text": "Veja [o pedido](/apps/my-requests).\nFonte: [portal do fornecedor](https://fornecedor.example/doc/1)" }
```

- **Interno:** `href` começa com `/` — caminho absoluto same-origin do Portal. Só pode ser emitido quando o valor vem de RouteRef/EntityRef governed (registro/rota que o backend conhece), nunca de URL gerada por modelo. Sem `//host`, sem `?token=`, sem URL-encoding que resolva para scheme externo.
- **Externo:** `https:` apenas, hostname presente na lista de origem verificável do turno (provenance/sources admitidas). `http:`, `mailto:`, `javascript:`, `data:`, `blob:`, `attachment:`, `file:`, relativos (`x`, `./`, `../`), hash-only `#` são **proibidos no emissor e derrubados no consumidor**.
- Renderização: externo → `target="_blank" rel="noopener noreferrer"`; interno → `<a href>` same-origin sem `target` (Portal intercepta quando legal; caso contrário navegação nativa — ambos com AuthZ live).
- Link inválido/não admitido **degrada para o texto do rótulo sem elemento `<a>`** — nunca navega, nunca alerta.
- AuthZ: clicar num link nunca é permissão; o destino resolve com `/me/apps` + Domain authority de sempre.

### 2.5 Erros de contrato e versões

| Caso | Comportamento |
|---|---|
| `version` ausente/`"1"` | Parse v1 atual, inalterado |
| `version` desconhecida (`"3"`, `"2x"`…) | `parsePresentation → null` → campos legados (texto inerte) |
| `version="2"` com `format` ausente/desconhecido num bloco `text` | **Bloco descartado** (não rebaixado silenciosamente); se nenhum bloco restar → erro neutro de apresentação |
| `markdown_safe` malformado (parser falha em conteúdo admitido) | Fallback: renderiza `block.text` como texto inerte (pre-wrap) — conteúdo já admitido nunca se perde |
| Payload estruturalmente inválido/não aderente ao schema | Erro neutro `ConversationError`-like/turno neutro, **sem** exibir conteúdo parcial, sem log do payload |
| `content` ausente junto a `presentation` v2 | Estado neutro; nada fabricado |

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

### 2.9 JSON Schema (proposta — ainda não publicada no OpenAPI)

```jsonc
"DeliaPresentationV2": {
  "type": "object",
  "required": ["version","message_kind","semantic_status","grounding_status","blocks","allowed_interactions"],
  "properties": {
    "version":   { "const": "2" },
    "message_kind": { "$ref": "#/components/schemas/DeliaMessageKind" },
    "semantic_status": { "type": ["string","null"] },
    "grounding_status": { "enum": ["GROUNDED","NON_GROUNDED"] },
    "blocks": {
      "type": "array", "maxItems": 8,
      "items": { "oneOf": [
        { "type":"object","required":["kind","format","text"],
          "properties":{
            "kind":{"const":"text"},
            "format":{"enum":["plain","markdown_safe"]},
            "text":{"type":"string","maxLength":16384}}},
        { "type":"object","required":["kind","role","text"],
          "properties":{
            "kind":{"const":"notice"},
            "role":{"const":"owner_hint"},
            "text":{"type":"string","maxLength":16384}}}
      ], "additionalProperties": true }
    },
    "allowed_interactions": { "type":"array", "items":{"enum":["reply","confirm","reject"]} }
  },
  "additionalProperties": true
}
```

`additionalProperties: true` nos níveis de objeto preserva extensibilidade aditiva (mesmo princípio de v1); consumidores ignoram campos desconhecidos.

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

## 4. Produtor governado (D3/D5) — proposta

```text
InteractiveTurnResult (já governado)
  → GovernedResponseFormatter (NOVO, application/interaction)
      entrada: campos admitidos do result (content estruturável,
               provenance.sources, owner_hint)
      saída: blocks[] v2 com format decidido deterministicamente
  → compose_presentation v2 (serializer tipado, fail-closed)
  → response
```

- **Decisão de formato é determinística** no formatter: coleção de registros/etapas presentes nos dados admitidos → lista; saudação/resposta curta → `plain`; código técnico presente → fenced code. Heurística vive na boundary DÉLIA, nunca no frontend, nunca no modelo solto.
- Formatação por modelo assistido (LLM sugerindo estrutura) fica **fora da proposta inicial**: exige prova de fidelidade contra dados admitidos; se desejado depois, novo bounded slice com validação fail-closed (todo token de conteúdo deve rastrear a campo governado). Registrado como `DECISION_OPTION_DEFERRED`.
- Se os dados admitidos não carregam estrutura (content é prosa única), formatter emite `plain` — v2 sem falsos Markdown.
- O formatter nunca acrescenta fatos, URLs, fontes ou instruções: sua única licença é **estruturar** texto já admitido. Falha → `plain`.

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

### 5.2 Matriz de reutilização

| CANDIDATE | EXISTING_EQUIVALENT | REUSE_DECISION | JUSTIFICATIVA |
|---|---|---|---|
| `MarkdownDocumentView`+`buildMarkdownDocumentModel` | YES (documental) | **DO_NOT_REUSE** | innerHTML+denylist, Mermaid, anchors globais, GFM tables — tudo fora do escopo conversacional; adaptar custa mais que compor |
| `stripDangerousRichTextTags` | YES (sanitizer genérico) | **DO_NOT_REUSE para DÉLIA** | denylist; permite `attachment:`/`blob:`/relativos/`mailto:`; fallback regex sem prova; política alvo é allowlist positiva. Não se copia nem se estende indevidamente |
| `markdownToRichTextHtml` / `messageThreadMarkdown` | YES (colaboração) | **DO_NOT_REUSE** | semântica Chat (menções/anexos/HTML islands); regra explícita: sem dependência do runtime Chat |
| `marked` (dependência) | YES | **REUSE** (lexer/tokenizer) | parser já homologado no kit; usa-se só `marked.lexer` + tipos — o `parse→HTML` não é usado |
| **Novo `ConversationMarkdown` (plugin-ui)** | NO | **NEW (proposta)** | token→React com allowlist positiva; zero `dangerouslySetInnerHTML`, zero DOMParser; gera também a serialização plain-text do copy (§2.7) a partir da mesma árvore |
| `stripDown`/turndown p/ copy | YES (TurndownService) | **DO_NOT_REUSE** | copy vem do modelo de tokens, não de reparse HTML→texto |

`NEW` justificada: Abstraction Gate — consumer real (DÉLIA), owner legítimo `plugin-ui` (renderers/read-models do kit), boundary claro (conversational read-only), REUSE/EXTEND provados insuficientes acima, bundle mínimo (só `marked.lexer` — `marked` já é dep do kit; tree-shaking remove mermaid/turndown do caminho).

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

**Gap honesto:** a política de link depende de `RouteRef/EntityRef` governados existirem no producer path — hoje `result.content` é texto e links navegáveis não têm fonte tipada. Opções registradas: (a) B2 inicial emite `markdown_safe` **sem links** (links degradam a texto — D7 implementado quando houver fonte tipada); (b) inventariar/governar RouteRef primeiro. Recomendação **(a)** — reduz a superfície do primeiro slice. `DECISION_PENDING` para Architecture Coordination.

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
| `LINK_SOURCE_TYPED` (RouteRef/EntityRef no turn result) | TO_INVENTORY | Decidir: B2 inicial sem links navegáveis (recomendado) vs governar refs primeiro |
| `GOVERNED_FORMATTER` | NEW componente proposto (backend DÉLIA) | Aprovar nome/boundary no freeze do contrato |
| `MODEL_ASSISTED_FORMATTING` | DEFERRED | Fora do slice inicial; requer prova de fidelidade |
| `CONVERSATION_MARKDOWN` (plugin-ui token→React) | NEW componente proposto | Aprovação G2 de owner/equivalence |
| Spec 82 TRACEABILITY_GAP tabelas/gráficos | OPEN, inalterado | B2 não cobre C/D/E |
| Live-region `role=status`/`alert` do ActivityViewer dentro do turno | kit-owned, pré-existente | Sem ação em B2 |
| Drift entre spec 83 baseline e HEAD | Nenhum encontrado nos arquivos inspecionados | — |

## 7. Matriz de aceite G1/G2 (CP-333)

| Gate | RQ/AC cobertos | Evidência nesta doc | Status |
|---|---|---|---|
| G1 envelope/discriminator | B2-RQ01,02,05; AC01,08,23 | §2.1–2.2, §2.5 | `CANDIDATE_DOCUMENTED` |
| G1 producer | B2-RQ03,19,20; AC18,21,22,24 | §4 | `CANDIDATE_DOCUMENTED` |
| G1 links | B2-RQ14,21; AC25,26 | §2.4 (+pendência §6) | `CANDIDATE_DOCUMENTED_WITH_DECISION` |
| G1 copy | B2-RQ12,22; AC14,27 | §2.7 | `CANDIDATE_DOCUMENTED` |
| G1 fallback/compat | B2-RQ05,09,18,23,25; AC08,17,28,30 | §2.5–2.8 | `CANDIDATE_DOCUMENTED` |
| G1 bounds | B2-RQ13; AC07,19 | §2.2, §5.3 | `CANDIDATE_DOCUMENTED` |
| G2 reuse | B2-RQ10,17 | §5.2 | `CANDIDATE_DOCUMENTED` |
| G2 threat model | B2-RQ04; AC05,06,12 | §5.3 | `CANDIDATE_DOCUMENTED` |
| G2 a11y criteria | B2-RQ08,11; AC03,15,16 | §5.4 | `CANDIDATE_DOCUMENTED` |
| Evidence separation | B2-RQ06,24; AC11,29 | §2 (inalterados), §5 | `CANDIDATE_DOCUMENTED` |
| No authority drift | B2-RQ07,15 | §2.1, §2.8 obs | `CANDIDATE_DOCUMENTED` |
| Conformance/outcome | B2-RQ16; AC02,04,09,10,13,20 | testes — slice futuro | `TEST_NOT_RUN` (nenhum runtime teste nesta task) |

## 8. Implementation readiness

- **I1** (backend): `GOVERNED_FORMATTER` + serializer v2 + `content` plain canônico + OpenAPI v2 (não ativado). Depende de: freeze de §2 e decisão de links §6.
- **I2** (plugin-ui): `ConversationMarkdown` token→React + link policy + copy serializer. Depende de: aprovação G2 §5.
- **I3** (delia MFE): `parsePresentation` aceitar v2 + slot de conteúdo em `DeliaAssistantMessage` + fallback. Depende de: I1/I2.
- **Q1**: matriz adversarial AC01–30 + browser QA full/dock/temas/zoom/teclado.
- **R1**: revisão independente (ACCEPT/REWORK/DRIFT).

Ordem física I1↔I2 pode inverter; contrato congelado antes de ambos.

## 9. Handoff para revisão independente

- Revisar §2 (schema/semântica/compat) e §5 (allowlist/threat/reuse) como candidatos.
- Decidir `LINK_SOURCE_TYPED` (§6) — recomendação: B2 sem links navegáveis até fonte tipada existir.
- Se aprovado: próxima task bounded = `DELIA-UX-CONVERSATION-MARKDOWN-B2-G3-BRIEF` (brief de implementação por slice, sem código).
- Estados que este documento **não** altera: `G1_CONTRACT_DECISION=PENDING`, `G2_SECURITY_REUSE=PENDING`, `G3/G4=PENDING`, `RUNTIME_IMPLEMENTATION=BLOCKED_UNTIL_GATES`, `C_D_E_TRACEABILITY_GAP=OPEN`, `CP-333=PLANNED`, `PHASE_PROGRESSION=NONE`.
