# 82 — DÉLIA: Conversation Rich Content & Structured Presentation

**Status:** `PRODUCT_UX_SPEC / IMPLEMENTATION_NOT_AUTHORIZED`  
**Data:** 2026-10-16  
**Task:** `DELIA-UX-CONVERSATION-RICH-CONTENT-DOCUMENTATION-01`  
**Escopo:** especificação documental completa da evolução da apresentação de respostas. Nenhum runtime, schema, API ou componente foi criado por este documento.  
**Referência de inventário:** `58d53f52ca0868983c932a2015f2fedca02102ca`; branch documental iniciada em `47f4017551e767371db18d6ee993c37878075f42`. Revisar HEAD na implementação.

## 1. Objetivo de produto

DÉLIA deve apresentar respostas operacionais legíveis, seguras e verificáveis, evoluindo de texto literal para formatação tipográfica rica e, somente quando contratos e fases permitirem, blocos tipados de tabelas, métricas, gráficos e outras experiências. A direção é **chat-first, não dashboard**: texto explicativo é primário; elementos estruturados aparecem quando agregam valor e possuem evidence.

Este documento é uma **especificação-alvo e um gate de implementação futura**, não autorização para o Devin alterar o backend, `presentation.v1`, o planner ou executar ações. A futura task precisa de novo reanchor, owner/contract freeze, CP/RQ rastreáveis, acceptance e autorização explícita. Não reutilizar Minha DELPI Chat como runtime.

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

| Candidato | Equivalente | Reuse decision preliminar | Condição |
|---|---|---|---|
| DeliaAssistantMessage | YES_LOCAL | KEEP_LOCAL | DÉLIA mantém semântica e slots; não criar shell paralelo especulativo |
| UnifiedAvatar, ActivityViewer, ConversationStatus, GovernedConfirmation, EvidenceDetails, MessageActionBar | YES | REUSE | Comportamentos, owners e presentation atuais intactos |
| MarkdownDocumentView + buildMarkdownDocumentModel | YES, document-grade | REUSE_OR_EXTEND_TO_VALIDATE | Investigar limites de segurança, semântica, anchors, Mermaid e estilos no turno; não acoplar editor/document navigation à conversa |
| messageThreadMarkdown | PARTIAL | TO_INVENTORY | Inventariar dependências de attachment/mention; não copiar frontend de Chat |
| DataTable | YES, genérico | REUSE_OR_EXTEND_TO_VALIDATE | Somente com dados tipados, bounded e modo read-only; evitar recursos falsamente habilitados |
| Charts de plugin-ui | YES, visual | REUSE_OR_EXTEND_TO_VALIDATE | Aprovação de shape de dados, unidades, semântica, acessibilidade, formato compacto e source/evidence |
| Novo registry de UI/renderer dinâmico | TO_INVENTORY | DO_NOT_CREATE_NOW | Novo mecanismo exige Abstraction Gate e consumer/necessidade real |

`EXISTING_EQUIVALENT = YES` para renderizadores/visuais parciais já presentes. `REUSE_DECISION = REUSE/EXTEND CANDIDATE` condicionado a provas específicas; nenhuma autorização para `NEW` nesta etapa.

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

**B — Safe typography / Markdown, se autorizado:** consumidor DÉLIA distingue texto literal e rich text explicitamente por contrato; reutiliza ou estende renderer legitimo do `plugin-ui`; preserva fallback e segurança; implementa testes no SHA/config. Não alterar o formato de todas mensagens por heurística.

**C — Structured tables, se autorizado:** contrato typed e dataset evidence antes da UI, REUSE DataTable ou primitive apropriado; sem affordances falsas.

**D — Charts/metrics, se autorizado:** contrato e owners de séries/métricas, REUSE charts genéricos via projection/adapters, fallback acessível e testes de outcome de dados.

**E — Interatividade avançada, fase própria:** somente com action/authorization gates completos.

Não acoplar B a C/D; melhoria tipográfica pode ocorrer antes de backend de charts quando seu próprio contrato estiver autorizado.

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

**Traceability:** `25-requirements-traceability.md` deve ser consultado para mapear CP-*/identificar `TRACEABILITY_GAP` antes de implementar. Não criar CP automaticamente nesta task puramente documental.

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
DOCUMENTATION = RECORDED_FOR_REVIEW
PRODUCT_INTENT = TARGET
DÉLIA_PLAIN_TEXT_RENDERER = PROVEN
PLUGIN_UI_MARKDOWN_DOCUMENT_RENDERER = PROVEN_IN_DIFFERENT_CONTEXT
PLUGIN_UI_DATA_TABLE_AND_CHART_VISUALS = PROVEN_IN_DIFFERENT_CONTEXT
DELIA_RICH_MARKDOWN_IN_TURNS = NOT_PROVEN
DELIA_TYPED_TABLE_CHART_CONTRACT = NOT_PROVEN
NEW_RENDERER_OR_CHART_FRAMEWORK = NOT_AUTHORIZED
EXISTING_EQUIVALENT = YES_PARTIAL / REQUIRE_INVENTORY
REUSE_DECISION = PREFER_REUSE_OR_EXTEND_AFTER_GATES
PHASE_PROGRESSION = NONE
RUNTIME_DIFF = NONE
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
```

**Next bounded step:** revisão arquitetural/contratual e inventário de compatibilidade no HEAD de execução; somente depois gerar brief de implementação Devin. Esta spec não é ordem de execução.

## 14. Referências

- `16-execution-master-plan.md`; `17-component-and-contract-map.md`; `20-testing-and-acceptance-matrix.md`; `25-requirements-traceability.md`; `evidence/execution-ledger.md`.
- `73-chat-first-visual-identity-and-message-anatomy-specification.md`, `75-assistant-message-visual-specification.md`, `79-conversation-activity-summary-visual-specification.md`, `80-evidence-details-provenance-visual-specification.md`.
- Código verificado: `plugins/delia/src/ui/DeliaAssistantMessage.tsx`, `plugins/delia/src/api/presentation.ts`, `plugins/plugin-ui/src/components/markdown/`, `plugins/plugin-ui/src/components/collaboration/messageThreadMarkdown.ts`, `plugins/plugin-ui/src/components/data/DataTable.tsx`, `plugins/plugin-ui/src/components/charts/`.
