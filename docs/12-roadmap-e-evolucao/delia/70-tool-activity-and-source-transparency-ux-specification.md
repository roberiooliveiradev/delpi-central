# DÉLIA — Atividade de Ferramentas, Fontes e Transparência Operacional

**Status:** `APPROVED_PRODUCT_UX_DIRECTION` / `DESIGN_SPEC`; `IMPLEMENTATION=NOT_AUTHORIZED_BY_THIS_DOCUMENT`.  
**Data da decisão:** 2026-10-09.  
**Escopo:** exibição de atividade observável de MCP/A2A, especialistas, Domain APIs/apps Minha DELPI, pesquisa web e integrações externas, em página completa e dock.  
**Reancoragem documental consultada:** HEAD `540df57ad0ad4d4785d795662b05d192d8146f59`; revalidar no SHA de execução e ler Project Instructions/`.cursor`, [16](./16-execution-master-plan.md), [50](./50-standalone-copilot-application-architecture.md), [17](./17-component-and-contract-map.md), [49](./49-architecture-and-design-patterns-standard.md), [51](./51-platform-integration-baseline.md), [52](./52-standalone-repository-and-bootstrap-plan.md), [21](./21-data-and-state-model.md), [20](./20-testing-and-acceptance-matrix.md), [25](./25-requirements-traceability.md), [02](./02-arquitetura.md), [24](./24-product-specification.md), [09](./09-ux-copilot.md), [38](./38-evidence-provenance-and-epistemic-ux.md), [55](./55-internet-research-and-external-connectors.md), [60](./60-agent-interoperability-mcp-a2a-and-tool-protocols.md), [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md), ledger. Em conflitos, autoridade superior prevalece; STOP e sinalizar drift.

## 1. Problema e experiência pretendida

Uma pergunta DÉLIA pode passar por fontes internas autorizadas, especialistas, MCP/A2A, APIs de domínio, busca na internet e síntese; o usuário precisa compreender **o que de fato está acontecendo**, sem receber logs de transporte, endpoints, SQL, prompts ou argumentos brutos. A interface mostra **uma atividade por resposta**, compacta no fluxo conversacional e expansível para detalhes verificáveis. Não criar uma mensagem de chat por `tools/call`.

Objetivo: transmitir clareza, confiança calibrada e localização de falhas; não teatralizar raciocínio. A experiência visual é única e provider-neutral. A DÉLIA continua produto standalone e não reutiliza runtime do Minha DELPI Chat.

**Direção UX aprovada:** três camadas:
1. **Linha imediata:** símbolo DÉLIA + texto curto `Aguardando resposta da DÉLIA...` ou outro status *verdadeiramente conhecido*.
2. **Detalhes expandíveis:** fontes/ferramentas e etapas observadas, status por consulta, limitações e, quando permitido, momento/duração.
3. **Resumo final:** `Como esta resposta foi obtida`, com provenance, resultado material e incertezas; uma consulta técnica finalizada **não equivale** a dado encontrado/validado.

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
| Evidências verificadas | Status só se procedimento explícito com autoridade/provenance satisfizer requisitos; `HTTP 200` não prova isso |
| Ação preparada | PREPARE autorizado, side effects proibidos sem ACT |
| Ação executada | Execução técnica registrada, separada de resultado de negócio |
| Resultado confirmado | Domain API/postcondition authoritative confirmou o outcome |
| Sem permissão | Live Core AuthZ/Domain authority negou; não prometer workaround |
| Fonte indisponível | Indisponibilidade ou timeout real com identificador de causa seguro |

Nunca expor cadeia de pensamento; `MCP discovery != approval`, `tool metadata != permission`, `model output != FACT`, `JWT != AuthZ`, `write != read`.

## 3. Wireframes detalhados

### WF-T01 — uma pergunta e linha de atividade compacta

```text
                     +--------------------------------------------+
              Você   | Consulte os chamados abertos mais antigos |
                     +--------------------------------------------+

 [Marca DÉLIA] DÉLIA
 ┌───────────────────────────────────────────────────────────────┐
 │ ◌ Aguardando resposta da DÉLIA...       [Ver atividade ▾]   │
 └───────────────────────────────────────────────────────────────┘
 [Após receber JSON] Resposta em texto e blocos tipados permitidos
 [Fonte: TÉO] [Limitações, quando pertinentes]
```

O ícone pode ter pulso *sutil* institucional `--primary`; não animar indicador de etapa inexistente. Status técnico não vira outra mensagem.

### WF-T02 — detalhes expandidos com eventos reais futuros

```text
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
```

O item de futuro só surge depois de evento do backend. Ordenação por sequência real; múltiplas tentativas podem ser agrupadas na operação lógica sem revelar tokens/credentials.

### WF-T03 — resposta multi-owner / fontes distintas

```text
 [✓ Consultas finalizadas]                         [Detalhes ▾]
 [DAVI · dados]   [VISTA · indicadores]   [Web · referências]
 A resposta distingue informações internas autorizadas e web.
 [Fontes e referências]  [Limitações de comparabilidade]
```

Chips são identificações neutras, não badges de confiança automática. Eventos "completed" de ferramentas não representam `FACT`; web externo deve ser explicitamente diferenciado de fonte oficial.

### WF-T04 — falha, acesso e precondição

```text
 [! A consulta precisa de atenção]           [Ver detalhes ▾]
 Não foi possível acessar os chamados: vínculo requerido.
 [Próximo passo informado pelo owner, somente se contratado]
```

Falta de permissão `AUTHZ_DENIED`, `SOURCE_UNAVAILABLE`, `PRECONDITION_REQUIRED` e `WRITE_REJECTED` são exibidos por semantics do backend. Não derivar link GLPI ou CTA de descrição MCP/LLM ou inventar `authorize_url`. Owner TÉO deve publicar mensagem/ação user-facing em contrato legítimo se necessário.

### WF-T05 — consultas versus ações materiais

```text
 [Fontes consultadas]      DAVI · VISTA · Pesquisa externa
 [Ação preparada]          Prévia governada [Confirmar] [Rejeitar]
 [Ação executada]          Execução técnica (não equivale a sucesso)
 [Resultado do negócio]    ✓ Confirmado pela Domain API / ? Inconclusivo
```

