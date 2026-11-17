# GLPI #1567 — Frete sobre compras (paridade com Portal Financeiro)

## Histórico e motivo da correção (17/11/2026)

A PR #225 implementou uma primeira versão em **Portal Suprimentos → Análises → Frete sobre compras**. A solicitante percebeu diferença entre os valores por NF desse indicador e o relatório de **Fretes** do Portal Financeiro, cujo rateio já foi validado.

**Causa identificada na comparação dos fontes:** o código antigo de Suprimentos somava `SD1010.D1_CUSTO` para mercadorias e frete, enquanto o Financeiro utiliza `SF1010.F1_VALMERC` para a mercadoria e `SF1010.F1_VALBRUT` para o CT-e. O Financeiro também reparte o valor bruto de cada CT-e proporcionalmente entre **todas** as NFs vinculadas, inclusive as fora da data consultada, resolve centavos residuais e identifica vínculos inconsistentes. Os dois métodos não podem produzir valores idênticos.

## Regra vigente proposta

1. O indicador consulta o mesmo contrato de vínculos NF x CT-e `GetPurchaseFreightLinksUseCase` e a mesma SQL `purchase_freight_sql.py`, com leitura da SF8/SF1 e valor de mercadorias e CT-e. Não há gravação no Protheus.
2. A regra matemática de `FreightAllocationService` e o conteúdo de `freight.json` são cópias **byte a byte** dos arquivos do Financeiro mantidos em `shared/delpi_freight`. Uma regressão em `shared/tests/test_freight_financial_parity.py` exige que as cópias acompanhem qualquer alteração futura, impedindo divergência silenciosa. **O serviço financeiro original não foi alterado.**
3. Rateio de cada CT-e: `F1_VALBRUT(CTe) × F1_VALMERC(NF) / ΣF1_VALMERC(todas NFs vinculadas ao CT-e)`. Arredondamento `ROUND_HALF_UP` a dois decimais e ajuste residual na NF de maior valor; a soma dos rateios fecha com o bruto do CT-e.
4. Por NF: soma de todos os rateios dos CT-es vinculados / valor das mercadorias da nota × 100. Valor e percentual calculados com `Decimal`, iguais aos do Financeiro.
5. Situações e metas do Financeiro: **01 Matriz SC = 3,25%** e **02 Filial ES = 4,25%**. Acima da meta somente quando o percentual **exibido após arredondamento** supera o limite da própria filial. Igual ao limite = dentro da meta. Vínculos inválidos = inconsistente e não entram no consolidado.
6. Consolidado: soma de fretes rateados / soma dos valores das mercadorias apenas das NFs com vínculo **consistentes**. O filtro de situação afeta a listagem, sem modificar KPIs. NFs sem qualquer vínculo de CT-e **não pertencem a essa base**. O total difere, por definição, de um indicador de frete dividido por TODAS as compras nacionais.
7. Mensal: aplica a mesma razão por competência de **emissão** da NF. A consulta permite escolher período de emissão ou de digitação, como no Financeiro; a evolução permanece agrupada por emissão.

### Contrato e apresentação

- `GET /supplies/freight-impact` na api-delpi permanece protegido pelo escopo de Suprimentos e passa a usar `GetPurchaseFreightLinksUseCase` por filial, consultando o CT-e inteiro para fechar o rateio. A resposta não é entregue se houver truncamento de vínculos de uma filial (limite do contrato financeiro: 20.000).
- `GET /analytics/freight-impact` na supplies-api mantém `supplies.access` e `require_units("branch")`; repassa `date_mode` e `situation`, preservando a autorização por unidade e o acesso interno restrito.
- `plugins/supplies/src/features/freight-impact` mostra KPI de notas acima da meta, metas de cada unidade, filtro `Situação`, linha/percentual **vermelhos** quando acima, alerta de inconsistência e grade com as mesmas informações relevantes do Financeiro: nota, fornecedor, emissão, digitação, valor das mercadorias, frete rateado, percentual, meta e situação. `Ver rateio` mostra cada CT-e, transportadora, valor bruto, base, quantidade de NFs, parcela da NF e chave do documento.
- O Manual da Ajuda foi atualizado com a nova metodologia, metas, diferenças entre base com e sem vínculo e dúvidas sobre rateio.

## Testes e aceite

- `pytest api-delpi/tests/test_supplies_freight_impact.py`: múltiplos CT-es, um CT-e dividido entre duas NFs, NF fora do filtro participando da base, metas, fronteira exata, inconsistências e total global.
- `pytest shared/tests/test_freight_financial_parity.py`: identidade dos arquivos de rateio e metas em relação ao Financeiro.
- `cd plugins/supplies && npm run ci`: lint, contratos de query, testes e build.
- Checar API em HML: permissão de filial 01/02, 401/403, truncamento, datas emissão/digitação, situação e tempo de consulta. **Não rodar varreduras pesadas diretamente em produção.**
- Comparar com o Portal Financeiro pelo menos 10 NFs de cada filial (incluindo 1 CT-e multi-NF, mais de 1 CT-e na mesma NF, e NFs com inconsistência). Filtrar pelos mesmos períodos, unidades e situação **Todas**. Para cada NF conferir mercadorias, CT-e bruto, base rateada, valor rateado, % e meta. Validar total consolidado e destaque acima do limite com Joici/Fiscal.
- Publicar somente após aprovação e execução do CI. Ordem: `api-delpi`, `supplies-api`, `supplies`. Não é necessário rebuild do `financial-api`, cuja implementação homologada foi mantida.
- **Status:** código proposto para PR de correção. Não marcar o chamado como solucionado sem validação real dos valores.

## Histórico técnico

- PR #225: versão inicial por `D1_CUSTO`, já integrada. Seus resultados históricos **não** devem ser interpretados como equivalentes ao Portal Financeiro.
- PR #228: primeiro manual de ajuda, substituído nesta correção pela explicação da metodologia do Financeiro.
- Demanda atual: comparabilidade e rateio exato por NF, metas 3,25%/4,25%, destaque vermelho e situação acima da meta.
