# Portal PCP: excluir pedidos de venda de matéria-prima MP (#1552)

## Problema
A carteira de pedidos de venda de matérias-primas (SB1.B1_TIPO = MP)
aparecia na aba Demandas. Quantidades em KG, MT e outras unidades eram
misturadas aos produtos sob responsabilidade produtiva do PCP, distorcendo
tabela, gráficos, KPIs e sugestões de novas OPs.

## Escopo
Exclusivamente **pedidos de venda** da aba Demandas / Gestão à Vista do PCP,
para as filiais 01 e 02. Não alterar documentos do TOTVS nem ocultar vendas
de matérias-primas em módulos Comercial, Expedição ou Faturamento. Não
interferir nas necessidades MyWEG genuínas.

## Como foi implementado
1. A consulta global api-delpi de pedidos abertos, que já possui JOIN em
   SB1010, passou a incluir **B1.B1_TIPO como tipo_produto**; o use case
   preserva o campo no payload e normaliza espaços/caixa.
2. O endpoint global continua retornando MP para os consumidores que
   precisam dela. Não foi aplicada cláusula SQL global para exclusão.
3. DemandCoverageService do PCP descarta linhas **Protheus**
   classificadas como MP **antes** de qualquer alocação de estoque/OP.
4. MyWegDemandCoveragePreviewService também exclui pedidos MP do
   conjunto Protheus **antes** da classificação de sobreposições,
   pool de estoque e composição dos cenários, sem remover necessidades
   coletadas do cliente MyWEG.
5. O mesmo conjunto filtrado gera lista, resumo, clientes, prazos,
   gráficos de horizonte e pendências de inclusão de OP. Não há
   filtro meramente visual nem recálculo paralelo no frontend.

## Regras de confiabilidade
- Reconhecer somente o código de tipo **MP** (case/whitespace-insensitive).
- Preservar PA, PI e tipos não informados para não inferir tipo sem cadastro.
- Preservar o filtro existente de entidade CLIENTE vs FORNECEDOR.
- A distinção usa classificação oficial SB1.B1_TIPO, não prefixos de
  códigos de materiais.
- Não apagar rupturas de estoque no card Pendências: esses alertas são
  uma categoria distinta, calculada por outra fonte.

## QA e publicação
Testes de regressão incluem:
- classificação MP vs PA/PI/sem tipo;
- alocação de estoque após retirar MP;
- exclusão em resumo, lista, gráfico de horizonte, paginação e pendência;
- filiais 01/02;
- consolidação Protheus/MyWEG sem overlap falso;
- necessidades MyWEG legítimas preservadas;
- contrato API global de pedidos sem exclusão de MP.

Ajustes em serviços: **api-delpi** e **production-control-api**.
O frontend não requer rebuild para este chamado, pois o contrato existente
já entrega tabela/gráficos a partir do backend.
Antes de encerrar o #1552, publicar os serviços e conferir ambas as filiais
com o botão Atualizar na aba Demandas e na Gestão à Vista. Sem migrações.
