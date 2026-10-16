# 83 — DÉLIA: Plano B2 de Markdown Seguro em Respostas Conversacionais

**Status:** `PLAN_ONLY / COORDINATION_REVIEW_REQUIRED / IMPLEMENTATION_NOT_AUTHORIZED`  
**Data:** 2026-10-16  
**Task documental:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-PLANNING-01`  
**Parent:** [82 — Conversation Rich Content & Structured Presentation](./82-conversation-rich-content-and-structured-presentation-specification.md)  
**Produto:** DÉLIA standalone; não é Minha DELPI Chat, nem compartilha seu runtime/tabelas/agents/services.  
**Snapshot de descoberta:** branch `main`, HEAD reancorado em `b0b4f8c028f706d2a4bd47e70690ea07badea089`, com rechecagem do HEAD antes da publicação. O HEAD de implementação deve ser revalidado.  
**Natureza:** planejamento contratual, de segurança, UX, implementação e testes; este documento não altera código, contrato, requisitos CP, ledger de execução, fase ou permissão de execução.

## 0. Resumo executivo e decisão proposta

Entregar B2 como **renderização opcional e explicitamente contratada de Markdown seguro no corpo das respostas da DÉLIA**, sem reinterpretar as mensagens literais existentes. O B2 é independente de gráficos, tabelas estruturadas, métricas e HTML arbitrário. Reutilizar, quando aprovado por inventário e Security Review, os primitives e mecanismos existentes em `@delpi/plugin-ui`. A DÉLIA mantém a composição local de `DeliaAssistantMessage`; não inaugurar um segundo framework de rich UI.

**Proposta de sequência:** Coordenação resolve rastreabilidade/fase/owner → contrato de origem+formato e compatibilidade → inventário e política de renderização segura → tests RED → menor implementação no owner correto → validação integrada e browser QA → review e aceite independentes.

**Gate atual:** `TRACEABILITY_GAP=OPEN` (spec 82 seção 11.1); `B2_IMPLEMENTATION_AUTHORIZED=NO`. Este plano **não** resolve esses gates sozinho e não é prompt de implementação para o Devin. O aceite de B1 tipográfico não libera B2, nem o CP-001 é suficiente, isoladamente, para um novo contrato Markdown.

## 0.1 Decisões vinculantes do Product Master (2026-10-16)

As decisões a seguir foram expressamente aprovadas pelo Product Master no contexto de definição de B2. São **decisões de direção do produto**, sujeitas aos gates normativos de traceability, owner, security, contract freeze e implementação. Nenhuma delas equivale à autorização de alterar runtime, `25` ou `presentation.v1` por inferência.

| ID | Decisão do Product Master | Estado | Implicação congelada |
|---|---|---|---|
| `B2-PD-01` | Markdown textual **com links clicáveis seguros** | `APPROVED_PRODUCT_DIRECTION` | Link somente quando URL legítima, validada e autorizada por contrato; sem link inventado, tracking ou navegação arbitrária |
| `B2-PD-02` | **`presentation.v2`** com formato explícito e transição segura de clientes | `APPROVED_PRODUCT_DIRECTION` | **Não** estender informalmente `presentation.v1`; escolher schema/semântica/ciclo de rollout de v2 em G1. Como não há histórico conversacional durável implementado, não há migração de mensagens persistidas a planejar para o runtime atual; ainda testar versões coexistentes, sessões transitórias e fallback |
| `B2-PD-03` | **DÉLIA controla a produção de Markdown** a partir de conteúdo admitido e governado | `APPROVED_PRODUCT_DIRECTION` | MCP/providers/especialistas não controlam apresentação nem elevam texto a FACT. DÉLIA pode organizar visualmente dados aprovados sem inventar fatos, unidades, IDs ou autoridade |
| `B2-PD-04` | **Markdown textual completo e controlado** | `APPROVED_PRODUCT_DIRECTION` | Permitir headings subordinados, parágrafos, negrito, itálico, listas, citações, divisores, código inline/fenced e links seguros. Permanecem OFF: tabelas estruturadas/GFM tables, gráficos, métricas, imagens, Mermaid, HTML arbitrário, embeds e widgets |
| `B2-PD-05` | **Formatação automática, contextual, proporcional e adaptável ao pedido do usuário** | `APPROVED_PRODUCT_DIRECTION` | DÉLIA decide apresentação no seu boundary com base no objetivo e no conteúdo *admitido*: saudação simples → texto natural; itens/etapas → listas quando útil; explicações longas → seções moderadas; código técnico → bloco inerte apenas quando realmente pertinente. Usuário pode solicitar brevidade/detalhamento, sem mudar fatos, autoridade nem contratos |

**Ainda não decidido:** `B2-PD-06` — política de destinos permitidos para links seguros (internos ao ecossistema/externos verificados e como abrir); demais detalhes como limites exatos, subset do renderer, conteúdo do contrato OpenAPI, negociação entre versões e rollout.

**Separação de homônimos:** `B2` neste documento = **Markdown B2 da spec 82**, não `C3-STAGE-02-B2` registrado no ledger para governança de execução/ACT. Status e autorizações de uma trilha **não** se transferem à outra. Responder às decisões futuras no mesmo documento assim que aprovadas.

**Gates que permanecem abertos:** `TRACEABILITY_GAP=OPEN`, `CP_MAPPING=PENDING`, `PRESENTATION_V2_SCHEMA=TO_DESIGN`, `SECURITY_REUSE_GATE=PENDING`, `B2_IMPLEMENTATION_AUTHORIZED=NO`. Produto aprovado **não** é contrato implementado nem aceite de fase. O plano 83 prevalece como detalhamento B2 sob a autoridade superior 82/16/25.

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

**Estado no HEAD inventariado:** `TRACEABILITY_GAP=OPEN`. A matriz 25 possui CPs transversais relacionados, porém **nenhum CP comprovado que especifique Markdown seguro em turns da DÉLIA, wire format explícito, compatibilidade e renderer**. Os itens a seguir são **dependências**, não autorização substitutiva:

| CP | Relação | Limite |
|---|---|---|
| CP-001 | UX DÉLIA no Portal/full-page/dock | Não cobre novo schema/rich renderer |
| CP-015 | Análise e comparação grounded | Não autoriza formato Markdown |
| CP-027 | Resumo/relatório grounded | Não especifica renderer conversacional |
| CP-093 | EvidenceRef transversal | Evidence ≠ admissão de rich content |
| CP-135 | Error/Result model | Não versiona formato rich |
| CP-196 | External content untrusted | Security invariant sem contrato B2 |
| CP-270 | Personalização de conteúdo/formato | Preferência não autoriza conteúdo |

**Decision request para Architecture / Coordination:** (a) provar CP existente suficiente com texto/gate/evidence; ou (b) aprovar novo requisito CP na matriz 25, com owner/fase/AC; ou (c) declarar `OUT_OF_SCOPE_WITH_DECISION` para a fase. Registro de candidato local `B2-CP-CANDIDATE` é **identificador de planejamento, não ID CP válido**. Atualização de `25` precisa de decisão formal, não de inferência deste documento.

**Gate de desbloqueio:** `CP_MAPPING_APPROVED=YES` + `PHASE_BOUNDED_TASK_AUTHORIZED=YES` + `CONTRACT_DECISION_APPROVED=YES` + `SECURITY_REUSE_GATE_APPROVED=YES`; caso contrário, `STOP` antes de qualquer diff de B2. A autorização B1 sob CP-001 foi bounded e não se propaga para B2.

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

## 9. Plano bounded de execução (não autorizado ainda)

| Slice | Owner principal | Entregável de entrada | Ação bounded | Saída/gate |
|---|---|---|---|---|
| B2-G0 — Architecture/Traceability | Coordination + Product/Security | 82/83 + HEAD + 25 | Decidir CP, fase, RQ/AC, owner e autorização; resolver drift | Decisão canônica escrita ou STOP |
| B2-G1 — Contract Decision | DÉLIA API owner + Frontend + Security | G0 aprovado | Escolher format signal/version, producer, fallbacks, bounds, wire schema e compatibilidade | Contract/ADR congelado |
| B2-G2 — Reuse/Security Feasibility | plugin-ui + DÉLIA frontend + Security | G1 e código atual | Prova de reuse/extend, auditoria sanitizer e política por tipo | Reuse Decision + threat model + testes RED |
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

**G0 (autorização) — BLOCKING:** registro canônico em `25` ou decisão equivalente rastreável que explicite CP específico, fase e owner; autorização task bounded no `16`/ledger conforme processo vigente. Doc 83 não resolve G0 por si.

**G1 (contrato) — BLOCKING:** direção `presentation.v2` **já escolhida pelo Product Master**; falta congelar OpenAPI/schema/ADR, distinguir formato literal versus Markdown, DÉLIA como producer, compatibilidade old/new, fallbacks, URLs/links e limites. Não retomar aditivo v1 sem nova decisão explícita.

**G2 (segurança/reuse) — BLOCKING:** avaliação de sanitizer/renderer e escopo permitido; componente real e owner legítimos; no raw HTML, no provider tools as authority.

**G3 (execução) — BLOCKING:** brief Devin com RQ/AC/Critical mapping, SHA atual, staged steps e stop conditions; sem mudar controle do produto.

**G4 (QA/aceite) — BLOCKING:** testes, security e browser QA reais no SHA/config; reviewer independente emite `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**O que Architecture / Coordination deve devolver:**
1. `CP_MAPPING_DECISION` e eventual alteração na matriz 25 (com justificativa).
2. `B2_SCOPE_AUTHORIZED` e owner/fase/eventual restrição de rollout, no HEAD real.
3. `PRESENTATION_FORMAT_CONTRACT_DECISION` — implementar **a escolha de produto `presentation.v2`** em OpenAPI, com detalhes ainda sujeitos a G1; não escolher silenciosamente v1.
4. `REUSE_DECISION` final por componente, incluindo sanitizer/links.
5. `DELEGATED_IMPLEMENTATION_BRIEF_APPROVED` com gates e review owner.

