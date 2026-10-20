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