Separação visual e semântica obrigatória. Somente backend pode produzir confirmação válida com `proposal_digest`, `preview_fingerprint` e `session_id`; frontend não fabrica ACL, autoridade ou postcondition.

### WF-T06 — dock compacto / mobile

```text
 ┌──────── DÉLIA ────────────────┐
 │ [Você] Qual é a situação?    │
 │ [DÉLIA] ◌ Trabalhando... ▾   │
 │ [Resposta, fontes resumidas]  │
 │ [Pergunte à DÉLIA]   [Enviar] │
 └───────────────────────────────┘
```

Expandir detalhes em disclosure inline ou painel de detalhe móvel, jamais segunda sidebar que consuma o espaço do Portal. Mesma semântica e contratos da página completa.

## 4. Matriz de comportamento por integração

| Categoria | Cabeçalho durante evento observado | Detalhes verificáveis (se divulgáveis) | Resumo após resposta |
| --- | --- | --- | --- |
| MCP / especialista | `Consultando TÉO` | Nome owner/serviço e objetivo semântico, status por chamada | Fonte(s), data de referência se fornecida, limitações |
| Domain API / app DELPI | `Consultando indicadores de produção` | Domínio de dados, consulta semântica | Provenance Domain API, recorte/versão quando disponível |
| Pesquisa web | `Pesquisando fontes públicas` | Busca executada, domínios/fontes reais se citáveis | Links verificáveis, distinção explícita de fonte externa |
| Multiple owners | `Reunindo informações` | Suboperações por fonte e comparabilidade | Referências agrupadas + lacunas/dependências |
| Automation Hub | `Preparando/Executando ação` | Estado de preparo, confirmação e execução governada | Outcome authoritative quando disponível |
| MCP/A2A error | `Fonte indisponível` | Razão segura; retry real, se suportado e governado | Resultados parciais e limitações, sem falso sucesso |
| Core/AuthZ | `Acesso não autorizado` | Recusa sem vazamento da política interna | Falha clara; sem recomendação de contorno |
| Internet disabled | Não mostrar estado de pesquisa | Capability ausente/negada, se pertinente | Responder com limites sem alegar pesquisa feita |

Labels devem vir de uma projeção segura de eventos owned pelo backend, não de metadata retornada por tool; `provider-neutral` significa suportar novos providers sem branches no planner ou no MFE. Um app visual não equivale à API de domínio; nomear o owner correto.

## 5. Estados de atividade e regras de transição — modelo candidato, não contrato

```text
UNKNOWN / LOCAL_PENDING
  → ACCEPTED (observado)
  → SELECTED_SOURCE (observado)
  → STARTED (observado)
  → COMPLETED | FAILED | BLOCKED | CANCELLED (observado)
  → PRESENTED (resposta emitida)
```

Não há obrigação de percorrer todas etapas. Uma operação pode ter N subconsultas, inclusive paralelas, desde que haja correlation, idempotência de evento e ordem causal. Falhas parciais e timeout precisam permanecer visíveis. `CANCELLED` exige confirmação efetiva (abort visual de request não prova cancelamento remoto). `BLOCKED` para precondição não se confunde com `DENIED`.

Campos candidatos para contract discovery, **NÃO shapes aprovados**: `turn_id`, `activity_id`, `sequence`, `stage_kind`, `semantic_label`, `source_category`, `source_display_name`, `started_at/completed_at`, `status`, `result_summary`, `limitations`, `provenance_refs`, `privacy_class`, `correlation_id`. Limitar tamanho/quantidade, minimizar PII, sanitizar labels, manter seq/order, evitar clock drift e nomes sensíveis. Não mostrar duração sem medição.

## 6. Contrato atual e restrições comprovadas

Existe `POST /interaction/turns` com retorno HTTP JSON e projeção `presentation.version="1"` dentro do backend da DÉLIA. `presentation.v1` usa `message_kind`, `semantic_status`, `grounding_status`, blocos `text` e `notice/owner_hint`, `allowed_interactions`, mantendo campos legados de `provenance` e `limitations`. Não há evidência de SSE/eventos progressivos no contrato atual; em request pendente o MFE pode afirmar somente a espera local.

**Primeiro rollout UI, se autorizado:** mostrar `Aguardando resposta da DÉLIA`, depois renderizar resposta e provenance efetivamente recebidas. Não afirmar `TÉO consultado em andamento` sem canal real. `owner_hint` pode estar duplicado em conteúdo legado e notice, portanto garantir render único. Fail-safe para versions/blocks desconhecidos. Sem tabela/gráfico/áudio/video/atividade estruturada não contratados.

**Evolução futura sob decisão explícita:** inventariar infraestrutura de tracing/activity/event stream e front-end. Extensão contratual governada para activity events; selecionar transporte (SSE, polling ou outro) apenas após comparar mecanismos existentes, owner, scale/latência, autenticação, replay/correlation, error, backpressure, compatibilidade, custo e cancelamento. `SSE` é candidato, não decisão congelada. Não transformar logs técnicos em eventos de UI automaticamente.

## 7. Hierarquia da transparência e proteção de dados

- **Camada pública mínima:** status curto, duração se real, nome semântico do serviço e resultado material.
- **Disclosure do usuário:** etapas observadas, nome do owner, fontes/citações, limitações, resultado parcial, quando consentidos/divulgáveis.
- **Observabilidade operacional restrita:** traces, correlation IDs, auditoria e logs seguros em seu owner; não despejar no chat.
- **Nunca mostrar:** prompt chain-of-thought, raciocínio oculto, tokens, credentials, secret headers, payload brutos de MCP, embeddings, estratégia interna, dados de terceiros sem permissão, esquemas confidenciais, endereços privados ou URLs de auth inferidas.

Links de fonte somente se URL e direito de divulgação forem aprovados por contrato e policy. A DÉLIA não promove fonte pública a FACT DELPI.

## 8. Microinterações, ritmo e acessibilidade

