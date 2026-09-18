# Portal Transforma+ — architecture runway

> **Status:** decisão de ordem e de contrato. **IMPLEMENTATION = NOT AUTHORIZED.**  
> **BASE desta consolidação:** `824970024`.  
> Este arquivo é a **única fonte de sequência**. Visão, domínio e UX continuam nos documentos ligados abaixo. Não descreve runtime novo.

| Assunto | Fonte | Este arquivo não repete |
|---|---|---|
| O que é o produto hoje | [OVERVIEW.md](./OVERVIEW.md), [ARCHITECTURE.md](./ARCHITECTURE.md) | ER e fórmulas |
| Ciclo de domínio | [CICLO-INTELIGENCIA-DE-PROCESSO.md](./CICLO-INTELIGENCIA-DE-PROCESSO.md) | Matriz método→resultado |
| Experiência e reuso do Comercial | [PORTAL-TRANSFORMA-PLUS.md](./PORTAL-TRANSFORMA-PLUS.md) | Inventário de componentes |
| ADRs | [adr-portal-transforma-plus.md](../../../transformometro-api/docs/architecture/adr-portal-transforma-plus.md), [adr-ciclo-inteligencia-processo.md](../../../transformometro-api/docs/architecture/adr-ciclo-inteligencia-processo.md) | Texto das decisões já tomadas |
| Entrega histórica | [ROADMAP.md](./ROADMAP.md) | Fases 0–6 já entregues |
| Playbook de portal de 2026-09-17 | [PLAYBOOK-PORTAL-TRANSFORMA.md](./PLAYBOOK-PORTAL-TRANSFORMA.md) | Inventário daquele HEAD. A tabela de fases 0–6 daquele arquivo **não** ordena o trabalho |

Rejeitado: reescrever o Transformômetro como Portal Transforma+. A estratégia é evolutiva: domínio que já existe, shell novo, capability incremental. Dados atuais de processo, diagrama, árvore, revisão, medição e melhoria não exigem redigitação.

## 1. Mapa documental

| Documento | Para que serve | Status | Canônico? | Sobreposição | Ação |
|---|---|---|---|---|---|
| Este runway | Ordem, decisões caras, DoR/DoD, pacote | TARGET de governança | Sim, para sequência | PI, fases A–I, playbook §28 | Criado. Os outros apontam para cá |
| PORTAL-TRANSFORMA-PLUS | UX, reuso, branding | TARGET | Sim, para experiência | Playbook de portal | Mantido. Sequência removida da autoridade |
| CICLO-INTELIGENCIA | Domínio alvo, métodos, budget de tool | TARGET | Sim, para domínio | Runway waves 3–10 | Mantido. PI não é calendário |
| ARCHITECTURE / OVERVIEW | Estado construído | PROVEN + ponte | Sim, para o que já roda | — | Ponte curta, sem reescrita |
| ROADMAP | Histórico de entrega | HISTORICAL para o futuro | Sim, para o passado | Waves | Não renumerar |
| PLAYBOOK-PORTAL-TRANSFORMA | Inventário 2026-09-17 | SUPPORTING / STALE na sequência | Não para ordem | Runway, portal | Cabeçalho já avisa. §28 fica histórico |
| Playbooks 18–23 | Contratos já implementados | CANONICAL do que entregaram | Sim, no assunto | — | Não fundir |
| ADRs de diagrama, árvore, ciclo, portal | Decisão | CANONICAL | Sim | — | Índice na §2 |
| ESPECIFICACAO, status jul/2026 | Origem e snapshot | HISTORICAL | Não contra o código | OVERVIEW | Não apagar |
| MCP / GPT Actions docs | Adapters vigentes | CANONICAL de superfície | Sim | Budget | Uma frase aponta para a §8 |
| `tm_app/core/catalogs.py` | Enums | CANONICAL | Sim | Glossário | Código vence o glossário se divergir |

