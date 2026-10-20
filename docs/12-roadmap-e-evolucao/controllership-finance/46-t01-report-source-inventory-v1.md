# 46 — T01 REPORT-SOURCE-INVENTORY V1 — PROC-0072

> **Data da captura:** 20/10/2026. **Estado:** DOCUMENTED / PARTIAL / TO_INVENTORY. Inventário documental de sources; não autoriza runtime, SQL write, grants, migration nem endpoint novo. Evidência TÉO = AS-IS; GitHub = TARGET/runtime. Um search miss não prova ausência física.

## 1. Proveniência consultada

- TÉO `record_read(process=PROC-0072)`: processo `21f70cd0-d513-46f5-bfcf-29ae5573f2f6`; instância `fa3074bd-c852-44d1-b145-72a2f17043d6`; baseline `85358475-3fbf-4bec-9f48-56ec15706b34`.
- TÉO `record_read(decomposition_tree, get)`: tarefas/subtarefas da decomposição; `record_read(process_diagram, get)`: cinco raias de execução e os caminhos de revalidação.
- TÉO `record_read(process_document, search)`: 43 registros documentais catalogados (inclui 06, 06.2, 31.14, 31.18, 33 e 34); catálogo não substitui conteúdo binário.
- GitHub: `02-proc-0072-as-is-e-baseline.md`, `03-evidencias-proveniencia-e-rastreabilidade.md`, `17-backlog-de-confirmacoes-e-inventarios.md`, `21-boundaries-produtos-e-owners.md`, `45-g0-excecao-fastapi-e-fechamento-gates.md` §15, inventário CF-CLOSING-PREDECESSORS-01 entregue pelo executor.
- DAVI `discover_delpi_information`: capacidades de `get_protheus_table`, `search_protheus_columns_by_description`, `get_supplies_stock_value` descobertas. **Nenhuma execução SQL arbitrária autorizada; nenhum dado de linha/coluna física comprovado nesta revisão.** Requer consultas tipadas subsequentes.
- Vídeo: doc 03 registra MP4 original (~54m44s; SHA-256 documentado), mas derivação aponta 01:02:15; `TIMECODE_PROVENANCE=STALE_EVIDENCE`; vídeo original ainda **não reexaminado**. Não atribuir timecodes observados.

## 2. Macroetapas do processo (TÉO — AS-IS)

| Etapa | Grupo da decomposição | Coletas/documentos e operação |
|---|---|---|
| 01 | kp01 Preparar e controlar competência | checklist, entregáveis aplicáveis, período mensal |
| 02 | kp02 Financeiro e bancos | FINR190 pagar/receber e ordenações; extratos, aplicações, cartões, prova sem movimentação |
| 03 | kp03 Importações | planilhas de fechamento/internalização, dossiês, documentação de câmbio e rastreio |
| 04 | kp04 Estoque/custos/consumo | P7 padrão/Bloco H, consumo OP, entradas/saídas, Kardex 01/99, CPV, MOD, H02, inventários, notas por CC, Acompanha Custos, custo reposição, Refaz Saldos; repetir por filial aplicável |
| 05 | kp05 Fiscal/contábil | documentos aplicáveis, obtenção direta pela Contabilidade, destinatários |
| 06 | kp06 Conferência | parâmetros/período/completude, conciliação Entradas/Saídas x P7 x H02 |
| 07 | kp07 Pendências | solicitar complementos e investigar diferenças por grupo/material |
| 08 | kp08 Corte/estoque/pacote | confirmar fim das movimentações, sacramentar estoque no Protheus, consolidar e enviar pacote |
| 09 | kp09 Esclarecimentos | dúvidas/complementos pós-envio; só depois conclusão do ciclo |

## 3. Inventário inicial por saída / relatório

IDs de inventário são locais ao doc, **não** códigos nativos de relatório.

