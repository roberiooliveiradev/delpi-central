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


## 11. R03 — Fase B: prova SQL de reprodução (rodada B1, 20/10/2026)

**Natureza:** execução DAVI `SELECT` read-only; nenhuma execução MATR460, nenhuma escrita em TOTVS, nenhum código/API/UI alterado. Fonte AS-IS: TÉO; referência numérica do vídeo: transcrição derivada NotebookLM fornecida pelo PO, timecodes ainda `STALE_EVIDENCE`.

### B1.1 Baseline e resultado de origem

Em `SB9010` ativa (`D_E_L_E_T_=''`), `B9_DATA='20260930'`, `B9_FILIAL='01'`:
- Total `SUM(B9_VINI1) = 3.884.439,52`, 4.812 linhas, 4.027 produtos. P7 relatado na derivação: **3.776.994,69**; delta fonte − relato **+107.444,83**. **Ainda não reproduzido.**
- `B9_LOCAL='01'`: 3.945 registros, `SUM(B9_VINI1)=3.524.856,22`; `99`: 753 / **293.334,20**; `98`: 101 / **9.402,08**; `50`: 5 / **54.302,52**; `25`: 6 / **2.455,33**; `03`: 1 / **33,17**; `0`: 1 / **56,00**.
- Filtro meramente exploratório excluindo armazéns `98`/`99` produz **3.581.703,24**, não o P7 relatado; não implementar essa exclusão como regra.
- `B9_QINI > 0` somado separadamente pode divergir da soma bruta: armazém 01 contém **−5.038,25** de valor com quantidade zero; armazém 99 contém **+6.315,75** com quantidade zero; armazém 98 contém **−0,05** com quantidade negativa. Total filial 01 com `B9_QINI<>0`: **3.883.162,02**, também diferente do relatório. Isso pode refletir saldos/ajustes e **não** prova defeito da SB9 nem regra P7.
- `SB1010.B1_FILIAL=''` ativo em cadastro, join por `B9_COD=B1_COD` sem ausências na janela verificada. Por `B1_TIPO`: `MP 3.364.885,39`; `II 266.321,45`; `PA 190.511,24`; `PI 24.528,59`; demais `38.192,85`. Subtotal de Insumos igual ao relato do NotebookLM (**coincidência aritmética, não aceite de paridade**).
- Excluindo somente armazém 99, `MP` cai para **3.071.598,77**; o subtipo II permanece em **266.321,45**. A composição do processo exige regra de estoque e não simples exclusão por depósito.

### B1.2 Configuração SX6 na DELPI

Valores `SX6010` comprovados na leitura: `MV_CUSMED=M`, `MV_CUSFIFO=F`, `MV_CUSLIFO=F`, `MV_CUSTRON=.T.`, `MV_CUSZERO=S`, `MV_CUSTNEG=S`, `MV_CUSTCUR=1`, `MV_CUSENT=DIARIO`, `MV_CUSFIL=A`, `MV_LOCPROC=99`, `MV_M460PRC=.T.`, `MV_MT460EP=.T.`, `MV_R460PRC=1`, `MV_R460UNP=.T.`. Valores provam configuração encontrada, **não a semântica/versionamento exatos do código MATR460**.

### B1.3 Metadados adicionais e lacuna do programa

- `SX1010` existe e contém perguntas com `X1_GRUPO`, `X1_ORDEM`, `X1_PERGUNT`, `X1_VARIAVL`, `X1_DEF01..05`.
- Busca exata `X1_GRUPO IN ('MATR460','MATR460A','MATR460B')` retornou zero linhas; busca de grupos com `%460%` retornou candidatos (por exemplo `MTR460`, `MT460A`, `MTA460`) **sem prova de que sejam perguntas da MATR460**. Não atribuir grupo por semelhança. Necessário confirmar versão/source ADVPL, identificador SX1 efetivo e parâmetros completos com owner TI/Protheus.
- `SB8010` (lotes) existe; `TOP 1 *` retornou zero linhas na leitura; isso não demonstra ausência total ou irrelevância de controle de lotes.
- Tabelas `H_*` de 2023–2025 seguem fonte de saída histórica Bloco H; nenhuma série `H_` 30/09/2026 foi identificada no inventário anterior; `H_` não substitui as regras de geração do P7 padrão.

