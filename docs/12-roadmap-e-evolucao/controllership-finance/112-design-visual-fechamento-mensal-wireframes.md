# 112 — Design visual colaborativo: Fechamento mensal (wireframes por página)

**Data:** 2026-10-26. **Produto:** Portal Controladoria & Finanças. **Processo:** PROC-0072. **Natureza:** abertura de ciclo de DESIGN / documentação; **nenhum GO de implementação**, nenhuma migração/alteração em runtime.

**Estado:** `DESIGN_IN_PROGRESS / PENDING_PO_VISUAL_APPROVAL`. A solicitação do PO é criar a experiência de uma página central chamada **Fechamento mensal** e desenhar **todas as páginas e componentes incrementalmente**, sempre validando visualmente na conversa e atualizando o GitHub com as decisões aprovadas. Este documento registra um **wireframe V0.1 proposto**, não uma decisão definitiva sobre rotas, remoção de páginas, domínio, esquema de banco ou regras de workflow.

**Base e precedência:** [instruções oficiais GPT Arquiteto](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md); regras `.cursor` aplicáveis, a carregar pelo executor; [padrão visual dos Portais](../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md); [mapa de reuso plugin-ui 30](./30-plugin-ui-reuse-map.md); [README de estado](./README.md); [ledger RQ/AC 23](./23-ledger-rq-ac-testes.md); [P1 cockpit 08](./08-p1-cockpit-da-competencia.md), [P2 checklist e documentos 09](./09-p2-checklist-e-documentos.md), [P3 conciliação 10](./10-p3-estoque-cutoff-e-conciliacao.md), [P4 pendências 11](./11-p4-classificacoes-e-pendencias.md), [P5 revisão 37](./37-p5-submissao-e-revisao-no-portal.md), [roadmap 93](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md), [CLARA smoke 111](./111-clara-chatgpt-smoke-autenticado-retomada-central-2026-10-26.md).

## 1. Problema observado em produção

Screenshots do usuário na rota `https://minhadelpi.com.br/apps/controllership-finance` em 26/10/2026 mostram página **Início** em tema claro com:
- cabeçalho/saudação e cartões de **Competência** e **Atenções** com traços no lugar de valores;
- seção **Eventos e interações** exibindo “Eventos operacionais indisponíveis nesta versão”;
- seção **Caminhos e funcionalidades** listando Checklist da competência, Baixas financeiras, Administração do checklist, Catálogos governados, Pendências do fechamento, Pacotes e revisão, Cockpit do fechamento e Estoque histórico — P7.

**PROVEN por screenshot:** navegação atual apresenta diversos destinos separados; não há nesta captura uma bancada unificada de trabalho na Home. **Não inferir** falha nas páginas de destino, ausência de dados reais no backend ou impossibilidade operacional por uma imagem da Home.

**Objetivo de UX aprovado em nível de intenção:** simplificar a descoberta e o tratamento de **divergências, documentos, pendências e estado da competência**, tornando **Fechamento mensal** uma entrada operacional clara. **DECISION_REQUIRED** sobre estrutura final de rotas/abas, reagrupamento ou desativação de links existentes; preservar deep routes e backward compatibility até decisão e inventário.

## 2. Método e gates do design

`DISCOVER EXISTING CONTRACTS → WIREFRAME CHAT → COMPONENT BREAKDOWN → VISUAL STATES → PO REVIEW → DOC UPDATE + SHA → NEXT PAGE`. A aprovação visual não autoriza implementação. Se a página for grande, trabalhar componente por componente e manter versões V0.1, V0.2, APPROVED. Para cada elemento, registrar: propósito, origem do dado (owner/producer), RQ/AC, estado vazio/loading/partial/error, ação, AuthZ, foco/teclado, mobile, Help, dependências, status `PROVEN|TO_INVENTORY|PLANNED|TARGET`.

Não inventar endpoints, permission codes, indicadores, colunas de banco, números financeiros ou ações de correção automáticas. Core continua authority de effective permissions; `api-delpi` de regras TOTVS; MFE só chama sua BFF. `@delpi/plugin-ui/index` e CSS do kit primeiro, não duplicar chrome e controles.

## 3. Sequência proposta do desenho (a validar pelo PO)

1. **Página operacional Fechamento mensal**: arquitetura visual geral, contexto de competência, KPIs e fila priorizada.
2. **Visão Divergências**: lista/master-detail, proveniência e drilldown em owner P3/P4; não pressupor persistência de uma entidade transversal chamada divergência.
3. **Visão Documentos**: checklist/evidências P2, anexos/versionamento/validação conforme contratos existentes; vinculação nova entre entidades = `DECISION_REQUIRED` se não prevista.
4. **Visão Pendências**: worklist, responsáveis, histórico, owner P4.
5. **Visão Revisão**: pacotes, submissão e decisões humanas P5, sem pular segregação e gates.
6. **Elementos de apoio**: administração/catálogos governados P6, estoque histórico P7 e outras rotas existentes preservadas até inventário e decisão explícita.

**Observação:** páginas comuns do Portal (Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda, perfil como deep route) continuam padrão de plataforma. A nova página é domínio e não substitui automaticamente a TopBar comum.

## 4. Wireframe 01 — Fechamento mensal / Visão geral V0.1

**Estado:** `TARGET / DRAFT / PO_REVIEW_PENDING`; exemplo sem dados reais.

```text
TOPBAR PADRÃO MINHA DELPI (plugin-ui; não duplicar)
──────────────────────────────────────────────────────────────────────────
Fechamento mensal                              [Ajuda] [Atualizar]
Acompanhe e trate os itens da competência
[Competência: selecionar ▼] [Status: derivado da BFF] [escopo visível]
──────────────────────────────────────────────────────────────────────────
[Divergências: —] [Documentos pendentes: —] [Bloqueios: —]
───────────── NAVEGAÇÃO DA BANCADA ─────────────────────────────────────────
[Visão geral] [Divergências] [Documentos] [Pendências] [Revisão]
──────────────────────────────────────────────────────────────────────────
O que precisa de atenção
[Filtros de competência/escopo/status] [Pesquisar itens...] [Atualizar]
┌────────────────────────────────────────────────────────────────────────┐
│ Tipo / Descrição       Origem       Responsável  Situação  Abrir detalhe│
│ ... dados reais somente após producer + AuthZ + RQ/AC validados ...    │
└────────────────────────────────────────────────────────────────────────┘
[estado parcial / indisponibilidade com causa e freshness] [histórico]
```

### 4.1 Componentes V0.1

