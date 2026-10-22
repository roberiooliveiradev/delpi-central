# 83 — DÉLIA: Plano B2 de Markdown Seguro em Respostas Conversacionais

**Status:** `PRODUCT_DECISIONS_D1_D12_APPROVED / CP-333_MAPPED / BOUNDED_AUTHORIZATION_CONDITIONAL / G1_G2_INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL / RUNTIME_B2_NOT_AUTHORIZED`
**Data:** 2026-10-16  
**Task documental:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-PLANNING-01`  
**Parent:** [82 — Conversation Rich Content & Structured Presentation](./82-conversation-rich-content-and-structured-presentation-specification.md)  
**Produto:** DÉLIA standalone; não é Minha DELPI Chat, nem compartilha seu runtime/tabelas/agents/services.  
**Snapshot de descoberta:** branch `main`, HEAD reancorado em `b0b4f8c028f706d2a4bd47e70690ea07badea089`, com rechecagem do HEAD antes da publicação. O HEAD de implementação deve ser revalidado.  
**Natureza:** planejamento contratual, de segurança, UX, implementação e testes; as decisões D7–D12 vinculam o escopo de produto e D12 autoriza somente a trilha bounded **condicionada** a gates técnicos. `CP-333` passa a constar da matriz 25; nenhum código, schema de runtime, deploy ou fase é alterado por este documento.

## 0. Resumo executivo e decisão proposta

Entregar B2 como **renderização opcional e explicitamente contratada de Markdown seguro no corpo das respostas da DÉLIA**, sem reinterpretar as mensagens literais existentes. O B2 é independente de gráficos, tabelas estruturadas, métricas e HTML arbitrário. Reutilizar, quando aprovado por inventário e Security Review, os primitives e mecanismos existentes em `@delpi/plugin-ui`. A DÉLIA mantém a composição local de `DeliaAssistantMessage`; não inaugurar um segundo framework de rich UI.

**Proposta de sequência:** Coordenação resolve rastreabilidade/fase/owner → contrato de origem+formato e compatibilidade → inventário e política de renderização segura → tests RED → menor implementação no owner correto → validação integrada e browser QA → review e aceite independentes.

**Gate após D12:** rastreabilidade **Markdown B2** formalizada em `CP-333` (matriz 25) e autorização de **escopo bounded, condicional** registrada pelo Product Master. Contrato `presentation.v2` (G1), reuse e segurança (G2), compatibilidade, testes e aceite permanecem por provar. **Nenhum diff de runtime é autorizado antes de G1+G2 completos e brief G3 formalizado**. `TRACEABILITY_GAP` para tabelas/gráficos C/D/E segue aberto. B1 e `CP-001` não autorizam este contrato.

## 0.1 Decisões vinculantes do Product Master (2026-10-16)

As decisões a seguir foram expressamente aprovadas pelo Product Master no contexto de definição de B2. São **decisões de direção do produto**, sujeitas aos gates normativos de traceability, owner, security, contract freeze e implementação. Nenhuma delas equivale à autorização de alterar runtime, `25` ou `presentation.v1` por inferência.

| ID | Decisão do Product Master | Estado | Implicação congelada |
|---|---|---|---|
| `B2-PD-01` | Markdown textual **com links clicáveis seguros** | `APPROVED_PRODUCT_DIRECTION` | Link somente quando URL legítima, validada e autorizada por contrato; sem link inventado, tracking ou navegação arbitrária |
| `B2-PD-02` | **`presentation.v2`** com formato explícito e transição segura de clientes | `APPROVED_PRODUCT_DIRECTION` | **Não** estender informalmente `presentation.v1`; escolher schema/semântica/ciclo de rollout de v2 em G1. Como não há histórico conversacional durável implementado, não há migração de mensagens persistidas a planejar para o runtime atual; ainda testar versões coexistentes, sessões transitórias e fallback |
| `B2-PD-03` | **DÉLIA controla a produção de Markdown** a partir de conteúdo admitido e governado | `APPROVED_PRODUCT_DIRECTION` | MCP/providers/especialistas não controlam apresentação nem elevam texto a FACT. DÉLIA pode organizar visualmente dados aprovados sem inventar fatos, unidades, IDs ou autoridade |
| `B2-PD-04` | **Markdown textual completo e controlado** | `APPROVED_PRODUCT_DIRECTION` | Permitir headings subordinados, parágrafos, negrito, itálico, listas, citações, divisores, código inline/fenced e links seguros. Permanecem OFF: tabelas estruturadas/GFM tables, gráficos, métricas, imagens, Mermaid, HTML arbitrário, embeds e widgets |
| `B2-PD-05` | **Formatação automática, contextual, proporcional e adaptável ao pedido do usuário** | `APPROVED_PRODUCT_DIRECTION` | DÉLIA decide apresentação no seu boundary com base no objetivo e no conteúdo *admitido*: saudação simples → texto natural; itens/etapas → listas quando útil; explicações longas → seções moderadas; código técnico → bloco inerte apenas quando realmente pertinente. Usuário pode solicitar brevidade/detalhamento, sem mudar fatos, autoridade nem contratos |
| `B2-PD-06` | **Links internos e externos verificados**, ambos no escopo B2 | `APPROVED_PRODUCT_DIRECTION` | Links internos apenas para rotas/entidades legitimamente publicadas pelo ecossistema DELPI; externos apenas para URL comprovada, validada e permitida por contrato/policy. Nenhum endereço inventado pelo modelo; link não autorizado = não clicável. Modo de abertura e regras específicas de navegação ainda precisam ser fechados |
| `B2-PD-07` | **Navegação: links internos no Portal, externos em nova aba** | `APPROVED_PRODUCT_DIRECTION` | Rota/entidade interna usa contrato legítimo de navegação do Portal e live AuthZ/Domain; link externo verificado usa nova aba segura (`noopener noreferrer`), sem auto-open. Nenhuma URL arbitrária abre router ou concede autorização |
| `B2-PD-08` | **Copiar texto legível** | `APPROVED_PRODUCT_DIRECTION` | Botão Copiar gera texto plano compreensível sem sintaxe decorativa Markdown; preservar códigos, valores, unidades, ordem significativa, blocos de código como texto e quebras úteis. Evitar perda/corrupção em transformação, sem falso feedback de sucesso |
| `B2-PD-09` | **Fallback seguro diferenciado** | `APPROVED_PRODUCT_DIRECTION` | Erro apenas de parse/formatação com conteúdo já validado → texto React inerte; payload inválido/inseguro/não admissível → erro neutro, sem exibir ou executar conteúdo adversarial. Não aceitar versão/schema desconhecidos como válidos |
| `B2-PD-10` | **Provenance permanece em `EvidenceDetails`** | `APPROVED_PRODUCT_DIRECTION` | Links legítimos podem aparecer no corpo da resposta sem duplicar ou substituir Evidence/SourceRef, limitations, grounding e seus owners |
| `B2-PD-11` | **Paridade página completa e Companion Dock** | `APPROVED_PRODUCT_DIRECTION` | Mesmo comportamento/componente responsivo em full-page e dock real, release versionado com compatibilidade transitória; mixed clients e rollback testados, sem presumir persistência de mensagens |
| `B2-PD-12` | **Formalizar CP específico e autorizar B2 bounded condicionado** | `APPROVED_PRODUCT_AUTHORIZATION_CONDITIONAL` | Requisito `CP-333` registrado na matriz 25. Pode executar **planejamento final G1 e G2**; implementação I1/I2/I3 somente após contract/security/reuse/compatibility gates provados, brief G3 no HEAD e testes negativos definidos; D12 não é aceite nem liberação de fase |


**Rodada de decisões do Product Master concluída:** `B2-PD-01…12` aprovadas. **Pendências técnicas, não novas decisões de produto automáticas:** schema/erro/discriminator/limites de `presentation.v2`, conjunto de URLs e mecanismo de navegação autorizada, algoritmo determinístico de transformação para texto legível, política positiva de elementos/atributos, compatibilidade v1↔v2, reuse gate e provas de testes/QA. Se as evidências invalidarem alguma escolha, STOP e nova decisão do Product Master; não redesenhar silenciosamente.

**Separação de homônimos:** `B2` neste documento = **Markdown B2 da spec 82**, não `C3-STAGE-02-B2` registrado no ledger para governança de execução/ACT. Status e autorizações de uma trilha **não** se transferem à outra. Responder às decisões futuras no mesmo documento assim que aprovadas.

**Estado de gates:** `CP_MAPPING=CP-333_RECORDED`; `BOUNDED_SCOPE_AUTHORIZED_CONDITIONAL=YES`; `G1_CONTRACT=PENDING`; `G2_SECURITY_REUSE=PENDING`; `G3_IMPLEMENTATION_BRIEF=PENDING`; `RUNTIME_IMPLEMENTATION=BLOCKED_UNTIL_GATES`; `C_D_E_TRACEABILITY_GAP=OPEN`. Produto aprovado **não** é contrato implementado, runtime PASS ou fase concluída. Este plano é subordinado às authorities 16/25 e à spec 82.

### 0.2 Independent review G1/G2 — REWORK (2026-10-16)

O candidato documental [84 — G1/G2](./84-presentation-v2-contract-and-markdown-security-g1-g2-proposal.md) foi revisado independentemente no SHA `d5ed426a08f0fee2aa9179a50d75f828fadd72b2`. Veredito: [85 — Independent Review](./85-presentation-v2-g1-g2-independent-architecture-review.md) = `REWORK` para G1 e G2 (static GitHub review; testes não executados).

- `RW-G1-01` provar dados estruturados governados disponíveis antes de introduzir novo formatter; `InteractiveTurnResult.content` atual é string.
- `RW-G1-02` fechar fonte tipada/contrato de links e preservar D1/D6/D7; B2 sem links navegáveis no primeiro slice exige **nova decisão explícita do Product Master**, não pode ser redefinido pelo executor.
- `RW-G2-01` corrigir enum de `REUSE_DECISION` e demonstrar por inventário/probe por que EXTEND compartilhado não basta antes de criar `NEW ConversationMarkdown`.
- `RW-G1-03` especificar OpenAPI/schema machine-validatable, limites, erros/versões, interactions e fallback v2 vs legado.
- Estado `G1=REWORK / G2=REWORK / G3=BLOCKED / CP333=PLANNED / TEST_NOT_RUN`. Nenhum impacto em D1–D12, C/D/E, fase ou runtime. Próximo bounded: `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R1`.

### 0.3 Rework R1 executado (2026-10-16)

O rework dos 4 achados foi executado sobre `c3e090ac70` e registrado em [86 — Rework R1 Report](./86-presentation-v2-g1-g2-rework-r1-report.md). Correções no candidato [84](./84-presentation-v2-contract-and-markdown-security-g1-g2-proposal.md): produtor = **EXTEND** `render_specialist_outcome` existente (seam provado, categorias A/B/C, fidelity probe 16/16 — sem formatter paralelo); schema real em `contracts/presentation-v2.proposal.schema.json` validado mecanicamente (22/22); links com pacote de decisão `LINK_SOURCE_TYPED` (fonte tipada inexistente — sem redução silenciosa de D1/D6/D7); reuse gate com REUSE/EXTEND/NEW comparados e probe do lexer `marked` (22 casos adversariais). Regressões: 195/195 delia-api alvo, 191/191 vitest delia, 149/149 plugin-ui markdown/rich-text; typecheck com 3 erros pré-existentes de plugin-ui (baseline §6.194). SSH: inspeção read-only em `srv-api` executada.

- Estado pós-R1: `G1=CANDIDATE_REWORKED / G2=CANDIDATE_REWORKED` (nova revisão independente pendente — o executor não emite ACCEPT) `G3=BLOCKED` (aguarda decisão `LINK_SOURCE_TYPED` + ACCEPT) `G4=TEST_NOT_RUN` `CP-333=PLANNED` `RUNTIME_B2_IMPLEMENTATION_AUTHORIZED=NO`.

### 0.4 Decisão L1 e rework R2 (2026-10-16)

**Decisão vinculante do Product Master:** `LINK_SOURCE_TYPED = L1_APPROVED_CONDITIONAL` — links navegáveis reutilizam/estendem contratos governados por owner/capability; condições completas em doc 84 §2.4. **Proibido** promover campos genéricos `url`/`href`/`link`/`*_url` a links navegáveis por nome ou presença em `structured`. L2 (`LinkRef` novo) e L3 (deferir navegável) não aprovadas. Sem contrato governado do owner publicando o destino → zero link navegável (rótulos viram texto) — isso **não** revoga D1/D6/D7.

R2 executado em `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R2` (HEAD `5997604835`): fallback §2.5 reescrito como tabela de decisão executável (probe versionado); testes/probes persistidos em `delia-api/tests/test_presentation_v2_proposal.py` + `test_render_specialist_outcome_fidelity.py` e `plugin-ui/.../conversationMarkdownLexer.probe.test.ts`; residual `token` (R2-03) registrado com RED probe `xfail(strict=True)` + brief bounded de correção — **runtime não alterado**. Inventário L1 (R2-01): um contrato governado real encontrado (`mural_acessos` link `url`, owner api-delpi com validação no write) mas **sem binding capability→structured provado** → `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY`.

- Estado pós-R2: `G1=CANDIDATE_REWORKED` / `G2=CANDIDATE_REWORKED` / `G3=BLOCKED` / `G4=TEST_NOT_RUN` / `LINK_L1_CONTRACT=SPECIFIED` / `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY` / `TOKEN_EXPOSURE=RED_PROBE_RECORDED` (fix aguarda autorização bounded) / `CP-333=PLANNED` / `RUNTIME_B2_IMPLEMENTATION_AUTHORIZED=NO`.

### 0.5 Rework R3 — security closure + inventário L1 + fallback (2026-10-16)

Task `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R3-FINAL-CLOSURE` (relatório [88](./88-presentation-v2-g1-g2-rework-r3-report.md)):

1. **R3-01:** `"token"` adicionado a `_SENSITIVE_KEY_NAMES` no owner `capability_provision` — RED→GREEN em `test_bare_token_key_is_redacted` (sem `xfail`). Matching exato preserva `token_count`/`token_value`.
2. **R3-02:** inventário L1 revalidado — único contrato URL governado continua `mural_acessos.link.url`; **nenhum** binding capability→`SpecialistOutcome.structured`→turno em `delia-api`. `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY` / emissão navegável `BLOCKED`.
3. **R3-03:** doc 84 §2.9/§6 reconciliados com §2.5 — v2 estruturalmente inválido (incl. `additionalProperties`) → `neutral_error`, **não** fallback legado. Probe versionado. Runtime `parsePresentation` inalterado.

- Estado pós-R3: `G1=CANDIDATE_REWORKED` / `G2=CANDIDATE_REWORKED` / `G3=BLOCKED` / `G4=TEST_NOT_RUN` / `TOKEN_REDACTION_STATUS=CLOSED_R3_01` / `FALLBACK_CONTRACT_STATUS=RECONCILED_R3_03` / `LINK_L1_CONTRACT=SPECIFIED` / `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY` / `CP-333=PLANNED` / `RUNTIME_B2_IMPLEMENTATION_AUTHORIZED=NO` / `INDEPENDENT_REVIEW=PENDING`.

### 0.6 Independent closure R3 / G1+G2 (2026-10-16)

Revisão independente [89](./89-presentation-v2-g1-g2-r3-independent-closure-review.md) sobre o delivery R3 `444e03d7d2` no HEAD `08f0bd1041`:

| Dimensão | Veredito |
|---|---|
| R3 security fix (`token`) | `ACCEPT` — código + testes + comportamento no container |
| R3 fallback / schema consistency | `ACCEPT` |
| R3 SSH deploy provenance | `ACCEPT_WITH_RESIDUAL` — redação provada; image sem label git SHA |
| G1 contract candidate | `ACCEPT_WITH_RESIDUAL` — envelope textual pronto; emissão de links bloqueada |
| G2 security/reuse candidate | `ACCEPT_WITH_RESIDUAL` — matriz REUSE/EXTEND/NEW aceita; renderer não implementado |
| G3 / runtime B2 | **BLOCKED** |
| CP-333 | `PLANNED_NOT_PASS` |

**Separação:** aceite do fix R3 ≠ autorização de `presentation.v2` runtime ≠ autorização G3.

- Estado pós-review: `G1=ACCEPT_WITH_RESIDUAL` / `G2=ACCEPT_WITH_RESIDUAL` / `G3=BLOCKED` / `G4=TEST_NOT_RUN` / `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY` / `NAVIGABLE_LINK_EMISSION=BLOCKED` / `RUNTIME_B2_IMPLEMENTATION_AUTHORIZED=NO` / `PHASE_PROGRESSION=NONE`.
- **NEXT bounded (trilha Markdown B2):** `DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-BINDING-INVENTORY-01`.

### 0.7 L1 binding inventory (2026-10-16)

Task `DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-BINDING-INVENTORY-01` — inventário [90](./90-l1-governed-link-binding-inventory-and-contract-closure.md):

- Contratos de domínio **PARTIAL**: `api-delpi` mural `link.url` (write/read publicados) + padrão Core notifications (`portal_route`/`external_url` https) como reuse de validação.
- Caminho **capability → SpecialistOutcome.structured → apresentação DÉLIA** = **NOT_PROVEN** (`rg mural` em `delia-api` = 0; nenhum `capability_id` tipado).
- Chat indexa oids mural — **não** é autoridade DÉLIA (standalone).
- Gap: mural write admite `http`; emissão B2 exige `https` externo.
- Probes de política (não runtime): `delia-api/tests/test_l1_governed_link_admission_policy.py`.

```text
LINK_L1_CAPABILITY_BINDINGS = PARTIAL
NAVIGABLE_LINK_EMISSION = BLOCKED
G3 = BLOCKED
CP-333 = PLANNED_NOT_PASS
```

- **NEXT bounded:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-MURAL-CAPABILITY-BINDING-01` (menor EXTEND para fechar um binding real) — sujeito a revisão independente; **não** libera G3 automaticamente.

