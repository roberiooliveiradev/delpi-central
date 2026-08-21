# Portal PCP (MFE)

Microfrontend federado da plataforma **Portal PCP** (`id`: `production-control`): shell estilo command-center com **gestão à vista** na home e subplugins (Demanda, Carga máquina, Análise de problemas).

**Recado para quem implementa:** o destino do módulo é o **Portal de Produção**, com o PCP como primeira área — não absorver dashboard/eficiência/apontamentos neste BFF. Detalhe: [docs/12-roadmap-e-evolucao/production-control/README.md](../../docs/12-roadmap-e-evolucao/production-control/README.md) § Recado.

## Fluxo técnico

```text
Portal → production-control (remoteEntry.js)
      → /apps/production-control-api/*
      → api-delpi /production/otd, /production/otd/series, /production/pcp-orders/*,
                  /production/machine-load/*, /production/production-order-sets/incomplete,
                  /pedidos-venda-abertos/totvs-open-orders, /pedidos-venda-abertos/ops-abertas
      → @delpi/plugin-ui (Module Federation)
```

O MFE **não** chama `/apps/api-delpi`. Header: `X-Delpi-Caller-App: production-control`.

## Rotas UI

| Rota | Tela |
|------|------|
| `/apps/production-control?branch=` | Gestão à vista (OTD do mês, OPs atrasadas, fila) |
| `…/demand?branch=01\|02&q=&status=` | Demanda (carteira a entregar com cobertura) |
| `…/machine-load?branch=01\|02&ct=&startDate=&endDate=&locate=` | Carga máquina (abas por centro de trabalho) |
| `…/problem-analysis?branch=01\|02&detector=` | Análise de problemas (grade de detectores + registros) |

Subplugins futuros (`capacity`) aparecem na rail com estado *Em breve*.

**Gestão à vista:** card de OTD do mês com tendência diária via `MultiTypeSeriesChart` (`chartType: "line"`) e, abaixo, card **Volume de produção** em colunas (`chartType: "column"`) com a quantidade diária de PAs — mesma fonte do apontamento (`GET /production/appointments/series`, só `qty_produced` / última operação do roteiro). A média diária exibida no card considera **somente dias úteis** (seg–sex). OTD e fila de atraso permanecem no grid superior.

**Demanda:** carteira a entregar da filial (`GET /demand`) — quatro KPIs (saldo a entregar, linhas atrasadas, saldo sem cobertura e próxima entrega), gráfico de colunas do saldo por **semana de entrega** (o primeiro grupo é o que já venceu) e a tabela das linhas em aberto. A coluna *Cobertura* resume quanto vem do estoque, quanto está em OP e quanto ficou descoberto; a *Situação* traduz o status decidido pelo BFF (`late`, `at_risk`, `covered_by_order`, `covered_by_stock`) — o MFE é render-only. Busca, status e janela de entrega vão ao BFF (que pagina e ordena); `?q=` e `?status=` abrem a tela já filtrada. Clicar na linha abre o detalhe com as OPs que cobrem o saldo e o atalho **Ver na Carga máquina** (`?locate=` no produto). O botão **Exportar CSV** baixa a página visível no formato do Excel pt-BR. Nenhum campo financeiro trafega: o PCP olha quantidade, não preço.

**Carga máquina:** uma aba por centro de trabalho (`UnderlineNav` `mode="tabs"`) com a fila de operações alocadas — situação, OP completa, produto da operação, quantidade (3 casas), ferramenta, operação, código do PA e entrega do PA. O deep link (`?ct=`, `?startDate=`, `?endDate=`, `?locate=`) reabre a mesma aba, recorte de entrega e rastreio; trocar de filial ou de CT preserva o recorte.

**Rastreio conjunto / produto:** campo na barra da Carga máquina busca conjunto (`C2_NUM` — 6 primeiros dígitos da OP completa `H8_OP`/`C2_OP`), produto (PA) ou intermediário via `GET /machine-load/locate`. Ex.: OP `10840401003` rastreia **todas** as OPs que começam com `108404` (um único conjunto). Busca por PA lista cada C2_NUM daquele produto. Botão direito → **Rastrear produção do conjunto** usa o C2_NUM da linha.

**Priorizar conjunto (botão direito):** a segunda ação do menu leva **todas** as OPs do conjunto (mesmo `C2_NUM`) ao topo da fila em cada centro de trabalho onde elas aparecem, via `POST /machine-load/prioritize`. Operação **já iniciada** (em produção ou já apontada) não é ultrapassada — o conjunto entra logo depois dela. Há confirmação antes de aplicar; o aviso da barra informa em quantos centros a fila mudou. Como a mudança atravessa vários CTs, a pilha de Ctrl+Z do CT ativo é zerada.

