# Ciclo 1 — CC matriz: inventario conceitual sanitizado

Status: TO_INVENTORY. Escopo: PROC-0072, Central de Fechamento. Documento conceitual; nao contem dados fiscais, linhas, valores, IDs de produtos, fornecedores ou documentos privados.

## Evidencia de processo
- Na demonstracao AS-IS, a responsavel usa extracao de itens de notas fiscais de entrada, com origem declarada SD1 no TOTVS/Protheus.
- Seleciona filial e periodo de digitacao do mes de referencia; aplica exclusoes de tipos de entrada e de materias-primas; revisa centro de custo, produto, contas e itens excepcionais.
- O objetivo do artefato e classificar movimentacoes elegiveis entre custos/despesas diretos, indiretos e administrativos para envio a Contabilidade.
- O video registra verificacoes manuais, regras de excecao, cadastro incorreto e necessidade de revisao humana.

## Evidencia estrutural observada em arquivo privado, SEM replicacao de dados
- Exportacao identificada como SD1 e tabular, contendo colunas equivalentes a filial, item de NF, produto, tipo de produto, tipo de entrada, centro de custo, conta contabil, valor e data de digitacao.
- Existe coluna de classificacao com categorias Direto, Indireto, Adm, sem cabecalho. Nao presumir tratar-se de campo nativo do TOTVS.
- O arquivo recebido pode ser resultado filtrado/tratado; nao equivale necessariamente ao universo bruto da SD1.
- Nomes exibidos no relatorio podem ser aliases; requer mapeamento ao dicionario fisico do ERP.

## Hipoteses a verificar
1. Owner ERP/API: localizar campos fisicos SD1, integridade filial/chave, soft deletion, joins e aliases de exportacao.
2. Obter catalogo de TES, seus significados e regra exata de elegibilidade; confirmar em amostra controlada sem expor dados.
3. Descobrir cadastro canonico de produtos/tipos e exclusao MP, inclusive excecoes e vigencia.
4. Inventariar cadastro de centros de custo, descricao, validade, hierarquia e eventual classificacao gerencial ja persistida.
5. Distinguir centro de custo, classificacao gerencial e decisao de elegibilidade; validar tratamento de itens sem centro ou com cadastro invalido.
6. Especificar base monetaria correta (total bruto, descontos, impostos, outras despesas) e reconciliacao com contabil, sem assumir que Vlr.Total e custo DRE.
7. Identificar aprovador humano, regras de override com justificativa, revisoes, trilha auditavel, versao da competencia e fechamento por filial.
8. Comparar regras do AS-IS com transformacoes efetivamente existentes em codigo, API e dashboards; busca sem resultado nao comprova ausencia.

## Guardrails
- Arquivo original, texto colado, linhas de registros, totais, documentos e atributos fiscais especificos NAO podem ser versionados no GitHub.
- Conservar apenas conceitos e resultados agregados nao sensiveis apos revisao; nunca copiar payloads reais em issues, logs ou testes.
- Nenhuma regra de classificacao e aprovada como contrato ou codigo ate validacao por owner/PO; sem inferir prefixos como regra universal.
- Integrações por api-delpi e BFF do Portal; Core resolve permissoes efetivas, somente controllership-finance.access/manage.
- Fase atual: READ/VERIFY/CLASSIFY; implementacao e persistencia de lancamentos sao PLANNED e exigem gate.

## Proximo passo
Inventario de dicionario SD1 + cadastro de centros de custo + TES + cadastro de produtos, com evidencia e owners. Depois matriz RQ/AC de elegibilidade, classificacao, excecoes e conciliacao. Referencia AS-IS: trecho da reuniao de acompanhamento do fechamento mensal, aproximadamente 44:28 a 50:35 (tempos narrados a confirmar na fonte integral).
