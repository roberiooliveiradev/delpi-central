# 82 — DÉLIA: Conversation Rich Content & Structured Presentation

**Status:** `PRODUCT_UX_SPEC / B2_TEXTUAL_CP-333_MAPPED / B2_BOUNDED_CONDITIONAL_AUTHORIZATION / RUNTIME_GATES_OPEN / C_D_E_TRACEABILITY_GAP_OPEN`  
**Data:** 2026-10-16  
**Task:** `DELIA-UX-CONVERSATION-RICH-CONTENT-DOCUMENTATION-01`  
**Escopo:** especificação documental completa da evolução da apresentação de respostas. Nenhum runtime, schema, API ou componente foi criado por este documento.  
**Referência de inventário:** `58d53f52ca0868983c932a2015f2fedca02102ca`; revalidado o contrato DÉLIA e a matriz de requisitos em `821f0cd78ce75a8a703a7dc9d95144c6303bf854`. Este arquivo é publicado diretamente na `main`; revalidar HEAD na implementação.

> **DECISÃO VIGENTE DO PRODUCT MASTER — 2026-10-22 (substitui o bloqueio histórico por L1 interno):** Markdown B2 textual seguro pode avançar sem capability→URL interna ou sistema de links privados administrado pela DÉLIA. Links públicos HTTPS só se houver fonte admitida e validação de scheme/destino; URLs inventadas pelo modelo, advindas de metadados não confiáveis ou não verificadas são texto inerte. Referências internas são opcionais e apenas quando contratualmente publicadas; Portal navega, Core decide RBAC/rotas e Domain API decide acesso final ao recurso. A DÉLIA não pré-autoriza navegação, não cria RBAC/allowlist privada e não infere rotas por ID. O L1 interno permanece evolução futura independente, não gate do núcleo Markdown B2. **G3 ainda exige brief formal aprovado e os gates de contrato/segurança aplicáveis; CP-333 continua não PASS; runtime não foi alterado.** Histórico de 2026-10-16 mantido como evidência, não como direção vigente nesse ponto. Ver decisão de produto no doc 83 e reconciliação de 2026-10-22.

## 1. Objetivo de produto

DÉLIA deve apresentar respostas operacionais legíveis, seguras e verificáveis, evoluindo de texto literal para formatação tipográfica rica e, somente quando contratos e fases permitirem, blocos tipados de tabelas, métricas, gráficos e outras experiências. A direção é **chat-first, não dashboard**: texto explicativo é primário; elementos estruturados aparecem quando agregam valor e possuem evidence.

Este documento originou a **especificação-alvo e o gate de implementação futura**, sem autorização de runtime por si. **Atualização 2026-10-16:** a direção de produto B2 D1–D12 e autorização *bounded condicional* estão registradas na [spec 83](./83-conversation-markdown-b2-contract-and-implementation-plan.md), com `CP-333` na matriz 25. Isso **não** dispensa contract freeze G1, Security/Reuse G2, brief G3 e aceite independente G4; `presentation.v1` segue o runtime atual até implementação comprovada. Não reutilizar Minha DELPI Chat como runtime.

## 2. Precedência, authorities e relação com outras specs

Reanchor obrigatório: HEAD/git status → Project Instructions/.cursor → 16 (sequência) → 50 (standalone) → 17 (owners/contracts) → 49 (patterns) → 51 (baseline) → 52 (bootstrap) → 21 (state) → 20 (tests) → 25 (traceability) → arquitetura técnica → product spec → 69 (conversation), 70 (activity), 73 (chat-first anatomy), 75 (assistant message), 79 (activity), 80 (evidence) → ledger.

Em divergência seguir autoridade superior; `STOP → EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`. Este documento complementa 73/75, não os substitui e não muda a ordem de fases. A spec 75 contém descrições históricas de provenance/meta row: a composição atual `EvidenceDetails`, sem `protocol` user-facing, prevalece como fato de implementação observado; reconciliar documentação por review sem ressuscitar o formato antigo.

## 3. Estado observado e limites factuais

