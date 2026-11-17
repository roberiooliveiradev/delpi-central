# GLPI #1598 — Divergências de estoque no GR Diário (TV Dashboard)

**Solicitante:** Fabiano Schmitz · **Origem:** Helpdesk #1598 (16/11/2026)
**Escopo:** somente rotas de leitura na api-delpi e catálogo de fontes do TV Dashboard. **A tela/playlist será criada pelo solicitante da implementação (TI) no editor TV.**

## 1. Necessidade de negócio

- Divergência acumulada no ano, em reais;
- Divergência do mês, em reais;
- Itens com divergência na semana: código, descrição, quantidade e valor em reais.
- O objetivo é evidenciar as perdas/ajustes e mobilizar a investigação de causas.

## 2. Fontes encontradas (17/11/2026)

| Origem | Rotas existentes | Regra |
|---|---|---|
| Portal Controladoria/Financeiro, R07 | `/financeiro/inventory-adjustments` e `/summary` via api-delpi; BFF `/closing/inventory-adjustments` | Inventário (MATR910, SD3 `D3_DOC='INVENT'`), custo **as-of TTAT** na competência, restrito a S2S da Controladoria; paridade da emissão oficial **pendente** |
| Portal Suprimentos, ajustes | `GET /supplies/inventory-adjustments/summary` e `GET /supplies/inventory-adjustments` | SD3 `INVENT`, estornos excluídos, `D3_CF='RE0'` = furo, `DE0` = sobra; `D3_CUSTO1` atual, filtros por datas livres |
| Portal Suprimentos, acuracidade (%) | `/supplies/inventory-accuracy/{summary,items}` | Percentual de contagens e eventos SB7. **Não confundir** com valor dos ajustes em R$ |

**Decisão de fonte:** reutilizar o domínio/critério canônico já implementado em Suprimentos para o **acompanhamento operacional diário**; não duplicar SQL do R07 nem abrir indevidamente o escopo S2S financeiro no TV Dashboard. Isso assegura granularidade diária/semana e atualização após novos lançamentos.

**Ressalva de paridade contábil:** o R07 do fechamento mensal lê custo histórico as-of com TTAT (a revisão G6 ainda está pendente), enquanto as rotas operacionais utilizam o `D3_CUSTO1` **corrente**, que pode ser recalcado pelo MATA330. Não prometer igualdade monetária exata entre visões em competências antigas. Toda divergência material deve ser reconciliada pela Controladoria. Não alterar a fonte R07.

## 3. Definições dos indicadores

- **Divergência bruta (R$)** = soma dos valores absolutos de furos e sobras de inventário; não subtrair sobras dos furos, pois isso esconderia as divergências. Também disponibilizamos valores separados para perdas (furo) e sobras, além do saldo líquido.
- **Furo (falta)** = saída de inventário `D3_CF='RE0'`, valor representado como perda em R$ positivo no campo `shortage_value`, e como negativo no saldo assinado.
- **Sobra** = entrada `D3_CF='DE0'`, valor positivo.
- **Ano** = de 01/01 até `as_of` inclusive; **mês** = do dia 1 até `as_of`; **semana** = segunda-feira até `as_of` (semana ISO corrente, não os últimos sete dias).
- **As-of default**: hoje em `America/Sao_Paulo`; parâmetro `as_of=YYYY-MM-DD` opcional para reprodução histórica, desde 2023.
- **Filial:** `branch=all|01|02` (padrão `all`, mesmo escopo da rota existente); `warehouse` opcional. Para GR Diário local, filtrar a unidade correta.
- **Arredondamento:** valor monetário em R$ exibido a dois decimais, após somar `D3_CUSTO1`. A API fornece quantidade com seis casas no detalhe.
- Movimentos com CF diferente de RE0/DE0 não entram na divergência. Estornos e registros excluídos não entram.

## 4. Novos endpoints (somente leitura)

API base: `api-delpi`. Todos protegidos por `api-delpi.access` como as rotas de ajustes já existentes. Mantidos contratos/operationIds para curadoria e sincronização automática do TV Dashboard.

### 4.1. Indicadores acumulados: KPIs do ano e do mês

`GET /supplies/inventory-adjustments/tv/summary?branch=02`

operationId: `get_supplies_inventory_adjustments_tv_summary`

Campos principais, **escalares**:
- `year_divergence_brl`: valor bruto acumulado no ano;
- `month_divergence_brl`: valor bruto do mês;
- `year_shortage_value_brl`, `month_shortage_value_brl`: furos/perdas;
- `year_surplus_value_brl`, `month_surplus_value_brl`: sobras;
- `year_net_value_brl`, `month_net_value_brl`: saldo líquido (sobras - faltas);
- `year_adjustment_count`, `month_adjustment_count`, `as_of`, `year_start`, `month_start`.

**Sugestão de TV:** dois KPIs grandes, R$, com título e referência visível. Como complemento, KPI de perdas do mês em vermelho. Não usar `net_value` como divergência bruta.

### 4.2. Série mensal para gráfico (ano até a referência)

`GET /supplies/inventory-adjustments/tv/monthly-series?branch=02`

