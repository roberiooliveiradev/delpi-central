# DÉLIA — Resposta Conversacional com Contexto Progressivo — Especificação de UX

**Data:** 2026-10-23. **Status:** PRODUCT_UX_DECISION / PLANNED / DOC_ONLY. **HEAD de referência:** cd5f349f7148bfc6ee059f37980b08216a0fc05a. **Produto:** DÉLIA (standalone). **Escopo:** apresentação de mensagens do assistente em full-page e Companion Dock, sem alteração de autorização, evidence/decision gate, runtime, protocolos ou modelos.

## 1. Motivação e intenção do Product Owner

Na captura de conversa real, a saudação “Olá! Tudo bem? Sou a sua DÉLIA...” apareceu dentro de card azul alto, com “Atividade concluída”, “Ver detalhes”, “Sem fonte vinculada” e “Detalhes da evidência”. O conteúdo conversacional simples ficou visualmente secundário frente aos indicadores de execução/proveniência. A decisão é priorizar **resposta legível e natural**, oferecendo **contexto progressivo** quando acrescentar informação sem esconder incerteza relevante.

Os screenshots são evidência de problema de UX, **não** prova de defeito de grounding/authority. Não remover contextos ou metadados estruturados para obter visual mais limpo.

## 2. Direção visual

- A resposta da DÉLIA integra o fluxo da conversa, com avatar institucional, identificação discreta e corpo de mensagem como protagonista; **sem card azul pesado/envelope de altura mínima** para uma resposta simples.
- Hierarquia: identidade discreta → conteúdo real → ações legítimas (ex.: Copiar) → contexto/proveniência colapsável quando aplicável. Não repetir “DÉLIA” e avatares sem necessidade.
- Fundo majoritariamente transparente/neutral; borda/realce apenas para elementos semânticos (alerta real, outcome, referências, blocos estruturados). Preservar Markdown, listas, código, tabelas e demais componentes já aprovados.
- Espaçamento determinado pelo conteúdo, legibilidade tipográfica e alinhamento consistente com mensagens do usuário; evitar espaços vazios em card longo.
- Hover e transições suaves de 160–200ms para expandir contexto sem provocar layout jump; não atrasar conteúdo, não animar palavras ou prejudicar screen readers. Reduced-motion respeitado.

## 3. Variantes de apresentação — não classificações de autoridade

As seguintes são **variantes de apresentação derivadas de dados estruturados existentes**, sem segundo planner, novo classificador LLM, novos fatos ou branches baseados em palavras da resposta.

### Variante A — Conversacional

Saudação, orientação geral ou conteúdo que não exigiu consulta de fonte operacional, **quando isso for sustentado pelo contrato real**. Mostrar avatar, nome, conteúdo e ações disponíveis. Não exibir “Sem fonte vinculada” como anomalia, nem “Atividade concluída” se não houver atividade operacional material a destacar. Não falsificar a existência/ausência de fontes só pelo texto “olá”.

### Variante B — Resposta contextualizada

Quando houver observações/fonte/proveniência real no envelope de resposta, apresentar corpo e indicador discreto “Fontes”/“Contexto” com acesso à proveniência autoritativa e suas limitações. Não converter provider/tool metadata em FACT. Não criar links ou citações fictícias.

### Variante C — Atividade, investigação ou ação governada

Para activity/work/outcome real e tipado, mostrar estado importante e resultado na mensagem, com detalhes de execução/evidências progressivamente acessíveis. **HTTP 200, completion técnico e texto do modelo não provam business outcome.** Estados de erro, pendência, preparação/confirmação e riscos materiais permanecem visíveis, não ficam escondidos exclusivamente dentro de popover.

As variantes podem coexistir; usar composição dos componentes reais conforme contrato. Não usar strings/regex sobre resposta para decidir modo.

## 4. Disclosure de contexto e evidência

- “Contexto”, “Fontes”, “Detalhes da execução” ou “Evidências” são affordances **somente quando há conteúdo correspondente legítimo**; nomenclatura ajustada ao tipo real.
- Em saudação comum, omitir rótulos de origem não exigida; **não** converter ausência de fonte em warning. Quando uma pergunta precisar de fonte, mas grounding estiver ausente/inconclusivo, preservar limitação de forma clara e visível.
- Um bloco de contexto progressivo pode reunir, por composição, status, proveniência e evidências sem duplicar a fonte de verdade.
- Conteúdo de execução só deve declarar “Concluída” se esse for o estado de activity real, e não confundir com outcome aceito.
- Citações, links, provas, segurança e políticas permanecem ligados aos contratos de backend, sem inferências do UI.
- Não excluir tracking, audit, evidência ou disclaimers por estética. Avisos materiais não podem depender de clique para serem conhecidos.

