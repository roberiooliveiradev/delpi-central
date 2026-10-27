# 112 — Design visual colaborativo: Fechamento mensal (wireframes por página)

> **DECISÃO PO — UX DE CADASTRO DOCUMENTAL (26/10/2026):** criar e editar **configurações dos tipos de documentos/PDFs exigidos à DRE** deve usar **página dedicada de Administração**, e NÃO modal. Preservar listagem, botão Adicionar, rota/formulário de criação, rota/formulário de edição, retorno à listagem com contexto e foco, validação, histórico, vigência inicial/final/excepcional, responsividade e Help. Acesso à configuração apenas por `controllership-finance.manage` (ou Super Admin com autoridade efetiva); backend autoriza fail-closed. Esta página administrativa NÃO é uma quarta aba do Fechamento mensal; uploads/anexos operacionais continuam dentro da aba Documentos e interações. **TARGET**, não implementação vigente; inventariar modal atual, router, componentes `@delpi/plugin-ui`, contratos, consumidores e gates antes de executar. Preservar modal legado até substituição validada e depreciação expressamente autorizada.

> **PLANO CANÔNICO DE CONTINUIDADE — 26/10/2026:** [Doc 113 — fluxo Controladoria → DRE, abertura contextual e vigência documental](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md). Reúne as decisões do PO para o Devin: consulta do mês sem abertura, abertura formal contextual por `.access`, operação interna com relatórios/divergências, catálogo de PDFs DRE gerido por `.manage` com vigência inicial/final/excepcional, entrega DRE restrita e tratamento de versões. TARGET ≠ runtime, gates preservados, limpeza de legado em fase posterior.

> **DECISÃO VIGENTE DO PO — 26/10/2026 — CORREÇÃO DO FLUXO DE COMPETÊNCIA (TARGET; RUNTIME NÃO ALTERADO).** O usuário entra em `/apps/controllership-finance/closing/monthly-closing`, seleciona um **mês de referência** autorizado e acessa as **três abas aprovadas**: **Visão geral**, **Documentos e interações**, **Relatórios e divergências**. A **consulta** de visão geral, fontes/relatórios calculados e catálogo aplicável independe de competência formalmente aberta, checklist publicado ou documentos anexados. Sem documentos = lista vazia honesta, não bloqueio. O cadastro dos **tipos/entregáveis exigidos** é **global/versionado por vigência a partir de uma competência**, não um recadastro mensal; adições e exclusões prospectivas não alteram fechamentos já finalizados. A anexação/validação/versionamento das **evidências** é vinculada ao mês e sujeita a autorização. Selecionar mês **não é** `openCompetence`, criar snapshot ou concluir P5. Preservar histórico de fechamento, `ATTACHED != VALIDATED`, limites dos contexts, duas permissions existentes e Ajuda. **Execução atual diverge (EXECUTION_DRIFT):** `listCompetences()` lista apenas competências formalmente abertas; o relatório read-only CF-PROC0072-COMPETENCE-DIAG-001 relatou produção com zero competências e template v1 DRAFT, mas SQL e smoke autenticado ainda não foram revalidados independentemente. Não criar dataset fictício, não mudar contrato silenciosamente, não publicar template nem abrir período para contornar a tela vazia. **Pendente de gate técnico:** decidir owner/API de contexto mensal independente de abertura, derivação temporal da lista, momento de congelamento de snapshots para competências em andamento, elegibilidade de cadastro/anexo em mês sem abertura e compatibilidade P2/P5. Conteúdo anterior que apresente abertura formal como pré-requisito de **consulta** deve ser lido como histórico/AS-IS substituído por esta decisão; fluxos formais ainda exigem reconciliação, não foram revogados automaticamente.


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


## 14. Wireframe 02 — Documentos e interações / bancada compartilhada V0.7

**Data:** 26/10/2026. **Estado:** `TARGET / VISUAL_DRAFT / PENDING_PO_APPROVAL`. A proposta atende à jornada explicitada pelo PO: uma pessoa entrega o arquivo, outra pessoa da Contabilidade/DRE o consulta/analisa sem enviar arquivos, ambas acompanham a mesma trilha auditável. Não confirma ainda o contrato de colaboração, elegibilidade, novas rotas ou runtime de um único workspace.

### 14.1 Modelo de trabalho, componentes e hierarquia

```text
FECHAMENTO MENSAL  [competência existente/autorizada] [escopo] [situação]
[Visão geral] [Documentos e interações]* [Relatórios e divergências] [Revisão]
Documentos e interações                                [Ajuda] [Atualizar]
Entregáveis e evidências vinculados ao fechamento desta competência

[Todos] [Falta enviar] [Em análise] [Ajustes solicitados] [Aceitos]
[Busca por documento] [Grupo/área] [Origem] [Estado] [Responsável?]
┌──────────────────────────────────────┬────────────────────────────────────────┐
│ LISTA DO CHECKLIST / Fila             │ DETALHE DO ITEM SELECIONADO              │
│ Documento | Requisito | Estado        │ Título + requisito + origem + recipient  │
│ Responsável | Última interação       │ Arquivos: versão, status, preview        │
│ ... seleção preservada               │ Avaliação documental (escopo real P2)    │
│ ... paginação                        │ Interações auditáveis contextualizadas   │
│                                      │ Linha do tempo de eventos + solicitações │
│                                      │ Ações elegíveis (entrega/análise)        │
└──────────────────────────────────────┴────────────────────────────────────────┘
* visão/rota final ainda depende de D-FM06-REBASE-01.
```

**Prioridade visual:** preservar checklist como fonte única do rol de documentos; estado do item não é substituído pelo status de um comentário. Desktop `ResizableColumns`, com aproximadamente 40% fila / 60% detalhe conforme componente existente; detalhe não é modal. Mobile: lista `DataRecordCard` → detalhe full width → `BackLink`.

### 14.2 Wireframe detalhado — listagem única

**Linha do item:** título de documento, exigência `REQUIRED/CONDITIONAL/OPTIONAL`, grupo/área, origem, responsável/provider se disponível, situação de evidência (não confundir `EXPECTED` com `ATTACHED`), última atividade/freshness do owner e indicador de solicitação de ajuste se houver contrato. Os exemplos “Extrato bancário”, “Comprovante de aplicação” e “Documento fiscal” são placeholders de layout; os nomes físicos provêm do snapshot P2 real.

**Filtros de UI propostos:** Todos; Falta enviar; Em análise; Ajustes solicitados; Aceitos; busca por nome/código; grupo/origem/destinatário; responsáveis somente quando o DTO suportar. Os chips traduzem estados reais do P2 (não criar enum livre). O filtro “Ajustes solicitados” exige correlação auditável com decisão de rejeição/clarification; sem contrato, marcar indisponível e não simular.

**Uma fila compartilhada:** mesmos identificadores e versões dentro do escopo de cada usuário; visibilidade e ações podem diferir pelo resource scope, mas não duplicar documento nem criar uma tabela “documentos Contabilidade”.

### 14.3 Wireframe detalhado — detalhe do documento

```text
[Extrato bancário • exemplo]        [REQUIRED] [Estado da evidência]
Origem / área destinatária / responsabilidade / regra de satisfação
─────────────────────────────────────────────────────────
ARQUIVOS E VERSÕES
[V1 • extrato_setembro.pdf • ATTACHED]   [Ver] [Baixar autorizado]
[Histórico V0/V1 ...]                    [Anexar/Substituir se elegível]
─────────────────────────────────────────────────────────
ANÁLISE DOCUMENTAL
[Estado por anexo ou WHOLE_SET] [Validador] [Motivo estruturado]
[Aceitar/Rejeitar/Reverter apenas se backend autorizar]
─────────────────────────────────────────────────────────
INTERAÇÕES E ACOMPANHAMENTO
[Atividade 1 • autor • data • tipo • vínculo a versão/decisão]
[Atividade 2 • solicitação ou resposta • estado]
[Responder/Solicitar ajuste SOMENTE se operação contratada e autorizada]
─────────────────────────────────────────────────────────
HISTÓRICO AUDITÁVEL
[snapshot → upload → análise → rejeição → nova versão → decisão]
```

**Nota importante:** interação documental é um conceito funcional aprovado como necessidade; **não** inferir que existe API de comentário bidirecional. O histórico canônico de eventos de P2 pode ser ponto inicial; comentários livres, menções, threads, solicitações independentes de rejeição, avisos e SLA exigem contrato e decisão explícitos.

### 14.4 Duas jornadas no mesmo detalhe

| Tarefa | Entregador do documento (exemplo PO: Joyce) | Usuário de Contabilidade/DRE |
|---|---|---|
| Ver lista e arquivos | READ conforme `access` efetivo, escopo e resource rule | Mesmo checklist/versão, READ no próprio escopo |
| Enviar arquivo | **Permitido somente após elegibilidade de entrega por item/regra P2** | **Não exibir upload/substituição** no fluxo solicitado pelo PO; exigir bloqueio server-side |
| Substituir rejeitado | Elegibilidade da versão/competência, com OCC e histórico | Não permitido nesse modo de trabalho |
| Consultar análise | Resultado, motivo, responsável, versão e histórico | Resultado, versão, escopo de análise e histórico |
| Analisar documento | Apenas se designado como validador e contrato autorizar; não derivar proibição geral pelo nome “Joyce” | Ações de análise/validação somente se designado e backend autorizar; “pode visualizar” **não** equivale automaticamente a “pode aceitar/rejeitar” |
| Pedir complemento / responder | Receber/responder conforme operação aprovada e escopo | Solicitar ajuste/responder conforme operação aprovada e escopo |
| Histórico | Mesmo histórico auditável autorizado, sem misturar versões | Mesmo histórico auditável autorizado, sem sobrescrever decisão |

**Exemplo de status compartilhado:** entregador anexa V1 → evidência `ATTACHED`; analista autorizado identifica problema e rejeita com motivo estruturado → registro `REJECTED` preservado; entregador substitui, cria V2 e a nova composição segue regra de validação. Isto é demonstração visual de semântica P2, **não teste E2E executado**.

### 14.5 Estados UX e segurança

- Loading por lista/detalhe com skeleton; competência e filtros preservados.
- `EXPECTED` ainda não tem arquivo; **não** exibir preview fantasma.
- `ATTACHED` não equivale a `ACCEPTED`; decisões PER_ATTACHMENT e WHOLE_SET diferentes.
- Item sem acesso: ocultar informação de recurso não autorizado; BFF reautoriza inclusive download/preview.
- Fonte externa indisponível: `UNAVAILABLE/PARTIAL`, sem “Nenhum documento” falso.
- Solicitação pendente e rejeição devem ter motivo e actor/timestamp reais; não inventar severidade ou SLA.
- Mudança de competência descarta detalhe/versão antiga; deep link e retorno preservam contexto autorizado.
- P2 valida evidência; P5 revisa pacote. Estados e aprovação de ambos não são intercambiáveis.
- A mesma árvore suporta tema claro/escuro; teclado/foco, rótulos PT-BR, animações discretas, Help contextual atualizado.

### 14.6 Componentes do kit preferenciais

`createDashboardPageHero`, `createDashboardPagePath`, `createDashboardFiltersKit`, `DataTableSection`, `DataRecordCard`, `ResizableColumns`, `StatusBadge`, `AttachmentFileList`, `AttachmentPreviewStrip`, `FileDropzone`, `Timeline`, `StateBanner`, `EmptyState`, `LoadingState`, `ConfirmModalPanel`, `FloatingNoticeStack`, `BackLink`. Não criar controles duplicados; mapear exports atuais no HEAD antes de brief de implementação.

### 14.7 RQ/AC e decisões materiais

- **PROVEN no contrato P2 doc 09 e ledger 23:** snapshot/versionamento, entrega não valida, rejeição motivada, substituição com histórico, validação por anexo ou conjunto, AuthZ backend.
- **REPORTADO em execução, ainda requer verificação no HEAD/runtime:** upload/list/get/download/replace/cancel e validação P2 conforme adendos doc 09/100/103.
- **D-DOC-AUTHZ-01 = DECISION_REQUIRED:** como o BFF resolve elegibilidade para anexar vs analisar por item/recipiente/assignment, mantendo apenas `access` e `manage`; não criar terceira permission.
- **D-DOC-COLLAB-01 = DECISION_REQUIRED:** mecanismo de mensagem/solicitação/resposta contextual com históricos; escolher reuso de eventos/clarifications/notifications existentes após inventário, ou novo contrato governado. Sem SQL/schema por conveniência.
- **D-DOC-ENTRY-01 = PENDING_PO_VISUAL:** a listagem deve abrir primeiro, com painel de detalhe do item selecionado, sem modal de documento; recomendação: sim.
- **D-DOC-UX-02 = PENDING_PO_VISUAL:** incluir no detalhe um bloco “Interações” separado de “Histórico”, ou uma timeline única com filtros; recomendação: “Interações e acompanhamento” como bloco visual e timeline auditável abaixo, distinguindo conversa de evento sistêmico.
- **D-FM06-REBASE-01** segue pendente quanto às quatro vs cinco abas. Não inferir aceite porque o PO solicitou prosseguir ao próximo wireframe.

### 14.8 Próximo review

Demonstrar versão interativa da listagem e do detalhe no chat; confirmar distribuição dos blocos e o modelo de interação (um histórico compartilhado), avançando depois à bancada “Relatórios e divergências”. `DESIGN_V0.7=PENDING_PO`, `RUNTIME_GO=NO`.


## 15. Reconciliacao do Wireframe 02 com decisao anterior Contabilidade/DRE (Doc 91)

**Data:** 26/10/2026. **Origem:** PO perguntou se diferenciação de acesso já seria controlada pelo manifesto e se valeria criar página própria. **Classificação:** `PROVEN` para evidência de decisão documental anterior e manifesto HEAD; `TARGET / DECISION_REQUIRED` para nova experiência de interações. **Natureza:** documentação de arquitetura de informação, nenhuma alteração de runtime.

### 15.1 Evidência de contrato vigente

- Manifesto em `plugins/controllership-finance/controllership-finance.manifest.json` está em `schemaVersion 1.0.0` e declara exatamente **duas permissions**: `controllership-finance.access` e `controllership-finance.manage`. Rotas `/closing/checklist`, `/closing/pendencies`, `/closing/packages` usam `.access`. Uma rota de Contabilidade dedicada não foi registrada nesse manifesto.
- O [Documento 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) registra decisão expressa anterior **Opção B / PRODUCT_DIRECTION_APPROVED**: uma **página própria** dentro da Central, exclusiva da audiência Contabilidade/DRE, com consulta/download de documentos e pacotes liberados por competência histórica. O documento solicita **exceção** para terceira permission específica, ainda **não ratificada como contrato runtime**. A criação da permission/rota foi **adiada pelo PO** em §8, e não revogada.
- `controllership-finance.access/manage` continuam únicas capabilities aprovadas no baseline do projeto até gate transversal. A BFF aplica efetivas do Core **AND** recipient assignment/resource scope **AND** regra de negócio, fail-closed; UI e manifest não bastam para autorizar operação de arquivo.
- Documento 91 estabelece **DRE sem upload, validação P2, aprovação/rejeição P5 ou aceite na V1**. A Controladoria prepara, anexa e disponibiliza, com eventos separados e trilha auditada. Este boundary é diferente da atuação dos revisores P5.

### 15.2 Recomendação de composição — sem reabrir a decisão B

**Preservar a decisão prévia de produto de entrada/página específica para Contabilidade/DRE dentro do mesmo Portal**, reutilizando uma única base/snapshot e os componentes da bancada de documentos, sem criar Portal paralelo nem cópias de evidência. Proposta visual:

```text
                              MESMA COMPETENCIA / ITENS / ARQUIVOS
                                     BFF / storage / auditoria
                                      /                \
CONTROLADORIA / ENTREGA                CONTABILIDADE / DRE
Página Fechamento mensal               Página Documentos para Contabilidade
  Documentos e interações              Consulta de documentos liberados
  lista+detalhe+envio elegível         lista+detalhe+download autorizado
  relatórios e divergências            acompanhamento de interações autorizadas
  revisão P5 quando aplicável          SEM upload, SEM revisão/aceite P5 na V1
```

Ambas as páginas podem utilizar a mesma composição visual `DocumentList` + `DocumentDetail` + `AttachmentFileList` + `Timeline` do `@delpi/plugin-ui`, com affordances distintas e **AuthZ de backend, não flags confiadas pelo cliente**. A página restrita deve ser descoberta e aberta via entrada segura do Core/launcher; não conceder `.access` geral para contornar raiz protegida. O path `/closing/accounting-documents` do Doc 91 permanece candidato, não rota implementada/aprovada para runtime.

### 15.3 Mudança funcional que requer nova decisão

O Doc 91 aprovou **consulta/download apenas** e **sem aceite** para Contabilidade/DRE. O novo pedido do PO adiciona **interações bidirecionais relativas ao documento** que também devem aparecer à entregadora. Esta é a diferença material entre:
1. **Ver eventos/histórico**: leitura das evidências e decisões já auditadas; ou
2. **Escrever comentário / solicitar esclarecimento / responder**: mutação governada com ator, versão, recorte e audience, notificações, AuthZ e persistência — não autorizada automaticamente por uma capability de leitura.

**`D-DOC-COLLAB-01=DECISION_REQUIRED`** antes de prometer postagem de interações pelo usuário DRE. Investigar funções existentes em P2, P5 e Sala de Interação, e definir owner/action contract, sem confundir consulta DRE com revisor P5. Se decisão incluir escrita, resolver `read-only` versus `comment-only` de forma explícita, sem criar permission por botão/CRUD por conveniência.