operationId: `get_supplies_inventory_adjustments_tv_monthly_series`

`items[]`, grão **mês**:
- `periodo`: AAAA-MM;
- `shortage_value_brl`: valor de faltas;
- `surplus_value_brl`: valor de sobras;
- `gross_value_brl`: divergência bruta;
- `net_value_brl`: saldo assinado;
- `adjustment_count`, `shortage_count`, `surplus_count`.
- Meses sem movimentos são emitidos explicitamente com **zero**.

**Gráfico recomendado:** **colunas agrupadas** por mês, duas séries: faltas e sobras. Assim se identifica aumento persistente das perdas; evite empilhar sinais opostos em um gráfico sem rótulo. Alternativa: linha de faltas por mês.

### 4.3. Itens da semana para tabela/ranking

`GET /supplies/inventory-adjustments/tv/weekly-items?branch=02&top_limit=10`

operationId: `get_supplies_inventory_adjustments_tv_weekly_items`

`items[]`, grão **filial + código do produto + armazém + natureza (furo/sobra)**:
- `product_code`, `product_description`, `unit`, `warehouse`, `branch`;
- `nature` (`shortage` / `surplus`), `nature_label` (Falta/Sobra);
- `quantity` (absoluta), `value_brl` (R$ absoluto);
- `signed_quantity`, `signed_value_brl` (negativos para falta);
- `movement_count`, `unpriced_movements` (valores faltantes).

Metadados: `week_start`, `week_end`, `total_groups`, `returned`, `truncated`.
- Consulta agregada em SQL **antes** do ranking; `top_limit` 1 a 50, padrão 10.
- Naturezas ficam separadas: sobras e faltas do mesmo produto **não se anulam**.
- Se `truncated=true`, mostrar “TOP N de total_groups grupos”; **não** afirmar que a grade contém todos os itens.

**Visual recomendado:** tabela compacta com Código | Descrição | Natureza | Qtd. | R$, ordenada por valor. Para visual adicional, barras horizontais com Top 10 impactos. Definir destaque de faltas em vermelho, sobras em outra cor.

## 5. Disponibilidade no TV Dashboard

Os operationIds acima possuem overlays em `tv-dashboard-api/tv_app/content/tv_data_route_overlays.json` com nomes em português, campos de valor, filtros, tipo recomendado de gráfico e limites.

O **catálogo runtime é reconstruído do OpenAPI da api-delpi**, após deploy/sincronização. `tv-dashboard-api` usa o overlay versionado; portanto a ordem de deploy recomendada é:
1. `api-delpi` (novas rotas no OpenAPI);
2. `tv-dashboard-api` (overlays e sync de OpenAPI após a API subir).

Sem sync bem-sucedido, rotas novas **não aparecerão na seleção de fontes**. Procedimento de ressincronização já existente: `scripts/homologacao/sync-api-delpi-openapi-tv.sh`, ou opção administrativa `POST /apps/tv-dashboard-api/data/openapi/sync` autorizada.

**A implementação NÃO cria a tela, slideshow ou programação.**

## 6. Testes e critérios de aceite

- `pytest api-delpi/tests/test_tv_inventory_divergences_1598.py -q` (períodos, mês faltante, limites, furo/sobra não compensados, SQL agregado antes do TOP, contrato das rotas).
- `pytest tv-dashboard-api/tests/test_inventory_divergence_1598_overlays.py -q` (opIds/colunas da curadoria, sem depender do servidor).
- Verificar 401/403 sem `api-delpi.access`; parâmetros inválidos rejeitados; `branch=01/02/all`, armazéns, virada de mês/ano e ano bissexto.
- Em HML: comparar cada total com `GET /supplies/inventory-adjustments/summary` nos mesmos filtros (01/01→data de referência e dia 1→data de referência); comparar amostra de TOP itens com movimentos reais do Protheus.
- Em TV Dashboard: confirmar 3 rotas no seletor de fontes, duas métricas monetárias, série mensal, tabela semanal e coerência visual/legibilidade em 16:9.
- Confrontar mês fechado com R07 **com ressalva do custo as-of**; validar com Controladoria se o painel diário exigirá série histórica congelada para fechamento.
- **Refresh operacional recomendado: a cada 5–10 minutos**, sem consulta pesada a cada frame.
- Status da demanda: **rotas propostas em PR, sem deploy nem homologação funcional nesta fase**. Chamado permanece aberto até a TV ser montada e validada.

## Referências

- `api-delpi/app/domain/services/supplies/inventory_adjustment_service.py`: classificação oficial do SD3 INVENT por CF;
- `api-delpi/app/infrastructure/persistence/totvs/supplies_repositories/inventory_adjustments_repository.py`: resumo e detalhes operacionais;
- `api-delpi/app/interface/http/routes/financeiro/stock_kardex_router.py`: R07 mensal do Financeiro;
- `docs/12-roadmap-e-evolucao/controllership-finance/fichas/R07-ficha.md`: status de paridade do fechamento;
- `tv-dashboard-api/README.md`: sync OpenAPI e catálogo de dados.