### B1.4 Resultado, classificação e próximos critérios

`R03_PHASE_B1=ACCEPT_WITH_RESIDUAL` **somente para a investigação**; `P7_FULL_REPRODUCTION=INCONCLUSIVE`; `MATR460_SQL_RULES=TO_INVENTORY`; `SX1_PARAMETERS=TO_INVENTORY`; `PROTHEUS_VERSION_CUSTOMIZATIONS=TO_INVENTORY`; `VIDEO_TIMECODES=STALE_EVIDENCE`; `P7_EXPORT_PARITY=TEST_NOT_RUN`. Não declarar `PASS` para a soma P7, nem `OFFICIAL_TOTAL`.

**Para continuar Fase B:** obter pergunta/grupo SX1 validado pela rotina (ou fonte ADVPL/trace autorizada), layout P7 de 30/09/2026 e parâmetros de emissão, confirmar o corte/fim do Acompanha Custos e tratamento de depósitos 98/99, critérios de `B9_QINI=0`, custos `B9_CM1` vs `B9_VINI1`, seleção de tipos/terceiros e composição do WIP. Confrontar linhas, totais por tipo/grupo e saldo geral; divergência exige explicação demonstrável. **Não desenvolver endpoint/UI nem sacramentar fechamento com fórmulas inferidas.**


## 12. R03 — Rechecagem temporal e drift da posição histórica (21/10/2026)

**Motivo:** PO pediu verificar se o delta entre P7 NotebookLM (3.776.994,69) e SUM(SB9.B9_VINI1) (3.884.439,52), ambos atribuídos a 30/09/2026 filial 01, poderia vir da data/período ou erro de extração derivada.

**NOVO RESULTADO DAVI READ-ONLY:** `SELECT ... FROM SB9010 WHERE B9_DATA='20260930' AND B9_FILIAL='01'` retornou **zero linhas**, inclusive sem filtro `D_E_L_E_T_`. Repetição por `GROUP BY B9_DATA,B9_FILIAL` confirma que setembro/2026 tem **3.117 linhas apenas filial 02** (10.576.487,84), enquanto a Fase A/B1 (20/10/2026) tinha **4.812 linhas filial 01** e 3.884.439,52, com amostras de `S_T_A_M_P_` em 01/10/2026. Este é um **EXECUTION_DRIFT** na fonte observada entre rodadas; **causa UNKNOWN**, não presumir deleção nem alteração ou erro na consulta anterior.

**Histórico agora observado (filial 01, ativos, SUM B9_VINI1):** 31/08/2026 = 4.720 linhas / **3.931.904,10**; 31/07/2026 = 4.631 / **3.784.923,95**; 30/06/2026 = 4.585 / **3.766.250,64**; 31/05/2026 = 4.472 / **3.813.064,69**; 30/04/2026 = 4.400 / **3.608.427,62**; 31/03/2026 = 4.442 / **3.564.942,32**; 28/02/2026 = 4.435 / **3.474.907,58**; 31/01/2026 = 4.372 / **3.468.259,86**. Nenhum desses totais brutos coincide com o P7 derivado de 3.776.994,69; proximidade de junho/julho não comprova erro de competência ou regra MATR460.

**Validação do NotebookLM:** original catalogado no doc 03 com 00:54:44, mas resposta derivada menciona >01:00; período informado como 30/09/2026, valores de P7 e Insumos são `INFORMED_DERIVED`, não uma exportação analisada diretamente. Sem PDF original, captura de parâmetros e explicação da mudança na SB9, **não é possível atribuir delta a erro de data ou NotebookLM**.

**Conclusão:** `R03_SB9_SEP_FILIAL01=EXECUTION_DRIFT`; `P7_DIFF_10744483=STALE_EVIDENCE` como comparação contra estado atual (era diferença aritmética válida nos snapshots anteriores), `MATR460_REPRODUCTION=INCONCLUSIVE`; `EXPORT_PARITY=TEST_NOT_RUN`. **Próximo gate:** owner api-delpi/TI-Protheus verificar histórico de movimentação/manutenção da SB9, origem/ambiente da consulta e preservação de snapshots; obter relatório P7/PDF de 30/09/2026 com parâmetros e data/hora de execução; só então reexecutar conciliação do período. Não escrever/reconstituir a SB9 e não mudar filtros para forçar igualdade.