Não há chat nomeado «00 Arquitetura» nem «03 Processos & Métodos» no playbook vigente. Trilhas que existem: **01 Backend & Domain**, **02 TÉO / Actions**, **05 Frontend & UX**, **06 Security**, **07 Integration & Acceptance**, **08 Documentation**. Coordenação de arquitetura deste runway fica em 08 até um chat 00 existir.

## 2. Índice de ADR

| ADR | Estado |
|---|---|
| [adr-diagramas-processo.md](../../../transformometro-api/docs/architecture/adr-diagramas-processo.md) | `flowchart_v1` canônico. PROVEN |
| [adr-decomposicao-processo.md](../../../transformometro-api/docs/architecture/adr-decomposicao-processo.md) | Árvore + `meta.decomposition_id` opcional. PROVEN |
| [adr-ciclo-inteligencia-processo.md](../../../transformometro-api/docs/architecture/adr-ciclo-inteligencia-processo.md) | Método ≠ entidade. TARGET, não implementado |
| [adr-portal-transforma-plus.md](../../../transformometro-api/docs/architecture/adr-portal-transforma-plus.md) | Experiência ≠ domínio. TARGET, não implementado |

## 3. O que estamos construindo

Portal Transforma+ é shell, navegação e workspace no MFE `plugins/transformometro` (`basePath=/apps/transformometro`). Transformômetro (`transformometro-api`, schema `transformometro`) continua dono de processo, instância, revisão, medição, investimento, recurso, diagrama, árvore, evidência, ata e do que o ciclo ainda marca como TARGET. TÉO é adapter. Keycloak é identidade. Core é RBAC de app. Comercial é referência de UX.

Frontend owner do shell: o MFE Transformômetro, composto com `@delpi/plugin-ui`. Não importar `plugins/commercial`. Não extrair `PluginShell` agora.

## 4. Registro de decisões

| ID | Decisão | Status | Custo | Reversível? | Bloqueia código? |
|---|---|---|---|---|---|
| D1 | Portal = experiência; TM = domínio; sem rename de API, schema, URL, MCP, Actions | DECIDED | Alto | Não sem ADR | Sim, se alguém renomear |
| D2 | Página ≠ rota ≠ tool ≠ Action | DECIDED | Alto | Não | Sim |
| D3 | Kit `plugin-ui` sim; internals do Comercial não; sem `PluginShell` compartilhado agora | DECIDED | Alto | Extração depois é possível | Sim para a Wave 1 |
| D4 | URLs atuais permanecem. Árvore aninhada `/processes/:id/diagnostic` é conceito, não path aprovado | DECIDED | Alto | Redirect é plano próprio | Sim |
| D5 | AuthZ backend-first, fail-closed. Menu, cargo, perfil e favorito não autorizam | DECIDED | Alto | Não | Sim |
| D6 | Leitura: dashboard, listagem, `search_records` / `get_record`, contexto e `analyze` antes de endpoint novo | DECIDED | Alto | — | Sim |
| D7 | `get_process_context` não vira payload ilimitado. Hoje não há `sections` | DECIDED o princípio. Forma do parâmetro TO_INVENTORY | Alto | — | Não para Wave 1–2 |
| D8 | Writes: domínio/application primeiro; MCP segue PREPARE → ACT → read-back; Actions continuam ponte legada | DECIDED | Alto | — | Sim quando houver write |
| D9 | Migration só `up`, arquivo aplicado imutável, nullable primeiro quando houver backfill | DECIDED | Alto | — | Sim a partir da Wave 3 |
| D10 | Portfólio = projeção, sem entidade, até existir participação explícita | DEFERRED | Alto | — | Bloqueia Wave 9, não a 1 |
| D11 | Tarefas, sala e favorito de página sem owner próprio | TO_INVENTORY | Alto | — | Bloqueia Wave 9 |
| D12 | Busca de caminho (palette) ≠ busca de processo (`search_records`) ≠ busca global | DECIDED a separação. Índice global TO_INVENTORY | Médio | — | Busca global adiada |
| D13 | Workspace é composição, não agregado novo | DECIDED | Alto | — | Sim |
| D14 | SIPOC não reutiliza o nome do escopo organizacional | DECIDED | Alto | — | Sim na Wave 3 |
| D15 | AS-IS/TO-BE são projeção de revisão e overlay | DECIDED | Alto | — | Sim na Wave 6 |
| D16 | KPI definition ≠ `measurement` | DECIDED a distinção. Onde persistir TO_INVENTORY | Alto | — | Bloqueia Wave 5 |
| D17 | Plano de ação sem entidade TM; Qualidade não é owner | TO_INVENTORY | Alto | — | Bloqueia Wave 7 |
| D18 | Arquitetura corporativa não reusa a árvore de um processo | DECIDED | Alto | — | Bloqueia Wave 10 |
| D19 | Completude é PRESENT/PARTIAL/MISSING/NOT_APPLICABLE | DECIDED | Baixo | — | Não antes da Wave 8 |
| D20 | Primeira fatia de código = shell + lista e workspace já existentes, só leitura de navegação | PROPOSED | Médio | Sim | Não autorizada por este arquivo |
| D21 | Labels, ordem de card, ícone | DEFERRED para revisão de UX | Baixo | Sim | Não |
| D22 | `ProcessContextService` importa `Request` e repositórios | Observado. Limpeza SAFE_TO_DEFER | Médio | — | Não bloqueia shell |

