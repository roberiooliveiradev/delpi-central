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
| SQL TOTVS | `api-delpi` (`/production/otd*`, `/production/pcp-orders/*`, `/production/machine-load/*`, `/pedidos-venda-abertos/totvs-open-orders`, `/pedidos-venda-abertos/ops-abertas`, `/supplies/purchase-requests/open-coverage`) |

MFE não chama api-delpi. Subplugins são views internas do mesmo remote (não manifests aninhados).

## Visual

Shell híbrido Linear (rail compacta) + MES (cards de exceção, semáforo). Home = gestão à vista (logo Delpi, OTD do mês, OPs atrasadas, fila com scroll).

## Wireframe v1

Home: `/apps/production-control?branch=01`. Demanda: `/apps/production-control/demand?branch=01&status=at_risk`. Carga máquina: `/apps/production-control/machine-load?branch=01&ct={centro}`. Análise: `/apps/production-control/problem-analysis?branch=01&detector=incomplete-order-sets`. Materiais: `/apps/production-control/materials?branch=01&issue=excess`. Mapa de entrega: `/apps/production-control/delivery-map?branch=01`.

## Subplugins

| Subplugin | Estado | Escopo |
|-----------|--------|--------|
| `home` | ativo | Gestão à vista (OTD do mês, OPs atrasadas, fila) |
| `demand` | ativo | Carteira a entregar: saldo por cliente/produto/data com cobertura por estoque e OP |
| `machine-load` | ativo | Sequenciamento SH8 congelado por filial (janela por entrega do PA) + status HZA vivo + refresh sob confirmação |
| `problem-analysis` | ativo | Grade de detectores de exceção (primeiro: conjuntos incompletos) |
| `materials` | ativo | Excesso e falta de SC1 de MP vs ESTSEG (somente leitura) |
| `delivery-map` | ativo | OPs PA com saldo, agrupadas por entrega prevista; MP-OK/CT manuais; snapshot congelado |
| `capacity` | em breve | Capacidade e ocupação percentual por CT |

Contrato TOTVS da carga máquina: [production-machine-load.md](../../../api-delpi/docs/api/production-machine-load.md); conjuntos incompletos: [production-order-sets-incomplete.md](../../../api-delpi/docs/api/production-order-sets-incomplete.md); convenção de chave de OP: [ordem-producao-chave.md](../../../api-delpi/docs/api/padroes-totvs/ordem-producao-chave.md); apontamento de operação: [apontamento-operacao-hza.md](../../../api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md).

A Análise de problemas é **grade de detectores**: cada card é uma regra registrada no BFF e descrita em `production-control-api/production_control_app/content/problem_analysis.json`. A OP atrasada saiu da área e continua na gestão à vista, com a fila da home abrindo a Carga máquina no rastreio (`?locate=`).

## Fora desta versão

APS/Gantt, escrita no TOTVS, drag-and-drop de sequenciamento, export CSV da fila, embed de outros MFEs de chão de fábrica.
