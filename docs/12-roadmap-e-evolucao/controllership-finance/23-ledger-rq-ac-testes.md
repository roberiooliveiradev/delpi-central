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
| RQ-P1-01 | selecionar/identificar competência e unidade no scope | contexto exibido e preservado em navegação/deep link | positive + cross-unit negative + F5 | T05 | TARGET |
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

## Requisitos transversais de segurança

| RQ | Requisito | Aceite mínimo |
|---|---|---|
| RQ-SEC-01 | backend autoriza fail-closed | UI ocultar ação não concede autorização |
| RQ-SEC-02 | effective permissions vêm do Core | JWT sozinho não é authority final |
| RQ-SEC-03 | unit/resource scope sempre aplicados | URL direta cross-unit é rejeitada |
| RQ-SEC-04 | MANAGE não apaga histórico | delete/overwrite material rejeitado |
| RQ-SEC-05 | IA respeita scope e não muda estado | tool/prompt não contorna business rule |
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