Nenhuma dessas linhas implementa feature. DECIDED aqui não torna a capability PROVEN.

## 5. Glossário

| UI (pt-BR) | Termo técnico | Não confundir com |
|---|---|---|
| Portal Transforma+ | experiência no MFE | `transformometro-api` |
| Transformômetro | bounded context | o portal |
| Processo | `process` / processo-mestre | instância, arquitetura corporativa |
| Instância | `instance` | mestre |
| Revisão | `revision` | estado de produção, até ativação verificada |
| Baseline | `CENARIO_TIPO=baseline` | o cadastro mestre |
| Cenário | revisão não baseline (`melhoria`, `automacao`, `correcao`) | TO-BE já implantado |
| AS-IS | projeção da baseline + overlays + medição | mestre |
| TO-BE | projeção do cenário ainda proposto | revisão ativa |
| Melhoria | instância operacional + fase `FASE_MELHORIA` | finding |
| Escopo organizacional | filiais/setores do mestre | SIPOC |
| Interfaces / SIPOC | view TARGET | escopo organizacional |
| Achado | finding TARGET | método Lean |
| Problema | efeito, não causa | hipótese |
| Hipótese causal | nó com estado epistemológico | causa comprovada |
| Evidência | arquivo de processo **ou** evidência de revisão | terceiro blob store |
| Definição de indicador | conceito TARGET | `measurement` |
| Medição | valor da revisão | definição |
| Plano de ação | TARGET, owner não fechado | task store |
| Resultado | ganho medido / verificado | ganho estimado |
| Arquitetura de processos | TARGET corporativo | `decomposition_tree` de um mestre |
| Meu portfólio | projeção adiada | carteira comercial |

Enums PROVEN em `tm_app/core/catalogs.py`: `STATUS_PROCESSO` ativo/descontinuado/em_implantacao; `STATUS_INSTANCIA` ativo/inativo; `CENARIO_TIPO` baseline/melhoria/automacao/correcao; `FASE_MELHORIA` planejado/piloto/implantado/encerrado; `STATUS_APROVACAO_REVISAO` rascunho/em_analise/aprovada/rejeitada. Status de achado, causa, evidência epistemológica e ação **não existem**. Não criar enum paralelo de «fase do portal» em cima desses.

## 6. Modelo

