# DÉLIA — Experiência Conversacional: wireframes, UI central e jornada de atividade

**Status:** DESIGN DIRECTION APPROVED IN PRODUCT CONVERSATION; IMPLEMENTATION NOT AUTHORIZED BY THIS DOCUMENT  
**Escopo:** planejamento detalhado de UX/UI para `plugins/delia`, host `portal` e componentes `plugins/plugin-ui`.  
**Referência de HEAD do inventário:** `5e4ae559a5e9e22626a323fde5fd9d12a66e713d` (revalidar antes de executar).  
**Autoridade:** Project Instructions / `.cursor` → [16](./16-execution-master-plan.md) → [50](./50-standalone-copilot-application-architecture.md) → [17](./17-component-and-contract-map.md) → [49](./49-architecture-and-design-patterns-standard.md) → [51](./51-platform-integration-baseline.md) → [52](./52-standalone-repository-and-bootstrap-plan.md) → [21](./21-data-and-state-model.md) → [20](./20-testing-and-acceptance-matrix.md) → [25](./25-requirements-traceability.md) → [09](./09-ux-copilot.md) → [38](./38-evidence-provenance-and-epistemic-ux.md) → ledger.  
**Regra:** documento de design NÃO muda fase, contracts de backend, autorização, persistência, deployment ou execução.

## 1. Intenção de produto e decisões visuais

DÉLIA é uma aplicação standalone de Continuous Operational Intelligence. Deve parecer parte da Minha DELPI, não um modo do Minha DELPI Chat. A experiência deve ser moderna, clean, responsiva, discreta e acessível; inspirar-se na organização visual de assistentes conversacionais atuais sem copiar implementação privada, inventar capabilities ou multiplicar componentes. O objetivo é uma única experiência para qualquer especialista, MCP/A2A, OpenAPI, integração externa ou operação governada.

**Decisões aceitas como direção visual:**
1. Um fluxo central de apresentação do backend até a UI, provider-neutral, sem renderizadores especiais por especialista.
2. Reutilizar componentes/tokens `@delpi/plugin-ui` sempre que adequados; componente compartilhável novo pertence ao `plugin-ui` **somente se** inventário provar necessidade/owner/consumers. O adaptador de contrato e composição de tela pertencem ao MFE DÉLIA.
3. Três superfícies consistentes: **página inicial/recepção**, **conversa ativa em página completa** e **dock global compacto**. Mesmas mensagens, estados e composer em todas; layouts adaptativos, não runtimes paralelos.
4. Mensagens do usuário discretas à direita; mensagens da DÉLIA à esquerda, sem um cartão pesado envolvendo toda a resposta. Componentes ricos ganham contêiner próprio somente quando suportados por contrato backend.
5. Evidência/fonte e limitações acessíveis quando materiais; badges apenas para estados relevantes, não decoração.
6. Sidebar própria da DÉLIA separada da sidebar Portal; recepção enxuta, sem dashboard desnecessário; composer único; jornada de atividade compacta e expansível.
7. Contrato backend determina conteúdo e interações permitidas; frontend valida versão/tipos e renderiza, nunca interpreta modelo/tool output como autoridade.
8. Temas claro e escuro herdados dos tokens oficiais do Portal, sem paleta paralela.
9. Os **mockups/imagens do chat são referências visuais não técnicas**. Podem mostrar tabelas, histórico, upload, microfone, ações e botões ainda não autorizados: NÃO implementar só porque aparecem na imagem.

## 2. Evidência de inventário preliminar (revalidar no HEAD de implementação)

| Fonte | Evidência localizada | Decisão provisória |
| --- | --- | --- |
| `portal/src/index.css` | Tokens `--primary`, `--secundary`, `--bg`, superfícies, estados, dark mode, `data-theme` | REUSE |
| `portal/src/ui-kit/tokens.md` | Define `index.css` como fonte de verdade; evita hex fixo no componente | REUSE |
| `portal/public/logoMinhaDelpi.svg`, `logoDelpi.svg`, `icon-minhadelpi.png` | Assets institucionais do host | REUSE por asset oficial, sem duplicar arquivo sem necessidade |
| `plugins/plugin-ui/src/brand/delpiLogoMark.ts` | Componente compartilhado de marca DELPI | Avaliar adequação ao contexto, REUSE quando aplicável |
| `plugins/delia/src/App.tsx` | MFE com turns transitórios em React, textarea, confirmação governada, proveniência | EXTEND, não criar segundo runtime |
| `plugins/delia/src/ui/deliaUi.ts` | Importa page header/empty state do `plugin-ui` | REUSE |
| `plugins/plugin-ui/docs/component-catalog.md` | Catálogo de ActionButton, IconButton, campos, status, Timeline/ActivityTimeline, feedback etc. | Inventariar props/semântica antes de reutilizar |
| `plugins/plugin-ui/src/styles/*` | Includes message-thread, room-conversation-shell, timeline, inline-loading-progress, loading activity, interaction-room, native-controls | `TO_INVENTORY`: CSS/nome semelhante não prova equivalente suficiente |
| `portal/src/ui/GlobalDeliaDock.*` | Host global da DÉLIA, proprietário da superfície dock | Respeitar Portal como host/navegação; preservar contrato de montagem |
| `delia-api/app/application/interaction/presentation.py` | `presentation.version="1"`, block allowlist `text|notice`, semantic states, allowed_interactions | Frontend deve seguir contrato comprovado |
| `POST /interaction/turns` | Hoje responde JSON HTTP; nenhuma prova de SSE de progresso | NÃO simular eventos técnicos em tempo real |

**Classificação:** `EXISTING_EQUIVALENT=YES (PARCIAL)`; `REUSE_DECISION=REUSE/EXTEND` por componente após inventário; `NEW` exige prova de gap e Abstraction Gate. Este documento não fecha essas decisões individualmente.

## 3. Design system canônico do Portal

Referência primária: `portal/src/index.css`. Aplicar tokens, não cópias de valores.