## 13. Índice cronológico NotebookLM recebido do PO (21/10/2026) — NÃO verificado diretamente

**Proveniência:** texto integral do índice fornecido pelo PO a partir do NotebookLM. `EVIDENCE_CLASS=INFORMED_DERIVED`; `VIDEO_DIRECT_VERIFICATION=TEST_NOT_RUN`; `TIMECODE_PROVENANCE=STALE_EVIDENCE`. O NotebookLM afirma duração **01:02:15** para arquivo `Acompanhamento do Processo do Fechamento Mensal de Estoques e Custos-20260930_143151-Gravação de Reunião (1) (1).mp4`; metadado catalogado no doc 03 do arquivo original aponta **00:54:44.125**. **Não promover a duração ou timecodes para PROVEN** até verificar integridade/hash e eventual versão distinta do vídeo.

### 13.1 Janelas candidatas para navegação (transcrição do NotebookLM)

| Tema | Início candidato | Geração/saída candidata | Situação relatada |
|---|---|---|---|
| Acompanha Custos (código MATA330 não comprovado no vídeo) | 00:00:15 | 00:02:40; conferência 00:18:20 | derivado a verificar; suposto processamento, não export observado |
| Custo Reposição (MATA331 não comprovado) | 00:05:12 | 00:08:31 | derivado |
| Posição de títulos Pagar/Receber | 00:08:31 | Excel 00:09:50 | derivado; confirmar qual relatório |
| Refaz Saldos (MATA280 não comprovado em tela) | 00:09:45 | 00:11:10 | derivado; potencial operação com escrita ERP, não executar sem autorização |
| Faturamento × MOD | 00:14:30 | Excel 00:19:15; conferência 00:37:14–00:40:10 | derivado |
| Baixas DLP / _F190C | 00:18:20 | erro 00:19:30–00:23:10 | derivado; conferir drift com referência anterior de 00:43:51–00:46:14 |
| Kardex 01 / CPV | 00:21:10 | Excel 00:23:30; conferência 00:24:00–00:28:39 | derivado |
| Entradas/Saídas | 00:23:10 | PDF 00:33:45; conferência 00:33:00–00:37:13 | derivado |
| P7 padrão | 00:28:40 | PDF/spool 00:31:00; conferência 00:36:30 e 00:40:11–00:43:50 | derivado; total reportado 3.776.994,69 |
| P7 Bloco H | 00:31:30 | PDF 00:32:50 | derivado |
| H02 / Material em Processo | 00:33:00 | PDF 00:34:50; confronto 00:40:11–00:42:10 | derivado; valor relatado 64.591,71 |
| SD1 / CC | 00:52:31 | XML 00:54:50; Excel 00:55:00–00:58:30 | derivado; fora do MP4 catalogado após 54:44 |
| Extratos Bradesco | 00:55:41 | PDFs 00:56:50 | derivado; fora do MP4 catalogado |

**Mencionados sem execução demonstrada segundo NotebookLM:** Kardex 99 (~00:21:10, ~00:45:30), MATR860 (~00:21:10), extratos BB/Sicoob/BNB/XP (~00:58–00:59), repetição filial 02 (~00:59:50) e virada/sacramentação (00:42:11 e 01:00:11). Horários concatenados recebidos `00:21:1000:45:30` e `00:42:1101:00:11` foram **interpretados somente como candidatos separados, não prova**.

### 13.2 Inconsistências a depurar no vídeo

