# Portal PCP (`production-control`)

Plataforma de planejamento e controle da produção na Minha Delpi.

## Recado para quem implementa

O **módulo** que faz sentido a médio prazo é o **Portal de Produção**. O **PCP** é a primeira área dentro dele — não o nome da casa.

Hoje o tile e o copy dizem **Portal PCP** porque as telas ativas (gestão à vista, carga máquina, análise de problemas) são trabalho de PCP. O `id` técnico já é mais largo (`production-control`), o manifesto já está no grupo **Produção**, e o papel alvo já é **módulo** (shell), igual `maintenance` e `strategic-indicators`.

**Não** tratar este app como guarda-chuva de tudo que é fábrica. Dashboard Produção, eficiência fabril, apontamentos, retrabalho, scrap, inspeção de processo e TV continuam plugins irmãos, cada um com permissão e contrato próprios. O BFF `production-control-api` dona a regra de sequenciamento (fila congelada, priorizar, retirar, transferir); **não** absorve OEE, apontamento HZA/SH6 nem retrabalho. SQL TOTVS permanece na `api-delpi`.

Quando a rail tiver mais de um público de verdade:

1. O tile vira **Portal de Produção**; PCP vira o primeiro grupo da rail (junto com Capacidade, já *em breve*).
2. Irmãos entram por `routes[].target` (plugin-vs-módulo) — **não** copiando tela nem fundindo API.
3. **Não** rebatizar `production-control-api` / schema `production_control` como umbrella genérico de produção. Planos futuros do PCP usam tabelas irmãs no mesmo schema.

Até lá: não renomear o launcher só para “prometer” um portal que ainda não existe. Analogia: Portal Comercial × Dashboard Comercial — dois nomes, dois trabalhos.

## Ownership

| Camada | Pacote |
|--------|--------|
| UI | `plugins/production-control` |
| BFF / regra PCP | `production-control-api` |
| SQL TOTVS | `api-delpi` (`/production/otd*`, `/production/pcp-orders/*`, `/production/machine-load/*`, `/production/orders/operation-materials*`, `/pedidos-venda-abertos/totvs-open-orders`, `/pedidos-venda-abertos/ops-abertas`, `/supplies/purchase-requests/open-coverage`, `/supplies/stock-balances/items`, `/products/{code}/raw-material-set-shortages`) |
| Contagem MES (shadow) no cockpit | `production-control-api` + telemetria `production-pulse-api` — ver [MES-PULSE-COUNTING.md](./MES-PULSE-COUNTING.md) |
| Fatos MES e contrato S2S temporário | `production-control-api` expõe `/integrations/mes/*` para o futuro `delpi-mes-api` — ver [Delpi MES](../delpi-mes/README.md) |

MFE não chama api-delpi. Subplugins são views internas do mesmo remote (não manifests aninhados).

O ownership dos fatos MES permanece temporariamente neste BFF, sem transformá-lo em umbrella gerencial. A superfície interna somente leitura existe para permitir que o futuro `delpi-mes-api` atravesse a fronteira por contrato, sem banco compartilhado, repositories internos ou rotas públicas do cockpit.

## Visual

Shell híbrido Linear (rail compacta) + MES (cards de exceção, semáforo). Home = gestão à vista (logo Delpi, OTD do mês, OPs atrasadas, fila com scroll).

## MyWEG Necessidades

- [E1 contrato/normalização](./MYWEG-NEEDS-INGESTION-E1.md)
- [E2 persistência/S2S](./MYWEG-NEEDS-INGESTION-E2.md)
- [Publicador Linux manual](./MYWEG-NEEDS-LINUX-PUBLISHER.md)
- [E3 Portal PCP](./MYWEG-NEEDS-PORTAL-E3.md)
- [E4 matching SB1](./MYWEG-NEEDS-PROTHEUS-E4.md)
- [E5 evolução do planejamento](./MYWEG-NEEDS-PLANNING-EVOLUTION-E5.md)

## Wireframe v1

Home: `/apps/production-control?branch=01`. Demanda: `/apps/production-control/demand?branch=01&status=at_risk`. Carga máquina: `/apps/production-control/machine-load?branch=01&ct={centro}`. Análise: `/apps/production-control/problem-analysis?branch=01&detector=incomplete-order-sets`. Materiais: `/apps/production-control/materials?branch=01&issue=excess` (consulta de ruptura: `?issue=pa-shortage&q=90263114`). Alimentador de linha: `/apps/production-control/line-feeder?branch=01` (coleta dinâmica por horizonte — [LINE-FEEDER-UI-E4.md](./LINE-FEEDER-UI-E4.md); parâmetros legados de corte na URL são ignorados com segurança). Mapa de entrega: `/apps/production-control/delivery-map?branch=01`.

## Subplugins