| ID | Componente | Conteúdo mínimo | Dono visual e observações | Status |
|---|---|---|---|---|
| FM-01 | Shell / TopBar | Navegação, Buscar, favoritos, usuário | **@delpi/plugin-ui** — preservar padrão comum | PROVEN (padrão), composição nova TARGET |
| FM-02 | PageHero + título + Help | Fechamento mensal, descrição, estado do refresh | `createDashboardPageHero`, `createDashboardPagePath`, Help contextual | TARGET |
| FM-03 | CompetenceSelector | Competência ativa, deep link e escopo | Contrato/producer exatos `TO_INVENTORY`; nunca inventar competência | TARGET |
| FM-04 | StatusSummary | Estado derivado do processo, fonte/freshness | Não somar independentemente eixos P2/P3/P5 nem confundir ausência com zero | TARGET |
| FM-05 | MetricStrip | Divergências, documentos pendentes, bloqueios | Valores apenas se houver contrato; `—` = ainda não carregado/indisponível, com motivo textual acessível | TARGET |
| FM-06 | WorkspaceViews | Visão geral / Divergências / Documentos / Pendências / Revisão | **Proposta de visualização, não decisão de rota**; teclado/mobile | TARGET |
| FM-07 | WorkQueue | Busca, filtros, registros e ação para abrir detalhe | `DataTableSection`/worklist do kit; agregação cross-context exige owner/contrato | TO_INVENTORY |
| FM-08 | DetailPanel | Resumo, origem, documentos relacionados, timeline, ações autorizadas | `ResizableColumns`, `Timeline`, estados e AuthZ backend; ações dependem do owner | TARGET |
| FM-09 | Feedback states | loading/empty/partial/error/fail-closed | `StateBanner`, `EmptyState`, `LoadingState` | TARGET |

### 4.2 Estados e responsividade obrigatórios
- **Desktop:** contexto + fila; detalhe em master-detail quando seleção contínua justificar.
- **Mobile:** fila → detalhe full width, filtros colapsáveis, botões acessíveis, sem tabela larga comprimida.
- **Claro/escuro:** mesma árvore, tokens do kit; foco visível, labels PT-BR e navegação por teclado.
- **Estados:** loading, empty real, unavailable source, partial, error, permission denied; freshness explícita quando contrato permitir.
- **Ações:** nenhuma operação ACT será presumida; clique pode navegar ao owner da operação até contrato de tratamento ser aprovado.

## 5. Perguntas de produto pendentes (não implementar)
1. A navegação interna será por abas com deep links persistentes, ou páginas filhas sob rota única? **DECISION_REQUIRED** após inventário de rotas.
2. Fila de trabalho combinará dados de P2/P3/P4/P5 ou terá visões separadas? Exige owner/contrato para agregação e definição de prioridade. **DECISION_REQUIRED**.
3. “Divergência” é leitura derivada de conciliação P3 e pendência P4 ou uma nova entidade gerenciada? Não criar esquema sem decisão e evidência. **DECISION_REQUIRED**.
4. Qual competência deve aparecer inicialmente e quem pode alterá-la? **TO_INVENTORY**.
5. Links antigos da Home permanecem como atalhos, migram ou são retirados? Preservar compatibilidade até decisão. **DECISION_REQUIRED**.

## 6. Critério de aprovação da página

O PO deve conseguir identificar em até uma leitura da tela: (a) competência, (b) situação e bloqueios com fonte, (c) itens para trabalhar, (d) onde tratar documentos e divergências, (e) caminho para histórico/revisão. Aceite visual requer desktop/mobile/teclado/tema/Help, além dos estados de vazio/erro e mapeamento componente→RQ/AC→owner. **Design aprovado ainda não significa backend pronto ou E2E PASS.**

## 7. Próxima ação

Revisar **FM-01 a FM-03 (cabeçalho, contexto e competência)** no chat com o PO. Atualizar este documento a cada aprovação e versionar os wireframes. Não iniciar código antes da aprovação de toda a composição transversal e de GO específico.


## 8. Wireframe 01 — detalhamento V0.2 após concordância do PO com a estrutura geral

**Registro de interação (26/10/2026):** PO concordou com a estrutura de cinco visões **Visão geral, Divergências, Documentos, Pendências, Revisão** e solicitou maior detalhamento da página. Isto aprova a **direção da arquitetura de informação**, **não** os campos, agregações, indicadores, mutações, rotas ou contrato técnico definidos abaixo. **Status:** `PO_APPROVED_INFORMATION_ARCHITECTURE / V0.2_COMPONENTS_UNDER_REVIEW`.

### 8.1 Objetivo mensurável para o usuário

Na chegada, responder nesta ordem:
1. **Qual competência e escopo estou examinando?**
2. **O que impede ou ameaça o fechamento?**
3. **O que posso tratar agora, e quem é o responsável?**
4. **Qual evidência ou documento sustenta cada ocorrência?**
5. **Qual é o próximo passo e o estado de revisão humana?**

Uma página de trabalho deve reduzir alternância entre destinos sem converter páginas existentes em novas entidades de domínio por suposição.

### 8.2 Composição visual em desktop — refinamento

```text
[TopBar canônica da Minha DELPI: Início | Visão geral | ... | Administração | Ajuda]
[PagePath] Controladoria & Finanças / Fechamento mensal
Fechamento mensal                    [Ajuda da página] [Atualizar]
Acompanhe a competência, investigue divergências e trate documentos.
[Competência 09/2026 ▼] [Empresa/unidade: escopo autorizado ▼] [Status do fechamento]
[Última atualização: origem e timestamp, ou "indisponível"]
────────────────────────────────────────────────────────────────────────────
[ Bloqueios relevantes — ] [ Divergências — ] [ Documentos a tratar — ]
Cada número abre a visão filtrada SE houver contrato de contagem e drilldown.
────────────────────────────────────────────────────────────────────────────
[ Visão geral ] [ Divergências ] [ Documentos ] [ Pendências ] [ Revisão ]
────────────────────────────────────────────────────────────────────────────
[Precisa de atenção]                 [Busca] [Status ▼] [Origem ▼] [Atualizar]
[empty/partial/error banner com fonte, motivo e freshness]
┌────────────────────────────────────────────────┬─────────────────────────┐
│ LISTA DE TRABALHO / AGRUPAMENTO POR ORIGEM       │ DETALHE SELECIONADO      │
│ Prioridade | Tipo | Item | Owner | Estado        │ Título + provenance     │
│ ... origem P2/P3/P4/P5 quando houver producer   │ Descrição, dependências  │
│ ... nunca inventar fila unificada              │ Evidências relacionadas  │
│ Paginação/filtro/contagem legítima              │ Timeline, ações elegíveis│
└────────────────────────────────────────────────┴─────────────────────────┘
[Histórico por competência] [Acessos rápidos às rotas legadas autorizadas]
```

