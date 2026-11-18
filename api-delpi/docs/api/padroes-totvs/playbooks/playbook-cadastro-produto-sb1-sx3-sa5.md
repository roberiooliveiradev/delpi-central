# Playbook — Inventário integral SB1/SX3/SA5 + contratos CREATE/UPDATE (PRC)

**TASK_ID:** `EVA-PRC-TOTVS-SB1-SX3-SA5-COMPLETE-FIELD-CONTRACT-INVENTORY-01` (G0-A do capítulo `PRC-TOTVS-AUTOMATION-AND-NORMATIVE-SIMILARITY`, [plano mestre](../../../../../docs/12-roadmap-e-evolucao/engineering/PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md)).

**Seção curta relacionada:** [cadastro-produto.md](../cadastro-produto.md).

> **Documento de inventário — não autoriza escrita.** Nenhum campo marcado como exposto/suportado abaixo deve ser enviado ao ERP sem contrato ratificado, feature gate, pin de ambiente e evidência. Política vigente: `TOTVS_WRITE_TEST_FORBIDDEN` para testes comuns; ensaios TST01 exigem aprovação delimitada. **Nunca** `INSERT`/`UPDATE`/`DELETE` SQL em tabelas `S*` — escrita só via REST + `MSExecAuto` na rotina oficial.

## 1. Método e evidência

| Camada | Fonte | Estado |
|---|---|---|
| Schema físico | `INFORMATION_SCHEMA.COLUMNS` do banco TOTVS `DELPI` (192.168.1.230:1433), leitura via `delpi-api-delpi` (pyodbc, credencial de serviço do ambiente), 18/11/2026 | `PROVEN_RUNTIME` |
| Dicionário SX3 | `SX3010 WHERE X3_ARQUIVO IN ('SB1','SA5') AND D_E_L_E_T_=' '` na mesma base | `PROVEN_RUNTIME` |
| Handler ADVPL | `docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW` (WSRESTFUL `DelpiProduto`) | `PROVEN_SOURCE` — **não** comprova a versão compilada/publicada; conferir em `/restall` antes de evoluir contrato |
| Façade api-delpi | `protheus_router.py`, `protheus_product_payload.py`, `protheus_field_normalizer.py`, `product_repository.py`, `product_suppliers_repository.py` | `PROVEN_CODE` |
| Catálogo PRC | `engineering-api/engineering_app/domain/product_registration/catalog.py` (`PAYLOAD_SCHEMA_VERSION=1`) | `PROVEN_CODE` |
| Catálogo REST publicado | playbook de write-integration: ~527 classes nativas + `delpiproduto` em `/restall` (evidência autenticada 17/11) | `PROVEN_DOCUMENTED`; validade da lista deve ser reconfirmada por sessão |

Semânticas não comprovadas são `TO_INVENTORY` — nunca inferidas.

## 2. Resumo executivo

| Métrica | Valor |
|---|---|
| Colunas físicas `SB1010` | **318** (313 de negócio + 5 de controle `D_E_L_E_T_`, `R_E_C_N_O_`, `R_E_C_D_E_L_`, `S_T_A_M_P_`, `I_N_S_D_T_`) |
| Campos `SB1` no SX3 (`D_E_L_E_T_=' '`) | **319** (6 campos de dicionário sem coluna física — `B1_VM_*`, `B1_OBS`, `B1_GRPTIDC` — legado/versão) |
| Colunas físicas `SA5010` | **123** (118 de negócio + 5 controle) |
| Campos `SA5` no SX3 | **125** (2 SX3 sem físico: `A5_NOMERED`, +1 controle visual; convergência 122) |
| Campos `B1_*` no handler ADVPL `delpiproduto` (CREATE op3 **e** UPDATE op4 — arrays idênticos) | **22** (incl. `B1_COD`) |
| Campos aceitos pela façade `PUT /integrations/protheus/products/{code}` | **21** + `B1_COD` do path — **representação completa obrigatória** |
| Campos na façade CREATE de produto (api-delpi) | **0 — `POST` inexistente**; upstream `delpiproduto/v1/IncProduto/incluir` existe mas sem façade e sem contrato de obrigatórios verificado |
| Campos READ `products.detail` projeção completa (repositório) | ~76 `B1_*` selecionados |
| Campos READ `view=engineering` | **43** normalizados |
| Campos READ `products.suppliers` `view=engineering` | **15** (7 colunas SA5 + joins SB1/SA2 + agregados de lead time) |
| Paths do catálogo PRC v1 | **10** (9 SB1 + coleção `suppliers`) |
| Escrita SA5 (ADD/UPDATE/REMOVE) em qualquer camada | **NOT_IMPLEMENTED** — nenhuma rota ADVPL/façade localizada |
| DELETE de produto (`IncProduto/excluir`) | Playbook menciona; `.PRW` versionado **só** contém POST+PUT → `TO_INVENTORY` divergência a resolver na próxima fase |

## 3. SB1 — físico × dicionário

- Tipos SX3: **C** 215 · **N** 88 · **D** 10 · **M** 6.
- `X3_PROPRI='U'` (customizações Delpi): **29** campos — `B1_CODDES, B1_CONV3, B1_EMBDELP, B1_ITEMWEG, B1_LINHA, B1_LMP, B1_MPLOCAL, B1_NF3UM, B1_REFCANT, B1_REFEREN, B1_SUBGRUP, B1_TPMAT, B1_UM3, B1_XBLQCOM, B1_XLEWEG, B1_YCAT, B1_YDESP, B1_YHOHS, B1_YMI, B1_YNFE, B1_YPC, B1_YPDESD, B1_YPDESF, B1_YPV, B1_YSC, B1_YVLPC, B1_ZDESREV, B1_ZDLPSEG, B1_ZINVDLP`.
- `X3_OBRIGAT`: valor `'x'` em ~273 campos e vazio em 46. **Semântica desta flag nesta base é `TO_INVENTORY`** — não coincide com a obrigatoriedade real de MATA010 (ex.: `B1_GRUPO` vazio no dict mas exigido na prática; `B1_DESC='x'`). A obrigatoriedade efetiva por operação deve ser confirmada via `VALID`/`WHEN`/`CHKSQL`, validação ExecAuto em TST01 e TDN — não pelo flag isolado.
- `X3_BROWSE`: `S`/`N` — apenas navegação no browse, não regra de negócio.
- Colunas físicas sem SX3: **0** de negócio (somente as 5 de controle técnico).

## 4. Contrato do handler `delpiproduto` (DLP04I01.PRW)

Ambos os métodos montam o **mesmo array de 22 triplas** `{campo, oDados["CAMPO"], Nil}` e chamam `MSExecAuto(Mata010, aSB1, op)` — POST `op=3` (inclusão), PUT `op=4` (alteração):

`B1_GRUPO, B1_COD, B1_DESC, B1_REFEREN, B1_REFCANT, B1_CODDES, B1_TIPO, B1_YHOHS, B1_POSIPI, B1_LOCPAD, B1_UM, B1_SEGUM, B1_TE, B1_TS, B1_PICMRET, B1_CONV, B1_TIPCONV, B1_TPMAT, B1_ESPECIE, B1_EX_NCM, B1_EX_NBM, B1_ORIGEM`.

Implicações comprovadas pelo ledger homologado:

- O handler lê **todos** os campos incondicionalmente (`VAL()` em `B1_PICMRET`/`B1_CONV`) → **PUT parcial quebra com 400 e, se passasse, zeraria campos** no ExecAuto. A façade api-delpi por isso exige representação completa dos 21 campos + `B1_COD`.
- O mesmo conjunto se aplica a CREATE (op3): o upstream aceita os 22 nomes; **quais são exigidos pela rotina MATA010 na inclusão depende de tipo/grupo/filial e não está provado** — `TO_INVENTORY` via ensaio TST01 governado.
- Campos fora do array (ex.: `B1_CONTA`, `B1_PESO`, `B1_QE`, fiscais `B1_PICM`/`B1_IPI`/`B1_PIS`…) **não são alcançáveis** por este handler: alterá-los exigiria ampliar o array do `.PRW` (mudança contratual upstream, nova compilação/publicação) ou outra rotina oficial.
- Sem `codusr` no contrato upstream — carimbo = conta de serviço; ator real no ledger local api-delpi.

## 5. Superfície api-delpi (contrato vigente)

| Operação | Endpoint | Campos | Estado |
|---|---|---|---|
| READ detalhe | `GET /products/{code}` + `view=full|engineering` | 76 `B1_*` selecionados; eng restringe a 43 (remove comerciais/custo/fiscal) | `PROVEN_CODE` |
| READ vínculos | `GET /products/{code}/suppliers` + `view=engineering` | `A5_PRODUTO/FORNECE/LOJA/CODPRF/CODPRCA/CODBAR/LEAD_T` + `B1_DESC/B1_UM` join + `A2_NOME` + agregados lead-time real | `PROVEN_CODE` |
| UPDATE produto | `PUT /integrations/protheus/products/{code}` | 21 `B1_*` completos (§4 menos `B1_COD`) — gate `PROTHEUS_PRODUCT_UPDATE_ENABLED` + pin `PROTHEUS_REST_EXPECTED_BASE_URL` | `PROVEN_CODE` (ensaio TST01 17/11, não integrado ao PRC) |
| CREATE produto | — | inexistente (upstream `incluir` sem façade) | `GAP` |
| SA5 ADD/UPDATE/REMOVE | — | inexistente nas duas camadas | `GAP / NOT_IMPLEMENTED` |
| Read-back pós-write | `ACKNOWLEDGED` + `persistence_proven=false` | sem reconciliação autoritativa | `GAP` já registrado no plano |

