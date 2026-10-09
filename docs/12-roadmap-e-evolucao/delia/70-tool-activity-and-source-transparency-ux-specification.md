# DÉLIA — Atividade de Ferramentas, Fontes e Transparência Operacional

**Status:** \`APPROVED_PRODUCT_UX_DIRECTION\` / \`DESIGN_SPEC\`; \`IMPLEMENTATION=NOT_AUTHORIZED_BY_THIS_DOCUMENT\`.  
**Data da decisão:** 2026-10-09.  
**Escopo:** exibição de atividade observável de MCP/A2A, especialistas, Domain APIs/apps Minha DELPI, pesquisa web e integrações externas, em página completa e dock.  
**Reancoragem documental consultada:** HEAD \`540df57ad0ad4d4785d795662b05d192d8146f59\`; revalidar no SHA de execução e ler Project Instructions/\`.cursor\`, [16](./16-execution-master-plan.md), [50](./50-standalone-copilot-application-architecture.md), [17](./17-component-and-contract-map.md), [49](./49-architecture-and-design-patterns-standard.md), [51](./51-platform-integration-baseline.md), [52](./52-standalone-repository-and-bootstrap-plan.md), [21](./21-data-and-state-model.md), [20](./20-testing-and-acceptance-matrix.md), [25](./25-requirements-traceability.md), [02](./02-arquitetura.md), [24](./24-product-specification.md), [09](./09-ux-copilot.md), [38](./38-evidence-provenance-and-epistemic-ux.md), [55](./55-internet-research-and-external-connectors.md), [60](./60-agent-interoperability-mcp-a2a-and-tool-protocols.md), [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md), ledger. Em conflitos, autoridade superior prevalece; STOP e sinalizar drift.

## 1. Problema e experiência pretendida

Uma pergunta DÉLIA pode passar por fontes internas autorizadas, especialistas, MCP/A2A, APIs de domínio, busca na internet e síntese; o usuário precisa compreender **o que de fato está acontecendo**, sem receber logs de transporte, endpoints, SQL, prompts ou argumentos brutos. A interface mostra **uma atividade por resposta**, compacta no fluxo conversacional e expansível para detalhes verificáveis. Não criar uma mensagem de chat por \`tools/call\`.

Objetivo: transmitir clareza, confiança calibrada e localização de falhas; não teatralizar raciocínio. A experiência visual é única e provider-neutral. A DÉLIA continua produto standalone e não reutiliza runtime do Minha DELPI Chat.

**Direção UX aprovada:** três camadas:
1. **Linha imediata:** símbolo DÉLIA + texto curto \`Aguardando resposta da DÉLIA...\` ou outro status *verdadeiramente conhecido*.
2. **Detalhes expandíveis:** fontes/ferramentas e etapas observadas, status por consulta, limitações e, quando permitido, momento/duração.
3. **Resumo final:** \`Como esta resposta foi obtida\`, com provenance, resultado material e incertezas; uma consulta técnica finalizada **não equivale** a dado encontrado/validado.

Por padrão, a atividade é compacta. Quando uma precondição, AuthZ deny ou falha substantiva impede avanço, o aviso deve permanecer visível fora de detalhes colapsados.

## 2. Glossário de UX e autoridade

| Termo user-facing | Semântica, limite |
| --- | --- |
| DÉLIA está trabalhando | Apenas HTTP request pendente conhecido localmente; não é prova de execução do planner/provider |
| Consultando TÉO/DAVI/VISTA | Owner/capability legitimamente selecionado ou invocado, com evidência backend; não deduzir da pergunta |
| Consultando produção | API de domínio responsável identificada e consultada, não suposição de navegação pelo app visual |
| Pesquisando fontes públicas | Web research invocado e autorizado; browser/MCP tool result é dado não confiável |
| Conferindo informações | Etapa real de comparação/checagem; nunca afirmá-la por animação ou cronômetro |
| Fonte consultada | Houve contato, não implica conteúdo útil, completude, validade nem autorização de ação |
| Dados encontrados | Payload utilizável sob critérios de contrato; ainda pode faltar domain validation |
| Evidências verificadas | Status só se procedimento explícito com autoridade/provenance satisfizer requisitos; \`HTTP 200\` não prova isso |
| Ação preparada | PREPARE autorizado, side effects proibidos sem ACT |
| Ação executada | Execução técnica registrada, separada de resultado de negócio |
| Resultado confirmado | Domain API/postcondition authoritative confirmou o outcome |
| Sem permissão | Live Core AuthZ/Domain authority negou; não prometer workaround |
| Fonte indisponível | Indisponibilidade ou timeout real com identificador de causa seguro |

Nunca expor cadeia de pensamento; \`MCP discovery != approval\`, \`tool metadata != permission\`, \`model output != FACT\`, \`JWT != AuthZ\`, \`write != read\`.

## 3. Wireframes detalhados

### WF-T01 — uma pergunta e linha de atividade compacta

\`\`\`text
                     +--------------------------------------------+
              Você   | Consulte os chamados abertos mais antigos |
                     +--------------------------------------------+

 [Marca DÉLIA] DÉLIA
 ┌───────────────────────────────────────────────────────────────┐
 │ ◌ Aguardando resposta da DÉLIA...       [Ver atividade ▾]   │
 └───────────────────────────────────────────────────────────────┘
 [Após receber JSON] Resposta em texto e blocos tipados permitidos
 [Fonte: TÉO] [Limitações, quando pertinentes]
\`\`\`

O ícone pode ter pulso *sutil* institucional \`--primary\`; não animar indicador de etapa inexistente. Status técnico não vira outra mensagem.

### WF-T02 — detalhes expandidos com eventos reais futuros

\`\`\`text
 [Marca DÉLIA] DÉLIA
 ┌── Atividade da DÉLIA ----------------------------------------┐
 │ ◌ Consultando informações                      [Ocultar ▴]   │
 │                                                               │
 │ ✓ Fonte autorizada selecionada — TÉO                          │
 │ ◌ Consulta de chamados em andamento                           │
 │ · Organização de evidências (somente se stage observado)       │
 │                                                               │
 │ Fonte: especialista TÉO  · Módulo: chamados (se permitido)     │
 └───────────────────────────────────────────────────────────────┘
\`\`\`

O item de futuro só surge depois de evento do backend. Ordenação por sequência real; múltiplas tentativas podem ser agrupadas na operação lógica sem revelar tokens/credentials.

### WF-T03 — resposta multi-owner / fontes distintas

\`\`\`text
 [✓ Consultas finalizadas]                         [Detalhes ▾]
 [DAVI · dados]   [VISTA · indicadores]   [Web · referências]
 A resposta distingue informações internas autorizadas e web.
 [Fontes e referências]  [Limitações de comparabilidade]
\`\`\`

Chips são identificações neutras, não badges de confiança automática. Eventos "completed" de ferramentas não representam \`FACT\`; web externo deve ser explicitamente diferenciado de fonte oficial.

### WF-T04 — falha, acesso e precondição

\`\`\`text
 [! A consulta precisa de atenção]           [Ver detalhes ▾]
 Não foi possível acessar os chamados: vínculo requerido.
 [Próximo passo informado pelo owner, somente se contratado]
\`\`\`

Falta de permissão \`AUTHZ_DENIED\`, \`SOURCE_UNAVAILABLE\`, \`PRECONDITION_REQUIRED\` e \`WRITE_REJECTED\` são exibidos por semantics do backend. Não derivar link GLPI ou CTA de descrição MCP/LLM ou inventar \`authorize_url\`. Owner TÉO deve publicar mensagem/ação user-facing em contrato legítimo se necessário.

### WF-T05 — consultas versus ações materiais

\`\`\`text
 [Fontes consultadas]      DAVI · VISTA · Pesquisa externa
 [Ação preparada]          Prévia governada [Confirmar] [Rejeitar]
 [Ação executada]          Execução técnica (não equivale a sucesso)
 [Resultado do negócio]    ✓ Confirmado pela Domain API / ? Inconclusivo
\`\`\`

Separação visual e semântica obrigatória. Somente backend pode produzir confirmação válida com \`proposal_digest\`, \`preview_fingerprint\` e \`session_id\`; frontend não fabrica ACL, autoridade ou postcondition.

### WF-T06 — dock compacto / mobile

\`\`\`text
 ┌──────── DÉLIA ────────────────┐
 │ [Você] Qual é a situação?    │
 │ [DÉLIA] ◌ Trabalhando... ▾   │
 │ [Resposta, fontes resumidas]  │
 │ [Pergunte à DÉLIA]   [Enviar] │
 └───────────────────────────────┘
\`\`\`

Expandir detalhes em disclosure inline ou painel de detalhe móvel, jamais segunda sidebar que consuma o espaço do Portal. Mesma semântica e contratos da página completa.

## 4. Matriz de comportamento por integração

| Categoria | Cabeçalho durante evento observado | Detalhes verificáveis (se divulgáveis) | Resumo após resposta |
| --- | --- | --- | --- |
| MCP / especialista | \`Consultando TÉO\` | Nome owner/serviço e objetivo semântico, status por chamada | Fonte(s), data de referência se fornecida, limitações |
| Domain API / app DELPI | \`Consultando indicadores de produção\` | Domínio de dados, consulta semântica | Provenance Domain API, recorte/versão quando disponível |
| Pesquisa web | \`Pesquisando fontes públicas\` | Busca executada, domínios/fontes reais se citáveis | Links verificáveis, distinção explícita de fonte externa |
| Multiple owners | \`Reunindo informações\` | Suboperações por fonte e comparabilidade | Referências agrupadas + lacunas/dependências |
| Automation Hub | \`Preparando/Executando ação\` | Estado de preparo, confirmação e execução governada | Outcome authoritative quando disponível |
| MCP/A2A error | \`Fonte indisponível\` | Razão segura; retry real, se suportado e governado | Resultados parciais e limitações, sem falso sucesso |
| Core/AuthZ | \`Acesso não autorizado\` | Recusa sem vazamento da política interna | Falha clara; sem recomendação de contorno |
| Internet disabled | Não mostrar estado de pesquisa | Capability ausente/negada, se pertinente | Responder com limites sem alegar pesquisa feita |

Labels devem vir de uma projeção segura de eventos owned pelo backend, não de metadata retornada por tool; \`provider-neutral\` significa suportar novos providers sem branches no planner ou no MFE. Um app visual não equivale à API de domínio; nomear o owner correto.

## 5. Estados de atividade e regras de transição — modelo candidato, não contrato

\`\`\`text
UNKNOWN / LOCAL_PENDING
  → ACCEPTED (observado)
  → SELECTED_SOURCE (observado)
  → STARTED (observado)
  → COMPLETED | FAILED | BLOCKED | CANCELLED (observado)
  → PRESENTED (resposta emitida)
\`\`\`

Não há obrigação de percorrer todas etapas. Uma operação pode ter N subconsultas, inclusive paralelas, desde que haja correlation, idempotência de evento e ordem causal. Falhas parciais e timeout precisam permanecer visíveis. \`CANCELLED\` exige confirmação efetiva (abort visual de request não prova cancelamento remoto). \`BLOCKED\` para precondição não se confunde com \`DENIED\`.

Campos candidatos para contract discovery, **NÃO shapes aprovados**: \`turn_id\`, \`activity_id\`, \`sequence\`, \`stage_kind\`, \`semantic_label\`, \`source_category\`, \`source_display_name\`, \`started_at/completed_at\`, \`status\`, \`result_summary\`, \`limitations\`, \`provenance_refs\`, \`privacy_class\`, \`correlation_id\`. Limitar tamanho/quantidade, minimizar PII, sanitizar labels, manter seq/order, evitar clock drift e nomes sensíveis. Não mostrar duração sem medição.

## 6. Contrato atual e restrições comprovadas

Existe \`POST /interaction/turns\` com retorno HTTP JSON e projeção \`presentation.version="1"\` dentro do backend da DÉLIA. \`presentation.v1\` usa \`message_kind\`, \`semantic_status\`, \`grounding_status\`, blocos \`text\` e \`notice/owner_hint\`, \`allowed_interactions\`, mantendo campos legados de \`provenance\` e \`limitations\`. Não há evidência de SSE/eventos progressivos no contrato atual; em request pendente o MFE pode afirmar somente a espera local.

**Primeiro rollout UI, se autorizado:** mostrar \`Aguardando resposta da DÉLIA\`, depois renderizar resposta e provenance efetivamente recebidas. Não afirmar \`TÉO consultado em andamento\` sem canal real. \`owner_hint\` pode estar duplicado em conteúdo legado e notice, portanto garantir render único. Fail-safe para versions/blocks desconhecidos. Sem tabela/gráfico/áudio/video/atividade estruturada não contratados.

**Evolução futura sob decisão explícita:** inventariar infraestrutura de tracing/activity/event stream e front-end. Extensão contratual governada para activity events; selecionar transporte (SSE, polling ou outro) apenas após comparar mecanismos existentes, owner, scale/latência, autenticação, replay/correlation, error, backpressure, compatibilidade, custo e cancelamento. \`SSE\` é candidato, não decisão congelada. Não transformar logs técnicos em eventos de UI automaticamente.

## 7. Hierarquia da transparência e proteção de dados

- **Camada pública mínima:** status curto, duração se real, nome semântico do serviço e resultado material.
- **Disclosure do usuário:** etapas observadas, nome do owner, fontes/citações, limitações, resultado parcial, quando consentidos/divulgáveis.
- **Observabilidade operacional restrita:** traces, correlation IDs, auditoria e logs seguros em seu owner; não despejar no chat.
- **Nunca mostrar:** prompt chain-of-thought, raciocínio oculto, tokens, credentials, secret headers, payload brutos de MCP, embeddings, estratégia interna, dados de terceiros sem permissão, esquemas confidenciais, endereços privados ou URLs de auth inferidas.

Links de fonte somente se URL e direito de divulgação forem aprovados por contrato e policy. A DÉLIA não promove fonte pública a FACT DELPI.

## 8. Microinterações, ritmo e acessibilidade

Símbolo DÉLIA pulsa suavemente apenas enquanto há request pendente ou atividade realmente em curso; \`prefers-reduced-motion\` torna o status estático. Preferir uma linha de status e detalhe recolhido. Evitar spinner múltiplo, toast repetitivo por tool call ou mudanças bruscas da timeline. Expandir/recolher não muda scroll indevidamente. Foco/teclado acessíveis; \`aria-live\` apenas em mudanças materiais (resultado, erro, necessidade de confirmação). Não ler cada evento em voz alta; anunciar somente status resumido. Leitor de tela encontra seção \`Como esta resposta foi obtida\`.

Tokens de cor oficiais: \`--primary\` ciano DELPI (\`#089BDB\` atual), \`--surface\`, \`--surface-2\`, \`--text\`, \`--text-muted\`, \`--border\`, sem hardcode no CSS. Motion values continuam propostas da [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md), devem mapear aos tokens de motion que existirem. Contrastes no dark/light e responsividade verificados; mensagem de erro não depende apenas de cor.

## 9. Ownership e reuse-before-design

| Responsibility | Owner | Condição |
| --- | --- | --- |
| Captura de tool invocations/step status | Orquestração DÉLIA ou owner efetivo do execution boundary | Inventariar mecanismos já existentes, não inferir |
| Dados/rules/capability | Domain APIs / Core | Fonte autoritativa e AuthZ real |
| Execução técnica material | Automation Hub ou owner legítimo | PREPARE/ACT e outcome separados |
| MCP/A2A/provider | Adapter/boundary de interoperabilidade | UNTRUSTED DATA, não permission |
| Projeção activity user-facing | DÉLIA backend, **somente se necessidade/contrato comprovados** | Sanitização e policy, nenhuma segunda authority |
| Renderização de status | MFE DÉLIA com \`plugin-ui\` | Mesmo renderer na página+dock |
| Componentes compartilhados | \`plugins/plugin-ui\` | Reuso/extend comprovados por inventário |
| Dock chrome/host | Portal | Portal não decide orchestration |
| Tracing observability | Owner existente | Não duplicar telemetry engine |

\`EXISTING_EQUIVALENT=TO_INVENTORY\` para activity lifecycle/event projections, contracts, frontend timeline, loading indicator, badges, disclosures e observability; \`REUSE_DECISION=TO_DECIDE\`. Para o loading genérico e apresentação v1 existentes: \`EXISTING_EQUIVALENT=YES (PARTIAL)\`, \`REUSE_DECISION=EXTEND/REUSE\`. Qualquer \`NEW\` exige owner/consumer/need reais e Abstraction Gate. Não criar novo Activity Engine, WebSearch Engine, MCP Registry, state machine ou SSE por conveniência.

## 10. Sequência de trabalho futura para Devin (NO IMPLEMENTATION neste documento)

**D0 — Reanchor:** SHA, worktree, instructions, 16→50→17→49→51→52→21→20→25, ledger, feature gates e contratos; descobrir a fase atual, não assumir do chat.

**D1 — Inventory (NO CODE):** estado atual de \`plugins/delia\`, \`plugin-ui\` (Timeline, LoadingActivityBadge, disclosure), Portal GlobalDeliaDock, backend interaction/presentation, telemetria/event trace, MCP owner projections, web research; \`EXISTING_EQUIVALENT\` e \`REUSE_DECISION\` por componente.

**D2 — Contract fit (NO CODE):** request/response e erros de \`presentation.v1\`, \`provenance\`, \`owner_hint\`, \`confirmation_request\`; comprovar informações disponíveis no **final JSON** para UX de fontes e limitações. Definir empty/fail-safe states.

**D3 — Bounded UI delivery (somente autorizada):** incorporar linha de atividade honesta durante request, disclosure de fontes ao concluir, avisos e estados, dentro da timeline existente. Usar design system, a11y e shared plugin-ui. Dock usa mesmo componente.

**D4 — Progressive activity discovery:** se produto exige atualizações reais, elaborar ADR/contrato semântico com owner/safety/privacy; decidir SSE/polling/event mechanism com evidência; **voltar à coordenação para autorização**. Sem mudanças no modelo de Authority/Policy.

**D5 — Verification:** tests desktop/dock/mobile/theme, a11y/reduced motion, malicious source labels, missing events, long statuses, partial failures, timeout/abort, slow request, parallel tools, multi-owner provenance, Core AuthZ denial, confirmation gated, web external vs internal, idempotency; código e outcome evidence no SHA; residual search e ledger.

**Acceptance verdict** somente \`ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE\` por review separado.

## 11. Critérios verificáveis de aceite e proibições

- [ ] Request pendente sem eventos = label genérico honesto; sem ferramenta fictícia.
- [ ] Por turn, um bloco de atividade expansível; não uma mensagem por tool call.
- [ ] Nome semântico de provider/app/web apenas quando evidência e disclosure permitirem.
- [ ] Distinção técnica \`completed\` vs dado útil vs outcome de negócio confirmado.
- [ ] Provenance e limitações preservadas, web pública marcada como externa.
- [ ] \`AUTHZ_DENIED\`, \`PRECONDITION_REQUIRED\` e falhas parciais visíveis, sem promessa de autorização.
- [ ] Confirmar/rejeitar apenas payload governado e após live AuthZ/Domain checks.
- [ ] Sem exibição de reasoning privado, secrets, tool metadata brutos ou URLs não autorizadas.
- [ ] Sem novo planner/engine paralelo; reutilização antes de design demonstrada.
- [ ] Mesma UI na página e dock, responsive, acessível, light/dark e reduzido movimento.
- [ ] Sem inventar SSE/realtime/histórico; evolução depende de contrato e fase.
- [ ] Testes/evals com resultado final, SHAs, config, evidence/outcome, residual search.

## 12. Status e handoff

**PLANNED:** direções de UX WF-T01..T06, camadas de transparência, distinção de consulta/action/outcome, regras de microinteração.  
**PROVEN (apenas no inventário prévio, revalidar):** \`presentation.v1\` de resposta HTTP JSON e componentes visuais candidatos.  
**TO_INVENTORY:** traces, eventos de atividade em tempo real, engine/projection existente, disclosure de fontes por owner, tipo de sessão, disponibilidade de web, contratos/a11y reais.  
**TARGET:** progressive activity UI com eventos verdadeiros, transporte aprovado.  
**TEST_NOT_RUN:** nenhuma implementação/teste executado nesta tarefa documental.

Este documento complementa a [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md) e não altera o Plano Mestre, a fase, o ledger de execução ou o estado do produto. Handoff para chat de Frontend/UX → Integration Review → Coordination antes de autorização ao Devin.