**Densidade:** cabeçalho compacto para reservar espaço à bancada; cartões de KPI são links de contexto, nunca decoração. Sem hero de saudação duplicado da Home. Os valores `—` são apenas placeholder de wireframe; runtime precisa diferenciar carregando, sem dados e fonte indisponível.

### 8.3 Matriz detalhada de componentes

| ID | Detalhe de UX | Evento previsto | Dependência para runtime |
|---|---|---|---|
| FM-01 | TopBar compartilhada permanece constante; área de domínio nasce abaixo dela | Navegar por seção comum/voltar | plugin-ui + padrão shell (PROVEN do padrão) |
| FM-02 | PagePath, título "Fechamento mensal", descrição breve, Ajuda contextual, Atualizar | Ajuda abre manual; refresh refaz somente reads autorizados | PageHero/Help kit; endpoint/read model de refresh TO_INVENTORY |
| FM-03 | Seletor de competência com `MM/AAAA`, contexto de empresa/unidade por escopo real, deep link e preservação em troca de visão | Selecionar competência restaura filtros; escopo inválido gera no-access, não zero | owner de competência e contratos de contexto T05 TO_INVENTORY |
| FM-04 | Estado oficial mostrado com rótulo e `freshness`; três eixos P2/P3/P5 não viram "concluído" por agregação arbitrária | Abrir explicação de status e blockers | P1/contratos e regras de conclusão PROVEN documental, integração TO_INVENTORY |
| FM-05 | Três cartões: Bloqueios, Divergências, Documentos a tratar; descrição no tooltip e drilldown quando suportado | Selecionar filtro da visão respectiva | contagens/fontes e semântica de divergência TO_INVENTORY |
| FM-06 | Abas: Visão geral / Divergências / Documentos / Pendências / Revisão, com indicador ativo sem depender apenas de cor | Trocar visão mantendo competência; deep links pendentes de decisão | URL e backward compatibility DECISION_REQUIRED |
| FM-07 | Fila principal: prioridade, tipo, descrição, área/owner, estado, atualização, ação de abrir; busca, filtros e paginação | Selecionar registro abre detalhe sem perder filtros e scroll | read-model transversal/ordenação/ownership TO_INVENTORY; alternativa: blocos separados por owner |
| FM-08 | Detalhe apresenta contexto, motivo, regra/fonte, anexos relacionados, timeline, ação encaminhada ao owner | Abrir documento, ver origem, navegar para tratamento permitido | P2/P3/P4/P5 producers e AuthZ; cruzamento de recursos TO_INVENTORY |
| FM-09 | Estados: skeleton, empty real, partial, permission denied, erro de rede, indisponibilidade de source, stale | Retentar sem apagar contexto, abrir Help | kit `StateBanner`/`EmptyState`/`LoadingState`; mensagens PT-BR |
| FM-10 | Acesso a histórico, evidências e ações de revisão | Abrir detalhe ou rota legada | não sacramentar/validar/concluir fora de P2/P5 owner |

### 8.4 Comportamentos essenciais e limites de domínio

- **Divergência** não significa automaticamente uma entidade nova. Pode ser resultado de conciliação P3 ou ocorrência do fluxo P4; preservar proveniência e tipos do backend.
- **Documento** mantém estados `EXPECTED`, `ATTACHED`, validação/rejeição, versões e vínculo real. Upload não implica aceite e apenas o owner P2 executa mutação autorizada.
- **Pendência** pertence às classificações/workflows governados existentes; prioridade e responsável devem ser derivados de contratos, não imputados pelo frontend.
- **Revisão** mantém decisões humanas, segregação de funções, versões de pacote, esclarecimentos e blockers; sem conclusão por percentual.
- **Competência** é eixo transversal. Se o contexto mudar, a lista e o detalhe precisam ser revalidados; evitar exibir um detalhe da competência anterior.
- **Segurança:** UI só sinaliza elegibilidade; a BFF aplica Core effective permissions AND resource scope/ownership AND business rule, fail-closed; nenhuma permission nova.

### 8.5 Cenários UX para desenhar após visual principal

1. Competência selecionada com pendências reais — fila, detalhe e documento.
2. Competência sem itens — mensagem de vazio verdadeiro, sem `0` fictício.
3. Fonte ERP indisponível — `PARTIAL/UNAVAILABLE_SOURCE`, quais informações estão desatualizadas, origem.
4. Usuário sem `manage` ou fora do escopo — pode ler o permitido, sem ação mutável; backend revalida.
5. Mudança rápida de competência e filtros — cancelar detalhes anteriores, manter contexto consistente.
6. Documento substituído/rejeitado — timeline e versões, estado atual não sobrescreve histórico.
7. Revisão com esclarecimento aberto — blocker explicado e nenhuma conclusão indevida.
8. Loading lento, timeout e retry — preservação de filtros e indicação de freshness.

### 8.6 Desktop, mobile e acessibilidade

- Desktop: bancada `master-detail` quando houver item selecionado; cabeçalho resumido e tabelas densas de trabalho.
- Mobile: contexto e KPIs empilhados, abas navegáveis com labels, lista de cards `DataRecordCard`, detalhe como tela separada com `BackLink`, filtros recolhíveis.
- Teclado: tab order previsível; filtros, abas e fila com foco visível; seleção e retorno de detalhe acessíveis; sem ações escondidas só em hover.
- Tema claro/escuro usa a mesma árvore do `@delpi/plugin-ui`; tipografia, espaços, status e ícones do kit, sem duplicar CSS.
- Help contextual deve acompanhar o gate de cada feature e explicar diferença entre divergência, pendência, evidência e bloqueio.

### 8.7 Próximo review visual em componentes

**Primeiro bloco a detalhar/validar: FM-02 + FM-03 + FM-04 (cabeçalho, seleção da competência, contexto/estado).** Depois: FM-05 indicadores; FM-06 abas; FM-07/08 fila e detalhe; FM-09 estados; por fim composições das visões Divergências, Documentos, Pendências e Revisão, uma por vez.

**Não aprovar implicitamente** contagem de KPIs, dataset transversal, alteração de URL, remoção dos atalhos atuais, nova entidade divergência, persistência ou endpoints com base no aceite do wireframe geral.


## 9. Página Fechamento mensal — cabeçalho FM-02/FM-03/FM-04 — Wireframe V0.3 (26/10/2026)

**Estado:** `TARGET / DETAILED_PROPOSAL / PENDING_PO_COMPONENT_APPROVAL`. Não implica aprovação de rota, endpoint, cardinalidade de selector ou implementação. A estrutura de cinco visões da bancada foi aceita como orientação, mas os elementos e comportamentos deste cabeçalho estão sob revisão.

### 9.1 Hierarquia visual e limites