## 6. Catálogo PRC v1 (`catalog.py`)

`officialProductCode→B1_COD · description→B1_DESC · group→B1_GRUPO · productKind→B1_TIPO · defaultWarehouse→B1_LOCPAD · unit→B1_UM · thirdPartyProduct→B1_TPMAT · accountingAccount→B1_CONTA · customerReference→B1_REFEREN · suppliers→SA5{supplierCode→A5_FORNECE, store→A5_LOJA, partNumber→A5_CODPRF, catalogNumber→A5_CODPRCA}` (+ `supplierName` display via SA2). Todos `verifiable=True` — cobertura READ existe; `accountingAccount` é READ-only sem suporte de escrita no handler atual (ver §9).

## 7. Matriz SB1 integral (SX3 × físico × ADVPL × API × PRC)

Legenda: **Obrig SX3** = valor bruto `X3_OBRIGAT` da base (`x` marcado, `-` vazio — semântica TO_INVENTORY, §3). **ADVPL C/U** = presente no array de 22 (CREATE op3 e UPDATE op4). **API READ** = nome normalizado; `(eng)` = view=engineering, `(full)` = somente view=full. **API WRITE** = campo do PUT (21) ou `path` (B1_COD). **PRC** = path do catálogo v1. **Nota** = `custom Delpi` (X3_PROPRI=U), `SX3 sem físico`, `físico sem SX3`, `memo`, `chave`.

