# DÉLIA — Fila Conversacional e Meus Trabalhos: UX, Comportamento e Gates

**Status:** \`APPROVED_PRODUCT_UX_DIRECTION\` — documentação de decisão de produto, **não autorização de implementação**.  
**Data:** 2026-10-09. **HEAD observado antes do registro:** \`8764efc701c562b7b04901e7f6c6d09701a67c76\` (revalidar antes de qualquer trabalho).  
**Contexto:** decisões explícitas do Product Master no planejamento do frontend.  
**Autoridades (reancorar nesta ordem antes de implementar):** Project Instructions / \`.cursor\` → [16](./16-execution-master-plan.md) → [50](./50-standalone-copilot-application-architecture.md) → [17](./17-component-and-contract-map.md) → [49](./49-architecture-and-design-patterns-standard.md) → [51](./51-platform-integration-baseline.md) → [52](./52-standalone-repository-and-bootstrap-plan.md) → [21](./21-data-and-state-model.md) → [20](./20-testing-and-acceptance-matrix.md) → [25](./25-requirements-traceability.md) → arquitetura técnica, product spec, [09](./09-ux-copilot.md), [36](./36-copilot-tasks-cases-and-interaction-rooms.md), [43](./43-durable-workflow-runtime.md), [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [70](./70-tool-activity-and-source-transparency-ux-specification.md), ledger. Autoridade superior prevalece sobre decisões conversacionais em conflito; sem reconciliação silenciosa.

## 1. Decisão de produto congelada no planejamento

**Duas experiências distintas e conectáveis sob contratos legítimos:**

1. **Fila da conversa:** vinculada **individualmente a cada conversa**, análoga à experiência de filas de IDE/assistentes. Contém solicitações ainda não iniciadas, reorganizáveis dentro de limites governados. Mini fila compacta **acima do composer**, recolhida por padrão, altura máxima adaptativa, sem competir com a timeline.
2. **Meus Trabalhos:** área própria na navegação da DÉLIA, para trabalhos longos/duráveis e estados de acompanhamento, consolidados por usuário/escopo autorizado. Pode mostrar um trabalho originado de conversa diferente, se contratos de Work, permissão, retenção e ownership o permitirem.

**Não** confundir fila conversacional com scheduler, Automation Hub, Durable Work runtime, filas de infraestrutura ou task execution. Fila de UX não cria um segundo planner ou engine. Nenhuma persistência, cross-device sync, pause/cancel, concurrency, background execution ou action material pode ser inferida deste design.

## 2. Objetivos e não objetivos

**Objetivos:** enviar várias solicitações sem esperar; entender a solicitação ativa; visualizar pendências; reordenar itens ainda não iniciados; remover/corrigir pendências; adicionar orientação à atividade corrente sob gate; acompanhar trabalhos longos em local próprio; manter interação limpa em desktop, mobile e dock.

**Não objetivos nesta decisão:** autorizar API nova, executar em paralelo por default, implementar \`localStorage\` durável, abandonar AuthZ, criar retry automático, interromper ação material, adivinhar dependências por LLM como fato, criar tela técnica de logs, mudar ordem do Plano Mestre ou fase.

## 3. Anatomia visual / lugares na DÉLIA

\`\`\`text
Portal Sidebar (owner Portal) | DÉLIA Sidebar (owner MFE) | MAIN
                              | [+ Nova conversa]        | timeline / atividade do turno atual
                              | Conversas*               |
                              | [Meus Trabalhos]*        | respostas e evidências
                              | Histórico*               |
                              |                           | ┌ Mini fila recolhível (apenas pendentes) ┐
                              |                           | │ 3 solicitações aguardando         [▾] │
                              |                           | └────────────────────────────────────────┘
                              |                           | ┌ Composer único ────────────────────────┐
                              |                           | │ Envie outra pergunta à DÉLIA...        │
                              |                           | └────────────────────────────────────────┘
\`\`\`

\`*\` Na implementação, navegação/itens só podem prometer funcionalidades comprovadas, autorizadas por fase e com contrato. \`Meus Trabalhos\` pode ser um destino planejado, não um painel com dados fictícios.

**Separação:** a **atividade atual** está junto à resposta em andamento na timeline; **mini fila** mostra somente pendentes acima do composer; **Meus Trabalhos** mostra Work durable real autorizado na sua própria surface. Não misturar progresso interno MCP/API com posições da fila.

## 4. Wireframes versionados

### WF-Q01 — estado recolhido (padrão)

\`\`\`text
  ┌────────── Mini fila ──────────────────────────┐
  │ ≡ 3 solicitações aguardando  ·  Próxima: SC/ES ▾│
  └───────────────────────────────────────────────┘
  ┌────────── Composer ───────────────────────────┐
  │ Faça outra pergunta ou adicione orientação... │
  │ [+]                           [Fila ▾] [Enviar]│
  └───────────────────────────────────────────────┘
\`\`\`

Quando \`0 pendentes\`, mini fila desaparece. Resumo de próximo item é opcional e truncado para caber na viewport. Não reservar altura vazia permanente.

### WF-Q02 — expandida em desktop (com altura máxima)

\`\`\`text
  ┌────────── 5 solicitações aguardando ──────[▴]───────┐
  │ ○ 1  Comparar indicadores de SC e ES   [↑][↓][×]   │
  │ ○ 2  Consultar chamados de TI          [↑][↓][×]   │
  │ ○ 3  Resumir principais desvios        [↑][↓][×]   │
  │    --- rolagem interna para demais pendentes ---   │
  └─────────────────────────────────────────────────────┘
  ┌────────── Composer sempre visível ──────────────────┐
  │ Outra solicitação...                       [Enviar] │
  └─────────────────────────────────────────────────────┘
\`\`\`

Uma linha compacta por item: ordinal/status, rótulo de até uma linha com ellipsis, controles discretos e acessíveis; botão de detalhes/gestão completa quando necessário. Reordenação por botões de subir/descer é fallback obrigatório; drag-and-drop, caso exista, **não** é único mecanismo nem prioridade de implementação.

### WF-Q03 — dock flutuante/mobile

\`\`\`text
 ┌──────────── DÉLIA ──────────────┐
 │ Atividade atual na conversa     │
 │ Resposta/timeline               │
 │ [3 na fila ▾]                   │
 │ [Pergunte à DÉLIA...] [Enviar]  │
 └─────────────────────────────────┘

 Expandida: ver ~1–2 itens; overflow scroll interno
 Gestão completa: drawer/surface dedicada sob demanda
\`\`\`

Não abrir outra sidebar DÉLIA permanentemente no dock. Não sobrepor composer, foco ou confirmation gate.

### WF-Q04 — página “Meus Trabalhos” (futura, dados reais)

\`\`\`text
 DÉLIA / Meus Trabalhos
 [Filtro: Em andamento | Aguardando | Concluídos | Todos]*
 ┌───────────────────────────────────────────────────────────┐
 │ Título do trabalho      Estado      Origem     Atualizado │
 │ Análise de desvios      Em curso    Conversa A    ...     │
 │ Consolidação mensal     Bloqueado   Conversa B    ...     │
 └───────────────────────────────────────────────────────────┘
 [Abrir detalhes/evidências] [Voltar à conversa de origem]*
\`\`\`

\`*\` Filtros, cross-navigation e campos exigem contrato aprovado; trabalhos são próprios do usuário ou do escopo autorizado, nunca global por padrão. Sem inventar histórico e sem expor existência de trabalho de terceiros não autorizado.

### WF-Q05 — enviar enquanto a DÉLIA está ocupada

\`\`\`text
 [Atividade atual: analisando indicadores...]
 [Composer] "Compare também com a semana passada"
 [Ao enviar:]
   (A) Adicionar à fila                 ← default, quando backlog válido
   (B) Orientação para trabalho atual   ← só se boundary permitir
   (C) Priorizar próxima                ← altera apenas PENDING elegíveis
\`\`\`

No momento de enfileirar, interface informa confirmação verdadeira (persistida ou apenas transitória, conforme contrato). Não anunciar “enfileirado” após mera mutação local caso o produto prometa durabilidade backend.

## 5. Altura máxima e densidade — decisão de UX

**A mini fila não pode dominar a tela.** Recolhida por padrão e com \`max-height\` no corpo expandido. Valores *propostos para testes, não tokens congelados nem medidas implementadas*:

| Surface | Recolhida | Expandida — altura máxima candidata |
| --- | --- | --- |
| Desktop amplo | ~40 px (1 linha) | até 180 px |
| Tablet | ~40 px | até 140 px |
| Mobile | ~36 px | até 110 px |
| Dock global | ~36 px | até 100 px |

**Regras responsivas:** aplicar também limite relativo à altura real disponível (\`min(px-cap, viewport/bounding-box cap)\` a definir em teste), evitando que queue+composer ocupem excessivamente a tela em landscape, teclado virtual ou janelas pequenas. Overflow no **corpo da lista**, não scroll global. Priorizar visibilidade de composer e confirmations; se viewport insuficiente, recolher automaticamente visualização expandida ou oferecer drawer. Bordas sutis, sem card dentro de card desnecessário, tokens Portal \`--surface-2\`, \`--border\`, \`--primary\`. Touch targets/contraste e foco não devem ser sacrificados por densidade: a altura total pode se adaptar ao tamanho de fonte e acessibilidade.

## 6. Comportamento funcional esperado, condicionado ao contrato

### 6.1. Classes de solicitações

| Classe | Exemplo | Tratamento |
| --- | --- | --- |
| Pergunta independente | “Quais chamados estão abertos?” | Pode entrar na fila da conversa |
| Dependente | “Compare com a análise anterior” | Precisa dependência explícita/resolvida |
| Orientação ao trabalho corrente | “Considere apenas Santa Catarina” | Edição/contexto vinculados a ponto seguro |
| Investigação longa | “Analise desvios da fábrica no mês” | Elegibilidade a Work durável sob contrato |
| Ação material | “Prepare/abra solicitação” | Nunca executar só por entrar na fila; gates completos |

### 6.2. Política de ordenação

- **FIFO** como ordem inicial entre pendentes elegíveis.
- Subir/descer/priorizar **apenas pendentes**; operação real aceita pelo backend quando persistente.
- **Dependência prevalece sobre ordem manual**; UI mostra bloqueio/razão e impede reordenação impossível. Não duplicar planner no MFE.
- Item já \`RUNNING\` ou com ação material em curso não muda de ordem nem retrocede apenas porque outro item foi promovido.
- Itens rejeitados/falhados não travam automaticamente os independentes.
- \`Remove pending\` é diferente de \`cancel running\`. Descartar pendente exige contrato de cancelamento/removal verdadeiro; execução remota pode já ter começado.
- Correção ao trabalho atual requer identidade inequívoca do alvo, estado/versão e gate; não altera postconditions passadas.
- Paralelismo **não é default**; candidato futuro com orçamento/isolamento/consent e owner aprovados.

### 6.3. Estados a diferenciar (modelo candidato)

\`DRAFT\` / \`QUEUED\` / \`BLOCKED_BY_DEPENDENCY\` / \`RUNNING\` / \`WAITING_USER\` / \`COMPLETED\` / \`FAILED\` / \`CANCEL_REQUESTED\` / \`CANCELLED_CONFIRMED\`. Não presumir esses enums implementados. Mapeamento à state machine canônica depende de contrato. \`WORK_COMPLETED\` tampouco prova \`BUSINESS_OUTCOME_CONFIRMED\`. UI não marca sucesso por HTTP 200, saída do modelo ou MCP response.

### 6.4. Sessão e isolamento

Cada fila tem uma **conversa proprietária** (a definir: id autoritativo do backend, ownership e lifecycle). Nunca transferir pendentes de conversa A para conversa B por engano; reordenação não muda contexto, authorizations ou dependências. Nova conversa não herda fila anterior. Multi-tab e refresh requerem concorrência/idempotência/versão se houver persistência; sem contrato durável, não prometer sobrevivência a reload, outros devices ou fechamento do navegador.

### 6.5. Falhas e recuperação

Casos mínimos: conexão offline, timeout/5xx, rejeição de enqueue, priorização concorrente, item iniciado entre clique e confirmação, auth revoked, dependência falha, owner indisponível, cancel requested mas não efetivado, resposta parcial, sessão revogada, ausência de Work na fase. UI comunica “reordenando” / “alteração confirmada” somente após confirmação real do owner e pode reverter optimistic view; não esconder erros nem reexecutar write por retry automático.

## 7. Contratos, boundaries e security

**Owners normativos:** Portal=host/dock/navigation; \`plugins/delia\`=experiência e adaptação de contratos; \`plugin-ui\`=primitivas reutilizáveis; DÉLIA Application=conversation/context/work orchestration e Decision; Core=AuthZ/governança; Domain APIs=business authority; Automation Hub=technical execution; MCP/A2A=interop, não permissão.

**Antes de mudar código/autorizar fila:** reanchor HEAD + ledger + fase; inventário real de conversation/session persistence, Work durable, scheduler existente, queue mechanism, job IDs, idempotência, status, cancel/pause, prioridade, dependências, Core AuthZ e contratos. Não criar Redis queue, DB, timer, scheduler, state machine, registry nem component kit novo por conveniência.

**Contrato candidato, NÃO aprovado:** conversation identity, owner/consumers, enqueue request/ack, queue position/version, dependency refs, move/remove commands, conflict errors, status observations, reauthorization/freshness, retention, delete/export, replay, subscribe/poll (se necessário), observability, outcomes; OpenAPI+\`operationId\` estáveis quando aplicável. History page e \`Meus Trabalhos\` dependem de privacy/tenant isolation e autenticação. Planner nunca passa provider endpoint/tool mechanics para UI. \`READ != WRITE; PREPARE != ACT; draft != send; simulate != apply\`.

## 8. Integração com jornada de atividade e compositor

A [70](./70-tool-activity-and-source-transparency-ux-specification.md) apresenta a atividade **dentro da resposta atual**; esta spec apresenta apenas **backlog do usuário**; a [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md) define composer, timeline e surfaces. Não criar duas barras concorrentes de progress. Composer oferece resposta de submit apropriada: \`enviar pergunta\` quando livre; \`adicionar à fila\` quando ocupado e backend suportar; \`orientar trabalho atual\` como opção secundária autorizada. Controles de ditado/voz/mídia continuam subordinados a seus contracts e não enviam automaticamente itens à fila após transcrição.

**Meus Trabalhos** é um destino de navegação, não o motor que executa trabalhos. Quando houver Work durável real, mostrar estados, origem, última atualização, dependências, permission-checks e postconditions, com links apenas a objetos autorizados. Trabalho iniciado por conversa pode continuar independentemente de dock aberto/fechado somente se runtime canônico suportar. Não deixar um controle de UI alterar estado de negócio sem gates.

## 9. Reuse-before-design: matriz candidata

| Recurso | Equivalente | Decisão antes do inventário |
| --- | --- | --- |
| Composer da DÉLIA | \`plugins/delia\` atual + \`plugin-ui\` | \`YES_PARTIAL\` → \`EXTEND\` candidato |
| Badges, ícones, disclosure, list, scroll area | \`plugin-ui\` catálogo | \`TO_INVENTORY\` → \`REUSE/EXTEND\` a validar |
| Sidebar/Global Dock Portal | \`portal\` | \`YES\` → \`REUSE\` boundary |
| Durable Work / Task / Case | specs \`36\` e \`43\` (TARGET) | \`TO_INVENTORY\` runtime e contrato |
| Conversation queue persistence | Não comprovada | \`TO_INVENTORY\`; nenhuma conclusão de ausência |
| Scheduler e execução material | owners externos/DÉLIA approved runtime | \`TO_INVENTORY\`, \`REUSE\` primeiro |
| Cross-conversation My Work | feature target | \`TO_INVENTORY\`, precisa auth/projection |

\`EXISTING_EQUIVALENT=TO_INVENTORY\` para capacidade completa de queue/Work, \`REUSE_DECISION=TO_DECIDE\`. Para Portal shell, \`EXISTING_EQUIVALENT=YES\`, \`REUSE_DECISION=REUSE\`. Fazer Abstraction Gate por componente, não usar similaridade superficial de CSS como prova.

## 10. Plano de implementação candidato para Devin (não executar sem autorização)

**DQ0 — Reanchor/Discovery:** HEAD/status, Project Instructions + \`.cursor\`, authorities em ordem, ledger, fase/CP/RQ, contratos de conversation/Work e estado das specs 36/43/69/70; delimitar ownership.

**DQ1 — Inventário e fit (NO IMPLEMENTATION):** componentes \`plugin-ui\`, composer DÉLIA, Dock Portal, conversation/session IDs, backend state, Work durable, queue/status contracts, idempotência, AuthZ, tests. Documento de gap com \`EXISTING_EQUIVALENT\` e \`REUSE_DECISION\` por capacidade.

**DQ2 — UX scaffold bounded (somente após gate):** mini fila com estado verdadeiramente suportado. Sem API/persistência, pode haver apenas protótipo isolado de Storybook/teste, não produção que prometa workflow real.

**DQ3 — Backend contract first (fase específica):** se faltam contract owners, retornar ao coordenador; aprovar contract/projection/status/ordering/boundaries antes de implementar. Nunca fazer scheduler React nem persistência oportunista.

**DQ4 — Frontend surface:** plug-in UI compartilhado para queue compacta, controles aria e max-height responsivos, mesma experience página/dock; Meus Trabalhos apenas após Work real, com fontes authoritative.

**DQ5 — Acceptance:** tests de regressão, viewport mobile/dock/desktop, teclado/zoom/reduced-motion, validação de estado concorrente, auth isolation, queued-vs-running, idempotência, dependência e falhas, contracts, business outcome, logs/evidence no SHA/config avaliado, residual search, ledger. Reviewer separado emite \`ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE\`.

## 11. Critérios de aceite objetivos

- [ ] Fila atrelada à conversa correta; trocar conversa não mistura backlog.
- [ ] Item em andamento aparece como atividade da resposta, **não** duplicado como item pendente.
- [ ] Recolhida por padrão, sumida quando vazia, altura máxima responsiva, overflow interno.
- [ ] Composer/confirmation nunca obscurecidos; mobile/dock com gestão em drawer sob demanda.
- [ ] Reordenação acessível por teclado e toque, aplicada somente ao \`QUEUED\` elegível.
- [ ] Não há “executar agora” fingido; pausa/cancelamento somente quando comprovados.
- [ ] Dependência preservada apesar de priorização; contexto da pergunta não troca silenciosamente.
- [ ] Requisições/ordens concorrentes tratadas com status real e rollback visual seguro.
- [ ] \`Meus Trabalhos\` só expõe objetos com AuthZ real do usuário; separa Work e outcome.
- [ ] Não há execução material sem Core/Domain/Decision Gates.
- [ ] Sem scheduler/service/port novo sem inventário e contrato; sem reuse do runtime Chat.
- [ ] Accessibility, themes oficiais, testes/evals e evidence no SHA atual.

## 12. Status e handoff

**APPROVED PRODUCT DIRECTION:** fila **por conversa**, FIFO inicial, reordenação somente de pendentes elegíveis, mini fila clean de altura limitada e recolhida, drawer de gestão; destino **Meus Trabalhos** para Work durável.  
**PLANNED:** wireframes WF-Q01–WF-Q05, limites propostos e comportamentos.  
**TO_INVENTORY:** API/storage de conversas, estado de Work, fila, scheduler, controle de concorrência, long-running resumability, source da verdade e contratos.  
**TARGET:** execução durável, cross-session My Work e mecanismos de prioridade quando fase liberar.  
**TEST_NOT_RUN:** tarefa documental não realizou implementação, testes ou deploy.

**Progresso/fase:** somente \`16\` + ledger + evidência de runtime podem definir próximos passos. Documentação não avança fase. Próximo handoff: \`4. DÉLIA — Frontend/MFE/UX\` → \`3. DÉLIA — Backend/Domain/Application\` (contratos, se necessário) → \`10. Integration/Acceptance Review\` → \`1. Architecture/Coordination\`, para implementação autorizada pelo Devin.