CURRENT, já persistido: Process, Instance, Revision, Measurement, Investment, Shared resource, Diagram, Decomposition (+ escopos e overlays), Impact-effort matrix, Process file, Revision evidence, Meeting minute, Audit log, Dashboard read model.

TARGET, sem classe de implementação: Finding, Cause hypothesis, Indicator definition, Action plan, Process interfaces, Corporate process architecture, Completeness projection, Portfolio projection.

| Conceito | Classe recomendada | Por quê, ainda sem implementar |
|---|---|---|
| Interfaces / SIPOC | DOCUMENT ou PROJECTION | Não é lifecycle próprio; não é `ProcessoEscopo` |
| Atributo de nó (papel, entrada, saída) | EXTENSION do schema da árvore | Identidade já é `node_id` |
| Finding / causa | NEW ENTITY se a Wave 4 provar lifecycle e referência | Não cabe no nó |
| Indicator definition | TO_INVENTORY (EXTENSION de measurement ou NEW ENTITY) | Valor já existe |
| Action plan | TO_INVENTORY | Pode ser de outro contexto |
| AS-IS / TO-BE | PROJECTION | Revisões já existem |
| Completude | PROJECTION | Sem score |
| Portfólio | PROJECTION | Sem regra própria |
| Arquitetura corporativa | NEW ENTITY na Wave 10 | Não é a árvore |

## 7. Workspace — contrato por seção

O workspace PROVEN usa seções em `processWorkspaceNav.ts` e rotas `/apps/transformometro/processes/...`. Hash de seção não é agregado.

| Seção | Estado | Owner | Leitura hoje | Escrita hoje | AuthZ de escrita | Persistência |
|---|---|---|---|---|---|---|
| Visão geral | PROVEN | TM | dashboard + processo | — | `transformometro.view` | projeção |
| Dados e escopo organizacional | PROVEN | TM | processo | CRUD processo | `processes.manage` | tabela processo + escopo |
| Interfaces / SIPOC | TARGET | TM | — | — | a decidir no pacote | não criar tabela `sipoc` por default |
| Mapeamento | PROVEN | TM | árvore | documento da árvore | manage de processo, conferir rota no pacote | `decomposition_tree_v1` |
| Diagrama | PROVEN | TM | `flowchart_v1` | documento | idem | não Mermaid como original |
| Diagnóstico | TARGET | TM | — | — | pacote da Wave 4 | não no mestre |
| Indicadores | PARTIAL | TM | medição + dashboard | medição | `measurements.manage` | valor, não definição |
| Melhorias / revisões | PROVEN | TM | instância + revisão | CRUD + ativar | `revisions.manage` | não é TO-BE automático |
| Priorização | PROVEN | TM | matriz da revisão | update da matriz | manage de revisão | `impact_effort_matrix` |
| AS-IS × TO-BE | PARTIAL | TM | compare/overlays. Contexto avisa que diagrama AS-IS/TO-BE de revisão não está no v1 | overlays | manage de revisão | sem segunda fonte |
| Plano de ação | TO_INVENTORY | — | — | — | — | — |
| Arquivos | PROVEN | TM | arquivos do processo | upload | manage de processo | `ProcessoArquivoStorage` |
| Evidência de revisão | PROVEN | TM | metadata + binário | upload da revisão | manage de revisão | `RevisaoEvidenceStorage` |
| Timeline | PROVEN | TM | `audit_logs` | nenhum write direto de UI | view | append de mutação, não event sourcing |
| Atas | PROVEN | TM | meeting minutes | manage/sign | permissões de ata | não é plano de ação |

Dependência: diagnóstico e plano não entram na nav até o pacote da wave passar no DoR. A Wave 2 só reorganiza o que esta tabela marca PROVEN.

## 8. API, contexto, MCP, Actions

Ordem de leitura, nesta ordem, antes de rota nova: CRUD/search genérico, `get_record`, `get_process_context`, `analyze` / dashboard, comando de negócio já existente (`activate`, duplicar, recalcular). Rota nova só para transação atômica, validação, simulação, agregação que não cabe, ou PREPARE/ACT.