**PROVEN no código do HEAD inventariado:**

- `plugins/delia/src/ui/DeliaAssistantMessage.tsx`: conteúdo principal `<p className="delia-turn__content">{displayContent}</p>`; React text inerte. Reutiliza `UnifiedAvatar`, `ActivityViewer`, `ConversationStatus`, `GovernedConfirmation`, `EvidenceDetails`, `MessageActionBar` e `IconButton`.
- `plugins/delia/src/index.css`: `white-space: pre-wrap`, `overflow-wrap: anywhere`, resposta aberta no canvas; full-page e dock usam a mesma composição.
- `plugins/delia/src/api/presentation.ts`: `presentation.version = "1"`, allowlist de blocos `text` e `notice(role="owner_hint")`, máximo de oito blocos e 16.384 caracteres por bloco; `reply|confirm|reject` são valores conhecidos, **não permissões**. Unknown kind/version degrada de forma neutra.
- `ConversationTimeline` é dona da ordenação e `role="log"`; não inferir que mensagem contém componentes rich.
- `plugins/plugin-ui/src/components/markdown/MarkdownDocument.tsx` + `markdownDocumentModel.ts`: **equivalente existente** para documentos Markdown/GFM, code fences e Mermaid; código utiliza HTML derivado e sanitização. Foi projetado para documentos, não está aprovado automaticamente para turnos DÉLIA.
- `plugins/plugin-ui/src/components/collaboration/messageThreadMarkdown.ts`: utilitários de conversão/preview de Markdown e rich text em mensagens de outro contexto, com dependências de menções/anexos; **não** portar lógica de Chat nem assumir adequação à DÉLIA.
- `plugins/plugin-ui/src/components/data/DataTable.tsx`: tabela genérica existente, com affordances de sorting/scroll/seleção; ainda precisa de adaptação e projeção de dados `read-only` para uso conversacional.
- `plugins/plugin-ui/src/components/charts/`: `ConfigurableSeriesChart`, `LineSeriesChart`, `BarSeriesChart`, `AreaSeriesChart`, `ChartViewShell`, `MultiTypeSeriesChart`, primitives adicionais e componentes responsivos existentes. Há **capacidade visual compartilhada**, não comprovação de contrato de dados/chart na DÉLIA.

**Não comprovado:** Markdown como conteúdo autorizado de turnos DÉLIA, typed rich blocks no `presentation.v1`, backend produzindo tabelas/gráficos, renderer conversacional, segurança end-to-end do reuse, pipeline de metrics, URLs legitimamente publicadas, autorização da fase e deploy. Classificar `TO_INVENTORY / PLANNED / TARGET`, nunca `PROVEN` por presença de código em outro owner.

## 4. Reuse-before-design e responsabilidades

| Candidato | EXISTING_EQUIVALENT | REUSE_DECISION | Evidência / condição |
|---|---|---|---|
| `DeliaAssistantMessage` | `YES` (local DÉLIA) | `REUSE` | Manter a composição local e o contrato atual; não criar shell paralelo |
| `UnifiedAvatar`, `ActivityViewer`, `ConversationStatus`, `GovernedConfirmation`, `EvidenceDetails`, `MessageActionBar` | `YES` | `REUSE` | Componentes compartilhados já consumidos pela DÉLIA |
| `MarkdownDocumentView` + `buildMarkdownDocumentModel` | `YES` (uso documental) | `PENDING` | Avaliar `REUSE` ou `EXTEND` somente após comprovar segurança, anchors, Mermaid e adequação ao turno |
| `messageThreadMarkdown` | `YES` (uso em colaboração) | `PENDING` | Compatibilidade e dependências de menções/anexos `TO_INVENTORY`; não importar runtime do Chat |
| `DataTable` | `YES` (visual genérico) | `PENDING` | Decidir `REUSE` ou `EXTEND` após contrato tipado, read-only e UX conversacional |
| Gráficos existentes em `plugin-ui` | `YES` (visuais genéricos) | `PENDING` | Decidir `REUSE` ou `EXTEND` após contrato de séries/métricas e QA no dock |
| Novo registry/engine de UI | `TO_INVENTORY` | `PENDING` | Nenhum mecanismo `NEW` autorizado; só considerar após Abstraction Gate e comprovação de necessidade real |

