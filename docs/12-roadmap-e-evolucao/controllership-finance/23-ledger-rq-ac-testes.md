# 23 — Ledger de Requisitos, Critérios de Aceite e Testes

## Objetivo

Fornecer rastreabilidade executável entre requisito funcional, página, critério de aceite, teste e dependência de implementação.

Este ledger complementa:
- [15-requisitos-criterios-de-aceite-e-testes.md](./15-requisitos-criterios-de-aceite-e-testes.md);
- [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md);
- [22-handoff-implementacao-p1-p6.md](./22-handoff-implementacao-p1-p6.md).

`READY` neste documento significa requisito funcional fechado; não prova runtime nem libera gate de página sozinho.

## P1 — Cockpit da Competência

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P1-01 | selecionar/identificar competência e contexto de empresa/unidade quando aplicável | contexto exibido e preservado em navegação/deep link sem criar permission por filial | positive + contexto alternativo + F5 | T05 | TARGET |
| RQ-P1-02 | mostrar eixos Estoque/Documentos/Pacote independentemente | mudança em um eixo não falsifica estado dos demais | positive + sibling | P2/P3/P5 | TARGET |
| RQ-P1-03 | mostrar blockers com motivo/source/ação | blocker material aparece sem percentual mascarando causa | positive + partial source | T01 | TARGET |
| RQ-P1-04 | source indisponível não pode virar zero/sucesso | estado PARTIAL/UNAVAILABLE_SOURCE explícito | negative | T01 | TARGET |
| RQ-P1-05 | P1 é leitura/composição, sem sacramentar/validar/enviar | ações proibidas não existem como authority de P1 | negative | boundaries | TARGET |
| RQ-P1-06 | histórico do fechamento navegável | eventos materiais aparecem com contexto | positive | P2–P5 audit | TARGET |
| RQ-P1-07 | Help explica eixos, freshness e conclusão | usuário acessa Help contextual da página | UI/help check | feature help | TARGET |