### 0.8 Gate stop — implementação B2 não autorizada (2026-10-16)

Task `DELIA-UX-CONVERSATION-MARKDOWN-B2-GATES-AND-IMPLEMENTATION-01` (HEAD `f7121e8b76`):

**Revalidação L1 (não inventário genérico):** o caminho canônico DÉLIA OpenAPI exige `openapi_declarations.delpi.json`. Declarations vigentes = apenas `search_products`, `get_product_summary`, `get_product_stock`, `search_customers`. **Nenhuma** operação `mural_acessos` / `list_mural_acessos_links`. Projection rejeita ops sem declaration (`missing_semantic_declaration`). `delia-api/app` = 0 refs mural. Contrato Domain mural permanece real no owner `api-delpi`; binding capability→structured→turno = **ABSENT**.

**Gates:**

| Gate | Estado | Impede runtime? |
|---|---|---|
| G1 | `ACCEPT_WITH_RESIDUAL` (doc 89) — residual links | Sim (links D1/D6/D7) |
| G2 | `ACCEPT_WITH_RESIDUAL` (doc 89) — renderer não implementado | Sim (I2) |
| G3 | **NOT APPROVED** — sem `G3_TASK_BRIEF_APPROVED` | Sim |
| L1 binding | `PARTIAL` Domain / path DÉLIA ABSENT | Sim (emissão navegável) |