`EXISTING_EQUIVALENT` usa exclusivamente `YES | NO | TO_INVENTORY`. `REUSE_DECISION` só está congelada nos itens decididos (`REUSE | EXTEND | NEW`); `PENDING` **não** é um quarto valor decisório, mas indicação de que não há decisão e o gate continua aberto. A existência de um renderer em outro contexto prova capacidade visual parcial, não a adequação à DÉLIA. Não criar abstrações novas com base em equivalência parcial.

Owners: `plugin-ui` = chrome/apresentação genérica; `plugins/delia` = composição e projeção user-facing; DÉLIA backend = decisões de apresentação contratual dentro de sua boundary; Domain API = dados e regra final; Core = AuthZ; providers/MCP = interoperabilidade e resultados não confiáveis; Automation Hub = execução técnica. Nunca modelo/metadata/DOM viram authority.

## 5. Princípios de apresentação

1. Resposta é sequência ordenada de conteúdo comunicável, com fallback legível; renderização **não** muda fatos, números, unidades ou estado.
2. `text` literal continua seguro e compatível. **Não reinterpretar silenciosamente payload legado como Markdown**: frases com `*`, `_`, `#`, tags, IDs ou códigos podem ser dados literais.
3. Markdown seguro serve a **prosa**: headings controlados, parágrafos, ênfase, listas, blockquotes, code inline/fenced, links validados e tabelas textuais quando expressamente contratadas; extras (imagens, Mermaid, HTML inline, embeds) ficam OFF até decisão explícita.
4. Elementos estruturados (table/chart/metric) são **props/dados tipados**, não HTML/SVG/JS/CSS/JSON arbitrário interpretado como instrução.
5. O modelo pode propor forma de apresentação; renderização precisa de contrato, dados admitidos e evidence. Conteúdo gerado nunca torna `HYPOTHESIS/PREDICTION` em `FACT`.
6. Preservar `ActivityViewer != EvidenceDetails != ConversationStatus != GovernedConfirmation != MessageActionBar`.
7. Mesmo MFE e componentes em full-page/dock; sem segunda stack ou renderização especial por provider.

## 6. Anatomia visual futura

```text
[DÉLIA avatar] DÉLIA
               ActivityViewer?            [observado]
               ConversationStatus?        [estado semântico]
               Rich prose/content         [primeiro plano]
               Structured block(s)?       [table / metric / chart, future gated]
               owner_hint?                [notice real]
               GovernedConfirmation?     [contrato real]
               EvidenceDetails?           [fonte, observado em, limites]
               MessageActionBar?          [ações secundárias reais]
```

Espaço de leitura confortável, tipografia de alto contraste, títulos subordinados ao contexto do turno, margin rhythm por bloco, tabelas com scroll horizontal intencional no dock, gráficos com fallback textual/tabela, code com scroll e cópia apenas quando aplicável. Nenhum card pesado em cada nível. Preservar estado crítico visível; não ocultar material limitations em disclosure inapropriado.

### 6.1 Tipografia — alvo

- Parágrafos com `line-height` legível, whitespace coerente, espaçamento interparágrafo diferenciado do espaço entre status/evidence/ações.
- Heading dentro do turno nunca compete com header da página ou introduz `h1` global repetido.
- Listas com marcadores corretos e indent responsivo; textos longos/URLs/códigos não causam overflow.
- Inline code e blocos fenced com fonte monoespaçada, contraste e scroll; conteúdo deve permanecer copiável.
- Tabela Markdown de prosa é diferente de tabela de dados operacional (requisitos de tipos, unidades, semântica e fonte).

### 6.2 Table — target sem contrato executável