`ProcessContextService.get_context` hoje exige `process_id` e aceita `instance_id` e `revision_id`. Monta registros, diagrama, árvore, comparação e matriz. Não aceita `sections`. Recomendação, não implementada: default = resumo; coleções paginadas; include explícito. Não é decisão de nome de query param.

MCP preferido no futuro: `search_records`, `get_record`, prepare/act genéricos, `get_process_context`, `analyze`, `get_methodology_guide`. Actions: `gpt_search_records`, `gpt_get_record`, create/update/delete genéricos, actions de domínio já existentes, `gpt_get_methodology_guide`. Entidade nova entra no schema, não como tool.

| Capability | Rota hoje | Contrato alvo | Rota nova? | MCP / Actions |
|---|---|---|---|---|
| Shell, Início, Visão geral | dashboard já exposto | mesmos GETs | Não | Nenhum |
| Meus processos | listagem de processos | `search_records` ou lista atual | Não na Wave 2 | Genérico |
| Workspace PROVEN | rotas de processo, diagrama, árvore, revisão | composição no cliente com poucas chamadas já existentes | Não | `get_process_context` só se o pacote mostrar N+1 real |
| Interfaces, achado, KPI definition, plano | — | pacote próprio | Só se os 8 checks falharem | Sem tool dedicada por default |

Frontend: cada página declara read model, fonte, refresh, vazio, erro e 403. Não montar domínio com dezenas de chamadas. Não criar mega-endpoint para esconder isso. Cache de dashboard já existe como read model; não inventar outro na Wave 1.

## 9. AuthZ

Códigos PROVEN no manifesto. Escopo de filial: `transformometro.branch.filial-01/02` (aliases `view.filial-*` e `manage.filial-*` são legado). Visão sem filtro de filial: `transformometro.view.consolidated`.

| Capability | Ler | Escrever | Escopo | UI |
|---|---|---|---|---|
| Abrir portal, dashboard, lista | `transformometro.view` | — | filial via branch | esconder item não substitui 403 |
| Processo | view | `processes.manage` | branch | idem |
| Revisão / ativar | view | `revisions.manage` | branch | idem |
| Medição | view | `measurements.manage` | branch | idem |
| Investimento | view | `investments.manage` | branch | idem |
| Recurso | view | `shared-resources.manage` | catálogo | idem |
| Recalcular | view | `dashboard.recalculate` | consolidado à parte | idem |
| JSON | — | `data.transfer` | — | idem |
| Ata | `meeting-minutes.view` | manage / `sign` | — | idem |

Permissão nova é TARGET do pacote da capability, não deste runway. TÉO e o portal não enxergam mais do que o usuário.

## 10. Persistência, auditoria, evidência

Schema owner: `transformometro` em `postgres-plugins`. Versões em `transformometro-api/migrations/` (`schema_migrations`). Arquivo aplicado não se edita. Produção não faz reset. Rollback de migration não está automatizado: o plano do pacote diz se a mudança é expand-contract (coluna nova nullable, backfill, constraint depois).

Auditoria PROVEN: `audit_logs` nas mutações, mais ações `diagram.*.updated` e `decomposition.*.updated`. Timeline lê isso. Ata tem audit próprio. Não há event sourcing.

Quando uma wave criar conceito, o pacote diz se a mutação grava `audit_logs` **no mesmo passe**, não depois. Eventos candidatos (finding, evidência ligada, causa validada, indicador definido, cenário criado/ativado, ação concluída, medição, resultado verificado) só entram se a entidade existir. Ativação de cenário e medição já devem continuar no audit atual.

Evidência: dois donos de binário já existem (arquivo do processo e evidência da revisão). Conceito novo referencia um deles. Não criar blob store. AuthZ do binário acompanha o dono atual.

## 11. Frontend