| # | Campo | Título SX3 | Tipo×Tam | Obrig SX3 | ADVPL C/U | API READ | API WRITE | PRC | Nota |
|---|---|---|---|---|---|---|---|---|---|
| 1 | B1_FILIAL | Filial | C×2.0 | x | — | — | — | — |  |
| 2 | B1_GRUPO | Grupo | C×4.0 | - | C+U | group_code (eng) | PUT | group |  |
| 3 | B1_COD | Codigo | C×15.0 | x | C+U | code (eng) | path | officialProductCode | chave |
| 4 | B1_DESC | Descricao | C×120.0 | x | C+U | description (eng) | PUT | description |  |
| 5 | B1_CODITE | Cod Item | C×27.0 | x | — | — | — | — |  |
| 6 | B1_REFEREN | Ref. Cliente | C×15.0 | - | C+U | customer_reference (eng) | PUT | customerReference | custom Delpi |
| 7 | B1_CODDES | Cod. Desenho | C×15.0 | - | C+U | drawing_code (eng) | PUT | — | custom Delpi |
| 8 | B1_REFCANT | Ref. Cl. Ant | C×15.0 | - | C+U | customer_reference_old (eng) | PUT | — | custom Delpi |
| 9 | B1_TIPO | Tipo | C×2.0 | x | C+U | type (eng) | PUT | productKind |  |
| 10 | B1_YHOHS | RoHS ? | C×1.0 | - | C+U | rohs_indicator (eng) | PUT | — | custom Delpi |
| 11 | B1_POSIPI | Pos.IPI/NCM | C×10.0 | x | C+U | ncm_ipi_position (full) | PUT | — |  |
| 12 | B1_ESPECIE | Especie TIPI | C×2.0 | x | C+U | — | PUT | — |  |
| 13 | B1_EX_NCM | Ex-NCM | C×3.0 | x | C+U | — | PUT | — |  |
| 14 | B1_EX_NBM | Ex-NBM | C×3.0 | x | C+U | — | PUT | — |  |
| 15 | B1_LOCPAD | Armazem Pad. | C×2.0 | x | C+U | default_warehouse (eng) | PUT | defaultWarehouse |  |
| 16 | B1_UM | Unidade | C×2.0 | x | C+U | unit (eng) | PUT | unit |  |
| 17 | B1_LINHA | Linha | C×3.0 | - | — | production_line (eng) | — | — | custom Delpi |
| 18 | B1_SUBGRUP | Cod.SubGrupo | C×20.0 | - | — | subgroup (eng) | — | — | custom Delpi |
| 19 | B1_MPLOCAL | Mapa Localiz | C×5.0 | - | — | — | — | — | custom Delpi |
| 20 | B1_TPMAT | Produto 3º | C×1.0 | - | C+U | material_type (eng) | PUT | thirdPartyProduct | custom Delpi |
| 21 | B1_PICM | Aliq. ICMS | N×5.0.2 | x | — | icms_rate (full) | — | — |  |
| 22 | B1_BITMAP | Foto | C×8.0 | x | — | — | — | — |  |
| 23 | B1_SEGUM | Seg.Un.Medi. | C×2.0 | x | C+U | secondary_unit (eng) | PUT | — |  |
| 24 | B1_IPI | Aliq. IPI | N×5.0.2 | x | — | ipi_rate (full) | — | — |  |
| 25 | B1_ALIQISS | Aliq. ISS | N×5.0.2 | x | — | — | — | — |  |
| 26 | B1_CODISS | Cod.Serv.ISS | C×9.0 | x | — | — | — | — |  |
| 27 | B1_TE | TE Padrao | C×3.0 | x | C+U | entry_tes (full) | PUT | — |  |
| 28 | B1_TS | TS Padrao | C×3.0 | x | C+U | exit_tes (full) | PUT | — |  |
| 29 | B1_PICMRET | Solid. Saida | N×6.0.2 | x | C+U | — | PUT | — |  |
| 30 | B1_PICMENT | Solid. Entr. | N×6.0.2 | x | — | — | — | — |  |
| 31 | B1_IMPZFRC | Imp.Z.Franca | C×1.0 | x | — | — | — | — |  |
| 32 | B1_CONV | Fator Conv. | N×8.0.3 | - | C+U | conversion_factor (eng) | PUT | — |  |
| 33 | B1_TIPCONV | Tipo de Conv | C×1.0 | x | C+U | conversion_type (eng) | PUT | — |  |
| 34 | B1_UCOM | Ult. Compra | D×8.0 | - | — | last_purchase_date (eng) | — | — |  |
| 35 | B1_ALTER | Alternativo | C×15.0 | x | — | — | — | — |  |
| 36 | B1_QE | Qtd.Embalag. | N×9.0.4 | - | — | package_quantity (eng) | — | — |  |
| 37 | B1_ESTFOR | Form.Est.Seg | C×3.0 | x | — | — | — | — |  |
| 38 | B1_PRV1 | Preco Venda | N×17.0.7 | - | — | sale_price (full) | — | — |  |
| 39 | B1_EMIN | Ponto Pedido | N×13.0.3 | - | — | — | — | — |  |
| 40 | B1_CUSTD | Custo Stand. | N×14.0.5 | - | — | standard_cost (full) | — | — |  |
| 41 | B1_UCALSTD | Ult. Calculo | D×8.0 | x | — | standard_cost_date (full) | — | — |  |
| 42 | B1_UPRC | Ult. Preco | N×13.0.3 | - | — | last_purchase_price (full) | — | — |  |
| 43 | B1_MCUSTD | Moeda C.Std | C×1.0 | x | — | cost_currency (full) | — | — |  |
| 44 | B1_PESO | Peso Liquido | N×11.0.4 | x | — | net_weight (eng) | — | — |  |
| 45 | B1_ESTSEG | Seguranca | N×13.0.3 | - | — | — | — | — |  |
| 46 | B1_FORPRZ | Form. Prazo | C×3.0 | x | — | — | — | — |  |
| 47 | B1_PE | Entrega | N×5.0 | x | — | — | — | — |  |
| 48 | B1_TIPE | Tipo Prazo | C×1.0 | x | — | lead_time_type (eng) | — | — |  |
| 49 | B1_LE | Lote Econom. | N×13.0.3 | - | — | — | — | — |  |
| 50 | B1_LOJPROC | Loja Padrao | C×2.0 | x | — | — | — | — |  |
| 51 | B1_LM | Lote Minimo | N×13.0.3 | - | — | — | — | — |  |
| 52 | B1_CONTA | Cta Contabil | C×20.0 | x | — | accounting_account (eng) | — | accountingAccount |  |
| 53 | B1_TOLER | Tolerancia | N×3.0 | x | — | — | — | — |  |
| 54 | B1_CC | C Custo | C×9.0 | - | — | cost_center (full) | — | — |  |
| 55 | B1_ITEMCC | Item Conta | C×9.0 | x | — | — | — | — |  |
| 56 | B1_FAMILIA | Familia | C×1.0 | x | — | — | — | — |  |
| 57 | B1_UREV | Ult. Revisao | D×8.0 | x | — | last_revision_date (eng) | — | — |  |
| 58 | B1_DATREF | DT Referenc. | D×8.0 | x | — | cost_reference_date (full) | — | — |  |
| 59 | B1_PROC | Forn. Padrao | C×6.0 | x | — | — | — | — |  |
| 60 | B1_QB | Base Estrut. | N×7.0 | x | — | — | — | — |  |
| 61 | B1_APROPRI | Apropriacao | C×1.0 | x | — | appropriation_type (full) | — | — |  |
| 62 | B1_TIPODEC | Tipo Dec. OP | C×1.0 | x | — | operation_decimal_type (eng) | — | — |  |
| 63 | B1_DTREFP1 | Dt.Ref.Prc 1 | D×8.0 | x | — | — | — | — |  |
| 64 | B1_ORIGEM | Origem | C×1.0 | x | C+U | origin (full) | PUT | — |  |
| 65 | B1_CLASFIS | Class.Fiscal | C×2.0 | x | — | — | — | — |  |
| 66 | B1_FANTASM | Fantasma | C×1.0 | x | — | — | — | — |  |
| 67 | B1_RASTRO | Rastro | C×1.0 | - | — | traceability (eng) | — | — |  |
| 68 | B1_FORAEST | Fora estado | C×1.0 | x | — | — | — | — |  |
| 69 | B1_CONINI | Cons.Inicial | D×8.0 | x | — | initial_consumption_date (eng) | — | — |  |
| 70 | B1_CONTSOC | Cont.Seg.Soc | C×1.0 | x | — | — | — | — |  |
| 71 | B1_COMIS | % Comissao | N×5.0.2 | x | — | — | — | — |  |
| 72 | B1_CODBAR | Cod Barras | C×15.0 | - | — | barcode (eng) | — | — |  |
| 73 | B1_GRADE | Grade | C×1.0 | x | — | — | — | — |  |
| 74 | B1_FORMLOT | Cod Form Lot | C×3.0 | x | — | — | — | — |  |
| 75 | B1_MONO | Forn. Canal | C×1.0 | x | — | — | — | — |  |
| 76 | B1_FPCOD | Cod.Familia | C×10.0 | x | — | — | — | — |  |
| 77 | B1_PERINV | Per.Invent. | N×3.0 | x | — | — | — | — |  |
| 78 | B1_CONTRAT | Contrato | C×1.0 | x | — | contractual_product (eng) | — | — |  |
| 79 | B1_DESC_P | Desc. Portug | C×6.0 | x | — | — | — | — |  |
| 80 | B1_DESC_GI | Desc. L.I. | C×6.0 | x | — | — | — | — |  |
| 81 | B1_DESC_I | Desc. Ingles | C×6.0 | x | — | — | — | — |  |
| 82 | B1_GRTRIB | Grupo Trib. | C×6.0 | - | — | tax_group (full) | — | — |  |
| 83 | B1_MRP | Entra MRP | C×1.0 | x | — | mrp_considered (eng) | — | — |  |
| 84 | B1_VM_I | Desc. Ingles | M×36.0 | x | — | — | — | — | SX3 sem físico; memo |
| 85 | B1_VM_GI | Desc. LI | M×48.0 | x | — | — | — | — | SX3 sem físico; memo |
| 86 | B1_VM_P | Desc. Portug | M×36.0 | x | — | — | — | — | SX3 sem físico; memo |
| 87 | B1_OPC | Opc. Default | C×80.0 | x | — | — | — | — |  |
| 88 | B1_ANUENTE | Anuente | C×1.0 | x | — | customs_authority (full) | — | — |  |
| 89 | B1_CODOBS | Cod. Obs. | C×6.0 | x | — | — | — | — |  |
| 90 | B1_NOTAMIN | Nota Minima | N×1.0 | x | — | — | — | — |  |
| 91 | B1_PRVALID | Prazo Valid. | N×3.0 | x | — | — | — | — |  |
| 92 | B1_FABRIC | Fabricante | C×20.0 | x | — | — | — | — |  |
| 93 | B1_NUMCOP | Qtde. Copias | N×5.0 | x | — | — | — | — |  |
| 94 | B1_IRRF | Impos.Renda | C×1.0 | x | — | — | — | — |  |
| 95 | B1_LOCALIZ | Contr.Endere | C×1.0 | - | — | — | — | — |  |
| 96 | B1_OPERPAD | Rt.Op Padrao | C×2.0 | x | — | — | — | — |  |
| 97 | B1_PRODPAI | Produto Pai | C×15.0 | x | — | — | — | — |  |
| 98 | B1_VLREFUS | Val.Ref.US$ | N×15.0.5 | x | — | — | — | — |  |
| 99 | B1_IMPORT | Prod. Import | C×1.0 | x | — | imported_product (full) | — | — |  |
| 100 | B1_OBS | Observacao | M×60.0 | x | — | — | — | — | SX3 sem físico; memo |
| 101 | B1_SITPROD | Situacao | C×2.0 | x | — | — | — | — |  |
| 102 | B1_MODELO | Modelo | C×15.0 | x | — | — | — | — |  |
| 103 | B1_SETOR | Setor | C×2.0 | x | — | — | — | — |  |
| 104 | B1_BALANCA | Balanca | C×1.0 | x | — | — | — | — |  |
| 105 | B1_TECLA | Tecla | C×3.0 | x | — | — | — | — |  |
| 106 | B1_TIPOCQ | Tipo de C.Q. | C×1.0 | x | — | — | — | — |  |
| 107 | B1_SOLICIT | Restricao | C×1.0 | x | — | requester_restriction (eng) | — | — |  |
| 108 | B1_GRUPCOM | Gr. Compras | C×6.0 | x | — | — | — | — |  |
| 109 | B1_NALNCCA | NALADI NCCA | C×7.0 | x | — | — | — | — |  |
| 110 | B1_NUMCQPR | Produþ÷es CQ | N×3.0 | x | — | — | — | — |  |
| 111 | B1_NALSH | NALADI SH | C×8.0 | x | — | — | — | — |  |
| 112 | B1_CONTCQP | Cont.Prod.CQ | N×3.0 | x | — | — | — | — |  |
| 113 | B1_REVATU | Rev.Estrutur | C×3.0 | x | — | current_revision (eng) | — | — |  |
| 114 | B1_INSS | Calcula INSS | C×1.0 | x | — | inss_incidence (full) | — | — |  |
| 115 | B1_CODEMB | Embalagem | C×20.0 | x | — | — | — | — |  |
| 116 | B1_ESPECIF | Descr.Espec. | C×80.0 | x | — | — | — | — |  |
| 117 | B1_DATASUB | Data Substit | D×8.0 | x | — | — | — | — |  |
| 118 | B1_MAT_PRI | Materia Pri. | C×20.0 | x | — | — | — | — |  |
| 119 | B1_REDINSS | % Red. INSS | N×5.0.2 | x | — | — | — | — |  |
| 120 | B1_ALADI | ALADI | C×3.0 | x | — | — | — | — |  |
| 121 | B1_REDIRRF | % Red. IRRF | N×5.0.2 | x | — | — | — | — |  |
| 122 | B1_TAB_IPI | IPI de Pauta | C×2.0 | x | — | — | — | — |  |
| 123 | B1_GRUDES | Grupo Descon | C×3.0 | x | — | — | — | — |  |
| 124 | B1_REDPIS | %Red.PIS | N×5.0.2 | x | — | — | — | — |  |
| 125 | B1_REDCOF | %Red.COFINS | N×5.0.2 | x | — | — | — | — |  |
| 126 | B1_PCSLL | Perc. CSLL | N×5.0.2 | x | — | — | — | — |  |
| 127 | B1_PCOFINS | Perc. COFINS | N×5.0.2 | x | — | cofins_percent (full) | — | — |  |
| 128 | B1_PPIS | Perc. PIS | N×5.0.2 | x | — | pis_percent (full) | — | — |  |
| 129 | B1_QTDSER | Vld Num Seri | C×1.0 | x | — | — | — | — |  |
| 130 | B1_MTBF | MTBF em Hr. | N×9.0.2 | x | — | — | — | — |  |
| 131 | B1_MTTR | MTTR em Hr. | N×9.0.2 | x | — | — | — | — |  |
| 132 | B1_FLAGSUG | Tip Sugestao | C×1.0 | x | — | suggestion_flag (eng) | — | — |  |
| 133 | B1_CLASSVE | Status Venda | C×1.0 | x | — | sales_class (eng) | — | — |  |
| 134 | B1_MIDIA | Calc.Midia | C×1.0 | x | — | media_product (full) | — | — |  |
| 135 | B1_VLR_IPI | IPI de Pauta | N×9.0.2 | x | — | — | — | — |  |
| 136 | B1_QTMIDIA | Qtde. Midia | N×14.0.2 | x | — | media_quantity (full) | — | — |  |
| 137 | B1_ENVOBR | Env. Obrigat | C×1.0 | x | — | — | — | — |  |
| 138 | B1_SERIE | Serie/Colec. | C×20.0 | x | — | — | — | — |  |
| 139 | B1_FAIXAS | Nr.faixas CD | N×2.0 | x | — | — | — | — |  |
| 140 | B1_NROPAG | Nro. Paginas | N×4.0 | x | — | — | — | — |  |
| 141 | B1_ISBN | Codigo ISBN | C×10.0 | x | — | — | — | — |  |
| 142 | B1_TITORIG | Tit.Original | C×50.0 | x | — | — | — | — |  |
| 143 | B1_LINGUA | Lingua Orig. | C×20.0 | x | — | — | — | — |  |
| 144 | B1_EDICAO | Nro.Edicao | C×3.0 | x | — | — | — | — |  |
| 145 | B1_CORPRI | Cor Princip. | C×6.0 | x | — | — | — | — |  |
| 146 | B1_CORSEC | Cor Secund. | C×6.0 | x | — | — | — | — |  |
| 147 | B1_NICONE | Icone APS | C×15.0 | x | — | — | — | — |  |
| 148 | B1_ATRIB1 | Atributo 1 | C×6.0 | x | — | — | — | — |  |
| 149 | B1_ATRIB2 | Atributo 2 | C×6.0 | x | — | — | — | — |  |
| 150 | B1_ATRIB3 | Atributo 3 | C×6.0 | x | — | — | — | — |  |
| 151 | B1_REGSEQ | Regra Sequ. | C×6.0 | x | — | — | — | — |  |
| 152 | B1_OBSISBN | Obs ISBN | C×40.0 | x | — | — | — | — |  |
| 153 | B1_CLVL | Classe Valor | C×9.0 | x | — | — | — | — |  |
| 154 | B1_ATIVO | Ativo | C×1.0 | x | — | active (eng) | — | — |  |
| 155 | B1_PESBRU | Peso Bruto | N×11.0.4 | x | — | — | — | — |  |
| 156 | B1_REQUIS | Requisitado | C×1.0 | x | — | — | — | — |  |
| 157 | B1_SELO | Utiliza Selo | C×1.0 | x | — | — | — | — |  |
| 158 | B1_TIPCAR | Tipo Carga | C×6.0 | x | — | — | — | — |  |
| 159 | B1_VLR_ICM | Icms Pauta | N×14.0.2 | x | — | — | — | — |  |
| 160 | B1_VLRSELO | Valor Selo | N×15.0.2 | x | — | — | — | — |  |
| 161 | B1_CODNOR | Cod. Norma | C×3.0 | x | — | — | — | — |  |
| 162 | B1_LOTVEN | Qtde Venda | N×12.0.2 | x | — | — | — | — |  |
| 163 | B1_OK | OK | C×4.0 | x | — | — | — | — |  |
| 164 | B1_CPOTENC | Contr. Poten | C×1.0 | x | — | power_control (eng) | — | — |  |
| 165 | B1_MSBLQL | Blq. de Tela | C×1.0 | x | — | blocked (eng) | — | — |  |
| 166 | B1_POTENCI | Potencia Pad | N×6.0.2 | x | — | — | — | — |  |
| 167 | B1_QTDACUM | Qtde. Acum. | N×9.0 | x | — | — | — | — |  |
| 168 | B1_QTDINIC | Qtd Inic Mes | N×9.0 | x | — | — | — | — |  |
| 169 | B1_EMAX | Estoq Maximo | N×12.0.2 | x | — | — | — | — |  |
| 170 | B1_UMOEC | Ult Moe Comp | N×2.0 | x | — | — | — | — |  |
| 171 | B1_UVLRC | Ult Vlr Comp | N×12.0.2 | x | — | — | — | — |  |
| 172 | B1_PIS | Retem PIS | C×1.0 | x | — | pis_incidence (full) | — | — |  |
| 173 | B1_COFINS | Retem COF | C×1.0 | x | — | cofins_incidence (full) | — | — |  |
| 174 | B1_FRETISS | F.Ret.ISS | C×1.0 | x | — | — | — | — |  |
| 175 | B1_TPREG | Tp. Reg | C×1.0 | x | — | — | — | — |  |
| 176 | B1_CSLL | Retem CSLL | C×1.0 | x | — | csll_incidence (full) | — | — |  |
| 177 | B1_CNAE | C. Atividade | C×9.0 | x | — | — | — | — |  |
| 178 | B1_VLR_PIS | Pis Pauta | N×12.0.2 | x | — | — | — | — |  |
| 179 | B1_VLR_COF | COFINS Pauta | N×12.0.2 | x | — | — | — | — |  |
| 180 | B1_CALCFET | Calc. FETHAB | C×1.0 | x | — | — | — | — |  |
| 181 | B1_PAUTFET | Pauta FETHAB | N×9.0.4 | x | — | — | — | — |  |
| 182 | B1_LMP | LMP | N×5.0 | - | — | — | — | — | custom Delpi |
| 183 | B1_DESPIMP | Desp.Import. | C×1.0 | x | — | import_expense (full) | — | — |  |
| 184 | B1_PARCEI | Parceiro | C×6.0 | x | — | — | — | — |  |
| 185 | B1_QUADPRO | Classe Repos | C×1.0 | x | — | — | — | — |  |
| 186 | B1_USAFEFO | FEFO | C×1.0 | x | — | — | — | — |  |
| 187 | B1_AGREGCU | Custeio OP | C×1.0 | x | — | — | — | — |  |
| 188 | B1_FRACPER | Frac Permit | N×5.0.2 | x | — | — | — | — |  |
| 189 | B1_CLASSE | Classe Selo | C×6.0 | x | — | — | — | — |  |
| 190 | B1_INT_ICM | P.ICMS Prop. | N×12.0.2 | x | — | — | — | — |  |
| 191 | B1_GCCUSTO | Gr Cnt Custo | C×8.0 | x | — | — | — | — |  |
| 192 | B1_CCCUSTO | CC p/ Custo | C×9.0 | x | — | — | — | — |  |
| 193 | B1_PMACNUT | % Macronutr. | N×6.0.2 | x | — | — | — | — |  |
| 194 | B1_PMICNUT | % Micronutr. | N×6.0.2 | x | — | — | — | — |  |
| 195 | B1_CODPROC | Cód.desc.pro | C×6.0 | x  xxx | — | — | — | — |  |
| 196 | B1_CODQAD | Dep Correcao | C×33.0 | x | — | — | — | — |  |
| 197 | B1_VM_PROC | Desc.Process | M×48.0 | x  xxx | — | — | — | — | SX3 sem físico; memo |
| 198 | B1_QBP | Base Pre-Es. | N×7.0 | x | — | — | — | — |  |
| 199 | B1_VLCIF | Valor CIF | N×12.0.3 | x  xxx | — | — | — | — |  |
| 200 | B1_RETOPER | Ret.Operação | C×1.0 | x | — | retention_by_operation (full) | — | — |  |
| 201 | B1_CRDEST | Crd Estímulo | N×5.0.2 | x | — | — | — | — |  |
| 202 | B1_PRFDSUL | Pr.Fundersul | N×12.0.8 | - | — | — | — | — |  |
| 203 | B1_CODANT | Cód. ant. | C×15.0 | x | — | previous_code (eng) | — | — |  |
| 204 | B1_FETHAB | Inc.FETHAB | C×1.0 | x | — | — | — | — |  |
| 205 | B1_FECP | Aliq FECP | N×5.0.2 | x | — | — | — | — |  |
| 206 | B1_IVAAJU | Cal. IVA Aju | C×1.0 | x | — | — | — | — |  |
| 207 | B1_ESCRIPI | Est Cred IPI | C×1.0 | x | — | — | — | — |  |
| 208 | B1_FUSTF | Fust/Funttel | C×1.0 | x | — | — | — | — |  |
| 209 | B1_CRICMS | ICMS 271 | C×1.0 | x | — | — | — | — |  |
| 210 | B1_SELOEN | Enq. Selo | C×6.0 | x | — | — | — | — |  |
| 211 | B1_ALFECOP | Aliq. FECOP | N×5.0.2 | x | — | — | — | — |  |
| 212 | B1_REGRISS | Regra ISS Pg | C×2.0 | x | — | — | — | — |  |
| 213 | B1_ALFECST | Al. FECOP ST | N×5.0.2 | x | — | — | — | — |  |
| 214 | B1_PRODREC | Material Rec | C×1.0 | x | — | — | — | — |  |
| 215 | B1_FECOP | Calc. FECOP | C×1.0 | x | — | — | — | — |  |
| 216 | B1_VIGENC | Data Vigenc | D×8.0 | x | — | — | — | — |  |
| 217 | B1_EMBDELP | Embal Client | N×13.0.3 | - | — | customer_packaging (eng) | — | — | custom Delpi |
| 218 | B1_CRDPRES | %Cred. Pres | N×5.0.2 | x | — | — | — | — |  |
| 219 | B1_AFETHAB | Aliq. FETHAB | N×5.0.2 | x | — | — | — | — |  |
| 220 | B1_AFACS | Aliq. FACS | N×5.0.2 | x | — | — | — | — |  |
| 221 | B1_AFABOV | Aliq. FABOV | N×5.0.2 | x | — | — | — | — |  |
| 222 | B1_REFBAS | Ref. Base | C×1.0 | x | — | — | — | — |  |
| 223 | B1_TFETHAB | Tipo FETHAB | C×1.0 | x | — | — | — | — |  |
| 224 | B1_VEREAN | Código EAN | C×2.0 | x | — | — | — | — |  |
| 225 | B1_RPRODEP | Rel. Prodepe | C×1.0 | x | — | — | — | — |  |
| 226 | B1_RICM65 | Art65 RICMPR | C×1.0 | x | — | — | — | — |  |
| 227 | B1_PRDORI | Cod. Orig. | C×15.0 | x | — | — | — | — |  |
| 228 | B1_CFEM | Cal. CFEM | C×1.0 | x | — | — | — | — |  |
| 229 | B1_CFEMS | Sit. CFEM | C×1.0 | x | — | — | — | — |  |
| 230 | B1_CFEMA | Aliq. CFEMA | N×6.0.2 | x | — | — | — | — |  |
| 231 | B1_DTCORTE | Mud.Reg.Trib | D×8.0 | x | — | — | — | — |  |
| 232 | B1_TRIBMUN | C. Trib. Mun | C×20.0 | x | — | — | — | — |  |
| 233 | B1_TNATREC | Tab. Na. Rec | C×4.0 | x | — | — | — | — |  |
| 234 | B1_TPPROD | Tipo Medic. | C×2.0 | x | — | — | — | — |  |
| 235 | B1_CODLAN | Cod.Cat83 | C×6.0 | x | — | — | — | — |  |
| 236 | B1_PR43080 | %Red.43080 | N×6.0.2 | x | — | — | — | — |  |
| 237 | B1_CNATREC | Cod Nat Rec | C×3.0 | x | — | — | — | — |  |
| 238 | B1_DCI | Prod. DCI | C×1.0 | x | — | — | — | — |  |
| 239 | B1_DCRE | Nr. DCRE | C×10.0 | x | — | — | — | — |  |
| 240 | B1_ALFUMAC | Alq. FUMACOP | N×5.0.2 | x | — | — | — | — |  |
| 241 | B1_DCR | Nr. DCR | C×9.0 | x | — | — | — | — |  |
| 242 | B1_PRN944I | Prod. RN944i | C×1.0 | x | — | — | — | — |  |
| 243 | B1_DCRII | Vl. DCRII | N×16.0.7 | x | — | — | — | — |  |
| 244 | B1_COEFDCR | Coef. DCR | N×5.0.2 | x | — | — | — | — |  |
| 245 | B1_CHASSI | Num Chassi | C×25.0 | x | — | — | — | — |  |
| 246 | B1_DIFCNAE | Dif. CNAE | C×11.0 | x | — | — | — | — |  |
| 247 | B1_REGESIM | Rg. Simp. MT | C×1.0 | x | — | — | — | — |  |
| 248 | B1_RSATIVO | Rastro Ativo | C×1.0 | x | — | — | — | — |  |
| 249 | B1_FECPBA | Aliq FECP BA | N×5.0.2 | x | — | — | — | — |  |
| 250 | B1_PRINCMG | Pr.Inc.Leite | N×6.0.2 | x | — | — | — | — |  |
| 251 | B1_CRICMST | Cont ICMS-ST | C×1.0 | x | — | — | — | — |  |
| 252 | B1_ALFECRN | Ali.FECOP-RN | N×5.0.2 | x | — | — | — | — |  |
| 253 | B1_AJUDIF | Ajust/Difer | C×1.0 | x | — | — | — | — |  |
| 254 | B1_GRPNATR | Grp.Nat.Rec. | C×2.0 | x | — | — | — | — |  |
| 255 | B1_SITTRIB | Sit Trib | C×1.0 | x | — | — | — | — |  |
| 256 | B1_DTFIMNT | Dt.Fim N. R. | D×8.0 | x | — | — | — | — |  |
| 257 | B1_DESBSE3 | Des SubFam | C×60.0 | x | — | — | — | — |  |
| 258 | B1_BASE3 | SFamilia | C×14.0 | x | — | — | — | — |  |
| 259 | B1_IAT | Trunc ou Arr | C×1.0 | x | — | — | — | — |  |
| 260 | B1_IPPT | Prop ou Terc | C×1.0 | x | — | — | — | — |  |
| 261 | B1_TALLA | Tamanho | C×6.0 | x | — | — | — | — |  |
| 262 | B1_GDODIF | Grau Dificul | C×1.0 | x | — | — | — | — |  |
| 263 | B1_MARKUP | % Markup | N×5.0.2 | x | — | — | — | — |  |
| 264 | B1_PRODSBP | Atende Nec? | C×1.0 | x | — | make_or_buy (eng) | — | — |  |
| 265 | B1_CARGAE | Carga Esp? | C×1.0 | x | — | — | — | — |  |
| 266 | B1_VALEPRE | Vale Present | C×1.0 | x | — | — | — | — |  |
| 267 | B1_LOTESBP | Lote SBP | N×12.0.2 | x | — | — | — | — |  |
| 268 | B1_TIPOBN | Tipo BN | C×2.0 | x | — | — | — | — |  |
| 269 | B1_DESBSE2 | Des SubFam | C×60.0 | x | — | — | — | — |  |
| 270 | B1_ADMIN | Admin. | C×10.0 | x | — | — | — | — |  |
| 271 | B1_BASE2 | SubSubFamil | C×14.0 | x | — | — | — | — |  |
| 272 | B1_GARANT | Garantia? | C×1.0 | x | — | warranty_product (eng) | — | — |  |
| 273 | B1_TIPVEC | Tipo Vetor | C×6.0 | x | — | — | — | — |  |
| 274 | B1_BASE | Cod Familia | C×14.0 | x | — | — | — | — |  |
| 275 | B1_TPDP | Calc. TPDP | C×1.0 | x | — | — | — | — |  |
| 276 | B1_PERGART | % Garantia | N×5.0.2 | x | — | — | — | — |  |
| 277 | B1_MEPLES | Exe. Serviço | C×1.0 | x | — | — | — | — |  |
| 278 | B1_IDHIST | ID.Hist. | C×20.0 | x | — | — | — | — |  |
| 279 | B1_MSEXP | Ident.Export | C×8.0 | x | — | — | — | — |  |
| 280 | B1_PAFMD5 | MD5 | C×32.0 | x | — | — | — | — |  |
| 281 | B1_PORCPRL | Porc. PRL | C×2.0 | x | — | — | — | — |  |
| 282 | B1_ESTRORI | Estr. Origem | C×15.0 | x | — | — | — | — |  |
| 283 | B1_AFAMAD | Aliq. FAMAD | N×5.0.2 | x | — | — | — | — |  |
| 284 | B1_GRPTI | Grupo - TI | C×4.0 | x | — | intelligent_tes_group (full) | — | — |  |
| 285 | B1_GRPCST | Enq. IPI | C×3.0 | x | — | — | — | — |  |
| 286 | B1_CEST | CEST | C×7.0 | x | — | — | — | — |  |
| 287 | B1_AFASEMT | Alíq.FASE-MT | N×5.0.2 | x | — | — | — | — |  |
| 288 | B1_AIMAMT | Alíq. IMA-MT | N×5.0.2 | x | — | — | — | — |  |
| 289 | B1_AFUNDES | Alq.FUNDESA | N×5.0.2 | x | — | — | — | — |  |
| 290 | B1_MOPC | M. Opcional | M×80.0 | x | — | — | — | — | memo |
| 291 | B1_COLOR | Cor | C×10.0 | x | — | — | — | — |  |
| 292 | B1_INTEG | Integracao | C×1.0 | x | — | — | — | — |  |
| 293 | B1_HREXPO | Hr. Ult. Exp | C×8.0 | x | — | — | — | — |  |
| 294 | B1_USERLGI | Log de Inclu | C×17.0 | x | — | created_by (eng) | — | — |  |
| 295 | B1_IMPNCM | Aliq. de Imp | N×14.0.2 | x | — | — | — | — |  |
| 296 | B1_TERUM | Terc Un Med | C×2.0 | x | — | — | — | — |  |
| 297 | B1_GRPTIDC | Desc. Gr. TI | C×50.0 | x | — | — | — | — | SX3 sem físico |
| 298 | B1_USERLGA | Log de Alter | C×17.0 | x | — | updated_by (eng) | — | — |  |
| 299 | B1_CODGTIN | Cod. GTIN | C×15.0 | x | — | — | — | — |  |
| 300 | B1_YDESP | Despesa | C×1.0 | - | — | — | — | — | custom Delpi |
| 301 | B1_YSC | Obg CC SC? | C×1.0 | - | — | mandatory_cc_sc (full) | — | — | custom Delpi |
| 302 | B1_YPC | Obg CC PC | C×1.0 | - | — | mandatory_cc_pc (full) | — | — | custom Delpi |
| 303 | B1_YPV | Obg CC PV | C×1.0 | - | — | mandatory_cc_pv (full) | — | — | custom Delpi |
| 304 | B1_YMI | Obg CC MI | C×1.0 | - | — | mandatory_cc_mi (full) | — | — | custom Delpi |
| 305 | B1_YNFE | Obg CC NFE | C×1.0 | - | — | mandatory_cc_nfe (full) | — | — | custom Delpi |
| 306 | B1_YPDESD | % Desp Delpi | N×6.0.2 | - | — | — | — | — | custom Delpi |
| 307 | B1_YPDESF | % Desp Func | N×6.0.2 | - | — | — | — | — | custom Delpi |
| 308 | B1_YVLPC | Vld Alcada | C×1.0 | - | — | approval_validation (full) | — | — | custom Delpi |
| 309 | B1_XLEWEG | Le Docto Cli | C×1.0 | - | — | — | — | — | custom Delpi |
| 310 | B1_CONV3 | Conv 3 UM | N×8.0.3 | - | — | — | — | — | custom Delpi |
| 311 | B1_UM3 | 3 UM | C×2.0 | - | — | — | — | — | custom Delpi |
| 312 | B1_NF3UM | NF 3 UM | C×1.0 | - | — | — | — | — | custom Delpi |
| 313 | B1_APOPRO | Ap. p/ Prod. | C×1.0 | x | — | — | — | — |  |
| 314 | B1_ITEMWEG | Item WEG | C×13.0 | - | — | — | — | — | custom Delpi |
| 315 | B1_YCAT | Categ Delpi | C×2.0 | - | — | delpi_category (eng) | — | — | custom Delpi |
| 316 | B1_ZDLPSEG | Segmento Dlp | C×3.0 | - | — | delpi_segment (eng) | — | — | custom Delpi |
| 317 | B1_ZINVDLP | Freq Invent | C×1.0 | - | — | — | — | — | custom Delpi |
| 318 | B1_ZDESREV | Rev Desenho | C×9.0 | - | — | — | — | — | custom Delpi |
| 319 | B1_XBLQCOM | Bloq. Compra | C×1.0 | - | — | — | — | — | custom Delpi |

