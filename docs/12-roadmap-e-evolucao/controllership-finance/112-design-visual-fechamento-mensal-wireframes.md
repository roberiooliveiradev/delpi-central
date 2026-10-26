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