## P2 — Checklist e Documentos

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P2-01 | competência usa snapshot do template vigente na abertura | publicação nova não altera competência aberta | positive + sibling | P6 | TARGET |
| RQ-P2-02 | REQUIRED nunca pode N/A; CONDITIONAL pode conforme regra | tentativa inválida é rejeitada server-side | positive + negative | business rule | TARGET |
| RQ-P2-03 | ATTACHED != VALIDATED quando validation required | upload não produz ACCEPTED automaticamente | positive + negative | validator | TARGET |
| RQ-P2-04 | rejeição preserva versão e exige motivo estruturado | evidência rejeitada permanece histórica | positive + audit | E06 seed | TARGET |
| RQ-P2-05 | replacement cria nova validação | nova evidência não herda aceite antigo | positive + negative | — | TARGET |
| RQ-P2-06 | PER_ATTACHMENT e WHOLE_SET obedecem escopo de validação | rejeição parcial/conjunto seguem regra configurada | positive + sibling | config | TARGET |
| RQ-P2-07 | item excepcional é somente da competência | criação não altera template mestre | positive + sibling | T05 | TARGET |
| RQ-P2-08 | CANCELLED não é delete nem NOT_APPLICABLE | item cancelado sai da completude ativa e histórico permanece | positive + negative | — | TARGET |
| RQ-P2-09 | correção estrutural pós-execução cria nova revisão | request/review/audit separados; histórico preservado | positive + stale negative | MANAGE | TARGET |
| RQ-P2-10 | reversão de rejeição respeita nova versão | reversão é bloqueada quando replacement já existe | positive + negative | notification | TARGET |
| RQ-P2-11 | notificações seguem targets efetivos e histórico | reversão não apaga notificação anterior | positive | T02 | TARGET |
| RQ-P2-12 | Help explica requirement, validação, N/A, replacement e correção | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## P3 — Estoque, Cutoff e Conciliação

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P3-01 | cutoff requer confirmação humana autorizada | estabilidade aparente não confirma cutoff automaticamente | positive + negative | T05 | TARGET |
| RQ-P3-02 | pós-cutoff revalida P7, Entradas/Saídas, H02 e conciliação | readiness usa resultado revalidado | positive | T01 | TARGET |
| RQ-P3-03 | paridade monetária é exatamente R$ 0,00 | qualquer valor não zero bloqueia READY_TO_CLOSE | AC-P3-PARITY-01..07 | T01 | TARGET |
| RQ-P3-04 | zero pré-cutoff não é final | permanece PRELIMINARY/WAITING conforme state | negative | — | TARGET |
| RQ-P3-05 | source obrigatório indisponível não vira zero | readiness bloqueada e indisponibilidade explícita | negative | T01 | TARGET |
| RQ-P3-06 | input alterado após revalidação invalida prontidão aplicável | estado volta a requerer revalidação | positive + sibling | source version/freshness | TARGET |
| RQ-P3-07 | V1 não grava sacramentação no ERP | nenhuma action de escrita ERP é criada | architecture negative | E03/T03 | TARGET |
| RQ-P3-08 | STOCK_CLOSED usa estado canônico do owner se existir | sem fallback manual silencioso | integration/contract | T03 | TARGET / STOP_CONDITION |
| RQ-P3-09 | freshness/proveniência acompanham resultado | source/time/competência/unidade/finality/rule version disponíveis | contract/UI | T01 | TARGET |
| RQ-P3-10 | Help explica cutoff, revalidação, paridade e estado canônico | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## P4 — Classificações e Pendências

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P4-01 | regra determinística/IA pode sugerir classificação | sugestão não altera ERP nem conclui decisão | positive + AI negative | T01 | TARGET |
| RQ-P4-02 | humano autorizado confirma classificação | decisão confirmada registra ator/evidência | positive + permission negative | T05 | TARGET |
| RQ-P4-03 | pendência usa state machine fechada | estado livre/inválido rejeitado | positive + negative | — | TARGET |
| RQ-P4-04 | claim/reassign preserva ownership history | responsável anterior/atual e timestamps auditados | positive + sibling | T05 | TARGET |
| RQ-P4-05 | DISMISSED exige justificativa e não substitui N/A | blocker real não pode ser ocultado por dismiss indevido | positive + negative | business rule | TARGET |
| RQ-P4-06 | sem SLA/overdue no target | UI mostra pending_since/idade factual sem atraso formal | UI negative | — | TARGET |
| RQ-P4-07 | boundary com Portal Financeiro P0 é preservado | P4 não reutiliza despesas CC como authority automática | architecture review | 21-boundaries | TARGET |
| RQ-P4-08 | Help explica sugestão, owner, states e dismiss | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## P5 — Pacote, Finalização e Envio

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P5-01 | PACKAGE_INCOMPLETE só avança quando requisitos aplicáveis permitirem | blockers impedem READY_TO_FINALIZE | positive + negative | P2/P3 | TARGET |
| RQ-P5-02 | Finalizar cria versão/snapshot e não envia | PACKAGE_FINALIZED sem PACKAGE_SENT | positive | — | TARGET |
| RQ-P5-03 | reabrir antes do envio preserva versão anterior | V1 histórica + working copy + V2 | positive + audit | — | TARGET |
| RQ-P5-04 | pacotes são por destinatário dentro da mesma competência | enviar um destinatário não avança sibling | positive + sibling | recipients config | TARGET |
| RQ-P5-05 | envio real usa capability corporativa comprovada | nenhum canal é assumido antes do inventário | contract/integration | E04/T04 | PENDING_IMPLEMENTATION |
| RQ-P5-06 | PACKAGE_SENT é imutável | tentativa de editar pacote enviado é rejeitada | negative | — | TARGET |
| RQ-P5-07 | correção pós-envio cria complemento/nova versão ligada à anterior | histórico de entrega preservado | positive + audit | — | TARGET |
| RQ-P5-08 | conclusão exige todos pacotes aplicáveis enviados e nenhum esclarecimento aberto | sem botão de force completion | positive + negative | send capability | TARGET |
| RQ-P5-09 | ack/read do destinatário não bloqueia V1 | ausência de ack não impede conclusão se demais regras satisfeitas | sibling/negative | — | TARGET |
| RQ-P5-10 | Help explica finalizar, enviar, versões e esclarecimentos | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## P6 — Administração e Configuração

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P6-01 | template segue DRAFT→REVIEW→PUBLISH→EFFECTIVE_FROM | salvar draft não publica | positive + negative | MANAGE | TARGET |
| RQ-P6-02 | publicação não altera snapshot de competência aberta | competência continua na versão original | positive + sibling | P2 snapshot | TARGET |
| RQ-P6-03 | inativação é prospectiva e sem delete físico | histórico continua referenciável | positive + negative | audit | TARGET |
| RQ-P6-04 | ACCESS usa opções; MANAGE administra catálogos | ACCESS não altera mestre | permission negative | T05 | TARGET |
| RQ-P6-05 | bancos/contas são configuráveis, não hardcoded | seed pode mudar sem diff de regra | config test | E01 | TARGET |
| RQ-P6-06 | motivos de rejeição = núcleo + extensões | inativação preserva códigos históricos | positive + sibling | E06 | TARGET |
| RQ-P6-07 | attachment roles são catalogados com genérico quando permitido | role obrigatório/configurado respeitado | positive + negative | E05 | TARGET |
| RQ-P6-08 | notification targets usam opções governadas | targets inválidos não são free-form | positive + negative | T02 | TARGET |
| RQ-P6-09 | um MANAGE pode publicar com auditoria no target atual | segundo MANAGE não é requisito implícito | positive | T05 | TARGET |
| RQ-P6-10 | Help explica draft/publish/effective_from/snapshot/inativação | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## Superfícies da topbar

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
Fonte detalhada do Início: [32-inicio-home.md](./32-inicio-home.md).