## 8. Matriz SA5 integral (SX3 × físico × API READ × PRC)

Entidade separada da SB1 — vínculo produto×fornecedor. `A5_FORNECE`/`A5_LOJA` referenciam SA2 (`A2_COD+A2_LOJA`); `A5_PRODUTO` referencia `B1_COD`. Lead time cadastrado = `A5_LEAD_T` (diferente de `B1_PE` geral e `SBZ.BZ_PE` por filial — ver [lead-time-prazo-entrega.md](../lead-time-prazo-entrega.md)). **Nenhuma capacidade de escrita SA5 existe hoje** — qualquer ADD/UPDATE/REMOVE exige nova rotina oficial (`.PRW` + `MSExecAuto` ou API nativa confirmada em `/restall`) + façade + gate/pin.

Campos-chave confirmados no contrato de leitura vigente: `A5_PRODUTO` (id produto), `A5_FORNECE`+`A5_LOJA` (id fornecedor+loja), `A5_CODPRF` (Part Number — obrigatório no PRC), `A5_CODPRCA` (código de catálogo — opcional), `A5_CODBAR`, `A5_LEAD_T`. A identidade completa da chave primária física é `(A5_FILIAL?, A5_PRODUTO, A5_FORNECE, A5_LOJA)` a confirmar via SIX — `TO_INVENTORY`.