**`D-DRE-ENTRY-01=DOCUMENTED_PRODUCT_DIRECTION/DEFERRED`**: manter página própria aprovada, mas sem implementação até exceção transversal formal para permissão e entrada restrita, inclusive impacto manifest/Core launcher/router/BFF/guards/testes.

**`IMPLEMENTATION_AUTHORIZED=NO`** para qualquer alteração de plugin, manifest, Core, grants, BFF, rotas, banco ou UI nesta rodada.

### 15.4 Próximo refinamento visual

No Wireframe 02, desenhar duas variantes reutilizando lista/detalhe: a) entregador autorizado, com upload e acompanhamento; b) Contabilidade, sem controles de upload/aceite, com consulta/download e histórico visível. A área de **nova interação escrita** permanece marcada `TARGET / DECISION_REQUIRED` até contrato. A decisão das quatro versus cinco abas da mesa Controladoria segue independente e ainda em revisão.


## 16. Decisão funcional do PO — acesso de Contabilidade/DRE SOMENTE a documentos anexados

**Data:** 2026-10-26. **Status:** `PRODUCT_DIRECTION_APPROVED` para separação de experiências; `TARGET / DECISION_REQUIRED` para AuthZ, menu/entrada restrita, nova capability excepcional e contrato de interação. **Evidência:** manifestação explícita do PO no chat, incluindo correção enfática: **“DRE NÃO ACESSA RELATÓRIOS, APENAS OS DOCS ANEXADOS!”**. Esta seção complementa o [Doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md), sem alterar o manifesto, o Core ou qualquer runtime. `IMPLEMENTATION_AUTHORIZED=NO`.

### 16.1 Separação funcional inequívoca

| Capacidade/superfície | Controladoria, conforme escopo e elegibilidade | Contabilidade/DRE restrito |
|---|---|---|
| Consulta de evidências anexadas e liberadas | Sim, conforme acesso autorizado | **Sim**: somente documentos efetivamente anexados/liberados ao destinatário e competência autorizados |
| Download | Autorizado por recurso/versão | **Sim**, com BFF reautorizando recurso/versão e auditando download |
| Comentar documento | Quando autorizado | **Sim**, no item/versão liberados, sob contrato de interação |
| Solicitar complemento/correção | Quando autorizado | **Sim**, sem transformar solicitação em rejeição ou aceite formal P2/P5 |
| Anexar/substituir/cancelar | Somente responsável elegível e regras P2 | **NÃO** |
| Validar/rejeitar evidência P2 | Somente validador elegível | **NÃO** |
| Pacote/aceite/revisão P5 | Conforme escopo e elegibilidade | **NÃO** na V1; consulta documental não é review de pacote |
| Relatórios TOTVS, reproduções R01–R15, conferências/paridade e divergências operacionais | Conforme autorização | **NÃO: jamais apresentar ou expor DTO/API de relatórios nesse perfil** |
| Administração/catálogos, tarefas operacionais internas, estoque/custos/baixas | Conforme acesso autorizado | **NÃO** |

**Exigência mandatória do PO:** não incluir **Relatórios e divergências** no menu, nas abas, nos cartões, na busca, nos links diretos nem em respostas BFF para o perfil de Contabilidade/DRE. Não mostrar dados de relatórios nem mesmo em agregados, contagens ou previews. A checagem é de backend por effective permissions Core AND recipient/resource scope AND business rule, fail-closed — esconder item na UI não autoriza API.

### 16.2 Duas experiências dentro do mesmo Portal, dados documentais compartilhados

```text
Minha DELPI / Portal Controladoria & Finanças
       ├─ Controladoria, escopo operacional autorizado:
       │  Fechamento mensal → Visão geral / Documentos e interações
       │                     / Relatórios e divergências / outras visões aprovadas
       └─ Contabilidade/DRE, escopo documental restrito:
          Fechamento mensal → Documentos anexados e liberados
                             [competência autorizada]
                             [lista de arquivos] [abrir] [baixar]
                             [comentário] [solicitar complemento] [histórico]
                             SEM upload; SEM relatórios TOTVS; SEM análise P3/P4;
                             SEM aprovação P2/P5; SEM administração.
```

**Uma mesma origem documental P2/P5, sem duplicar arquivo/histórico.** A vista restrita não deve exibir como arquivo disponível um item apenas `EXPECTED`: esses itens podem constar no checklist interno da Controladoria, mas **a Contabilidade visualiza apenas anexos liberados para sua audiência**, na competência/versão permitida. “Liberado” exige estado/ato verificável definido pelo owner, não implica `PACKAGE_SUBMITTED_FOR_REVIEW` por conveniência.

### 16.3 Interações aprovadas e notificação — regra de audiência a fechar

O PO determinou que Contabilidade/DRE pode **comentar e solicitar complementos**, e essas interações geram **mensagem/notificação** para as demais pessoas com acesso ao Portal, **excluindo a audiência Contabilidade/DRE**. Este requisito é direção de produto, **não autorização para notificação irrestrita a todos os usuários com `.access`**.

**Decisão contratual pendente:** recipients efetivos devem ser resolvidos por Core/ownership e pelas competências/itens/recipients autorizados. Não enviar conteúdo de documento a usuários sem vínculo legítimo, não notificar quem não pode visualizar o item, não usar lista de usuários arbitrária por setor, não conceder acesso por notificação. Registrar quem recebeu e o resultado da entrega, auditando sem expor dados sensíveis. Usar capability de notificações da Minha DELPI já existente; reusar eventos/clarifications P2/P5 somente se seus contratos forem adequados. O comentário é ação WRITE governada, distinta de download/consulta e de validação P2/revisão P5.

**Diferença importante:** o histórico pode ser compartilhado dentro do mesmo documento autorizado, mas os destinatários da **notificação** podem ser subconjunto do grupo de leitores. A Contabilidade tem permissão de escrever comentários/solicitações no contrato de interação, sem permissão para upload nem para relatórios.

### 16.4 Reconciliação de manifesto e proteção de entrada

O manifesto atual `plugins/controllership-finance/controllership-finance.manifest.json` declara **apenas `controllership-finance.access` e `controllership-finance.manage`**. O [Doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) registra aprovação funcional prévia de **página/permission específica**, mas a exception ao freeze e a implementação ficaram adiadas. **Não alterar** o manifesto por esse wireframe. A exigência de que a área restrita apareça como **Fechamento mensal** para a audiência de Contabilidade precisa de gate de Core/launcher, guard, BFF, contratos e testes, inclusive negando rotas e endpoints TOTVS mesmo que URLs sejam conhecidas.

### 16.5 Wireframe restrito — proposta

```text
[TOPBAR DO PORTAL AUTORIZADA]
Fechamento mensal                             [? Ajuda]
Documentos disponibilizados para Contabilidade
[Competência existente/autorizada ▼] [Última atualização]
[Buscar documento] [Tipo/área] [Somente arquivos liberados]
┌────────────────────────────────┬────────────────────────────────────┐
│ DOCUMENTOS ANEXADOS            │ DETALHE DO DOCUMENTO               │
│ Documento, versão, data, origem│ Arquivos efetivamente liberados    │
│ Situação de complemento        │ Visualização / download autorizado │
│ [Abrir]                        │ Comentários e solicitações         │
│ ...                            │ Histórico auditável               │
│                                │ [Comentar] [Solicitar complemento] │
└────────────────────────────────┴────────────────────────────────────┘
NÃO renderizar relatórios TOTVS, divergências operacionais ou botões de upload.
```

### 16.6 Pendências e decisões técnicas

- `D-DRE-ACCESS-01`: **PRODUCT_APPROVED**: acesso somente documental, sem relatórios nem outras bancadas.
- `D-DRE-DOC-01`: **PRODUCT_APPROVED**: consulta/download dos anexos liberados, comentar e solicitar complementos, sem upload/aceite.
- `D-DRE-NOTIFY-01`: **PRODUCT_DIRECTION_APPROVED**: comunicar interações para não-DRE; **DECISION_REQUIRED** para regra exata de recipients, visibilidade por item/competência, notificação e auditoria.
- `D-DRE-MANIFEST-01`: exceção de capability/rota específica no Doc 91, **DEFERRED / TRANSVERSAL_GATE_PENDING**; nenhuma permission nova, branch de menu ou BFF atualizados neste ato.
- `D-DRE-COLLAB-01`: comentário/solicitação são mutações governadas, modelo e APIs **TO_INVENTORY / DECISION_REQUIRED**.
- `IMPLEMENTATION_AUTHORIZED=NO`: design/documentação somente.

**Próximo wireframe:** detalhar somente a **página restrita de documentos anexados para Contabilidade/DRE**, sem qualquer referência visual a relatórios TOTVS. Depois validar a jornada interna de entrega da Controladoria e a visibilidade cruzada do histórico.


## 17. Wireframe 03 — Página exclusiva Fechamento mensal / Contabilidade-DRE V0.8

