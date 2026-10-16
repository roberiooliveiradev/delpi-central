# 85 — Revisão independente de G1/G2: `presentation.v2` e Markdown B2 (CP-333)

**Review task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-INDEPENDENT-REVIEW-01`  
**Data:** 2026-10-16  
**Reviewed candidate SHA:** `d5ed426a08f0fee2aa9179a50d75f828fadd72b2`  
**Candidate:** [84 — Proposta G1/G2](./84-presentation-v2-contract-and-markdown-security-g1-g2-proposal.md)  
**Product authority:** [82](./82-conversation-rich-content-and-structured-presentation-specification.md) + [83](./83-conversation-markdown-b2-contract-and-implementation-plan.md), decisões D1–D12  
**Requirements:** [25](./25-requirements-traceability.md), `CP-333` = `PLANNED`; [20](./20-testing-and-acceptance-matrix.md), `C3-MD-B2-*`  
**Execution order:** [16](./16-execution-master-plan.md); ledger, sem avanço de fase  
**Review method:** inspeção estática independente de commit/diff, docs, código dos contracts/produtor/parser/renderer e navegação do Portal. **Nenhum teste executado e nenhum browser QA.**

## 1. Veredito

```text
REVIEW = REWORK
G1_CONTRACT_PROPOSAL = REWORK
G2_REUSE_SECURITY_PROPOSAL = REWORK
G1_APPROVED = NO
G2_APPROVED = NO
G3_IMPLEMENTATION_BRIEF_AUTHORIZED = NO
RUNTIME_IMPLEMENTATION_AUTHORIZED = NO
CP_333 = PLANNED_NOT_PASS
D1_TO_D12_PRODUCT_DECISIONS = PRESERVED
C3_EXECUTED = NO
C4_AUTHORIZED = NO
C5_AUTHORIZED = NO
PHASE_PROGRESSION = NONE
TESTS = TEST_NOT_RUN
DEPLOY = NOT_PERFORMED
```

O commit candidate `d5ed426a08` adiciona apenas documentação (doc 84; atualiza 83, 20 e ledger), sem runtime. A proposta acerta na direção de `presentation.v2` explícito, separação de semântica/autoridade, texto legado inerte, sanitização de saída como tokens→React, links fail-closed e paridade de full-page/dock. O review **não** rejeita essas decisões de produto. Requer correções documentais antes de congelar G1/G2 e preparar G3.

Este B2 é **Markdown conversacional**, não `C3-STAGE-02-B2` de PREPARE/ACT; os estados são independentes.

## 2. Achados bloqueantes

### RW-G1-01 — Produção de Markdown estrutural sem fonte estruturada comprovada (CRITICAL)

**Evidência:** doc 84 §4 propõe `GovernedResponseFormatter` **NEW** e transformação determinística de registros/etapas em listas. Contudo, no SHA revisado, `delia-api/app/application/interaction/contracts.py` define `InteractiveTurnResult.content: str`; `handle_interactive_turn.py::_grounded_result` recebe `attempt.content` e constrói `InteractiveTurnResult(content=content)`. O fluxo de dados governados em formato estruturado — itens/etapas/campos tipados suficientes para gerar Markdown sem inferência — **não foi demonstrado**.

**Risco:** formatter transformar prosa operacional por heurística, segmentar registros indevidamente ou alterar IDs/valores; isso viola D3/D5 e os gates de faithfulness. `NEW` exige prova de equivalentes existentes e motivo para não usar projeção/formatter já previsto na boundary.

**Rework:** inventariar por capability e produtor os campos realmente disponíveis; distinguir `string already structured by source`, `domain typed admitted data` e `plain prose`. Definir regras determinísticas por formato comprovável e política de preserve-verbatim. Onde não houver estrutura confiável, **emitir plain**, sem prometer listas automáticas. Provar um cenário grounded com IDs, quantidades e unidades sem transformação factual. Não criar `GovernedResponseFormatter` por antecipação sem `EXISTING_EQUIVALENT` e `REUSE_DECISION` válidos.

### RW-G1-02 — Links aprovados em D1/D6/D7 permanecem sem fonte tipada/contrato (CRITICAL / ARCHITECTURE_DECISION_REQUIRED)

**Evidência:** doc 84 §2.4 exige links emitidos de RouteRef/EntityRef ou origem externa admissível, mas o contrato corrente `GovernedCapabilityProvenance.to_projection` expõe `source_id`, `source_system`, `observed_at` e metadados, **não URLs publicáveis**. §5.3/§6 reconhecem `LINK_SOURCE_TYPED=TO_INVENTORY` e recomendam o B2 inicial **sem links navegáveis**.

**Risco:** declarar B2 completo sem cumprir decisões de produto já congeladas. Um `/apps/...` hardcoded como exemplo não prova existência, permissionamento e vínculo legítimo do recurso ou da fonte.

**Rework:** inventariar owners/contratos legítimos de links internos e externos; produzir contrato de link tipado de fonte governada + política de navegação/URL + casos negativos, **sem inventar RouteRef ou URI source**. A função `portal/src/utils/sameAppAnchorNavigation.ts` intercepta somente destino same-origin dentro de `appBasePath` ou shell; navegação cross-app cai em browser navigation nativa. Afirmar AuthZ do destino somente por contrato live, não por `href`. Se for impossível entregar links no primeiro slice, **pedir nova decisão explícita ao Product Master** sobre rollout parcial; não reduzir D1/D6/D7 silenciosamente.

### RW-G2-01 — Reuse Gate inválido/incompleto para `NEW ConversationMarkdown` (CRITICAL)

**Evidência:** doc 84 §5.2 usa `REUSE_DECISION=DO_NOT_REUSE` para vários candidatos, valor fora do vocabulário normativo `REUSE|EXTEND|NEW`. `EXISTING_EQUIVALENT=YES` para `MarkdownDocumentView`, `markdownDocumentModel` e `marked`, mas a comparação não comprova exaustivamente por teste/spike por que **EXTEND** de uma primitive neutra e segura dentro de `plugin-ui` é inviável ou inferior a criar `NEW ConversationMarkdown`.

**Risco:** duplicação de parsing/policy/read-model de Markdown e manutenção de dois renderers sem necessidade/consumer adicional comprovados. O renderer documental atual tem Mermaid/GFM/HTML e **não deve** ser aplicado diretamente ao output DÉLIA sem safety gate; isso não prova automaticamente a necessidade de novo componente.

**Rework:** separar decisão `NOT_SELECTED` (justificativa) de `REUSE_DECISION` (somente `REUSE|EXTEND|NEW` para solução selecionada). Comparar ao menos `REUSE` de parser/tokenização, `EXTEND` de shared read-model/allowlist, e `NEW` de primitive com owner/consumer, bundle, CSS, APIs e efeitos em consumidores existentes. Congelar `NEW` somente com evidência reexecutável de alternativas rejeitadas; sem modificar código nesta fase.

### RW-G1-03 — Schema e fallback não suficientemente fechados para contract freeze (HIGH / BLOCKING G1)

**Evidência:** doc 84 §2.9 é **fragmento JSONC**, ainda não um documento OpenAPI/JSON Schema resolvível e verificável; `additionalProperties:true` nos níveis do envelope e `oneOf` permitem atributos não definidos, sem política clara para objetos sensíveis. A relação de `allowed_interactions` com `message_kind`, limits, envelope completo do HTTP e o comportamento de unknown/malformed vs legacy demandam contrato conformance testável. §2.5 faz fallback para `content` em versão desconhecida enquanto D9 exige erro neutro em payload inválido/inseguro — as classes de confiança precisam ser separadas explicitamente.

**Risco:** emissor/consumer divergirem sobre `v2`, fallback ocultar falha estrutural e status de confirmação/act serem interpretados de forma inconsistente. `format:"markdown_safe"` não é certificação de segurança.

**Rework:** entregar esquema completo proposto e **machine-validatable** (OpenAPI com schemas/operationId onde aplicável) e exemplos positive/negative. Definir por nível `additionalProperties` intencional, required/maxLength/minItems/maxItems, unknown-kind/format/version, versão validamente recebida mas parse falha vs payload hostil estrutural, autorização de interações derivada **somente** do contrato backend atual, e matriz v1/v2 incluindo old client e rollback. Schema documental não deve ser aplicado ao runtime nesta task.

## 3. Residuals / correções de consistência

- **RX-01 (COPY):** converter Markdown para texto legível por token model é direção adequada, mas `content` legacy e clipboard precisam ter exatamente uma fonte determinística de plain text e testes de valores/code/newline; caso contrário mixed-version divergence.
- **RX-02 (DoS/A11Y):** limite proposto de 64 nós, 16 links e headings `h4`–`h6` necessita prova de adequação e fallback não truncador; nesting, tabela GFM, HTML literal e texto hostil requerem casos adversariais. Os bounds não são PASS apenas por documentação.
- **RX-03 (Navigation):** rota/navegação interna `<a href>` em app/shell pode usar SPA; cross-app native reload exige evidência de host route contract e experiência no dock. Não confundir navegação nativa com Core/Domain authorization.
- **RX-04 (Traceability):** doc 84 §7 referencia CP-333 corretamente, mas testes e outcome continuam `TEST_NOT_RUN`. `G1/G2=CANDIDATE_FOR_REVIEW` é descrição factual da entrega, não aceite.

## 4. Itens aceitáveis para preservar no rework

- D1–D12 e escolha vinculante de `presentation.v2` permanecem intactas.
- `text` com formato explícito `plain|markdown_safe`, `notice(owner_hint)` sempre literal é uma **direção contratual apropriada**, ainda sujeita a schema validado.
- Retorno de compatibilidade com clientes v1 pela projeção literal `content`, condicionado à prova do produtor canônico de plain text.
- Parser token→React **sem HTML executável** como política de segurança alvo, sem antecipar `NEW` de componente.
- `EvidenceDetails`, confirmação, atividade e status não podem ser substituídos por Markdown ou links.
- Formatação factual read-only, sem ações, tabelas, gráficos, Mermaid, imagens, attachments ou provider mechanics.
- Sem runtime, deploy, QA ou fase avançada nesta task.

## 5. Ações bounded de correção

| Slice | Owner | Entrega documental exigida | Gate |
|---|---|---|---|
| `G1-R1-A` | DÉLIA API/Application + Domain evidence owners | Inventário dos inputs efetivamente estruturados; contrato de `GovernedResponseFormatter` ou extensão legítima de projection; prova de fidelity e fallback plain | RW-G1-01 |
| `G1-R1-B` | Portal/Core + Domain API + DÉLIA contract owner | Contratos legítimos para rota/URL publicável e provenance; política de links internos/externos; decisão Product Master somente se escopo for parcialmente postergado | RW-G1-02 |
| `G1-R1-C` | DÉLIA API + MFE + Security | Schema/OpenAPI validável, compat old/new, errors/trust/fallback, interactions e copy explicitamente definidos | RW-G1-03 |
| `G2-R1` | plugin-ui + Security + Frontend DÉLIA | Reuse-vs-extend-vs-new comparativo com probe/test plan, owner e security policy; vocabulário de decisão normativo | RW-G2-01 |

**Ordem:** inventário/provas em paralelo; G1/G2 candidatos **reapresentados a review independente**; se aceitos, preparar G3 per-owner brief no HEAD real. Não publicar `REUSE_DECISION=NEW` como frozen antes da comparação.

## 6. Evidence / handoff

```text
BASE_CANDIDATE_SHA = d5ed426a08f0fee2aa9179a50d75f828fadd72b2
REVIEW_METHOD = INDEPENDENT_STATIC_GITHUB_REVIEW
G1_VERDICT = REWORK
G2_VERDICT = REWORK
EXECUTION_DRIFT = NOT_PROVEN
ARCHITECTURE_DECISION_REQUIRED = LINK_SCOPE_IF_DEFERRED
CP333 = PLANNED_NOT_PASS
PRODUCT_DECISIONS = D1_TO_D12_PRESERVED
RUNTIME_TESTS = TEST_NOT_RUN
SECURITY_TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
DEPLOY = NOT_PERFORMED
NEXT_BOUNDED = DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R1
```

Revisão de documentação não significa aceitação de implementação, nem libera G3. `HTTP 200 != business outcome`; model output e link não viram FACT/authorization. Atualizar ledger com o verdict e referenciar este relatório, sem alterar fase, código, contract efetivo ou outras linhas B2.