| # | Campo | Título SX3 | Tipo×Tam | Obrig SX3 | API READ (eng) | PRC | Nota |
|---|---|---|---|---|---|---|
| 1 | A5_FILIAL | Filial | C×2.0 | x | — | — |  |
| 2 | A5_FORNECE | Fornecedor | C×6.0 | x | supplier_code | suppliers[].supplierCode |  |
| 3 | A5_LOJA | Loja | C×2.0 | x | supplier_store | suppliers[].store |  |
| 4 | A5_NOMEFOR | Nome | C×50.0 | x | — | — |  |
| 5 | A5_NOMERED | Nome Reduz. | C×20.0 | x | — | — | SX3 sem físico |
| 6 | A5_PRODUTO | Produto | C×15.0 | x | product_code | — |  |
| 7 | A5_NOMPROD | Descricao | C×120.0 | - | — | — |  |
| 8 | A5_CODPRF | Cod.Prod.For | C×50.0 | x | supplier_part_number | suppliers[].partNumber |  |
| 9 | A5_CODPRCA | Cod.Prod.Cat | C×18.0 | - | catalog_code | suppliers[].catalogNumber |  |
| 10 | A5_SITU | Situacao | C×1.0 | - | — | — |  |
| 11 | A5_FABREV | Fab/Rev/Perm | C×1.0 | - | — | — |  |
| 12 | A5_PE | Entrega | N×5.0 | x | — | — |  |
| 13 | A5_TIPE | Tipo Prazo | C×1.0 | - | — | — |  |
| 14 | A5_EMBAL | Qtde Embalag | N×5.0 | - | — | — |  |
| 15 | A5_FABRRED | Nome Fabric. | C×20.0 | x | — | — | SX3 sem físico |
| 16 | A5_MOE_US | Moeda Utiliz | C×3.0 | x | — | — |  |
| 17 | A5_VLCOTUS | Vlr.Cotaþao | N×15.0.5 | x | — | — |  |
| 18 | A5_ULT_ENT | Ult. Entrega | D×8.0 | x | — | — |  |
| 19 | A5_QT_COT | Quant.Cotada | N×13.0.3 | x | — | — |  |
| 20 | A5_ULT_FOB | Vlr.Ult.FOB | N×15.0.5 | x | — | — |  |
| 21 | A5_PARTOPC | Part-Num.Opc | C×48.0 | x | — | — |  |
| 22 | A5_UNID | Unidade | C×2.0 | x | — | — |  |
| 23 | A5_SKPLOT | Skip-Lote | C×2.0 | x | — | — |  |
| 24 | A5_RIAI | RIAI | C×8.0 | x | — | — |  |
| 25 | A5_DTRIAI | Data RIAI | D×8.0 | x | — | — |  |
| 26 | A5_VALRIAI | Valid. RIAI | D×8.0 | x | — | — |  |
| 27 | A5_CHAVE | Cod. Ligacao | C×8.0 | x | — | — |  |
| 28 | A5_ATUAL | Atualiza | C×1.0 | x | — | — |  |
| 29 | A5_INCOTER | Incoterm | C×8.0 | x | — | — |  |
| 30 | A5_TR_COST | Transf. Cost | N×15.0.5 | x | — | — |  |
| 31 | A5_CODGRP | Grupo | C×4.0 | x | — | — | SX3 sem físico |
| 32 | A5_CODITE | Cod. Produto | C×27.0 | x | — | — | SX3 sem físico |
| 33 | A5_CODBAR | Cod.Barras | C×15.0 | - | barcode | — |  |
| 34 | A5_TIPOCOT | Tipo Cotacao | C×1.0 | - | — | — |  |
| 35 | A5_STATUS | Status | C×1.0 | x | — | — |  |
| 36 | A5_SKIPLOT | Contr. Lote | N×4.0 | - | — | — |  |
| 37 | A5_DTCOM02 | 2a. Data | D×8.0 | x | — | — |  |
| 38 | A5_DTCOM03 | 3a. Data | D×8.0 | x | — | — |  |
| 39 | A5_DTCOM04 | 4a. Data | D×8.0 | x | — | — |  |
| 40 | A5_DTCOM05 | 5a. Data | D×8.0 | x | — | — |  |
| 41 | A5_DTCOM06 | 6a. Data | D×8.0 | x | — | — |  |
| 42 | A5_DTCOM07 | 7a. Data | D×8.0 | x | — | — |  |
| 43 | A5_DTCOM08 | 8a. Data | D×8.0 | x | — | — |  |
| 44 | A5_DTCOM09 | 9a. Data | D×8.0 | x | — | — |  |
| 45 | A5_DTCOM10 | 10a. Data | D×8.0 | x | — | — |  |
| 46 | A5_DTCOM11 | 11a. Data | D×8.0 | x | — | — |  |
| 47 | A5_DTCOM12 | 12a. Data | D×8.0 | x | — | — |  |
| 48 | A5_ENTREGA | Entregas | N×4.0 | - | — | — |  |
| 49 | A5_FABR | Fabricante | C×6.0 | - | — | — |  |
| 50 | A5_FALOJA | Loja Fabric. | C×2.0 | - | — | — |  |
| 51 | A5_QUANT01 | 1a. Quant. | N×12.0.2 | x | — | — |  |
| 52 | A5_QUANT02 | 2a. Quant. | N×12.0.2 | x | — | — |  |
| 53 | A5_QUANT03 | 3a. Quant. | N×12.0.2 | x | — | — |  |
| 54 | A5_QUANT04 | 4a. Quant. | N×12.0.2 | x | — | — |  |
| 55 | A5_QUANT05 | 5a. Quant. | N×12.0.2 | x | — | — |  |
| 56 | A5_QUANT06 | 6a. Quant. | N×12.0.2 | x | — | — |  |
| 57 | A5_QUANT07 | 7a. Quant. | N×12.0.2 | x | — | — |  |
| 58 | A5_QUANT08 | 8a. Quant. | N×12.0.2 | x | — | — |  |
| 59 | A5_QUANT09 | 9a. Quant. | N×12.0.2 | x | — | — |  |
| 60 | A5_QUANT10 | 10a. Quant. | N×12.0.2 | x | — | — |  |
| 61 | A5_QUANT11 | 11a. Quant. | N×12.0.2 | x | — | — |  |
| 62 | A5_QUANT12 | 12a. Quant. | N×12.0.2 | x | — | — |  |
| 63 | A5_PRECO01 | 1o. Preco | N×16.0.2 | x | — | — |  |
| 64 | A5_PRECO02 | 2o. Preco | N×16.0.2 | x | — | — |  |
| 65 | A5_PRECO03 | 3o. Preco | N×16.0.2 | x | — | — |  |
| 66 | A5_LEAD_T | Lead Time | N×5.0 | x | registered_lead_time_days | — |  |
| 67 | A5_PRECO04 | 4o. Preco | N×16.0.2 | x | — | — |  |
| 68 | A5_PRECO05 | 5o. Preco | N×16.0.2 | x | — | — |  |
| 69 | A5_TIPATU | Tipo Atualiz | C×1.0 | - | — | — |  |
| 70 | A5_LOTEMIN | MOQ | N×8.0.2 | - | — | — |  |
| 71 | A5_LOTEMUL | Embalagem | N×8.0.2 | - | — | — |  |
| 72 | A5_PRECO06 | 6o. Preco | N×16.0.2 | x | — | — |  |
| 73 | A5_PRECO07 | 7o. Preco | N×16.0.2 | x | — | — |  |
| 74 | A5_MSBLQL | Bloqueado? | C×1.0 | - | — | — |  |
| 75 | A5_PRECO08 | 8o. Preco | N×16.0.2 | x | — | — |  |
| 76 | A5_PRECO09 | 9o. Preco | N×16.0.2 | x | — | — |  |
| 77 | A5_PRECO10 | 10o. Preco | N×16.0.2 | x | — | — |  |
| 78 | A5_PRECO11 | 11o. Preco | N×16.0.2 | x | — | — |  |
| 79 | A5_PRECO12 | 12o. Preco | N×16.0.2 | x | — | — |  |
| 80 | A5_PLAM1 | Pl. Amost. a | C×2.0 | x | — | — |  |
| 81 | A5_NIVEL1 | Nivel a | C×2.0 | x | — | — |  |
| 82 | A5_NQA1 | NQA a | C×5.0 | x | — | — |  |
| 83 | A5_PLAM2 | Pl. Amost. b | C×2.0 | x | — | — |  |
| 84 | A5_NIVEL2 | Nivel b | C×2.0 | x | — | — |  |
| 85 | A5_NQA2 | NQA b | C×5.0 | x | — | — |  |
| 86 | A5_COND01 | 1a. Cond. | C×3.0 | x | — | — |  |
| 87 | A5_COND02 | 2a. Cond. | C×3.0 | x | — | — |  |
| 88 | A5_COND03 | 3a. Cond. | C×3.0 | x | — | — |  |
| 89 | A5_COND04 | 4a. Cond. | C×3.0 | x | — | — |  |
| 90 | A5_COND05 | 5a. Cond. | C×3.0 | x | — | — |  |
| 91 | A5_TEMPLIM | Tempo Limite | N×2.0 | - | — | — |  |
| 92 | A5_NOTA | Nota | N×1.0 | x | — | — |  |
| 93 | A5_COND06 | 6a. Cond. | C×3.0 | x | — | — |  |
| 94 | A5_COND07 | 7a. Cond. | C×3.0 | x | — | — |  |
| 95 | A5_COND08 | 8a. Cond. | C×3.0 | x | — | — |  |
| 96 | A5_COND09 | 9a. Cond. | C×3.0 | x | — | — |  |
| 97 | A5_COND10 | 10a. Cond. | C×3.0 | x | — | — |  |
| 98 | A5_COND11 | 11a. Cond. | C×3.0 | x | — | — |  |
| 99 | A5_COND12 | 12a. Cond. | C×3.0 | x | — | — |  |
| 100 | A5_REFGRD | Ref Grd Cfg | C×14.0 | x | — | — |  |
| 101 | A5_DESREF | Desc. Ref Gr | C×30.0 | x | — | — |  |
| 102 | A5_DTCOM01 | 1a. Data | D×8.0 | x | — | — |  |
| 103 | A5_TEMPTRA | Tempo Transi | N×3.0 | - | — | — |  |
| 104 | A5_PESO | Peso Liquido | N×11.0.4 | x | — | — |  |
| 105 | A5_ENTSIT | Num.Ent.Sit. | N×2.0 | - | — | — |  |
| 106 | A5_CCUSTO | C.Custo | C×9.0 | x | — | — |  |
| 107 | A5_DIASSIT | Entradas Sit | N×4.0 | - | — | — |  |
| 108 | A5_TESBP | TE p/ Bonif. | C×3.0 | x | — | — |  |
| 109 | A5_CODFIS | Cod.Fis.Forn | C×15.0 | x | — | — |  |
| 110 | A5_CONV | Conv Forn NF | N×16.0.4 | - | — | — |  |
| 111 | A5_TPCONV | Tipo Convers | C×1.0 | - | — | — |  |
| 112 | A5_CODTAB | Tab.Preco | C×3.0 | x | — | — |  |
| 113 | A5_DSCTAB | Desc.Tab.Prc | C×30.0 | x | — | — | SX3 sem físico |
| 114 | A5_LEADT | Lead Time | N×3.0 | - | — | — |  |
| 115 | A5_QTDMN | Qtd Minima | N×10.0.2 | - | — | — |  |
| 116 | A5_UMNFE | UM p/ NFe | C×1.0 | x | — | — |  |
| 117 | A5_NCMPRF | NCM Prod.Frn | C×10.0 | x | — | — |  |
| 118 | A5_DESCPRF | Desc.Prod.Fr | C×120.0 | x | — | — |  |
| 119 | A5_TESCP | TE p/ Compl. | C×3.0 | x | — | — |  |
| 120 | A5_ECFLAG | E-Commerce | C×1.0 | - | — | — |  |
| 121 | A5_ECDTEX | Dt Exp | C×8.0 | x | — | — |  |
| 122 | A5_ECSEQ | Numero Seq | C×15.0 | x | — | — |  |
| 123 | A5_CNO | Cod CNO | C×6.0 | x | — | — |  |
| 124 | A5_TOLEDIF | Dif. Qtd Nfe | N×5.0.2 | x | — | — |  |
| 125 | A5_VOLMAX | Vol. Maximo | N×9.0 | x | — | — |  |