**Data:** 2026-10-26. **Natureza:** design/documentação exclusiva da experiência restrita Contabilidade/DRE. **Estado:** \`TARGET / DETAIL_VISUAL_DRAFT / PENDING_PO_APPROVAL\`. **Não altera** a página Controladoria, a bancada de relatórios TOTVS, permissões ou runtime.

### 17.1 Jornada e contrato de acesso

**Job:** “Quero encontrar os documentos que foram anexados e disponibilizados para minha área na competência, consultá-los/baixá-los e pedir esclarecimento ou complemento, acompanhando as respostas no mesmo item.”

- Entrada no menu: **Fechamento mensal**, com landing restrita documental para a audiência autorizada Contabilidade/DRE, sem acesso à Home ampla da Controladoria como efeito colateral.
- Listar **somente anexos efetivamente existentes, vinculados a item da competência e disponibilizados para aquele recipient/resource scope**. Ausência de anexo não vira linha com botão de download; pedido de documento não entregue depende de decisão específica (o PO pediu “apenas docs anexados”).
- O identificador de documento/item é estável; versões e decisões são rastreáveis. Download não significa aceite, validação ou conclusão.
- Usuário pode **comentar** e **solicitar complemento** de documento disponibilizado; não pode anexar/substituir, validar/rejeitar evidência P2, aceitar/rejeitar pacote P5 ou acessar relatórios TOTVS e dados de reconciliação.
- Ação permitida na UI é projeção; backend exige identity + **Core effective permission apropriada** + recipient_assignment/resource scope + business rule da competência/versão/estado, e falha fechado. Documento 91 registra a solicitação de terceira capability de consulta como exceção técnica **ainda não ratificada/implementada**, logo o manifest atual com \`.access/.manage\` **não atende sozinho** ao acesso restrito futuro. O PO não autorizou alteração do freeze neste wireframe.
- Compartilhamento de comentários/solicitações com Controladoria precisa de contrato explícito e linha do tempo auditável, sem criar chat separado. A instrução “notificar todo mundo que tem acesso ao Portal, menos DRE” depende de delimitação da audiência que pode ver a competência/documento e consentimento/segurança; não enviar detalhes indiscriminadamente.

### 17.2 Wireframe desktop — uma única página, sem abas de domínio do Portal amplo

\`\`\`text
┌────────────────────────────────────────────────────────────────────────────┐
│ PORTAL SHELL / TOPBAR PADRÃO, SOMENTE DESTINOS EFETIVAMENTE AUTORIZADOS    │
├────────────────────────────────────────────────────────────────────────────┤
│ Controladoria & Finanças  ›  Fechamento mensal                              │
│ FECHAMENTO MENSAL                                      [Ajuda] [Atualizar] │
│ Documentos disponibilizados para sua área.                                 │
│ [Competência existente/autorizada: MM/AAAA ▼]  [Área/destinatário permitido]│
│ [Atualizado em: hh:mm/fonte, ou indisponível]                               │
├────────────────────────────────────────────────────────────────────────────┤
│ [Buscar documento...] [Tipo/grupo ▼] [Situação do complemento ▼]          │
│ [N documentos liberados] [N solicitações em aberto (se houver contrato)]  │
├─────────────────────────────────┬──────────────────────────────────────────┤
│ DOCUMENTOS DISPONÍVEIS          │ DETALHE DO DOCUMENTO                     │
│ Nome / origem / versão          │ Nome, competência, arquivo(s), versão    │
│ Disponibilizado em / contexto   │ Disponibilização e destinatário         │
│ Situação de complemento         │ [Pré-visualizar*] [Baixar]               │
│ Última interação                │                                          │
│ [selecionar]                    │ INTERAÇÕES                               │
│ ...                             │ timeline com autor/data/tipo/versão      │
│ paginação                      │ [Escrever comentário]                    │
│                                 │ [Solicitar complemento]                  │
│                                 │ HISTÓRICO AUDITÁVEL                      │
│                                 │ disponibilização / downloads* / replies │
└─────────────────────────────────┴──────────────────────────────────────────┘
* somentes ações suportadas e autorizadas pelos contratos de preview/audit.
SEM upload, relatórios TOTVS, paridade, divergências operacionais, administração
ou aprovação/rejeição de P2/P5.
\`\`\`

**Layout:** cabeçalho enxuto, lista master/detail aproximadamente 40/60 com kit \`ResizableColumns\` e sem modal para detalhe principal. Destacar seleção da lista. Dividir comentários e histórico pelo tipo de evento, preservando sequência auditável. Nome “Fechamento mensal” continua sendo a entrada; subtítulo explicita o escopo documental.

### 17.3 Inventário visual componente por componente

| ID | Componente | Campos e comportamento | Owner/estado |
|---|---|---|---|
| DRE-01 | Shell restrito / PagePath | Apenas navegação autorizada; título “Fechamento mensal” + subtítulo documental | Core manifest/guards e kit; \`TARGET/CONTRACT_GATE_PENDING\` |
| DRE-02 | CompetenceSelector | Apenas competências já existentes para aquele recipient, formatação MM/AAAA; revalidar lista/seleção ao trocar | P1/P5/Core scope; \`TO_INVENTORY\` |
| DRE-03 | Contexto de destinatário | Área/destinatário em texto; seletor apenas para múltiplos escopos efetivamente autorizados | Core/P5; \`TO_INVENTORY\` |
| DRE-04 | Filtros/busca | nome/código, tipo/grupo, situação de complemento e ordenação temporal quando DTO suportar | BFF projection; \`TARGET\` |
| DRE-05 | Lista única de documentos | item, anexo liberado, versão, timestamps, destinatário, última interação; contagem somente se resposta válida | P2/P5 view; \`TARGET\` |
| DRE-06 | Detalhe documental | metadados da versão, proveniência, estado de liberação, ações de preview/download quando existentes | P2/P5/BFF/attachment kit; \`TO_INVENTORY\` |
| DRE-07 | Comentar | composer de texto, confirmar, feedback, linha do tempo; não é validação | Novo contrato de interação \`DECISION_REQUIRED\` |
| DRE-08 | Solicitar complemento | formulário contextual com documento/versão, descrição objetiva, registrar; sem rejeição P2/P5 implícita | Novo contrato de ação \`DECISION_REQUIRED\` |
| DRE-09 | Histórico compartilhado | evento, autor, data/hora, origem, vínculo a versão; disponível também à Controladoria quando scope permitir | timeline/event owners \`TO_INVENTORY\` |
| DRE-10 | Notification projection | apenas eventos relativos a documento/competência e destinatários autorizados fora da audiência DRE | Core Notifications \`DECISION_REQUIRED\` |
| DRE-11 | Help | como acessar documentos, baixar, comentar, solicitar e consultar resposta; limitações de acesso | \`TARGET\` no mesmo gate |

**Reuso visual:** \`createDashboardPagePath\`, \`createDashboardPageHero\`, \`ResizableColumns\`, \`DataTableSection\`/\`DataRecordCard\`, \`createDashboardFiltersKit\`, \`AttachmentFileList\`, \`AttachmentPreviewStrip\`, \`Timeline\`, \`StateBanner\`, \`EmptyState\`, \`LoadingState\`, \`ConfirmModalPanel\`, \`ActionButton\`, \`BackLink\`, \`HelpTooltip\`, todos sob \`@delpi/plugin-ui/index\` após conferência de exports do HEAD.

### 17.4 Microinterações propostas

**Abertura:** Portal autentica → Core resolve rota/permissão específica quando aprovada → BFF retorna competências e documentos liberados só para audiência daquele usuário → página abre última competência autorizada **se contrato fornecer essa preferência**; alternativa padrão é exigir seleção. Não adivinhar competência corrente.

**Selecionar arquivo:** lista mantém filtros; detalhe exibe nome, versão, data de disponibilização, origem e destinatário; preview/download reautorizados individualmente. Se houver duas versões, explicitar vigente e histórico consultável autorizado; versão rejeitada/histórica pode não estar liberada para DRE.

**Comentar:** editor vinculado ao documento e à versão exibida; descrever o comentário → enviar após confirmação do usuário → backend cria evento auditado → timeline comum atualiza → notificação eventual fora da audiência DRE segundo contrato. Sem mensagens vazias ou post automático ao navegar. Não inserir upload ou anexos no compositor.

**Solicitar complemento:** ação independente de “Comentar”, pede texto objetivo e referência ao documento/versão; após backend confirmar gravação, exibir etiqueta “Complemento solicitado” e evento na timeline. A existência de campos de prioridade, prazo, categoria, responsável, fechamento da solicitação e botão “Resolvido” permanece **PENDING_PRODUCT/CONTRACT**; não gerar status livre nem acoplar a P4 sem owner aprovado.

**Resposta da Controladoria:** deve aparecer na mesma timeline a partir de mensagem/evento autorizado no lado interno do Portal; o usuário DRE visualiza a resposta no documento, sem editar ou apagar eventos anteriores. A possibilidade de resposta adicional DRE será definida na semântica de thread.

**Atualizar:** refetch de leitura preserva competência/filtros e não duplica mensagens; erro de POST mantém texto digitado e permite retry idempotente quando contrato definir.

### 17.5 Estados e segurança de experiência

| Estado | Mensagem / comportamento |
|---|---|
| Competência sem documentos liberados | “Não há documentos disponibilizados para sua área nesta competência.” (somente se ausência real confirmada) |
| Carregamento | Skeleton lista/detalhe, título e competência preservados |
| Nenhuma competência acessível | “Nenhuma competência disponível para consulta.” sem revelar competências de terceiros |
| Arquivo indisponível | Distinguir autorização negada de storage/fonte indisponível; não oferecer link inseguro |
| Solicitação aberta | Mostrar somente se evento/status físico existir; motivo e autor/timestamp |
| Download permitido | arquivo obtido por caminho temporário/autorizado, auditado na BFF, sem URL pública fixa |
| 403/404 | não expor metadados de outro destinatário e não indicar existência sensível |
| Network timeout | retry sem apagar contexto; em comentário, não duplicar gravação |
| Troca de competência | limpar detalhe e versões anteriores antes de novo fetch |
| Tema/mobile | claro/escuro mesma árvore; lista→detalhe full width, botões acessíveis e retorno, foco/teclado |

### 17.6 Critérios de aceite visual (não equivalem a teste executado)

A1: usuário DRE entra por **Fechamento mensal** e encontra exclusivamente documentos anexados e liberados do próprio scope.
A2: não há controles, navegação, busca ou exposição de payloads TOTVS, relatórios, paridade, estoque, administração, upload ou aceite.
A3: lista e detalhe permitem selecionar, ler e baixar arquivo/versão autorizado; download é auditável.
A4: comentar e solicitar complemento têm modos distintos e mostram contexto do documento/versão, confirmação/feedback e trilha auditada.
A5: quando houver resposta, o entregador autorizado e o DRE veem a mesma trilha permitida, sem duplicar documento.
A6: o motor de notificação exclui DRE destinatário de broadcast e nunca notifica usuário sem scope; alvos finais dependem de contrato.
A7: desktop/mobile, teclado/foco, tema claro/escuro e Help aprovados; error/empty/partial não mentem sobre dados.
A8: testes futuros precisam cobrir acesso direto à URL TOTVS/stock/API, acesso cruzado por recipient/competência/versão, permissão revogada e falha Core fail-closed.

### 17.7 DECISION_REQUIRED antes de runtime

1. **D-DRE-MANIFEST-01:** exceção à identidade de duas permissions congeladas no produto e rollout Core/manifest/launcher/guards/BFF. Doc 91 registra direção de produto e adiamento; não implementar por inferência.
2. **D-DRE-COLLAB-01:** persistência/owner/DTO do comentário e da solicitação, thread/visibilidade/resposta, estado e idempotência; mapear reuso de eventos/notifications e P2/P5.
3. **D-DRE-NOTIFY-01:** escopo de “todo mundo menos DRE” deve restringir recipients a atores elegíveis com visibilidade do documento e competência; broadcast indiscriminado criaria exposição indevida. Exige PO + segurança/Core Notifications.
4. **D-DRE-LIBERATION-01:** fato/estado que libera anexo individual ou PackageVersion para consulta DRE; separar de “enviado para revisão” P5 e de aceitação P2.
5. **D-DRE-HISTORY-01:** se versões anteriores ficam visíveis à audiência externa, e quais eventos de download/comentário são partilhados.
6. **D-DRE-ENTRY-01:** rota/URL exatas, navegação do launcher e comportamento para \`.manage\` sem acesso geral. \`MANAGE != ACCESS\`; não tratar manage como superusuário de leitura.

**Próximo passo:** revisão visual PO da listagem + detalhe + composer e solicitação de complemento. \`DESIGN_V0.8=PENDING_PO\`, \`RUNTIME_GO=NO\`.


## 18. Aprovação PO — conversa inline no detalhe e reuso real do plugin-ui / Minhas Solicitações

**Data:** 2026-10-26. **Entrada:** PO aprovou o wireframe DRE V0.8 e mostrou capturas do Portal **Minhas Solicitações**, apontando que o padrão de conversas já existe no \`@delpi/plugin-ui\`. **Estado:** \`PO_APPROVED_VISUAL\` para conversa e histórico permanentes no detalhe; \`PROVEN_CODE_EXPORTS\` para o reuso visual; \`CONTRACT_TO_INVENTORY\` para integração à BFF de Fechamento Mensal. A decisão não constitui autorização de runtime.

### 18.1 Evidência visual das capturas anexadas pelo PO

As duas imagens da interface de Minhas Solicitações apresentam:
- tópico “Conversa sobre a solicitação” em área maior, com mensagens identificadas por ator e data/hora, alinhamentos diferenciados e miniaturas de anexos;
- um compositor na parte inferior do histórico quando a solicitação permite mensagens;
- no estado finalizado, aviso textual “Esta solicitação foi finalizada. A conversa está somente leitura.”, sem compositor de escrita;
- painéis separados de documentos da solicitação e documentos gerados no atendimento.

**Limite:** as capturas comprovam layout observado, não compatibilidade de DTO/API da conversa com a Central de Fechamento, nem garantem política de edição/anexo idêntica.

### 18.2 Reuso técnico confirmado no HEAD do GitHub

- \`plugins/my-requests/src/ui/mrUi.tsx\` importa de \`@delpi/plugin-ui/index\` os exports **\`createDashboardMessageThread\`**, **\`createDashboardMentionComposer\`**, **\`createDashboardRoomConversationShell\`** e **\`createDashboardAttachmentPreviewStrip\`**.
- O mesmo arquivo compõe \`MyRequestsMessageThread\`, \`MyRequestsMentionComposer\` e \`MyRequestsRoomConversationChatColumn\` a partir das factories do kit (prefixo próprio \`my-requests\`).
- \`plugins/my-requests/src/components/CommentsPanel.tsx\` utiliza esses wrappers, com API/DTO de \`RequestComment\` e métodos \`listComments/createComment/patchComment\` **específicos do contexto My Requests**.
- Portanto **reutilizar as factories genéricas do \`@delpi/plugin-ui\`, NÃO copiar \`CommentsPanel\` nem chamar API de \`my-requests\`** a partir da Central de Fechamento; evitar import cross-context.
- Existência de factory UI **não comprova** que já exista porta/contrato de comentários/solicitações para documentos P2/P5; novos adapters e integração somente após inventário+decisão+GO.

### 18.3 Design visual aprovado para a página restrita

**\`D-DRE-UX-THREAD-01=PO_APPROVED\`:** no detalhe do documento, a ordem visual é:
1. título do documento, metadados, competência, status de disponibilização;
2. arquivo liberado/versão e \`Visualizar\`/\`Baixar\` conforme contrato;
3. **“Conversa sobre o documento” permanentemente visível**, em painel abaixo do arquivo, seguindo a hierarquia visual de Minhas Solicitações;
4. mensagens de Contabilidade e Controladoria, com ator, instante, tipo \`COMENTARIO\` vs \`SOLICITACAO_COMPLEMENTO\` e vínculo à versão/competência;
5. compositor contextual na parte inferior, com modo **Comentar** ou **Solicitar complemento**, disponível apenas quando BFF autorizar;
6. histórico de eventos sistêmicos (disponibilização, versões, correções) auditável, junto ao diálogo ou em subseção distinguível, sem apagar mensagens.

**Não transformar a conversa em área de upload documental.** O controle de anexar imagens na conversa existente em Minhas Solicitações **não autoriza anexos no contexto DRE**: por padrão no wireframe DRE, compositor **texto apenas**; suporte a imagens/anexos de comentário exige decisão própria. O usuário DRE continua sem poder carregar/substituir arquivos da documentação.

**Estado somente leitura:** se o contrato da competência/versão/recorte vedar interações, apresentar explicitamente a mensagem de indisponibilidade de conversa, mantendo timeline legível; não inferir terminalidade a partir de estado P5 sem contrato.

### 18.4 Mapeamento visual para a implementação futura

| Necessidade | Kit first | Contexto e responsabilidade |
|---|---|---|
| Conversa de mensagens | \`createDashboardMessageThread\` | Renderizar mensagens da BFF do fechamento, não de my-requests |
| Editor contextual | \`createDashboardMentionComposer\` | Usar apenas capabilities contratadas (texto sem anexo neste wireframe) |
| Estrutura conversa | \`createDashboardRoomConversationShell\` | Adaptar grid/composição ao painel documental; não duplicar shell |
| Lista de arquivos liberados | \`createDashboardAttachmentPreviewStrip\` ou P2 \`AttachmentFileList\` | Download e preview com AuthZ por versão na BFF |
| Eventos sistêmicos | \`createTimeline\` | Registrar tipo, ator, timestamp, versão e source preservada |
| Estado read-only/erro | \`StateBanner\`, \`EmptyState\`, \`LoadingState\` | Sem falsos vazios; manter conteúdo quando comentário falhar |

**Visual mobile:** documento primeiro; mensagens em largura total; campo de texto acessível no final; enviar com foco/feedback; scroll da thread sem esconder cabeçalho, botão de retorno à lista. **Light/dark:** mesma árvore, tokens do kit.

### 18.5 Gates ainda pendentes — não mascarar como aprovado

1. **\`D-DRE-COLLAB-01\`**: owner/contrato de mensagem, comentário e solicitação de complemento, visibilidade cruzada, resposta, histórico, edição e estado aberto/resolvido.
2. **\`D-DRE-NOTIFY-01\`**: público não-DRE autorizado a receber notificações, restrito por item/competência/scope, com payload seguro; sem broadcast sensível indiscriminado.
3. **\`D-DRE-MANIFEST-01\`**: exceção a freeze de duas permissions, já aprovada como intenção no Doc 91, porém deferida e pendente de gate transversal.
4. **\`D-DRE-COMPOSER-01\`**: manter texto somente (recomendação) ou permitir imagens anexas às mensagens (não confundir com envio de documento); decisão a discutir se necessária.
5. **\`D-DRE-RELEASE-01\`**: estado que libera o anexo ao usuário DRE, com versionamento e recipient.
6. Nenhuma implementação de UI/BFF/Core/manifest/permission/storage foi autorizada neste ciclo. \`RUNTIME_GO=NO\`.

**Próximo desenho recomendado:** estados da conversa (nova mensagem, complemento solicitado, resposta, somente leitura, erro, upload documental proibido) e contrato de notificações de audiência, mantendo o wireframe restrito.


## 19. Destaque e notificação para solicitação de complemento — confirmação funcional

**Data:** 2026-10-26. **Origem:** PO perguntou se a ação "Solicitar complemento" aparece em destaque e gera notificação na Minha DELPI. **Direção confirmada em design:** SIM. **Status:** `PRODUCT_BEHAVIOR_CONFIRMED / CONTRACT_PENDING / NOT_IMPLEMENTED`. Não interpretar como prova de notificação ativa em runtime.

**Fluxo de interface proposto:**
1. Contabilidade/DRE autorizada abre documento **anexado e liberado** e envia uma `solicitação de complemento`, com mensagem obrigatória e vínculo à competência, ao documento e à versão.
2. A conversa ganha evento destacado **Complemento solicitado**, identificando autor, momento, descrição e contexto; a listagem sinaliza que há complemento solicitado. O destaque não se confunde com rejeição/validação P2 nem com aceite/revisão P5.
3. Após gravação confirmada pela BFF, gerar evento para **Core Notifications / Minha DELPI**. Destinatários: usuários internos **não-DRE** efetivamente autorizados a acessar a competência/documento e envolvidos no tratamento, conforme regra owner/scope a contratar; **não** fazer broadcast irrestrito para toda conta com app access.
4. A notificação abre deep link seguro para a competência/documento/conversa, sujeito a nova AuthZ na BFF; nenhuma capacidade se concede por receber notificação.
5. A Contabilidade acompanha solicitação e respostas na mesma linha do tempo, sem poder anexar/substituir ou consultar relatórios TOTVS.

**Apresentação:** selo textual `Complemento solicitado`, ícone semanticamente correspondente, marcação da mensagem na conversa e indicação discreta no registro da lista. Cor não é único sinal de status. A definição de `aberta/resolvida` e de como retirar o destaque **depende do contrato de lifecycle de solicitações**; não fabricar estado de negócio.

**Dependências:** contrato de comentário/solicitação e persistência, mapeamento de audiência elegível, integração com notificações existentes, idempotência e auditoria, estados/erro/falha parcial, deep links e testes. `D-DRE-NOTIFY-01=PRODUCT_BEHAVIOR_CONFIRMED / TARGET`; `D-DRE-NOTIFY-AUDIENCE=DECISION_REQUIRED`; `IMPLEMENTATION_AUTHORIZED=NO`.


## 20. Fechamento documental do Wireframe DRE — complemento validável, WebSocket e contratos posteriores

**Data:** 2026-10-26. **Origem PO:** “Depois tem que ser validado a questão do complemento”; conversas atualizadas em tempo real com WebSocket; contratos da API do Portal definidos em gate posterior; retornar agora à definição das outras páginas. **Estado:** \`PRODUCT_DIRECTION_APPROVED / DESIGN_FLOW_RECORDED\`; \`API_WEBSOCKET_CONTRACT=TO_INVENTORY\`; \`RUNTIME_GO=NO\`.

### 20.1 Fluxo funcional TARGET — não presumir máquina de estados existente

\`\`\`text
Contabilidade/DRE: Solicitar complemento (documento + versão + texto)
  → BFF autoriza e persiste solicitação/evento, com idempotência
  → mesma conversa destaca “Complemento solicitado” + lista sinaliza
  → evento de domínio após commit → Core Notifications para internos autorizados, excluindo DRE
  → WebSocket atualiza conversas abertas dos participantes autorizados
  → Controladoria responde / fornece complemento conforme P2
  → Contabilidade visualiza resposta e avalia atendimento
  → confirmação de atendimento por ator/owner definido
  → encerramento auditado do pedido; destaque evolui conforme estado efetivo
\`\`\`

**Invariante:** \`MENSAGEM_RESPONDIDA != COMPLEMENTO_VALIDADO != EVIDENCIA_P2_ACEITA != PACOTE_P5_APROVADO\`. Não encerrar automaticamente porque houve resposta, novo arquivo ou download. Não prometer novo enum físico/alteração de estado sem decisão.

**DECISION_REQUIRED (D-DRE-COMP-VALIDATION-01):** ator autorizado a declarar complemento atendido (solicitante Contabilidade, Controladoria, outro owner?), critérios de aceite de complemento, possibilidade de devolução, estado aberto/aguardando/verificado/encerrado e SLA (não presumir). Recomendação para avaliação do PO: **Contabilidade solicitante confirma atendimento**, Controladoria só marca “Resposta enviada”, preservando ausência de aceite formal P2/P5. Isto requer compatibilidade com restrição “DRE não aprova documentos/pacotes”; confirmação do *pedido de informação* é ato diferente.

### 20.2 Reuso técnico verificado — My Requests realtime

**HEAD inspecionado:** \`plugins/my-requests/src/app/MyRequestsRealtimeProvider.tsx\` estabelece \`WebSocket\`, heartbeat, reconexão, joins/leaves por request e handlers \`request.created\`, \`request.changed\`, \`request.timeline\`. \`RequestDetailPage.tsx\` usa \`useMyRequestsDetailSync\` para \`reload\` do detalhe/timeline em evento. O shell visual de conversa usa \`@delpi/plugin-ui/index\` — \`createDashboardMessageThread\`, \`createDashboardMentionComposer\` e \`createDashboardRoomConversationShell\` — documentados no §18.

**Diretriz:** copiar o **padrão arquitetural**, não importar application/domain/components internos de My Requests nem reutilizar API/rooms próprias do outro contexto. Identificar capability transversal de realtime da plataforma e os contratos/regras de segurança antes de definir o adapter do \`controllership-finance-api\`. Uma conexão existente em outro app não prova rota WS de Fechamento.

### 20.3 Contratos a fechar em gate posterior

| Plano | A verificar/definir | Segurança/resultado |
|---|---|---|
| Comando HTTP | criar comentário; solicitar complemento; responder; declarar atendimento; listar histórico; ler estado, ids/idempotency keys/versões | Core effective permissions + resource/recipient scope + business rule, nunca JWT como authority |
| Read model | documento, versão, competência, thread, mensagens, estado do complemento, paginação e cursor de sincronização | somente audience autorizada, sem dados de relatório TOTVS no DRE |
| Eventos WS | notificações de evento criado/alterado, sequência/cursor e envelope typed; eventos mínimos devem disparar reconsulta ao BFF | conexão e subscribe reautorizados; não distribuir payload sensível entre destinatários |
| Resiliência | reconnect, resubscribe, replay/missed messages, duplicidade, ordenação e reconciliação HTTP após retorno | não perder nem duplicar mensagem; ack persistido ≠ entregue em tempo real |
| Notificações Minha DELPI | evento após commit, filtros de destinatários, deep link documental | audiência interna não-DRE **e autorizada ao documento**; não broadcast irrestrito |
| Históricos | autoria/instante/versão/correlação, pedido e resposta, confirmação | append-only audit, sem apagar eventos ao substituir arquivo |
| Critérios de aceitação | duas sessões autenticadas; envio simultâneo; Core revogado; subscribe cruzado; conexão perdida e recuperada; mensagem repetida; histórico | \`TEST_NOT_RUN\` até execução com provas |

**NÃO criar endpoint ou WS path nesta fase, não adicionar permission nova, não alterar manifesto/Core ou persistência.** A exceção documental do [Doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) permanece \`DEFERRED\`.

### 20.4 Encaminhamento de UX — retorno às outras páginas

O PO solicitou avançar para páginas além de documentos. Próxima proposta a revisar: **Relatórios e divergências** (área da Controladoria exclusivamente), usando a classificação R01–R15 dos [docs 46](./46-t01-report-source-inventory-v1.md) e [47](./47-t01-report-column-audit-tracker-v1.md), sem afirmar equivalência funcional de relatórios G6 pendentes. Depois: **Visão geral/Cockpit** P1 e **Revisão do fechamento** P5; **Pendências** P4 permanece owner independente e a decisão de tab próprio ou fila contextual segue aberta.

**Estado de resultado desta rodada:** \`DESIGN_DOCUMENTED / CONTRACT_PENDING\`; sem revisão de runtime, \`TEST_NOT_RUN\`; próxima página \`TARGET / PENDING_PO_VISUAL_REVIEW\`.


## 21. Wireframe Relatórios — prévia fiel PDF TOTVS + disponibilização direta a Contabilidade/DRE (V0.9)

**Data:** 2026-10-26. **Origem funcional:** PO determinou que a apresentação final do relatório deve **preservar o formato do PDF exportado pela Joici**; relatórios como P7 / Bloco H são hoje extraídos em PDF e enviados ao conjunto de documentos destinado ao DRE. Novo fluxo proposto: **gerar PDF na ferramenta e disponibilizar diretamente na área documental do DRE**, sem ação manual de baixar e reenviar. PO também destacou que PDFs e demais evidências estão nas fontes do projeto. **Status:** \`PRODUCT_INTENT_PROVEN / VISUAL_TARGET_V0.9 / TECH_CONTRACT_DECISION_REQUIRED / RUNTIME_GO=NO\`.

### 21.1 PDFs originais inspecionados (fontes privadas da conversa/projeto)

Inspeção visual renderizada da página inicial e texto da primeira página dos seis PDFs fornecidos ao projeto (26/10/2026). **Não versionar conteúdo financeiro original, dados pessoais, screenshot das planilhas ou binários no GitHub público**. Lista, páginas, formato e títulos observados:

| Arquivo-fonte privado | Páginas | Formato PDF observado | Identidade/layout observado na primeira página | Referência |
|---|---:|---|---|---|
| \`Pagos por dt.pdf\` | 33 | A4 paisagem | \`SIGA/DLP06R01.prt/v.12\`, “Relação dos Títulos Pagos em REAL por data de pagamento”, colunas numerosas e pagination | R01 / FINANCEIRO |
| \`Pagos por nat.pdf\` | 35 | A4 paisagem | \`SIGA/nat.prt/v.12\`, “Relação dos Títulos Pagos em REAL por Natureza”, groupings/cabeçalho repetidos | R01 / FINANCEIRO |
| \`Recebidos.pdf\` | 36 | A4 paisagem | \`SIGA/DLP06R01.prt/v.12\`, “Relação dos Títulos Recebidos em REAL por data de pagamento” | R02 / FINANCEIRO |
| \`Entradas e saidas.pdf\` | 1 | A4 paisagem | \`SIGA/MATR320.prt/v.12\`, resumo entradas/saídas por tipo e valores/saldos | R05 / ESTOQUE |
| \`Estoque.pdf\` | 1 | A4 retrato | \`REGISTRO DE INVENTÁRIO\`, firma/filial, coluna classificação fiscal, unidade, quantidade, valores | CANDIDATO R03 P7, emissão ampla |
| \`Resumo Estoque.pdf\` | 1 | A4 retrato | \`REGISTRO DE INVENTÁRIO\`, mesma estrutura visual com totalização/escopo distinto | CANDIDATO R03 P7, emissão resumida |

**Interpretação:** os PDFs são **baseline visual e de comparação** para campos, ordem, cabeçalho, agrupamentos, subtotais, quebras/páginas e proporção/saída. Não são, por si, prova de código/queries equivalentes ao Protheus nem de G6. A [trilha R03 do Doc 46](./46-t01-report-source-inventory-v1.md) distingue \`Estoque.pdf\` amplo e \`Resumo Estoque.pdf\` MP/PI/PA com totais distintos, \`PDF_CATEGORIES=PROVEN\`, \`EXACT_SELECTION_RULE=TO_INVENTORY\`, \`EXPORT_PARITY=TEST_NOT_RUN\` naquele checkpoint. Conferir versões e se o “Bloco H” mencionado pelo PO corresponde exatamente à emissão resumida; **não equiparar sem parâmetros, source e aceite**.

Arquivos adicionais XLSB/XLSX, vídeo e roster do checklist também foram fornecidos no projeto. **Não assumir que os seis PDFs cobrem todos os entregáveis do snapshot P2 nem que cada relatório R01–R15 vira PDF enviado à Contabilidade**. A lista canônica de documentos obrigatórios/aplicáveis deriva do snapshot/recipient P2/P5 e das regras de liberação.

### 21.2 Princípio UX: fidelidade PDF + investigação rica separada

Duas superfícies do **mesmo relatório** para Controladoria:
- **Dados e conferência:** tabela navegável, filtros, fórmulas/regras, proveniência, diferenças, destaque de inconsistências. Pode usar componentes de análise distintos do PDF, mas sem mudar o conteúdo canônico.
- **Prévia do PDF final:** visualizar **a saída paginada que será gerada** com orientação A4, colunas, agrupamentos, labels, cabeçalhos, subtotais, rodapés, paginação e formatação monetária equivalentes ao original homologado. **Sem acrescentar badges, overlays, cores de divergência ou observações internas ao PDF oficial** salvo decisão formal de nova versão/layout. Divergências ficam no painel de conferência ao lado/aba distinta, não alteram o documento silenciosamente.

**Layout desktop proposto:**
\`\`\`text
Relatórios e divergências — Controladoria (DRE NUNCA acessa)
[Competência] [Empresa/filial] [Parâmetros da emissão] [Versão de layout]
[Catálogo R01–R15] → [Relatório R03 P7] [Dados e conferência | Prévia do PDF*]
                                                           *padrão oficial
[Parâmetros/escopo e comparação documentada] [Status de paridade/fonte]
┌───────────────────────────────────────────┬──────────────────────────────┐
│ PRÉVIA DE PDF ORIGINAL                    │ INFORMAÇÃO DA EMISSÃO       │
│ A4 retrato/paisagem conforme layout       │ Relatório/rotina/versão     │
│ cabeçalho, título, empresa, filial        │ Competência e filtros      │
│ linhas/colunas e totais paginados         │ Paridade e proveniência    │
│ Folha X de Y                              │ Documentos de destino      │
└───────────────────────────────────────────┴──────────────────────────────┘
[Baixar PDF gerado*] [Disponibilizar para Contabilidade/DRE*]
*habilitar somente quando os contratos/fonte/regra/aceite/autorização provarem.
\`\`\`

### 21.3 Sequência funcional desejada: gerar → conferir → disponibilizar

1. **Selecionar:** competência existente/autorizada, relatório específico (ex.: P7 / layout Bloco H), empresa/filial/armazenagem e demais parâmetros da rotina homologada.
2. **Carregar a origem:** BFF consome owner(s) canônicos via contratos; tela mostra freshness, disponibilidade e equivalência técnica; não pressupor SQL a partir de PDF.
3. **Conferir:** render de dados e divergências no workspace; fonte parcial, regra sem paridade ou divergência material bloqueadora ficam claramente visíveis.
4. **Pré-visualizar o PDF que será entregue:** gerar artefato de preview determinístico a partir de parâmetros/snapshot versão; comparar layout e totais à saída baseline. O preview deve representar os bytes que serão finalizados, não uma imagem simulada sem correspondência.
5. **Gerar documento:** registrar PDF com ID, layout version, filtros, competência, scope, fonte/snapshot, hash, autor, timestamp, e integridade; permitir download autorizado.
6. **Disponibilizar ao DRE:** ação da **Controladoria autorizada**, distinta de gerar/baixar, cria o vínculo ao **item correto de checklist/recipient e versão/competência** no contexto P2/P5, com idempotência, audit e confirmação. O PDF **não sai automaticamente só por ser gerado**; evitar envio indevido sem revisão. Se existir publicação segura já contratada, reutilizar a operação owner; não criar cópia/armazenamento paralelo.
7. **Confirmar resultado real:** a BFF comprova que o arquivo/versão foi vinculado e **liberado** ao destinatário correto. UI mostra estado e link read-only de destino quando permitido; usuário DRE enxerga **apenas o PDF final liberado**, nunca tabelas fontes de relatório, projeções, divergências, filtros ERP nem rotas de geração. Se publicação falhar, manter PDF gerado e estado “não disponibilizado”, com retry idempotente.
8. **Histórico:** preservar emissão anterior, quem gerou, parâmetros, quem disponibilizou, versão, hash e destinatário; reemissão não substitui versões liberadas silenciosamente.

**Invariantes:** \`PDF_GENERATED != PDF_VALIDATED != EVIDENCE_P2_ACCEPTED != PDF_RELEASED_TO_DRE != PACKAGE_SUBMITTED_P5 != MONTHLY_CLOSING_COMPLETED\`. O PO pediu envio direto; a semântica exata de “liberar ao DRE” deve ser reconciliada com Doc 91 (destinatário de consulta) e P5 (review formal) sem promover estado de pacote automaticamente.

### 21.4 Critérios de qualidade/aceite por relatório e não por catálogo

- **R01/R02 financeiro:** A4 paisagem, cabeçalhos específicos \`DLP06R01.prt\` vs \`nat.prt\`, dados por data vs natureza, colunas/ordens, grupos, subtotais, totalizadores, números, páginas; preservar diferença de layout e período, sem afirmar reprodução oficial só por G5.
- **R05 entradas/saídas:** A4 paisagem, categorias/colunas de saldo inicial/movimentações/saldo atual com valores conforme precisão do relatório.
- **R03 P7/inventário:** A4 retrato e título do Registro de Inventário, classificação fiscal/discriminação/unidade/quantidade/unitário/parcial/total, cabeçalho fiscal, folha e data-base; separar emissão ampla vs resumo/Bloco H, regras de seleção e totais; prova de layout e dados antes de liberar ao DRE.
- Reproduzir data/hora de emissão com semântica correta (emissão real, não hardcode de PDF histórico), quebras de página e cabeçalhos por folha.
- Campos/colunas/agrupamentos devem ter rastreio no Doc 47 (G1–G6) + source producer/owner/DTO + comparação PDF baseline (amostra e diffs visuais e monetários, incluindo totalizadores).
- Não “melhorar” layouts padrão com informação extra inserida no PDF sem gate de breaking visual; insights operacionais ficam na interface, não no PDF oficial.
- Armazenar original/proveniência com proteção adequada; jamais subir PDFs contendo dados financeiros ao repositório GitHub.

### 21.5 Decisões materiais pendentes

| ID | Questão | Proposta | Estado |
|---|---|---|---|
| D-REPORT-PDF-01 | Preview fiel e layout por relatório | Preservar layout homologado, A4 orientação original, dados e paginação | **PO intent approved**, \`TO_INVENTORY\` layout/versões por relatório |
| D-REPORT-PDF-02 | “Disponibilizar diretamente ao DRE” | CTA explícito depois da prévia, com confirmação e publicação no item/recipient certo | **TARGET / DECISION_REQUIRED** para release state/owner/integração P2/P5 |
| D-REPORT-PDF-03 | Qual saída de P7/Bloco H é o documento esperado | Comparar \`Estoque.pdf\`, \`Resumo Estoque.pdf\`, parâmetros MATR460 e checklist | \`TO_INVENTORY / PENDING_FUNCTIONAL_ACCEPTANCE\` |
| D-REPORT-PDF-04 | Política de divergências na emissão | Alertar/blocker segundo regra canônica; nunca declarar PDF aprovado sem paridade | \`DECISION_REQUIRED\` para cada bloqueio/override, não implementar por UI |
| D-REPORT-PDF-05 | Formato de artefato + hashing/storage/download | Adapter proprietário de P2/P5 conforme padrões plataforma e source owner | \`TO_INVENTORY\` |
| D-REPORT-PDF-06 | G6 / aceite visual e monetário | PO/Controladoria valida amostras por emissão/layout | \`TEST_NOT_RUN\` no ciclo atual |

### 21.6 Próxima página/componente

Dentro de Relatórios e divergências, priorizar o **componente “Prévia oficial do PDF”** com comparação visual do R03 Registro de Inventário (completo versus resumido/Bloco H), depois o CTA **Disponibilizar para Contabilidade/DRE**. Em seguida aplicar mesma matriz a R01/R02 e R05. Não implementar endpoint, render PDF ou storage por inferência enquanto não houver G6/ownership/contrato/GO.


## 22. Prioridade de design redefinida pelo PO — PDF em container e próxima página Visão geral

**Data:** 2026-10-26. **Diretriz explícita do PO:** manter o **container da prévia do PDF** na página Relatórios e divergências, mas **postergar o refinamento visual da reprodução fiel** e voltar ao desenho das demais páginas, sem gastar o ciclo em paginação/formatação de relatórios.

### 22.1 Escopo congelado do PDF neste gate

- **Mantido como requisito aprovado de intenção:** container para visualização do PDF final; relatório na tela pode oferecer dados/conferências; geração e disponibilização ao DRE devem ser ações conceitualmente separadas e autorizadas, com documento vinculado a item/competência/recipient correto.
- **Adiado:** detalhe pixel a pixel de Estoque/Resumo Estoque, cabeçalhos, tipografia, paginação, margens, quebras, campos, versões de layout, testes de equivalência visual e homologação.
- **Sem GO:** nenhum componente PDF, endpoint, storage, mutation ou botão de publicação foi implementado ou autorizado por este wireframe.
- **Próximo foco de design:** Página Visão geral da competência (P1), depois Pendências P4 e Revisão P5, preservando o mapa de owners e sem decidir silenciosamente se Pendências é aba ou fila transversal.

### 22.2 Wireframe 04 — Visão geral da competência, V1.0, proposta

**Estado:** `TARGET / DESIGN_DRAFT / PENDING_PO_VISUAL_APPROVAL`. A regra canônica do [Documento 08](./08-p1-cockpit-da-competencia.md) exige: contexto → blockers materiais → eixos independentes Estoque/Documentos/Pacote → pendências prioritárias → histórico → links aos owners. Os **três cartões clicáveis já aprovados** Bloqueios/Divergências/Documentos a tratar permanecem como atalhos na moldura comum da página, não substituem os três eixos de readiness.

```text
Portal Controladoria & Finanças > Fechamento mensal
[Competência existente autorizada ▼] [empresa/unidade escopo] [situação/freshness]
[ALERTA DE BLOQUEIOS MATERIAIS COM FONTE E DESTINO QUANDO HOUVER]
[Bloqueios — →] [Divergências — →] [Documentos a tratar — →]
[Visão geral*] [Documentos e interações] [Relatórios e divergências] [Revisão]
────────────────── VISÃO GERAL ──────────────────────────────────────────
ESTADO DOS EIXOS — NÃO SOMAR NEM TRANSFORMAR EM 100%
[ESTOQUE]                  [DOCUMENTOS]               [PACOTE]
estado P3 + fonte          estado P2 + fonte           estado P5 + versão
cutoff/paridade quando     entregáveis/validações     finalizado/submetido/
válidos                    e bloqueios                revisão humana
[Abrir Estoque*]           [Abrir Documentos]         [Abrir Revisão]
* somente destinos realmente disponíveis e autorizados
────────────────────────────────────────────────────────────────────────
O QUE PRECISA DA SUA ATENÇÃO
prioridade material (quando real) | tipo | motivo | source | responsável | desde
[ver ocorrência / abrir owner]
────────────────────────────────────────────────────────────────────────
ÚLTIMOS ACONTECIMENTOS DA COMPETÊNCIA
[timeline de eventos P2/P3/P4/P5, com autor, hora e versão quando disponível]
────────────────────────────────────────────────────────────────────────
[Acessos às áreas operacionais autorizadas, não duplicar Home como catálogo]
```

**Comportamento UX:**
1. Usuário responde primeiro “qual competência?” e “o que está bloqueando?”; blocker material fica antes dos indicadores e eixos, sem afirmar zero se alguma fonte estiver indisponível.
2. Os três indicadores FM-05 continuam **cartões inteiramente clicáveis**, navegando à referência/filtro conforme contrato e scope.
3. Os três eixos de fechamento são **independentes**: estoque fechado não implica documentação validada; documentação validada não implica pacote aprovado; não usar “% fechamento”.
4. Em **O que precisa da sua atenção**, mostrar apenas subconjunto factual de ações/pendências realmente atribuíveis/visíveis ao usuário; P4 continua owner da pendência. Nunca mostrar “atrasado” sem SLA contratada.
5. Histórico usa events materializados/auditáveis, não mensagens de conversa arbitrárias convertidas em decisão.
6. Link abre owner (P2/P3/P4/P5) com competência e escopo preservados; UI não executa mutation de owner na P1.
7. Estados loading, vazio verdadeiro, partial/unavailable, permissão insuficiente, divergência de fonte e stale com mensagens específicas. Mobile empilha blockers e eixos, depois fila e histórico. `@delpi/plugin-ui/index` first: PagePath, PageHero, AlertQueue, MetricStrip, StatusBadge, SectionCard, WorklistItem, Timeline, StateBanner/EmptyState/LoadingState.
8. O acesso restrito Contabilidade/DRE **NÃO exibe essa página completa, eixos nem relatórios TOTVS**: sua entrada Fechamento mensal abre exclusivamente os documentos anexados e liberados, conforme §§16–18.

**Decisão para o próximo review visual:** confirmar a estrutura da Visão geral (blockers → 3 indicadores → 3 eixos → atenção → histórico) e se o componente de pendências prioritárias abre uma página P4 independente ou uma visão contextual. **D-FM06-REBASE-01 permanece DECISION_REQUIRED**; avanço no wireframe não revoga a decisão documental anterior nem autoriza código.


## 23. Correção de navegação conforme referência visual do PO — quatro abas do Fechamento mensal

**Data:** 2026-10-26. **Evidência:** PO reapresentou captura do próprio wireframe V0.6 e afirmou: “essa eram as paginas definidas”. **Estado:** `PO_RECONFIRMED_VISUAL_INFORMATION_ARCHITECTURE`. Esta seção é a referência visual vigente e corrige as sequências posteriores que sugeriam uma aba `Pendências` como quinta página sem aprovação.

### 23.1 Estrutura visual definida

**Moldura:** cabeçalho `Fechamento mensal` + competência existente/autorizada + três indicadores clicáveis, **Bloqueios**, **Divergências**, **Documentos a tratar**.

**Quatro visões da bancada operacional da Controladoria, na ordem da captura:**

1. **Visão geral** — panorama da competência, blockers materiais, eixos estoque/documentos/pacote, fila contextual e histórico.
2. **Documentos e interações** — checklist/entregáveis, versões de evidências, upload elegível, avaliações/interações e histórico compartilhado.
3. **Relatórios e divergências** — relatórios TOTVS por família, conferência/diagnóstico, container de prévia do PDF final e ação futura de disponibilizar PDF liberado ao DRE.
4. **Revisão** — pacotes, versões, submissão, esclarecimentos, aceites humanos P5 e condições de conclusão conforme contrato.

`D-FM06-REBASE-01 = A / PO_RECONFIRMED_VISUAL`: **quatro abas**. Não criar quinta aba `Pendências` nesta composição, e não converter a página `Pendências e classificações` em nova navegação top-level apenas porque consta como P4 no roadmap. O processo P4 continua autônomo no domínio, com worklist contextual e eventual navegação profunda para seu owner mediante contrato e rota existente; preservar paths legados até decisão formal de alteração/depreciação. **Pendência não é sinônimo de documento.**

**Contabilidade/DRE:** mantém **uma página restrita própria**, acessada como `Fechamento mensal` no escopo autorizado, com somente documentos anexados/liberados, consulta/download/comentário/complemento. **Não** é uma das quatro abas da Controladoria e não possui acesso aos relatórios TOTVS. Permission específica previamente aprovada como intenção (Doc 91) segue exceção contratual deferida; nenhum runtime nesta rodada.

### 23.2 Correção no sequenciamento do projeto visual

Na resposta anterior, “Próximo detalhamento — Pendências e classificações” foi apresentado como se fosse próxima página independente. **CORRIGIDO:** concluir detalhamento da **Visão geral** e avançar diretamente para **Revisão**, que é a quarta aba ainda não detalhada no mesmo nível. P4 é componente/contexto transversal a mapear sem alterar a navegação de quatro abas.

**Permanecem pendentes:** componente P4 em profundidade, estados reais do P1, decisão de contrato sobre navegação em rota vs aba/deep link, PDF de cada emissão, contrato de complemento/WebSocket e gate de permissions DRE. Esta aprovação é **visual/informacional**, não GO de implementação.


## 24. Regra PO de navegação mínima e avaliação de integração de P5 — NÃO criar páginas redundantes

**Data:** 2026-10-26. **Manifestação PO:** “A gente não deve sair criando muitas páginas”; documentos a tratar pertencem a Documentos, divergências e sugestões de correção TOTVS pertencem ao próprio relatório, e o usuário não deve precisar entrar e sair de abas para concluir uma tarefa. Pergunta material: se a aba `Revisão` precisa existir ou pode ser absorvida pelas áreas existentes.

**Decisão documental confirmada — `PO_APPROVED_UX_PRINCIPLE`:** **nenhuma nova aba/página por métrica, botão, categoria, pendência ou etapa técnica quando o trabalho cabe na bancada funcional já existente**. O princípio limita a navegação e preserva os owners de domínio P2/P3/P4/P5. Não criar nova permission por página nem eliminar rotas legadas sem decisão e plano de compatibilidade.

### 24.1 Mapeamento canônico por trabalho do usuário

| Trabalho | Lugar principal | Comportamento de entrada |
|---|---|---|
| Documentos a tratar, upload elegível, versões, comentários e complementos | `Documentos e interações` P2 | Cartão de indicador navega para esta aba com filtro “a tratar” quando contratado; não criar aba própria |
| Divergências, conciliações, regra de negócio e sugestões de correção manual no TOTVS | `Relatórios e divergências` P3 / owner canônico | Card navega ao relatório/filtro correto, mostra origem, diferença, regra, evidência e orientação; **não** alterar ERP pela UI |
| Bloqueios materiais, status dos três eixos, acontecimentos e próximo trabalho | `Visão geral` P1 | Composição/read-only de owners, sem percentual único de conclusão |
| Pendências/classificações P4 | Subárea contextual pertinente com worklist/links ao owner P4 | Não fundir P4 com P2 nem criar quinta aba sem PO; preservar lifecycle/contratos |
| Finalização/submissão/revisão humana do pacote consolidado | P5 `PackageVersion` | P5 é processo próprio, não sinônimo de validação de documento nem simples conciliação |

**Invariante UX:** ficar no contexto da competência, com drilldown, seleção, filtros e retorno preservados. Cards FM-05 são atalhos clicáveis para a bancada funcional correspondente, não destinos top-level independentes.

### 24.2 Esclarecimento canônico sobre P5 — ver doc 37

P5 significa **revisão do pacote/versionamento do fechamento**, que pode abranger documentos e resultados de diferentes fluxos. O contrato vigente registra:

```text
PREPARAR PACOTE
→ FINALIZAR (PackageVersion imutável)
→ ENVIAR PARA ANÁLISE (reviewers elegíveis na Minha DELPI)
→ NOTIFICAR
→ RECEBER ANÁLISES/ACEITES HUMANOS/ESCLARECIMENTOS
→ VERIFICAR CONDIÇÕES CANÔNICAS DE CONCLUSÃO DA COMPETÊNCIA
```

`FINALIZE != SUBMIT_FOR_REVIEW != NOTIFY != REVIEW != MONTHLY_CLOSING_COMPLETED`. Revisores P5 têm atribuição por área/versão e acesso/escopo efetivos; **destinatário Contabilidade/DRE restrito que só consulta/baixa/comenta documentos não é automaticamente reviewer P5 nem aprova na V1**. Não transferir a authority das decisões P5 para P2/P3 por reorganização visual.

### 24.3 DECISION_REQUIRED — três vs quatro abas, sem substituir decisão prévia silenciosamente

**A — Três abas principais (opção nova em análise):**
1. Visão geral
2. Documentos e interações
3. Relatórios e divergências

`Revisão` P5 seria tratada como painel/fluxo contextual a partir da Visão geral e referências do pacote, **sem perder** versões, auditoria, notificações, tarefas dos reviewers nem deep links. **Impacto:** simplifica menu, mas risco de sobrecarregar Visão geral e de ocultar decisões formais. Precisa detalhar navegação P5 e modo reviewer antes de aprovação.

**B — Quatro abas principais (baseline visual V0.6 / §23):**
1. Visão geral
2. Documentos e interações
3. Relatórios e divergências
4. Revisão

P5 permanece bancada própria somente para **pacote, versões, submissão, decisões humanas, esclarecimentos, critérios de conclusão**, sem duplicar o catálogo de documentos ou relatórios. **Recomendação de arquitetura atual: B** pela distinção real do fluxo, mantendo a navegação principal compacta. **PO ainda não escolheu entre A e B nesta reconsideração**; até decisão, prevalece baseline V0.6 de quatro abas, sem qualquer alteração de implementação.

### 24.4 Diretrizes para sugestões de divergência

Na própria bancada Relatórios e divergências mostrar: origem e estado da fonte, regra/cálculo, diferença comprovada, explicação da causa quando suportada pela regra/evidência, sugestão governada do procedimento manual no TOTVS, owner e ação para reexecutar a leitura/reconciliação. A sugestão **não executa write no ERP**, não confirma classificação P4 automaticamente e não substitui evidência de resultado. Quando a causa não for determinada, mostrar `CAUSA_NAO_CONFIRMADA` em UI como mensagem explicativa, **não** como novo enum de domínio.

### 24.5 Limites e próximo passo

- Estrutura: **nenhuma quinta aba** de Pendências, Documentos a tratar ou Divergências; indicadores continuam atalhos da moldura.
- PDF: preservar apenas container de prévia/gerar/disponibilizar neste momento, detalhamento de fidelidade adiado a pedido PO.
- DRE: landing documental restrita já decidida, sem relatórios TOTVS, independente do número de abas da Controladoria.
- Se a escolha for A, documentar alteração **explícita** da decisão visual de quatro abas, com destino e deep links de P5, antes de runtime.
- **`DECISION_REQUIRED / PENDING_PO`** para contêiner de P5 na opção A vs aba dedicada B.
- **`RUNTIME_GO=NO`**: nenhum código, manifest, permission, rota, API ou schema implementado por esta discussão.


## 25. PO aprova três abas e histórico integral por competência — decisão visual V1.1

**Data:** 2026-10-26. **Origem:** decisão explícita do PO em chat: “três abas é o correto”; a revisão operacional ocorre por documento, por exemplo P7 PDF enviado, ajuste solicitado pela Contabilidade, nova versão substituída pela Joici, histórico preservado; a **Visão geral** seleciona competências mensais e apresenta contexto histórico de documentos e relatórios de cada fechamento. **Classificação:** `PO_APPROVED_INFORMATION_ARCHITECTURE` (navegação de três abas); `TARGET` (modelo de exibição temporal e revisão documental); `DECISION_REQUIRED` (reconciliação do contrato P5). `IMPLEMENTATION_AUTHORIZED=NO`.

### 25.1 Decisão D-FM06-REBASE-01 = A — três abas, não quatro

**Substitui expressamente** a proposta anterior de quatro abas da V0.6/§23/§24 no aspecto de **navegação visual**. Abas na bancada operacional da Controladoria, somente:

1. **Visão geral** — ~~seletor de competências existentes e autorizadas~~ **SUPERADO pela decisão PO de 26/10/2026 (ver §3 e §31): seleção livre de mês de referência YYYY-MM, sem exigir competência aberta** — consulta de setembro/2026, outubro/2026 etc., status histórico do fechamento, bloqueios, eventos e entradas contextualizadas por competência;
2. **Documentos e interações** — checklist/documentos, anexos, versões (V1, V2, ...), comentários, pedidos de complemento/correção, resposta, documentação disponibilizada à audiência autorizada e histórico do item;
3. **Relatórios e divergências** — catálogo e resultados TOTVS autorizados, parâmetros e versões da emissão referentes à competência, divergências e orientações de correção manual na origem, container de prévia PDF e disponibilização governada do arquivo resultante à documentação.

**Não criar aba top-level** Revisão, Pendências, Documentos a tratar ou Divergências. Os três cartões clicáveis da moldura (Bloqueios, Divergências, Documentos a tratar) passam apenas filtros/foco às superfícies acima. Manter competência, empresa/filial autorizada, filtros, item/relatório selecionado e link de retorno durante drilldown. Pendências P4 preservam domínio/owner e são contexto/fila aplicável, não nova aba. A Controladoria e a Contabilidade/DRE **não** recebem a mesma experiência: DRE continua página documental restrita, sem relatórios TOTVS, uploads ou aceite formal P2/P5.

### 25.2 Revisão de documento: timeline vinculada a cada entrega, não pacote novo a cada PDF

**Exemplo de jornada** (sem equivalência de status garantida até contratos):
- Joici gera/anexa versão V1 do PDF P7 vinculado à competência e ao entregável correspondente;
- o arquivo é disponibilizado ao destinatário autorizado mediante ato explícito e auditado;
- Contabilidade/DRE consulta, comenta ou solicita complemento/ajuste do documento; a solicitação ganha destaque e notificação interna conforme recipients autorizados;
- a Joici responde e, quando cabível, produz/anexa V2; o binário e o evento V1 continuam no histórico, vinculados à mesma identidade de item/documento;
- Contabilidade consulta nova versão, registra resposta/resultado de **atendimento do complemento** sob contrato futuro; isto **não equivale** a validar formalmente evidência P2 ou aceitar PackageVersion P5;
- UI pode mostrar `V1 → pedido de ajuste → V2 → resposta`, com ator, instante, versão e vínculo, sem sobrescrita silenciosa.

**Vocabulário visual:** evitar usar “primeira revisão” como estado de package review P5 se significa “primeira versão do PDF”. Exibir “Versão 1”, “Versão 2”, “Ajuste solicitado”, “Resposta registrada” e “Complemento atendido” apenas se houver status contratados. O último evento na conversa não torna documento/pacote automaticamente aceito ou competência encerrada.

### 25.3 Visão geral histórica por mês: layout-alvo

```text
Fechamento mensal
[Mês de referência: 2026-09 ▼]  (SUPERADO §3/§31: seleção livre, não restrita a competências abertas) [empresa/escopo autorizado]
[Estado do fechamento e última atualização canônicos]
[Bloqueios → contexto] [Divergências → Relatórios] [Documentos a tratar → Docs]