```text
[TOPBAR COMUM / @delpi/plugin-ui — EXISTENTE, FORA DA PÁGINA]
Início / Central de Fechamento / Fechamento mensal
─────────────────────────────────────────────────────────────────────────
FECHAMENTO MENSAL                                      [? Ajuda] [↻ Atualizar]
Acompanhe divergências, documentos e pendências desta competência.

[ COMPETÊNCIA                  ] [ EMPRESA / UNIDADE — CONTEXTO         ]
[ 09/2026 ▼                    ] [ Todas autorizadas ▼ / somente escopo ]
[ Situação da competência: texto derivado ] [Atualizado em ... / fonte...]
─────────────────────────────────────────────────────────────────────────
[ ALERTA/BLOCKER CRÍTICO, SE REAL E COM FONTE ]  ← antes de indicadores
[ cartões de indicadores: bloco separado FM-05 ]
```

**Ordem:** PagePath → título e propósito → ações utilitárias → seletor de competência e escopo → estado geral com provenance/freshness → alertas materiais. Não duplicar avatar, Buscar, Favoritos ou saudação da Home. `TopBar` permanece no shell da plataforma. No mobile, título e ações em linhas separadas, selectors empilhados.

### 9.2 FM-02 — Título, contexto e ações

| Campo/controle | Rótulo PT-BR | Regra |
|---|---|---|
| Breadcrumb | `Controladoria & Finanças / Central de Fechamento / Fechamento mensal` | Deep links só após conferir router; breadcrumbs não simulam navegação sem rota real |
| Título | `Fechamento mensal` | H1 único da página, sem saudação pessoal |
| Subtítulo | `Acompanhe divergências, documentos e pendências da competência selecionada.` | Sem afirmar que toda correção ocorre nesta superfície |
| Ajuda | `Ajuda desta página` | Explica competência, divergência vs pendência vs bloqueio, documentos e revisão; sincronizar com feature |
| Atualizar | `Atualizar dados` | Atualiza projeções de leitura, mantém seleção e filtros; spinner/indicação de sucesso/erro com timestamps quando contratados; não executa mutation |
| Estado de atualização | `Atualizado em [data/hora] · origem [...] ` ou `Fonte indisponível` | Tempo deve vir da fonte real; não usar relógio do browser como freshness canônica |

### 9.3 FM-03 — Seletor de competência e escopo

**Competência** é o controle de maior prioridade no cabeçalho. Escolha de UX recomendada **para decisão**: seletor de **competências existentes e autorizadas**, com `MM/AAAA` legível e busca rápida; permitir navegação por mês/ano como filtro, **não** criar competência automaticamente ao escolher mês. Necessita inventário de endpoint/listagem e autorização real. Sem lista disponível, mostrar `Não foi possível consultar competências` + tentar novamente, e jamais criar estado inventado.

**Empresa/unidade**: exibir somente se o contrato da competência envolver esse contexto. O seletor deve listar apenas recursos dentro do escopo autorizado; `Todas as unidades` só existe se a API permitir agregação explícita. Filial/unidade não vira permission code. Se só houver uma opção, mostrar chip informativo/read-only em vez de dropdown falso.

**Troca de competência**: revalidar toda a bancada, remover detalhe de contexto anterior, preservar a visão ativa apenas se compatível, zerar filtros incompatíveis com aviso discreto, atualizar deep link sem deixar o usuário em rota de recurso antigo. Em erro, manter contexto anterior com alerta e retry; nunca apresentar dados do mês antigo sob título do novo.

### 9.4 FM-04 — Estado geral da competência

O status exibido é **resumo derivado da BFF**, não campo editável. Não usar um indicador genérico `Concluído` por percentual; preservar os eixos **Estoque / Documentos / Pacote** (P1) independentes, com bloqueio de conclusão se source não disponível ou esclarecimento aberto conforme contratos. Status possíveis **na UI ilustrativa**: `Em andamento`, `Aguardando revisão`, `Concluído`, `Informação indisponível` — mapear somente depois de conferir enum/DTO real e seu owner. Proibir status hardcoded como verdade de negócio.

Mostrar `Estado geral`, um badge semântico com texto, texto auxiliar `Situação derivada dos eixos de fechamento`, botão/link `Ver critérios de conclusão` quando houver rota real. Blockers críticos visíveis **imediatamente abaixo do cabeçalho**, antes de KPIs, com fonte/owner/ação de navegação; não esconder atrás das cinco abas.

### 9.5 Matriz de estados

| Estado | Comportamento |
|---|---|
| Inicial/loading | Skeleton apenas nos campos de domínio; título/Ajuda preservados |
| Competência não selecionada | `Selecione uma competência para começar`, sem contagens fictícias |
| Sem competências elegíveis | Empty state `Nenhuma competência disponível no seu escopo`, distinguir autorização e ausência real |
| Read-only/sem manage | Seleção e READ conforme access/scope; nenhuma mutação exposta |
| Fonte indisponível | `Dados operacionais indisponíveis` e motivo/fonte; não concluir que são zero |
| Partial/stale | Banner de parcial/freshness, contagens só das fontes válidas e explicitamente rotuladas |
| Erro ao trocar contexto | Contexto anterior permanece; erro acessível com retry; sem mistura de dados |
| Revogação de acesso | Fail-closed da BFF/Core; expurgar detalhes fora de escopo |
| Competência concluída | Estado somente se owner provar conclusão humana; leitura preservada, ações condicionadas |

### 9.6 Componentização plugin-ui e DoD visual

`createDashboardPagePath`, `createDashboardPageHero`, `StatusBadge`, `StateBanner`, `LoadingState`, `EmptyState`, `HelpTooltip`, `ActionButton` e selectors do kit conforme catálogo vigente. Evitar criar componentes genéricos paralelos. Desktop: selectors em linha após heading; mobile: stack, affordance de seletor, refresh acessível. Foco visível e sem informação codificada exclusivamente por cor; mesma árvore em claro/escuro. Testes de mudança de competência, recuperação de rede, rota/deep link, contexto único/vários, source partial, no-access e atualização.

### 9.7 Decisões reais para PO

- **D-HEADER-01 = A — PO_APPROVED (26/10/2026):** seleção principal **exclusivamente entre competências existentes e autorizadas**, apresentadas em `MM/AAAA`, com busca por mês/ano. Calendário livre não é navegação principal; escolher período não cria competência. O producer da listagem e deep link seguem `TO_INVENTORY`, não implicando endpoint aprovado.
- **D-HEADER-02:** se houver mais de um escopo de empresa/unidade, exibir seletor contextual quando producer real permitir; caso contrário chip informativo. **PENDING_INVENTORY** (comportamento recomendado).
- **D-HEADER-03:** status textual derivado com detalhe dos três eixos P1 e freshness; **TARGET consistente com doc 08**, requer DTO real.
- **D-HEADER-04:** breadcrumbs e deep link devem respeitar router existente e compatibilidade retroativa; nenhum path novo é aprovado por este wireframe.