## 9. Gaps principais (inventário × PRC × API)

1. **Cobertura PRC ~9/313 campos SB1** — 304 campos físicos não rastreados; a maioria é ERP-owned ou irrelevante, mas classes inteiras relevantes à Engenharia existem na leitura `view=engineering` sem path PRC: `drawing_code (B1_CODDES)`, `subgroup (B1_SUBGRUP)`, `secondary_unit/conversion_*`, `production_line (B1_LINHA)`, `operation_decimal_type`, `current_revision/last_revision_date (B1_REVATU/B1_UREV)`, `net_weight (B1_PESO)`, `package_quantity (B1_QE)`, `barcode`, `customer_packaging (B1_EMBDELP)`, `make_or_buy (B1_PRODSBP)`, `previous_code`, `active/blocked`, `lead_time_type`, `requester_restriction`, `rohs_indicator (B1_YHOHS)`, `traceability (B1_RASTRO)`, `warranty_product`, `mrp_considered`, `power_control`, `delpi_category/segment`, `initial_consumption_date`, `created_by/updated_by`, `contractual_product`, `sales_class`.
2. **WRITE ⊂ READ ⊂ SB1** — dos 21 campos graváveis pelo PUT vigente, PRC rastreia só 8 (`B1_GRUPO, DESC, REFEREN, TIPO, LOCPAD, UM, TPMAT` + `B1_COD` path); os outros 13 (`B1_REFCANT, CODDES, YHOHS, POSIPI, SEGUM, TE, TS, PICMRET, CONV, TIPCONV, ESPECIE, EX_NCM, EX_NBM, ORIGEM` — na verdade 14 com `B1_ORIGEM`) são graváveis mas invisíveis ao diff PRC ⇒ risco de a ficha solicitar alteração sem verificação dedicada ou de a representação completa do PUT reescrever valores sem baseline rastreado.
3. **`accountingAccount` (B1_CONTA) rastreado + verificável, porém não gravável** pelo handler atual (ausente do array de 22) — UPDATE PRC que altere `B1_CONTA` não teria caminho de materialização oficial hoje ⇒ contrato a ratificar (ampliar handler ou rotina distinta).
4. **CREATE sem façade** — upstream `incluir` existe; conjunto de obrigatórios por tipo/família não comprovado (`TO_INVENTORY` via TST01); geração/atribuição de `B1_COD` não documentada no `.PRW` (regra de código sequencial/range a confirmar com o owner).
5. **SA5 write zero** — vínculo PN/catálogo rastreado no PRC não tem caminho de materialização; `MSExecAuto` da rotina oficial de amarração (MATA080-family / rotina SA5 correspondente) e formato de triplas `A5_*` são `TO_INVENTORY`.
6. **Read-back formal ausente** — `ACKNOWLEDGED`≠`CONFIRMED`; reconciliação autoritativa exige leitura oficial pós-write já contratada.
7. **Campos comerciais/fiscais/custo** (sale_price, standard_cost, last_purchase_price, ICMS/IPI/PIS/COFINS/CSLL/INSS, TES, NCM) — presentes na leitura full, fora da view=engineering por decisão PO; **não devem virar editáveis no PRC** sem decisão explícita de owner fiscal/comercial. Marcá-los `READ_RESTRICTED/NO_PRC` na expansão.
8. **SX3 sem físico** (`B1_VM_*`, `B1_OBS`, `B1_GRPTIDC`; `A5_NOMERED`) — legado de versão; não expor.
9. **6 colunas `M` (memo)** na SB1 — não adequadas a diff escalar; se relevantes, tratar como anexo/documento governado.
10. **Divergência playbook×PRW** sobre `IncProduto/excluir` — confirmar catálogo publicado antes de projetar DELETE (fora do escopo proposto mesmo se existir).