| RQ-NAV-01 | topbar contém exatamente Início, Visão geral, Sala de interação, Minhas tarefas, Administração e Ajuda | ordem/conjunto canônico sem item de P1–P5 na topbar | navigation + mobile + keyboard | 24 | TARGET |
| RQ-HOME-01 | Início usa Home family comum dos Portais | TopBar + Hero + Eventos + launcher/recentes; zero redesign local | visual/component + mobile/dark | plugin-ui + 32 | TARGET |
| RQ-HOME-02 | Hero é operacional, não analítico | Competência ativa + Minhas tarefas + Blockers; indicadores financeiros ficam na Visão geral | positive + source partial | H02/H03/H04 | TARGET |
| RQ-HOME-03 | Eventos degradam independentemente | tasks/alerts podem falhar sem derrubar catálogo; sem SLA inventado | positive + partial + negative | H02/H04 | TARGET |
| RQ-HOME-04 | catálogo mostra somente runtime implementado + autorizado | P1–P5 entram page-by-page; Administração só MANAGE; profile fora do launcher | positive + route/permission negative | router/Core | TARGET |
| RQ-HOME-05 | busca local usa catálogo e deep link ?q= | F5 preserva query; rota sem acesso não aparece | search + F5 + permission negative | router/catalog | TARGET |
| RQ-HOME-06 | recentes são efêmeros e seguros | máx. 5; stale/unauthorized filtrado; sem dado financeiro/PII | storage + corruption negative | local UI state | TARGET |
| RQ-HOME-07 | favoritos sincronizam estrela e TopBar | falha save faz rollback; persistência física somente após H01 | positive + backend failure + stale | H01 | TO_INVENTORY |
| RQ-HOME-08 | Home preserva light/dark/mobile/a11y | mesmos componentes/tokens; teclado/foco; estado não só por cor | visual/a11y | plugin-ui | TARGET |
| RQ-HOME-09 | Help explica Home | Home vs Overview, eventos, busca, recentes e favoritos documentados quando runtime existir | help sync | feature-help-sync | TARGET |
| RQ-TASK-01 | Minhas tarefas usa workspace comum | `TaskWorkspacePage` + task primitives; zero clone/CSS local | visual/component + mobile/dark | plugin-ui + 27 | TARGET |
| RQ-TASK-02 | TaskProjection não é task entity | sem create/edit/complete/cancel/defer/reassign genérico; owner state não é copiado | architecture + negative | D-TASK-01/02 | TARGET |
| RQ-TASK-03 | worklist é self-only | `/me/tasks`; sem user selector/team scope; MANAGE não implica team | permission/privacy negative | Core + D-TASK-03 | TARGET |
| RQ-TASK-04 | producer exige responsabilidade individual | P2/P4 governados; P5 conditional; blocker/mention sozinho não gera task | positive + sibling + negative | TSK01 | TARGET |
| RQ-TASK-05 | ação V1 abre owner | deep link seguro; owner reautoriza; nenhuma ação de negócio local | navigation + stale item | TSK03 | TARGET |
| RQ-TASK-06 | sem SLA global | sem Atrasadas/Hoje/Depois; due/overdue só owner-provided; pendingSince factual | negative due/SLA | D-TASK-04 | TARGET |
| RQ-TASK-07 | partial coverage é honesta | source failure preserva siblings; count não parece total; empty só COMPLETE | partial + source failure | TSK04 | TARGET |
| RQ-TASK-08 | filtros são shareable | source/competence/q em URL; F5; sem user override/open redirect | URL roundtrip + negative | TSK03 | TARGET |
| RQ-TASK-09 | Home reusa a mesma projeção | summary/count seguem coverage; nenhuma regra duplicada | contract sibling | Home H02 | TARGET |
| RQ-TASK-10 | Sala não cria task na V1 | `onCreateTask` oculto; message/mention não geram TaskProjection | interaction negative | D-TASK-07 | TARGET |
| RQ-TASK-11 | light/dark/mobile/a11y seguem kit | mesmos componentes/tokens; teclado/foco; tabela responsiva | visual/a11y | plugin-ui/TSK05 | TARGET |
| RQ-TASK-12 | Help sincronizada | explica projection/owner/no-SLA/no-free-task e só producers implementados | help sync | feature-help-sync | TARGET |