Dados tabulares read-only com colunas, tipos, unidades e linhas bounded; cabeçalhos acessíveis, ordenação apenas quando realmente suportada, estados empty/error, scroll no dock. Não oferecer edit/export/download/filtro apenas por existir affordance no componente compartilhado. DataTable é primeira hipótese de REUSE, sujeita a teste do modo de apresentação.

### 6.3 Chart — target sem contrato executável

Charts exigem tipo aprovado, séries categóricas/temporais, eixo/unidade, locale, fórmula e definição de métrica de owner, período/grain, freshness, lineage e limites. Não derivar números do texto livre; não inventar série faltante. Exibir tabela de dados alternativa e títulos/descrições. Proporção e layout fluidos full-page/dock. Em C5/C6/C7, visualização nunca equivale a autorização/ACT.

### 6.4 Metrics e outros blocos — target

KPI/métrica tem nome, unidade, valor, precisão/escala, período, origem, versão de definição e status epistêmico; proibir tendências, percentuais e cores inferidos de valores sem cálculo/regra legítima. Imagens, arquivos, mapas, cards de entidade, quizzes e controles interativos ficam fora do primeiro slice e requerem specs/contracts próprios. `iframe`, scripts e HTML arbitrário são proibidos.

## 7. Contract-first — questões a decidir, não schema congelado

O contrato existente permanece `presentation.v1`. Antes de futura extensão:
- Definir se formato rich é campo additive explicitamente tipado, nova versão, ou capability de projection distinta; **não** decidir por conveniência de frontend.
- Owner, consumers, OpenAPI/JSON Schema quando aplicável, discriminação de tipo, request/response, bounded size, max rows/series/blocks, validation, erros, fallback desconhecido, versionamento/compatibilidade, observabilidade.
- Fonte de confiança do conteúdo textual; o backend distingue `PLAIN_TEXT` de `MARKDOWN_SAFE` explicitamente quando aprovado. Fallback legacy sempre texto literal.
- Dados de tabelas/gráficos ligados a source references e definitions oficiais; separar narrativa do dataset e evitar data leakage.
- `read != write`, `PREPARE != ACT`, `simulate != apply`; interação visual não implica `allowed_interactions` para business action.
- Não emitir `chart/table` sob `presentation.v1` atual. Frontend não deve interpretar unknown block como autorização de renderer novo.

**Exemplo conceitual não executável (somente shape ilustrativo, NÃO aprovado):**

```json
{
  "hypothetical_content": [
    {"kind": "rich_text", "format": "markdown_safe", "source": "..."},
    {"kind": "table", "dataset_ref": "authoritative-reference"},
    {"kind": "chart", "dataset_ref": "authoritative-reference", "view": "bar"}
  ]
}
```

Este exemplo **não** é payload válido da DÉLIA e não autoriza sua implementação.

## 8. Segurança e privacidade

- UNTRUSTED: model text, Markdown, provider output, MCP results, tool schemas, URLs e metadata. Bloquear raw HTML, script/event handler, `javascript:`, unsafe `data:` e inline injection; sanitização/allowlist baseada em testes adversariais.
- `dangerouslySetInnerHTML` já existe no componente documental compartilhado após sanitização. Reuso na conversa exige avaliação de sanitizer/contexto, testes anti-XSS e CSP; nunca passar HTML direto de LLM/provider.
- Links somente por schemes/hosts aprovados conforme contrato; `rel="noopener noreferrer"` ao abrir nova janela; sem navigation hijack do Portal/hash. Imagens externas, attachment refs e Mermaid permanecem desabilitados no primeiro slice até política própria.
- Max length, max nesting, resource bounds, parser DoS e conteúdo extremamente longo; impedir DOM explosion.
- Sem secrets/tokens, raw identity ou internal provider IDs no prompt/render/logs; telemetry minimizada.
- Preserve leitura de texto hostil como texto inerte e a possibilidade de copiar texto visível sem criar ação de negócio.
- Sanitizer confiável em reutilização é hipótese a testar, não `PASS` automático.

## 9. Accessibility, responsiveness e themes