[Visão geral*] [Documentos e interações] [Relatórios e divergências]

RESUMO DA COMPETÊNCIA
[Estoque: status owner] [Documentos: status owner] [Pacote: status owner]
[Acontecimentos relevantes, pendências e blockers materiais]

ARQUIVO DO FECHAMENTO — ESTA COMPETÊNCIA
[Documentos/versões disponibilizadas] [Relatórios/fontes/gerações utilizadas]
[Histórico cronológico de eventos e alterações]
[Contexto de finalização e submissão/decisões de pacote, se houver]
[Filtrar tipo, período, área, origem; não misturar competências]
```

O seletor mostra competências realmente existentes e autorizadas, **não cria mês**. Cada competência usa seu snapshot histórico e preserva versões, autor, timestamp, parâmetros do relatório/fonte, destinatário, status e rastreabilidade. Não mostrar PDF atual como se fosse a versão usada no fechamento histórico; emitir novo documento é evento separado, sem mutar a prova anterior. `Disponibilizado ao DRE` depende de scope/estado de liberação real. Cada recurso permanece protegido por Core effective permissions **AND** resource/recipient scope **AND** regra de negócio, fail-closed.

### 25.4 Conflito semântico material P5 — não revogado pela decisão visual

O [Doc 37 P5](./37-p5-submissao-e-revisao-no-portal.md) define **PackageVersion imutável**, `FINALIZE != SUBMIT != REVIEW != MONTHLY_CLOSING_COMPLETED`, reviewers atribuídos, aceites humanos por área/versão, esclarecimentos e requisitos de conclusão. O [Doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) define a audiência restrita DRE **sem aceite formal** na V1. O PO descreveu revisão documental cotidiana, **não aprovou expressamente a remoção dos invariantes P5**. Assim:

- **DECISION_REQUIRED: D-P5-SURFACE-01** — onde exibir preparação/finalização/submissão, decisões e status P5 **sem quarta aba**. **Recomendação:** resumo do pacote e acesso ao painel contextual na própria Visão geral, com fluxo de detalhe sob mesma competência, sem nova navegação top-level; manter owner e deep links P5 existentes até gate de compatibilidade.
- **DECISION_REQUIRED: D-P5-CLOSURE-01** — o relato “fechado o pacote” refere-se a registro visual e arquivo histórico ou propõe alteração de regras de conclusão/aceites humanos? **Não presumir** equivalência nem retirar workflow formal do Doc 37.
- **D-DRE-DOC-REVIEW-01:** comentário e solicitação de complemento **não são aceite P5**; confirmar quem declara complemento atendido em contrato posterior.
- **D-ARCHIVE-SNAPSHOT-01:** recorte imutável por competência, associação de versões de PDF geradas e links aos relatórios; producer/API/evidência `TO_INVENTORY`.
- **D-FM06-ROUTER-01:** o fato de haver três abas não autoriza apagar rotas P4/P5, alterar permission codes ou quebrar deep links; inventário + gate.

### 25.5 Critério de navegação mínima e próximos wireframes

O design de **três abas fica aprovado pelo PO** e será a nova base dos wireframes; a arquitetura interna de pacotes P5, histórico de competência e editabilidade temporal será refinada dentro das áreas definidas. Priorizar novo wireframe da **Visão geral histórica por competência**, depois painel contextual de pacote, depois relatório e documento em contexto mensal. O PDF final fica em container até revisão posterior da fidelidade.

**Status da rodada:** `PO_APPROVED_VISUAL_THREE_TABS / P5_RECONCILIATION_PENDING / RUNTIME_GO=NO / NO_CODE_CHANGED`.


## 26. Gate do primeiro incremento de implementação — Home e Fechamento mensal; DRE por último

**Data:** 26/10/2026. **Ordem explícita do PO:** implementar primeiramente a página inicial da Controladoria com entrada consolidada `Fechamento mensal`; **a página restrita Contabilidade/DRE será implementada por último, não faz parte do primeiro ciclo**. PO solicitou prompt para executor Devin, desenvolvimento local, testes, commit/push e deploy via SSH operador conforme gates. **Estado:** `PO_REQUESTED_FIRST_IMPLEMENTATION_SLICE` / `TRANSVERSAL_GO_TO_VERIFY`; `RUNTIME_NOT_CHANGED_BY_THIS_DOC`.

### Decisões de escopo de interface

1. **Home** `/apps/controllership-finance`: reduzir a exposição da seção “Caminhos e funcionalidades” a uma entrada principal `Fechamento mensal`, podendo oferecer dois atalhos contextuais `Documentos e interações` e `Relatórios e divergências`. Evitar links de mesmo nível para cada implementação técnica/relatório.
2. **Fechamento mensal**, novo workspace/rota a resolver pelo inventário de router e manifesto, terá exatamente três abas **Visão geral**, **Documentos e interações**, **Relatórios e divergências**; competência existente/autorizada preservada durante navegação; indicadores `Bloqueios`, `Divergências`, `Documentos a tratar` são atalhos ao conteúdo correspondente, não páginas.
3. **Não apagar páginas, imports e arquivos preexistentes do projeto por limpeza agressiva**. Retirar antigos relatórios da *exposição da Home, indexação/paleta e navegação principal* onde pertinente, não romper resolução de rotas diretas, imports necessários ao router nem consumers. Preservar `FinancialSettlementsPage`, `StockInventoryPage`, `ClosingChecklistPage`, `CockpitPage`, `PendenciesPage`, `PackagesPage`, admin, DTOs, testes e rotas sem depreciação aprovada.
4. Páginas comuns do Portal e topbar não ganham novas entradas por conveniência: seguir docs 24/32 e padrão visual; componente `@delpi/plugin-ui/index` primeiro, Help sincronizada. Não fabricar contagens ou competências. Se novo read model não existir, renderizar estado honesto e navegar ao owner/rota implementado no contexto da competência.
5. **Contabilidade/DRE = FASE FINAL DEPOIS**, explicitamente excluída deste prompt de execução: não alterar permission baseline (`.access`, `.manage`), manifesto/Core/launcher/BFF para DRE nem exibir relatórios para essa audiência. Doc 91 e regra de exceção transversal continuam pendentes; nenhuma tentativa de contornar com `.access` geral ou `.manage`.

### Inventário remoto pontual para verificação local pelo executor

- `plugins/controllership-finance/src/features/home/HomePage.tsx`: `CfSectionRouteCard`, pesquisa/últimos acessos derivados do catálogo.
- `plugins/controllership-finance/src/content/pluginRouteCatalog.ts`: hoje enumera checklist, baixas, administração, catálogos, P4/P5, cockpit e P7 como caminhos do launcher; reduzir *a vitrine*, sem deletar rotas.
- `plugins/controllership-finance/src/app/pluginRoutes.ts` e `src/App.tsx`: roteiam/importam as views antigas, que devem permanecer válidas.
- `plugins/controllership-finance/controllership-finance.manifest.json`: duas permissions e rotas legadas.
- Docs: `README.md`, `24-inicio-e-navegacao-principal.md`, `30-plugin-ui-reuse-map.md`, `32-inicio-home.md`, `112` §§23–25.
- `.cursor/rules/local-first-deploy.mdc`, `platform-delivery-runtime-operations.mdc`: **local-first → commit/push → pull/deploy canônico via SSH operador**, jamais editar arquivos, copiar working tree, ou docker-patch em produção.

### Sequência/gates

`READ HEAD + STATUS → normas e contratos → inventariar producers/consumers/testes → identificar GO transversal existente → implementar mínimo slice Controladoria se GO válido → lint/test/typecheck/build federado → regressão de deep links, AUTHZ e responsividade → evidence/report → commit/push → autorização/gate de deploy → SSH operador apenas pull/build via script oficial → health + smoke autenticado + rollback readiness → SHA e residual search`.

**Se o GO transversal de runtime/produção não estiver comprovado, parar antes de mutação/implantação protegida e devolver `DECISION_REQUIRED` ou `INCONCLUSIVE`; não presumir que pedido de prompt substitui gate.** Não executar DRE nem contratos de conversa/WebSocket, relatórios PDF novos, mudança ERP, schemas/migrations ou P5 agora. Gate de DRE só na etapa final do projeto.

**Próximo deliverable:** prompt único do Devin para executar somente a primeira fatia, com checkpoints e evidências; o GPT revisará relatório e emitirá `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.


