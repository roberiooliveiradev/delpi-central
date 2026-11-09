# Portal PCP: conciliação FIFO fiscal e necessidades MyWEG (#1551)

## Caso real
Em 09/11/2026, filial 02, o produto 90263918 do pedido 002792 foi
faturado e ainda gerava sugestão de OP para seis peças. Consulta somente
leitura à SD2010 confirmou NF 017071, série 02, item 04, cliente
WEG Linhares 000001/09, emissão 09/11, quantidade 0,006 MI = 6 peças.

## Decisão
Não usar o indicador C6_DATFAT como quantidade fiscal e não dar baixa
na necessidade bruta WEG. Reutilizar itens fiscais SD2/SF2 da rota
totvs-outbound-invoice-line-items da api-delpi, que já fornece
quantity_un normalizado e exclui devoluções/cancelamentos elegíveis.

A conciliação operacional aplica FIFO por produto DELPI confirmado,
ordenando a remessa mais antiga primeiro. O tamanho do pedido de venda
não precisa coincidir com o tamanho da necessidade. A identidade da NF
é filial + documento + série + item e cada item entra uma única vez,
com cálculo determinístico a cada leitura, sem escrita no Protheus.

A camada de planejamento ajusta a necessidade MyWEG **antes** de calcular
estoque, OPs e saldo descoberto. A mesma cobertura abastece a aba Demandas
e o card Pendências. Quando a NF já cobre toda a necessidade, ela não
gera recomendação de OP. Se cobrir apenas parte, só o residual segue.

## Unidade, segurança e temporalidade
Somente filial 02 e WEG Linhares (000001/09), vínculo de produto
confirmado, quantidade em UN normalizada pela api-delpi.
Uma NF em MI nunca deve ser multiplicada novamente no BFF.
Itens com identidade, unidade ou quantidade inconclusiva não entram
num abatimento silencioso.

O Protheus informa D2_EMISSAO apenas na granularidade dia. Para notas
do mesmo dia da última coleta WEG, a aplicação de crédito é provisória
e só ocorre quando collected_at comprova coleta anterior a 06:00
em America/Sao_Paulo; caso contrário o produto entra como pendente
de conferência, sem recomendação definitiva para criar OP.

Ao chegar nova coleta, a janela de NFs é redefinida em função da nova
data de coleta, evitando subtrair novamente notas anteriores. A hipótese
de reconhecimento WEG continua **não comprovada**. Se a WEG não
atualizar a necessidade nas coletas seguintes, a evolução futura deve
considerar comparação de lotes e um ledger persistente de reconhecimento,
para não voltar a recomendar OP desnecessária. Esse risco precisa ser
homologado com duas coletas reais.

Falha na consulta fiscal não equivale a zero faturamento: não se
desconta e as pendências afetadas recebem aviso de inconsistência.

## Contrato aditivo de leitura
Nas linhas MyWEG parcialmente conciliadas:
- raw_myweg_quantity_mi: volume original WEG;
- fiscal_offset_mi: crédito fiscal provisório;
- fiscal_offset_status: provisional_invoice_offset;
- fiscal_invoice_refs: documentos e quantidade usada em cada remessa;
- fiscal_coverage_incomplete: quando não é seguro sugerir OP.

Metadados gerais em myweg.fiscal_reconciliation contêm status, data
da coleta, volume aplicado, itens usados e produtos pendentes.
Linhas integralmente atendidas podem sair da lista de demandas abertas,
mas permanecem contabilizadas no resumo da conciliação.

Nenhuma gravação em estoque, OPs, faturamento ou lotes WEG.

## Validação recomendada
1. Confirmar a NF 017071/02/04 do produto 90263918 (6 peças).
2. Atualizar a Gestão à Vista e verificar o desaparecimento da sugestão
   de nova OP para essas seis peças quando o cutoff permitir o crédito.
3. Simular saldo de 11 peças com NF de 6: restam cinco para cobertura.
4. Testar duas NFs, várias datas, remessa mais antiga, idempotência,
   volume da venda diferente do volume WEG e sobras não negativas.
5. Verificar outros clientes, filial 01, unidade incompatível, NF
   cancelada, fonte indisponível e coleta tardia do mesmo dia.
6. Após a próxima coleta WEG, conferir se o faturamento foi refletido
   pelo cliente sem gerar nova sugestão de OP indevida.

Workflow de testes: .github/workflows/production-control-quality.yml.
Serviços a publicar: production-control-api e production-control.
A api-delpi é reutilizada, sem modificação necessária.
