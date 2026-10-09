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