**Próximo ciclo:** D-HEADER-01 aprovado pelo PO; detalhar FM-05 (indicadores) na V0.4, depois FM-06 abas, mantendo rastreabilidade.


## 10. Decisão PO do cabeçalho e proposta FM-05 — Indicadores de atenção V0.4

**Data:** 26/10/2026. **D-HEADER-01=A / PO_APPROVED** conforme manifestação explícita do PO no chat: “Aprovo a opção A: o seletor deve listar competências existentes e autorizadas.” A aprovação limita-se ao comportamento de seleção; não comprova producer, persistência, autorização de desenvolvimento nem aceita automaticamente o design dos demais componentes.

### 10.1 FM-05 — Objetivo e posição no layout

**Objetivo:** oferecer leitura rápida do que exige ação na competência, sem transformar métricas em um resumo enganoso do estado de conclusão. Os indicadores ficam **abaixo do cabeçalho de competência e do banner de blocker material** e **acima das cinco visões**. Cada cartão abre uma visão operacional já filtrada **somente quando houver contrato de contagem + drilldown**; em fonte indisponível, o cartão não apresenta zero falso.

```text
┌──────────────────────┬──────────────────────┬────────────────────────┐
│ BLOQUEIOS            │ DIVERGÊNCIAS         │ DOCUMENTOS A TRATAR     │
│ [—]                  │ [—]                  │ [—]                    │
│ Impedem avançar      │ Exigem investigação  │ Pendentes/validação*   │
│ [Ver bloqueios →]    │ [Ver divergências →] │ [Ver documentos →]     │
└──────────────────────┴──────────────────────┴────────────────────────┘
*subtipos reais serão aqueles do owner P2; sem inventar soma ou estado.
```

### 10.2 Cartões e semântica

| ID | Título de UI | Definição visual | Origem e limite | Clique previsto | Situação |
|---|---|---|---|---|---|
| FM-05A | **Bloqueios** | Contagem factual dos impedimentos materiais, texto “Impedem avançar”; lista precisa mostrar motivo e owner | P1 compõe P2/P3/P5; deduplicação/total dependem de contrato; não confundir pendência qualquer com blocker | Vai à Visão geral com foco/âncora na seção de bloqueios | `TARGET / CONTRACT_TO_INVENTORY` |
| FM-05B | **Divergências** | Contagem de diferenças/anomalias verificáveis, texto “Exigem investigação”; não inventar limite monetário | P3/owner de conciliação e/ou ocorrências P4; evitar dupla contagem e entidade nova | Vai a Divergências com filtro relevante | `TARGET / CONTRACT_TO_INVENTORY` |
| FM-05C | **Documentos a tratar** | Contagem de evidências/itens que exigem alguma ação, texto “Envio, validação ou substituição”; subtipo esclarecido no drilldown | P2, estados reais como EXPECTED, ATTACHED, UNDER_REVIEW, REJECTED; a regra de inclusão precisa vir do DTO/owner | Vai a Documentos filtrado por tratamento | `TARGET / CONTRACT_TO_INVENTORY` |

**Não somar os três cartões em um “total pendente”**: podem se sobrepor por causa e relação. Não apresentar `0` quando fonte não retornou dados válidos, nem usar `100%` como conclusão. Cartão de bloqueios pode ficar visualmente mais saliente **somente se houver blocker real**, sem badge colorido decorativo. As três legendas ajudam compreensão e leitores de tela.

### 10.3 Aparência e hierarquia

- Desktop amplo: 3 cartões em linha com altura coerente, título pequeno, número de maior peso, descrição, link textual de drilldown; espaço vertical econômico para preservar fila abaixo.
- Tablet: 2 cartões na primeira linha, terceiro abaixo se o componente responsivo determinar.
- Mobile: cartões empilhados, cada alvo clicável acessível; sem números cortados; títulos e textos permanecem visíveis.
- Não criar CSS/chrome paralelo: preferir `MetricStrip`, `MetricKpiCard`, `StatusBadge`, `StateBanner`, `ActionButton`/link do `@delpi/plugin-ui/index` conforme catálogo aplicável. Exibir a mesma árvore lógico-semântica em temas claro e escuro.
- Ao clicar, preservar competência, unidade autorizada e histórico navegável; filtros contextuais devem ser visíveis e removíveis, nunca “mágicos”.

### 10.4 Estados completos do indicador

| Estado | Valor/feedback | Ação |
|---|---|---|
| Loading | Skeleton e rótulo preservado | Desabilitar drilldown até resposta válida |
| Count=0 validado | `0` acompanhado de “Nenhum item identificado nesta fonte/recorte” | Pode abrir lista vazia autêntica |
| Count positivo validado | Número e subtipo/contexto; descrever origem/freshness quando material | Drilldown ativo se suportado |
| Fonte parcial | “Parcial” + número somente se escopo da contagem conhecido e explicitamente rotulado | Drilldown só nos dados válidos, alerta de cobertura |
| Fonte indisponível | `Indisponível`, jamais `0` | Link de diagnóstico ou retry, não abrir lista inventada |
| Sem permissão de leitura | “Sem acesso” ou bloco omitido conforme contrato de exposição | Não revelar contagem de recurso fora do scope |
| Erro de rede | Erro tipado + `Tentar novamente`; seleção mantida | Retry de leitura, não mutação |
| Competência trocada | Descartar números anteriores; loading com novo contexto | Não apresentar dados da competência antiga |

### 10.5 Critérios de aceite visual e contrato pendente

- RQ/AC relacionados: P1 `RQ-P1-02/03/04` (eixos, blockers e fonte indisponível), P2 (documentos/validação) e P3/P4 (conciliação e pendências); cruzar IDs exatos e DTOs no inventário antes do GO.
- Cada cartão possui título, explicação, valor semântico, origem quando necessária, estado de dado, interação de drilldown e foco visível.
- Números de exemplo do wireframe não são evidência de fechamento real.
- Não criar endpoint `/metrics` novo por conveniência sem examinar producers existentes.
- **`D-FM05-01 = A / PO_APPROVED (26/10/2026)`**: exatamente três cartões, nesta ordem: **Bloqueios, Divergências e Documentos a tratar**. Não adicionar cartão Pendências nesta faixa.
- `D-FM05-02` **PENDING_OWNER_CONTRACT**: critérios exatos de contagem e drilldown, sem inventar dado/entidade.

**Próximo review:** demonstrar os três cartões e seus estados ao PO. Após aprovação da hierarquia, detalhar FM-06 (navegação/abas), preservando a autonomia dos owners P2/P3/P4/P5.


## 11. Aprovação PO de FM-05 e detalhamento inicial FM-06 — Navegação da bancada