| Subplugin | Estado | Escopo |
|-----------|--------|--------|
| `home` | ativo | Gestão à vista (OTD do mês, OPs atrasadas, fila) |
| `demand` | ativo | Carteira a entregar: saldo por cliente/produto/data com cobertura por estoque e OP |
| `machine-load` | ativo | Sequenciamento SH8 congelado por filial (janela por entrega do PA) + status HZA vivo + refresh sob confirmação; `GET /machine-load/cockpit-status` expõe os estados de execução dos runs MES locais — desde a Etapa 02 é também a **fonte oficial de proteção de posições** em `prioritize`/`optimize` (apontamentos HZA e flags do snapshot não travam mais posição), e o refresh carrega a fila em `schedule_no_status_asc` (cronologia SH8 sem prioridade por coletor) com `include_in_production_outside_period=false` — a exceção de período é sustentada pelos pares `OP:operação` dos runs abertos, nunca por apontamento HZA abandonado; desde a Etapa 03 o MFE apresenta execução só pelo `cockpit-status` (snapshot completo de runs, sem nomes de operador) e lê saldos por `GET /machine-load/balances` (SH6/SC2 em lote, sem HZA) — o `live-status` HZA permanece como contrato legado, fora do consumo do PCP; **horizonte temporário por CT** (`POST /machine-load/horizon/preview` + `POST /machine-load/horizon/apply`): após o refresh padrão, o PCP pode ampliar só um centro (21/28/42 dias ou data final), mesclando operações adicionais no WORKING sem tocar PUBLISHED — exige estado draft/unpublished (se LIVE, orientar «Atualizar»); metadados `horizon_exceptions` no payload JSON da geração; próximo refresh descarta todas as exceções; cockpit só muda após «Enviar para máquinas» |
| `problem-analysis` | ativo | Grade de detectores de exceção (conjuntos, quantidades, demanda, intermediários compartilhados) |
| `materials` | ativo | Excesso e falta de SC1 de MP vs ESTSEG + consulta de ruptura de MP no conjunto do PA (empenhos SD4 efetivos) |
| `line-feeder` | ativo | Coleta dinâmica por horizonte ([LINE-FEEDER-UI-E4.md](./LINE-FEEDER-UI-E4.md)); E1 fila PUBLISHED ([LINE-FEEDER-PUBLISHED-QUEUE-E1.md](./LINE-FEEDER-PUBLISHED-QUEUE-E1.md)); E2 horizonte ([LINE-FEEDER-HORIZON-E2.md](./LINE-FEEDER-HORIZON-E2.md)); E3 materiais pelo saldo real do ponto de uso ([LINE-FEEDER-MATERIALS-E3.md](./LINE-FEEDER-MATERIALS-E3.md)); segurança shortfall×incomplete / early-stop ([LINE-FEEDER-HORIZON-SAFETY-E1.md](./LINE-FEEDER-HORIZON-SAFETY-E1.md)); ST progressivo ([LINE-FEEDER-HORIZON-OPT-E2.md](./LINE-FEEDER-HORIZON-OPT-E2.md)); pick-plans/requirements legados preservados fora do fluxo principal |
| `delivery-map` | ativo | OPs PA com saldo, agrupadas por entrega prevista; MP-OK/CT manuais; snapshot congelado |
| `capacity` | em breve | Capacidade e ocupação percentual por CT |

Contrato TOTVS da carga máquina: [production-machine-load.md](../../../api-delpi/docs/api/production-machine-load.md); conjuntos incompletos: [production-order-sets-incomplete.md](../../../api-delpi/docs/api/production-order-sets-incomplete.md); convenção de chave de OP: [ordem-producao-chave.md](../../../api-delpi/docs/api/padroes-totvs/ordem-producao-chave.md); apontamento de operação: [apontamento-operacao-hza.md](../../../api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md). Inventário e contratos propostos para seleção múltipla de operações (E1): [MACHINE-LOAD-MULTI-SELECTION-E1.md](./MACHINE-LOAD-MULTI-SELECTION-E1.md). Troca guiada de OP no cockpit (E1, backend e contrato): [MES-GUIDED-HANDOFF-E1.md](./MES-GUIDED-HANDOFF-E1.md). Horizonte temporário por CT: [MACHINE-LOAD-HORIZON-EXPANSION.md](./MACHINE-LOAD-HORIZON-EXPANSION.md).

A Análise de problemas é **grade de detectores**: cada card é uma regra registrada no BFF e descrita em `production-control-api/production_control_app/content/problem_analysis.json`. A OP atrasada saiu da área e continua na gestão à vista, com a fila da home abrindo a Carga máquina no rastreio (`?locate=`).

## Integração MyWEG (Necessidades · filial 02)

- Etapa 1 (contrato `myweg.needs.batch.v1` + normalização): [MYWEG-NEEDS-INGESTION-E1.md](./MYWEG-NEEDS-INGESTION-E1.md).
- Etapa 2 (persistência V025, POST S2S, consultas JWT, sem MFE): [MYWEG-NEEDS-INGESTION-E2.md](./MYWEG-NEEDS-INGESTION-E2.md).
- Publicador Linux manual (sem cron): [MYWEG-NEEDS-LINUX-PUBLISHER.md](./MYWEG-NEEDS-LINUX-PUBLISHER.md).
- Etapa 3 (Portal PCP): [MYWEG-NEEDS-PORTAL-E3.md](./MYWEG-NEEDS-PORTAL-E3.md).
- Etapa 4 (matching SB1): [MYWEG-NEEDS-PROTHEUS-E4.md](./MYWEG-NEEDS-PROTHEUS-E4.md).
- Etapa 5 (evolução + faturamento indicativo): [MYWEG-NEEDS-PLANNING-EVOLUTION-E5.md](./MYWEG-NEEDS-PLANNING-EVOLUTION-E5.md).

## Produto relacionado

**Factory Supply (Abastecimento Fabril)** — `docs/12-roadmap-e-evolucao/factory-supply/` — é produto distinto, fora do ownership `production-control-api`. O `line-feeder` continua capability ativa deste portal e serve de referência de implementação para o Factory Supply; nenhuma dependência de backend é criada entre eles.

## Fora desta versão

APS/Gantt, escrita no TOTVS, drag-and-drop de sequenciamento, export CSV da fila, embed de outros MFEs de chão de fábrica.