Símbolo DÉLIA pulsa suavemente apenas enquanto há request pendente ou atividade realmente em curso; `prefers-reduced-motion` torna o status estático. Preferir uma linha de status e detalhe recolhido. Evitar spinner múltiplo, toast repetitivo por tool call ou mudanças bruscas da timeline. Expandir/recolher não muda scroll indevidamente. Foco/teclado acessíveis; `aria-live` apenas em mudanças materiais (resultado, erro, necessidade de confirmação). Não ler cada evento em voz alta; anunciar somente status resumido. Leitor de tela encontra seção `Como esta resposta foi obtida`.

Tokens de cor oficiais: `--primary` ciano DELPI (`#089BDB` atual), `--surface`, `--surface-2`, `--text`, `--text-muted`, `--border`, sem hardcode no CSS. Motion values continuam propostas da [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md), devem mapear aos tokens de motion que existirem. Contrastes no dark/light e responsividade verificados; mensagem de erro não depende apenas de cor.

## 9. Ownership e reuse-before-design

| Responsibility | Owner | Condição |
| --- | --- | --- |
| Captura de tool invocations/step status | Orquestração DÉLIA ou owner efetivo do execution boundary | Inventariar mecanismos já existentes, não inferir |
| Dados/rules/capability | Domain APIs / Core | Fonte autoritativa e AuthZ real |
| Execução técnica material | Automation Hub ou owner legítimo | PREPARE/ACT e outcome separados |
| MCP/A2A/provider | Adapter/boundary de interoperabilidade | UNTRUSTED DATA, não permission |
| Projeção activity user-facing | DÉLIA backend, **somente se necessidade/contrato comprovados** | Sanitização e policy, nenhuma segunda authority |
| Renderização de status | MFE DÉLIA com `plugin-ui` | Mesmo renderer na página+dock |
| Componentes compartilhados | `plugins/plugin-ui` | Reuso/extend comprovados por inventário |
| Dock chrome/host | Portal | Portal não decide orchestration |
| Tracing observability | Owner existente | Não duplicar telemetry engine |

`EXISTING_EQUIVALENT=TO_INVENTORY` para activity lifecycle/event projections, contracts, frontend timeline, loading indicator, badges, disclosures e observability; `REUSE_DECISION=TO_DECIDE`. Para o loading genérico e apresentação v1 existentes: `EXISTING_EQUIVALENT=YES (PARTIAL)`, `REUSE_DECISION=EXTEND/REUSE`. Qualquer `NEW` exige owner/consumer/need reais e Abstraction Gate. Não criar novo Activity Engine, WebSearch Engine, MCP Registry, state machine ou SSE por conveniência.

## 10. Sequência de trabalho futura para Devin (NO IMPLEMENTATION neste documento)

**D0 — Reanchor:** SHA, worktree, instructions, 16→50→17→49→51→52→21→20→25, ledger, feature gates e contratos; descobrir a fase atual, não assumir do chat.

**D1 — Inventory (NO CODE):** estado atual de `plugins/delia`, `plugin-ui` (Timeline, LoadingActivityBadge, disclosure), Portal GlobalDeliaDock, backend interaction/presentation, telemetria/event trace, MCP owner projections, web research; `EXISTING_EQUIVALENT` e `REUSE_DECISION` por componente.

**D2 — Contract fit (NO CODE):** request/response e erros de `presentation.v1`, `provenance`, `owner_hint`, `confirmation_request`; comprovar informações disponíveis no **final JSON** para UX de fontes e limitações. Definir empty/fail-safe states.

**D3 — Bounded UI delivery (somente autorizada):** incorporar linha de atividade honesta durante request, disclosure de fontes ao concluir, avisos e estados, dentro da timeline existente. Usar design system, a11y e shared plugin-ui. Dock usa mesmo componente.

**D4 — Progressive activity discovery:** se produto exige atualizações reais, elaborar ADR/contrato semântico com owner/safety/privacy; decidir SSE/polling/event mechanism com evidência; **voltar à coordenação para autorização**. Sem mudanças no modelo de Authority/Policy.

**D5 — Verification:** tests desktop/dock/mobile/theme, a11y/reduced motion, malicious source labels, missing events, long statuses, partial failures, timeout/abort, slow request, parallel tools, multi-owner provenance, Core AuthZ denial, confirmation gated, web external vs internal, idempotency; código e outcome evidence no SHA; residual search e ledger.

**Acceptance verdict** somente `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE` por review separado.

## 11. Critérios verificáveis de aceite e proibições

- [ ] Request pendente sem eventos = label genérico honesto; sem ferramenta fictícia.
- [ ] Por turn, um bloco de atividade expansível; não uma mensagem por tool call.
- [ ] Nome semântico de provider/app/web apenas quando evidência e disclosure permitirem.
- [ ] Distinção técnica `completed` vs dado útil vs outcome de negócio confirmado.
- [ ] Provenance e limitações preservadas, web pública marcada como externa.
- [ ] `AUTHZ_DENIED`, `PRECONDITION_REQUIRED` e falhas parciais visíveis, sem promessa de autorização.
- [ ] Confirmar/rejeitar apenas payload governado e após live AuthZ/Domain checks.
- [ ] Sem exibição de reasoning privado, secrets, tool metadata brutos ou URLs não autorizadas.
- [ ] Sem novo planner/engine paralelo; reutilização antes de design demonstrada.
- [ ] Mesma UI na página e dock, responsive, acessível, light/dark e reduzido movimento.
- [ ] Sem inventar SSE/realtime/histórico; evolução depende de contrato e fase.
- [ ] Testes/evals com resultado final, SHAs, config, evidence/outcome, residual search.

## 12. Status e handoff

**PLANNED:** direções de UX WF-T01..T06, camadas de transparência, distinção de consulta/action/outcome, regras de microinteração.  
**PROVEN (apenas no inventário prévio, revalidar):** `presentation.v1` de resposta HTTP JSON e componentes visuais candidatos.  
**TO_INVENTORY:** traces, eventos de atividade em tempo real, engine/projection existente, disclosure de fontes por owner, tipo de sessão, disponibilidade de web, contratos/a11y reais.  
**TARGET:** progressive activity UI com eventos verdadeiros, transporte aprovado.  
**TEST_NOT_RUN:** nenhuma implementação/teste executado nesta tarefa documental.