```text
IMPLEMENTATION_ALLOWED = NO
RUNTIME_B2_DIFF = NONE
NAVIGABLE_LINK_EMISSION = BLOCKED
```

**Bloqueio preciso (único material para Architecture/Coordination):**

1. `L1_CAPABILITY_BINDING_ABSENT` — owner competente `api-delpi`; menor EXTEND legítimo = declaration OpenAPI + disclosure do owner no campo `url` + schema de saída tipado; **não** inventar capability local DÉLIA.
2. `G3_TASK_BRIEF_APPROVED` ausente — I1/I2/I3 bloqueados mesmo para Markdown sem links; slice sem links exigiria decisão explícita do Product Master (L3 foi rejeitada).

Sem autoaceitação de gates. Sem I1/I2/I3. Sem deploy.

### 0.7 — Autorização específica de frontend desacoplado (Product Master, 2026-10-16)

O Product Master determinou a execução imediata **apenas** do componente visual compartilhado e sua importação no frontend DÉLIA, sem aguardar o vínculo L1/backend. Isto não é a opção L3 de remover links do objetivo final. Separar:

- `plugin-ui` pode criar o renderer conversacional seguro `ConversationMarkdown` (token→React, sem HTML executável, parsing provider-neutral, links explicitamente allowlisted, CSS próprio do kit).
- `plugins/delia` pode importar e integrar o componente em `DeliaAssistantMessage` **com `enabled={false}`** na superfície v1. A resposta atual continua com parágrafo literal; nenhuma string de modelo/ferramenta, `presentation.v1` ou hint de frontend pode ativar Markdown.
- `presentation.v2` producer/emitter, links navegáveis L1, ativação de `markdown_safe`, formatter backend, runtime de ACT e G3 do fluxo **end-to-end** continuam **BLOQUEADOS** até contrato legítimo e aprovação dos gates.
- O estado `CP-333=PLANNED_NOT_PASS` e os gates G1/G2 `ACCEPT_WITH_RESIDUAL` não mudam por código render-only.
- Aceite frontend exige unit/adversarial tests, typecheck, build/federation, real Portal full-page/dock QA e revisão independente em SHA/config verificados. Onde não executado: `TEST_NOT_RUN`. Proibido afirmar rollout ativo ou business outcome por commit documental.

**Frontend-specific bounded authorization** não substitui a autorização G3 de backend/contrato. O subescopo é reversible e disabled-by-default enquanto L1 não estiver comprovado.

### 0.9 — Frontend component implementation (2026-10-16)

Task `DELIA-UX-CONVERSATION-MARKDOWN-FRONTEND-COMPONENT-IMPLEMENTATION-01` (relatório [91](./91-conversation-markdown-frontend-component-implementation.md)):

```text
PLUGIN_UI_COMPONENT = IMPLEMENTED
DELIA_FRONTEND_IMPORT = IMPLEMENTED
DELIA_INTEGRATION = IMPLEMENTED
MARKDOWN_RENDERER_TESTS = PASS (20 plugin-ui + suite delia 202)
LEGACY_V1_BEHAVIOR = PRESERVED
PRESENTATION_V2_FRONTEND_READER = IMPLEMENTED (parse-only)
RUNTIME_MARKDOWN_ACTIVATION = OFF (sem emitter backend)
BACKEND_V2_PRODUCER = NOT_IMPLEMENTED
L1_BINDING = NOT_PROVEN
NAVIGABLE_LINK_EMISSION = BLOCKED_UNTIL_CONTRACT
CP_333 = PLANNED_NOT_PASS
PHASE_PROGRESSION = NONE
```

Ativação no MFE exige `contentFormat=markdown_safe` + `markdownSource` vindos de `parsePresentationV2` — nunca heurística sobre `turn.content`. Links só com `authorizedLinks` explícitos (App envia `[]` até L1). Build/federation PASS. Browser QA real = `TEST_NOT_RUN`. Aceite independente pendente.

## 1. Autoridades, ordem de reanchor e condição de STOP

Antes de qualquer decisão vinculante ou diff, ler no HEAD real, nesta ordem:

1. HEAD/git status e Project Instructions/.cursor (incluindo `delia-execution-protocol`, `platform-frontend-mfe-experience`, `plugins-reusable-components`).
2. `16-execution-master-plan.md` — fase, NEXT e autorização.
3. `50-standalone-copilot-application-architecture.md` — boundary standalone.
4. `17-component-and-contract-map.md` — owners, consumers e contratos.
5. `49-architecture-and-design-patterns-standard.md` — Clean Architecture e gates.
6. `51-platform-integration-baseline.md` e `52-standalone-repository-and-bootstrap-plan.md`.
7. `21-data-and-state-model.md` → `20-testing-and-acceptance-matrix.md` → `25-requirements-traceability.md`.
8. Arquitetura técnica e `24-product-specification.md`.
9. Specs temáticas 69 (conversation UX), 70 (activity), 73 (chat-first), 75 (assistant message), 79/80 (activity/evidence), 82 (rich content); este documento 83.
10. `evidence/execution-ledger.md`; registros recentes não substituem autoridades superiores.

A autoridade superior prevalece em conflito; reportar `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`, sem reconciliação silenciosa. O doc 16 indica `C3_EXECUTED=NO`, C4/C5 phase-level locked e próximo passo de coordenação; não usar B2 para avançar fase. Documentação aprovada, HTTP 200 ou testes verdes não equivalem a aceitação de implementação ou de outcome.

## 2. Necessidade e critérios de sucesso do produto

**Problema real:** o turno da DÉLIA atualmente apresenta `displayContent` como texto React inerte com `white-space: pre-wrap`. Exemplo observado no produto: resposta de busca com registros iniciados por hífen aparece com quebras literais, sem semântica de lista e recuo de continuidade. B1 melhorou largura/ritmo tipográfico; B2 destina-se à estrutura textual.

**Resultado alvo:** quando **um produtor autorizado** fornecer uma resposta explicitamente declarada Markdown seguro, a conversa poderá exibir, de modo acessível: parágrafos, negrito/itálico, listas numeradas e com marcadores, citações, código inline e blocos de código, e níveis controlados de heading. Links são condicionados a política/contrato de URLs. Pela decisão `B2-PD-05`, a seleção do formato visual é **automática e contextual**, não uma regra de usar Markdown em toda resposta: a DÉLIA deve preferir a menor estrutura que aumenta compreensão e respeitar pedidos válidos do usuário sobre concisão, detalhamento e organização, sem mudar os fatos.

**Não objetivo de B2:** converter toda saída legada; habilitar tabelas GFM automaticamente; gráficos, KPIs, Mermaid, imagens, upload, anexos, HTML livre, widgets, iframe, tool-call UI, streaming fictício, links a entidades sem Domain/Portal contract, ações e novos providers. Tabelas tipadas e gráficos permanecem nas fases C/D da spec 82.