| Token | Light efetivo | Dark efetivo |
| --- | --- | --- |
| `--primary` | `#089BDB` | `#089BDB` (herdado) |
| `--secundary` | `#003866` | herdado, usar `--text` para texto |
| `--bg`, `--surface` | `#FFFFFF` | `#0F1115` |
| `--surface-2` | `#F7F7F7` | `#1B2030` |
| `--surface-3` | `#FAFAFA` | `#111521` |
| `--text` | `var(--secundary)` = `#003866` | `rgba(255,255,255,.85)` |
| `--text-muted` | `rgba(17,17,17,.7)` | `rgba(255,255,255,.7)` |
| `--border` | `#E6E6E6` | `rgba(255,255,255,.12)` |
| `--border-2` | `#D9D9D9` | `rgba(255,255,255,.16)` |
| `--success` | `#067647` | `#2ECC71` |
| `--danger` | `#B42318` | `#FF6B6B` |
| `--warning` | `#F59E0B` | `#FBBF24` |

`--text` tem duas declarações no `:root`: a última (`var(--secundary)`) prevalece. Respeitar theme do host e preferência do sistema, contraste WCAG, foco visível, motion reduction, teclado, screen readers; evitar CSS hardcoded em componente. Marca: usar assets oficiais do Portal; ícone/naming DÉLIA próprio só com decisão de branding. O mockup não substitui o logo oficial.

## 4. Mapa das superfícies e ownership

- **Portal Sidebar:** apps, usuário, tema, permissões de host/rotas; owner Portal. Não transportar regra de negócio.
- **DÉLIA Sidebar:** nova conversa, busca/lista de conversas (se o backend suportar), agrupamentos temporais e navegação interna; owner MFE DÉLIA. Na página completa pode ficar aberta e ser recolhida; no dock fica recolhida por padrão.
- **Timeline:** ordena turnos e blocos da mesma composição user-facing, incluindo estados governados e atividade. Owner MFE DÉLIA, primitivas visuais reutilizáveis `plugin-ui`.
- **Composer:** único componente de input multiline com submit, foco e acessibilidade; usado em página e dock, sem anexos/voz/ferramentas enquanto não houver contrato real. Owner visual `plugin-ui` quando demonstrada reutilização; integração do request no MFE.
- **Painel contextual de fontes:** opcional, sob demanda, recolhido por padrão. Nunca ocupação obrigatória em dock estreito.
- **Global dock:** host/mount/abertura/tamanho são responsabilidades do Portal; conteúdo conversacional, DÉLIA MFE. Não criar segunda sidebar Portal, sessão paralela ou runtime Chat.
- **Mobile:** navegação DÉLIA como drawer, composer acessível, timeline em coluna; fonte/detalhes em disclosure.

## 5. Wireframes textuais — aprovados como layout conceitual, não contrato implementado

### WF-01 — Página completa / recepção (antes do primeiro envio)

```text
+-- PORTAL SIDEBAR --+-- DELIA SIDEBAR ------+--------------------- DELIA / MAIN ----------------------+
| Minha DELPI       | DÉLIA                | Header: DÉLIA                                [ações]  |
| Apps / navegação  | [+ Nova conversa]     |                                                      |
| DÉLIA selecionada | [Buscar conversas]*   |                      [ícone DÉLIA]                    |
| outros apps       | Hoje*                |                 Como posso ajudar hoje?              |
| Tema / perfil     |  • indicadores*       |         Consulte informações da DELPI autorizadas    |
|                   | Ontem*               |                                                      |
|                   |  • solicitações*      |          [Produtos]      [Indicadores]               |
|                   |                      |          [Solicitações] [Investigar]                 |
|                   | Preferências*        |                                                      |
|                   |                      |  +------------------------------------------------+  |
|                   |                      |  | Pergunte à DÉLIA...                            |  |
|                   |                      |  |                                      [Enviar]  |  |
|                   |                      |  +------------------------------------------------+  |
+-------------------+----------------------+------------------------------------------------------+
```

`*` Elementos conceituais: histórico persistente, busca, agrupamento, preferências e sugestões dependem de owner/contrato e autorização. **Hoje turns permanecem em memória React e não sobrevivem a reload**; não usar localStorage como substituto, nem prometer conversas recentes. Saudação personalizada só usando contexto legítimo do host; ausência de perfil → saudação neutra. Cards de sugestões só para capabilities autorizadas/comprovadas; clicá-los preenche composer, não executa tool diretamente.

### WF-02 — Página completa / conversa ativa

```text
+-- PORTAL --+-- DÉLIA NAV -------+--------------------- TIMELINE --------------------------------+
|           | Nova conversa       | Você                                          [pergunta]       |
|           | Conversas*          | DÉLIA                                                          |
|           |                     |  [Atividade compacta: Consultando fonte...]  [Expandir]       |
|           |                     |  Resposta em prosa legível                                     |
|           |                     |  +--- BLOCO TIPADO (se contrato autorizar) -----------------+   |
|           |                     |  | conteúdo estruturado validado e evidence-bound           |   |
|           |                     |  +---------------------------------------------------------+   |
|           |                     |  Fonte / provenance   ·   limitação material · cópia*          |
|           |                     |                                                                  |
|           |                     | Você                                         [outra pergunta]   |
|           |                     | DÉLIA     [Aviso / clarificação / preview governado]             |
|           |                     |                                                                  |
|           |                     |  +-------------------- COMPOSER -----------------------------+  |
|           |                     |  | Pergunte à DÉLIA...                              [Enviar] |  |
|           |                     |  +-----------------------------------------------------------+  |
+-----------+---------------------+------------------------------------------------------------------+
```

Usar margens confortáveis, largura legível, mensagens usuário à direita, DÉLIA à esquerda; badges discretos. Não transformar toda resposta em card. Evidência e limitações aparecem se relevantes; painéis técnicos somente por disclosure. Não exibir dados fictícios em runtime.

### WF-03 — Dock global compacto

```text
+------------------------- portal / apps correntes -----------------------+----- DOCK DÉLIA -----+
| sidebar Portal e tela ativa permanecem visíveis                         | DÉLIA    [↗] [×]    |
|                                                                         |---------------------|
|                                                                         | [Você] pergunta      |
|                                                                         | DÉLIA responde       |
|                                                                         | [Atividade resumida] |
|                                                                         | [Aviso/estado]       |
|                                                                         |                     |
|                                                                         | [Composer][Enviar]   |
+-------------------------------------------------------------------------+---------------------+
```

Sem sidebar DÉLIA permanente; largura reduzida sem compressão ilegível. Abrir página completa é navegação pelo contrato do Portal, não nova instância de backend por conveniência. Continuidade entre dock/página é `TO_INVENTORY`; não assumir sincronização/persistência de sessão.

### WF-04 — Estados da mensagem