## 10. Proposta de evolução do schema PRC (proposta — não implementada)

Elevar `PAYLOAD_SCHEMA_VERSION` para **2** com anel de campos por camada, preservando leitura de casos v1:

| Camada | Conteúdo proposto |
|---|---|
| `CREATE_INTAKE` (solicitante) | conjunto mínimo v1 + `drawing_code` opcional |
| `ENGINEERING_PREPARATION` (analista) | paths editáveis = subset dos 21 graváveis com baseline oficial + paths read-only de contexto (revisão, peso, conversão) |
| `UPDATE_REQUESTED_DIFF` | só intenção seletiva por path (imutável) |
| `ERP_FULL_WRITE_REPRESENTATION` | backend compõe os 21 completos a partir do **snapshot oficial fresco** + diff (nunca do draft) — elimina risco de zerar campos não tocados |
| `OFFICIAL_READBACK` | leitura oficial pós-write gravada como evidência por campo |
| `TRACKED_PRODUCT_REVISION` | snapshot versionado autorizado por path (inclui SA5 ops) — habilita comparação antes×solicitado×confirmado |
| `NO_PRC` | fiscais/comerciais/custo e ERP-owned — nunca expostos à edição |

Dependências: catálogo versionado com `official_field`+`source`; migração/backfill nulo para v1 (paths novos ausentes = não rastreados, sem reinterpretação); contrato api-delpi para SA5 write + CREATE façade; ratificação de owner por família de campo (engenharia × fiscal × comercial × ERP). Critérios de aceite da fase seguinte: matriz aprovada, SA5 write comprovado em TST01, read-back `CONFIRMED` no fluxo, zero campo novo sem owner ratificado.

