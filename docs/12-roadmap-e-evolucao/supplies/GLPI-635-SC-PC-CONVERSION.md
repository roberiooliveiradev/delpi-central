# GLPI #635 · PROC-0075 · Tempo de conversão SC → PC após liberação

Data: 2026-11-16. Status: implementação em PR; sem validação de produção nem aceite de Joici/Compras.

## Contrato de negócio

**Início:** data da **última liberação válida** da alçada de compras, proveniente exclusivamente da SCR010 (CR_TIPO='SC', CR_STATUS='03', CR_DATALIB preenchida, CR_USERLIB/CR_LIBAPRO comprovados), condicionada a SC1010.C1_APROV='L' em todos os itens. Não se mede desde a abertura da SC.

**Fim:** C7_EMISSAO do **primeiro PC comprovadamente vinculado** a um item da mesma SC, via C7_FILIAL/C7_NUMSC/C7_ITEMSC = C1_FILIAL/C1_NUM/C1_ITEM. PCs concluídos e parciais são elegíveis. Excluir registros logicamente excluídos.

**Fórmula:** DATEDIFF(day, final_approval_date, first_order_date), em **dias corridos**; mesmo dia = 0. TOTVS oferece datas sem horários, então o cálculo não é por horas úteis.

**Grão:** uma SC distinta por filial/número, mesmo com muitos itens, PCs ou níveis SCR. Competência por data da **última liberação**, não pela criação da SC nem pela data do PC. Primeiro PC mede início da conversão, não atendimento integral.

**Exceções fora da média:**
- pending = SC liberada sem PC vinculado;
- order_before_release = PC emitido antes da última liberação, inclusive possíveis reaprovações;
- invalid_order_date = PC com data ou identificação inválida;
- SC sem SCR íntegro ou com itens ainda pendentes não entra no universo aprovado.

Média consolidada = soma dos dias de SCs validamente convertidas / quantidade de SCs convertidas. Não tirar média simples das filiais.

## Arquitetura

1. api-delpi: SQL read-only sobre SC1010/SCR010/SC7010 no repository do domínio Suprimentos. GET /supplies/purchase-requests/sc-pc-conversion. Protegido por token interno e identidade do chamador. strategic-indicators-api pode ler exclusivamente com summary_only=true e sem request_number.
2. supplies-api: GET /purchase-requests/sc-pc-conversion aplica supplies.access e escopo autorizado de filial, rejeita filtros extras e origem inconsistente.
3. plugins/supplies: /apps/supplies/purchase-requests/sc-pc-conversion, link nas Solicitações, catálogo do portal, cards, distribuição por prazo, pesquisa SC e listagem paginada com links SC/PC.
4. strategic-indicators-api: fornecedor lê apenas sumário por filial, preserva null quando a fonte está indisponível e publica a média ponderada. Migração V035 cria supplies-sc-pc-conversion-days com peso 0, sem meta de desempenho inventada, e branch_value_aggregation=source_consolidated.

## Regressões planejadas

- api-delpi: pytest tests/test_purchase_request_sc_pc_conversion.py
- supplies-api: pytest tests/interface/http/test_purchase_request_sc_pc_conversion.py
- strategic-indicators-api: pytest tests/test_supplies_sc_pc_conversion.py
- plugins/supplies: npm test -- --run src/features/purchase-requests/scPcConversionApi.test.ts && npm run build
- Smoke autenticado, filtro por filial, datas, competência, paginação, links para SC/PC e tratamento de erros.

## Homologação e publicação

1. Revisar amostras reais com Compras: SCR final, SC liberada, primeiro PC, PCs parciais, reaprovação após PC, pendências e histórico SCR ausente.
2. Validar consulta read-only no Protheus, médias por unidade e consolidado, valores nulos, performance e datas de fronteira da competência.
3. Verificar acesso S2S ao resumo estratégico e aplicar migração V035 em ambiente controlado. Confirmar apresentação do KPI com peso zero e sem meta.
4. Executar CI/testes e smoke autenticado antes do deploy. Não confundir código na branch com produção. O GLPI #635 permanece aberto até aceite.
5. Atualizar PROC-0075 e GLPI #635 com link da PR e evidências após homologação.

## Limitações

- Datas inteiras; sem horas/minutos.
- Reaprovação posterior ao PC produz anomalia, nunca prazo negativo.
- Primeiro PC não equivale a conversão integral do pedido.
- Links interfiliais ou registros excluídos podem exigir revisão de dados.
- Leitura SQL segue o padrão NOLOCK do indicador de aprovações existente. Exige conferência antes de decisão gerencial.