Este documento complementa a [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md) e não altera o Plano Mestre, a fase, o ledger de execução ou o estado do produto. Handoff para chat de Frontend/UX → Integration Review → Coordination antes de autorização ao Devin.


---

## 13. Especificação visual detalhada — DÉLIA Activity (decisão de produto em elaboração)

**Registro:** 2026-10-09. Esta seção detalha os exemplos visuais compartilhados pelo Product Master (atividade expansível, etapas, indicação de especialista, ferramentas e painel de fontes). **Não** representa aprovação de novo contrato, implementação, transmissão progressiva ou permissão. A direção vigente do próprio documento — linha imediata, detalhes expansíveis e resumo final — permanece preservada.

### 13.1 Componentes e ownership

| Parte | Responsabilidade visual | Origem legítima dos dados |
| --- | --- | --- |
| `ActivitySummary` | Uma linha curta por turno, com status, texto e affordance de expansão | Estado local de requisição ou projeção de atividade do backend |
| `ActivitySteps` | Linha do tempo vertical de passos comprovados | Eventos/snapshot de execução autorizado |
| `ActivityToolDetail` | Capability/ferramenta efetivamente acionada, com rótulo semântico público | Projeção backend, jamais envelopes MCP brutos |
| `ActivitySources` | Fontes consultadas, resultados disponíveis e provenance | Contrato de Evidence/provenance com disclosure aprovado |
| `ActivityOutcome` | Distinção entre consulta técnica, dados utilizáveis e postcondition autoritativa | Outcome/Evidence e autoridade de domínio |
| `ActivityInspector` | Região detalhada opcional para atividade extensa | Mesma projeção sanitizada; **TARGET** quando houver volume/contrato real |

**Abstraction Gate:** estes nomes são responsabilidades de design, **não instrução para criar seis arquivos/componentes**. Inventariar `plugins/plugin-ui` e os componentes DÉLIA antes de decidir `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. UI genérica compartilhável pode ficar no plugin-ui; adaptação de Evidence/Policy e orquestração pertence à DÉLIA.

### 13.2 Posicionamento e hierarquia

**Opção recomendada, ainda sujeita a decisão final:** linha de atividade **acima do corpo da resposta**, dentro do mesmo turno da timeline, não como card de dashboard ou mensagem separada. Durante a requisição, permanece alinhada à posição futura da resposta; depois pode ser aberta novamente. O dock usa o mesmo modelo responsivo, sem outro runtime.

```text
[Você] Qual a descrição do item 10080055?

[ícone DÉLIA] DÉLIA
   ◌ Aguardando resposta da DÉLIA…             [⌄]
   ├─ (se e somente se observado) Capacidade selecionada
   ├─ (se e somente se observado) Fonte consultada
   └─ (se e somente se observado) Etapa concluída/pendente

   [Resposta real ou aviso governado — quando disponível]
   Fonte / provenance / limitações