```text
RESULT                 DÉLIA: resposta grounded / observação + fonte material.
PRECONDITION_REQUIRED  Ícone informativo + mensagem declarada pelo owner + próxima etapa apenas autorizada.
CLARIFICATION_REQUIRED Pergunta específica + campo/alternativas aprovadas quando contrato suportar.
CONFIRMATION_REQUIRED  Preview seguro + [Confirmar] [Rejeitar] pelo payload do contrato existente.
AUTHZ_DENIED           Permissão negada explicada, sem instrução para contornar o gate.
SOURCE_UNAVAILABLE     Falha de fonte, retry só se houver contrato e segurança.
WRITE_REJECTED         Operação não permitida/invalidada sem reinterpretar como sucesso.
INCOMPARABLE           Limitação honesta de comparação, sem evidência inventada.
```

`INCOMPARABLE` aqui é UX de limitação, NÃO um novo `message_kind` sem contrato backend. A distinção epistêmica não deve promover `OBSERVATION` a `FACT`.

## 6. Backend presentation.v1 → MFE (contrato atual)

Origem comprovada: `delia-api/app/application/interaction/presentation.py` e `POST /interaction/turns`. Resposta é JSON; atualmente **não há canal SSE para progresso em tempo real**.

```json
{
  "presentation": {
    "version": "1",
    "message_kind": "RESULT",
    "semantic_status": "OBSERVATION",
    "grounding_status": "GROUNDED",
    "blocks": [{"kind": "text", "text": "Conteúdo já governado"}],
    "allowed_interactions": ["reply"]
  }
}
```

Tipos emitidos: `text`, `notice` com `role=owner_hint`; demais `list/table/metric/chart/comparison/action_preview/artifact` são futuros, **não implementados** em v1. Mensagens: `RESULT`, `CLARIFICATION_REQUIRED`, `CONFIRMATION_REQUIRED`, `WRITE_REJECTED`, `AUTHZ_DENIED`, `SOURCE_UNAVAILABLE`, `PRECONDITION_REQUIRED`. O backend continua autoridade por `message_kind`, `epistemic_class`, `grounding_status`, `limitations`, `provenance`, `confirmation_request`.

O frontend deve aplicar validação de versão/schema; fallback seguro para bloco desconhecido; plain text sem `innerHTML` executável; não duplicar `owner_hint` quando já presente no conteúdo legado. `allowed_interactions` é sugestão de UX, **não autorização**. `confirm/reject` só com payload existente `{decision,proposal_digest,preview_fingerprint,session_id}` e backend verificando gates. Nunca produzir links de `authorize_url` vindos de texto, tool ou modelo. Orientação `glpi_link_required` amigável depende do owner TÉO declarar contrato user-facing, não da DÉLIA inventar domínio.

## 7. Jornada de Atividade — planejamento obrigatório

**Objetivo:** mostrar atividade operacional verificável enquanto o usuário aguarda, sem expor cadeia de pensamento, prompts, credenciais, tokens, argumentos sensíveis ou logs.

### WF-05 — Compacto e expandido

```text
[DÉLIA]  ◌ Processando sua solicitação...       [Detalhes ▾]
  quando houver evidência backend:
  ✓ Solicitação recebida
  ✓ Capacidade selecionada: TÉO (somente após seleção real)
  ◌ Consultando chamados (somente após início real da chamada)
  · Organizando evidências (somente se stage observável)
  ✓ Resposta disponível (somente após resultado)
[Após concluir] ✓ Consulta concluída · TÉO · 21s* [Como foi obtida ▾]
```

`*` Duração ilustrativa: apresentar tempo apenas se medido. Mensagens de "pensando", "consultando MCP", "pesquisando na internet", "comparando fontes", "preparando resposta", "aguardando confirmação", "indisponível" ou "concluído" exigem eventos/estados reais backend, nunca timers ou animações que **alegam** estágios não observados. Atividade pode exibir provider/owner apenas após seleção/invocação legítima, com nomenclatura segura; Internet somente se capability autorizada de pesquisa realmente foi invocada. Falha de owner não vira sucesso. Estados de confirmação não implicam ACT.

**Modelo de UX progressivo:**
- **Hoje (JSON):** somente estado genérico local e honesto `Aguardando resposta da DÉLIA` durante POST; após receber response mostrar resumo de fontes/provenance/limitações realmente presentes. Não inventar timeline intermediária.
- **Futuro (se aprovado):** backend projeta `activity events` semânticos e bounded, correlation id, sequência, timestamps, fase, owner opcional, status `started/completed/failed/blocked`, proteção de dados; transporte (SSE/polling/etc.) requer ADR/contrato e não é autorizado por este plano.
- **Após resposta:** linha de atividade recolhida, expandível para eventos verificáveis; não exibir reasoning privado.
- **Erros e bloqueios:** elevar condição material para `notice`/clarificação/governed decision; texto e CTA só quando contratualmente autorizados.

`EXISTING_EQUIVALENT=TO_INVENTORY` para telemetria pública de activity e `plugin-ui` Timeline/LoadingActivity. `REUSE_DECISION=TO_DECIDE`. Não criar Activity Engine/Service/Registry ou SSE sem provar boundary e fase.

## 8. Sidebar / histórico — decisão de UX vs persistência

Design pretendido: nova conversa, buscar conversas, seções Hoje/Ontem/Anteriores, títulos de conversa, renomear/arquivar/excluir, seleção atual e navegação. **Não há prova de storage/contrato de histórico durável no runtime atual**. Antes de implementar: owner de conversation/session, Core AuthZ, isolamento de usuário/tenant, retenção/consentimento, privacy, export/delete, concorrência, migração, versionamento, API e outcome tests. Enquanto isso: mostrar apenas sessões realmente presentes em estado transitório quando apropriado e rotulá-las como não salvas, sem prometer busca/histórico posterior.

## 9. Componentes e decisão reuse-before-design