**Princípios:** chat-first, texto principal em primeiro plano; atividade, status, confirmação, evidência, limitações e ações secundárias preservados; conteúdo e metadata não viram autoridade. Format != provenance != AuthZ.

## 3. Baseline factual do repositório (PROVEN por leitura de código; não por teste nesta task)

| Superfície | Owner | Evidência atual | Consequência |
|---|---|---|---|
| `delia-api/app/application/interaction/presentation.py` | DÉLIA backend | `PRESENTATION_CONTRACT_VERSION="1"`; output `text` e `notice/owner_hint`; bounds 8 blocos/16.384 chars | Não existe autorização para um bloco Markdown emitido |
| `plugins/delia/src/api/presentation.ts` | DÉLIA MFE adapter | parse-only; allowlist `text` e `notice`; versão desconhecida → fallback | Não ampliar heurística/permitidos por conveniência |
| `plugins/delia/src/ui/DeliaAssistantMessage.tsx` | DÉLIA MFE | render `<p className="delia-turn__content">{displayContent}</p>`; conteúdo inerte; projeção separada de atividade/evidência | Preservar composição; integrar rich text só se contract autorizar |
| `plugins/delia/src/ui/ConversationTimeline.tsx` | DÉLIA MFE | ordem dos turnos e `role="log"` | Sem novo live-region/superfície dock |
| `plugins/delia/src/index.css` | DÉLIA MFE | B1: tamanho 0.9375rem, line-height 1.62, max-width 68ch e pre-wrap | Usar como baseline; rich text precisa de layout semanticamente distinto |
| `plugins/plugin-ui/src/components/markdown/MarkdownDocument.tsx` | plugin-ui | renderer de **documento** com GFM, code e Mermaid, renderiza HTML derivado via `dangerouslySetInnerHTML` | Equivalente existente; não afirmar fit de conversa |
| `plugins/plugin-ui/src/components/markdown/markdownDocumentModel.ts` | plugin-ui | `marked`, headings/anchors, sanitização compartilhada, separação de Mermaid | Candidate reuse/extend; desabilitar extras não aprovados |
| `plugins/plugin-ui/src/components/rich-text/richTextHtmlFormat.ts` | plugin-ui | sanitizer genérico aceita certos links relativos, `attachment:` e `blob:`, dentro de outro contexto | NÃO copiar a política para DÉLIA sem Security Review |
| `plugins/plugin-ui/src/components/collaboration/messageThreadMarkdown.ts` | plugin-ui colaboração | Markdown com semântica de anexos/menções específica | Evitar dependência do runtime/fluxo de Chat |
| `plugins/plugin-ui/src/components/data/DataTable.tsx` e `components/charts/` | plugin-ui | componentes visuais existentes | Fora de B2; inventário futuro C/D, sem duplicação |

A composição B1 foi observada no commit `ffc0c36c88ec9ab3681d8e9951d73bb7316613b1`; sem claim de deploy no presente documento. Testes documentais de Markdown existentes provam cobertura em contexto documental, **não** segurança de integração com DÉLIA. Inventário do backend inclui `interactionClient`, mas não prova um produtor confiável de Markdown.

## 4. Responsibility → owner → source → consumers → contract → implementation → test → outcome

| Responsabilidade | Owner | Source / autoridade | Consumer |
|---|---|---|---|
| Dado operacional e regras | Domain API / owner da fonte | Resposta validada e autorizada; definição de métrica se aplicável | DÉLIA application |
| Permissão efetiva | Core + Domain | Live AuthZ e regra final | DÉLIA action/read boundary |
| Decisão de apresentação e admissão de conteúdo | DÉLIA Application/Interfaces | Dados governados, Evidence, Policy; não provider metadata | Contrato de interação |
| Contrato explícito de formato | DÉLIA API contract owner | OpenAPI/JSON Schema + version + conformance | API serializer + adapter MFE |
| Parsing e renderer visual seguro | `plugin-ui` owner | Renderer/policy aprovada para conversational read-only | Composição `plugins/delia` |
| Composição semântica da resposta | DÉLIA MFE | projection parse-only + componentes do kit | Full-page e Companion Dock |
| Evidence, provenance e limitations | DÉLIA evidence/projection + source owner | Contratos atuais | `EvidenceDetails` |
| Teste e aceite independente | QA/Security/Architecture Coordination | SHA/config/traceability e browser real | Reviewer/Product Master |

O planner nunca decide renderizadores/URLs por nomes de provider, endpoints ou ferramentas. MCP/A2A tool metadata e model output são UNTRUSTED DATA; formato não implica acesso, segurança factual, execução, publicação, confirmação ou permissão.

## 5. Rastreabilidade: gap explícito, sem CP inventado

**Baseline anterior à decisão D12:** `TRACEABILITY_GAP=OPEN`, sem CP próprio. **Decisão factual atual:** Product Master aprovou D12 e a matriz 25 recebeu `CP-333` para Markdown textual em `presentation.v2`. A lacuna de CP para **B2 textual foi mapeada**; o gap separado de tabelas/métricas/gráficos **permanece aberto**. CPs abaixo continuam dependências transversais, não substituem `CP-333`:

| CP | Relação | Limite |
|---|---|---|
| CP-001 | UX DÉLIA no Portal/full-page/dock | Não cobre novo schema/rich renderer |
| CP-015 | Análise e comparação grounded | Não autoriza formato Markdown |
| CP-027 | Resumo/relatório grounded | Não especifica renderer conversacional |
| CP-093 | EvidenceRef transversal | Evidence ≠ admissão de rich content |
| CP-135 | Error/Result model | Não versiona formato rich |
| CP-196 | External content untrusted | Security invariant sem contrato B2 |
| CP-270 | Personalização de conteúdo/formato | Preferência não autoriza conteúdo |

**Decisão concluída:** `CP_MAPPING_DECISION=NEW_CP_333`, por decisão expressa D12 do Product Master, registrado no `25` (owner DÉLIA API/Application + MFE/Portal + plugin-ui + Security). `CP-333` está `PLANNED`, não `PASS` e nem `IN_PROGRESS` por documentação. Os requisitos B2-RQ continuam IDs locais até receberem vínculo explícito e critérios de aceite em task G3. Não atribuir `CP-333` a C/D/E.

**Gate de desbloqueio para diff de runtime:** `CP_MAPPING=CP-333_RECORDED` e `BOUNDED_SCOPE_AUTHORIZED_CONDITIONAL=YES` são satisfeitos por D12. **AINDA EXIGIDOS:** `G1_CONTRACT_DECISION=APPROVED` (OpenAPI + compatibilidade + producer + erros + limites + copy + navigation) e `G2_SECURITY_REUSE=APPROVED` (allowlist links/nós, threat model e equivalence decision), seguidos de `G3_TASK_BRIEF_APPROVED` para I1/I2/I3 no HEAD real. Ausência → STOP; não tratar D12 como autorização automática de codificação.

## 6. Contract-first — pontos de decisão obrigatórios

O payload atual de `presentation.v1` é vigente e fechado. Não alterar o parser para interpretar `text` como Markdown sem nova semântica publicada.

### 6.1 Estratégia de formato — produto decidiu `presentation.v2`; schema técnico pendente

**Decisão `B2-PD-02`: `presentation.v2` será o contrato alvo**, com discriminação explícita entre texto literal e Markdown seguro. Não executar a antiga opção de campo aditivo direto em `presentation.v1` por conveniência. `presentation.v1` continua como runtime atual até implantação autorizada.

**O que ainda cabe ao Contract Gate G1 (não definido nesta decisão):**

- Shape do envelope, discriminators, union de blocos, nomes de campos, `operationId`, semântica de fallback e erros; publicar OpenAPI/JSON Schema no owner.
- Determinar limites, forma de conteúdo, origem do formato e validação do produtor do backend; nenhuma field/projection inventada por frontend.
- Matriz de compatibilidade **backend v1/v2 × MFE v1/v2** e coexistência de abas/sessões abertas. Não há migração de histórico durável atualmente, mas isso **não elimina** mixed-version rollout/rollback.
- Comportamento de versão desconhecida, degradação para texto inerte quando permitida e proteção contra exibição enganosa de markup em clientes antigos.
- Não ativar emissão v2 até consumidores compatíveis e estratégia de deployment/verificação serem demonstrados.

G1 não rediscute v1 vs v2 sem nova evidência que justifique retornar a decisão ao Product Master. Se houver impossibilidade real de v2 sem drift, **STOP → ARCHITECTURE_DECISION_REQUIRED**.

### 6.2 Origem/declaração de Markdown

Por decisão `B2-PD-03`, **a DÉLIA é o único owner da produção e admissão do Markdown**, com **formato explicitamente publicado no futuro contrato `presentation.v2`**, a partir de informação governada. Especialistas e providers podem fornecer dados/textos não confiáveis pela integração legítima, mas não decidem o formato user-facing por metadata ou output. O backend atual projeta conteúdo já governado e **não permite prosa factual livre escrita pelo modelo** como autoridade. O plano NÃO altera esse freeze: markup não autoriza geração livre de novas afirmações, cálculos, URLs ou fatos.