## 11. Limitações desta evidência

- Metadados = base **DELPI produção** (espelho do que o runtime serve). Divergências TST01×PRD de dicionário são possíveis — revalidar antes de ensaios.
- Versão do `.PRW` compilada não comprovada por este inventário (`/restall` listing é `PROVEN_DOCUMENTED` de 17/11; refazer listing autenticado ao iniciar a fase de implementação).
- `X3_OBRIGAT`, `X3_CBOX`, defaults `X3_RELACAO` e `X3_VALID` estão extraídos mas **não interpretados** campo a campo — obrigatoriedade real sai de rotina+ensaio, não do flag.
- Nenhuma escrita executada; nenhum endpoint novo criado.

---

## 12. Inventário RESTALL autenticado (G0-B — 19/11/2026)

Catálogo vivo consultado por **login de formulário** (`POST {restall} __USER/__PSW`) com a conta de serviço `USR_PROTHEUS` resolvida de `PARAMETROS_MINHADELPI` — mesmo mecanismo governado que a api-delpi usa. Somente GET/POST de catálogo; **zero chamada de negócio, zero escrita**.

| Ambiente | URL_REST | Catálogo | Classes | Evidência |
|---|---|---|---|---|
| amb=1 (PRD) | `http://192.168.1.231:8061` | `POST /restall` | **527** | HTML ~1,9 MB |
| amb=2 (TST01) | `http://192.168.1.233:8701/rest` | `POST /rest` | **526** | HTML ~1,9 MB |

**Delta PRD×TST01:** única classe — `ESTABLISHMENT` presente só em PRD. Todas as classes relevantes a produto/fornecedor existem **nos dois** ambientes (ensaios TST01 são representativos).

### 12.1 Rotas relevantes publicadas (confirmadas em ambos)

| Classe | URI oficial | Métodos | Semântica | Leitura/Escrita |
|---|---|---|---|---|
| `DELPIPRODUTO` (custom) | `/v1/IncProduto/incluir` `…/alterar` | POST, PUT | Insere / altera produto via `MATA010`+`MSExecAuto` (DLP04I01.PRW) | WRITE custom |
| `MRPPRODUCT` (nativa) | `api/pcp/v1/mrpproduct` | GET, GET `/{branchId}/{product}`, POST (inclui **ou atualiza**), POST `/sync`, DELETE | "Produto MRP" — dados MRP do produto (subconjunto planejamento; escopo de campos B1 `TO_INVENTORY`) | READ + WRITE nativa |
| `MRPPRODUCTINDICATOR` (nativa) | `api/pcp/v1/mrpproductindicator` | idem | Indicadores MRP do produto | READ + WRITE nativa |
| `TSIITEM` (nativa) | `/tsiitem` | GET, POST, PUT, DELETE | "Api de persistência ao produto" (EAI/TSI) — schema de payload `TO_INVENTORY` | READ + WRITE nativa |
| `GETITEMSINFORMATION` (nativa) | `/getitemsinformation` | GET (params obrigatórios: `sourceapp,companyid,branchid,initialiteminternalid,finishiteminternalid`) | Info de produtos p/ integração EAI | READ nativa |
| `CUSTOMERVENDOR` (nativa) | `/api/crm/v1/customerVendor` | GET(all/byType/byId), POST, PUT `/{Type}/{id}`, DELETE `/{Type}/{id}` | Cadastro **SA1/SA2** (cliente/fornecedor) — **não** é vínculo produto×fornecedor | READ + WRITE nativa |
| `ACCOUNTINGITEMS` (nativa) | `/api/ctb/v1/AccountingItems` | GET, POST, PUT, DELETE por `InternalId` | "Item Contábil" (contexto CTB) — **candidata** a cobrir dimensão contábil de itens (`B1_CONTA`?) `TO_INVENTORY` | READ + WRITE nativa |
| `MRPBILLOFMATERIAL` (nativa) | `api/pcp/v1/mrpbillofmaterial` | GET/POST/DELETE (+component/alternative) | Estrutura SG1 — fora do escopo PRC cadastro | referência |

**Correção ao playbook de write-integration:** `delpiproduto` publica somente `POST_INCPROD`+`PUT_INCPROD` — **não existe `excluir` publicado** em nenhum ambiente (confirma o alerta já registrado no G0-A).

### 12.2 SA5 — veredito do catálogo vivo

`PROVEN_NOT_PUBLISHED`: nenhuma classe nas 527/526 publicadas manipula amarração produto×fornecedor (MATA061/SA5). `CUSTOMERVENDOR` cobre SA1/SA2; `TOTVSEAI` é serviço genérico de orquestração EAI (não é contrato de SA5). Toda capacidade SA5 (ADD/UPDATE/REMOVE/read-back) exige **capacidade nova** — rotina oficial em .PRW + publicação + façade + gate.

### 12.3 Matriz necessidade PRC × rota existente

| Necessidade PRC | Equivalente TOTVS | Publicada | api-delpi expõe | Decisão proposta |
|---|---|---|---|---|
| Consultar produto | `GETITEMSINFORMATION`, `MRPPRODUCT` GET | SIM | SIM (ODBC `products.detail`) | REUSE api-delpi atual |
| Consultar vínculos SA5 | — (não há classe SA5) | NÃO | SIM (ODBC `products.suppliers`) | REUSE api-delpi atual |
| Criar produto SB1 | `DELPIPRODUTO` POST (custom, 22 campos); `TSIITEM` POST; `MRPPRODUCT` POST (subconjunto) | SIM | **NÃO** | REUSE custom existente → criar **façade** api-delpi (nova rota DELPI, não TOTVS) |
| Alterar produto SB1 | `DELPIPRODUTO` PUT (22 campos); `TSIITEM` PUT; `MRPPRODUCT` POST | SIM | SIM (`PUT /integrations/protheus/products/{code}`) | REUSE existente |
| `B1_CONTA` | fora do array delpiproduto; `ACCOUNTINGITEMS` candidata | SIM | NÃO | `TO_INVENTORY` — validar se AccountingItems grava dimensão SB1 antes de propor |
| SA5 ADD/UPDATE/REMOVE | **nenhuma** | NÃO | NÃO | **CREATE** — decisão arquitetural (rotina oficial MATA061 via execauto ou recno-write governado) |
| Read-back pós-escrita | `MRPPRODUCT` GET, `GETITEMSINFORMATION`, `CUSTOMERVENDOR` GET | SIM | SIM (ODBC) | REUSE api-delpi ODBC (grão SB1/SA5 real) |

### 12.4 Achados de contrato

- **CREATE SB1:** rota custom já publicada em ambos os ambientes; payload = os mesmos 22 campos do UPDATE (§4). Obrigatórios reais de `MATA010` op3 **não** comprovados — `TO_INVENTORY` (ensaio TST01). `B1_COD`: passado no array (código manual); geração automática via semáforo `SXE/SXF` não comprovada no handler.
- **UPDATE SB1:** 22 campos idênticos ao CREATE; façade já impõe representação completa (lição `VAL()` documentada). Cobertura = 22/313 campos de negócio.
- **`B1_CONTA`:** rastreado pelo PRC sem caminho de write no handler. Alternativa `ACCOUNTINGITEMS` publicada — schema/semântica `TO_INVENTORY`; **não presumir** que grava `SB1.B1_CONTA` sem homologação.
- **SA5:** gap total — ver §12.2.
- **MRPPRODUCT:** POST é **upsert** ("Inclui ou atualiza"); provavelmente subconjunto MRP/planejamento de SB1 — candidato complementar para campos de planejamento (B1_LE/B1_RE/B1_CC etc.) — escopo `TO_INVENTORY`.
- **TSIITEM:** CRUD completo "persistência ao produto" via TSI/EAI — contrato de payload não exposto no catálogo; `TO_INVENTORY` antes de qualquer uso.
- **GETITEMSINFORMATION:** leitura EAI com params obrigatórios pesados — read-back preferencial continua sendo ODBC api-delpi.

### 12.5 Protocolo de ensaios TST01 (proposto — `TEST_NOT_RUN`)

| Ensaio | Massa | Critério | Rollback |
|---|---|---|---|
| CREATE mínimo | produto `TESTEPRC` filial 01, grupo existente, tipo `PA` | campos mínimos aceitos, read-back ODBC, obrigatórios reais mapeados | delete governado ou flag de teste |
| CREATE/UPDATE campo-a-campo | mesmo produto | cada um dos 22 campos persiste; campos fora do array preservados | snapshot SB1 anterior |
| UPDATE representação | produto de teste | PUT com 21 campos + path; read-back confirma não-destruição | restore snapshot |
| `B1_CONTA` via `ACCOUNTINGITEMS` | produto de teste | comprova/elimina a hipótese de gravação em SB1 | restore |
| SA5 | vínculo `TESTEPRC`×fornecedor de teste | exige capacidade nova — **bloqueado até decisão arquitetural** | — |
| Negativos | permissão insuficiente, payload inválido, obrigatório ausente, código duplicado, timeout | recusa determinística, `UNKNOWN` sinalizado | — |

Execução depende de **autorização explícita TST01** com identidade, dados e rollback definidos — `TEST_NOT_RUN` nesta fase.