| UI | Candidato existente | Gate |
| --- | --- | --- |
| Botões / ações | `plugin-ui` ActionButton, IconButton | REUSE após verificar API |
| Composer textarea | TextAreaField / NativeTextAreaControl | REUSE/EXTEND após verificar acessibilidade e multiline |
| Empty/welcome | EmptyGuidance / EmptyState | REUSE/EXTEND |
| Badges/notice | StatusBadge / StateBanner / InfoStatePanel | REUSE/EXTEND |
| Indicador de espera | InlineLoadingProgress / LoadingActivityBadge | REUSE/EXTEND após checar semântica |
| Timeline de atividade | Timeline / ActivityTimeline | TO_INVENTORY: não assumir que é timeline de conversa |
| Mensagem / thread | Estilos message-thread / room-conversation-shell | TO_INVENTORY: não reutilizar runtime Minha DELPI Chat |
| DataTable / KPI / charts | disponíveis no plugin-ui | NÃO EMITIR até backend tipar e autorizar block schemas |
| Branding | Portal assets / plugin-ui brand | REUSE institucional |
| Sidebar Dock | Portal GlobalDeliaDock | REUSE boundary Portal; sem fork |
| DÉLIA contract adapter | `plugins/delia` | EXTEND somente para mapear presentation.v1 |

Para cada proposta nova: `OWNER → CONSUMER → EXISTING_EQUIVALENT → REUSE_DECISION → ABSTRACTION_GATE → CONTRACT → TEST`. Nenhum componente visual reutilizável nasce diretamente dentro da DÉLIA se pertence legitimamente ao plugin-ui; nenhum componente domain-specific vai ao kit genérico sem consumidor comprovado.

## 10. Acessibilidade, responsive e comportamento

- Teclado completo, foco visível e restauração de foco após submit/erro/modal; `aria-live` com parcimônia para resultado e avisos, sem ler telemetria verbosa continuamente.
- Composer aceita Enter/Shift+Enter conforme convenção comprovada no kit e acessibilidade; prevent double submit; abort visual/semântico honesto; resize sem cobrir mensagens.
- Usuário controla scroll; autoscroll apenas quando próximo do fim e sem interromper leitura anterior.
- Estado loading de turno é transitório e não afirma qual provider está trabalhando até receber evidência.
- Responsividade: desktop Portal sidebar + DÉLIA sidebar + main; tablet DÉLIA sidebar recolhível; mobile drawer + composer de largura total; dock sem lateral extra.
- Tema light/dark via tokens host; suporte reduced motion, contraste, zoom 200%, erro não codificado só por cor.
- Contexto pessoal publicado pelo host é não confiável para AuthZ; perfil opcional na saudação.

## 11. Referências de wireframe e imagens

Os **wireframes textuais WF-01 a WF-05 são a especificação visual legível versionada**. Os mockups de referência foram gerados no chat e incluem duas referências de layout de produção fornecidas pelo usuário: (a) Portal Minha DELPI com DÉLIA no dock direito; (b) `/apps/delia` aberto em página inteira. Em ambas, preserve a sidebar real do Portal, o chrome existente e o tema real; evolua **somente** a experiência da DÉLIA. Um mockup adicional das versões light/dark da conversa integra direção de linguagem visual.

**Não afirmar que imagens binárias foram anexadas ao GitHub:** este documento não contém os arquivos de imagem; assets oficiais existentes estão em `portal/public/`. Se for necessário versionar os mockups gráficos, fazê-lo em tarefa de documentação/assets separada, com arquivos exatos fornecidos e sem capturar informações pessoais reais dos screenshots. Números, nomes, datas, textos e botões dos mockups são ilustrativos, não prova de capability. As capturas do usuário são referência de layout atual, não autorização para copiar dados pessoais para docs.

## 12. Plano sequencial bounded para Devin (não autoriza executar)

**P0 — Documentation + Acceptance (esta tarefa):** revisar este documento em Coordination e integrar às specs canônicas sem alterar fase.

**P1 — Component inventory:** reanchor HEAD → authorities → `plugins/plugin-ui` catálogo/exports/CSS/testes, `portal` Dock e theme, `plugins/delia` runtime; matrizes `EXISTING_EQUIVALENT`/reuse por componente, owners/consumers e gaps. `NO IMPLEMENTATION`.

**P2 — Contract fit:** confrontar `presentation.v1`, HTTP JSON, `confirmation_request`, `provenance`, loading e history com WF-01–WF-05; definir árvore mínima e backward compatibility; stage/progress real vai a backend Coordination se faltar contrato. `NO NEW BACKEND ENGINE`.

**P3 — UI foundation, se autorizada:** separar componentes puros de apresentação em `plugin-ui` apenas quando lacuna comprovada; `plugins/delia` faz adapter de v1, timeline semântica, safe fallback, composer único, recepção + conversa ativa. Sem streaming/histórico fictício.

**P4 — Dock reuse + mobile:** integrar mesmas primitivas no host Portal existente, sem duplicar sessão/composer; testar desktop/mobile/dark/light, acessibilidade, foco, loading, confirms.