Matriz exigida quando implementar: full-page, dock real, light/dark, 320/420px, zoom 200%, fonte aumentada, teclado/focus-visible, screen reader, nested lists, wide tables, long links, code blocks, empty/partial/invalid datasets, reduced motion.

Headings sem salto de hierarquia; tabelas com `caption`/headers quando apropriado; chart acessível por summary e tabular equivalent; não depender apenas de cores; disclosures e cópia navegáveis por teclado. Roll/scroll da timeline não deve ser quebrado por overflow de child. Dock não cria renderer paralelo.

## 10. Etapas bounded futuras (NÃO autorizadas por esta spec)

**A — Inventory and contract decision (primeira):** Devin ou Cursor reancora HEAD e reexecuta inventário de `MarkdownDocumentView`, `messageThreadMarkdown`, `DataTable`, charts, exports/styles, DÉLIA adapter/backend, 73/75/25/ledger. Produz Reuse Gate itemizado, CP/RQ/AC e ADR/decision request se extensão material for exigida. Sem implementação até aceite de contrato.

**B1 — Refinamento tipográfico do texto literal (se autorizado separadamente):** ajustar somente CSS/chrome local e, quando necessário, tokens ou estilos já existentes no `plugin-ui`; manter `displayContent` como React text inerte e `presentation.v1` intacto. Não executar parse Markdown, `innerHTML`, reconversão de quebras, alteração de payload nem inferência de formato. Exigir QA full-page/dock/light/dark/zoom/teclado e testes de regressão; esse slice visual **não depende** do backend de gráficos/tabelas, mas ainda exige brief/CP/AC e autorização de execução.

**B2 — Markdown semântico seguro (somente após gate próprio):** decidir contrato de formato explícito e compatibilidade com o legado antes de renderizar Markdown. Revalidar segurança, sanitização, links, conteúdo hostil, limitações e adequação do `MarkdownDocumentView` ou outro mecanismo legítimo a turnos DÉLIA; reutilizar ou estender `plugin-ui` após Reuse Gate. Desconhecido/sem formato aprovado continua texto literal. Nenhum `HTML` bruto de provider/model é executado.

**C — Structured tables, se autorizado:** contrato typed e dataset evidence antes da UI, REUSE DataTable ou primitive apropriado; sem affordances falsas.

**D — Charts/metrics, se autorizado:** contrato e owners de séries/métricas, REUSE charts genéricos via projection/adapters, fallback acessível e testes de outcome de dados.

**E — Interatividade avançada, fase própria:** somente com action/authorization gates completos.

Não acoplar B1/B2 a C/D: B1 pode ser exclusivamente render-only; B2 depende de contrato e Security Review próprios. Tabelas e gráficos exigem fonte e contrato tipado adicionais.

## 11. Requirements candidatos para formalização

Estes IDs **locais de planejamento**, não substituem `CP-*` canônicos nem são RQs de execução autorizada:

| ID | Requisito-alvo | Critério futuro |
|---|---|---|
| RQ-RICH-01 | Preservar texto legado literal e fallback neutro | Testes de literalidade e conteúdo adversarial |
| RQ-RICH-02 | Rich prose só por format explícito governado | Nenhuma heurística `plaintext→markdown` |
| RQ-RICH-03 | Tipografia consistente em full-page/dock/light/dark | Browser QA visual em matriz |
| RQ-RICH-04 | Reuse de componentes legítimos | Diff sem renderer/table/chart duplicado |
| RQ-RICH-05 | Conteúdo externo seguro | XSS/URL/CSP/DoS gates |
| RQ-RICH-06 | Table/chart somente com dados tipados de fonte legítima | Dataset, units, lineage, limits e fallback |
| RQ-RICH-07 | Sem AuthZ/ACT pelo renderer | Cenários negativos e ausência de side effect |
| RQ-RICH-08 | Acessibilidade e degradação | SR, teclado, zoom, overflow, reduced motion |
| RQ-RICH-09 | Compatibilidade contratual | Versioned schema, unknown kind safe, old clients |
| RQ-RICH-10 | Provar testes/evidence no SHA aceito | Coverage + security + browser QA sem falso PASS |