SHARED UI: TopBar, PageHero, CommandPalette, NavigationCard, KpiCard, FiltersRow, FilterBarShell, SectionCard, EmptyState. DOMAIN UI: workspace, diagrama, árvore, formulários TM. Ficam no MFE.

Rotas PROVEN a preservar na primeira fatia: `/apps/transformometro`, `/dashboard`, `/processes`, `/meeting-minutes`, `/settings/*`, `/data`, `/my-signature`. Aliases PT continuam. Árvore conceitual (`/overview`, `/tasks`, `/portfolio`, `/help`, seções aninhadas) não é path aprovado.

Refator obrigatório antes de feature: nenhum, para a Wave 1. Acoplamento com Comercial está proibido, não presente. Limpar `ProcessContextService` é opcional.

## 12. Grafo e caminho crítico

| Capability | Depende de | Bloqueia | Paralelo? |
|---|---|---|---|
| W0 este runway | inventário já feito | qualquer código | — |
| W1 shell | W0, kit, rotas atuais | W2 navegável | não com rename |
| W2 lista + workspace | APIs PROVEN, W1 | W3–W8 de UX | sim com modelagem no papel, não com migration |
| W3 interfaces + nó | D14, schema da árvore | diagnóstico que aponta para nó | não com W4 se o achado exige o nó novo |
| W4 diagnóstico | W3 se referir nó; evidência atual se só ligar revisão | W7, completude | não com task store |
| W5 definição de KPI | D16 fechada | cards de indicador que não sejam o dashboard atual | sim com W6 |
| W6 AS-IS × TO-BE | revisões e overlays | — | sim com W5 |
| W7 plano de ação | D17 | «minhas tarefas» que dependam de ação | não antes |
| W8 resultado e completude | medição + audit | — | depois de W6 |
| W9 sala, tarefas, portfólio, favoritos | D10 D11 | — | não |
| W10 arquitetura corporativa | processo individual estável | — | não |

Caminho crítico de código, ainda não autorizado:

```text
1. W1 shell sobre rotas atuais
2. W2 Meus processos + workspace existente
3. W3 interfaces, sem colidir com escopo organizacional
4. W4 diagnóstico
5. W5 definição de indicador, depois que D16 fechar
6. W6 AS-IS × TO-BE na UX
7. W7 plano, se o gap continuar
8. W8 resultado e completude
9. W9 colaboração, se o owner aparecer
10. W10 arquitetura corporativa
```

W5 e W6 podem trocar de ordem. W9 não entra no meio.

| Workstream | Pode começar | Depende de | Trilha |
|---|---|---|---|
| Shell | depois que este runway for aceito como ordem | D3 D4 | 05 |
| Modelagem de interfaces no papel | já, como pacote | D14 | 01 + 08 |
| Migration, MCP, sala, portfólio | não | pacote com DoR | 01 / 02 / 06 |

## 13. Waves

A Wave 1 está IMPLEMENTED_NOT_RUNTIME_PROVEN (SHA `383e07b73`, MFE em `srv-api`, browser smoke TEST_NOT_RUN). As demais continuam NOT_READY_FOR_IMPLEMENTATION até o pacote da §14. W0 é este documento.