```

**Visual:** resumo leve sem fundo card obrigatório; ícone de status + frase de uma linha que quebra naturalmente + chevron; hover/focus visíveis. Expansão inline por clique, Enter ou Space. Estado inicial colapsado; caso de bloqueio/negação/falha material, alerta permanece visível **fora** da parte recolhida. Não forçar abertura de inspector nem rolagem quando o usuário está lendo outra mensagem.

### 13.3 Estados e microcopy: fonte de verdade

| Estado visual | Resumo permitido | Critério mínimo |
| --- | --- | --- |
| `PENDING_REQUEST` | “A DÉLIA está processando sua solicitação…” | POST pendente no frontend, sem alegar provider |
| `WAITING` | “Aguardando resposta…” | Apenas se espera de fonte/etapa vier de evento real; caso contrário usar `PENDING_REQUEST` |
| `CAPABILITY_SELECTED` | “Preparando consulta de produtos” | Selection comprovada em projeção, sem sugerir autorização |
| `TOOL_RUNNING` | “Consultando informações de produtos” | Invocação efetiva e autorizada, status real |
| `TOOL_COMPLETED` | “Consulta à fonte concluída” | Completion técnica comprovada; não inferir dados |
| `NO_DATA` | “Consulta concluída sem dados utilizáveis” | Projeção pós-validação, não apenas `0 results` de search |
| `COMPLETED` | “Atividade concluída” | Turno finalizado; tempo somente medido |
| `PARTIAL` | “Algumas fontes não responderam” | Evidência explícita de execução parcial |
| `BLOCKED` | “Uma etapa adicional é necessária” | `PRECONDITION_REQUIRED` real |
| `DENIED` | “Solicitação não autorizada” | `AUTHZ_DENIED` real |
| `FAILED` | “Não foi possível concluir a consulta” | Falha observada; não generalizar indisponibilidade |
| `CANCELLED` | “Interação interrompida” | Cancelamento confirmado, jamais presumido a partir de fechamento de UI |

Evitar **“Pensou por 14s”** ou `chain-of-thought`. Quando duração for mensurada, preferir “Atividade concluída em 14s”; nunca representar investigação, uso de MCP ou pesquisa web por timer animado. Idioma user-facing PT-BR; identificadores técnicos só em detalhes autorizados.

### 13.4 Anatomia da expansão inline

Para cada passo comprovado:
1. **Ícone** (pendente/ativo/concluído/bloqueado/falhou), com redundância textual.
2. **Título semântico:** “Consultar descrição do produto”, não nome de endpoint.
3. **Especialista/owner:** DAVI, TÉO ou VISTA **apenas se de fato selecionado/invocado e exposto por contrato**.
4. **Recurso:** capability semântica + categoria `MCP`, `A2A`, `Domain API`, `Web` quando provada; protocolo nunca tratado como autoridade.
5. **Fonte:** sistema/data owner identificado; distinguindo invocação, payload utilizável e grounding.
6. **Tempo:** início/fim/duração quando existem timestamps de confiança e granularidade autorizada.
7. **Resultado:** `concluída`, `sem dados`, `parcial`, `falhou`, `negada`; sucesso HTTP não é sucesso de negócio.

Não permitir que conteúdo remoto determine ícone de autorização, estado de policy, link ou comportamento. Não renderizar argumentos de chamada, query completa, SQL, JSON de MCP, instruções de agente, identificadores internos sensíveis, credenciais, prompt ou conteúdo privado da reflexão do modelo. Rótulos vindos de metadata devem passar pelo contrato aprovado/sanitização no backend.

### 13.5 Fontes, evidência e outcome

A UI deve distinguir quatro fatos:

- **Fonte contatada:** pedido enviado a um owner; ainda sem prova de dados úteis.
- **Dados recebidos:** conteúdo retornado, não necessariamente validado.
- **Informação fundamentada:** provenance e critérios de grounding do contrato DÉLIA satisfeitos.
- **Resultado confirmado:** Domain authority/postcondition verificou resultado material.

A expansão pode agrupar fontes por owner e deduplicar referências **sem perder atribuições ou misturar evidência de turnos diferentes**. Para fonte externa/web, marcar origem externa e não promover resultado de pesquisa a FACT. Se existir autorização explícita para abrir fonte, link deve ser real, seguro e checado por contrato; não construir URL ou botão a partir de strings de tool.

### 13.6 Inspector lateral (evolução condicionada)

**TARGET/CONTRACT_REQUIRED**, não parte da primeira entrega só porque aparece na arte. Quando permitido, exibir título “Atividade”, resumo do turno, sequência de etapas, fontes, limitações e outcome; conservar a timeline e composer em largura utilizável. Em dock estreito, priorizar o painel inline; inspector lateral não deve reduzir a conversa a largura impraticável nem esconder confirmações críticas. Abertura e fechamento por controles com foco/restauração apropriados. Sem logs de transporte nem `debug dump` de payload.

### 13.7 Comportamento e acessibilidade

- Um disclosure `button` por atividade, com `aria-expanded` e `aria-controls`; foco visível, Enter/Space, leitura linear por leitor de tela.
- Atualizações dinâmicas pontuais com `role=status` e sem anúncios repetitivos de cada etapa. Falhas materiais por `role=alert`; feedback não só por cor.
- Animação discreta apenas quando execução real pendente; `prefers-reduced-motion` respeitado. Nunca spinner eterno após término da requisição.
- Scroll automático somente quando o usuário está próximo do fim; expansão preserva posição de leitura. Timeline longa precisa de wrapping, truncamento honesto e navegação por teclado.
- Light/dark via tokens Portal/plugin-ui; no dock linhas quebram sem overflow, ícones/chevrons alvos de toque adequados.
- Persistência **por turno na sessão atual** somente na medida em que os dados reais estejam disponíveis; não inventar histórico durável, multi-tab ou replays de ferramentas.
- **Modo demo:** fixtures explicitamente rotuladas `Simulação` e isoladas de produção real; etapas fictícias não devem ser confundidas com execução de DAVI/MCP.

### 13.8 Matriz de gates e fases de entrega

| Capacidade | Evidência atual | Gate |
| --- | --- | --- |
| Loading simples durante `POST /interaction/turns` | Frontend observa pending real | Pode reutilizar UI atual |
| Expandir resumo final de provenance/limitações | `presentation.v1` final JSON, se disponível | Inventário de campos/consumers; decisão bounded UI |
| Nome real de especialista/capability | Possível somente se projeção permitir | Owner/disclosure + contrato comprovado |
| Etapas progressivas e ferramentas ao vivo | **TO_INVENTORY**; POST atual não prova SSE | Novo contrato/projeção + autorização de fase |
| Durations por etapa | **TO_INVENTORY** | Instrumentação real e schema |
| Inspector lateral rico | **TARGET** | Evidências suficientes + design e contrato |
| Transcript de pensamento / `chain-of-thought` | Proibido | **FORBIDDEN** |
| Console MCP bruto / tool-call arguments / secrets | Proibido | **FORBIDDEN** |

**Ordem de realização:** inventário de componentes/contratos/eventos existentes → review owner/privacy/security → menor UI fiel com informação final real → decisão independente para atividade progressiva → testes de regressão, generalização, a11y, page/dock → verificação visual real → ledger. Nenhum contrato ou mecanismo de transporte pode ser escolhido só para imitar a animação dos prints.

### 13.9 Critérios adicionais de aceite visual

- [ ] Linha curta integrada ao turno; não ocupar card pesado na conversa.
- [ ] Expansão inline possível, fechada por padrão, com teclado e leitor de tela.
- [ ] Pending sem eventos não inventa consulta, especialista ou ferramentas.
- [ ] Nome/protocolo/fonte somente quando projeção aprovada traz evidência real.
- [ ] Erro, precondição e AuthZ deny materiais continuam visíveis mesmo recolhidos.
- [ ] Tool completion, dados utilizáveis, GROUNDED e Domain outcome têm rótulos distintos.
- [ ] Nenhum texto de chain-of-thought, prompt interno, token, argumentos brutos ou metadados de discovery expostos.
- [ ] Contexto visual consistente em página/dock, light/dark, 200% zoom, mobile e reduced-motion.
- [ ] Em modo demo, toda etapa é claramente marcada como simulação e não causa side effects.
- [ ] Testes e revisão no SHA/config reais; `TEST_NOT_RUN` para navegador ausente.

**Status documental desta seção:** `DESIGN_DETAIL_PROPOSED`, preservando a direção já aprovada no documento 70. A posição exata linha-acima-vs-dentro do corpo da resposta e a habilitação do inspector permanecem **decisões de coordenação pendentes**. Nenhuma implementação, contrato, commit de código, deploy ou avanço de fase é produzido por esta especificação.

## 14. Registro de implementação — DELIA-UX-ACTIVITY-PLUGIN-UI-FULL-IMPLEMENTATION-01

Implementação efetiva do componente de atividade. Evidência factual; não altera gates nem avança fase.

### 14.1 Peças implementadas

| Peça | Local | Estado |
| --- | --- | --- |
| `ActivityViewer` (summary expansível + steps + sources + outcome) | `plugins/plugin-ui/src/components/activity/ActivityViewer.tsx` | PROVEN |
| Estilos do componente | `plugins/plugin-ui/src/styles/activity-viewer.css` | PROVEN |
| Adapter DÉLIA→view | `plugins/delia/src/activity/activityView.ts` | PROVEN |
| Integração no turno | `plugins/delia/src/ui/DeliaAssistantMessage.tsx` (acima do conteúdo) | PROVEN |
| Resumo pending real | `plugins/delia/src/App.tsx` (substitui badge genérico; mantém `role=status` e texto honesto) | PROVEN |
| Fixture de atividade demo | `plugins/delia/src/demo/demoMode.ts` cenário `?delia-demo=activity` | PROVEN |
| ActivityInspector (painel lateral) | — | TARGET — CONTRACT_REQUIRED (não implementado) |
| Etapas progressivas ao vivo (SSE/streaming) | — | TO_INVENTORY (POST atual não prova) |

### 14.2 API pública (provider-neutral)

`ActivityViewerProps`: `title`, `state` (`pending|running|completed|partial|blocked|denied|failed|cancelled|no_data`), `steps?: ActivityStepView[]`, `sources?: ActivitySourceView[]`, `outcome?` (com `persistent` para avisos que permanecem recolhidos), `durationLabel?`, `summaryDetail?`, `expandable?`, `defaultExpanded?`, `children`, `className`. Sem `Record<string,unknown>`; campos MCP arbitrários nunca viram props.

### 14.3 Campos reais consumidos pelo adapter

Somente `presentation.messageKind`, `groundingStatus`, `provenance` (`specialist_id`, `remote_capability`, `protocol`, `source.{source_id,source_system,observed_at}`, `is_complete`, `observed_at`) e `activityView` (override explícito de fixture demo). Etapas mínimas honestas: `Solicitação recebida` + `Resposta elaborada/registrada`; `Capacidade acionada`/`Fonte consultada` somente com provenance real. Nenhum timestamp/duração inventado.

### 14.4 Reuso

| Responsabilidade | Decisão |
| --- | --- |
| Disclosure inline | NEW (nenhum Disclosure/Accordion no kit) — implementado dentro do ActivityViewer |
| Steps/timeline | NEW (o `Timeline` de data é log de eventos; semântica divergente) |
| Ícones/estado | REUSE lucide-react + tokens `--delpi-ui-*`/`--surface`/`--text` |
| Badge de loading | REUSE via substituição: pending agora é `ActivityViewer state=running` |
| StatusBadge | não usado por etapa (ícone+título bastam); outcome usa o mesmo vocabulário de tons |

### 14.5 Modo demo vs real

Real: adapter deriva do contrato; pending não revela provider/ferramenta. Demo (`?delia-demo=activity`): fixture com múltiplos especialistas fictícios e outcome persistente `SIMULAÇÃO — nenhuma ferramenta real executada.` Nunca ativada por erro 402/503; gate `import.meta.env.DEV || VITE_DELIA_DEMO=1`.

### 14.6 Evidência

- plugin-ui: `ActivityViewer.test.tsx` 21/21 PASS (estados, disclosure, teclado, sources, outcome persistente, markup hostil inerte).
- DÉLIA: 141/141 PASS (adapter 9 testes + integração demo + regressão S1–S3/composer).
- Build plugin-ui PASS + `verify:host-exports` OK; build delia PASS + `verify:federation` OK.
- Typecheck: residual externo conhecido (`TaskDetailCard.tsx`, `visualComponents.ts`) — fora do escopo.
- `BROWSER_VISUAL_EVIDENCE = TEST_NOT_RUN` (navegador real pendente).

### 14.7 Gaps contratuais preservados

Etapas progressivas reais, durações medidas, inspector lateral e sequência multi-etapa legítima continuam TO_INVENTORY/TARGET — exigem projeção/contrato novos do backend. Este registro não reclassifica TARGET como implementado.

## 15. Inventário de atividade progressiva — DELIA-UX-PROGRESSIVE-ACTIVITY-RUNTIME-01

**Registro:** inventário + REUSE GATE + proposta de contrato. **Não** há implementação — o transporte/contrato exigem autorização arquitetural explícita (ver §13.8/D4 e doc 69 §"Modelo de UX progressivo": "requer ADR/contrato e não é autorizado por este plano"; doc 50: "SSE, WebSocket e callbacks detalhados ficam para passos posteriores de contrato").

### 15.1 REUSE GATE

```
RESPONSIBILITY      = publish bounded real-time operational activity
                      for an in-flight DÉLIA interaction
