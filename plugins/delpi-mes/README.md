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

## Paradas — Etapa 2 (indicadores e análise)

Acima da listagem, a aba Paradas exibe uma área analítica recolhível alimentada por `GET /downtimes/analytics` do próprio BFF — todos os números vêm calculados do Production Control; o MFE nunca agrega fatos.

- **Indicadores:** tempo total parado (união temporal deduplicada por CT), ocorrências, duração média, pendentes de classificação e abertas — cada card com explicação contextual. Divergência entre tempo deduplicado e tempo atribuído (histórico sobreposto) é explicada inline, não escondida.
- **Pareto de motivos** e **ranking de CTs** via `HorizontalValueBars` clicável — selecionar um motivo aplica `reasonCode`, o grupo «Pendente de classificação» aplica `classification=pending` (nunca um código inventado), e um CT aplica `workCenter`; todos preservam filial e período.
- **Evolução diária** via `BarSeriesChart` com alternância tempo × ocorrências e chips de dia que filtram a lista para o dia civil (`America/Sao_Paulo`). Dias sem parada aparecem com zero dentro do período.
- **Mapa de calor** dia-da-semana × hora (matriz semântica local — o kit não possui heatmap dedicado): descritivo, com legenda e tooltip; não oferece filtro por hora porque a listagem não suporta esse recorte.
- Os agregados respeitam os mesmos filtros da listagem e ignoram paginação, ordenação e `downtimeId`; mudança de filial/filtros isola o estado por identidade de consulta — dados da consulta anterior nunca piscam. Erro na análise é localizado e recuperável, sem quebrar a listagem.

## Cadastros — Etapa 3

A área **Cadastros** (`/registrations`) é global: não exige filial, oculta o seletor de filial e exibe a indicação «Cadastro global — as alterações são válidas para todas as filiais». Hoje contém um único cadastro, **Motivos de parada**, que administra o catálogo global via `delpi-mes-api`:

- lista motivos ativos e inativos com busca local (código, descrição, categoria) e filtro de status;
- cria motivo (`code` técnico em lowercase) e edita `label`/`category`/`requiresNote`/`sortOrder` — `code` é somente leitura na edição;
- desativa com confirmação (o histórico é preservado) e reativa sem confirmação;
- trata 409/422 do BFF como conflito funcional (código duplicado; `setup` protegido mantém a mensagem segura do backend);
- não existe DELETE e os campos OEE nunca aparecem na tela nem nos bodies;
- `delpi-mes.downtime-reasons.manage` controla a visibilidade; acesso direto pela URL sem a permissão mostra o estado de acesso insuficiente — o backend continua autoridade.

Auditoria administrativa ainda não foi implementada.