### 11.1 Rastreabilidade canônica — lacuna aberta

**`TRACEABILITY_GAP = OPEN`** para o requisito específico de renderização de Markdown seguro em respostas DÉLIA e apresentação estruturada de tabelas/gráficos: o `25-requirements-traceability.md` consultado no HEAD de publicação não contém um CP que cubra explicitamente essa capability end-to-end. Isso é um **requisito de produto ainda sem rastreabilidade própria**, não prova de ausência de direção UX (já registrada em 69/73/75).

| CP existente | Relação transversal | Por que não substitui a nova rastreabilidade |
|---|---|---|
| `CP-001` | Experiência DÉLIA no Portal | Não especifica formato/renderização de conteúdo |
| `CP-015` | Análise/comparação de dados com evidence | Não estabelece contrato de apresentação de tabela/chart |
| `CP-027` | Resumo/relatório grounded | Não estabelece Markdown tipado e renderer conversacional |
| `CP-093` | Referência de evidências | Não autoriza transformar source result em UI estruturada |
| `CP-135` | Modelo transversal de Error/Result | Não versiona rich presentation |
| `CP-196` | Conteúdo externo não confiável | Security gate, não capability rich UI |
| `CP-270` | Personalização de conteúdo/formato | Preferências não concedem schema, permission ou renderer |

**Owner para resolução:** `Architecture / Coordination` com `Frontend / MFE / UX`, `Backend / Application`, `Security` e owner de métricas/Domain APIs conforme o bounded slice. O owner deve decidir formalmente se existe CP canônico que de fato cubra a evolução, se há `DISCOVERED_REQUIREMENT` que exige novo CP, ou se a capability permanece fora do escopo de uma fase; atualizar a matriz 25 via processo governado. **Não criar CP ou declarar o gap fechado neste commit documental.**

**STOP de implementação:** enquanto o `TRACEABILITY_GAP` material estiver aberto, nenhum prompt Devin de B2/C/D/E pode tratar esses requisitos como aprovados. B1 somente poderá avançar quando tiver escopo de UX/tipografia rastreado e autorização própria no HEAD real. Nenhum `RQ-RICH-*` desta spec equivale a um `CP-*` aceito.

### 11.2 Supersedência bounded do gap Markdown por decisão D12 — 2026-10-16

A §11.1 acima documenta corretamente o **gap no HEAD original da spec 82**. Após aprovação expressa do Product Master em D12, a matriz canônica [25](./25-requirements-traceability.md) recebeu **`CP-333`**, owner DÉLIA API/Application + DÉLIA MFE/Portal + plugin-ui + Security, com requisito específico de **Markdown textual conversacional** via contrato-alvo `presentation.v2`. As doze decisões e os gates estão na [83](./83-conversation-markdown-b2-contract-and-implementation-plan.md).

```text
B2_MARKDOWN_CP_TRACEABILITY = CP_333_MAPPED
B2_PRODUCT_DECISIONS = D1_TO_D12_APPROVED
B2_BOUNDED_SCOPE_AUTHORIZED = CONDITIONAL_YES
B2_PRESENTATION_CONTRACT = V2_TARGET_G1_PENDING
B2_SECURITY_REUSE = G2_PENDING
B2_RUNTIME_IMPLEMENTATION = BLOCKED_UNTIL_G1_G2_G3
CP_333_STATUS = PLANNED_NOT_PASS
C_D_E_TABLE_CHART_METRIC_TRACEABILITY_GAP = OPEN
C3_EXECUTED = NO
PHASE_PROGRESSION = NONE
```

**Escopo estrito de CP-333:** conteúdo Markdown textual completo e controlado, links internos/externos autorizados, cópia legível, fallback diferenciado, fonte independente em `EvidenceDetails`, apresentação adaptativa em full-page/dock e compatibilidade de versões. Não cobre tabelas estruturadas/GFM, métricas, charts, HTML arbitrário ou Mermaid; a lacuna dessas capacidades segue sem CP próprio. `C3-STAGE-02-B2` do ledger é outra linha de trabalho e não recebe autorização por esta decisão. A redação original §11.1 e o bloco §13 abaixo permanecem **evidência histórica da publicação**, não estado atual dos gates de B2; nenhuma evidência de implementação/teste foi produzida por esta reconciliação.