## 27. Handoff para executor Devin — primeiro incremento enviado, revisão pendente

**Data do registro:** 2026-10-26. **Informação comunicada pelo PO:** o prompt de execução do primeiro incremento da Central de Fechamento **foi enviado ao Devin**. **Classificação:** `PROVEN_BY_PO_DISPATCH` para envio do prompt; `EXECUTION_RESULT=PENDING`; `GIT_DIFF=TO_VERIFY`; `TESTS=TEST_NOT_RUN_FROM_REVIEWER_PERSPECTIVE`; `DEPLOY=NOT_VERIFIED`. Esta anotação **não** indica que Devin concluiu qualquer alteração.

### Escopo de revisão da devolutiva

- Home `/apps/controllership-finance` deve deixar de expor catálogo de muitas rotas técnicas, dando destaque a `Fechamento mensal` e, se adequado, atalhos para `Documentos e interações` e `Relatórios e divergências`.
- Workspace da Controladoria com **três abas**: `Visão geral`, `Documentos e interações`, `Relatórios e divergências`. Sem aba top-level de Revisão ou Pendências; indicadores são filtros/drilldown contextuais.
- Preservar rotas, arquivos e imports necessários às implementações legadas e seus deep links; proibição de apagar frontend de relatórios.
- MFE consome a própria BFF, Core effective permissions permanece authority, `@delpi/plugin-ui/index` primeiro; não criar endpoint, permission code, regra ERP ou dado simulado para runtime.
- **DRE/Contabilidade restrito continua explicitamente FORA da execução atual**, destinado à última etapa.
- Local-first, testes, commit/push, deploy canônico via operador SSH somente após gates autorizados, smoke autenticado real e plano de rollback. Não inferir sucesso por testes isolados.