Deve existir prova sobre **quem produz Markdown**, de quais dados e com qual transformação determinística ou política governada; não basta adicionar um flag ao frontend. O formatter não modifica identificadores, unidades, quantidades ou textos fornecidos pelo owner, nem inventa fonte. O owner do conteúdo permanece responsável pela veracidade dos dados; formatação só altera estrutura visual.

A fonte pode fornecer caracteres Markdown literais. Sem formato explicitamente aceito pelo contrato, exibir os caracteres exatamente como texto. Não inferir formato por presença de `#`, `*`, `-`, crases, URLs ou regex. Não retroconverter histórico/turnos anteriores automaticamente.

### 6.2.1 Política contextual de seleção de apresentação — `B2-PD-05` aprovada em produto

- **Saudação, resposta curta ou esclarecimento simples:** texto natural, sem headings, divisores ou listas decorativas.
- **Coleção de registros ou etapas distintas:** lista semântica quando houver agrupamento/ordem explícitos e o conteúdo admitido sustentar a estrutura; preservar códigos de produto, nomes, quantidades, ordem material e unidades, sem gerar novas afirmações.
- **Explicação extensa, procedimento ou comparação narrativa:** parágrafos e seções discretas somente quando a estrutura melhorar a leitura; não transformar toda resposta em relatório ou dashboard.
- **Código ou comandos técnicos efetivamente presentes e autorizados:** inline/fenced code inerte. Não inventar comandos, links, scripts ou instruções de operação/safety.
- **Preferência expressa do usuário:** adaptar nível de detalhe e densidade de formatação quando compatível com dados admitidos, policy e limites; preferências não autenticam, autorizam nem substituem fatos live. Não persistir preferências nesta task.
- **Implementação da decisão:** o produtor/formatador governado na boundary DÉLIA escolhe representação textual/Markdown explícita do contrato `presentation.v2`; **o frontend não adivinha o formato a partir de palavras, pontuação, regex, provider ou texto da conversa**. O algoritmo concreto de escolha, seus limites e avaliações de fidelidade ficam para G1/G2; não criar um segundo planner nem admitir prosa factual inventada.
- **Critério de qualidade:** conteúdo curto continua simples; listas e headings aparecem quando justificáveis; o leitor distingue conteúdo, atividade e evidência; falha de formatação degrada para texto seguro. Não usar estilo como evidência de confiança, materialidade ou permissão.

### 6.3 Invariantes de compatibilidade

- Respostas atuais sem o novo campo → React text inerte, idêntico ao comportamento legado.
- Contrato/version inválido, formato desconhecido, conteúdo inconsistente ou variante não suportada → fallback neutro e seguro **definido pelo contrato**; não renderizar HTML gerado arbitrariamente.
- Se parse Markdown falhar: fallback determinístico texto inerte; preservar conteúdo exibível sem throw de UI.
- O novo renderer não altera `message_kind`, `semantic_status`, `grounding_status`, `allowed_interactions`, `owner_hint`, `confirmation_request`, `provenance`, `limitations`, identity ou Activity.
- Copy action deve copiar conteúdo textual esperado e preservar IDs/verbatim; definir contrato para Markdown formatado (copiar fonte Markdown versus texto legível) **antes** do diff. Não copiar markup oculto nem dados de controle.
- Turnos de usuário, owner hints, códigos e campos técnicos não ganham Markdown sem uma decisão tipada própria.
- Não criar armazenamento, memory, embeddings, histórico ou estado retido no browser.

### 6.3.1 Aplicação das decisões D7–D11 no contrato (normativo de produto, implementação pendente)

- **D7 — navigation:** links internos aceitos representam route/entity contracts legítimos e são tratados pela navegação governada do Portal (não `window.location` ou URL interna construída pelo modelo); Core/Domain mantêm AuthZ. Links externos só clicáveis após validação/review de origem e URL, abrem em nova aba com `rel="noopener noreferrer"`; sem auto-fetch, auto-open, `javascript:`, `data:`, `blob:`, `attachment:` ou relative/hash que escape do host.
- **D8 — clipboard:** contrato de cópia de texto plano legível preserva informação factual (IDs, quantidades, unidades, sinais, lista/ordem, newline e conteúdo de blocos de código). Transformação deve ser determinística e testada; se não puder preservar, falha honestamente, sem copiar valor divergente.
- **D9 — fallback:** somente erro de render/parser com conteúdo previamente admitido permite fallback para texto inerte. Payload inválido, malicioso ou incompatível não deve ser apresentado disfarçado de fallback: erro neutro, sem execução ou log de raw content. Não reclassificar provenance ou status.
- **D10 — Evidence:** links no Markdown não substituem `EvidenceDetails`; este mantém Source/Evidence/provenance/limitations. Links de fonte exigem permissão de divulgação, não se tornam evidência por aparência.
- **D11 — surfaces/rollout:** mesma composição conversacional no MFE usada em full-page e dock real, com testes light/dark/320px/420px/zoom 200%/keyboard/SR e compatibilidade transitória `v1↔v2` em deploy misto. Sem persistência de histórico corrente, não há migração de mensagens, mas sessão/aba antiga e fallback continuam relevantes.
- **G1/G2 obrigatórios:** os detalhes do envelope `v2`, allowlists concretas, URLs, gateway/Portal contracts, budget e comportamento de versões precisam ser provados/revisados, não inventados por este registro.

### 6.4 Contract checklist de congelamento

| Campo | Evidência exigida antes do código |
|---|---|
| Owner/consumers | DÉLIA API + MFE, compatibilidade legacy, plugin-ui owner |
| Version/discriminator | OpenAPI e schema revisados; unknown version safe |
| Producer/invariants | Fonte admitida e transformações permitidas; sem prosa factual inventada |
| Constraints | Size/max nesting/max code length/max links/timeout/complexidade |
| Errors/fallback | Safe rendering para malformed/unknown/partial; sem ocultar avisos |
| Security | Allowlist de nós/atributos/URLs, sandbox/CSP, testes adversariais |
| Privacy | Sem secrets, PII indevida, tracking/remote fetch automático |
| Observability | Counters sanitizados de formato/fallback e version; sem raw content nos logs |
| Deployment | Sequência versionada backend→frontend, rollback/revoke e mistura de versões |
| Semantics | Separação `FORMAT != FACT != AUTHZ`; read-only renderer |

## 7. Reuse Gate e Abstraction Gate — registrar por candidato

| Candidato | EXISTING_EQUIVALENT | REUSE_DECISION | Ação antes do freeze |
|---|---|---|---|
| `DeliaAssistantMessage` e subcomponentes atuais | YES | REUSE | Manter composição e acessibilidade |
| `MarkdownDocumentView` | YES, documental | PENDING | Avaliar se reutilização pura serve sem Mermaid/anchor navigation; senão EXTEND legítimo |
| `buildMarkdownDocumentModel` | YES, documental | PENDING | Examinar se parsing GFM é configurável/fail-closed e o custo de reutilização |
| `stripDangerousRichTextTags` | YES, genérico | PENDING | Auditar allowlist real; política DÉLIA mais restritiva |
| `messageThreadMarkdown` | YES, colaboração | PENDING | Avaliar helper neutro, sem import do runtime Chat ou attachment/mention |
| Novo renderer/adapter/registry próprio | TO_INVENTORY | PENDING | Novo code path só se equivalente falhar em prova e Abstraction Gate autorizar |

`PENDING` é estado do gate, não quarto valor de `REUSE_DECISION`. Decisões finais somente `REUSE | EXTEND | NEW`; para toda `NEW` anexar evidence de owner, necessidade, consumer real, por que `REUSE/EXTEND` não atende e por que alternativa menor é insuficiente. O owner de estilos/primitive compartilhado é `plugin-ui`; não escrever CSS espelho/override indevido do kit no MFE.

## 8. Política mínima de Markdown B2 (candidata ao Security Review)

