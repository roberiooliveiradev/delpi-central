# Portal PCP (`production-control`)

Plataforma de planejamento e controle da produção na Minha Delpi.

## Ownership

| Camada | Pacote |
|--------|--------|
| UI | `plugins/production-control` |
| BFF / regra PCP | `production-control-api` |
| SQL TOTVS | `api-delpi` (`/production/otd*`, `/production/pcp-orders/*`, `/production/machine-load/*`) |

MFE não chama api-delpi. Subplugins são views internas do mesmo remote (não manifests aninhados).

## Visual

Shell híbrido Linear (rail compacta) + MES (inbox de exceções, semáforo). Home = gestão à vista (logo Delpi, OTD do mês, OPs atrasadas, fila com scroll).

## Wireframe v1

Home: `/apps/production-control?branch=01`. Carga máquina: `/apps/production-control/machine-load?branch=01&ct={centro}`. Análise: `/apps/production-control/problem-analysis?branch=01&issue=delayed-order:{op_key}`.

## Subplugins

| Subplugin | Estado | Escopo |
|-----------|--------|--------|
| `home` | ativo | Gestão à vista (OTD do mês, OPs atrasadas, fila) |
| `machine-load` | ativo | Sequenciamento SH8 congelado por filial (janela por entrega do PA) + status HZA vivo + refresh sob confirmação |
| `problem-analysis` | ativo | Inbox de exceções + detalhe da OP |
| `capacity` | em breve | Capacidade e ocupação percentual por CT |

Contrato TOTVS da carga máquina: [production-machine-load.md](../../../api-delpi/docs/api/production-machine-load.md); convenção de chave de OP: [ordem-producao-chave.md](../../../api-delpi/docs/api/padroes-totvs/ordem-producao-chave.md); apontamento de operação: [apontamento-operacao-hza.md](../../../api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md).

## Fora desta versão

APS/Gantt, escrita no TOTVS, drag-and-drop de sequenciamento, export CSV da fila, embed de outros MFEs de chão de fábrica.