**P5 — Acceptance:** lint/typecheck/build, testes React e integração Portal/MFE, perf/a11y, testes adversariais de bloqueios e malicious blocks, governança `read != write; PREPARE != ACT`, smoke authenticated read-only; evidência no SHA commitado, ledger, revisão `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

**P6 — Históricos/atividades rich/typed blocks:** somente quando requisitos/fase, owner e contratos backend permitirem; não embutir na P3.

### Acceptance checklist

- [ ] UI sem segundo planner/engine/catálogo de tool
- [ ] Mesma timeline/composer página+dock
- [ ] sem dados/capability simulados apresentados como reais
- [ ] presentation.v1 respeitado, unknown blocks fail-safe
- [ ] owner hint não duplicado nem executado
- [ ] confirmação continua backend-first, digests protegidos
- [ ] source e limitações acessíveis; sem inferência `FACT`
- [ ] loading não afirma progresso técnico não observado
- [ ] theme e marca oficiais; contraste/teclado/mobile comprovados
- [ ] session/history não prometidos sem contrato
- [ ] tests + evals + outcome + residual search no SHA atual
- [ ] deploy separado/autorizado; fase inalterada

## 13. Dependências e perguntas de governança abertas

1. `FRONTEND_COMPONENT_INVENTORY=TO_INVENTORY`, particularmente Timeline, thread e composer.
2. `LIVE_ACTIVITY_EVENT_CONTRACT=TO_INVENTORY`; atual `JSON_ONLY`; progresso genérico único permitido.
3. `PERSISTED_CONVERSATION_HISTORY=NOT_PROVEN`; definir source, owner e contrato antes da sidebar funcional.
4. `RICH_PRESENTATION_BLOCKS=NOT_AUTHORIZED` no v1; tables/charts mockups são future design.
5. `TEO_GLPI_FRIENDLY_USER_MESSAGE=OWNER_FOLLOWUP`: não fabricar texto domínio/link de autorização.
6. `SHARED_AUTH_JWKS=OWNER_FOLLOWUP_REQUIRED` separado.
7. Branding DÉLIA novo requer gate próprio, sem substituir logo Minha DELPI.

**Handoff:** chat `4. DÉLIA — Frontend / MFE / UX` → `10. DÉLIA — Integration / Acceptance Review` → `1. DÉLIA — Architecture / Coordination`. Implementation por Devin somente após reanchor, autorização de fase e contrato.



## 14. Microinterações e motion design — direção de UX aprovada (2026-10-09)

**Status:** `APPROVED_VISUAL_DIRECTION` por Product Master na conversa; `IMPLEMENTATION=PENDING`. As durações são alvos de design para validação, não fatos do runtime nem autorização para criar novos serviços ou fluxos de backend.

### 14.1. Princípios de movimento

1. Movimento deve comunicar estado, transição e resposta à ação do usuário, não apenas ornamentar a interface.
2. Identidade visual: marca DÉLIA discreta, azul institucional `var(--primary)`, superfícies e contraste herdados do tema Minha DELPI. Não criar avatar antropomórfico nem personagem animado.
3. Animação deve ser curta, suave, interrompível, consistente nas superfícies página completa e dock.
4. Estado técnico da orquestração não pode ser inferido de timers ou animações: sem eventos observáveis backend, somente `A DÉLIA está trabalhando...`/aguardando resposta. Nunca afirmar `Consultando TÉO/MCP`, `Pesquisando na internet`, `Comparando dados` ou `Preparando resposta` sem evidência real da atividade.
5. Após a resposta, mostrar resumo discreto e recolhido de fontes/atividade **somente quando houver evidência pública permitida**. Não expor chain-of-thought, prompts, tools arguments, tokens/segredos ou metadados não governados.
6. Respeitar `prefers-reduced-motion`, teclado, foco, contraste, screen readers, dispositivos de menor desempenho e economia de energia.

### 14.2. Componente de atividade: símbolo + status + detalhes

**Direção visual selecionada:** ícone/símbolo da DÉLIA com pulsação luminosa **muito sutil** e frase curta de status; detalhes colapsados por padrão e expansíveis sob demanda. Três pontos animados podem ser avaliados como fallback visual em inventário, não como outro componente paralelo. Não usar spinner e pulsação em competição visual.

```text
[marca DÉLIA + pulse sutil] A DÉLIA está trabalhando...  [Detalhes ▾]
  Somente se backend oferecer eventos/estados verificados:
  ✓ Solicitação recebida
  ✓ Fonte autorizada selecionada: TÉO
  ◌ Consultando chamados
  · Organizando evidências
[Após receber resposta] ✓ Resposta disponível  [Como foi obtida ▾]
```

**Estado inicial factualmente permitido hoje:** `POST /interaction/turns` é request/response JSON, sem progress streaming; mostrar apenas `Aguardando resposta da DÉLIA` enquanto HTTP estiver pendente. O status `source` no protótipo é **futuro e condicionado a evento de backend**, não timer nem simulação. Se source unavailable, auth denied ou precondition, renderizar o `presentation.v1` do backend em vez de inventar sucesso.

### 14.3. Composer único

- Textarea multiline de altura adaptativa com expansão suave, token de foco `--focus-ring`, placeholder discreto e controles compartilhados do `plugin-ui` após inventário.
- Envio indica `loading`, bloqueia submissão duplicada e oferece cancelamento apenas se o transporte/abort realmente o suportar; cancelar espera UI não equivale a cancelar execução remota.
- Entrada por teclado e tecnologias assistivas; sem atalhos não documentados. Ícones de anexo, voz, câmera, ferramentas e pesquisa web só quando houver capability contratada/autorizada; não renderizar como affordances falsas.
- Mesmo componente tanto no dock quanto na página completa.

### 14.4. Transição recepção → conversa

- Depois da primeira mensagem, a saudação/cartões iniciais deixam o foco; timeline ocupa região central; composer permanece visualmente consistente e se ancora no rodapé.
- Preferir animação curta de opacidade/posição sem reload e sem pular foco. Não criar histórico persistente por implicação visual.
- Se reduced-motion ativado, alternar layout sem deslocamentos animados.

### 14.5. Timeline e mensagens

- Entrada de turno com fade + deslocamento vertical leve, sem token-by-token fake streaming; revelar somente blocos já recebidos e permitidos por `presentation.v1`.
- Componentes ricos (list/table/metric/chart etc.) são **future contract**, não renderizar até backend suportar schema permitido.
- Estados materiais (precondition, auth denied, confirmation) devem ser visualmente claros, mas não usar animação persuasiva em confirmações governadas. Ações somente pelo protocolo confirmado `confirmation_request`; `allowed_interactions` não concede autorização.
- Autoscroll só se usuário estiver próximo do fim. Respeitar leitura/scroll e anúncio de mensagens para screen readers.

### 14.6. Sidebar DÉLIA e dock Portal

- Sidebar da DÉLIA abre/recolhe suavemente, com preservação de scroll/foco, separada da sidebar do Portal.
- Dock global abre/oculta sem tomar controle de outros MFEs. Estado de sessão compartilhada entre dock e página só após contrato realmente comprovado; não inventar sincronização.
- Adaptar comportamento desktop, tablet e mobile usando contratos/componentes compartilhados do `plugin-ui` e host Portal.

### 14.7. Tabela de motion tokens propostos

| Interação | Intervalo inicial para avaliação |
| --- | --- |
| Hover/foco de botão | 120–160 ms |
| Entrada de mensagem | 180–240 ms |
| Troca de status/aviso | 180–250 ms |
| Expandir/recolher detalhes | 200–280 ms |
| Abrir/recolher sidebar | 220–300 ms |
| Recepção → conversa | 250–350 ms |

**Não congelar valores em hex/CSS local.** Mapear para motion tokens canônicos existentes no `plugin-ui`/Portal se houver. `EXISTING_EQUIVALENT=TO_INVENTORY` para animações, loading, status, drawer, timeline e composer. `REUSE_DECISION=TO_DECIDE` por componente. Se não existir mecanismo legítimo, propor extensão compartilhada mínima e justificar Abstraction Gate antes de implementar.

### 14.8. Testes e critérios de aceite do motion

- Sem indicadores de estágio não observados; loading genérico honesto com HTTP JSON atual.
- Mesma experiência e semântica em página completa e dock compacto.
- `prefers-reduced-motion` elimina movimento não essencial; foco visível/não perdido; suporte teclado e leitor de tela.
- Nenhuma animação dispara ações ou altera confirmação/autorização; sem dupla submissão; loading e erro refletem resposta real.
- Sem regressão de layout shift, scroll inesperado, renderização ou performance em mobile.
- Reutilização demonstrada por inventário de componentes `plugin-ui`, com testes de integração e outcome no SHA avaliado.
- O desenho visual não autoriza criação de engine de activity, persistência, SSE, nova tool ou mudanças de fase.

**Handoff futuro ao Devin:** primeiro inventariar componentes/motion tokens reais e contrato backend; depois implementar o menor conjunto de componentes autorizados; somente então validar UX e acessibilidade com evidências.

## 15. Experiência multimodal — voz, áudio, imagem, câmera e vídeo (decisão visual, 2026-10-09)

**Status:** direção UX de produto aprovada para planejamento; capacidades `TARGET` / implementação `NOT_PROVEN`, não autorizada por este documento. Autoridades: [53](./53-multimodal-meeting-frontline-and-industrial-copilot.md), [30](./30-multimodal-expertise-and-drawing-analysis.md), [54](./54-biometric-identity-and-human-observation-governance.md), [55](./55-internet-research-and-external-connectors.md), [09](./09-ux-copilot.md), [16](./16-execution-master-plan.md) e demais autoridades superiores.

### 15.1. Direção de produto e superfícies

DÉLIA mantém **uma única timeline, um único composer conceitual e uma única orquestração governada** para texto e mídias. Os meios de interação não constituem chats independentes, segundo planner, bypass de autenticação ou nova autoridade. A página principal, dock do Portal, sessão de meeting e contextos frontline compartilham componentes/contratos onde legitimamente reutilizáveis, com apresentação adaptada ao espaço e ao dispositivo. Controles de captura só aparecem habilitados quando a capability real, o device e as permissões aplicáveis forem comprovados.

### 15.2. Voz: separar ditado de conversa

**Modo A — Ditado para o composer:** comando de microfone solicita permissão explícita, indica captura ativa, grava trecho limitado segundo policy, transcreve, mostra resultado editável no composer e **requer revisão/envio explícito pelo usuário na primeira versão**. Útil para nomes, códigos e medidas que podem ser reconhecidos incorretamente. Uma transcrição não é FACT nem autorização de ação.

```text
[Composer] Pergunte à DÉLIA...
[+ Mídia]                   [Microfone] [Voz] [Enviar]