**Data:** 26/10/2026. **Decisão explícita do PO:** “opção A e esses indicadores são clicaveis para levar a pagina de referencia”.

### 11.1 Decisão visual fechada: D-FM05-01=A + D-FM05-03=CLICKABLE

**PO_APPROVED / DESIGN:** três indicadores de atenção **Bloqueios → Divergências → Documentos a tratar**, nessa ordem, e **cada cartão é inteiramente clicável** para direcionar o usuário à visão/página de referência no Fechamento Mensal. **Destino conceitual aprovado**, sem inferir path do router ainda não inventariado:

| Card | Destino funcional aprovado | Filtro/contexto de entrada | Owner |
|---|---|---|---|
| Bloqueios | **Visão geral → seção de bloqueios** (ou detalhe canônico de blockers após inventário) | competência/escopo corrente, bloqueios materiais | P1 compondo fontes P2/P3/P5 |
| Divergências | **Visão Divergências** | competência corrente, itens divergentes, origem explícita | P3/P4 conforme evento |
| Documentos a tratar | **Visão Documentos** | competência corrente, itens que exigem tratamento | P2 |

**Contrato de interação obrigatório:** cartão inteiro com superfície clicável, cursor/hover e foco visível, `Enter` e `Space` conforme semântica do componente; não envolver link dentro de botão nem gerar dupla ação. Link semântico de navegação será preferido se suportado pelo kit/router. Nome acessível explicativo (“Ver divergências da competência MM/AAAA”). Manter o contexto da competência e unidade autorizada, aplicar filtro inicial visível e removível; botão voltar deve preservar seleção e scroll quando o router permitir. Não criar URLs, rotas, contagens ou endpoints antes do inventário. Se fonte indisponível, o cartão não é um atalho para lista fictícia; mostrar indisponibilidade/retry e explicar o bloqueio.

**Limites:** clicar **navega**, não altera a competência, não cria documento, não aprova evidência, não resolve pendência e não executa ACT. Contagens exatas e agregação permanecem `D-FM05-02=PENDING_OWNER_CONTRACT`. A aprovação do PO não autoriza implementação.

### 11.2 FM-06 — Wireframe V0.5 inicial: cinco visões da bancada

**Estado:** `TARGET / DESIGN_PROPOSAL / PENDING_PO_DETAIL_REVIEW`. A arquitetura visual de cinco visões já foi aceita no V0.2; agora detalha-se o comportamento.

```text
[Bloqueios: clique → Visão geral/Blockers]
[Divergências: clique → Divergências com filtro]
[Documentos: clique → Documentos com filtro]
────────────────────────────────────────────────────────────────────
[Visão geral] [Divergências] [Documentos] [Pendências] [Revisão]
                         linha/indicador de aba ativa
────────────────────────────────────────────────────────────────────
[Filtros do contexto atual + estado da fonte]
[Conteúdo específico da visão, com lista e detalhe quando aplicável]
```

| Visão | Propósito UX | Origem | Comportamento de entrada |
|---|---|---|---|
| Visão geral | síntese, blockers, eixos Estoque/Documentos/Pacote e trabalho prioritário | P1 composição | entrada padrão da bancada, sem ocultar blockers materiais |
| Divergências | investigar diferenças/ocorrências com fonte e encaminhamento | P3/P4 | filtro “divergentes” vindo do cartão, quando suportado |
| Documentos | localizar documentos a enviar/validar/substituir e inspecionar versões | P2 | filtro “a tratar” vindo do cartão, quando suportado |
| Pendências | acompanhar solicitações/ocorrências, owner, estado e histórico | P4 | filtro por escopo/estado próprio |
| Revisão | pacote, destinatários, decisões humanas e esclarecimentos | P5 | preservar decisões/segregação/versões |

**Comportamento proposto:** uma aba ativa por vez; trocar aba mantém competência e contexto de unidade, mas não reutiliza filtros incompatíveis silenciosamente; aba ativa indicada por texto/contraste/traço, não apenas cor. Suportar deep links e botão Voltar depois de revisar o router real. Desktop: navegação horizontal compacta; mobile: faixa acessível de abas (rolagem horizontal do controle sem perder labels), conteúdo em lista→detalhe. Foco do teclado e orientação do leitor de tela devem anunciar aba ativa/contagem real quando disponível; evitar troca de aba disparando escrita. `@delpi/plugin-ui` first e Help sincronizada.

**Decisões ainda abertas para revisão do PO e inventário técnico:**
- `D-FM06-01`: usar abas dentro da página operacional (recomendação) versus destinos de subpáginas com navegação equivalente; o usuário aprovou a arquitetura visual de cinco visões, não o contrato de rotas.
- `D-FM06-02`: URL/deep links e regras de retorno — `TO_INVENTORY` do router MFE atual.
- `D-FM06-03`: indicadores levam a visão de referência e destacam filtro; títulos e filtros finais dependem dos read models.
- `D-FM06-04`: quando alguma visão não tiver producer real, mostrar estado honesto de indisponibilidade ou navegação à página legada autorizada, nunca dummy data.

**Próxima revisão no chat:** apresentar as cinco abas interativas e pedir aprovação do comportamento interno, sem confundir com GO de implementação.


## 12. Esclarecimento de escopo — Pendências P4 e Revisão P5 não se limitam a documentos

**Data:** 26/10/2026. **Origem:** questionamento do PO durante revisão do wireframe FM-06: “pendecias e revisão não se ferem exclusivamente a documentos, ou estou erraod?”. **Resultado:** esclarecimento documental ancorado nos contratos canônicos [P4 doc 11](./11-p4-classificacoes-e-pendencias.md) e [P5 doc 37](./37-p5-submissao-e-revisao-no-portal.md). **Classificação:** `PROVEN` no contrato TARGET; não comprova paridade do runtime de produção.

### 12.1 Separação semântica obrigatória

| Visão | Objeto central | Dados e ações relevantes | Limite |
|---|---|---|---|
| Documentos — P2 | checklist, itens, evidências e versões | upload, leitura, validação, rejeição/substituição, histórico, conforme capability | documento anexado **não** é automaticamente validado; item EXPECTED não é evidência entregue |
| Pendências — P4 | ocorrência de fechamento e classificação/centro de custo | status `OPEN/IN_ANALYSIS/WAITING_EXTERNAL/RESOLVED/DISMISSED`, origem, fila, owner, `pending_since`, classificação e sugestão explicativa, confirmação humana quando autorizada, histórico | pode ter documentos/evidências, mas **não é uma lista de documentos**; não grava correção no ERP V1; não inventar SLA/atraso |
| Revisão — P5 | pacote/versionamento, recipient e decisão humana de análise | finalizar pacote, submeter para revisão no Portal, acompanhar reviewers, esclarecimentos, resultado por área e versão, histórico | revisão não é só aprovar anexos; `FINALIZE != SUBMIT != REVIEW != MONTHLY_CLOSING_COMPLETED` |