| ID | Artefato ou atividade coletada | Rotina/identificação documentada | Fonte física/HTTP | Situação |
|---|---|---|---|---|
| R01 | Baixas a pagar, Excel e PDF por DATA/NATUREZA | FINR190 (TÉO); `_F190C` (relato audiovisual derivado); FINSV010 (substituto oficial TOTVS, não equivalente provado) | Tabelas, filtros e joins TO_INVENTORY | SOURCE DOCUMENTED |
| R02 | Baixas a receber, PDF/Excel | FINR190 (TÉO); `_F190C` (relato audiovisual derivado); FINSV010 (substituto oficial TOTVS, não equivalente provado) | Tabelas, filtros e joins TO_INVENTORY | SOURCE DOCUMENTED |
| R03 | P7 padrão e layout Bloco H | MATR460, **não** MATR860 | Tabelas/algoritmo e output a conferir | SOURCE DOCUMENTED |
| R04 | Consumo / Relação por OP | MATR860 | Tabelas e colunas TO_INVENTORY | SOURCE DOCUMENTED |
| R05 | Entradas e Saídas / valor estoque | Relatório operacional a confirmar | api-delpi `GET /supplies/stock-value` adjacente; SB9/SD3/SB2 conforme executor; **não declarar equivalência** | PARTIAL |
| R06 | CPV e Kardex armazém 01 | Kardex01, filtros CFOP | `get_supplies_cpv` adjacente; relatório completo TO_INVENTORY | PARTIAL |
| R07 | Inventários e Kardex armazém 99 | Kardex99 / INVENT | Source físico TO_INVENTORY | SOURCE DOCUMENTED |
| R08 | Material em Processo | H02 | SC2 como proxy adjacente **não equivalente**, conforme inventário; fonte correta TO_INVENTORY | BLOCKED |
| R09 | Faturamento x MOD | Planilha exportada, desmesclar/converter numérico | Fonte e regra de transformação TO_INVENTORY | SOURCE DOCUMENTED |
| R10 | Notas/itens NF por centro de custo | SD1 mencionado no AS-IS | Chaves/colunas/escopo TO_INVENTORY | SOURCE DOCUMENTED |
| R11 | NF venda 9035 / CPV valor zero | Documento do checklist | Fonte/CFOP/regra TO_INVENTORY | SOURCE DOCUMENTED |
| R12 | Acompanha Custos, Custo Reposição, Refaz Saldos | Rotinas anteriores à extração P7/estoque | Operações no ERP; **não presumir leitura equivalente nem autorizar writes** | SOURCE DOCUMENTED |
| R13 | Extratos, aplicações, cartões, XP/BB/Bradesco/Sicoob | Documentos externos; XP depende de Dennis | Ownership externo; não presumir tabela Protheus | EXTERNAL |
| R14 | Importação: SWIFT, contrato câmbio, encontro contas, ACSI e planilhas | Fontes mistas | Mapear origem documento versus ERP; sem equivalência inferida | MIXED |
| R15 | Confirmação cutoff e sacramentação | Estado owner ERP | `get_supplies_stock_value` / SB9 com `official_closure_on_period_end` **candidato**, não aceite semântico de `STOCK_CLOSED` | T03 BLOCKED |

**Documentação disponível não basta para inferir nomes de colunas, joins, filtro `D_E_L_E_T_`, empresa/filial ou versão de rotina.** Registrar esses detalhes somente após catálogo DAVI/metadados tipados e paridade.

## 4. Regras/alertas já comprovados

1. `MATR860 != MATR460/P7`. Não igualar relatórios por proximidade de nome.
2. Paridade P3 exige `Entradas/Saídas - P7 - H02 = R$ 0,00` **até os centavos**, sem tolerância ou arredondamento implícito (doc 06.2/TÉO).
3. `STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED`.
4. `BANK_SCOPE_DRIFT=PRESENT`: checklist e procedimento divergentes; banco/conta configurável, seed a confirmar.
5. Escopo 01/03/04 (empresas em procedimento contábil) **não** pode ser automaticamente convertido em `branch=01/02` do endpoint de Suprimentos.
6. A presença de SB9 / último fechamento por filial é **candidata** a T03, mas não demonstra por si só o estado de negócio canônico de estoque fechado.
7. Dados externos (banco, cartão, câmbio, dossiê) não têm tabela ERP pressuposta.
8. Fonte técnica do Protheus pertence à `api-delpi`; orquestração/contexto/ownership da competência na BFF `controllership-finance-api`; MFE não acessa api-delpi diretamente.