**Retirar conjunto da programação (botão direito):** a terceira ação tira **todas** as OPs do conjunto da fila em todos os centros (`POST /machine-load/withdraw`), some com elas do cockpit do operador e recalcula resumo e contadores das abas. Nada é apagado: as operações continuam no snapshot na posição original. O botão **Fora da programação (N)**, na barra ao lado do link do operador, abre a lista dos conjuntos retirados (produto, operações, centros, quem retirou e quando) com **Devolver à fila** (`POST /machine-load/restore`), que recoloca cada OP onde estava. A retirada sobrevive ao **Atualizar** do TOTVS; o rastreio ainda encontra o conjunto, marcado com o selo *Fora da programação*. Como a mudança atravessa vários CTs, a pilha de Ctrl+Z do CT ativo é zerada.

**Enviar para outro centro de trabalho (botão direito):** a quarta ação abre um modal com o resumo da operação (OP, operação, descrição, centro atual) e um **select** com os demais centros com fila no período. Ao confirmar, `POST /machine-load/transfer` move só aquela operação para o **fim** da fila do destino — de lá o PCP reordena por DnD ou prioriza o conjunto. A linha passa a exibir o selo *veio de {CT}* enquanto estiver fora do centro de origem; devolvê-la ao centro original apaga o selo. A transferência sobrevive ao **Atualizar** do TOTVS e, como muda a fila de dois CTs, zera a pilha de Ctrl+Z do CT ativo.

**Otimizar por entrega (barra):** o botão ⇅ *Otimizar por entrega*, ao lado do link do operador, chama `POST /machine-load/optimize-delivery` e resequencia a fila de **todos** os centros da filial pela data de entrega do PA — o carga máquina do TOTVS às vezes deixa material de mês seguinte à frente do que está vencendo. Operações já iniciadas continuam onde estão, empate na mesma entrega preserva a ordem atual e operação sem entrega vai para o fim do seu centro. Conjuntos fora da programação não voltam à fila. Há confirmação antes de aplicar; o aviso da barra informa quantos centros mudaram e quantas operações trocaram de posição. Como a mudança atravessa vários CTs, a pilha de Ctrl+Z do CT ativo é zerada e o cockpit do operador atualiza sozinho.

**Análise de problemas:** grade de cards, um por **detector** de exceção (`GET /problem-analysis`), e abaixo a tabela dos registros do detector aberto (`GET /problem-analysis/{detectorId}`). O deep link é `?detector=`; sem ele, abre o primeiro card do catálogo. Título, descrição, ícone e severidade vêm do BFF — o MFE é render-only e não decide o que é crítico.

**Conjuntos incompletos (primeiro detector):** compara a estrutura do produto raiz (SG1, vigente na **emissão da OP mãe**) com as OPs criadas no mesmo conjunto (`C2_NUM` + `C2_ITEM`). *Falta* = intermediário da estrutura sem OP; *Sobra* = OP de produto fora da estrutura. Matéria-prima não entra, e conjunto criado certo com OPs já encerradas não aparece. A linha mostra conjunto, produto raiz com os códigos que faltam ou sobram, entrega, número de OPs e os dois contadores.

**Fila de atraso da home:** clicar numa OP atrasada abre a **Carga máquina** com `?locate=` na OP — de lá dá para priorizar, transferir ou tirar o conjunto da programação. A gestão à vista continua consumindo `GET /overview`.

**Em produção agora:** a coluna *Situação* mostra `production_status` vindo da API (apontamento `HZA010`). Operação rodando ganha linha verde, ponto pulsante, nome do operador e horário de início. Operação *Já apontada* exibe o último operador, tacha a linha e suaviza o contraste. A aba do centro de trabalho recebe o ponto só quando há OP em produção; o resumo do período mostra quantas estão na máquina. A UI é render-only — quem decide o status é a api-delpi, o MFE só mapeia `production_status` → rótulo e variante (`utils/machineLoadStatus.ts`).

**Fila congelada:** o sequenciamento SH8 fica salvo no BFF (`machine_load_snapshots`), **uma fila viva por filial**. A primeira visita da filial faz seed automático; depois disso, só o botão **Atualizar** (com confirmação) chama `POST /machine-load/refresh` e **substitui** a fila — inclusive qualquer ordem manual. Virada de dia não reseeda: a fila continua a mesma até o PCP atualizar. O status HZA continua vivo a cada GET. Trocar de centro de trabalho ou de recorte não regenera a fila.

**Período = entrega do PA:** o formulário da barra filtra por **data de entrega do PA** (`COALESCE(PA.DT_ENTREGA, C2_DATPRF)`), não pela programação. Sem recorte na URL, «De» já vem com a entrega mais antiga presente na fila e continua editável; «até» é hoje + 14 dias, o horizonte que o **Atualizar** puxa do TOTVS. Aplicar «De/até» é **lente de leitura** — recorta a fila congelada e esconde centros sem operação visível, sem chamar o ERP; **Voltar ao padrão** limpa o recorte. Se sobrar operação sem entrega, a barra avisa quantas são (falha de vínculo com a OP mãe no TOTVS).