1. Janelas sobrepostas: Acompanha Custos 00:01–00:18, Custo Reposição 00:05–00:09, Financeiro 00:08–00:10 e Refaz Saldos 00:09–00:14. Podem ser operações assíncronas/intercaladas, mas o índice não prova simultaneidade nem conclusão de processos.
2. `_F190C` agora aparece 00:18–00:23; extração derivada anterior indica 00:43:51–00:46:14. `IDENTITY_TIMECODE_DRIFT=YES`; não eleger um sem inspeção.
3. P7 às 00:28–00:33, Entradas/Saídas 00:23–00:37 e H02 00:33–00:35 têm sobreposições. Confirmar precisamente abertura, spool, PDF e contexto da tela.
4. Rotinas MATA330/MATA331/MATA280 e valores de conclusão (`CONCLUÍDO`, custos recalculados/saldos regravados) são **afirmações derivadas**, não execução ou efeito comprovado; não autorizar writes ERP ou inferir dependência.
5. Duração catalogada 00:54:44 vs 01:02:15 ainda sem reconciliação. Identificar artefato, faixa real, cortes/transcrição ou outra versão antes de utilizar timecodes finais.
6. Alegação de necessidade universal de re-extração após 18h não está homologada: confirmar ponto de corte operacional do mês e owner; `AFTER_18H_RULE=NOT_PROVEN`.

### 13.3 Próximo método de verificação conjunta

Usar índice como **roteiro de busca**, não `OBSERVED_VISUAL` em nosso repositório. PO pode conferir vídeo ou fornecer prints em janelas prioritárias **00:00–00:03 Acompanha Custos**, **00:09–00:14 Refaz Saldos**, **00:18–00:24 financeiro/Kardex**, **00:28–00:35 P7 e H02**, **00:40–00:44 conciliação**, depois resolver divergência de duração e blocos finais. Para cada tela registrar nome visível, duração/arquivo, filial, competência, parâmetros, tipo de ação (consulta/processamento/export), valores, arquivo gerado, e evidência visual ou verbal. Depois reclassificar o trecho individualmente, sem inferir ordem ótima e sem misturar R03 (P7), R04 (MATR860) e R12 (rotinas).


## 14. Transcrição integral NotebookLM anexada pelo PO — auditoria textual inicial (21/10/2026)

**Artefato recebido nesta conversa:** `PROC-0072_Transcricao_Integral_Video.md` (372 linhas, identificação de arquivo `Acompanhamento do Processo do Fechamento Mensal de Estoques e Custos-20260930_143151-Gravação de Reunião (1) (1).mp4`). **Origem derivada NotebookLM, não reprodução direta do MP4 verificada nesta rodada.** Não tratar o rótulo "transcrição integral" ou `[AÇÃO VISUAL]` gerados por IA como evidência visual independente. Conteúdo de falas tem valor investigativo de primeira ordem, mas requer checagem contra vídeo para mudar classificação.

### 14.1 Divergência interna comprovada NO PRÓPRIO ARQUIVO DERIVADO

- Seção "Identificação" afirma duração **01:02:15**; **última fala indexada = 00:54:12**, seguida de marcador visual genérico de fim em 01:02:15. O MP4 original anteriormente catalogado no doc 03 possui **00:54:44.125**; a causa é desconhecida. Não validar 01:02:15 como duração real.
- Títulos das seções e tabela-resumo **não coincidem com timecodes de fala**. Ex.: seção "Acompanha Custos" 00:02:15–00:05:11 contém fala de início 00:01:20; seção P7 intitulada 00:23:11–00:32:59 contém fala da emissão P7 em **00:18:50–00:20:10**; seção "Confronto Triplo" intitulada 00:40:11–00:43:50 contém falas entre **00:31:10–00:38:40**; seção bancária 00:43:51–00:52:30 contém falas **00:39:10–00:43:08**; SD1 seção 00:52:31–01:02:15 contém falas **00:43:20–00:54:12**. A tabela de índice repete horários de seções e pode estar deslocada.
- O incidente `_F190C` aparece na fala em **00:14:20–00:17:40**, enquanto a tabela indica 00:18:20–00:19:30 e outra análise anterior indicava 00:43:51–00:46:14. `TIMECODE_PROVENANCE=STALE_EVIDENCE`; usar **timecodes de fala como candidatos de navegação**, ainda não como verificados.

### 14.2 Falas específicas úteis para investigação (apenas TRANSCRIPT_DERIVED)