| RQ-ROOM-01 | Sala usa full-page comum | `InteractionRoomPage` como canvas; zero clone local | visual/component + mobile/dark | plugin-ui + 26 | TARGET |
| RQ-ROOM-02 | Sala é sempre contextual | sem wall/global room/criação livre; somente context registry | positive + invalid context negative | context registry | TARGET |
| RQ-ROOM-03 | uma sala por contexto | resolve idempotente; concorrência não duplica; título derivado | concurrency + contract | persistence future | TARGET |
| RQ-ROOM-04 | AuthZ depende do contexto | ACCESS + context access; member/mention não concede acesso | permission/resource negative | Core + owners | TARGET |
| RQ-ROOM-05 | conversa não muda business state | comment/reaction/pin não validam, aprovam, fecham ou enviam | negative business-state | P1–P5 | TARGET |
| RQ-ROOM-06 | edit/delete preservam histórico | autor edita própria text; delete é soft; system imutável | positive + negative author | message policy | TARGET |
| RQ-ROOM-07 | attachment de chat não é evidência P2 | evidence exige ação owner explícita | boundary negative | P2 | TARGET |
| RQ-ROOM-08 | mentions respeitam acesso | suggestion server-side; target permitido; mention não concede scope | privacy/resource negative | Core directory + context | TARGET |
| RQ-ROOM-09 | realtime é degradável | transport failure vira banner/partial, não perda total de chat | degraded/reconnect | R03 | TARGET |
| RQ-ROOM-10 | notifications usam capability canônica | mention notifica; sem SMTP/preferences local | integration negative | R04/T02 | TARGET |
| RQ-ROOM-11 | criar tarefa não existe na V1 | `onCreateTask` oculto; message/mention não geram TaskProjection | interaction negative | Item 5 / D-TASK-07 | TARGET |
| RQ-ROOM-12 | Help sincronizada | contexto, mensagem vs ação, attachments, mentions, edit/delete explicados no runtime | help sync | feature-help-sync | TARGET |

| RQ-OVW-01 | Visão geral usa Overview family comum | Hero compacto + período/filtros + KPI grid + charts | visual/component + mobile/dark | plugin-ui + 25 | TARGET |
| RQ-OVW-02 | indicador é governado por owner/source/fórmula | nenhum KPI sem metadata mínima; indisponível != zero | positive + source failure | D-OVW-01=C + O04 | TARGET |
| RQ-OVW-03 | filtros são shareable por URL | F5 reconstrói recorte; unidade é dimensão de dado | URL roundtrip + F5 | D-OVW-02=A + D-OVW-03=A | TARGET |
| RQ-OVW-04 | blocos degradam isoladamente | source failure de um indicador não derruba siblings | partial + sibling | contracts físicos | TARGET |
| RQ-OVW-05 | gráfico segue semântica do indicador | sem baseline/fórmula inventada; chart do kit | component + negative | indicator contract | TARGET |
| RQ-OVW-06 | drilldown é rastreável | preserva filtros e explica o número pelo mesmo owner/source | positive + deep link | route/contract | TARGET |
| RQ-OVW-07 | strategic scores vêm do owner | IDD/IGD não são recalculados no Portal; partial explícito | contract + negative | D-OVW-01=C / strategic-indicators-api | TARGET |
| RQ-OVW-08 | AuthZ usa ACCESS/MANAGE sem proliferation | ACCESS necessário; MANAGE não implica ACCESS; sem permission por indicador/unidade | permission negative | Core | TARGET |
| RQ-OVW-09 | light/dark/mobile/a11y seguem padrão comum | mesma ordem/DOM conceitual, tokens e teclado/foco | visual/a11y | plugin-ui | TARGET |
| RQ-OVW-10 | Ajuda acompanha indicadores aprovados | significado/fórmula/source/freshness/deep links sincronizados | help sync | feature-help-sync | TARGET |
| RQ-INT-01 | Sala de interação é contextual e não muda estado de negócio por mensagem | mensagem/comentário não valida, aprova, fecha estoque ou envia pacote | positive + resource negative | interaction contract inventory | CONTRACT_INVENTORY_REQUIRED |
| RQ-ADM-01 | Administração usa somente MANAGE | usuário apenas ACCESS não altera mestre; MANAGE não implica ACCESS operacional | positive + permission negative | Core effective permissions | TARGET |
| RQ-HELP-01 | Ajuda acompanha toda mudança user-facing | conteúdo/deep links sincronizados no mesmo gate da feature | help sync + link check | feature-help-sync | TARGET |
| RQ-AUTHZ-01 | permissions do Portal são somente access e manage | nenhum permission code por página, CRUD, filial, unidade ou indicador | manifest/contract review | Core | TARGET |