**Escopo textual aprovado pelo Product Master (`B2-PD-01` e `B2-PD-04`); implementação condicionada ao Security/Contract Gate:**
- Habilitáveis por contrato: parágrafos, ênfase forte/fraca, listas ordenadas/não ordenadas (nested com profundidade limitada), blockquote, código inline e fenced code **text-only**, divisores simples e headings subordinados ao heading da conversa (não usar H1 duplicado).
- Acessibilidade: listas são `ul/ol/li` reais; headings mapeados para hierarquia válida, sem âncoras globais geradas sem escopo; código não vira execução.
- Links **incluídos no escopo B2 por decisão de produto** e **bloqueados até existência da política/contrato aprovado**: URLs válidas, origem publicável e autorização do owner; allowlist positiva de schemes/hosts e navegação Portal; `noopener noreferrer` em nova aba externa. Não inferir fonte, criar URL nem auto-open. Se política não estiver aprovada, links específicos degradam para texto sem navegação, sem autorizar links inseguros.
- OFF no B2: HTML inline/bruto, CSS inline, styles, SVG, MathML, iframe, script, media, remote images, attachment/blob/data URLs, embeds, forms, interactive checkboxes, Mermaid, diagrams, **tabelas GFM e tabelas estruturadas**, gráficos, tool directives, JSX/MDX, browser/app controls, syntax-highlighter dinâmico, componentes React gerados pelo modelo.
- O renderer não deve carregar recursos remotos apenas por interpretar o Markdown. Sem fetching silencioso de imagens/links. Sem anchor hijack no hash/router do Portal.
- Visual chat-first: typography tokens do kit; não colocar cada parágrafo/lista em card; tabelas/gráficos em outra fase.

**Risco descoberto na reutilização:** o sanitizador genérico existente aceita `attachment:`, `blob:` e links relativos por razões de outros consumers, e o `MarkdownDocumentView` oferece Mermaid e HTML derivado por `dangerouslySetInnerHTML`. Essas superfícies **não** são automaticamente seguras para resultados de IA na DÉLIA. Exigir policy conversacional por allowlist positiva de elementos/atributos/URL, testes cross-browser, threat model e Security Review. Se o sanitizer entrar em fallback de parsing, não tratar regexp stripping como prova de proteção completa; falhar fechado ou retornar texto inerte. Nunca invocar `dangerouslySetInnerHTML` com HTML direto de modelo/MCP/owner.

## 9. Plano bounded de execução (D12 aprovou escopo condicional; diffs somente após gates)

| Slice | Owner principal | Entregável de entrada | Ação bounded | Saída/gate |
|---|---|---|---|---|
| B2-G0 — Architecture/Traceability | Coordination + Product/Security | D1–D12 + 82/83 + HEAD + 25 | `CP-333` formalizado, bounded C3 autorizado **condicionalmente**; conferir drift em HEAD | `DOCUMENTED / CONDITIONAL`; não libera runtime sem G1/G2 |
| B2-G1 — Contract Decision | DÉLIA API owner + Frontend + Security | G0 registrado, D2 escolheu `presentation.v2` | Especificar discriminator/blocks e producer DÉLIA, fallback/copy/links/limites, OpenAPI, old/new compatibility; **não rediscutir v1/v2 sem drift formal** | Contract/ADR reviewed/frozen (PENDING) |
| B2-G2 — Reuse/Security Feasibility | plugin-ui + DÉLIA frontend + Security | G0 registrado; avançar inventário paralelo a G1, aprovação final depois do contract freeze | Prova de reuse/extend, auditoria sanitizer, links e política positiva por tipo | Reuse Decision + threat model + testes adversariais RED (PENDING) |
| B2-I1 — Backend projection bounded | DÉLIA API owner | G1/G2 aprovados | Menor diff produtor/serializer de formato; sem prosa factual livre, sem novas capabilities | Testes de contrato, legacy/fallback, OpenAPI, no authority drift |
| B2-I2 — Shared renderer bounded | plugin-ui owner | G2 aprovado | Reuse/extend só dos primitives necessários, sem Mermaid/imagem/HTML | Testes de sanitizer/nós/links/DoS/a11y |
| B2-I3 — DÉLIA integration | DÉLIA MFE | I1/I2 aprovados | Adapter parse-only e slot de content no `DeliaAssistantMessage`; manter Evidence/Activity/Copy | Unit/integration/build/federation |
| B2-Q1 — Cross-surface QA | QA + Security + Frontend | I1/I2/I3 | Full-page/dock real, dark/light, teclado/zoom e ataques | QA evidence em SHA/config |
| B2-R1 — Independent review | Architecture/Coordination | Q1 evidence + git diff | Conferir invariantes, CP, contract, runtime claims, rollback e residual | ACCEPT / ACCEPT_WITH_RESIDUAL / REWORK / DRIFT / INCONCLUSIVE |

**Sequência física I1/I2:** pode variar segundo frozen contract; não inventar integração antes da decisão. O executor pode produzir somente estudo/prova RED antes do gate, sem diff de runtime. Cada slice tem owner, commit, gates e acceptance próprios; não juntar tudo em um prompt monolítico. Se o renderer já atender 100% sem extensão, `B2-I2=NOT_APPLICABLE_WITH_EVIDENCE` e reuse direto.

## 10. Requirements atômicos candidatos (não CPs canônicos)

Estes itens servem para elaborar o brief de implementação depois de G0 e **não equivalem a requisitos autorizados**. Cada um exigirá ligação a CP e AC formalmente aprovados.

| RQ local | Criticidade | Critério demonstrável |
|---|---|---|
| B2-RQ01 | CRITICAL | Formato Markdown **explícito** e somente quando autorizado por contract |
| B2-RQ02 | CRITICAL | Legacy plain text e caracteres especiais preservados sem parser |
| B2-RQ03 | CRITICAL | Backend produz apenas rich text admitido e evidence-bound; sem fato inventado |
| B2-RQ04 | CRITICAL | Parser/sanitizer com allowlist positiva, sem raw HTML/script/unsafe URL |
| B2-RQ05 | CRITICAL | Unknown/malformed/unsupported → fallback neutro e não executável |
| B2-RQ06 | CRITICAL | Estados, confirmação, owner_hint, activity, Evidence e limitações intactos |
| B2-RQ07 | CRITICAL | Sem alteração de AuthZ/Policy/Decision/ACT nem provider mechanics |
| B2-RQ08 | HIGH | Rich prose coerente e acessível (headings/lists/code) |
| B2-RQ09 | HIGH | Compatibilidade API/frontend antigos e downgrade/rollback |
| B2-RQ10 | HIGH | Reuse sem duplicar owner/plugin-ui/sanitizer e sem trazer Chat runtime |
| B2-RQ11 | HIGH | Full-page + dock real, 320/420px, zoom 200%, teclado, tema e screen reader |
| B2-RQ12 | HIGH | Cópia exata segundo semântica congelada de contrato |
| B2-RQ13 | HIGH | Bounds contra mensagens grandes, nesting/links/code e DOM explosion |
| B2-RQ14 | HIGH | Não exibir links/novas ações sem contrato legítimo |
| B2-RQ15 | HIGH | Evidência/observabilidade sem logar conteúdo/segredo |
| B2-RQ16 | CRITICAL | SHA/config, security eval, contract tests e outcome para aceite |
| B2-RQ17 | HIGH | Escopo B2 sem gráficos/tabelas/Mermaid/remote media |
| B2-RQ18 | HIGH | Rollout/rollback sem mudar legacy turn e sem client crash |
| B2-RQ21 | CRITICAL | Links internos por contrato de Portal e externos verificados em nova aba; sem URL inventada |
| B2-RQ22 | HIGH | Clipboard texto legível preserva IDs/unidades/ordem/quebras e dá feedback verdadeiro |
| B2-RQ23 | CRITICAL | Parse seguro → fallback literal; payload inválido/inseguro → erro neutro sem leak |
| B2-RQ24 | HIGH | EvidenceDetails preservado e independente de links inline |
| B2-RQ25 | HIGH | Paridade full-page/dock e mixed-version rollout com safe rollback |
| B2-RQ19 | HIGH | Escolha automática e proporcional de Markdown a partir de dados admitidos, sem overformatting |
| B2-RQ20 | CRITICAL | Pedidos de estilo do usuário não alteram facts/IDs/units/limitações/Policy e não geram escrita ou permissão |

## 11. Matriz de testes e evidência de aceite