[Microfone ativo] Ouvindo... [Parar] [Cancelar]
    → [Transcrição editável] Pergunta reconhecida...
    → [Revisar / Enviar]
    → POST interaction/turns pelo mesmo caminho governado de texto
```

**Modo B — Conversa por voz:** sessão explícita com indicadores `pronta`, `ouvindo`, `processando`, `reproduzindo resposta`, `pausada/microfone desligado`, `erro`, `encerrada`; legendas/transcrição textual coexistem. Identidade visual sugerida: marca DÉLIA em círculo com animação orgânica discreta ao ouvir/falar (não implica raciocínio interno ou stage não confirmado). Controles mínimos: iniciar/encerrar, silenciar microfone, legendas e retorno à timeline textual. TTS/STT, turn-taking, barging/interrupção, tratamento de latência e realtime dependem de provedores/ports/contratos realmente inventariados. **Não foi decidido ainda** se o modo principal futuro será chamada contínua ou push-to-talk; ambos permanecem alternativas de avaliação. Não pressupor suporte de áudio live apenas porque há ícone no protótipo.

```text
+---------------- DÉLIA | Conversa por voz ----------------+
| microfone e reprodução: explicitamente sinalizados        |
|                  [Marca DÉLIA]                           |
|                 "Ouvindo você..."                         |
|      [Silenciar] [Legendas] [Encerrar sessão]             |
| Transcrição / resposta textual acessível na timeline      |
+----------------------------------------------------------+
```

### 15.3. Imagem e câmera

Entrada de imagem por anexo/captura pontual para tarefas autorizadas como examinar peça, equipamento, desenho, documento ou ocorrência. O usuário seleciona mídia, visualiza preview, remove/cancela, digita pergunta e confirma envio. O backend valida formato, tamanho, tipo efetivo, malware/content-safety conforme contrato, metadados, privacidade e regras de retenção. Extração/percepção é adapter provider-neutral: preservar proveniência, limitações, versão do método/modelo e grau de incerteza quando cabível. Imagem não prova defeito, identidade nem condição de máquina por si só; comparação com desenho/revisão exige consulta à Domain API autoritativa.

```text
[+ Mídia > Imagem | Câmera]
[Preview da imagem selecionada]  [Remover]
[Pergunta: "Compare esta peça com o desenho aprovado"] [Enviar]
→ mídia autorizada / MediaRef (se contrato existir)
→ perception → Evidence → decisão/orquestração → resposta
```

### 15.4. Vídeo assistido e compartilhamento de tela

Escalonamento de produto alinhado à spec `53`:
- **V1** imagem/frame pontual (primeiro alvo).
- **V2** vídeo curto sob demanda, bounded em duração/tamanho/propósito.
- **V3** amostragem temporal de sessão assistida, autorizada com captura visível.
- **V4** assistência audiovisual contínua somente se tecnologia, rede, latência, custo, retenção, safety e Policy justificarem.

Wireframe: painel de preview de câmera com estado `Nenhuma captura ativa`; botões de `Capturar imagem`, `Gravar trecho` e `Parar` apenas quando capacidades reais estão disponíveis; pergunta contextual e timeline com resultado/evidências. Compartilhamento de tela em Meeting/Workspace requer consentimento específico, seleção de superfície, indicador persistente, redaction quando cabível e encerramento inequívoco. Screen share e câmera não concedem AuthZ adicional; não fazem DOM automation nem comandos industriais livres. Não armazenar/transmitir vídeo contínuo indiscriminadamente, nem manter tracking oculto de pessoas.

```text
+----------------- Assistência visual ---------------------+
| [Prévia câmera — captura INATIVA]                        |
| [Capturar imagem]   [Gravar trecho]   [Encerrar]         |
| Pergunte: "O que pode explicar esta ocorrência?"         |
| [Imagem/vídeo selecionado] [Remover] [Enviar]            |
+---------------------------------------------------------+
```

### 15.5. Composer multimodal unificado — sem prometer funcionalidades falsas

```text
+---------------------------------------------------------+
| Pergunte ou mostre algo à DÉLIA...                       |
| [Anexo/preview se selecionado]                            |
| [+ Mídia ▾]                         [Ditado] [Voz] [Enviar]|
+---------------------------------------------------------+
Menu FUTURO: imagem; documento; vídeo curto; câmera; tela.
```

**Aparência final depende da capability disponível**: um item TARGET pode existir no wireframe, mas não deve virar botão habilitado na produção sem contrato/owner/dispositivo/policy. Upload de mídia não autoriza a persistência, nem deve usar storage ou runtime do Minha DELPI Chat.

### 15.6. Interações, feedback e acessibilidade

- Indicadores visíveis para microfone, câmera, tela, transcrição e gravação persistente. Diferenciar captura transitória de retenção.
- Estados UX de permissão recusada, dispositivo ausente, captura interrompida, transcrição incerta, limite excedido, mídia rejeitada, rede indisponível, envio cancelado, source denied e capability indisponível.
- UI de voz nunca oculta o texto/legendas; não depender exclusivamente de cores, som, pulse, vibração ou gestos. Permitir teclado, touch, screen reader, `prefers-reduced-motion`, foco claro e microfone desligado.
- Preview seguro com opção `remover` antes do envio. Ao encerrar uma sessão, cessar efetivamente captura e liberar device; nunca afirmar que storage remoto foi excluído sem postcondition.
- Conservar provenance separada de saída gerada; capability multimodal não promove hipótese de visão/fala a FACT.
- Ações materiais extraídas de áudio/vídeo seguem Core AuthZ, Domain authority, Policy/Decision, confirmação, idempotência, audit e Outcome. `voz != autorização`; `biometric match != AuthN`; `visual detection != industrial safety`.

### 15.7. Dados e segurança

Definir contrato **antes** de runtime para: purpose, consent, captura, processamento externo, tipos MIME e limite de tamanho/duração, streaming/latência quando aplicável, identificadores de mídia, relação com turn/session/evidence, tratamento de erros, tenant/user isolation, malware, media privacy, retenção transitória/bruta e derivada, redaction, export/delete e observabilidade sem conteúdos sensíveis. Templates biométricos isolados. Consentimento para áudio não presume consentimento para vídeo, câmera ou armazenamento. Caso owner não autorize, comportamento fail-closed. MCP/provider metadata e mídia são UNTRUSTED DATA.

### 15.8. Reuso e contratualização antes do Devin

`EXISTING_EQUIVALENT=TO_INVENTORY` para Web Media API/device capture, upload/preview, player, transcript captions, síntese/ditado, backend ingestion, MediaRef, media storage, event/session transport e componentes `plugin-ui`. `REUSE_DECISION=TO_DECIDE` por item. Candidatos `SpeechToTextPort`, `TextToSpeechPort`, `MediaIngestPort`, `VisionAnalysisPort`, `RealtimeMediaSessionPort`, `MediaStoragePort` no doc `53` **não são contratos aprovados nem demanda para criar todos**. Portal controla host; DÉLIA contract/orchestration/evidence; providers sob adapters; Domain APIs continuam authoritative; Safety separada.

Ordem candidata: inventário e decisão de contrato → ditado revisável → saída de áudio com legendas → foto/anexo de imagem → vídeo curto → vídeo assistido/real-time mediante gates específicos. Fase e NEXT vêm do Plano Mestre e ledger, não desta sequência ilustrativa.

### 15.9. Critérios de aceite para futuro PR

- Captura sempre com permissão e indicadores reais; interromper realmente encerra captura.
- A resposta em texto permanece acessível, incluindo transcrição de voz e limitações de mídia.
- Mídia passa pelo mesmo AuthZ/Policy/Domain/Decision Gates que texto; nenhuma execução industrial por modelo livre.
- Estados reproduzem eventos e erros verdadeiros, sem streaming falso.
- Privacidade, retenção e exclusão testadas segundo contrato, inclusive device compartilhado.
- Provider-neutral, sem credenciais ou conteúdo de mídia em prompt/log comum indevido.
- Loading, cancelamento, retries e consentimento mostram consequências verdadeiras.
- Testes/evals de generalização, segurança e resultado no SHA e config avaliados; sem provas, `PENDING/INCONCLUSIVE`.


## 16. Decisão de produto — Ditado Inteligente primeiro; Voz Live posterior (2026-10-09)

**Decisão do Product Master:** há **duas experiências de voz independentes do ponto de vista de UX**, mas reutilizando a mesma identidade DÉLIA e o mesmo fluxo governado de interação. **(A) Ditado inteligente** é a primeira entrega multimodal candidata. **(B) Live/voz conversacional bidirecional** é uma entrega posterior. Esta decisão substitui a indefinição de prioridade apontada na §15.2; a escolha de push-to-talk versus chamada contínua é relevante apenas para desenhar a experiência Live futura. **Não autoriza iniciar fase ou implementar provider, storage, ports, endpoints ou UI sem gates do Plano Mestre.**

### 16.1. Caso A — ditado inteligente com transcrição e ajuste por IA

**Objetivo:** o usuário fala uma pergunta para a DÉLIA no composer existente, em experiência semelhante a ditado de assistentes modernos. A captura gera uma transcrição; uma etapa IA **opcional/contratada e conservadora** melhora legibilidade, pontuação, ortografia e construção frasal; o usuário **revê e edita** o texto; ao clicar Enviar, esse texto percorre o **mesmo** caminho atual de interação `POST /interaction/turns`, sujeito aos mesmos gates.

```text
Composer existente
  └── [Microfone — iniciar captura consentida]
          └── [Capturando | indicador real + Parar + Cancelar]
                 └── [Transcrição em processamento]
                        └── [Texto reconhecido: original disponível]
                               └── [Ajuste conservador IA, se autorizado]
                                      └── [Texto ajustado, totalmente editável]
                                             └── [Revisar / Enviar]
                                                    └── interação DÉLIA normal