EXISTING_EQUIVALENT = NO (para canal DÉLIA-consumível)
REUSE_DECISION      = PENDING (aguarda decisão de transporte/contrato)
```

| Candidato | Evidência | Veredito |
| --- | --- | --- |
| delia-api SSE/WS/progress | Flask 3.1 + gunicorn sync (`--workers 1 --threads 4`); rotas = `POST /interaction/turns` + health; zero eventos/ports de progresso; sem deps WS/SSE | `NO` |
| Portal `socket.io` (`portal/src/hooks/useSocket.ts`) | Canal Portal-owned (notifications/presence/app_usage/admin.changed) — não é event bus de MFE | `NOT_REUSABLE` (boundary) |
| requests-api `RequestsRealtimeHub` + `realtime_routes.py` | FastAPI WS com salas `user:{id}`/`request:{uuid}` — padrão provado atrás do gateway (upgrade + `proxy_buffering off`), porém pertence ao bounded context de requests | `NOT_REUSABLE` como consumo; `PROVEN_PATTERN` como referência |
| Automation Hub progress events | sem consumer/contrato DÉLIA-consumível inventariado | `TO_INVENTORY` |
| ActivityViewer progress props | `state=running` + `steps[]` existem; suporta updates incrementais por props, sem mudança | `YES` (frontend) |
| Observability/event bus compartilhado | não encontrado canal genérico | `NO` |

### 15.2 Milestones reais observáveis (delia-api)

`handle_interactive_turn.execute()` já percorre estados honestos e discretos: validação de acesso/input (`REQUEST_RECEIVED`), `capability_orchestration.attempt()` (`CONTEXTUALIZING`/`CAPABILITY_SELECTED`/`SOURCE_QUERY_*` conforme provenance), ramos terminais governados (`WAITING_CONFIRMATION`, `AUTHZ_DENIED`/`BLOCKED` via `GovernedCapabilityStatus`), modelo (`OUTCOME_PREPARING`), resultado final (`COMPLETED`/`FAILED`). `session_id`/`turn_id`/`correlation_id` já existem — nenhum ID novo de autoridade necessário.

### 15.3 Comparação de transporte

| Opção | Infra | Auth | Correlação | Riscos | Veredito |
| --- | --- | --- | --- | --- | --- |
| A — **Stream no próprio `POST /interaction/turns`** (opt-in `Accept: application/x-ndjson`; eventos `ActivityEvent` + evento final `turn_result` com payload v1 idêntico) | zero endpoint novo; mesmo thread; `X-Accel-Buffering: no` no response evita mudança de gateway | bearer middleware existente | mesma request — `turn_id`/`session_id` já no escopo | exige response streaming no Flask (generator); sem reconnect (request morre → fallback já existente) | **RECOMENDADO** |
| B — `GET /turns/{id}/activity` SSE/EventSource | endpoint novo | EventSource sem header `Authorization` → token em query (vazamento em logs) ou fetch-reader | turn_id é gerado no backend — frontend não o conhece cedo | mais superfície, correlação mais fraca | rejeitado |
| C — Polling `?after_seq=` | zero infra | bearer normal | ok | buffer in-memory depende de `--workers 1`, que o Dockerfile declara temporário até store durável | rejeitado (frágil) |
| D — WebSocket | Flask sem WS nativo → flask-sock+gevent (novas deps, worker class) | token handshake | ok | maior custo para canal unidirecional | rejeitado |

### 15.4 Contrato candidato (provider-neutral, versionado)

```
ActivityEvent.v1 {version, event_id, sequence, timestamp,
                  session_id, turn_id, correlation_id?,
                  phase, state, label_code,
                  capability_ref?, source_ref?, owner_ref?, outcome_ref?}