| Janela de fala candidata | Conteúdo da fala a conferir no MP4 | Leitura cautelosa |
|---|---|---|
| 00:01:20–00:04:30 | Joici explica iniciar processamentos demorados; Acompanha Custos calcula custo médio, database último dia, apropriação **diária**; Custo de Reposição acionado paralelamente para outros tipos | Evidência verbal derivada de **paralelismo por eficiência**, não de sequência obrigatória universal; execução/write somente com autorização ERP |
| 00:05:12–00:08:10 | Refaz Saldos para materiais em geral; Refaz Poder de Terceiros somente esporádico, com restrição de faturamento; Acompanha Custos ainda em 25% às 00:08:10 | Rotinas distintas; **Refaz Poder de Terceiros não confirmado executado** |
| 00:08:40–00:09:15 | Joici afirma não conseguir gerar Kardex 01/99 nem relatório de saldo de estoque antes da finalização do Acompanha Custos | **Dependência relatada pela operadora** nesta execução, `INFORMED_DERIVED`, ainda não regra técnica de programa comprovada |
| 00:11:50–00:14:00 | Posição de títulos a pagar/receber; ampla janela até 2049; export Excel/binário | **Diferente de baixas FINR190/_F190C**; não mesclar R01/R02 |
| 00:14:20–00:17:40 | Falha de compilação `_F190C`; cinco saídas informadas: Pagar/Receber Excel, Receber PDF por data, Pagar PDF por data/natureza | Executabilidade não provada; `ERROR_DERIVED` |
| 00:17:50–00:20:10 | Acompanha Custos termina; relatório de custos inicial/final; Joici informa **não executar etapa final ainda** por haver conferências; inicia P7 padrão e layout H, data último dia, **sem poder de terceiros** | **Distinguir cálculo concluído de sacramentação do fechamento**, parâmetro exato deve ser visto no vídeo |
| 00:20:35–00:23:45 | Kardex armazéns 01 e 99; período 01/09–30/09; arquivo Excel; `INVENT`/similar filtrado, SD3 mencionada | Kardex 99 **aparece sendo preparado** no texto; contradiz índice anterior que o tratava como apenas citado |
| 00:31:10–00:38:40 | P7 padrão total **3.776.994,69**, 91 páginas; Entradas/Saídas **3.890.247,18**, H02 ~**64.591,71**, diferença matemática **48.660,78**; grupos Insumos 266.321,45/46; MP 3.087.025,94 + 348.059,30 = 3.435.085,24; fechamento não sacramentado com fábrica ativa | **Valores derivados de falas**, sem PDF original nem paridade; diferença de Insumos observada no texto é 0,01; grupo MP requer entendimento de denominadores |
| 00:42:35–00:43:08 | Estoque repetido por filial 01/02; financeiro descrito como consolidado | Não converter em permission por filial; confirmar escopo de cada relatório |
| 00:45:00–00:51:50 | SD1 itens NF, export XML, tratamento por centro de custo e tipo de entrada no Excel | Há uma **etapa de transformação de planilha**, não apenas geração de relatório; regras precisam ser auditadas com owner |

### 14.3 Implicações para diagnóstico R03

A fala sobre rodar Acompanha Custos enquanto faz outras tarefas responde a hipótese de eficiência do PO: **motivo operacional explicitamente narrado**, mas apenas via transcrição derivada. A conclusão do custeio precede emissão P7 no relato, e Joici verbaliza dependência de relatório de saldo/Kardex; isso não autoriza transformar a dependência em gate técnico sem código/owner. A fala P7 **30/09/2026** e total de **3.776.994,69** está presente, mas **não comprova snapshot DB idêntico**; segue aberto o `EXECUTION_DRIFT` de desaparecimento da filial 01 na SB9 reportado no §12.

**Gates:** `TRANSCRIPT_RECEIVED=PROVEN` (existência do arquivo anexado); `TRANSCRIPT_CONTENT=INFORMED_DERIVED`; `SPEECH_TIMECODES=TO_VERIFY`; `SECTION_TIMECODES=STALE_EVIDENCE`; `VIDEO_DURATION=CONFLICT`; `AUDIOVISUAL_DIRECT_VERIFICATION=TEST_NOT_RUN`; `MATR460_PARITY=TEST_NOT_RUN`. Próximo passo: conferir audiovisual primeiro 00:01–00:09 (custeio/paralelismo) e 00:17–00:23 (P7/Kardex), 00:31–00:38 (resumo/confronto), identificando inclusive se os timecodes do reprodutor correspondem aos das falas, e obter prints com parâmetros.