## 5. Contratos e ownership

Reancorar e localizar no HEAD os documentos canônicos de conversation UI, presentation envelope, evidence projection, activity status, Markdown e componentes compartilhados antes de codificar. **Nenhum caminho de documento ou nome de componente hipotético é evidência de existência.**

**Owner:** `plugins/plugin-ui` para componentes reutilizáveis de mensagem, avatar, ações, disclosure e design system; `plugins/delia` para composição e interpretação de apresentação **de contratos tipados já admitidos**; DÉLIA backend mantém Evidence/Policy/Decision/Outcome; Domain APIs são autoridade sobre dados, Core sobre AuthZ. Nunca transportar essas autoridades para o frontend.

**Reuse Gate na execução:** `EXISTING_EQUIVALENT=TO_INVENTORY`, `REUSE_DECISION=TO_DECIDE`. Primeiro inventariar componentes de assistant message, evidence footer, activity details, status, avatar, copy, Markdown, rich responses e seus consumers. Se existir componente canônico, REUSE/EXTEND. Não criar `ConversationAssistantMessage`/registry/engine novo apenas por similaridade conceitual.

**Contratos antes do diff:** identificar owner/consumers, campos de status, evidência, source, errors, postcondition, compatibilidade e estados negativos. Não produzir classificações de autoridade a partir da aparência.

## 6. Comportamento e acessibilidade

- Progressive disclosure acessível por botão real com `aria-expanded`, heading e foco coerentes; estado inicial fechado somente quando não oculta informação material.
- Copiar copia somente o conteúdo apropriado, segundo componente atual, sem permitir divulgar material protegido.
- Abas/popovers não devem roubar foco, truncar resposta ou fechar antes de interação; teclado, Escape e screen reader.
- Full-page, Companion Dock nativo, 320/360/375/390/420px, 200% zoom, light/dark, reduced motion.
- Respeitar leitura incremental/streaming existente; não desmontar conteúdo ou perder scroll/seleção nas transições.
- Respostas longas e rich content mantêm estrutura tipográfica e controles interativos.

## 7. Critérios de aceite ARC-01..ARC-18

| ID | Critério |
|---|---|
| ARC-01 | Saudação simples é visualmente leve, com corpo como protagonista |
| ARC-02 | Sem card obrigatório de fundo azul ou altura mínima excessiva |
| ARC-03 | Avatar e identificação sem repetição desnecessária |
| ARC-04 | Mensagem conversacional sem “Sem fonte vinculada” decorativo |
| ARC-05 | Status operacional aparece quando contratualmente relevante |
| ARC-06 | Contexto real e fontes acessíveis por disclosure |
| ARC-07 | Ausência de grounding obrigatório não é escondida |
| ARC-08 | Warnings e bloqueios materiais continuam visíveis |
| ARC-09 | Evidence/Policy/Outcome não são reclassificados pelo frontend |
| ARC-10 | Mensagens com Markdown, code blocks e rich data não regrediram |
| ARC-11 | Ações legítimas como Copiar continuam funcionando |
| ARC-12 | Progressive disclosure e foco acessíveis a teclado e leitor de tela |
| ARC-13 | Motion suave, reduced motion e layout sem saltos |
| ARC-14 | Full-page e Companion Dock real |
| ARC-15 | Mobile 320–420px, zoom 200%, dark/light |
| ARC-16 | Streaming/scroll e estados in-flight/error preservados |
| ARC-17 | Reuse gate e ownership/contratos provados antes de novo componente |
| ARC-18 | RED/GREEN, regressão e QA autenticado no SHA implantado |

## 8. Roadmap de execução bounded

**Task proposta:** `DELIA-UX-CONTEXTUAL-ASSISTANT-RESPONSE-PROGRESSIVE-DISCLOSURE-01`.

REANCHOR: git HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → presentation/Markdown/evidence/activity specs e ledger. INVENTORY: identificar envelopes/owners/consumers/componentes reais. REUSE/CONTRACT GATES: provar equivalentes; manter classificação e provenance por dados autoritativos. Testes RED em saudação, resposta com fontes, evidência insuficiente, activity/outcome, erro/streaming. Implementar **o menor diff correto** no plugin-ui/composição, sem backend presumido. QA visual, regressão, documentação, ledger e deploy após gates. Se contrato não distinguir variantes com segurança, documentar `ARCHITECTURE_DECISION_REQUIRED` para essa parte e não inventar classificação textual; ainda executar melhorias puramente visuais seguras.

**STATUS FINAL DA PUBLICAÇÃO:** `SPEC_PUBLISHED; RUNTIME_NOT_CHANGED; TEST_NOT_RUN; PHASE_NOT_ADVANCED`.