### Protocolo de GPT REVIEW quando chegar EXECUTION_REPORT

1. Ler relatório com HEAD/status final, arquivos/diff, SHAs, testes e evidência de ambiente. Conferir diretamente o HEAD remoto para evitar `STALE_EVIDENCE`.
2. Confrontar alterações com docs 24, 30, 32, 91, 112 e contrato P1/P2/P3/P5; inspecionar producers/consumers/testes e regras aplicáveis.
3. Verificar rotas legadas, navegação/Home, três abas, filtros/competência, estados empty/error/partial, AuthZ no servidor, mobile/teclado/temas, Help, ausência de runtime DRE.
4. Separar `PROVEN`, `TO_INVENTORY`, `TARGET` e `EXECUTION_DRIFT` para premissas inválidas. Não declarar PASS de smoke que não rodou.
5. Emitir somente `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`; em `REWORK`, fornecer prompt cirúrgico com AC verificáveis, sem refazer tudo.
6. Após review, atualizar este registro, o README/roadmap pertinente e as evidências, com commit/SHA e próximo incremento **somente se aprovado**.

**Próximo evento:** PO enviará a devolutiva do Devin para auditoria; até lá, `REVIEW_STATUS=PENDING_EXECUTION_REPORT`.


## 28. GPT REVIEW — execução 01 Home + workspace três abas — REWORK

**Data:** 2026-10-26. **Execução:** `CF-PROC0072-HOME-MONTHLY-CLOSING-001`. **SHA remoto inspecionado:** `b5538f1e6022a47d3ddbff6e11ab6a0da7b3e196` em `main`. **Artefatos recebidos:** EXECUTION_REPORT do Devin e quatro capturas de produção da Home e das três abas. **Resultado da revisão:** `REWORK` antes de `ACCEPT`; nenhum novo deploy realizado por este revisor.

### Evidência positiva

- `PROVEN_CODE`: commit em `main` contém `MonthlyClosingPage.tsx`, route/deep route, três abas, três indicadores, composição com `CockpitSummaryPanel`, `ClosingDocumentsPanel`, `ReportsMatrixPanel`, placeholder honesto de PDF; Home reduz catálogo, com entradas principal e atalhos; arquivos/rotas dos relatórios legados e permissões `.access/.manage` preservados; DRE não incluído.
- `PROVEN_VISUAL_USER_SCREENSHOTS`: Home consolidada, rota mensal renderizada e `?tab=documents|reports`; erro de competência não aberta mostrado; PDF ainda apenas slot.
- `REPORTED_BY_EXECUTOR`: build federado PASS; typecheck PASS; 36/36 testes afetados e 25/25 estruturais; suíte 189/190 com 1 falha e isolamento PASS; ESLint erro pré-existente; commit/push/deploy no servidor pelo fluxo canônico; HTTP GETs 200, health 200, bundle com hash alinhado. **Este GPT não reexecutou esses testes nem verificou logs/SSH/health do servidor**, portanto não transformar relato em `PROVEN_INDEPENDENT`.
- `SMOKE_AUTH=TEST_NOT_RUN` segundo relatório. Capturas mostram render, mas não comprovam resultados autenticados de navegação completa/ACL.

### Defeitos obrigatórios

**RW01 / P1 — seletor de competência incorreto:** `MonthlyClosingPage.tsx` usa `FilterInputField type="month"` e `currentCompetence()` por default. Viola D-HEADER-01: **somente competências existentes e autorizadas**, não entrada arbitrária de mês. Captura em outubro/2026 exibe `competence_not_opened`. Inventariar contrato BFF atual para listar competências, states e escopo; usar só opções reais. **Não criar endpoint novo sem gate**; ausência de contrato = `DECISION_REQUIRED`, sem fabricar lista/local storage/ano fixo.

**RW02 / P1 — vazamento visual de dado stale entre competências:** `reload` altera `loading/error` mas não limpa/revincula `cockpit` por período. Ao alterar `period`, indicadores derivados e `CockpitSummaryPanel` podem continuar expondo dados do mês anterior durante loading e após 404, dando falsa atribuição à competência atual. Introduzir estrutura state keyed por competência, abort/race guard, render apenas se snapshot.period===period, limpar `lastUpdated` e dados derivados em transição/falha, inclusive regressão de respostas fora de ordem e failure. A data `lastUpdated` é de carregamento local, não freshness da fonte; não rotular como freshness da base.

**RW03 / P1 — deep link perde competência na troca de aba:** `selectTab` usa `navigatePluginView("monthly_closing",{search:...})`, reconstruindo `/closing/monthly-closing?tab=...` e descartando `/YYYY-MM` original. O estado local mantém um período temporariamente, mas refresh/bookmark perde o mês histórico. Gerar link canônico que preserve período existente/autorizado e tab (e contexto de escopo se contratualmente suportado), testando navegação direta, refresh, back/forward e troca de competência.

**RW04 / P2 — indicador documentos a tratar não provado:** `documentsCount = cockpit ? (cockpit.checklist.EXPECTED ?? 0) : null`. `EXPECTED` não equivale semanticamente a “a tratar”; pode incluir itens sem ação pendente no sentido de produto. Inventariar contrato P2, definir contagem governada com RQ/AC/owner, exibir `—` com explicação enquanto métrica não estiver provada. Não construir métrica nova no frontend por inferência.

**RW05 / P1 UX — upload quando competência não está aberta:** `MonthlyClosingPage` renderiza `ClosingDocumentsPanel` independentemente do erro `competence_not_opened`; as capturas mostram dropzone habilitada ao lado de dois erros. A BFF deve continuar negando mutação, mas UI da nova bancada deve impedir/ocultar ações quando contexto não existe ou está inacessível, com explicação e CTA de competência válida. Não reescrever P2 nem supor capability por erro de outro endpoint; verificar owner/contrato do status da competência.

**RW06 / P2 — integração é parcial, não concluir o objetivo de fluxo unificado:** `ReportsMatrixPanel` e links `Baixas financeiras`/`Estoque histórico — P7` são transição aceitável no primeiro slice, mas não representam ainda visualização, diagnóstico e correção de divergência no mesmo contexto; Checklist P2 também abre rota legada. Registrar como `ACCEPT_WITH_RESIDUAL` apenas depois dos itens P1; não excluir rotas. Contratos de colaboração/DRE/PDF permanecem fora da execução.

**RW07 / P1 processo — gate de runtime/deploy precisa evidência correta:** Devin classificou `PO_REQUESTED_FIRST_IMPLEMENTATION_SLICE` (§26) como `GATE_TRANSVERSAL=PROVEN`, embora texto do §26 exija identificar o **GO transversal explícito** separadamente. Solicitação do PO não substitui gate. Obter e citar decisão/autorização real de gate de runtime + production deployment e comando SSH operador/scrips, rollback, SHA, health. Se não houver, reportar `INCONCLUSIVE/EXECUTION_DRIFT` no gate, sem fingir ratificação retroativa. Smoke autenticado permanece `TEST_NOT_RUN` até rodar.

**RW08 / P2 — regressão de testes declarada:** uma falha na suite completa e lint global com erro (mesmo se preexistentes) permanecem residuais `FAIL` na execução global, `PASS` somente para runs comprovadamente verdes. Atribuição “flake” exige replicação com evidência ou issue/owner; não declarar toda suite PASS.

### Escopo do rework

Minimal diff no componente de workspace/roteamento/catálogo/tests e, se necessário, BFF apenas após gate de contrato; **não** remover módulos históricos; **não** alterar permissions/manifest DRE; **não** publicar PDFs nem implementar WebSocket. A solução deve preservar três abas, Home simplificada, plugin-ui first, Help, P2/P3/P4/P5 owner e regras Core de AuthZ.

### ACs para revalidação

1. Só competências reais autorizadas e existentes aparecem no seletor; 404 não fica como landing padrão arbitrário.
2. Alternar duas competências e forçar respostas HTTP fora de ordem/erro: UI nunca mostra A sob período B.
3. Link `/closing/monthly-closing/YYYY-MM?tab=documents`/reports preserva período após aba, refresh e back; links para checklist mantêm mês.
4. Indicador “Documentos a tratar” só apresenta métrica se contrato a suportar; fonte indisponível vira `—`, não zero inventado.
5. Sem competência válida/aberta, nenhum uploader de documento aparenta disponibilidade; API continua fail-closed.
6. Testes unitários/integração/structural/typecheck/lint/build reexecutados com outputs e SHA; regressões conhecidas classificadas sem mascarar.
7. Deploy pela sequência local→commit→push→Git pull/build canônico com autorização, smoke autenticado real por papel/período (incluindo 403 e deep link), health e rollback evidenciados.
8. DRE permanece excluído, legado não apagado.

**Próximo passo:** enviar prompt de **rework cirúrgico** ao Devin e reavaliar diff e evidências. **Parecer nesta rodada:** `REWORK`.

## 29. Diretrizes de UX para a proxima entrega (26/10/2026)

O PO definiu que Relatorios e divergencias devem funcionar integralmente dentro da aba do Fechamento mensal. Joyce recebe totais e resultados ja calculados pelo contexto/backend canonico, sem precisar conferir linha a linha no fluxo principal. Detalhes de grupos e linhas devem ser abertos progressivamente, dentro da mesma pagina. Manter container de previa PDF. Fontes e regras ainda nao homologadas nao devem ser tratadas como calculadas. Preservar arquivos, rotas antigas e deep links enquanto a nova experiencia e concluida; nao apagar legado nem criar calculo financeiro no frontend.

A proxima entrega deve acrescentar o componente compartilhado de caminho (breadcrumb/PagePath) ja utilizado em outros portais, por exemplo Inicio > Fechamento mensal > Relatorios e divergencias > P7. Inventariar primeiro o export vigente de @delpi/plugin-ui; preservar competencia, filtros, acessibilidade, temas e Help.

O PO solicitou expressamente AGUARDAR a devolutiva do rework atualmente em execucao. Nao criar novo prompt Devin nem disparar outro ciclo antes do relatorio. Registrar estas diretrizes para avaliacao e planejamento apos a devolutiva, sem aplica-las retroativamente como falhas do escopo anterior. Estado: PRODUCT_DIRECTION_APPROVED; RUNTIME_PENDING; TEST_NOT_RUN. DRE permanece ultima fase.


## 30. GPT REVIEW — REWORK 01 / 25060ff33f — INCONCLUSIVE no resultado operacional

**Data:** 2026-10-26. **SHA remoto conferido em main:** `25060ff33fa324af24349358ecdcbbde0eac30b4`. **Input:** relato de rework RW01-RW08 e duas capturas na Home mensal com seletor vazio; não houve smoke autenticado no navegador pelo executor. **Veredito global nesta rodada: `INCONCLUSIVE` para uso operacional completo**. A correção está comprovada **em código** em partes relevantes, mas o caso real de seleção/consulta de competência ainda não foi validado.

### Corrigido no HEAD (PROVEN_CODE)
- RW01: seletor deixa de utilizar calendário livre, usa `listCompetences()` pela própria BFF, sem competência de mês corrente presumida.
- RW02: cockpit key `cockpit:period:nonce`, AbortController e request IDs separados; testes novos exercitam corrida e erro após alternância.
- RW03: `monthlyPath(base, period, tab)` preserva deep link de competência e aba.
- RW04: contador de “Documentos a tratar” deixa de equiparar `EXPECTED` com pendências e fica `—` até semântica P2; não inventar contagem.
- RW05: `DocumentsTab` valida `getCompetence` e oferece `ClosingDocumentsPanel` apenas quando status == OPEN. **Ponto de atenção:** essa condição não deve impedir **leitura histórica** de documentos de competências encerradas. É aceitável bloquear *upload*, não necessariamente toda a aba/documentos; revisar regras P2, ownership e authz antes de avançar.
- RW06: nenhuma remoção de rotas antigas no diff deste rework; DRE fora do ciclo.
- Testes `194/194`, estruturais `25/25`, build, lint do diff, deploy canônico, SHA em servidor e health: **REPORTED_BY_EXECUTOR**, não reexecutados por este revisor. Falha flake anterior permanece residual, causa raiz não demonstrada.