| Wave | Objetivo | Inclui | Não inclui | Trilha | Aceite quando for executada |
|---|---|---|---|---|---|
| 0 | Congelar base | este arquivo | tela nova | 08 | sequência única, sem segunda ordem |
| 1 | Shell | nav, Início e Visão geral em cima do dashboard, Meus processos apontando para `/processes`, Administração para `/settings`, Ajuda só se for página de conteúdo sem backend novo | sala, task store, portfólio, favorito próprio, path novo | 05, 06 se o manifesto mudar | deep link antigo abre; 403 continua; nenhum import do Comercial |
| 2 | Processo no centro | lista, filtros que o backend já calcula, workspace atual, arquivos, timeline | seções TARGET | 05 | os mesmos registros de hoje |
| 3 | Limite do processo | gatilho, resultado, fornecedores, entradas, saídas, clientes, detalhe do nó | entidade SIPOC | 01 depois 05 | escopo organizacional intacto |
| 4 | Diagnóstico | achado, hipótese, elo de evidência, fator crítico | Lean/Ishikawa como tabela | 01 | hipótese não vira fato |
| 5 | Indicador | definição separada do valor | duplicar strategic-indicators | 01 | medição atual lê igual |
| 6 | AS-IS × TO-BE | baseline, cenário, overlays, comparação | segunda fonte | 05 + 01 se faltar projeção | cenário não aparece como produção |
| 7 | Plano de ação | só com gap confirmado | store paralelo; módulo de Qualidade | 01 | owner nomeado |
| 8 | Aprendizado | resultado verificado, timeline, completude | event sourcing; nota subjetiva | 01 + 05 | audit no mesmo passe |
| 9 | Pessoal | tarefas, sala, portfólio, favoritos, notificação | qualquer coisa sem owner | 01 + 06 | participação não vem de cargo |
| 10 | Corporativo | cadeia de valor | árvore do mestre | 01 | boundary escrito |

## 14. Pacote, DoR, DoD, testes

Nenhuma wave de código começa sem um pacote neste formato, preenchido com evidência, não com a tabela genérica acima:

```text
FEATURE
Goal / Owner / Canonical source
Current / Target
Domain / Use cases
Persistence / Migration
Read contract / Write contract
AuthZ / API / MCP / GPT Actions
Frontend / Audit / Evidence
Tests / Acceptance / Runtime verification
Rollback / Risks / Gaps
Status = NOT_READY_FOR_IMPLEMENTATION até o DoR
```

DoR decide se a wave pode começar. DoD decide se ela pode ser declarada concluída. Não misturar.

```text
CODE COMPLETE != IMPLEMENTATION DONE != PRODUCTION VERIFIED
technical success != business outcome
HTTP 2xx != write success
```

DoR: owner PROVEN, source PROVEN, boundary DECIDED, contrato de domínio DECIDED, AuthZ DECIDED, persistência DECIDED, impacto de API/MCP/Actions DECIDED, UX DECIDED, plano de migration READY ou NOT_APPLICABLE, testes READY, aceite READY. Falta um item necessário → não implementar.

DoD, por tipo de passe:

| Tipo | Runtime / deploy | Outcome |
|---|---|---|
| Só documentação | NOT_APPLICABLE | NOT_APPLICABLE |
| Código sem release neste passe | DEFERRED_BY_SCOPE. Não chamar de produção | NOT_APPLICABLE se não houver write |
| Runtime alterado | SHA, build, deploy, health, smoke, proveniência do ambiente | Se houver write: read-back autoritativo. Falha = `OUTCOME_VERIFICATION_FAILED`. 2xx não basta |
| Wave 1, quando for executada | Frontend implantado: SHA, build, health e smoke no browser da versão que subiu | NOT_APPLICABLE. A wave não exige write |

Itens do DoD só entram quando o pacote os marcar como materiais: código no owner, positive/sibling/negative, AuthZ fail-closed, migration `up`, OpenAPI se o HTTP mudar, descoberta MCP se a tool mudar, reimport de Actions se o schema mudar, estados de UI (loading, vazio, erro, 403), busca residual, docs da fonte canônica. Teste local verde não é produção.

Pirâmide: unitário de domínio e application quando houver regra nova; repositório se houver SQL; contrato HTTP se a rota mudar; AuthZ negativo; componente de UI na wave de tela; adapter MCP/Actions só se o pacote mexer neles. Dashboard e workspace atuais são o sibling que não pode quebrar.

## 15. Primeira fatia recomendada

**Portal shell + Meus processos em leitura + workspace que já existe.**