phase ∈ REQUEST_RECEIVED|CONTEXTUALIZING|CAPABILITY_SELECTED|
          SOURCE_QUERY_STARTED|SOURCE_QUERY_COMPLETED|
          OUTCOME_PREPARING|WAITING_CONFIRMATION|COMPLETED|
          PARTIAL|BLOCKED|FAILED|CANCELLED
state ∈ RUNNING|<phase terminal>
```

Backend emite `phase`/`state` semânticos; labels PT-BR são mapeados no adapter do MFE (apresentação é render-only). `capability_ref`/`source_ref` só vêm de provenance/projeção disclosure-safe — nunca args de tool, prompt, provider internals, host/path. Emissor = `ActivityEventPort` (application → port → infrastructure adapter que escreve no stream); o resultado final do POST permanece autoritativo e sobrescreve projeções progressivas.

### 15.5 Status

`DECIDED` — o Product Master aprovou explicitamente, para a implementação bounded `DELIA-C3-PROGRESSIVE-ACTIVITY-NDJSON-END-TO-END-IMPLEMENTATION-01`: transporte **Opção A** (NDJSON opt-in no `POST /interaction/turns` existente), contrato `ActivityEvent.v1` (owner `delia-api`, consumer principal `plugins/delia`, componente `@delpi/plugin-ui/ActivityViewer`), preservação integral do JSON legado, e reuso do `ActivityViewer` sem novo componente. A decisão é registrada aqui no momento da aprovação — nenhuma aprovação histórica foi inventada. Fase preservada: `C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`; `NEXT = RETURN_TO_ARCHITECTURE_COORDINATION`.

## 16. Contract freeze — ActivityEvent.v1 (decisão aprovada)

**OWNER:** `delia-api` (Application emite observações semânticas; `interfaces/http` transporta NDJSON). **CONSUMERS:** `plugins/delia` (adapter + `@delpi/plugin-ui/ActivityViewer` render-only).

### 16.1 Registros no stream

O corpo NDJSON (`Content-Type: application/x-ndjson`) é uma sequência de objetos JSON por linha:

| `type` | Papel |
| --- | --- |
| `activity_event` | Observação semântica de uma fronteira de execução realmente alcançada. Zero ou mais por turno. |
| `turn_result` | Registro terminal de sucesso. `result` = payload de `serialize_result` — **idêntico** ao corpo JSON legado (`presentation.v1`, provenance, confirmation_request, digests preservados). Exatamente um, sempre último. |
| `turn_error` | Registro terminal de falha após o stream iniciar. `code`/`message` são os mesmos do corpo de erro legado — HTTP status não é mais alterável após o primeiro chunk; este registro é o terminal seguro. Exatamente um, sempre último. |

Todo registro carrega `version: "1"`. Todo stream termina com exatamente um `turn_result` **ou** um `turn_error` — nunca ambos, nunca ausente.

### 16.2 `ActivityEvent.v1` — campos

| Campo | Origem | Regra de divulgação |
| --- | --- | --- |
| `type` | constante `"activity_event"` | sempre |
| `version` | `"1"` | sempre |
| `event_id` | `uuid4` por evento | chave de deduplicação; não é autoridade |
| `sequence` | inteiro ≥1, estritamente crescente por request | ordenação; ausência de lacuna não é garantida nem exigida — apenas monotonicidade |
| `timestamp` | UTC ISO-8601 no momento da observação | sempre |
| `session_id` | `InteractionSession.session_id` — criado em `execute()` antes do primeiro evento | sempre |
| `turn_id` | `InteractionTurn` do usuário — criado antes do primeiro evento | sempre |
| `correlation_id` | correlação da orquestração de capabilities | **opcional** — ausente até a orquestração iniciar; nunca inventado |
| `phase` | enum fechado (§16.3) | sempre |
| `state` | enum fechado (§16.3) | sempre |
| `label_code` | código semântico fechado; backend emite código, frontend mapeia pt-BR | sempre; nunca texto livre de provider |
| `capability_ref` | `{remote_name, protocol?, operation_class?}` da capability realmente selecionada/invocada | somente após seleção/invocação observada; `protocol` somente quando provenance do outcome o comprova; nunca `binding`, argumentos, tokens ou internals de provider |
| `source_ref` | `{source_id, source_system}` do `SourceRef` declarado do grupo | mesma projeção já divulgável de `provenance.to_projection()`; nunca URL/endpoint |
| `owner_ref` | `{display_name, owner_ref}` do `CapabilityGroup` | identidade aprovada do especialista; somente quando efetivamente selecionado |
| `outcome_ref` | `{status, record_count?}` | `status ∈ returned_data\|completed_no_data\|partial\|error`; `record_count` só de contagem real extraída — nunca inferido de HTTP 200 |

**IDs:** `session_id`/`turn_id` existem antes do primeiro evento; `correlation_id` é opcional até existir na orquestração. Nenhum ID novo de autoridade é criado.

### 16.3 Vocabulário fechado

```
phase ∈ REQUEST_RECEIVED | CONTEXTUALIZING | CAPABILITY_SELECTED |
          SOURCE_QUERY_STARTED | SOURCE_QUERY_COMPLETED |
          OUTCOME_PREPARING | WAITING_CONFIRMATION | COMPLETED |
          PARTIAL | BLOCKED | FAILED | CANCELLED