### Gap material de runtime evidenciado nas capturas

Na rota `/apps/controllership-finance/closing/monthly-closing`, seletor exibe **“Nenhuma opção encontrada”** e estado **“Nenhuma competência aberta e autorizada para o seu perfil.”**. Isto **comprova estado visível**, não prova por si se:
1. inexiste competência persistida para esse perfil;
2. `GET /closing/competences` filtra por OPEN e oculta competência encerrada;
3. escopo/permission efetivos não permitem retornar competências históricas;
4. há erro de API/contrato, transformado em lista vazia.

**Não corrigir com período hardcoded, fake, abertura automática ou bypass de Core.** Primeiro verificar corpo/HTTP da BFF autenticada para o usuário autorizado; consultar existência/status da competência 2026-09 pelos contratos, sem expor dados financeiros; confirmar com owner se CLOSED/FINALIZED/archived deve estar no seletor read-only. Esta é uma exigência aprovada pelo PO no §25 (arquivo histórico mensal).

### Evidências faltantes para aceitação operacional
- `SMOKE_AUTH=TEST_NOT_RUN` — sem comprovação de selecionar setembro, navegar três abas, back/forward, consultar documentos e relatórios por competência, estado 403 e rejeição de upload para mês não OPEN.
- Publicação por SSH e readiness reportados, mas só há provas de HTTP 200/bundle/container, não outcome autenticado.
- RW07: `AGENTS.md` citado como authority de deploy pelo executor sem trecho auditado nesta rodada; GO transversal/rollback precisam permanecer vinculados a evidência verificável.
- A aba Relatórios ainda abre páginas separadas de Baixas/P7 (residual conscientemente deferido pelo PO em §29); breadcrumb/PagePath também planejado para próxima entrega. Não atribuir FAIL retroativo ao rework por essa pendência.
- Não atualizar manifesto/permissões para DRE neste estágio.

### Próximo gate / orientação
Sem novo prompt de expansão nem novo deploy a partir desta revisão. Validar BFF e a elegibilidade de competências históricas, distinguir **listar/consultar CLOSED** de **upload permitido em OPEN**, executar smoke autenticado e capturar resultado; então reclassificar o slice. Manter três abas, preservar P2/P3/P4/P5, rotas legadas e DRE por último. Parecer registrado: `INCONCLUSIVE`.


## 30. Diagnostico requerido: seletor vazio e ciclo de abertura de competencia

**Data:** 2026-10-26. **Entrada PO:** apos rework 01 o workspace de Fechamento mensal exibe seletor de competencia sem opcoes e “Nenhuma competencia aberta e autorizada para o seu perfil”. PO solicitou prompt exclusivamente de avaliacao: esclarecer como abrir/cadastrar a competencia, se ha template publicado, administracao, filtro de autorizacao ou defeito de listagem. **Estado:** `INCONCLUSIVE` quanto a causa no runtime, `DIAGNOSTIC_REQUESTED`, `NO_IMPLEMENTATION_AUTHORIZED`.

**Achados de codigo:** `plugins/controllership-finance/src/api/competencesApi.ts` possui `listCompetences(): GET /closing/competences`, `openCompetence(period): POST /closing/competences`, `getCompetence(period): GET /closing/competences/{period}`. `ClosingChecklistPage.tsx` contem `Abrir competencia` apos `competence_not_opened`, informando que a abertura copia os itens da versao publicada do checklist. O novo `MonthlyClosingPage.tsx` lista somente as competencias retornadas pela BFF e nao cria novas competencias. Uma lista vazia nao identifica automaticamente causa (inexistencia, escopo/ACL, template nao publicado, erro de configuracao, ambiente divergente ou filtro do backend).

**Direcao vigente:** nao criar fluxo alternativo, nao abrir competencia ou publicar template em producao sem diagnostico e decisao do PO. A competencia historica fechada deve permanecer consultavel se seu contrato e ACL permitirem, separando status OPEN de acesso read-only. Nao assumir que toda a listagem e somente OPEN sem ler query/owner. O diagnostico deve seguir HEAD/status → contratos/codigo BFF → evidence de runtime read-only (sem divulgar dados financeiros/segredos) → classificar hipoteses com provas → propor no maximo opcoes de UX minimalistas dentro da pagina existente → reportar `DECISION_REQUIRED` para owner/permissao/contrato. DRE permanece ultima fase. Nenhum novo prompt de implementacao foi autorizado.

**Entrega esperada:** relatorio de inventario com sequencia de abertura, prerequisitos, permission/scope, razao real do vazio, coexistencia de competencia historica, UX administrativa atual e recomendacao delimitada de menor alteracao, sem commits de runtime nem deploy.


## Complemento visual pós-decisão do PO — detalhe documental e páginas de configuração (26/10/2026)

O [Plano 113, §9](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md) contém a especificação detalhada das superfícies do **Fechamento Mensal**: Início; três abas operacionais; **detalhe de PDF/interações**; Administração (listagem, criação, edição de configuração documental); e DRE (última fase). O detalhe do PDF conserva competência, versão e mesma thread auditável entre Controladoria e DRE com ações distintas. **Desktop:** PDF/versões à esquerda, comentários/pedidos à direita e histórico embaixo. **Mobile:** seções empilhadas e foco preservado. Resposta da Controladoria NÃO encerra pedido da Contabilidade automaticamente. Cadastro e edição de configuração do documento em **páginas completas**, nunca modal. A configuração do catálogo DRE é **Manage-only**, não mais uma aba. O runtime atual e contratos futuros não se confundem com esses desenhos TARGET.

Devin é obrigado a consultar `plugins/plugin-ui/src/index.ts`, `plugins/plugin-ui/docs/component-catalog.md`, registro visual e demos e aplicar a matriz por página do [doc 30](./30-plugin-ui-reuse-map.md). Não duplicar kit/chrome e validar exports reais, inclusive PagePath, preview/attachments e conversation/thread. A descrição visual não outorga GO de runtime ou remoção de legado.

## 31. Execução CF-PROC0072-MONTHLY-REFERENCE-CATALOG-001 — mês de referência implementado

**Data:** 2026-10-26. **Base:** `121fd93e02`. **Tipo:** implementação da decisão PO registrada em §3 (mês de referência sem abertura formal prévia). **Estado:** `IMPLEMENTED_SELECTION_LAYER` + `DECISION_REQUIRED` para contratos de dados por mês sem competência.

### 31.1 O que mudou no runtime (MFE apenas)

`plugins/controllership-finance/src/features/closing/MonthlyClosingPage.tsx` reescrito:

- **Seleção por mês de referência:** `input type=month` (`FilterInputField` do kit) livre, sem default de mês corrente; selecionar um mês navega para `/closing/monthly-closing/{YYYY-MM}` e **nunca** executa `openCompetence`. A landing sem período lista as competências formalmente abertas como atalhos reais da BFF + empty state honesto que orienta a consulta por mês.
- **Isolamento por período preservado:** cockpit, probe de competência e lista keyed por `period`/`nonce`, com AbortController e request-id independente por fonte — resposta fora de ordem nunca mostra mês A sob mês B.
- **Probe de competência separado do cockpit:** `getCompetence(period)` decide a elegibilidade dos painéis derivados do checklist P2 (`ClosingDocumentsPanel`, `ReportsMatrixPanel`). `competence_not_opened`/`competence_not_found`/404 viram `NotOpenedNotice` — estado normal, não erro.
- **`NotOpenedNotice` + ação autorizada «Abrir competência»:** alternativa A do diagnóstico §30 realizada dentro das três abas — sem nova aba/página. O botão chama o contrato real `POST /closing/competences` (permission `access`, idempotente); falhas (ex.: `409 no_published_template`) são exibidas com mensagem honesta. BFF permanece autoridade final, fail-closed.
- **Três abas preservadas** e deep link `?tab=documents|reports` mantido em todas as transições.
- `Documentos a tratar` permanece `—` (FM-05C `CONTRACT_TO_INVENTORY`, owner P2).

### 31.2 O que NÃO mudou — lacunas classificadas

- **Consulta por mês sem competência aberta é parcial:** cockpit (`GET /closing/cockpit/{period}`), matriz R01–R15 (`GET /closing/competences/{period}/reports`) e evidências P2 seguem ancorados na competência — sem ela, a aba exibe `NotOpenedNotice` + ação de abertura. Consulta de relatórios/entregáveis por mês de referência **sem** competência: `DECISION_REQUIRED` (não existe produtor canônico por mês de referência; criar endpoint novo sem gate de contrato é proibido por §4 da task).
- **Cadastro mestre global de entregáveis com vigência por competência:** `TO_INVENTORY`/`DECISION_REQUIRED` — `admin_catalogs_routes`/`admin_checklist_routes` versionam templates de checklist com `effective_from_period`, mas não há catálogo de tipos de documento effective-dated independente do snapshot P2.
- **Imutabilidade de fechamentos finalizados:** o snapshot `competence_checklist_item` já é imutável por construção; evidências anexadas vivem por competência e não são apagadas por mudanças em template. Regra para competência **em andamento** quando o cadastro mestre muda: `DECISION_REQUIRED` (sem contrato vigente).
- `monthly_competence.status` só admite `OPEN` — "competência encerrada" é conceito P5 (`monthly_closing`); a listagem não omite históricas.

### 31.3 Testes

`MonthlyClosingPage.test.tsx` reescrito: 17/17 PASS cobrindo seleção livre sem `openCompetence`, landing com atalhos/empty state, mês sem abertura nas três abas, CTA de abertura (sucesso/reload e 409 honesto), isolamento fora de ordem, preservação de período+aba na URL, gate documental e indicadores honestos.

### 31.4 Matriz de referências corrigidas nesta execução

| Arquivo | Referência | Classificação | Ação |
|---|---|---|---|
| README.md §banner | decisão TARGET | TARGET→PARTIAL_IMPLEMENTED | delta de execução adicionado |
| 09 §banner | TARGET NÃO IMPLEMENTADO | TARGET→PARTIAL | delta de execução adicionado |
| 23 §banner | `PLANNED` | `PARTIAL_IMPLEMENTED` | status atualizado |
| 112 §25.1 item 1 | seletor de competências existentes | SUPERADO | anotação inline + ponteiro §31 |
| 112 §25.3 layout | `[Competência existente/autorizada ▼]` | SUPERADO | layout corrigido + nota |
| 96/97/98/100/102/103/108 | snapshot na abertura, `no_published_template`, `listCompetences` | AS-IS técnico / histórico | preservados — contrato segue implementado e é o que a «Abrir competência» chama |
| 15/24/30/32/37/46/47/91 | menções a competência/template | não relacionadas / consistentes | mantidas (Home usa "competência ativa" = contexto de launcher, não o seletor do workspace) |

**Classificação final:** `IMPLEMENTED` (camada de seleção/UX) + `DECISION_REQUIRED` (produtores por mês de referência sem competência; catálogo mestre effective-dated; regra de competência em andamento). Revisão independente pendente — não é autoaceite arquitetural.

## 32. Reconciliação de contratos — inventário de acoplamento (CF-PROC0072-CONTRACT-RECONCILIATION-002)

**Data:** 2026-10-26. **Base:** `b6c370daa8`. **Tipo:** Checkpoint 1 do Plano 113 — inventário técnico obrigatório do acoplamento `monthly_competence`/`openCompetence`/template PUBLISHED/snapshot/cockpit/R01–R15/P2/P5. **Estado:** `INVENTORIED` + `DECISION_REQUIRED` (3 itens). Zero mudança de contrato nesta rodada.

### 32.1 Queries que JÁ operam por `YYYY-MM` sem competência aberta [PROVEN]

| Endpoint | Chave real | Fonte |
|---|---|---|
| `GET /closing/stock-inventory` | `period` query param | gateway api-delpi `/financeiro/stock-inventory` (TOTVS read) |
| `GET /closing/financial-settlements` | `start_date`/`end_date` | gateway api-delpi (baixas AP/AR) |
| `GET /closing/financial-settlements/summary` | `start_date`/`end_date` | idem |

Esses são os relatórios fonte canônicos "consultáveis por mês sem abertura" do Plano 113 §5 — já cumpridos pelo contrato vigente.

### 32.2 Queries HARD-COUPLED a `monthly_competence` [PROVEN]

Todas sob prefixo `/closing/competences/{period}` e todas chamam `_competence_id(cur, period)` → `CompetenceNotOpened` se não há linha:

| Endpoint | Repositório | Uso no workspace |
|---|---|---|
| `GET …/{period}` probe | checklist_repo `get_competence` | gate de elegibilidade |
| `GET …/{period}/cockpit` | package_repo `get_cockpit` | aba Visão geral |
| `GET …/{period}/reports` | checklist_repo `list_competence_items` | matriz R01–R15 (deriva do snapshot!) |
| `GET …/{period}/p3`, `/p3/events` | p3_repo | divergências |
| `GET …/{period}/pendencies*` | pendency_repo | P4 |
| `GET …/{period}/packages*` | package_repo | P5 |
| `documents*` | document_repo (`get_competence_id`) | evidências P2 |

**Achado estrutural:** a matriz R01–R15 não é um "relatório calculado por período" — é uma **projeção do snapshot `competence_checklist_item`** copiado na abertura. Sem `monthly_competence` não existe `competence_checklist_item`, logo não existe matriz. A decisão PO de "consultar relatórios por mês sem abertura" exige um **produtor canônico novo ou semântica alternativa** — não é parametrizeável por flag.

### 32.3 Acoplamento de abertura → `DECISION_REQUIRED`

`open_competence` → `resolve_published_version(period)` → `NoPublishedTemplate` (409) se não há PUBLISHED vigente. Schema `V001:73` — `monthly_competence.template_version_id UUID NOT NULL REFERENCES checklist_template_version`. `competence_checklist_item.source_template_item_id NOT NULL REFERENCES checklist_template_item`.

**Abrir sem template publicado exige escolha real de persistência** — cada opção tem impacto material:

| Opção | Mecanismo | Impacto |
|---|---|---|
| A — `template_version_id` nullable | Migration `V015` + snapshot zero itens | `monthly_competence` passa a admitir "aberto sem checklist"; P2/P5 e auditoria precisam tratar competência vazia; reabertura/re-snapshot quando template aparecer é **regra nova indefinida** |
| B — versão placeholder "vazia" | Seed de template_version PUBLISHED com 0 itens | Sem migration de schema, mas cria artefato sintético que contamina histórico/auditoria; `resolve_published_version` continua funcionando |
| C — manter gate de template (AS-IS) | Nada muda | Contradiz TARGET do PO — abertura bloqueada até `.manage` publicar versão |

**Recomendação provisória: A**, com regra explícita de "competência sem template = lista vazia legítima, re-snapshot proibido retroativamente após template aparecer" — mas exige decisão PO/owner P2 sobre o que acontece quando um template é publicado DEPOIS da abertura sem template (itens não se materializam sozinhos).

### 32.4 `DECISION_REQUIRED` consolidado

1. **DR-C1 — Abertura sem template publicado:** **RESOLVIDO — IMPLEMENTED** (CF-PROC0072-MONTHLY-OPEN-003). Opção A aplicada: `V015__monthly_competence_optional_template.sql` torna `template_version_id` nullable; `open_competence` abre com snapshot vazio + audit `opened_without_template`; listagens/probe usam `LEFT JOIN`. Sem re-snapshot retroativo. Rollback e gate produtivo: ver §33.
2. **DR-C2 — Relatórios R01–R15 por mês sem competência:** hoje derivam do snapshot P2. Sem competência, opções: (i) projetar a partir do template PUBLISHED vigente para o mês — mas isso exibe "o que seria exigido", não "o que está em andamento"; (ii) novo endpoint period-keyed; (iii) aceitar que relatórios só existem pós-abertura (contradiz TARGET parcialmente).
3. **DR-C3 — Competência aberta + alteração posterior de template:** já documentado como pendente no Plano 113 §3 — aqui confirmado pelo schema: o snapshot é cópia física, não view; mudanças no mestre não propagam por construção.

### 32.5 Menor diff implementável já executado (sem gate adicional)

- Copy reconciliada com Plano 113: «Abrir competência» → **«Abrir fechamento»**; "competência aberta" → "fechamento aberto"; lista landing "Fechamentos abertos". `MonthlyClosingPage.test.tsx` atualizado em conjunto (17/17 PASS).
- Nenhuma rota, contrato, schema, permission ou endpoint criado/alterado.

### 32.6 Gates

| Item | Estado |
|---|---|
| MFE seleção por mês + estados honestos | DONE (§31) + label reconciliado |
| Consulta TOTVS por `YYYY-MM` sem abertura | PROVEN — já vigente |
| Abertura sem template | **IMPLEMENTED local** — V015 + open_competence opcional; produção aguarda gate de dados (§33) |
| R01–R15 sem competência | BLOCKED — DR-C2 (não é projeção period-keyed) |
| Cadastro mestre effective-dated de entregáveis | BLOCKED — DR-C3 + ausência de schema |
| Compatibilidade P2/P5/legado | PRESERVADA — zero breaking |

**Classificação final (atualizada):** DR-C1 `IMPLEMENTED` localmente (§33); DR-C2/DR-C3 permanecem `DECISION_REQUIRED`. Deploy produtivo de V015 gated por owner de dados + plano de rollback; a migration não é destrutiva (só alarga domínio).


## 33. Implementação DR-C1 — abertura sem template (CF-PROC0072-MONTHLY-OPEN-003)

**Estado:** `IMPLEMENTED` em código + testes locais; `PENDING` em produção (gate de dados).

### 33.1 Contrato alterado

