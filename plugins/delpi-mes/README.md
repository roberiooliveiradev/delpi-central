# Delpi MES — MFE

Microfrontend gerencial do Delpi MES, integrado à Minha DELPI por Module Federation.

## Arquitetura

```text
Portal → plugins/delpi-mes → JWT → delpi-mes-api → S2S → production-control-api
```

O MFE consome exclusivamente `/apps/delpi-mes-api`. Não contém regra industrial, não acessa Production Control/Pulse/cockpit e não armazena token.

## Rotas

- `/apps/delpi-mes` → monitoramento;
- `/apps/delpi-mes/monitoring?branch=01`;
- `/apps/delpi-mes/downtimes?branch=01&period=&from=&to=&workCenter=&reasonCode=&source=&classification=&sort=&page=&pageSize=&downtimeId=`;
- `/apps/delpi-mes/history?branch=01`;
- `/apps/delpi-mes/registrations` → hub de Cadastros;
- `/apps/delpi-mes/registrations/downtime-reasons` → catálogo de motivos de parada.

A filial permanece na URL: `01 · SC` ou `02 · ES` — exceto em Cadastros, que é uma área global e não carrega `branch`.

## Permissões

- `delpi-mes.access`;
- `delpi-mes.monitoring.view`;
- `delpi-mes.downtimes.view`;
- `delpi-mes.history.view`;
- `delpi-mes.view.filial-01`;
- `delpi-mes.view.filial-02`;
- `delpi-mes.downtime-reasons.manage` — área Cadastros (criar, editar, ativar e desativar motivos de parada).

O frontend usa as permissões apenas para experiência visual; o backend continua sendo a autoridade.

## Desenvolvimento

```bash
npm install
npm run test
npm run typecheck
npm run lint
npm run build
```