Pacote: [WAVE-1-IMPLEMENTATION-PACKET.md](./WAVE-1-IMPLEMENTATION-PACKET.md). Desenho: [PORTAL-TRANSFORMA-BLUEPRINT.md](./PORTAL-TRANSFORMA-BLUEPRINT.md). Status: **IMPLEMENTED_NOT_RUNTIME_PROVEN**. A IA da TopBar foi revista: itens sem capability ficam TARGET oculto (sala, tarefas, ajuda, favoritos, usuário). As outras waves continuam sem pacote.

## 16. Drift

| Item | Classe |
|---|---|
| Três sequências (PI, fases A–I, playbook 0–6) | CONFLICT de calendário, resolvido: este arquivo manda na ordem. Conteúdo permanece no dono |
| «Portal Transformômetro» no playbook | HISTORICAL como nome de experiência |
| `status-atual` / ESPECIFICACAO jul/2026 | STALE como fotografia do produto inteiro. Regras de cálculo daquele arquivo não foram reauditadas aqui |
| Sala, favoritos, pedidos | CURRENT no Comercial, não no TM |
| `search_records`, `prepare_`, `act_`, `analyze`, `get_process_context` | CURRENT de adapter. `analyze` está em `TOOL_CLASS` como READ. O único ANALYSIS é `generate_from_transcript` |
| Finding, SIPOC entidade, plano de ação TM | TARGET ou TO_INVENTORY, não CURRENT |
| Contagem MCP/Actions | PROVEN no código em `TOOL_CLASS` (33) e `GPT_ACTIONS_OPERATION_IDS` (21). Meta `gpt_get_openapi_schema` fora. 20 Actions e 32 tools = HISTORICAL (2026-09-17). 14 Actions = HISTORICAL mais antigo |
| `gpt-builder-go-live.md` linhas que ainda diziam «20 actions» como critério atual | DOC_DRIFT corrigido neste passe. O reimport no Builder continua TEST_NOT_RUN |
| `.cursor/rules/openai-plugin-mcp-integration.mdc` exemplo «32 tools ≠ 20 Actions» | CURSOR_RULE_DRIFT = RESOLVED. O exemplo numérico saiu. Ficou a regra atemporal: tool count ≠ operation count; capability parity ≠ surface count parity |
| `ProcessContextService` importa `Request` FastAPI, `interface.http.branch_access_http` e repositórios concretos | CODE_DRIFT = OPEN_NON_BLOCKING. PROVEN. Wave 1 = NOT_USED. Correção pequena seria enganosa: não há ports desses repositórios e a AuthZ está no helper HTTP. Não é FALSE_POSITIVE e não bloqueia a Wave 1 |
| Definition of Done sem deploy | RESOLVED na §14. Docs = NOT_APPLICABLE. Release = SHA/deploy/smoke. Write = read-back ou `OUTCOME_VERIFICATION_FAILED` |
| Wave 1 | IMPLEMENTED_NOT_RUNTIME_PROVEN. SHA `383e07b73` no MFE de `srv-api`. Browser smoke TEST_NOT_RUN |
| AuthZ multiunidade | Hardening de enforcement aplicado. Manifesto não migrado. AUTHZ_MIGRATION = NOT_READY. Ver [AUTHZ-SIMPLIFICATION.md](./AUTHZ-SIMPLIFICATION.md) |
| «editor Mermaid bidirecional» em `status-atual.md` | TO_INVENTORY. `flowchart_v1` segue canônico; Mermaid tem export e parser no kit. Este passe não reprovou ida e volta |

Esta seção é o ledger de gap/drift da evolução Portal Transforma+ / TÉO. Não abrir outro ledger para o mesmo assunto.

## 17. Riscos

Começar pela Wave 4 antes do shell e chamar isso de portal. Tratar o contexto atual como se já tivesse `sections`. Promover path conceitual a rota. Criar permissão por tela. Tratar READY_FOR_ARCH_REVIEW como licença para codar. Este arquivo não autoriza implementação.