**P4** é owner do estado próprio de pendências e da confirmação humana de classificação no contexto do fechamento; regra upstream/CC continua em seu owner, effective permissions no Core, e sugestão da IA não significa decisão. Evidências documentais são contexto auxiliar quando relacionadas.

**P5** é owner da PackageVersion, recipients, submissão, decisões humanas de áreas obrigatórias e esclarecimentos. Uma versão finalizada pode ser submetida e disponibilizada aos revisores na Minha DELPI; o e-mail é notificação, nunca transporte do pacote. Conclusão mensal C2 exige aceites humanos válidos na versão vigente, áreas obrigatórias, pacotes aplicáveis submetidos, sem esclarecimentos abertos ou rejeição terminal, conforme doc 37. O pacote pode referenciar documentos de P2 e o status de outros eixos, mas não absorve as regras de P2/P3/P4.

### 12.2 Consequência para FM-06 e texto de ajuda

Atualizar as descrições visuais de abas para evitar ambiguidades:
- **Pendências:** “Acompanhe ocorrências, classificações, responsáveis e resoluções do fechamento.”
- **Revisão:** “Prepare e envie pacotes para análise, acompanhe revisores, decisões e esclarecimentos.”
- **Documentos:** “Consulte e trate evidências, anexos, versões e validações documentais.”
- **Divergências:** “Investigue diferenças e inconsistências com sua origem e contexto.”
- **Visão geral:** “Acompanhe eixos, bloqueios e o que precisa de atenção.”

**Estados visuais, lista e detalhe são por owner**: P4 exibe fila/assignee/histórico e ações permitidas; P5 exibe pacotes/recipients/versionamento/decisões; P2 exibe checklist/evidências. Não fundir “pendência”, “divergência”, “documento” e “revisão” em uma única entidade, nem representar cada pendência como documento pendente. Deep links e contratos continuam `TO_INVENTORY` antes de implementação.

**Estado da decisão:** `CLARIFICATION_RECORDED / FM-06_VISUAL_DETAIL_PENDING_PO`. Não altera a aprovação prévia da estrutura de cinco visões ou dos três indicadores clicáveis FM-05.


## 13. Rebaseline de UX pela jornada real: documentos compartilhados + relatórios TOTVS (proposta V0.6)

**Data:** 2026-10-26. **Origem:** feedback direto do PO durante revisão da FM-06. **Estado:** `PRODUCT_DIRECTION_RECORDED / DESIGN_V0.6_PROPOSED / DECISION_REQUIRED_ON_TAB_STRUCTURE`. Esta proposta **supersede como desenho proposto** a distribuição de cinco abas da V0.5, **sem revogar decisões previamente aprovadas** sobre seletor de competências e três cartões clicáveis. A anterior organização não deve ser implementada automaticamente.

### 13.1 Necessidade expressa pelo PO

- A pessoa que **entrega os documentos** (exemplo citado pelo PO: Joyce) precisa de uma lista padronizada de entregáveis obrigatórios e condicionais, incluindo extratos bancários e outras evidências, para enviar e acompanhar o tratamento.
- A pessoa de **Contabilidade/DRE** precisa consultar os documentos recebidos e interagir com sua análise, **sem ter autorização para anexar documentos** nesse fluxo proposto.
- Ambas visualizam no **mesmo local, por documento/item e competência**, estado, observações, solicitações, justificativas e histórico de interação.
- A Controladoria também precisa de uma **bancada separada de relatórios TOTVS**, reproduzidos somente onde houver contrato/source/paridade comprovados, com regras e divergências rastreáveis aos ciclos 1–2 e ao AS-IS. Não confundir catálogo de relatórios com relatório homologado.

**Cuidados com autoridade:** o PO descreveu duas responsabilidades funcionais. Não criar permissão por papel, página, botão, CRUD, empresa ou filial. As únicas capabilities globais permanecem `controllership-finance.access` e `controllership-finance.manage`. Se a atribuição de “anexar” vs “analisar” não estiver expressa no contrato vigente P2, a solução de authorization/ownership por recurso e regra de negócio deve voltar como `DECISION_REQUIRED`, não ser implementada por hardcode de identidade ou perfil “DRE”.

### 13.2 Nova arquitetura de informação para validação

**Recomendação:** começar com duas bancadas principais do fluxo real e deixar status/revisão em áreas semanticamente distintas:

```text
FECHAMENTO MENSAL
[Competência existente/autorizada ▼] [Contexto] [Status/freshness]
[Bloqueios] [Divergências] [Documentos a tratar]  ← os três cards clicáveis aprovados
[Visão geral] [Documentos e interações] [Relatórios e divergências] [Revisão do fechamento]
  ├─ Visão geral — bloqueios, três eixos e próximos passos (P1)
  ├─ Documentos e interações — checklist P2 e colaboração contextual
  ├─ Relatórios e divergências — biblioteca R01–R15 + execução/leitura verificada
  │                            + comparação/regras + divergências rastreáveis (P3 e owners)
  └─ Revisão do fechamento — pacotes/versionamento/aceites/esclarecimentos (P5)
Pendências P4 — possíveis filtros/fila transversais dentro da Visão geral e das
bancadas com owner e deep link; sua posição como aba separada segue em discussão.
```

**Não é aprovação para remover a aba Pendências, nem para fundir semanticamente P4 em P2/P3.** P4 segue owner de ocorrências/classificações/CC, inclusive pendências não documentais. Definir exposição como aba própria vs worklist transversal exige PO e inventário de contratos. Reutilizar `@delpi/plugin-ui`; manter páginas comuns do shell.

### 13.3 Wireframe da bancada A — Documentos e interações

```text
DOCUMENTOS E INTERAÇÕES   Competência MM/AAAA   [origem/freshness]
[Todos] [Falta enviar] [Aguardando análise] [Ajustes solicitados] [Aceitos]
[Grupo ▼] [Origem ▼] [Destinatário ▼] [Buscar documento]
┌───────────────────────────────────────┬─────────────────────────────────────┐
│ LISTAGEM DO CHECKLIST REAL            │ DETALHE DO ITEM                    │
│ Documento / requisito                 │ Identificação / requirement / owner│
│ Quem entrega / a quem se destina      │ Arquivos, versões, preview         │
│ Estado documental / última interação  │ Análise / esclarecimentos          │
│ [abrir item]                          │ Histórico compartilhado / timeline│
│ ...                                   │ Ações ELEGÍVEIS POR CONTEXTO       │
└───────────────────────────────────────┴─────────────────────────────────────┘
```