**Reordenar (DnD):** no CT ativo, arraste pela alça da linha para mudar a sequência. No drop, o MFE aplica a ordem na UI e chama `PATCH /machine-load/sequence` (só aquele CT). **Ctrl+Z** desfaz e **Ctrl+Shift+Z** refaz (pilha local + PATCH). A tabela não usa sort por coluna, para não conflitar com a ordem manual. A barra de período mostra `Sequência ajustada em…` quando houver `sequence_updated_at`.

**Cockpit do operador (link público):** o botão **Link do operador** na barra de período copia `…/p/production-control/cockpit/aberto?branch={filial}` — página aberta no `public-hub`, sem login. O operador escolhe o posto na primeira abertura (a escolha fica no navegador dele), acompanha a fila em tempo real via WebSocket, copia a OP e abre o **desenho do PA** quando o arquivo existe na pasta do FILESERVER montada no `production-control-api`. É **somente leitura**: o sequenciamento continua exclusivo do PCP. Ver [plugins/public-hub/README.md](../public-hub/README.md) § *Fila de produção*.

## API

Base: `/apps/production-control-api`

| Método | Path | Uso |
|--------|------|-----|
| GET | `/health` | Liveness |
| GET | `/subplugins` | Catálogo filtrado por permissão |
| GET | `/overview?branch=` | Gestão à vista (OTD + atrasos) |
| GET | `/demand?branch=&search=&status=&dueFrom=&dueTo=&sort=&direction=&page=&pageSize=&refresh=` | Carteira a entregar com cobertura por estoque e OP |
| GET | `/machine-load?branch=&workCenter=&startDate=&endDate=` | Centros de trabalho + fila do CT ativo (snapshot) |
| GET | `/machine-load/locate?branch=&q=` | Rastreio de conjunto (C2_NUM, 6 dígitos) ou produto (PA) |
| POST | `/machine-load/refresh?branch=&workCenter=&startDate=&endDate=` | Regenera o snapshot a partir do TOTVS (janela por entrega do PA) |
| PATCH | `/machine-load/sequence?branch=&workCenter=` | Persiste a ordem manual do CT (`ordered_keys`) |
| POST | `/machine-load/prioritize?branch=&orderNumber=&workCenter=` | Prioriza o conjunto (C2_NUM) no topo da fila de todos os CTs |
| POST | `/machine-load/optimize-delivery?branch=&workCenter=` | Reordena a fila de todos os CTs pela entrega do PA |
| POST | `/machine-load/withdraw?branch=&orderNumber=&workCenter=` | Tira o conjunto da programação (some da fila e do cockpit) |
| POST | `/machine-load/restore?branch=&orderNumber=&workCenter=` | Devolve o conjunto retirado à posição original |
| POST | `/machine-load/transfer?branch=&productionOrder=&operationCode=&targetWorkCenter=&workCenter=` | Move a operação para o fim da fila de outro CT |
| GET | `/problem-analysis?branch=` | Cards dos detectores de exceção |
| GET | `/problem-analysis/{detectorId}?branch=&page=&pageSize=` | Registros do detector |
| GET | `/public/machine-load/{token}?branch=&workCenter=` | Cockpit do operador (público, somente leitura) |
| GET | `/public/machine-load/{token}/drawings/{paCode}/pdf?branch=` | PDF do desenho do PA lido da pasta do FILESERVER montada no BFF (público, PA precisa estar na fila) |
| WS | `/public/machine-load/{token}/ws?branch=` | Aviso de mudança da fila para o cockpit |

Contrato TOTVS (não duplicado aqui): [production-pcp-orders.md](../../api-delpi/docs/api/production-pcp-orders.md) e [production-machine-load.md](../../api-delpi/docs/api/production-machine-load.md).

## Permissões

`production-control.access`, `production-control.demand.view`, `production-control.machine-load.view`, `production-control.problem-analysis.view`, `production-control.view.filial-01`, `production-control.view.filial-02`.

## Desenvolvimento

```bash
cd plugins/production-control
npm install
npm run test
npm run build
```

Dev federado: `VITE_PLUGIN_UI_DEV=1 npm run dev` com `plugin-ui` em `5010`.

CSS escopado em `.dashboard-production-control` — zero `.delpi-ui-*` no MFE.

## Docker

```bash
./infra/scripts/up-dev-sequential.sh --fase api --build production-control-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build production-control
# Nova location Nginx: recriar só o gateway (bind mount; sem --build em lote)
# docker compose -f infra/docker-compose.dev.yml -f infra/docker-compose.minimal.yml --env-file infra/.env \
#   up -d --no-deps --force-recreate --no-build gateway
```

## Registro

```bash
TOKEN=<jwt-admin> ./scripts/register-manifest.sh
```

## Smoke

```bash
curl -sI http://localhost/apps/production-control/assets/remoteEntry.js | head -3
curl -s http://localhost/apps/production-control-api/health
```