| AC local | Input/cenário | Expected / negative gate |
|---|---|---|
| B2-AC01 | `plain_text` com `**`, `#`, `<b>`, código de produto e `-` | Texto verbatim sem headings/links |
| B2-AC02 | Markdown aprovado: parágrafos + negrito + itálico | Nós semânticos corretos, texto íntegro |
| B2-AC03 | Listas nested e linhas longas | `ul/ol/li`, indent correto, nenhum overflow |
| B2-AC04 | Code inline/fenced com `<script>` e strings técnicas | Code inerte, copiável, nenhuma execução |
| B2-AC05 | Markup adversarial: script/onerror/onclick/svg/math/style/iframe/form | DOM seguro, zero execução/HTML perigoso |
| B2-AC06 | URL `javascript:`, `data:`, `blob:`, `attachment:`, `file:`, relativo e hash | Bloqueio conforme policy, sem navigation hijack |
| B2-AC07 | malformed HTML/Markdown, unicode confusables, deeply nested, huge payload | Fallback/limites fail-closed, sem browser hang |
| B2-AC08 | Unknown block/version/format e omit field | Safe fallback; legacy intacto |
| B2-AC09 | Owner hint duplicado no legado e rich response | Dedup conforme contrato, sem perda de conteúdo real |
| B2-AC10 | AUTHZ_DENIED, SOURCE_UNAVAILABLE, CONFIRMATION_REQUIRED | Status e confirmação sem side effects ou leaks |
| B2-AC11 | GROUNDED / NON_GROUNDED + provenance/limitations | Evidence não alterada, dados técnicos não exibidos |
| B2-AC12 | Model/MCP result com conteúdo de instrução/HTML | Tratado como dado não confiável, não como comando |
| B2-AC13 | User turn, ActivityViewer, metadata e label técnico com Markdown syntax | Nunca converter superfícies fora de escopo |
| B2-AC14 | Clipboard em plain/rich + falha da API | Valor conforme copy contract; feedback sem falso sucesso |
| B2-AC15 | Multi-turn em full-page e dock real, 320/420, light/dark, zoom 200 | Ordem, scroll, foco e leitura corretos |
| B2-AC16 | Keyboard/SR/reduced motion | Hierarquia heading/listas, tab/focus e announcement únicos |
| B2-AC17 | Backend antigo + frontend novo; backend novo + frontend antigo | Matrix compat e fallback sem regressão/HTML literal inesperado |
| B2-AC18 | Resultado operacional com IDs, unidades, contagens e Evidence | Valores/ordem sem transformação semântica, nenhuma fonte inventada |
| B2-AC19 | Medida de parser/DOM sob limites e erro de sanitização | Bound e degrade sem crash; sem timers ou progresso falso |
| B2-AC20 | Backend + plugin-ui + delia frontend build/typecheck/federation; CI | Evidence no SHA exato e unrelated failures classificadas, sem falso PASS |
| B2-AC21 | Saudação/resposta curta vs coleção de registros vs orientação em etapas vs texto longo | Saída proporcional: texto simples, lista e seções somente quando agregam legibilidade |
| B2-AC22 | Usuário solicita "responda em uma frase", "organize em tópicos" ou "explique em detalhes" | Formatação se adapta sem perder fatos, valores, códigos, provenance ou limitações |
| B2-AC23 | Texto contém caracteres Markdown literais mas formato explícito é plain_text | Nenhuma inferência de Markdown nem parse indevido pelo frontend |
| B2-AC24 | Conteúdo não justifica heading/lista ou traz comandos técnicos não admitidos | Não fabricar estrutura ou instruções operacionais; fallback inerte mantém conteúdo útil |
| B2-AC25 | Link interno autorizado, não autorizado, rota inventada e entidade sem permissão | Navegação somente via Portal contract + AuthZ; bloqueio de construções e vazamentos |
| B2-AC26 | Link externo verificado, URL desconhecida e protocols adversariais | Nova aba somente se policy aprovar; rel seguro, sem fetch/auto-open; demais são texto inerte |
| B2-AC27 | Copy de lista/heading/links/code com caracteres especiais e unidades | Texto legível determinístico; sem perda de valor/identificador/newline e sem falso sucesso |
| B2-AC28 | Parser falha em conteúdo admitido versus payload malicioso/schema inválido | Fallback inerte no primeiro; erro neutro sem raw HTML no segundo |
| B2-AC29 | Fonte embutida em link Markdown + `EvidenceDetails` com provenance | EvidenceDetails continua autoritativo/visível; link não eleva epistemic class |
| B2-AC30 | Full-page e dock real com API v1/v2, clientes antigos, rollback, dark/light, zoom/SR | Comportamento equivalente e seguro, sem reload/migração suposta |

Testes unitários, integration, adversariais, smoke autenticado read-only e browser QA real devem ser executados no SHA/config entregue. **Nenhum teste foi executado nesta task documental.** Testes verdes não provam a fidelidade de fatos operacionais sem um caso grounded comparado ao owner. Em produção, validar apenas leituras autorizadas com fonte; `MATERIAL_ACT_CALLS=0` no escopo.

### Evidências obrigatórias para aceite

- Lista de arquivos alterados, diff, HEAD base/final, branch e logs.
- CP/RQ/AC formalmente aprovados com status `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`.
- Contrato OpenAPI e conformance (cliente antigo/novo), bounds e fallback.
- Testes de XSS/URLs/HTML/escape e ausência de forced navigation.
- Browser QA screenshots legíveis e resultados de teclado/SR/full-page/dock real/light/dark/zoom.
- Evidência de leitura autoritativa quando houver dados operacionais; sem extrapolar para gráficos.
- CI status por job, análise de falhas unrelated, residual search.
- Version/deploy/rollback na boundary verdadeira; sem claim de deploy se não realizado.

## 12. Deployment, version compatibility, rollback e observabilidade

A ordem de deploy deverá ser decidida com o contract owner (não assumir infra/feature-flag existente): cliente tolerante ao legado, depois servidor com formato explícito, ou estratégia inversa **somente se** a matriz de compatibilidade prová-la segura. Não usar version bump como substituto de negociação. Mixed versions precisam de testes; eventos parcialmente recebidos não devem produzir HTML. Uma desativação deve restaurar texto literal com custo bounded e sem perda de dados, evitando contaminação de estado durável.

Se for necessária feature flag, inventariar mecanismo legítimo de Core/config antes de criar um registro paralelo; flag cliente não concede permissão. Logar apenas version/mode/fallback/exception code e correlation id permitido; nunca Markdown bruto, tokens ou provider payload.

## 13. Gates finais e entregáveis de Coordination

**G0 (rastreabilidade/autorização) — DOCUMENTED / CONDITIONAL:** D12 autorizou o escopo bounded e `CP-333` foi registrado no 25, com owner e fase C3 (slice de apresentação, **não** conclusão de C3). A liberação de runtime permanece condicionada a G1+G2 e brief G3; se o HEAD futuro mudar contrato/owner/fase, STOP para reancoragem.

**G1 (contrato) — BLOCKING:** direção `presentation.v2` **escolhida pelo Product Master**; falta congelar OpenAPI/schema/ADR (kind `plain_text` vs `markdown_safe` em representação explícita sem fixar nomes antecipadamente), DÉLIA como producer, compatibilidade old/new, política de erros/fallback D9, copy D8, navegação D7, Evidence D10 e limites. Não retomar aditivo v1 sem nova decisão explícita.

**G2 (segurança/reuse) — BLOCKING:** avaliação de sanitizer/renderer e escopo permitido; componente real e owner legítimos; no raw HTML, no provider tools as authority.

**G3 (execução) — BLOCKING:** brief Devin com RQ/AC/Critical mapping, SHA atual, staged steps e stop conditions; sem mudar controle do produto.