## 5. Matriz de execução pendente, por prioridade

| Prioridade | Prova de inventário | Owner | Estado |
|---|---|---|---|
| 1 | Analisar conteúdo de procedimento/checklist originais e vídeo com timecodes reconciliados; exportar cada filtro/coluna amostral | TÉO / Controladoria / documentos | TO_INVENTORY |
| 2 | Pesquisar via DAVI dicionário de tabelas e colunas para FINR190, MATR460, MATR860, SB9, SD3, SB2, H02, Kardex e movimentos | DAVI + owner api-delpi | TO_INVENTORY |
| 3 | Identificar a consulta read-only de cada saída: chave, filial, competência, temporalidade, moeda e tratamento de exclusão lógica | api-delpi/ERP | TO_INVENTORY |
| 4 | Comparar, com extratos sanitizados, volume/total/linhas de cada relatório e resposta estruturada no mesmo período e parâmetros | Controladoria + api-delpi | TEST_NOT_RUN |
| 5 | Verificar resource scope/eligibilidade Core T05, autoridade de abertura da competência e distinção empresa/filial | Core + produto | TO_INVENTORY / DECISION_REQUIRED |
| 6 | Validar SB9 como ou contra `STOCK_CLOSED`, com casos de ausência/estimativa/snapshot/fechamento oficial | Owner ERP + P3 | T03 BLOCKED |
| 7 | Escolher owner/persistência de `ClosingCompetence` após prova do lifecycle; manter D3=C | Arquitetura/Produto | DECISION_REQUIRED |

## 6. Critério para novos endpoints e gate

Não implementar endpoint api-delpi/BFF até existir: `report_id → owner → rotina/saída → tabela/coluna e joins → filtro empresa/filial/período → regra canônica → amostra de paridade → contrato DTO → authz/scope → RQ/AC/testes`.

**Estado:** `INVENTORY_PARTIAL`; `IMP-08/P1=NO_GO`; `T01/T03/T05=TO_INVENTORY`; `SQL_VALIDATION=TEST_NOT_RUN`; `VIDEO_PROVENANCE=STALE_EVIDENCE`; `RUNTIME_CHANGED=NO`.

## L1.2 — Reconciliação audiovisual derivada e documentação oficial TOTVS (20/10/2026)

**Evidência derivada, não reprodução direta do vídeo:** NotebookLM reportado pelo usuário: Joici tenta `Shift+F6` / `_F190C` entre `00:43:51–00:46:14`; erro de compilação impede geração. Cinco saídas são apenas verbalmente informadas (Pagar XLS, Receber XLS, Receber PDF/data, Pagar PDF/data, Pagar PDF/natureza). O TÉO `kp02_t01` usa `FINR190`. **IDENTITY_DRIFT_TO_RECONCILE:** possível customização versus rotina padrão; sem afirmar substituição local. `VIDEO_DIRECT_VERIFICATION=TEST_NOT_RUN`.