**Modos de uso propostos**, não novos permission codes:
- **Entrega:** usuário com elegibilidade de entrega para aquele item/competência visualiza lista, faz upload/substituição quando permitido e acompanha solicitações de ajuste; upload = `ATTACHED`, **não** `ACCEPTED`.
- **Consulta/análise contábil:** outro usuário com resource scope/elegibilidade pode ler documentos/versões, registrar análise/esclarecimento **somente se houver operação e autorização contratadas**, sem ação de anexar/substituir no fluxo definido pelo PO.
- **Ambos:** compartilham contexto e histórico auditável da mesma evidência/item, com mensagens/solicitações exibidas de acordo com regras de visibilidade e segurança. **Não criar chat paralelo nem banco de comentários** antes de inventariar P2/P5 e Sala de interação/notifications; integração e ownership de “interação documental” são `DECISION_REQUIRED`.
- **Listagem padrão:** partir do snapshot P2 da competência, não montar lista manual nova; 53 `EXPECTED` no registro P6-MIN+P2-READ são evidência histórica de seed/snapshot, não garantem homologação de todos os itens atuais ou completa presença dos anexos.
- **Sem sobreposição indevida:** o ato de validar uma evidência P2 difere de revisar pacote P5; revisor Contabilidade/DRE pode ter atribuições distintas em ambos os contextos. Não presumir que todo reviewer P5 valida evidência P2.

### 13.4 Wireframe da bancada B — Relatórios e divergências TOTVS

```text
RELATÓRIOS E DIVERGÊNCIAS     Competência / período / empresa / filial autorizada
[Financeiro] [Estoque e custos] [Fiscal/Contábil] [Outros/Externos]
[Busca relatório] [Somente fontes disponíveis] [Ver pendências de paridade]
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ CATÁLOGO R01–R15 / FAMÍLIAS         │ RELATÓRIO SELECIONADO                │
│ Nome, finalidade, origem/rotina      │ Parâmetros/filtros/competência       │
│ Disponibilidade da fonte            │ Dados tabulares, totais, agrupamento│
│ Equivalência validada? G1..G6       │ Regras de verificação e provenance  │
│ R01 Baixas a pagar                  │ Divergências por grupo/linha        │
│ R02 Baixas a receber                │ Comparações e documentos associados │
│ R03 P7 / Bloco H                    │ Detalhe, drilldown, histórico       │
│ ... R15                             │ Export somente após contrato        │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

**Fonte:** [46 — inventário R01–R15](./46-t01-report-source-inventory-v1.md) e [47 — tracker de auditoria](./47-t01-report-column-audit-tracker-v1.md). O inventário distingue relatórios, famílias/rotinas e documentos externos, portanto não apresentar R01–R15 como quinze PDFs equivalentes nem exigir renderização SQL de extrato bancário externo. Exemplos: R01/R02 baixas, R03 P7, R04 consumo por OP (MATR860), R05 entradas/saídas, R06/07 Kardex, R08 H02, R09 faturamento × MOD, R10/11 notas, R12 rotinas de custo, R13 extratos externos, R14 importação mista, R15 cutoff. `MATR860 != MATR460/P7`.

**Evidência datada no README:** Ciclo 2 registra coleta `47/60`, auditoria `55/90` e **`G6=0/15`**; o tracker 47 possui múltiplos G5 PASS em revisões técnicas, mas **nenhum item pode ser declarado oficialmente aceito pela Controladoria apenas por isso**. Os blocos de documentação de R01/R02 e runtime P1/P2 são datados; qualquer afirmação “rota já existe e é equivalente” exige HEAD, producer, resposta e paridade verificados por relatório.

**Tratamento de divergências:** exibir diferença, fórmula/regra, unidade, competência, fonte/versão, campos originários, impacto e owner com evidência; P3 exige paridade monetária exata `Entradas/Saídas − P7 − H02 = R$ 0,00` após critérios corretos de cutoff/revalidação. Não inferir divergência de dado parcial/nulo, nem aplicar tolerância implícita. Sem fonte equivalente, mostrar `PARIDADE_PENDENTE` / `UNAVAILABLE_SOURCE` com diagnóstico, nunca valor inventado ou “tudo conciliado”.

### 13.5 Interações entre as duas bancadas

Um relatório divergente pode **referenciar** o item/documento relacionado e vice-versa, **somente se os identificadores de vínculo e permissions estiverem contratados**. Navegação e leitura de evidência não significam edição da origem. Um comentário/solicitação de Contabilidade deve ser visível ao entregador quando pertinente e autorizado, com actor/timestamp/history; definir tecnologia/owner de colaboração por inventário e decisão, não por criação livre de tabela.

### 13.6 Decisões de produto pendentes

| ID | Escolha material | Opções | Recomendação e estado |
|---|---|---|---|
| D-FM06-REBASE-01 | Navegação principal | A: Visão geral / Documentos e interações / Relatórios e divergências / Revisão, com Pendências P4 em fila contextual; B: manter Pendências como quinta aba independente | **DECISION_REQUIRED**; recomendar testar A em wireframe, preservando P4 como owner distinto |
| D-DOC-AUTHZ-01 | Quem anexa, analisa, solicita correção e vê histórico | Vincular elegibilidade/assignment ao item e recurso pela BFF e Core; outra alternativa exige governança separada | **DECISION_REQUIRED** de boundary/contrato; nenhuma nova permission code |
| D-DOC-COLLAB-01 | Modelo de interação documental | Reuso de comentários/clarifications/notificações existentes vs novo contrato próprio | **TO_INVENTORY → DECISION_REQUIRED**, não criar automaticamente chat ou tabela |
| D-REPORT-01 | Quais relatórios realmente estão reproduzidos | Inventário API producer/consumer + HEAD + equivalência por R-ID | **TO_INVENTORY**; sem aprovação automática de todos os quinze |
| D-REPORT-02 | Dashboard de divergências | Agregar somente reads derivados e rules com source e ownership | **PENDING OWNER/PARITY**, sem nova regra em frontend |

### 13.7 Próximo ciclo de design

Priorizar **Documentos e interações** no próximo wireframe porque o PO descreveu claramente duas jornadas complementares. Em seguida **Relatórios e divergências** por família (começando por R01/R02 ou grupo acordado), conferindo o tracker físico 47. Desenhar versões desktop/mobile/sem acesso/partial/erro, mapeando checklist, estados e ações com o owner. Manter revisão P5 autônoma e preservar o fluxo de pendências P4 até decisão.

**Gates:** `USER_NEED=PROVEN_BY_PO`; `UX_REBASELINE=TARGET`; `DESIGN_APPROVAL=PENDING`; `REPORT_REPRODUCTION_ALL=NOT_PROVEN`; `RUNTIME_GO=NO`.