## 15. R03 — Primeiro PDF exportado efetivamente fornecido pelo PO: Resumo Estoque (21/10/2026)

**Novo nível de evidência:** documento binário original recebido como anexo nesta conversa, `Resumo Estoque.pdf`, 1 página física A4, 30.825 bytes, `pdfinfo` indica título `TOTVS Manufatura (TOTVS) 02.9.0002`, criador Mozilla/Chrome, PDF criado **2026-10-01 19:37:32 UTC** (metadado de geração, não hora comprovada de extração ou corte), sem assinatura de autenticidade verificada. **`REPORT_EXPORT_EVIDENCE=PROVIDED` para esta folha de resumo apenas; não para 74/91 páginas do P7 nem para o Bloco H integral.**

Cabeçalho do documento: `REGISTRO DE INVENTÁRIO`, `DELPI COMPONENTES LTDA`, `MATRIZ`, `FOLHA 000.074`, `ESTOQUES EXISTENTES EM 30/09/2026`. Nenhum identificador físico do programa MATR460, código de filial SQL, pergunta de layout ou custo aparece na página fornecida. Não deduzir layout do arquivo exclusivamente pelo nome.

**Valores lidos literalmente no PDF (formatação decimal original):**
- `EM ESTOQUE`: Matéria-prima **2.483.986,52**; Produto acabado **190.511,24**; Produto intermediário **24.528,60**; subtotal impresso **2.699.026,36** (soma das três linhas = subtotal).
- `EM PROCESSO`: Matéria-prima **277.686,77**; Produto intermediário **254,44**; subtotal impresso **277.941,20**; **soma das linhas impressas = 277.941,21**, diferença de **0,01** em relação ao subtotal (possível arredondamento, mecanismo ainda não provado).
- **TOTAL GERAL impresso = 2.976.967,56**, coerente com soma dos subtotais impressos `2.699.026,36 + 277.941,20`.

**Confronto com vídeo/NotebookLM derivado:** P7 padrão relatado **3.776.994,69** vs total desse PDF **2.976.967,56**, delta **800.027,13**. **Não classificar como falha de Protheus ou erro de NotebookLM sem verificar se se trata da mesma emissão, layout, filtros e universo**. O PDF aqui é evidência direta dos números impressos e data de referência, mas a *paridade de reprodução* segue `TEST_NOT_RUN`. O valor `PA=190.511,24` coincide com agregação SB9 × SB1 tipo PA observada na Fase A; `PI=24.528,60` difere em 0,01 de SB9 tipo PI **24.528,59**. Ambos são sinais investigativos, não paridade homologada; SB9 filial 01 em setembro desapareceu na rechecagem 21/10 (§12).

**Classificações:** `PDF_RECEIVED=PROVEN`; `PDF_VISIBLE_TOTALS=PROVEN`; `PDF_REPORT_VARIANT=TO_VERIFY`; `PDF_SOURCE_BRANCH=INFORMED_BY_HEADER_MATRIZ` (sem código SQL); `PDF_CALCULATION_RULES=TO_INVENTORY`; `P7_COMPARABILITY_WITH_NOTEBOOKLM=INCONCLUSIVE`; `P7_LINE_BY_LINE_PARITY=TEST_NOT_RUN`. **Próximo artefato a solicitar, isoladamente:** `Estoque.pdf` (aparenta conter detalhamento de inventário) para examinar páginas, cabeçalhos, parâmetros, variantes e ligação com resumo; não inferir mesmo arquivo a partir do nome. Alternativamente pedir PDF `Entradas e saídas` após fechar identidade/layout do P7.


## 16. R03 — Segundo PDF físico fornecido pelo PO: Estoque.pdf (21/10/2026)

**Artefato PDF efetivo:** `Estoque.pdf` (1 página PDF, 31.008 bytes), com metadados `Title: TOTVS Manufatura (TOTVS) 02.9.0004`, `CreationDate: 2026-10-01 19:22:54 UTC`; dados do arquivo apenas, não comprovam data/hora de congelamento dos saldos. Texto e PDF inspecionados via `pdftotext -layout` e `pdfinfo`. Classificação: `SOURCE_PDF_VALUES=PROVEN` e `REPORT_IDENTITY=MATR460_CANDIDATE`, pois o código não está visível no cabeçalho.