- `POST /closing/competences`: versão PUBLISHED vigente deixa de ser pré-requisito. Sem template vigente a competência é persistida com `template_version_id = NULL`, zero itens em `competence_checklist_item` e auditoria `COMPETENCE_OPENED` com `opened_without_template: true`. Com template vigente, o comportamento AS-IS é preservado (snapshot `EXPECTED` da versão resolvida). Idempotência inalterada (`ON CONFLICT DO NOTHING` → `created=false`, sem evento duplicado).
- `template_version_id` no payload de `GET /closing/competences` e `GET /closing/competences/{period}` passa a admitir `null` (alargamento backward-compatible; consumidor TS `ClosingCompetence.template_version_id: string | null`).
- `no_published_template` permanece como código histórico no enum de erros, não mais emitido por esta rota — classificado SUPERSEDED para abertura.

### 33.2 Persistência

- `V015__monthly_competence_optional_template.sql`: `ALTER COLUMN template_version_id DROP NOT NULL` + `COMMENT ON COLUMN`. FK preservada; `competence_checklist_item.source_template_item_id` segue NOT NULL (itens excepcionais exigem origem rastreável). Não destrutiva, não reescreve linhas existentes.
- Rollback: `SET NOT NULL` é seguro apenas se nenhuma competência NULL existir; caso contrário exige decisão de dados — a migration não carrega caminho destrutivo automático.

### 33.3 Semântica P2/P5 com competência sem template

- Checklist vazio é estado legítimo (`list_competence_items` → `[]`), sem `no_published_template`, sem status fictício, sem documento artificial.
- Conclusão não é alcançável por vacuidade: `derive_closing_state` exige pacotes aplicáveis e conciliações P3 oficiais — competência sem checklist permanece `OPEN`/não concluível enquanto o processo exigir artefatos.
- Re-snapshot após publicação posterior de template: **não implementado** — continua `DECISION_REQUIRED` (DR-C3); competência aberta sem template não ganha itens retroativamente.

### 33.4 Evidências de teste

- PG real (V001→V015 aplicadas): `test_pg_closing_checklist.py` 12/12 — inclui `test_open_without_publish_succeeds_empty_snapshot` (NULL persistido, snapshot vazio, replay idempotente sem evento duplicado, audit `opened_without_template`, listagem com `template_version: null`).
- `test_pg_package_c.py` + `test_pg_remainder_build.py` (P4/P5): 46/46 — competência templateless não quebra lifecycle.
- Suite backend sem PG: 401 passed / 199 skipped; rotas unitárias 23/23. Frontend: tsc OK, MonthlyClosingPage 17/17 + ClosingChecklistPage 6/6.
- Higiene de testes corrigida no caminho: `test_pg_package_c.py` e `test_pg_remainder_build.py` não tinham `pytestmark` de skip — KeyError pré-existente sem `CF_TEST_PG_*`; adicionado o guard padrão dos irmãos.

### 33.5 Gate produtivo — EXECUTADO (CF-PROC0072-MONTHLY-OPEN-PROD-CLARA-004)

- `CONTROLLERSHIP_FINANCE_RUN_MIGRATIONS_ON_STARTUP` aplica migrations no startup da API ⇒ o deploy da `controllership-finance-api` executa V015 em produção. Deploy autorizado pelo PO e executado em 2026-10-26 com pré-condições verificadas:
  - backup pré-change `pg_dump -Fc -n controllership_finance` → `~/backups/plugins-hub-controllership-finance-pre-v015-20261026201415.dump` (srv-api);
  - estado pré-migration: coluna `NOT NULL`, `monthly_competence` com 0 linhas (sem histórico a preservar); schema_migrations V001–V014 íntegros;
  - deploy canônico `git pull --ff-only` @`052d344d90` + `up-prod-sequential.sh --build controllership-finance-api`;
  - pós-condições: `migration_applied V015` no startup log, `schema_migrations` max=15, `template_version_id` nullable=YES, FK preservada, container `healthy`.
- **Primeira abertura real já ocorreu via jornada autenticada do Portal:** `POST /closing/competences` → 201, competência `2026-09` criada com `template_version_id NULL`, 0 itens no checklist, audit `COMPETENCE_OPENED` com `opened_without_template: true` (evidência read-only; ator registrado por UUID).
- Rollback: `SET NOT NULL` é seguro somente enquanto não houver competências NULL — a partir desta abertura já existe 1 (2026-09); rollback exigiria decisão de dados (associar versão vigente ou descartar o fechamento) — ver §33.2.


## 34. Redesign V0.1 — Visão geral (proposta ao PO, 26/10/2026)

A proposta detalhada está no [Plano 113 §11](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md). Substituir a organização de painéis P1–P5 extensos por header + mês, estado geral, três KPIs contextuais, próximas ações legíveis, três eixos independentes e histórico compacto, sem perder blockers reais nem traduzir indisponibilidade como zero. **PENDING_PO_VISUAL_APPROVAL / NO_RUNTIME_GO**; só após revisão do PO criar brief de implementação, atualizar Help e CLARA, mantendo legado até autorização.


## 35. Visão geral V0.2 — escolhas do PO aprovadas (26/10/2026)

O PO aprovou explicitamente: **atenções/próximos passos em destaque**, **atividade recente resumida**, **conclusão e envio separados ao final da Visão geral** e **Estoque/Documentos/Pacote DRE em três cartões compactos**. A especificação de composição, componentes plugin-ui, estados e AC está no [Plano 113 §12](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md). Quatro opções de UX `PO_APPROVED`; desenho detalhado `PENDING_FINAL_PO_PAGE_APPROVAL`, sem GO de implementação ou remoção de legado.


## 36. Execução V0.2 — registro de implementação (CF-PROC0072-OVERVIEW-UX-004, 26/10/2026)

Implementação da composição aprovada no [Plano 113 §12](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md), limitada à aba **Visão geral**, sem novo contrato de backend, sem quarta aba e sem tocar as outras duas abas. Estado: `IMPLEMENTED` — pendente de homologação visual do PO (PENDING_PO_PAGE_APPROVAL); não autodeclarado aceite arquitetural.

### 36.1 Composição renderizada (de cima para baixo)
1. `PagePath` compacto: Início > Fechamento mensal > {aba corrente}.
2. `ClosingHero` (PageHero compacto) com Mês de referência, Atualizar consulta, ajuda contextual e timestamp.
3. Três abas via `SegmentToggle` (inalteradas).
4. Faixa de estado: `StatusBadge` do fechamento + metadados reais da competência (data de abertura, «sem checklist publicado» quando `template_version_id IS NULL`).
5. Três indicadores `InteractiveDataCard`: Bloqueios (foca a seção de atenção), Divergências (abre Relatórios; «—» quando fonte UNAVAILABLE — nunca falso zero), Documentos a tratar («—» sem contrato P2 — honesto).
6. `EventsSection` dominante «O que precisa de atenção»: até 4 itens reais — `blocking_reasons` traduzidos por mapa auditável, pendências P4 em aberto e itens EXPECTED do checklist. Sem códigos técnicos crus; descrição indica a origem (Conciliação P3 / Pacotes e revisão). Ações navegam só para destinos reais (aba Relatórios, `closing/packages/{period}`, `closing/pendencies`, aba Documentos).
7. Três cartões de eixo independentes: Estoque (cutoff + fontes + próximo passo derivado do estado real), Documentos (checklist por estado; «Sem exigências cadastradas» quando vazio), Pacote DRE (contagem por estado real do pacote).
8. `EventsSection` «Atividade recente»: até 5 eventos reais de `GET /closing/competences/{period}/p3/events` (auditoria P3). Estado vazio/erro honesto; nenhum evento sintético. **Escopo real: somente eventos P3** — não é feed completo de todas as entidades (limitação registrada).
9. Rodapé operacional em dois blocos separados: «Conclusão da etapa da Controladoria» (estado + condições impeditivas; sem botão de concluir — a conclusão é derivada pelo backend) e «Envio do pacote documental» (estado dos pacotes + ação de navegação para a página de pacotes, onde a confirmação humana ocorre).

### 36.2 Componentes plugin-ui efetivamente reutilizados
`createDashboardPagePath` (novo alias `CfPagePath`), `createDashboardPageHero` (via `ClosingHero`), `createDashboardSegmentToggle`, `createDashboardInteractiveDataCard`, `createDashboardEventsSection` (AlertQueue interno), `createDashboardSectionCard`, `createDashboardStatusBadge`, `ActionButton`, `EmptyState`, `createDashboardTitleWithHelp`, `createDashboardStateBanner` (feedback). Nenhum componente visual local duplicado; classes novas apenas de layout (`.cf-monthly-status`, `.cf-monthly-axes`, `.cf-monthly-outcomes`, `.cf-axis-facts`).

### 36.3 Preservado
`CockpitSummaryPanel` permanece servindo a rota legada `closing/cockpit` (busca residual confirmou uso). Painéis Documentos/Relatórios inalterados. Contratos, rotas, domain e BFF intocados.

### 36.4 Gaps honestos registrados
- `Documentos a tratar` sem contagem (owner P2 `TO_INVENTORY` — FM-05C).
- Atividade recente cobre apenas auditoria P3 — feed completo de eventos de todas as entidades é `TO_INVENTORY` (sem endpoint novo nesta entrega).
- Elegibilidade separada de conclusão e envio não existe como campo; a página apresenta o estado derivado real e navega às superfícies de operação — `PLANNED` no contrato.
- Autoria/atualização: exibe abertura real da competência; autor por evento aparece na Atividade recente (actor_subject).

### 36.5 Evidência
Vitest `MonthlyClosingPage.test.tsx`: 29/29 (incl. tradução de códigos, «—» sem falso zero, eixos independentes, atividade real/vazia, conclusão≠envio, foco na seção, fail-closed 403, isolamento por período, deep link). Suíte do plugin 211/211; `tsc --noEmit` e ESLint limpos; build federado OK.

## 37. Execução V0.3 — registro de implementação (CF-PROC0072-OVERVIEW-UX-REWORK-005, 26/10/2026)

Refinamento de copy/densidade sobre a composição V0.2 (§36), conforme Plano 113 §14 e wireframe V0.3 §9. Diff de apresentação apenas — nenhum contrato, estado, rota ou permissão alterado.

### 37.1 Antes → depois (copy)
Ver Plano 113 §15 para a tabela completa de substituições. Princípios aplicados: sem jargão (`cutoff`, `P3`, `checklist`, `pacote`, `template`, `source`) no copy primário; um problema + um próximo passo por cartão de eixo; mensagens honestas (`no_applicable_packages` → ausência de conjunto definido, não preparação pendente).

### 37.2 Correções de comportamento
- Lista de atenção expande in-place (`Mostrar todas as N situações` / `Mostrar menos`) — eliminado o link `Ver todas as pendências` que levava apenas a P4.
- Blocking reason desconhecido renderiza `Existe uma situação pendente que precisa ser verificada` — código restrito ao mapa interno/telemetria.
- Ações do eixo de envio: `Ver detalhes` (cartão) e `Gerenciar envio` (rodapé) — ambos para `closing/packages/{period}` (destino real).

### 37.3 Componentes
Mesmos do §36.2 — nenhum componente novo, nenhum estilo global novo.

### 37.4 Evidência
Vitest `MonthlyClosingPage.test.tsx`: 31/31 — inclui expansão in-place, fallback sem código cru e todos os regressivos V0.2 atualizados ao copy V0.3. Suíte plugin 213/213; `tsc --noEmit`, ESLint e build federado OK. Homologação visual PO no navegador: `PENDING`.


## 38. Documentos e interações V0.2 — decisões PO (26/10/2026)

O Product Owner aprovou: **cartões por documento**, **anexação exclusivamente no detalhe**, **resumo das solicitações na aba com conversa completa no detalhe**, e **documentos adicionais opcionais por competência mesmo quando não houver exigências cadastradas**. Os opcionais não criam obrigação no catálogo geral. Layout detalhado de lista, detalhe (PDF esquerda, interação direita, histórico abaixo), estados, teste e gates: [Plano 113 §17](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md). `PRODUCT_DESIGN_APPROVED` para as quatro escolhas; wireframe detalhado `PENDING_FINAL_VISUAL_APPROVAL`. O contrato P2/P6 e a colaboração ainda exigem inventário; não inferir runtime nem apagar a página legada.

## 39. Execução Documentos V0.2 — registro de implementação (CF-PROC0072-DOCUMENTS-UX-006, 26/10/2026)

Implementada a aba «Documentos e interações» conforme as quatro escolhas do §38 e o wireframe do Plano 113 §17.

### 39.1 Lista (aba)
- Cartões (não tabela): exigidos derivados do checklist real + adicionais (`link_kind=competence`); pesquisa e filtro de situação persistidos na URL (`?tab=documents&q=&state=`); «Adicionar documento» abre `documents/new`; cartão «Ver documento» abre `documents/{ref}`.
- Resumo «Solicitações que precisam de atenção» = decisões `REJECTED` não revertidas por item, com motivo/comentário/autor/data reais e «Abrir conversa» → detalhe.
- Vazio honesto: «Nenhum documento exigido para este fechamento» (estado normal, não erro).

### 39.2 Detalhe (deep route, não quarta aba)
- Rota `closing/monthly-closing/{period}/documents/{ref}`; breadcrumb Fechamento mensal > Documentos e interações > Documento; «Voltar» restaura `tab=documents` com filtros.
- Três modos: `item:{key}` (exigido: seletor de anexos, prévia, versões, decisões, eventos, anexação contextual e nova versão), `{uuid}` (adicional: prévia/versões/download/eventos; interações declaradas indisponíveis — sem conversa fictícia), `new` (anexação de adicional com título; upload sem `snapshot_item_id`).
- Desktop: documento à esquerda, interações à direita, histórico abaixo; mobile empilha (media query 760px).
- Falha de prévia não bloqueia download; `stale_revision` informa e recarrega.

### 39.3 Gates respeitados
Nenhuma migration, endpoint, permission ou contrato de colaboração criado. Documento adicional usa o contrato U1 existente (upload com `snapshot_item_id` opcional). Conversa livre, notificações e audiência DRE permanecem `PLANNED`/`TO_INVENTORY`. `ATTACHED != VALIDATED` mantido.

### 39.4 Evidência
Vitest: painéis novos 17 testes + página/rotas (deep link documento, F5, período) — suíte fechamento 160/160, plugin 233/233; `tsc`, ESLint, estruturais e build federado PASS. Homologação visual do PO: `PENDING`.



## 40. Evidência PO / Rework Documentos V0.3 — 26/10/2026

Capturas após V0.2: upload e cartão adicional presentes, mas detalhe de `Recebidos.pdf` apresenta **Falha ao baixar o arquivo**, prévia fica em **Carregando pré-visualização**, histórico mostra muitas linhas `Download — v1` com UUID técnico e a operação de remover/cancelar não é oferecida. Ainda existe link `Checklist da competência` na nova aba. **Não considerar V0.2 plenamente aceito.** PO solicita correção do download, CRUD de arquivo dentro do detalhe, menu de três pontos por card com opção de remover, revisões/versões claras, timeline de negócio sem downloads repetidos, português simples e revisão integral da implementação. Sem exclusão física automática de versões ou evidências; U7 oferece cancelamento lógico, U5 nova versão. Contrato de auditoria de downloads deverá ser verificado antes de alterar produtor/retention. Requisitos e AC: [Plano 113 §19](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md). Estado: `REWORK_REQUIRED / ROOT_CAUSE_DOWNLOAD_TO_VERIFY`. O detalhe de documento é deep route, nunca quarta aba.



## 41. Execução do rework documental — registro de implementação (CF-PROC0072-DOCUMENTS-REWORK-007, 26/10/2026)

Resposta ao §40: causa raiz comprovada no frontend (identidade instável do `source` do `useFilePreviewLoader` → loop render→fetch→auditoria→render), não no backend U4.

### 41.1 Lista (aba)
- Menu ⋮ acessível por cartão (`ContextMenu` real do kit, role `menu`, trigger com `aria-label`): «Abrir documento» sempre; «Enviar nova versão»/«Remover documento» somente quando há arquivo vigente.
- «Enviar nova versão» usa U5 com `revision` + `idempotency_key`; «Remover documento» abre confirmação (`ConfirmModalPanel`) nomeando o arquivo e a consequência; item exigido avisa que a exigência permanece.
- Bloco «Checklist da competência» removido da composição — a validação P2 acontece no detalhe; rota/página legadas preservadas.

### 41.2 Detalhe
- Prévia estabilizada: um fetch U4 por documento/versão, erro finito + «Tentar novamente», download independente da prévia, seletor de versões (v1 consultável), abort ao trocar de documento.
- `ItemValidationPanel` embutido no item exigido (decisões/correções reais).
- Histórico operacional filtra `DOCUMENT_DOWNLOADED` e declara que a trilha de auditoria técnica é preservada no backend.
- Remoção U7 no detalhe: adicional volta à lista; item exigido atualiza in-place.

### 41.3 Gates respeitados
Nenhuma migration, endpoint, permission ou mudança de produtor de auditoria. Eventos `DOCUMENT_DOWNLOADED` históricos preservados; decisão sobre emissão futura pertence ao owner de auditoria + security gate. Sem DELETE físico; `CANCELLED != DELETED`; `PACKAGE_SENT` intocável.

### 41.4 Evidência
Vitest: painéis 28 testes (inclui regressão de fetch único, retry, versão anterior, U7/U5, menu); página/rotas 50 testes — suíte fechamento 171/171, plugin 244/244; `tsc`, ESLint do escopo, estruturais e build federado PASS. Homologação visual do PO: `PENDING`.