**Documentação oficial TOTVS (fontes públicas):**
- [TOTVS — Substituição do FINR190 por FINSV010 (19/08/2026)](https://centraldeatendimento.totvs.com/hc/pt-br/articles/42165342299287-Cross-Segmentos-Linha-BackOffice-Protheus-Smartview-Qual-relat%C3%B3rio-subistitui-o-relat%C3%B3rio-de-Baixas-FINR190-no-Smartview): FINSV010 é objeto Smart View de Relação de Baixas; **tabelas lógicas declaradas** `SE1, SE2, SED, F7G, FK1, FK2, FK5, FKA`; campos semânticos descritos: cliente/fornecedor, natureza, vencimento, histórico, data de baixa, valor original, valor pago, juros, multas e taxa permanência. Não inclui movimentos bancários sem título associado.
- [TOTVS — Reestruturação da SE5 na família FKx](https://tdn.totvs.com/pages/viewpage.action?pageId=183730415) e [documentação técnica FKx](https://tdn.totvs.com/pages/viewpage.action?pageId=203760476): FK1/FK2 baixas a receber/pagar; FK5 movimentos bancários; FK7 vínculo título-baixa; FK6 valores acessórios; FKA rastreio. A referência genérica à família não identifica o layout da customização local.
- [TOTVS — Visão de dados FINSV010](https://centraldeatendimento.totvs.com/hc/pt-br/articles/38268207768471-Cross-Segmentos-Backoffice-Linha-Protheus-Smartview-FINSV010-Qual-relat%C3%B3rio-possibilita-a-emiss%C3%A3o-da-listagem-de-baixas): oferece saídas a pagar/receber e exportação de dados XLSX; **não confirma os cinco arquivos personalizados** da Aliança.
- [TOTVS — Baixas parciais e relatórios de posição](https://centraldeatendimento.totvs.com/hc/pt-br/articles/39422738912663-Cross-Segmentos-Backoffice-Linha-Protheus-SIGAFIN-Relat%C3%B3rios-com-exibi%C3%A7%C3%A3o-de-baixas-parciais): FINSV010 é histórico de eventos de baixa, não confundir com posições FINSV005/FINSV013.

**Matriz inicial de entidades físicas candidatos** (sufixo físico do ambiente, schema, colunas exatas, joins, filtros e customização ainda TO_INVENTORY):
`SE1` título receber; `SE2` título pagar; `SED` natureza; `F7G` motivo; `FK1` evento receber; `FK2` evento pagar; `FK5` banco; `FKA` rastreio. DAVI retornou `FK1010.FK1_DATA` e `FK2010.FK2_DATA` no dicionário disponível, **somente metadados**, sem vínculo provado com `_F190C`.

**Próximo limite de auditoria:** G2 somente com nomes de colunas/layout vistos em exportação (ou fonte do programa confirmado), G3 somente quando owner/versão do programa local confirmados, G4 somente quando fonte `_F190C` e bindings físicos/regras forem comprovados; G5 após amostra de paridade. Nenhum novo gate promovido a PASS por similaridade FINSV010. `IMPLEMENTATION_AUTHORIZED=NO`.


## 9. Transição entre relatórios — R01/R02 encerrados como consulta operacional; R03 próximo (PO, 20/10/2026)

**R01/R02:** mapeamento das fontes `FK1/FK2/FK7/SE1/SE2/SED/FKB`, colunas, vínculos, contratos, implementação read-only e página do Portal concluídos conforme relatório de execução e doc 48 §§12–17. Não atualizar retrospectivamente os gates históricos deste inventário como se a paridade com relatório exportado tivesse sido realizada. **Arquivo FINR190/`_F190C` comparável NÃO FORNECIDO neste projeto; `EXPORT_PARITY=TEST_NOT_RUN`**, reservado ao fechamento completo. Ver doc 48 §17.

**Próximo da fila: R03 — P7 padrão e layout Bloco H, rotina MATR460.** É distinto de R04/MATR860 (Consumo/Relação por OP). Status atual `TO_INVENTORY`: não houve ainda inventário de tabelas/campos/joins nem validação de arquivo exportado R03 nesta rodada. Confirmar no TÉO o passo exato, owner, período de estoque/competência, parâmetros, fonte TOTVS, saída e dependência do corte de estoque. Em seguida realizar descoberta DAVI e SQL READ autorizado; buscar export original, mas se não houver registrar `NOT_PROVIDED/TEST_NOT_RUN` sem bloquear a criação futura da consulta operacional. Não criar endpoint ou equivalência por analogia a R01/R02.

**Método obrigatório por relatório:** AS-IS TÉO + owner; relatório/export e proveniência; colunas/tabelas SQL (DAVI); joins/cardinalidade/filtros; contrato api-delpi → BFF → visual; testes/smoke; comparação com export se presente; documentar lacuna de paridade se ausente; commit e evidências. GO de design/implementação separado por item.


## 10. R03 — Fase A, investigação SQL real para reproduzir P7/MATR460 (20/10/2026)

**Escopo:** investigação READ-only DAVI, sem alteração de runtime. GitHub TARGET, TÉO authority AS-IS. Não confundir o relatório P7 padrão com o Bloco H nem com MATR860.

### 10.1 Proveniência do procedimento (TÉO vs derivado NotebookLM)

- TÉO PROC-0072 identifica emissão **P7 padrão** para conferência de estoque e **P7 Bloco H** quando requerido; confronto de Entradas/Saídas − P7 − Material em Processo com divergência **R$ 0,00**, até centavos, sem tolerância. Joici Motta é a gestora do processo.
- Resposta do NotebookLM **fornecida pelo PO** (DERIVED, não revisão direta do vídeo): apresenta emissão P7 padrão e layout H, data 30/09/2026, filiais 01/02, relatório padrão supostamente 91 páginas, total de R$ 3.776.994,69, Insumos R$ 266.321,45, impressão/PDF e conciliação preliminar. Os timecodes derivados chegam após 01:00, mas o MP4 cadastrado no doc 03 dura 00:54:44: **STALE_EVIDENCE / TIMECODE_RECONCILIATION_PENDING**. O código MATR460 está associado à documentação, mas não foi visualizado na gravação conforme a resposta. PDF original/params/export não fornecidos; `EXPORT_PARITY=TEST_NOT_RUN`.
- A diferença aritmética entre Entradas/Saídas R$ 3.890.247,18, P7 R$ 3.776.994,69 e H02 R$ 64.591,71 é R$ 48.660,78 (ainda **derivada**, não homologada). A divergência entre R$ 266.321,46 e R$ 266.321,45 é R$ 0,01, não R$ 0,25 como afirmado no texto derivado. Nunca promover aceitação de arredondamento sem decisão de owner.

### 10.2 Fontes SQL físicas, consultas read-only DAVI

- Catálogo `sysobjects`: tabelas `SB1010`, `SB2010`, `SB6010`, `SB9010`, `SC2010`, `SD1010`, `SD2010`, `SD3010`, `SF4010` e `SX6010` presentes. **Existência física não prova uso pela MATR460.**
- `SB9010`: `B9_FILIAL`, `B9_COD`, `B9_LOCAL`, `B9_DATA`, `B9_QINI`, `B9_QISEGUM`, `B9_VINI1..5`, `B9_VINIFF1..5`, `B9_CM1..5`, `B9_CUSTD`, `B9_MCUSTD`, `S_T_A_M_P_`, `I_N_S_D_T_` identificados no schema. Campos numéricos de saldo/custo `float`.
- `SB1010`: `B1_FILIAL`, `B1_COD`, `B1_DESC`, `B1_UM`, `B1_TIPO`, `B1_GRUPO`, `B1_CUSTD`, `B1_CC`. `B1_FILIAL=''` nos 55.314 produtos ativos observados. Na amostra da filial 01 de 30/09/2026, LEFT JOIN `SB9.B9_COD=SB1.B1_COD` filtrando `D_E_L_E_T_=''` teve **zero SB9 sem SB1**; isso não garante regra de junção universal.
- `SB9010` em `B9_DATA='20260930'`, ativos: **7.929 linhas**, filial 01 **4.812 linhas / 4.027 produtos / SUM(B9_VINI1)=3.884.439,52**; filial 02 **3.117 linhas / SUM(B9_VINI1)=10.576.487,84**; valor global **14.460.927,36** (moeda funcional ainda não provada, não rotular BRL como resultado do SQL).
- Filial 01, `B9_LOCAL='01'`: 3.945 linhas, **3.524.856,22**; armazém `99`: 753 linhas, **293.334,20**; `98`: 101 linhas, **9.402,08**; demais locais `0`, `03`, `25`, `50` também existem. **Não subtrair 98/99 arbitrariamente**.
- Grupo por `SB1.B1_TIPO` usando `B9_VINI1` em filial 01, data 30/09/2026: `MP=3.364.885,39`, `II=266.321,45`, `PA=190.511,24`, `PI=24.528,59`, demais tipos `=38.192,85`. **II coincide aritmeticamente com subtotal Insumos 266.321,45 informado pelo NotebookLM; não é paridade de relatório**. Total bruto SB9 excede total P7 derivado em **107.444,83**; causa ainda desconhecida (filtros, armazéns, custeio/terceiros/processo etc.). Não ajustar por tentativa-e-erro.
- Há `B9_DATA='20260831'` com 7.813 linhas. O exemplo `SB9.B9_QINI`/ `B9_VINI1` de setembro prova posição histórica; uso exato pelo programa ainda depende de algoritmos/params.

### 10.3 SX6 — configurações observadas na DELPI

Consulta `SX6010`, campo `X6_VAR`/`X6_CONTEUD`: `MV_CUSFIL=A`, `MV_CONTERC=F`, `MV_ALMTERC=''`, `MV_LOCPROC=99`, `MV_M460PRC=.T.`, `MV_MT460EP=.T.`, `MV_R460PRC=1`, `MV_R460TPC=''`, `MV_SDTESN3=1`, `MV_PRODPR0=1` nas filiais 01/02. **Valores físicos PROVEN; semântica exata por release/ponto de entrada PENDING**. A existência de armazém 99 e flags de processo não autoriza classificar seu valor inteiro como WIP.

### 10.4 Saída histórica Bloco H — estrutura observada

`sysobjects`: **19 tabelas `H_%`** presentes (inventários 2023–2025); a mais recentemente criada é `H_2025123101_01` em 05/05/2026 14:23:54, referente no nome a 31/12/2025, com **3.450 registros**, **3.036 produtos distintos** e `SUM(TOTAL)=3.653.871,98`; situações 1 e 2 presentes. **Nenhuma H_ para 30/09/2026 encontrada** nesse inventário. A ausência nessa busca não prova que o relatório padrão não tenha sido emitido.
- Schema físico `H_2025123101_01`: `FILIAL varchar(2)`, `SITUACAO varchar(1)`, `PRODUTO varchar(15)`, `UM varchar(2)`, `QUANTIDADE float(53)`, `VALOR_UNIT float(53)`, `TOTAL float(53)`, `ARMAZEM varchar(2)`, `CLIFOR varchar(6)`, `LOJA varchar(2)`, `TPCF varchar(1)`, `D_E_L_E_T_ varchar(1)`, `R_E_C_N_O_ bigint`, `R_E_C_D_E_L_ bigint`, todos NOT NULL. Essa é **saída histórica candidata ao Bloco H**, não mapeamento integral do cálculo do P7 padrão.
- Último por `R_E_C_N_O_` (=3450): `FILIAL=01`, `SITUACAO=2`, `PRODUTO=50225203`, `UM=MI`, `QUANTIDADE=0.023`, `VALOR_UNIT=253.1304`, `TOTAL=5.822`; sem timestamp do item, não chamar de última atualização.

### 10.5 Lacunas e próxima fase

`R03_PHASE_A=ACCEPT_WITH_RESIDUAL`: fontes candidatas e metadados SQL observados; **não** afirmar algoritmo MATR460 completo, nem correspondência exata do relatório. `MATR460_SOURCE_RULES=TO_INVENTORY`, `ADVPL_CUSTOMIZATION=TO_INVENTORY`, `P7_STANDARD_PARITY=TEST_NOT_RUN`, `BLOCO_H_PARITY=TEST_NOT_RUN`. Fase B: obter versão do programa e perguntas SX1/parametrização/custos, verificar owner e fontes ADVPL ou rotina autorizada; reproduzir linha/grupo em 30/09/2026 e distinguir preliminar de fechamento final; confrontar com PDF original quando disponibilizado. Sem writes no ERP ou endpoints novos nesta fase.