state ∈ running | completed | partial | failed | blocked |
        denied | cancelled | waiting | no_data
```

Transições são fatos observados — não há obrigação de percorrer todas as fases. `SOURCE_QUERY_STARTED` só emite quando `provider.invoke` vai ser chamado; `SOURCE_QUERY_COMPLETED` carrega `outcome_ref` honesto (`error` em `CapabilityProviderError`). Sucesso técnico de transporte ≠ sucesso de negócio.

### 16.4 Semântica de erro e terminação

- Erros de validação/AuthN/AuthZ **antes do primeiro evento** respondem o JSON de erro legado com o HTTP status atual — headers nunca são comprometidos para esses casos (preflight: o primeiro item do canal é lido antes de retornar o Response de stream).
- Falha após o primeiro evento → evento `FAILED` (quando observável na Application) + registro terminal `turn_error`; nunca `turn_result` bem-sucedido, nunca `COMPLETED`.
- Desconexão do cliente aborta o consumo do gerador; a execução no worker termina pelo deadline do turno — cancelamento não duplica execução (o frontend nunca reenvia a mesma request).
- `CANCELLED`/`PARTIAL` só são emitidos com observação real; V1 não inventa cancelamento.

### 16.5 Transporte (Opção A implementada)

- Mesma rota `POST /interaction/turns`; opt-in somente por **media-range explícito** `Accept: application/x-ndjson` com `q > 0`. Wildcards (`*/*`), ausência do header, `application/json` ou `application/x-ndjson;q=0` mantêm JSON legado — wildcard nunca autoriza stream.
- Execução do use case roda em **um worker thread por request** drenando um `queue.Queue` — necessário e seguro: `execute()` é síncrono e não pode intercalar yields na mesma thread (worker gunicorn sync, `--threads 4`); sem thread só existiria streaming cosmético. Thread daemon, request-scoped, sem fila externa, sem novo endpoint.
- Headers do stream: `X-Accel-Buffering: no`, `Cache-Control: no-cache, no-store`. Sem mudança de gateway.
- O primeiro evento (`REQUEST_RECEIVED`) chega ao cliente antes da conclusão — verificado por teste de timing com latência determinística.

### 16.6 Limites e compatibilidade

- `presentation.v1`: inalterado — viaja dentro de `turn_result.result`.
- AuthZ/AuthN/PREPARE/ACT/confirmação/digests: inalterados; eventos nunca autorizam nada.
- Frontend: `Accept` enviado; se o servidor responder JSON legado, o cliente faz parse do caminho existente (fallback automático, sem segunda request).
- Limites client-side: tamanho de linha, número de eventos, sequência/dedup, terminal obrigatório.
- Proibições herdadas (§7/§13): sem chain-of-thought, prompts, tool args, raw payload MCP, `agent_directives`, candidate tokens, secrets, headers, SQL, hosts privados.


### 16.7 Hardening localizado do transporte — `DELIA-C3-NDJSON-TRANSPORT-HARDENING-R1`

**Implementação:** `d2390a401080c16e4f6555db5c6fa9cc18c96302` (`main`, 2026-10-15). **Escopo:** `delia-api/app/interfaces/http/interaction_routes.py` + `delia-api/tests/test_activity_streaming.py`. Não altera `ActivityEvent.v1`, `presentation.v1`, AuthZ, Domain authority, `ActivityViewer`, nem a semântica de `turn_result` / `turn_error`.

- **Opt-in explícito:** iteração pelos media-ranges declarados em `request.accept_mimetypes`, sem usar resolução por wildcard. Um cabeçalho genérico `*/*` não recebe NDJSON; media-range explícito com qualidade positiva recebe NDJSON.
- **Fila limitada:** `queue.Queue(maxsize=66)` por request, com no máximo **60** observações intermediárias, **4** observações terminais e **2** slots para resultado autoritativo/erro e sentinela. A publicação usa `put_nowait` e nunca bloqueia a thread por ausência de consumo da resposta.
- **Sob saturação:** observações intermediárias além do limite são omitidas (sem inventar eventos), preservando a capacidade para eventos terminais reais e `turn_result`/`turn_error` obrigatório. O histórico progressivo é uma projeção bounded, não um log completo nem uma fonte de autoridade.
- **Verificação:** testes adicionados para wildcard, `q=0`, opt-in positivo e 500 emissões com resultado/erro; **execução integral dos testes ainda = `TEST_NOT_RUN` neste ambiente** (sem checkout executável/dependências). Simulação isolada da invariância da fila = `PASS`, insuficiente para aceite de integração. `INDEPENDENT_REVIEW=PENDING`; live no SHA corrigido = `TEST_NOT_RUN`.
- **Gates preservados:** `C3_EXECUTED=NO`, `C4/C5_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`. Nenhum deploy incluído neste hardening.