## 12. Gates de aceite para Devin

- Reanchor HEAD/local status e authorities/spec/ledger; nova evidence pode tornar esta direção `SUPERSEDED`.
- `EXISTING_EQUIVALENT = YES|NO|TO_INVENTORY` e `REUSE_DECISION = REUSE|EXTEND|NEW` por renderer/visual/contract.
- Contract/security/abstraction/phase gates aprovados antes do diff.
- RQ/AC atômicos no brief da task, com CP rastreável; reportar `IMPLEMENTED/PARTIAL/NOT_IMPLEMENTED/BLOCKED/NOT_APPLICABLE`.
- Unit + component + integration + malicious payload + performance bounds + a11y + browser QA real + typecheck + build + federation, em SHA/config conhecido.
- Validar `PRESENTATION_CONTRACT_VERSION`, status/provenance/limitations/confirmation/copy/activity e `role=log` sem regressão.
- Residual search de renderers duplicados, bypass de sanitizer, HTML injection, links perigosos, providers e old contract references.
- Prova de business outcome não é `rendered successfully`: métricas/tabelas devem corresponder aos dados autoritativos; estados de uso sem side effect.
- Relatório final obrigatório `DÉLIA EXECUTION REPORT`; implementação não se autoaceita.
- `STOP` se precisar alterar owner, mudar fase, inventar schema, autoridade paralela ou descongelar decisão sem autorização.

## 13. Limites e decisão documental

```text
DOCUMENTATION = RECORDED_FOR_COORDINATION_REVIEW
PRODUCT_INTENT = TARGET
DÉLIA_PLAIN_TEXT_RENDERER = PROVEN
PLUGIN_UI_MARKDOWN_DOCUMENT_RENDERER = PROVEN (document context only)
PLUGIN_UI_DATA_TABLE_AND_CHART_VISUALS = PROVEN (other consumers)
DELIA_RICH_MARKDOWN_IN_TURNS = PLANNED
DELIA_TYPED_TABLE_CHART_CONTRACT = TARGET
NEW_RENDERER_OR_CHART_FRAMEWORK = NOT_AUTHORIZED
EXISTING_EQUIVALENT = ITEMIZED_IN_SECTION_4
REUSE_DECISION_FOR_CURRENT_CHROME = REUSE
RICH_REUSE_GATE = PENDING
TRACEABILITY_GAP = OPEN
PHASE_PROGRESSION = NONE
RUNTIME_DIFF = NONE
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
```

**Next bounded step:** Architecture / Coordination resolve o `TRACEABILITY_GAP` e decide escopo/CP/owner de B1 e B2 antes de qualquer brief de implementação. A revisão de compatibilidade com `MarkdownDocumentView`, `DataTable` e charts será refeita no SHA do executor. Esta spec não é ordem de execução nem fonte de permissão.

## 14. Referências

- `16-execution-master-plan.md`; `17-component-and-contract-map.md`; `20-testing-and-acceptance-matrix.md`; `25-requirements-traceability.md`; `evidence/execution-ledger.md`.
- `73-chat-first-visual-identity-and-message-anatomy-specification.md`, `75-assistant-message-visual-specification.md`, `79-conversation-activity-summary-visual-specification.md`, `80-evidence-details-provenance-visual-specification.md`.
- Código verificado: `plugins/delia/src/ui/DeliaAssistantMessage.tsx`, `plugins/delia/src/api/presentation.ts`, `plugins/plugin-ui/src/components/markdown/`, `plugins/plugin-ui/src/components/collaboration/messageThreadMarkdown.ts`, `plugins/plugin-ui/src/components/data/DataTable.tsx`, `plugins/plugin-ui/src/components/charts/`.