```

**Não enviar automaticamente na primeira entrega.** O simples ato de gravar/transcrever/ajustar não dispara MCP, Domain API, pesquisa externa ou ação material. Ajuste IA é preparação de INPUT, não Evidence/FACT, planejamento operacional, autorização ou decisão de negócio. O texto final enviado é a versão confirmada pelo usuário.

#### Wireframe textual WF-06

```text
+---------------- COMPOSER DÉLIA ------------------------------+
| Pergunte à DÉLIA...                                         |
|                                                              |
| [+ Mídia]                            [🎙 Ditado] [Enviar]     |
+--------------------------------------------------------------+

Estado: [🎙 Microfone ativo] [ondas visuais suaves]   [Parar] [Cancelar]
Estado: [Transcrevendo áudio...]                      [Cancelar]
Estado: [Ajustando texto...]                          [Cancelar]
+--------------------------------------------------------------+
| Transcrição original                        [Ver original]   |
| Texto ajustado pela IA — editável                             |
| "DÉLIA, mostre os indicadores de produção..."                 |
|                                      [Editar] [Enviar]        |
+--------------------------------------------------------------+
```

**Observação visual:** indicadores de captura refletem estado real de microfone, não animação simulada; `prefers-reduced-motion`, teclado e leitor de tela suportados. Nunca exibir opção ainda não implementada como habilitada.

### 16.2. Limites do ajuste por IA

O revisor de linguagem pode: corrigir erros de fala/transcrição evidentes, pontuação, grafia, concordância, segmentação e organização, mantendo o propósito original. **Não pode**: acrescentar intenção, transformar pedido consultivo em comando, substituir números/decimais/unidades, códigos de produto, OPs, nomes próprios, IDs, períodos, unidades fabris, quantidades ou negações sem validação explícita. Termos técnicos ambíguos devem permanecer como falados/transcritos e/ou ser sinalizados ao usuário, não silenciosamente corrigidos pelo modelo. Prompt injection contido no áudio/transcrito é dado não confiável.

**UX de confiança:** manter transcrição original acessível, deixar o texto final editável, sinalizar alterações relevantes e dar escolha de usar original quando possível. Falha do ajuste IA não deve impedir usar transcrição bruta revisada; falha STT deve apresentar erro e possibilidade de digitar. Não inventar texto quando o áudio é incompreensível. Evitar envio silencioso a terceiros; qualquer processamento externo depende de policy/consent e contrato.

**Exemplo ilustrativo:**
- Original: “delia me mostra os indicador de produção da unidade de santa catarina de ontem e compara com semana passada”.
- Ajustado: “DÉLIA, mostre os indicadores de produção da unidade de Santa Catarina de ontem e compare com os da semana passada.”
- O modelo não presume que números, semanas ou métricas ficaram inequívocos nem transforma a frase em autorização para executar ações.

### 16.3. Caso B — Live em entrega posterior

**Visão alvo:** sessão explícita de voz bidirecional, na qual usuário pergunta e DÉLIA responde por áudio com transcrição/legendas; possibilidade futura de turn-taking, interrupção, retomada e interações com especialistas/conectores autorizados. Precisa de sessão de mídia, áudio/STT/TTS/realtime, latência, observabilidade, gestão de dispositivos, autorização e controle de custos. Não misturar sua implementação com o ditado.

```text
[Iniciar Live] → [Microfone ativo / Ouvindo] ↔ [DÉLIA respondendo]
        ↘ [Legendas/texto na mesma timeline]
        ↘ [Silenciar] [Encerrar] [Retomar quando permitido]