Não se exige liberação de C/D (tabelas/gráficos) para um B2 estritamente textual.

## 14. Handoff futuro ao Devin — somente após G0/G1/G2

**Task futura sugerida:** `DELIA-UX-CONVERSATION-MARKDOWN-SAFE-B2-IMPLEMENTATION-01`. Sem autorização neste documento.

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
B2_LINK_DESTINATION_POLICY = PENDING_PRODUCT_DECISION_06
B2_RENDERER_SECURITY_FIT = TO_INVENTORY
EXISTING_EQUIVALENT = YES (shared markdown/document primitives)
REUSE_DECISION = PENDING_FOR_MARKDOWN_IN_DELIA
TRACEABILITY_GAP = OPEN
CP_MAPPING = PENDING
B2_IMPLEMENTATION_AUTHORIZED = NO
B2_RUNTIME_DIFF = NONE
C_AND_D_STRUCTURED_UI = OUT_OF_SCOPE_OF_B2
PHASE_PROGRESSION = NONE
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
DEPLOY = NOT_PERFORMED
NEXT = ARCHITECTURE_COORDINATION_B2_G0
```

Este documento é planejamento completo para decisão e execução futura, mas **não** afirma que G0/G1/G2 estejam aprovados. Não fechar gap por inferência. O ledger só deve registrar outcome real após review/aceite, preservando a sequência de autoridade do doc 16.

## 16. Referências verificadas

- Autoridades: `16, 50, 17, 49, 51, 52, 21, 20, 25`; Product Spec `24`; specs `69, 70, 73, 75, 79, 80, 82`; execution ledger.
- Backend: `delia-api/app/application/interaction/presentation.py`.
- Frontend: `plugins/delia/src/api/presentation.ts`; `interactionClient.ts`; `ui/DeliaAssistantMessage.tsx`; `ui/ConversationTimeline.tsx`; `index.css`.
- Shared: `plugins/plugin-ui/src/components/markdown/MarkdownDocument.tsx`, `markdownDocumentModel.ts`, seus testes; `rich-text/richTextHtmlFormat.ts`; `collaboration/messageThreadMarkdown.ts`; `data/DataTable.tsx` e `charts/` somente para exclusão de escopo.