## Página do usuário

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-USER-01 | perfil é deep route transversal, sem item novo de topbar | `/users/{userId}` funciona em deep link/F5; topbar permanece com 6 itens | navigation + F5 + mobile | foundation/router | TARGET |
| RQ-USER-02 | identidade corporativa vem do Core | Directory + Person Profile; zero tabela/migration/storage de perfil no Portal | contract + architecture negative | Core directory/person-profile | TARGET |
| RQ-USER-03 | viewer com ACCESS pode ver outro usuário do mesmo Portal | ACCESS positivo; target sem app access = 404; sem ACCESS = 403; nenhuma permission nova | positive + sibling + permission negative | Core app membership/effective permissions | TARGET |
| RQ-USER-04 | access/capabilities são self-only e D2 mostra label + código técnico | próprio perfil mostra somente `controllership-finance.access/manage` efetivos; outro perfil não expõe RBAC | positive + privacy negative | Core effective permissions | TARGET |
| RQ-USER-05 | edição de identidade pertence ao Meu Perfil | self CTA navega ao Meu Perfil da Minha DELPI; cargo/contatos e foto são editados pela Core API; BFF/MFE de Controladoria permanecem read-only e não criam proxy/form de write | navigation + architecture negative | host profile + Core person profile | TARGET |
| RQ-USER-06 | indisponibilidade de source não vira "Não informado" | Person Profile unavailable = PARTIAL; null real só quando source AVAILABLE; Directory failure = ERROR | partial + downstream negative | Core integrations | TARGET |
| RQ-USER-07 | perfil reutiliza full-page do `@delpi/plugin-ui` | `createDashboardPortalUserProfilePage`; zero clone/CSS do kit; tema/mobile/teclado | component/build + visual/a11y | plugin-ui | TARGET |
| RQ-USER-08 | atalhos refletem runtime + acesso do viewer, não roadmap | somente rota implementada e autorizada; Administração apenas com MANAGE | positive + route-not-implemented negative | manifest/router/effective permissions | TARGET |
| RQ-USER-09 | Ajuda acompanha a página | conteúdo só fica disponível quando a feature estiver implementada; deep links válidos | help sync + link check | feature-help-sync | TARGET |

Fonte detalhada: [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

## Requisitos transversais de segurança

| RQ | Requisito | Aceite mínimo |
|---|---|---|
| RQ-SEC-01 | backend autoriza fail-closed | UI ocultar ação não concede autorização |
| RQ-SEC-02 | effective permissions vêm do Core | JWT sozinho não é authority final |
| RQ-SEC-03 | resource ownership/context access sempre aplicados quando houver recurso restrito | URL direta para recurso não autorizado é rejeitada |
| RQ-SEC-04 | MANAGE não apaga histórico | delete/overwrite material rejeitado |
| RQ-SEC-05 | IA respeita acesso/ownership e não muda estado | tool/prompt não contorna business rule |
| RQ-SEC-06 | secrets/tokens não entram em frontend state/logs/prompts comuns | scanner/review sem exposição |

## Requisitos transversais de experiência

| RQ | Requisito | Aceite mínimo |
|---|---|---|
| RQ-UX-01 | estados LOADING/EMPTY/PARTIAL/UNAVAILABLE_SOURCE/ERROR/403/404 | página não colapsa estados distintos em erro genérico |
| RQ-UX-02 | desktop/mobile e claro/escuro | conteúdo e ações materiais permanecem utilizáveis |
| RQ-UX-03 | teclado/foco | fluxo principal operável por teclado com foco visível |
| RQ-UX-04 | deep link/F5 | contexto aplicável é preservado/reconstruído sem bypass de auth |
| RQ-UX-05 | status não depende apenas de cor | labels/texto acessíveis |
| RQ-UX-06 | Help sincronizada | mudança user-facing material atualiza ajuda antes do aceite |

## Regra de evidência para implementação

Cada RQ material da página em execução deve aparecer no report do Cursor com:
- status;
- arquivo/contrato que implementa;
- teste positive;
- sibling quando aplicável;
- negative;
- evidência do HEAD final;
- residual/unresolved.

Nenhum RQ pode ser marcado PASS apenas porque outro RQ da mesma página passou.
