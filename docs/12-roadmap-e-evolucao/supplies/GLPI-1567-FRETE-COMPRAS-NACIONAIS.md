# GLPI #1567 — Percentual de frete sobre compras nacionais

## Requisitante e objetivo

Solicitação de Joici Motta: percentual geral dos fretes nacionais sobre todas as compras nacionais, mais percentual individualizado por nota fiscal, com referência à customização Protheus **DLP02R01.PRW**, `02.Compras/` do repositório `Delpi-ti/protheus-erp`.

## Entrega técnica (branch feat/glpi-1567-supplies-freight-impact)

- **api-delpi:** `GET /supplies/freight-impact` (01/02, emissão de NF, até 367 dias, 25/100 por página). Consulta somente leitura em `SF1010`, `SD1010`, `SF8010` e `SA2010`.
- **supplies-api:** `GET /analytics/freight-impact`, protegido por `supplies.access` e autorização de todas as filiais solicitadas, com autenticação serviço-a-serviço já adotada.
- **plugins/supplies:** `/apps/supplies/analytics/freight-impact`; catálogo de Análises com KPI percentual ponderado, valor das compras, fretes, NFs com/sem vínculo, evolução mensal, tabela por NF, paginação e estados de erro/vazio/carregamento.

## Regra de cálculo

- **Denominador:** soma `D1_CUSTO` dos itens das NF-e de entradas normais (SF1: `F1_TIPO='N'`, `F1_ESPECIE='SPED'`; SD1: `D1_TIPO='N'`) de fornecedores com UF brasileira cadastrada em `SA2010.A2_EST`. Inclui NFs **sem CT-e**.
- **Numerador:** soma `D1_CUSTO` de itens de CT-es (SF1: `F1_ESPECIE='CTE'`), relacionados pela SF8 e pela origem de item `D1_ITEMORI` / `D1_SERIORI`; apenas frete associado às NFs do denominador.
- **Global:** `SUM(frete) / SUM(compras) * 100`, **não** média de percentuais de NFs. A série mensal aplica a mesma razão à emissão de cada NF.
- **Por NF:** `frete_NF / compras_NF * 100`. CT-e sem vínculo retorna zero de frete, **não** quer dizer que o transporte foi gratuito ou inexistente. Valor da NF sem custo positivo (ou frete negativo) é apresentado como não calculável e não integra o consolidado.
- Deduplicação de vínculos na SF8 por combinação de chave completa da NF e do CT-e. Nenhum dado é escrito no ERP.

## Limitações e pontos obrigatórios de homologação

1. **Definição de compras nacionais:** a UF brasileira do cadastro do fornecedor é uma aproximação operacional. Comparar com os critérios fiscais adotados na Delpi (por exemplo, `A2_CODPAIS` e CFOP) antes de classificar o KPI como definitivo.
2. **Definição de fretes nacionais:** inicialmente CT-e de origem vinculada a NF nacional, sem validação independente do país da transportadora. Se houver transportadora estrangeira, ajustar o filtro.
3. **Reconciliação DLP02R01:** conferir 5 a 10 NFs com uma ou mais linhas de origem, múltiplos CT-es e um CT-e com múltiplas NFs. Verificar que `SUM(D1_CUSTO)` corresponde ao relatório, inclusive diferentes TES/critério financeiro e dias de emissão/digitação.
4. **Qualidade de dados:** validar comportamento de documentos cancelados/devoluções, cadastros nacionais sem UF, vínculos órfãos SF8 e CT-es com itens especiais. Esses casos **não** foram contabilizados em indicadores específicos nesta primeira entrega.
5. **Performance:** período limitado a 367 dias e 50.000 NFs para evitar truncamento silencioso. Confirmar tempo/índices SQL no HML; não realizar testes pesados no servidor de produção.
6. **Validações automatizadas ainda necessárias:** executar `pytest api-delpi/tests/test_supplies_freight_impact.py` no ambiente apropriado e `npm run ci` em `plugins/supplies`; revisar a UI em viewport desktop e mobile.
7. **Segurança:** confirmar em HML permissões 401/403 por perfil, consulta por filial 01/02 e bloqueio de acesso sem autorização.

## Situação

Código proposto em branch isolada; requer CI, QA fiscal, homologação com Joici e deploy deliberado. **Não marcar o chamado como solucionado antes de validação.**