```

Interações por voz não fornecem Identity/AuthZ; toda material write mantém live Core AuthZ, Domain authority, Policy/Decision e Outcome. **Live continua TARGET e não pertence à primeira entrega de ditado.**

### 16.4. Reuso, contratos e escopo do futuro Devin

`EXISTING_EQUIVALENT=TO_INVENTORY`, `REUSE_DECISION=TO_DECIDE` para componentes de composer/captura/preview, STT, revisão linguística e componentes de feedback. Antes de propor `SpeechToTextPort` ou revisão-model-service, buscar capacidades existentes, Domain API, MCP/A2A, adapters, shared UI e contratos; escolher o menor boundary correto. Não acoplar frontend diretamente a SDK do provider sem contrato e segurança. Não reutilizar o runtime/tabelas/frontend Minha DELPI Chat.

**Gates prévios:** dono da captura e pipeline, AuthN/AuthZ/policy, consentimento, acesso à mídia, MIME/limites/duração, retenção/transient deletion, tratamento de falhas, provedores e external processing, request/response e erros, observabilidade com minimização, idempotência/retry, e critérios de aceitação. Em áudio de usuários/terceiros, capturar apenas com autorização informada. Classificar `STT=TO_INVENTORY`; `AI_TEXT_ADJUSTMENT=PLANNED`; `LIVE=TARGET`; `RUNTIME_PROOF=PENDING`. Documentação não libera C4/C5 nem autoriza Devin a implementar.

### 16.5. Aceitação funcional futura

1. Microfone só inicia após ação do usuário, permissão e indicador visível; Parar/Cancelar encerram captura efetiva.
2. STT fornece texto passível de revisão, sem enviar automaticamente.
3. Ajuste melhora redação **sem alterar significado, negadores, números, unidades ou identificadores** nos conjuntos de avaliação, inclusive casos ambíguos e adversariais.
4. Original e texto ajustado podem ser conferidos; usuário pode editar o final antes de enviar.
5. Apenas o texto confirmado segue via contrato atual da DÉLIA; revisão linguística não aciona ferramentas.
6. Falhas STT/IA e permissões negadas têm fallback seguro; sem mensagens enganosas de sucesso.
7. Retenção/exclusão de áudio e transcrições e disclosure de processamento externo obedecem políticas aprovadas.
8. Mesma UX funcional em página completa e dock, respeitando dimensões e acessibilidade.
9. Live não é incluído inadvertidamente no escopo/PR da primeira entrega.
10. Testar generalização, precisão em termos DELPI, segurança/privacidade, outcome, e registrar evidência no SHA/config avaliado.

**Encaminhamento:** quando o Plano Mestre autorizar, Devin começa por inventário + contrato do ditado, depois UX e implementação mínima governada. A conversa Live deve ser planejada em tarefa/aceite posterior.


**Complemento especializado:** [70 — Atividade de Ferramentas, Fontes e Transparência Operacional](./70-tool-activity-and-source-transparency-ux-specification.md). Define WF-T01–WF-T06 e a distinção entre consultas, ações e outcomes sem duplicar a autoridade desta especificação geral.