**Cabeçalho:** `REGISTRO DE INVENTÁRIO` / `DELPI COMPONENTES LTDA` / `MATRIZ` / `FOLHA 000.101` / `ESTOQUES EXISTENTES EM: 30/09/2026`.

**EM ESTOQUE** — Material de embalagem **10.354,36**; Gastos gerais **1,35**; Insumos industriais **266.321,46**; Material de consumo **12.121,47**; Material de limpeza/higiene **5.675,39**; Matéria-prima **3.071.684,80**; Material de segurança **7.802,62**; Material de expediente **2.190,07**; Produto acabado **190.511,24**; Produto intermediário **24.528,60**. **Subtotal impresso 3.591.191,36**, igual à soma das linhas impressas.

**EM PROCESSO** — Material de embalagem **39,12**; Material de limpeza/higiene **8,46**; Matéria-prima **354.938,50**; Produto intermediário **254,44**. **Subtotal impresso 355.240,51**; soma de linhas impressas **355.240,52**, delta **0,01** (não ajustar; investigar arredondamento/precisão).

**TOTAL GERAL impresso: 3.946.431,87**, igual a 3.591.191,36 + 355.240,51.

**Comparação com o primeiro PDF `Resumo Estoque.pdf` (§15):** ambos são `REGISTRO DE INVENTÁRIO`, Matriz, data estoque 30/09/2026, mas o primeiro era folha **000.074**, criado **19:37:32 UTC**, tinha somente categorias MP/PA/PI e total **2.976.967,56**; este é folha **000.101**, criado **19:22:54 UTC** (cerca de 14min38s ANTES), com mais tipos, total **3.946.431,87**, delta **969.464,31**. **Hipótese de duas emissões / escopos ou filtros distintos, NÃO comprovação**, apesar de datas e companhia iguais. A diferença entre quantidade de folhas **não implica** 74 ou 101 páginas físicas recebidas (ambos os arquivos anexos têm apenas uma página).

**Comparação com transcrição/NotebookLM:** P7 dito **3.776.994,69** vs este PDF **3.946.431,87**, delta **169.437,18**; não igualar outputs. **Coincidências verificáveis:** Insumos do PDF **266.321,46**, exatamente o segundo valor do par falado `266.321,45 / 266.321,46`; Produto acabado **190.511,24** e produto intermediário **24.528,60** repetem primeiro PDF. **Divergência de base temporal:** snapshot anterior da SB9 em filial 01 tinha `SUM(B9_VINI1)=3.884.439,52`, diferença **61.992,35** em relação a este PDF; atualmente as linhas SB9 daquela filial/data não aparecem (§12), logo comparação SQL deixou de ser reproduzível.

**Questões controladas para próxima etapa:** (i) qual arquivo representa `P7 padrão` versus `Bloco H` ou seleção de tipos? (ii) diferenças de seleção de produtos/situações/depósitos e parâmetros entre emissões; (iii) o `P7` de 3.776.994,69 aparece em um terceiro arquivo/corte? (iv) regra de arredondamento dos subtotais de processo; (v) identidade de filial SQL a partir do cabeçalho Matriz. Não presumir resposta pelos nomes `Estoque`/`Resumo Estoque`. **Próxima evidência a solicitar individualmente:** `Entradas e saídas.pdf` para ancorar a conciliação externa e verificar parâmetros/impressão; se PDF mostrar outra competência/unidade, reclassificar, não forçar comparação.

**Gates:** `R03_SECOND_PDF_RECEIVED=PROVEN`; `TWO_DISTINCT_PRINTED_SUMMARIES=PROVEN`; `DIFFERENT_EMISSION_PARAMETERS=TO_VERIFY`; `MATCH_NOTEBOOKLM_TOTAL=FAIL` para ambos os PDFs (apenas igualdade aritmética, não falha do Protheus); `FULL_PARITY=TEST_NOT_RUN`. Sem alteração de runtime.