**G4 (QA/aceite) — BLOCKING:** testes, security e browser QA reais no SHA/config; reviewer independente emite `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**Entregas restantes dos owners após D1–D12:**
1. `G0=CP-333_MAPPED_AND_CONDITIONAL_SCOPE_AUTHORIZED`: verificar que o HEAD não traz nova decisão incompatível; escopo C3 estritamente de apresentação.
2. `G1=PENDING`: OpenAPI/schema `presentation.v2` com formato explícito, produtor DÉLIA, matriz old/new, copy D8, erro D9, Portal/external URLs D7, Evidence D10, paridade D11 e limites.
3. `G2=PENDING`: `EXISTING_EQUIVALENT`/`REUSE_DECISION` final por componente, sanitizer positive allowlist, threat model e links seguros.
4. `G3=PENDING`: brief bounded por slice para Devin, com CP-333, RQ/AC, SHA de implementação, mocks/contratos/negativos/rollback.
5. `G4=PENDING`: browser QA completo e review independente, sem se autoaceitar.

Não se exige liberação de C/D (tabelas/gráficos) para um B2 estritamente textual.

## 14. Handoff futuro ao Devin — somente após G0/G1/G2

**Task futura sugerida:** `DELIA-UX-CONVERSATION-MARKDOWN-SAFE-B2-IMPLEMENTATION-01`. Escopo de produto bounded autorizado por D12; **não iniciar modificação de runtime** até G1+G2 completos e brief G3 aprovado. Preparar G1/G2 agora é permitido como documentação/review.

Modo: `REANCHOR → GATES → CONTRACT CONFORMANCE → REUSE → RED TESTS → MINIMAL DIFF → UNIT/SECURITY → BROWSER QA → BUILD/FEDERATION → RESIDUAL SEARCH → DOCS/LEDGER FACTUAL → COMMIT/PUSH → VERIFY → REPORT`.

Restrições: trabalhar em `main` **somente conforme política solicitada pelo Product Master e se os gates permitirem**; sincronizar origin, preservar concorrência, fast-forward apenas, não fazer force push; STOP em divergence. Não implementar C/D nem novos recursos de provider/AI. Não se autoaprovar.

**Required DÉLIA EXECUTION REPORT:** BASE_HEAD, FINAL_HEAD, branch, CP/RQ/AC, phase, authorization evidence, owner/contract, equivalence/reuse, diff, threat model, tested SHA/config, API conformance, a11y/browser QA real, source/outcome evidence, residuals/drifts, CI status, rollback, verdict independente posterior.

## 15. Registro de estado factual deste planejamento

```text
TASK = DELIA-UX-CONVERSATION-MARKDOWN-B2-PLANNING-01
ARTIFACT = DOC_83_PLAN_ONLY
B1_TYPOGRAPHY = IMPLEMENTED_WITH_REVIEW_RESIDUAL
B2_PRODUCT_DIRECTION = APPROVED_BY_PRODUCT_MASTER
B2_MARKDOWN_LINKS = APPROVED_IF_URL_CONTRACT_AND_SECURITY_GATES_PASS
B2_CONTRACT_VERSION_DIRECTION = PRESENTATION_V2_APPROVED
B2_FORMAT_CONTRACT_SCHEMA = TO_DESIGN
B2_PRODUCER_OWNER = DELIA_APPROVED_BY_PRODUCT_MASTER
B2_FORMAT_SCOPE = FULL_CONTROLLED_TEXT_MARKDOWN
B2_AUTOMATIC_FORMATTING_POLICY = PRODUCT_APPROVED_CONTEXTUAL_PROPORTIONAL_ADAPTIVE
B2_LINK_DESTINATION_POLICY = INTERNAL_AND_VERIFIED_EXTERNAL_PRODUCT_APPROVED
B2_LINK_NAVIGATION_BEHAVIOR = PORTAL_INTERNAL_EXTERNAL_NEW_TAB_APPROVED_D7
B2_COPY_BEHAVIOR = READABLE_TEXT_PRESERVE_DATA_APPROVED_D8
B2_FALLBACK_BEHAVIOR = SAFE_INERT_TEXT_OR_NEUTRAL_ERROR_APPROVED_D9
B2_EVIDENCE_LAYOUT = EVIDENCE_DETAILS_PRESERVED_APPROVED_D10
B2_SURFACE_ROLLOUT = FULL_PAGE_AND_DOCK_VERSIONED_COMPATIBLE_APPROVED_D11
B2_SCOPE_AUTHORIZATION = CONDITIONAL_APPROVED_D12
B2_RENDERER_SECURITY_FIT = TO_INVENTORY
EXISTING_EQUIVALENT = YES (shared markdown/document primitives)
REUSE_DECISION = PENDING_FOR_MARKDOWN_IN_DELIA
B2_MARKDOWN_TRACEABILITY = MAPPED_CP_333
C_D_E_STRUCTURED_TRACEABILITY_GAP = OPEN
CP_MAPPING = CP_333_PLANNED_NOT_PASS
B2_BOUNDED_SCOPE_AUTHORIZED = CONDITIONAL_YES
G1_CONTRACT_SECURITY = PENDING
G2_REUSE_SECURITY = PENDING
G3_IMPLEMENTATION_TASK_BRIEF = PENDING
B2_G1_CONTRACT_PROPOSAL = CANDIDATE_FOR_REVIEW (doc 84 §2–§4)
B2_G2_REUSE_SECURITY_REPORT = CANDIDATE_FOR_REVIEW (doc 84 §5)
B2_LINK_TYPED_SOURCE = DECISION_PENDING (doc 84 §6 — recomendação: B2 inicial sem links navegáveis)
B2_RUNTIME_IMPLEMENTATION = BLOCKED_UNTIL_G1_G2_G3
B2_RUNTIME_DIFF = NONE
C_AND_D_STRUCTURED_UI = OUT_OF_SCOPE_OF_B2
PHASE_PROGRESSION = NONE
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
DEPLOY = NOT_PERFORMED
NEXT_BOUNDED = B2_G1_PRESENTATION_V2_CONTRACT_AND_G2_SECURITY_REUSE_PROOF
```

Este documento é planejamento completo para decisão e execução futura, mas **não** afirma que G0/G1/G2 estejam aprovados. Não fechar gap por inferência. O ledger só deve registrar outcome real após review/aceite, preservando a sequência de autoridade do doc 16.

## 16. Referências verificadas

- Autoridades: `16, 50, 17, 49, 51, 52, 21, 20, 25`; Product Spec `24`; specs `69, 70, 73, 75, 79, 80, 82`; execution ledger.
- Proposta G1/G2 (candidata à revisão): [`84 — Proposta presentation.v2 e Reuse/Security Review`](./84-presentation-v2-contract-and-markdown-security-g1-g2-proposal.md).
- Backend: `delia-api/app/application/interaction/presentation.py`.
- Frontend: `plugins/delia/src/api/presentation.ts`; `interactionClient.ts`; `ui/DeliaAssistantMessage.tsx`; `ui/ConversationTimeline.tsx`; `index.css`.
- Shared: `plugins/plugin-ui/src/components/markdown/MarkdownDocument.tsx`, `markdownDocumentModel.ts`, seus testes; `rich-text/richTextHtmlFormat.ts`; `collaboration/messageThreadMarkdown.ts`; `data/DataTable.tsx` e `charts/` somente para exclusão de escopo.


## Product Master — decisão explícita de desacoplamento de links e escopo B2 (2026-10-22)

**Decisão de produto mais recente — requer reconciliação formal com CP-333 e D1/D6/D7 anteriores; não alterar retroativamente as decisões congeladas.** O Product Master decidiu que a emissão de **links internos governados pela DÉLIA não é pré-requisito para implementar o núcleo do Markdown B2**. O módulo deve avançar com formatação textual segura, sem que DÉLIA se torne owner do controle de acesso ou mantenha allowlist privada de rotas/permissões da plataforma.

**Fronteiras obrigatórias:**
- **DÉLIA** = composição/representação de conteúdo, evidência e referência; nunca outorga, confirma nem armazena permissão Core/Domain para abrir telas.
- **Core API** = autoridade de aplicações/rotas/RBAC e decisão de acesso à área interna; **Domain API** preserva regras e autorização final do recurso de negócio. **Portal** = host/navegação/contexto, sujeito às verificações efetivas das APIs. A mera exibição do link não é autorização nem garante que o destino será acessível.
- **Links internos Minha DELPI:** podem ser exibidos como referências, quando fornecidos por contrato legítimo; clique e navegação dependem da capacidade do Portal e da autorização live Core/Domain no destino. **Não** criar um catálogo de links privados, mecanismo de permissão, bypass, pré-autorização ou validação de acesso paralela na DÉLIA. Não inventar rota a partir de IDs ou nomes de ferramentas. Binding L1 de destinos tipados pode evoluir futuramente, sem bloquear núcleo B2.
- **Links públicos de internet:** podem continuar como links no conteúdo Markdown quando a URL vier de fonte admissível, o destino for validado e a política de segurança permitir (HTTPS, prevenção de schemes perigosos, navegação externa segura, no fabricated model link, sem confiar automaticamente em URLs de MCP/web). Link da internet **não** ganha automaticamente confiança, endosso, autorização nem classificação de evidência. Precisão de procedência e política de admissão ainda exigem contrato.
- **Primeira entrega B2:** headings, ênfases, listas, citações, inline/fenced code inerte e demais tokens *já admitidos* pelo contrato textual; não incluir automaticamente tabelas/graphs de outra fase nem novos nós fora de allowlist. Não bloquear implementação somente por ausência do binding L1 interno. Links sem admissão segura permanecem texto inerte.
- **Futuro:** evoluir integração de navegação com contratos oficiais do Portal/Core/Domain, sem criar acoplamento ou RBAC próprio na DÉLIA. Uma tela pode ser inacessível para o usuário; isso é resultado válido e controlado pela autoridade do destino.

**Impacto sobre decisões anteriores:** este direcionamento revisa a dependência histórica que condicionava **todo** Markdown B2 à emissão de links governados internos. Não equivale à aprovação implícita de L3 ou à remoção definitiva de links; é uma nova decisão explícita do Product Master a ser reconciliada por Architecture/Coordination com CP-333, D1/D6/D7, docs 82/84 e gates G1/G2/G3. Em caso de incompatibilidade com autoridade superior, **STOP → ARCHITECTURE_DECISION_REQUIRED**, não alterar silenciosamente o status. `CP-333=PLANNED_NOT_PASS`; `B2_RUNTIME=OFF`; `G3_TASK_BRIEF_APPROVAL=PENDING`; `NO_RUNTIME_CHANGE`.

**Próximo bounded:** revisão de contrato para diferenciar external-public link admission de internal-navigation reference, ajustar os AC/RQ afetados sem apagar requisitos históricos, comprovar reuso Portal/Core, registrar evidência e somente então solicitar liberação do brief de implementação B2 no HEAD.