Para subir com a infraestrutura canônica:

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build delpi-mes
```

## Manifesto

`delpi-mes.manifest.json` está pronto para importação manual. Esta entrega não registra o manifesto nem busca token administrativo.

## Monitoramento Industrial MVP

A página de monitoramento consulta `/monitoring` a cada 5 segundos em um único fluxo centralizado. O polling pausa com aba oculta ou navegador offline e retoma imediatamente ao voltar. Cronômetros são derivados de `stateStartedAt` com correção pelo `referenceAt` do servidor, sem requests por segundo.

Cada snapshot gera N cards sem fan-out. O detalhe usa os dados do card e, apenas ao abrir um CT e somente com `delpi-mes.history.view`, consulta o histórico do dia daquele centro (`/work-centers/{workCenter}/timeline?branch=&from=`): todos os estados do dia corrente, inclusive de runs/OPs anteriores, com refetch pontual quando o estado do CT muda — sem polling próprio e sem N+1. A visão cobre exclusivamente runs ativos; não representa catálogo de máquinas nem saúde/offline da telemetria.

## Paradas — Etapa 1

A área **Paradas** (`/downtimes`) consulta os eventos reais de parada do MES via `GET /downtimes` do próprio BFF — sem chamada direta a outro contexto e sem cálculo local de fatos.

- Tabela paginada pelo backend (`page`/`pageSize`/`total`), com ordenação `recent|oldest` e desempate determinístico; paradas abertas e pendentes têm badges distintos («Aberta» em perigo, «Pendente» em atenção — encerrada e classificada são condições independentes).
- Filtros: período (Hoje, Últimos 7 dias — padrão —, Últimos 30 dias, personalizado), centro de trabalho, motivo, origem e situação da classificação. Trocar filtro reinicia na página 1; «Limpar filtros» usa o componente canônico.
- Fuso operacional: os dias civis de todos os períodos (presets e datas personalizadas) e a apresentação temporal do detalhe/timeline seguem o fuso canônico do MES — `America/Sao_Paulo` (mesmo `FACTORY_TIMEZONE` do Production Control e `timeZone` padrão de `plugin-ui/periodPreset`) — independente do fuso do navegador. Datas personalizadas cobrem dias civis inteiros e o «Até» é limite exclusivo do dia seguinte.
- Acesso direto: abrir `/apps/delpi-mes/downtimes` sem `delpi-mes.downtimes.view` exibe «Acesso não disponível» e não emite nenhuma consulta — nunca redireciona silenciosamente para outra área. A rota raiz continua indo à primeira área permitida.
- Isolamento por contexto: lista, detalhe e opções de filtro associam o estado à identidade da consulta (filial + parâmetros); ao trocar de filial, nenhum registro do contexto anterior é exibido — nem por um único render — e respostas atrasadas são abortadas/descartadas.
- Motivos e origens vêm de `GET /downtimes/filter-options` (leitura — não exige a permissão administrativa de Cadastros); motivos inativos permanecem filtráveis para preservar o histórico.
- Detalhe somente leitura em `DrawerShell`: identificador, CT, OP/operação, início/término/duração, origem, motivo/categoria, confirmação e observação. `downtimeId` na URL abre o deep link por consulta pontual escopada na filial — nunca filtra a listagem.
- Duração: encerrada = `endedAt − startedAt`; aberta = `startedAt` → relógio de referência do servidor (`referenceAt` + `useServerClock`), sem requisição por segundo. Datas inválidas nunca viram `0s` — exibem «—».
- Com `delpi-mes.history.view`, o detalhe carrega sob demanda a linha do tempo do dia do CT (`/work-centers/{workCenter}/timeline`); sem ela, o detalhe permanece e a timeline é omitida. Com `delpi-mes.monitoring.view`, «Abrir no monitoramento» navega ao CT pela rota oficial.
- Paradas autônomas sem OP/run são fatos legítimos: exibem «Sem OP vinculada»/«Não informado» — nunca são descartadas.
- Filtros, página e seleção persistem na URL (F5, voltar/avançar, compartilhamento); atualização é manual (sem polling). Requisições obsoletas são abortadas na troca de contexto.

Histórico gerencial completo e as etapas seguintes de Paradas (evidências, ações corretivas, exportações e indicadores OEE) continuam nas fases seguintes.

## Paradas — organização visual do cockpit

A página Paradas foi reorganizada em cockpit gerencial, sem alterar contratos nem cálculos — todo número continua vindo do BFF/Production Control:

- **Cabeçalho interno compacto**: título com ajuda contextual (encerramento e classificação são estados independentes), referência da última consulta (`referenceAt`), «Atualizar» e menu «Exportar» agrupado (overlay via `AnchoredPanelPortal` — Escape e clique fora fecham; nunca cortado pelos containers do MFE).
- **Filtros em níveis** (`FilterBarShell`): período rápido em `SegmentToggle` com os presets existentes (Hoje, 7 dias, 30 dias, personalizado), centro de trabalho e estado na linha principal; motivo, origem, situação, ordenação e datas personalizadas no painel «Avançados», que exibe o contador de filtros aplicados mesmo recolhido e abre automaticamente quando um filtro avançado ou período personalizado está ativo na URL.
- **Indicadores executivos** (`MetricKpiCard`): tempo total parado em card em destaque (span 2), ocorrências, duração média, pendentes (tom atenção) e em aberto (tom perigo quando > 0) — mesmos valores e semântica do `MetricStrip` anterior.
- **Histórico**: seção com contagem total e instrução discreta de interação; tabela, paginação backend, drawer e gestão permanecem inalterados.

A ordem da página segue: cabeçalho → filtros → indicadores → análise (Pareto, CTs, evolução, mapa de calor) → análise avançada → ocorrências. Tema claro/escuro e responsivo cobertos pelos estilos do MFE.

## Paradas — Etapa 5 (exportações e relatórios)

A aba Paradas oferece exportações geradas no backend (permissão `delpi-mes.downtimes.export`), sempre sobre o universo autorizado completo que atende aos filtros vigentes — nunca sobre a página exibida:

- **CSV / Excel** (`GET /downtimes/export`): todas as ocorrências elegíveis com situação de tratamento e vínculo de solicitação; o arquivo identifica filial, filtros, instante de extração, fuso e referência temporal do cálculo.
- **Relatório de pendências** (`GET /downtimes/reports/pendencies`): ocorrências sem classificação confirmada ou com tratamento em aberto — universo definido pelo owner.
- **PDF executivo** (`GET /downtimes/reports/executive`): indicadores, Pareto de causas e centros de trabalho afetados — mesmos agregados do painel, calculados pelo Production Control.
- Volume acima do teto de exportação gera arquivo parcial sinalizado na interface; dados de filiais não autorizadas nunca entram no arquivo.


## Paradas — Etapa 3 (classificação e tratamento gerencial)

O detalhe da parada no drawer passa a oferecer gestão em seções, sempre render-only — nenhuma regra de negócio, validação de catálogo ou semântica temporal mora no MFE:

- **Classificação** (`delpi-mes.downtimes.classify`): atribui ou corrige o motivo via `POST /downtimes/{id}/classification` enviando `expectedUpdatedAt` — conflito 409 mostra a mensagem do owner com ação de atualização; perfil sem permissão vê somente leitura.
- **Triagem e tratamento** (`delpi-mes.downtimes.treat`): análise, tipo de causa (hipótese/confirmada), ação corretiva e justificativa via `PUT .../treatment` idempotente; encaminhamento ao departamento de Processos via `POST .../treatment/referrals` com catálogo local de tipos de problema (requer também `my-requests.process-issue.create`); conclusão via `POST .../treatment/conclusion` — bloqueada pelo backend enquanto a solicitação vinculada não estiver concluída, e a UI já sinaliza esse estado. O status vivo da solicitação aparece quando legível; indisponibilidade nunca esconde o vínculo.
- **Histórico**: linha auditável da parada (`GET .../history`) com ação, ator e instante — mesma fonte `mes_audit_events` do owner.

O filtro **Estado** (Abertas/Encerradas) usa `status=open|closed` na listagem e na análise — mesmo predicado compartilhado do owner. Estados de carregamento, conflito, acesso negado e fonte indisponível são visíveis em cada seção.


## Paradas — Etapa 2 (indicadores e análise)

Acima da listagem, a aba Paradas exibe uma área analítica recolhível alimentada por `GET /downtimes/analytics` do próprio BFF — todos os números vêm calculados do Production Control; o MFE nunca agrega fatos.

- **Indicadores:** tempo total parado (união temporal deduplicada por CT), ocorrências, duração média, pendentes de classificação e abertas — cada card com explicação contextual. Divergência entre tempo deduplicado e tempo atribuído (histórico sobreposto) é explicada inline, não escondida.
- **Pareto de motivos** e **ranking de CTs** via `HorizontalValueBars` clicável — selecionar um motivo aplica `reasonCode`, o grupo «Pendente de classificação» aplica `classification=pending` (nunca um código inventado), e um CT aplica `workCenter`; todos preservam filial e período.
- **Evolução diária** via `BarSeriesChart` com alternância tempo × ocorrências e chips de dia que filtram a lista para o dia civil (`America/Sao_Paulo`). Dias sem parada aparecem com zero dentro do período.
- **Mapa de calor** dia-da-semana × hora (matriz semântica local — o kit não possui heatmap dedicado): descritivo, com legenda e tooltip; não oferece filtro por hora porque a listagem não suporta esse recorte.
- Os agregados respeitam os mesmos filtros da listagem e ignoram paginação, ordenação e `downtimeId`; mudança de filial/filtros isola o estado por identidade de consulta — dados da consulta anterior nunca piscam. Erro na análise é localizado e recuperável, sem quebrar a listagem.

## Paradas — Etapa 6 (análise avançada)

Abaixo dos indicadores, o painel **Análise avançada** consome `GET /downtimes/insights` com os mesmos filtros vigentes — todo o cálculo e os parâmetros vêm do Production Control; o MFE permanece render-only:

- **Comparação de períodos:** deltas absolutos e percentuais contra a janela anterior imediatamente equivalente (critério explícito no contrato).
- **Reincidência** por centro de trabalho e motivo com ocorrências reais deduplicadas; clicar num grupo aplica `workCenter` + `reasonCode` (ou `classification=pending`) na lista.
- **Ocorrências críticas:** paradas abertas prolongadas e rajadas de reincidência conforme regras parametrizadas no owner — quando nenhuma regra está configurada a tela diz isso explicitamente, sem inventar limites.
- **Pendências gerenciais:** sem classificação, tratamentos em aberto e paradas abertas.
- **Eficácia das ações:** evidência antes/depois por tratamento concluído, rotulada como observacional — nunca como prova de causalidade.
- **Lacunas de telemetria:** centros sensorizados sem dados confiáveis recentes são sinalizados; a análise não inventa paradas nesses períodos.

## Cadastros — Etapa 3

A área **Cadastros** (`/registrations`) é global: não exige filial, oculta o seletor de filial e exibe a indicação «Cadastro global — as alterações são válidas para todas as filiais». Hoje contém um único cadastro, **Motivos de parada**, que administra o catálogo global via `delpi-mes-api`:

- lista motivos ativos e inativos com busca local (código, descrição, categoria) e filtro de status;
- cria motivo (`code` técnico em lowercase) e edita `label`/`category`/`requiresNote`/`sortOrder` — `code` é somente leitura na edição;
- desativa com confirmação (o histórico é preservado) e reativa sem confirmação;
- trata 409/422 do BFF como conflito funcional (código duplicado; `setup` protegido mantém a mensagem segura do backend);
- não existe DELETE e os campos OEE nunca aparecem na tela nem nos bodies;
- `delpi-mes.downtime-reasons.manage` controla a visibilidade; acesso direto pela URL sem a permissão mostra o estado de acesso insuficiente — o backend continua autoridade.

Auditoria administrativa ainda não foi implementada.
