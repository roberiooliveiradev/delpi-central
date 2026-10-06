# Auditoria do Modelo de Fornecedores — TOTVS Protheus (DELPI)

> CLASS = READ / INVENTORY / AUDIT. Nenhuma escrita foi executada. Todas as consultas foram SELECT read-only (com `NOLOCK` apenas em contagens agregadas), dicionário SX\* e catálogo `sys.*`.
> Base de evidência: SQL Server `srv-db01` (192.168.1.230), database `DELPI`, dicionários por empresa `SX?010` (empresa 01), `SX?030`, `SX?040`, `SX?050`.
> Convenção de evidência: **PROVEN** (evidência direta em dicionário/schema físico/dados/código), **TO_INVENTORY** (existe lead mas sem prova), **UNKNOWN** (não determinável com as capabilities disponíveis), **NOT_APPLICABLE**.

# 1. Executive Summary

- O cadastro de fornecedores é a tabela **`SA2`**, física **`SA2010`** na empresa 01 (MODO=C, compartilhada entre filiais — `A2_FILIAL` vazio em 100% dos registros). Empresas 03, 04 e 05 possuem tabelas próprias (`SA2030`, `SA2040`, `SA2050`) com bases distintas. **[PROVEN]**
- A SA2010 possui **248 campos de dicionário** (SX3010), dos quais 3 são virtuais (`A2_DTPAWB`, `A2_NOMFAV`, `A2_PAISDES` — não existem fisicamente) e o físico tem +5 colunas de sistema (`D_E_L_E_T_`, `R_E_C_N_O_`, `R_E_C_D_E_L_`, `S_T_A_M_P_`, `I_N_S_D_T_`). **[PROVEN]**
- **Identidade física**: PK `R_E_C_N_O_` + índice único `SA2010_UNQ (A2_FILIAL, A2_COD, A2_LOJA, R_E_C_D_E_L_)`. Chave de negócio = **`A2_COD` + `A2_LOJA`** (filial em branco). **CNPJ/CPF não é chave e não é único** (32 valores duplicados, inclusive entre códigos distintos). **[PROVEN]**
- **Geração de código**: `A2_COD` tem default `GETSXENUM("SA2")` nas empresas 01 e 05; nas empresas 03/04 o default não existe (entrada manual). Padrão observado: sequencial numérico 6 dígitos (`003929` atual máximo), com exceções manuais (`VIAGEM`, `FISCO`, `INPS`...). A tabela de numerador `SXE` **não existe** na base DELPI — mecanismo de resolução do próximo número é **TO_INVENTORY** (provavelmente lado appserver/licença TOTVS ou rotina MATA020). **[PROVEN parcial + TO_INVENTORY]**
- **Customizações DELPI na SA2**: apenas 3 campos de usuário — `A2_YROHS` (RoHS?, usado em 67% dos registros), `A2_YFGEN` (For. Genérico) e `A2_ZTABPRC` (Tab. Preço Compra, F3→AIA). Não há tabelas Z\* de fornecedor. **[PROVEN]**
- **Tabelas relacionadas materialmente usadas**: `SA5` Produto×Fornecedor (40.671 linhas, tabela cadastral separada — NÃO criada junto com SA2), `SAD` Grupo×Fornecedor (5.512), `AIA`/`AIB` tabelas de preço (329/8.616), `AIC` tolerância de entrada (636). Contatos/dados bancários ficam **dentro da SA2** (tabelas DKI/D30/FV6 existem mas têm 0 linhas). **[PROVEN]**
- **Lookups obrigatórios por validação** (SX9/X3): `SE4` cond. pagamento, `SED` natureza, `SA6` banco, `SA4` transportadora, `SYA` país, `CCH` país BACEN, `CC2` município IBGE, `CT1` conta contábil, `SX5` tabelas genéricas (12=UF, Y7=grupo, 58=forma pgto, T3=segmento, 48, 83, MF...), `SA1` cliente vinculado, `SRA` funcionário vinculado, `SAE`, `ACJ` DDI, `SYR` origem. **[PROVEN]**
- **Consumidores transacionais** (apenas leem SA2): SC1, SC7, SC8, SD1, SF1, SE2, SE5, SF3, SFT, SCY, SCE, SDS, SFJ — centenas de milhares de linhas. **[PROVEN]**
- **Rotina dona do cadastro**: `MATA020` (referenciada na SX2). A API/ponte deverá respeitar as mesmas validações. **[PROVEN]**
- Inventário de relacionamentos: **607 relações SX9 com SA2 como dominante** — a maioria de módulos TOTVS não instalados/sem dados na DELPI. Classificação: `COMPLETE_BY_AVAILABLE_METADATA` para a metadesesencial; `INCOMPLETE` para módulos verticais sem evidência de uso.
- **Capacidade não coberta**: a lógica interna da rotina MATA020 (ADVPL server-side) e o contrato da API/ponte do Gabriel não são introspectáveis por esta auditoria → seções `Questions for Gabriel` e `Capability Gaps`.

# 2. Scope and Evidence

| Fonte | Uso | Cobertura |
|---|---|---|
| SX2010/SX2030/SX2040/SX2050 (SX2) | tabela/alias/modo/chave única/rotina | completa p/ SA2, SA5 e tabelas relacionadas |
| SX3010/SX3030/SX3040/SX3050 (SX3) | 100% dos campos + VALID/RELACAO/F3/CBOX/WHEN | completa |
| SIX010 (SIX) | índices lógicos SA2/SA5 | completa |
| SX9010 (SX9) | relações declaradas dominante/filho | completa (607+41) |
| SXB010 (SXB) | consulta padrão FOR | completa |
| SX5010 (SX5) | domínios genéricos usados pela SA2 | parcial — apenas tabelas referenciadas por SA2 |
| sys.tables/sys.columns/sys.indexes/sys.triggers | schema físico, PK/UNQ, triggers | completa |
| Dados SA2010/SA5010 (read-only, NOLOCK) | fill rates, domínios, duplicidades | completa p/ perguntas da auditoria |
| Código api-delpi | evidência de uso vigente (read) | completa p/ leituras existentes |
| Rotina MATA020 (ADVPL) | **indisponível** — binário/appserver | CAPABILITY_GAP |
| API/ponte Gabriel | **inexistente no repo** — ainda não implementada | N/A |

# 3. Supplier Data Model Overview

```text
SA2 / SA2010 — FORNECEDOR (master, MATA020)                     [empresa 01]
├── SA5 / SA5010 — Amarração Produto × Fornecedor (MATA061)     [cadastral, NÃO automática]
│     ├── AIA/AIB — Tabela de Preços do Fornecedor              [cadastral, opcional]
│     ├── AIC — Tolerância na Entrada de Material               [cadastral, opcional]
│     └── SAD — Amarração Grupo × Fornecedor                    [cadastral, 5.5k regs usados]
├── Lookups obrigatórios conforme campos enviados:
│     SE4 (cond. pagto) · SED (natureza) · SA6 (banco) · SA4 (transportadora)
│     SYA (país) · CCH (país BACEN) · CC2 (município IBGE) · CT1 (conta contábil)
│     SX5 (UF '12', grupo 'Y7', forma pgto '58', segmento 'T3', '48', '83', 'MF')
│     SA1 (cliente vinculado) · SRA (funcionário) · SAE · ACJ (DDI) · SYR (origem)
├── Cadastro-complemento existentes mas VAZIOS na DELPI:
│     DKI (contatos×forn.) · D30 (compl. SIMP) · DD1 (docs exigidos) · FV6 (dados pagto favorecido) · G4R
├── Apenas-dicionário (módulos sem tabela física):
│     D2C (contatos) · COP · DD5 · FTG · BA4 · G4S · SS3
└── Consumidores transacionais (read-only do cadastro):
      SC1 Solicitação · SC7 Pedido Compra · SC8 Cotação · SF1 NF Entrada
      SD1 Itens NF Entrada · SE2 Contas a Pagar · SE5 Mov. Bancária
      SF3/SFT Livros Fiscais · SCY Hist. Pedidos · SCE · SDS · SFJ
```

# 4. Authoritative Master Table

| Propriedade | Valor | Evidência |
|---|---|---|
| Alias | `SA2` | SX2010.X2_CHAVE |
| Tabela física (emp. 01) | `SA2010` | SX2010.X2_ARQUIVO + sys.tables |
| Outras empresas | `SA2030` (emp 03), `SA2040` (emp 04), `SA2050` (emp 05) | sys.tables + SX2030/40/50 |
| Descrição | Fornecedores / Suppliers | X2_NOME |
| MODO/MODOUN/MODOEMP | C / E / E (compartilhada entre filiais; unidade e empresa exclusivas) | SX2010 |
| Rotina owner | `MATA020` (módulo Compras) | SX2010 |
| Chave única lógica | `A2_FILIAL + A2_COD + A2_LOJA` | X2_UNICO |
| PK física | `R_E_C_N_O_` (`SA2010_PK`) | sys.indexes is_primary_key |
| Único físico | `SA2010_UNQ (A2_FILIAL, A2_COD, A2_LOJA, R_E_C_D_E_L_)` | sys.indexes is_unique |
| TTS/auditoria | `X2_TTS=S`; trigger física `SA2010_STAMP`; tabela `SA2010_TTAT_LOG` (estrutura pronta, 0 linhas) | SX2010 + sys.triggers |
| Registros | emp01: 3.663 (19 deletados) · emp03: 226 · emp04: 68 · emp05: 314 | COUNT read-only |
| Campos dicionário | 248 (emp01) / 242 (emp03/04) / 248 (emp05) | SX3 |

Nota empresas: o registro de empresas (SM0) não existe nesta base — nomes das empresas 03/04/05 = **UNKNOWN**. Diferença 248↔242 campos: empresas 03/04 não possuem `A2_PABCB, A2_ECDTEX, A2_ECSEQ, A2_ECFLAG` (SYS) nem `A2_YFGEN, A2_YROHS` (DELPI).

# 5. SA2010 / SA2 — Complete Schema (SX3010, empresa 01)

Legenda de metadata: `V`=X3_VALID · `DEF`=X3_RELACAO (init/default) · `F3=`consulta padrão · `CBOX`=domínio enumerado · `WHEN`=condicional · `OBRIG1`=X3_OBRIGAT flag pos.1 · `DELPI`=PROPRI=U (custom) · `SYS`=PROPRI=S.

| # | Campo | Tipo | Tam | Dec | Título (SX3) | Metadata |
|---|---|---|---|---|---|---|
| 01 | `A2_FILIAL` | C | 2 | 0 | Filial |  |
| 02 | `A2_CGC` | C | 14 | 0 | CNPJ/CPF | V  |
| 03 | `A2_COD` | C | 6 | 0 | Codigo | V DEF  |
| 04 | `A2_LOJA` | C | 2 | 0 | Loja | V  |
| 05 | `A2_NOME` | C | 50 | 0 | Razao Social | V  |
| 06 | `A2_NREDUZ` | C | 20 | 0 | N Fantasia | V  |
| 07 | `A2_END` | C | 40 | 0 | Endereco | V  |
| 08 | `A2_NR_END` | C | 6 | 0 | Numero |  |
| 09 | `A2_BAIRRO` | C | 20 | 0 | Bairro | V  |
| 10 | `A2_ROYMIN` | N | 7 | 2 | Royalt Min. |  |
| 11 | `A2_SUBCOD` | C | 1 | 0 | Sub Codigo |  |
| 12 | `A2_PAGAMEN` | C | 1 | 0 | Receb.Pagto. | V CBOX  |
| 13 | `A2_SATIV1` | C | 6 | 0 | Segmento 1 | V F3=T3  |
| 14 | `A2_CONREG` | C | 10 | 0 | Numero C.R | V  |
| 15 | `A2_SIGLCR` | C | 7 | 0 | Sigla C.R | F3=B7  |
| 16 | `A2_PLFIL` | C | 1 | 0 | Filial Grupo | DEF CBOX  |
| 17 | `A2_DDD` | C | 3 | 0 | DDD |  |
| 18 | `A2_CIVIL` | C | 1 | 0 | Estado Civil | V CBOX WHEN  |
| 19 | `A2_DDI` | C | 6 | 0 | DDI | V F3=ACJ  |
| 20 | `A2_PLPEDES` | N | 13 | 4 | % Desc. PLS |  |
| 21 | `A2_TEL` | C | 50 | 0 | Telefone | OBRIG1  |
| 22 | `A2_DATBLO` | D | 8 | 0 | Data Bloq. |  |
| 23 | `A2_INSCR` | C | 18 | 0 | Ins. Estad. | V  |
| 24 | `A2_MSBLQL` | C | 1 | 0 | Bloqueado | V DEF CBOX  |
| 25 | `A2_INSCRM` | C | 18 | 0 | Ins. Municip |  |
| 26 | `A2_FAX` | C | 15 | 0 | FAX |  |
| 27 | `A2_CONTATO` | C | 15 | 0 | Contato | OBRIG1  |
| 28 | `A2_BANCO` | C | 3 | 0 | Banco | F3=SA6  |
| 29 | `A2_RECCSLL` | C | 1 | 0 | Rec.CSLL | V DEF CBOX  |
| 30 | `A2_AGENCIA` | C | 5 | 0 | Cod Agencia |  |
| 31 | `A2_NUMRA` | C | 6 | 0 | C�d Func | V  |
| 32 | `A2_ABICS` | C | 4 | 0 | Cod. Abics |  |
| 33 | `A2_DVAGE` | C | 1 | 0 | DV Ag Cnab |  |
| 34 | `A2_NUMCON` | C | 10 | 0 | Cta Corrente |  |
| 35 | `A2_RECSEST` | C | 1 | 0 | Recolhe SEST | V CBOX  |
| 36 | `A2_DTPAWB` | C | 30 | 0 | Desc.Tip.AWB | DEF  |
| 37 | `A2_DVCTA` | C | 2 | 0 | DV Cta Cnab |  |
| 38 | `A2_TIPAWB` | C | 1 | 0 | Tipo AWB | V F3=MF  |
| 39 | `A2_SWIFT` | C | 30 | 0 | Swift |  |
| 40 | `A2_NATUREZ` | C | 10 | 0 | Natureza | V F3=SED OBRIG1  |
| 41 | `A2_RECCOFI` | C | 1 | 0 | Rec.COFINS | V DEF CBOX  |
| 42 | `A2_TRANSP` | C | 6 | 0 | Transp. | V F3=SA4  |
| 43 | `A2_RECPIS` | C | 1 | 0 | Rec. PIS | V DEF CBOX  |
| 44 | `A2_PRIOR` | C | 1 | 0 | Prioridade |  |
| 45 | `A2_FILDEB` | C | 2 | 0 | Fil.Debito | V F3=DLB  |
| 46 | `A2_EST` | C | 2 | 0 | Estado | V F3=12  |
| 47 | `A2_RISCO` | C | 3 | 0 | Risco |  |
| 48 | `A2_COD_MUN` | C | 5 | 0 | Cod. Municip | V F3=CC2SA2 OBRIG1  |
| 49 | `A2_COND` | C | 3 | 0 | Cond. Pagto | V F3=SE4  |
| 50 | `A2_MUN` | C | 25 | 0 | Municipio | V  |
| 51 | `A2_LC` | C | 14 | 0 | Lim. Credito |  |
| 52 | `A2_ESTADO` | C | 20 | 0 | Nome Estado |  |
| 53 | `A2_MATR` | N | 4 | 0 | Maior Atraso |  |
| 54 | `A2_CODPAIS` | C | 5 | 0 | Pa�s Bacen | V F3=CCH OBRIG1  |
| 55 | `A2_MCOMPRA` | N | 17 | 2 | Maior Compra |  |
| 56 | `A2_CEP` | C | 8 | 0 | CEP |  |
| 57 | `A2_METR` | N | 5 | 1 | Media Atraso |  |
| 58 | `A2_CX_POST` | C | 5 | 0 | Caixa Postal |  |
| 59 | `A2_ULTCOM` | D | 8 | 0 | Ult Compra |  |
| 60 | `A2_TIPO` | C | 1 | 0 | Tipo | V DEF CBOX  |
| 61 | `A2_MSALDO` | N | 17 | 2 | Maior Saldo |  |
| 62 | `A2_PFISICA` | C | 18 | 0 | RG/Ced.Estr. | V  |
| 63 | `A2_NROCOM` | N | 6 | 0 | No Compras |  |
| 64 | `A2_PRICOM` | D | 8 | 0 | 1a Compra |  |
| 65 | `A2_CONTA` | C | 20 | 0 | C Contabil | V F3=CT1 OBRIG1  |
| 66 | `A2_TIPORUR` | C | 1 | 0 | Tp.Contr.Soc | CBOX  |
| 67 | `A2_SALDUP` | N | 17 | 2 | Sld Duplict |  |
| 68 | `A2_DESVIO` | N | 6 | 1 | Desvio |  |
| 69 | `A2_SALDUPM` | N | 17 | 2 | Sld Moed.For |  |
| 70 | `A2_RECISS` | C | 1 | 0 | Recolhe ISS? | V CBOX  |
| 71 | `A2_ID_FBFN` | C | 7 | 0 | Identificac. | V F3=48  |
| 72 | `A2_STATUS` | C | 1 | 0 | Status | V CBOX  |
| 73 | `A2_GRUPO` | C | 3 | 0 | Grupo | V F3=GRU  |
| 74 | `A2_ATIVIDA` | C | 7 | 0 | Cod.Ativida. |  |
| 75 | `A2_PAIS` | C | 3 | 0 | Pais | V F3=SYA  |
| 76 | `A2_PAISDES` | C | 25 | 0 | Descr. Pais | DEF  |
| 77 | `A2_DEPTO` | C | 30 | 0 | Departamento |  |
| 78 | `A2_ORIG_1` | C | 3 | 0 | Origem 1 | V F3=SYR  |
| 79 | `A2_REPRES` | C | 52 | 0 | Represent. |  |
| 80 | `A2_REPCONT` | C | 50 | 0 | Contato Repr |  |
| 81 | `A2_REPRTEL` | C | 50 | 0 | Tel. Repres. |  |
| 82 | `A2_REPRFAX` | C | 30 | 0 | FAX Repres. |  |
| 83 | `A2_ORIG_2` | C | 3 | 0 | Origem 2 | V F3=SYR  |
| 84 | `A2_ORIG_3` | C | 3 | 0 | Origem 3 | V F3=SYR  |
| 85 | `A2_VINCULA` | C | 1 | 0 | Vinculacao | V DEF CBOX  |
| 86 | `A2_REPRMUN` | C | 30 | 0 | Cidade |  |
| 87 | `A2_REPREST` | C | 2 | 0 | Estado Reprs | V F3=12  |
| 88 | `A2_REPRCEP` | C | 8 | 0 | CEP Repres. |  |
| 89 | `A2_REPPAIS` | C | 3 | 0 | Pais Repres. | V F3=SYA  |
| 90 | `A2_REPR_EM` | C | 30 | 0 | E-Mail Repr. |  |
| 91 | `A2_REPR_BA` | C | 3 | 0 | Bco. Repres. | V F3=BCO  |
| 92 | `A2_REPR_EN` | C | 52 | 0 | End.Repres. |  |
| 93 | `A2_REPBAIR` | C | 30 | 0 | Bairro Repr. |  |
| 94 | `A2_ID_REPR` | C | 1 | 0 | Identif.Repr | V DEF CBOX  |
| 95 | `A2_REPR_AG` | C | 5 | 0 | Agenc. Repr. | V F3=BC2 WHEN  |
| 96 | `A2_COMI_SO` | C | 1 | 0 | Tipo Comis. | V CBOX  |
| 97 | `A2_REPR_CO` | C | 10 | 0 | C/C Repres. |  |
| 98 | `A2_REPRCGC` | C | 14 | 0 | CNPJ Repres. | V  |
| 99 | `A2_CODMUN` | C | 5 | 0 | Cod. Mun. ZF | V F3=S1  |
| A0 | `A2_RET_PAI` | C | 1 | 0 | Comis.Retida | V CBOX  |
| A1 | `A2_EMAIL` | C | 50 | 0 | E-Mail | OBRIG1  |
| A2 | `A2_HPAGE` | C | 30 | 0 | Home-Page |  |
| A3 | `A2_CONTCOM` | C | 15 | 0 | Contato Com. |  |
| A4 | `A2_OK` | C | 2 | 0 | OK |  |
| A5 | `A2_FATAVA` | N | 6 | 2 | Fator Aval. | V  |
| A6 | `A2_DTAVA` | D | 8 | 0 | Data Aval. |  |
| A7 | `A2_DTVAL` | D | 8 | 0 | Data Valid. | V DEF  |
| A8 | `A2_UNFEDRP` | C | 30 | 0 | Unid.Fed.Ext |  |
| A9 | `A2_CONTAB` | C | 15 | 0 | C.Contab.Imp |  |
| AA | `A2_RECINSS` | C | 1 | 0 | Calc. INSS ? | V CBOX  |
| AB | `A2_TELEX` | C | 10 | 0 | Telex |  |
| AC | `A2_GRPTRIB` | C | 3 | 0 | Grp. Tribut. |  |
| AD | `A2_CLIQF` | C | 15 | 0 | Liquid.Futur |  |
| AE | `A2_PLGRUPO` | C | 3 | 0 | Classe Forn. | V F3=B9  |
| AF | `A2_CODBLO` | C | 3 | 0 | Cod.Bloqueio |  |
| AG | `A2_PAISORI` | C | 20 | 0 | Pais Origem |  |
| AH | `A2_ROYALTY` | C | 1 | 0 | Royalty | V F3=H4  |
| AI | `A2_TXTRIBU` | N | 6 | 2 | TX-BI-Tribut |  |
| AJ | `A2_B2B` | C | 1 | 0 | Utiliza B2B | V DEF CBOX  |
| AK | `A2_ENDCOMP` | C | 21 | 0 | Compl. End. |  |
| AL | `A2_GRPDEP` | C | 5 | 0 | Grupo Almox | V F3=74  |
| AM | `A2_FRETISS` | C | 1 | 0 | F.Ret.ISS | V CBOX  |
| AN | `A2_PABCB` | C | 5 | 0 | Cod.Pais BCB | SYS  |
| AO | `A2_FABRICA` | C | 1 | 0 | Fabricante | V F3=48 CBOX  |
| AP | `A2_PLCRRES` | C | 1 | 0 | Obrig.Resp? | DEF CBOX  |
| AQ | `A2_TPISSRS` | C | 2 | 0 | Tipo de Escr | V  |
| AR | `A2_CTARE` | C | 1 | 0 | Contr TARE ? | V CBOX  |
| AS | `A2_RECFET` | C | 1 | 0 | Rec. FETHAB | V CBOX  |
| AT | `A2_TPESSOA` | C | 2 | 0 | Tipo Pessoa | CBOX  |
| AU | `A2_RECCIDE` | C | 1 | 0 | Rec Cide | V CBOX  |
| AV | `A2_CODLOC` | C | 8 | 0 | Cod.Local | V  |
| AW | `A2_MNOTA` | N | 17 | 2 | Maior Nota |  |
| AX | `A2_CBO` | C | 7 | 0 | Cod CBO | WHEN  |
| AY | `A2_CNAE` | C | 9 | 0 | Cod CNAE | WHEN  |
| AZ | `A2_CODFAV` | C | 6 | 0 | Cod.Favorec | V F3=FOR  |
| B0 | `A2_LOJFAV` | C | 2 | 0 | Loja Favorec | V  |
| B1 | `A2_NOMFAV` | C | 50 | 0 | Nome Favorec | DEF  |
| B2 | `A2_NUMDEP` | N | 2 | 0 | Dependentes | V  |
| B3 | `A2_CALCIRF` | C | 1 | 0 | C�lc. IRRF | V CBOX  |
| B4 | `A2_VINCULO` | C | 2 | 0 | P. Vinculo | V F3=CC1TIP  |
| B5 | `A2_CODINSS` | C | 11 | 0 | C�d. INSS |  |
| B6 | `A2_DTINIV` | D | 8 | 0 | Dt Ini Vincu |  |
| B7 | `A2_DTFIMV` | D | 8 | 0 | Dt Fim Vincu |  |
| B8 | `A2_CODSIAF` | C | 4 | 0 | Cod.Mun.SIAF |  |
| B9 | `A2_PRSTSER` | C | 1 | 0 | Ind. Prest. |  |
| BA | `A2_SIMPNAC` | C | 1 | 0 | Opt Simp Nac | V CBOX  |
| BB | `A2_INSCMU` | C | 1 | 0 | Ins. no Munc | V CBOX  |
| BC | `A2_COMPLEM` | C | 50 | 0 | Complemento |  |
| BD | `A2_IRPROG` | C | 1 | 0 | IRRF Prog | V CBOX  |
| BE | `A2_RFACS` | C | 1 | 0 | Rec. FACS | V CBOX  |
| BF | `A2_RFABOV` | C | 1 | 0 | Rec. FABOV | V CBOX  |
| BG | `A2_INCULT` | C | 1 | 0 | Inc. Cultura | V CBOX  |
| BH | `A2_CONTPRE` | C | 1 | 0 | Contrib. Pre | V DEF CBOX  |
| BI | `A2_FOMEZER` | C | 1 | 0 | Fome Zero | V CBOX  |
| BJ | `A2_REGESIM` | C | 1 | 0 | Rg. Simp. MT | DEF CBOX  |
| BK | `A2_CGCEX` | C | 14 | 0 | CNPJ Empr.Ex | V  |
| BL | `A2_NEMPR` | C | 150 | 0 | Nome Empres. |  |
| BM | `A2_TPCON` | C | 2 | 0 | Tipo Contrat |  |
| BN | `A2_DTINIR` | D | 8 | 0 | Data Inicio | DEF  |
| BO | `A2_DTFIMR` | D | 8 | 0 | Data Fim | V DEF  |
| BP | `A2_PAISEX` | C | 3 | 0 | Codigo Pais | V F3=SYA  |
| BQ | `A2_NIFEX` | C | 30 | 0 | Codigo NIF |  |
| BR | `A2_LOGEX` | C | 60 | 0 | Logradouro |  |
| BS | `A2_NUMEX` | C | 6 | 0 | Numero |  |
| BT | `A2_COMPLR` | C | 25 | 0 | Complemento |  |
| BU | `A2_BAIEX` | C | 20 | 0 | Bairro/Dist. |  |
| BV | `A2_POSEX` | C | 10 | 0 | Cod.Postal |  |
| BW | `A2_CIDEX` | C | 40 | 0 | Cidade |  |
| BX | `A2_ESTEX` | C | 40 | 0 | Est./Prov. |  |
| BY | `A2_TELRE` | C | 15 | 0 | Telefone |  |
| BZ | `A2_BREEX` | C | 3 | 0 | Benef.Rend. | V  |
| C0 | `A2_TPREX` | C | 3 | 0 | Rendimento | V  |
| C1 | `A2_ENDNOT` | C | 1 | 0 | End.Not.Form | V CBOX  |
| C2 | `A2_TRBEX` | C | 2 | 0 | Forma Trib. | V  |
| C3 | `A2_CPFIRP` | C | 11 | 0 | CPF IR Progr | V WHEN  |
| C4 | `A2_INCLTMG` | C | 1 | 0 | Inc.Prd.Leit | V CBOX  |
| C5 | `A2_MINIRF` | C | 1 | 0 | Vlr. Min. IR | V DEF CBOX  |
| C6 | `A2_CODADM` | C | 3 | 0 | C�d. Adm. | V F3=SAE  |
| C7 | `A2_TIPCTA` | C | 1 | 0 | Tp. Cta. For | V DEF CBOX  |
| C8 | `A2_IBGE` | C | 11 | 0 | Cod.IBGE | V F3=AM1  |
| C9 | `A2_IMPIP` | C | 1 | 0 | Ident.Prod. | DEF CBOX  |
| CA | `A2_MJURIDI` | C | 1 | 0 | M.Jur�dico | V DEF CBOX  |
| CB | `A2_RNTRC` | C | 14 | 0 | RNTRC |  |
| CC | `A2_MUNSC` | C | 5 | 0 | Cod Mun SC |  |
| CD | `A2_CONFFIS` | C | 1 | 0 | Conf. F�sica | V DEF CBOX  |
| CE | `A2_CPOMSP` | C | 1 | 0 | Reg. CPOM | V CBOX  |
| CF | `A2_TPLOGR` | C | 3 | 0 | Tp.Lograd |  |
| CG | `A2_CCICMS` | C | 1 | 0 | CCICMS | V CBOX  |
| CH | `A2_TRIBFAV` | C | 1 | 0 | Pes.Tri.Fav. | V CBOX  |
| CI | `A2_SITESBH` | C | 1 | 0 | SitEspRes BH | V CBOX  |
| CJ | `A2_TPJ` | C | 1 | 0 | TPJ | V CBOX  |
| CK | `A2_RETISI` | C | 1 | 0 | Retem ISI | V DEF CBOX  |
| CL | `A2_ISICM` | C | 1 | 0 | Conv. ISI | V  |
| CM | `A2_FILTRF` | C | 2 | 0 | Fil. Transf. | V F3=DLB  |
| CN | `A2_DTRNTRC` | D | 8 | 0 | Venc. RNTRC |  |
| CO | `A2_IDHIST` | C | 20 | 0 | ID Hist. |  |
| CP | `A2_TPCONTA` | C | 1 | 0 | Tipo Conta | CBOX  |
| CQ | `A2_LOCQUIT` | C | 1 | 0 | Local Quitac | V CBOX  |
| CR | `A2_TPRNTRC` | C | 1 | 0 | Tipo RNTRC | CBOX  |
| CS | `A2_STRNTRC` | C | 1 | 0 | Status RNTRC | CBOX  |
| CT | `A2_RECFMD` | C | 1 | 0 | Rec. Famad | V CBOX  |
| CU | `A2_EQPTAC` | C | 1 | 0 | Equipara TAC | V CBOX  |
| CV | `A2_INOVAUT` | C | 1 | 0 | Inovar Auto | V DEF CBOX  |
| CW | `A2_DTCONV` | D | 8 | 0 | Dt. Conv |  |
| CX | `A2_NOMRESP` | C | 45 | 0 | Nome Resp. |  |
| CY | `A2_CARGO` | C | 40 | 0 | Cargo Resp. |  |
| CZ | `A2_APOLICE` | C | 15 | 0 | Num. Apolice |  |
| D0 | `A2_RESPTRI` | C | 2 | 0 | Reg.Esp.Trib | V F3=83  |
| D1 | `A2_INDRUR` | C | 1 | 0 | Ind.Prod.Rur | V DEF CBOX  |
| D2 | `A2_ECDTEX` | C | 8 | 0 | Dt Exp | SYS  |
| D3 | `A2_UFFIC` | C | 2 | 0 | UF Ficticia | CBOX WHEN  |
| D4 | `A2_ECSEQ` | C | 15 | 0 | Seq.Exp | SYS  |
| D5 | `A2_TPREG` | C | 1 | 0 | Tp. Reg | V CBOX  |
| D6 | `A2_SUBCON` | C | 1 | 0 | SUBCON | V CBOX  |
| D7 | `A2_RFASEMT` | C | 1 | 0 | Rec.FASE-MT | V CBOX  |
| D8 | `A2_RIMAMT` | C | 1 | 0 | Rec. IMA-MT | V CBOX  |
| D9 | `A2_CATEG` | C | 2 | 0 | Categ. SEFIP |  |
| DA | `A2_CODNIT` | C | 11 | 0 | Num Insc Aut |  |
| DB | `A2_CONTRIB` | C | 1 | 0 | Contribuinte | V CBOX  |
| DC | `A2_DTNASC` | D | 8 | 0 | Data nasc. |  |
| DD | `A2_OCORREN` | C | 2 | 0 | Ocorr�ncia | V WHEN  |
| DE | `A2_CODFI` | C | 3 | 0 | Cod. FIESP |  |
| DF | `A2_FORMPAG` | C | 2 | 0 | Form. Pgto | V F3=58 OBRIG1  |
| DG | `A2_RFUNDES` | C | 1 | 0 | Rec.FUNDESA | V CBOX  |
| DH | `A2_MSBLQD` | D | 8 | 0 | BlqTemporal |  |
| DI | `A2_ECFLAG` | C | 1 | 0 | E-Commerce | CBOX WHEN SYS  |
| DJ | `A2_ISSRSLC` | C | 1 | 0 | LC ISS RS | V CBOX  |
| DK | `A2_PAGGFE` | C | 1 | 0 | Pagto GFE | V DEF CBOX  |
| DL | `A2_FORNEMA` | C | 1 | 0 | Forn.Mailing | V DEF CBOX  |
| DM | `A2_MINPUB` | C | 1 | 0 | Vl. M�n. Pub | V DEF CBOX  |
| DN | `A2_REGPB` | C | 1 | 0 | Reg.Para�ba | V CBOX  |
| DO | `A2_MOTNIF` | C | 1 | 0 | Mot.NIF | DEF CBOX  |
| DP | `A2_DESPORT` | C | 1 | 0 | Assoc. Desp. | V CBOX  |
| DQ | `A2_CLIENTE` | C | 6 | 0 | C�d. Cliente | V F3=SA1  |
| DR | `A2_CALCINP` | C | 1 | 0 | Calc.INSS.Pt | V CBOX  |
| DS | `A2_DEDBSPC` | C | 1 | 0 | Ded.PIS/COF | V DEF CBOX  |
| DT | `A2_LOJCLI` | C | 2 | 0 | Loja Cliente | V  |
| DU | `A2_DRPEXP` | C | 8 | 0 | Ident.Exp. |  |
| DV | `A2_CPRB` | C | 1 | 0 | Ret. CPRB | V DEF CBOX  |
| DW | `A2_GROSSIR` | C | 1 | 0 | Base Calc IR | CBOX  |
| DX | `A2_TPENT` | C | 1 | 0 | Clas.PJ | V CBOX  |
| DY | `A2_YROHS` | C | 1 | 0 | RoHS ? | CBOX OBRIG1 DELPI  |
| DZ | `A2_INDCP` | C | 1 | 0 | Ind. Rural | V CBOX  |
| E0 | `A2_CPFRUR` | C | 11 | 0 | CPF Rural | V WHEN  |
| E1 | `A2_YFGEN` | C | 1 | 0 | For Generico | CBOX DELPI  |
| E2 | `A2_PAISSUB` | C | 6 | 0 | SubDivPais |  |
| E3 | `A2_CATEFD` | C | 3 | 0 | Cat eSocial | F3=S049BR  |
| E4 | `A2_ZTABPRC` | C | 3 | 0 | Tab Prc Comp | F3=AIA DELPI  |


Colunas físicas fora do dicionário (system-owned, nunca enviar): `D_E_L_E_T_` (soft delete `*`), `R_E_C_N_O_` (PK), `R_E_C_D_E_L_` (recno pré-delete — componente do índice UNQ), `S_T_A_M_P_` (rowversion mantido por trigger `SA2010_STAMP`), `I_N_S_D_T_` (timestamp de inserção).
Campos de dicionário sem coluna física (virtuais/calculados): `A2_DTPAWB`, `A2_NOMFAV`, `A2_PAISDES`.

# 6. SA2010 Indexes

Fonte: SIX010 (lógico) + sys.indexes (físico). Ordem lógica ⇄ índice físico.

| Ord | Chave lógica (SIX) | Descrição | Índice físico | Único? |
|---|---|---|---|---|
| 1 | `A2_FILIAL+A2_COD+A2_LOJA` | Código + Loja | `SA20101` | não (UNQ separado) |
| 2 | `A2_FILIAL+A2_NOME+A2_LOJA` | Razão Social + Loja | `SA20102` | não |
| 3 | `A2_FILIAL+A2_CGC` | CNPJ/CPF | `SA20103` | não |
| 4 | `A2_FILIAL+A2_ID_FBFN` | Identificação (integr. financeira) | `SA20104` | não |
| 5 | `A2_FILIAL+A2_CONREG+A2_SIGLCR` | Nº Conselho Regional + sigla | `SA20105` | não |
| 6 | `A2_FILIAL+A2_VINCULO` | Vínculo (F3=CC1TIP) | `SA20106` | não |
| 7 | `A2_FILIAL+A2_NUMRA` | Matrícula funcionário | `SA20107` | não |
| 8 | `A2_FILIAL+A2_CODADM` | Cód. administrador | `SA20108` | não |
| 9 | `A2_FILIAL+A2_IDHIST` | ID histórico | `SA20109` | não |
| A | `A2_FILIAL+A2_CONTA` | Conta contábil | `SA2010A` | não |
| B | `A2_FILIAL+A2_LOJA` | Loja (PROPRI=U — índice criado pelo cliente) | `SA2010B` | não |
| — | — | PK técnica | `SA2010_PK (R_E_C_N_O_)` | **sim (PK)** |
| — | `A2_FILIAL+A2_COD+A2_LOJA+R_E_C_D_E_L_` | unicidade física de negócio | `SA2010_UNQ` | **sim** |
| — | `A2_COD+A2_LOJA+A2_NOME` | busca (X2 key de consulta) | `SA2010_A01` | não |
| — | `S_T_A_M_P_` | stamp CDC | `SA2010_ST`, `SA2010_STAMP` | não |

# 7. SA2010 Relations

## 7.1 SA2 como filho (41 relações SX9 — dependências de lookup da SA2)

| Dom | Tabela alvo | Expressão alvo | Significado |
|---|---|---|---|
| ACJ | ACJ010 Códigos DDI | `ACJ_DDI` | A2_DDI |
| CC1 | CC1 Tipo Participante | `CC1_CODIGO` | A2_VINCULO |
| CC2 | CC2010 Municípios IBGE | `CC2_EST+CC2_CODMUN` | A2_EST+A2_COD_MUN |
| CCH | CCH010 Países BACEN | `CCH_CODIGO` | A2_CODPAIS |
| CT1 | Plano de Contas | `CT1_CONTA` | A2_CONTA |
| N12 | — | `N12_CGC` | vínculo CGC (contexto fiscal) |
| SA1 | SA1010 Clientes | `A1_COD+A1_LOJA`, `A1_COD` | A2_CLIENTE+A2_LOJCLI |
| SA2 | SA2 (auto-referência) | `A2_COD+A2_LOJA` | favorecido/grupo (A2_CODFAV+A2_LOJFAV) |
| SA4 | SA4010 Transportadoras | `A4_COD` | A2_TRANSP |
| SA6 | SA6010 Bancos | `A6_COD`, `A6_COD+A6_AGENCIA`, `A6_COD+A6_AGENCIA+A6_NUMCON` | dados bancários |
| SAE | Administradores | `AE_COD` | A2_CODADM |
| SE4 | SE4010 Condições Pagto | `E4_CODIGO` | A2_COND |
| SED | SED010 Naturezas | `ED_CODIGO` | A2_NATUREZ |
| SRA | SRA010 Funcionários | `RA_MAT` | A2_NUMRA |
| SX5 | SX5010 Genéricas (17 rels) | `X5_TABELA+X5_CHAVE` | UF '12', grupo 'Y7', forma pgto '58', segmento 'T3', etc. |
| SYA | SYA010 Países | `YA_CODGI` ×3 | A2_PAIS, A2_REPPAIS, A2_PAISEX |
| SYR | Origem | `YR_ORIGEM` ×3 | A2_ORIG_1/2/3 |
| VAM | IBGE | `VAM_IBGE` | A2_IBGE |

## 7.2 SA2 como dominante (607 relações SX9)

A totalidade é o mapa referencial padrão TOTVS (módulos Compras, Financeiro, Fiscal, TMS, EIC, Jurídico, Qualidade, Ativo, etc.). Destas, **existem fisicamente e contêm dados** na DELPI apenas as listadas em §12/§19/§20. Relações de módulos sem dados foram contabilizadas mas não detalhadas campo a campo — `RELATIONSHIP_INVENTORY` = completo no nível de tabela, parcial no nível de módulos verticais sem uso.

# 8. Mandatory Fields Analysis

Classificação por campo (evidência entre parênteses):

**REQUIRED_BY_DICTIONARY (chave única X2_UNICO):**
- `A2_FILIAL` — integra a chave única; na prática sempre vazio (tabela compartilhada). A ponte deve enviar `'  '` (branco) ou omitir → rotina preenche com a filial corrente/branco.
- `A2_COD` — chave; possui DEFAULT `GETSXENUM("SA2")` (emp 01/05) → **SYSTEM_GENERATED quando a ponte delega à rotina**; nas empresas 03/04 não há default.
- `A2_LOJA` — chave; sem default de dicionário; **deve ser enviado** (convenção observada `'01'`).

**REQUIRED_BY_VALIDATION (VALID rejeita vazio ou exige existência):**
- `A2_CGC` — `Vazio() .Or. (CGC() .And. A020CGC() .And. A020VldUCod())`: tecnicamente admite vazio, mas se informado precisa de dígito verificador válido e passa por verificação de duplicidade (`A020CGC`/`A020VldUCod`). 159 registros legados estão sem CGC — **não usar CNPJ como dedupe único**.
- `A2_CIVIL` — `naovazio()` quando `A2_TIPO='F'` (WHEN) → CONDITIONAL.
- Campos com `ExistCpo(...)` **sem** `Vazio()` antes — quando informados devem existir na tabela lookup: `A2_SATIV1` (SX5 'T3'), `A2_CONREG`+`A2_SIGLCR` (BA4 — tabela inexistente fisicamente!), `A2_EST` (SX5 '12'), `A2_COD_MUN` (CC2), `A2_CODPAIS` (CCH), `A2_NATUREZ` (SED), `A2_CONTA` (CT1 via `Ctb105Cta()`), `A2_CLIENTE`/`A2_LOJCLI` (SA1), `A2_CODADM` (SAE).

**REQUIRED_BY_PROCESS (não marcado no dicionário, mas obrigatório na prática — evidência: preenchimento ~100% + índices de busca + rotina MATA020):**
- `A2_NOME` (100%), `A2_NREDUZ` (100%), `A2_TIPO` (99,9% — J/F/X), `A2_EST` (100%), `A2_MUN` (100%), `A2_END` (100%), `A2_BAIRRO` (97,6%), `A2_CEP` (94,6%), `A2_COD_MUN` (99,8%), `A2_CODPAIS` (100%), `A2_CONTA` (99,9%), `A2_NATUREZ` (99,9%).
- Observação: fill-rate ≠ obrigatoriedade formal. Classificação `REQUIRED_BY_PROCESS` com confiança MÉDIA — a regra de tela da MATA020 (MVC, pasta Cadastro) não é introspectável via SQL. Campos marcados `OBRIG1` no bitmap X3_OBRIGAT pos.1: `A2_TEL, A2_CONTATO, A2_NATUREZ, A2_COD_MUN, A2_CODPAIS, A2_CONTA, A2_EMAIL, A2_FORMPAG, A2_YROHS`. Fill <100% em TEL/CONTATO/EMAIL prova que **não são bloqueantes** no create atual → tratar como CONDITIONAL até confirmação da rotina (ver §39/§40).

**DEFAULTED (X3_RELACAO — defaults de dicionário, emp. 01):**
- `A2_COD` `GETSXENUM("SA2")` · `A2_MSBLQL` `"2"` (não bloqueado) · `A2_PLFIL` `"N"` · `A2_RECCSLL/RECCOFI/RECPIS` `"1"` · `A2_TIPO` derivado de `A2_CGC` (F se <14 dígitos, J se 14) · `A2_VINCULA` `"1"` · `A2_ID_REPR` `'2'` · `A2_B2B` `"2"` · `A2_PLCRRES` `"N"` · `A2_CONTPRE` `"1"` · `A2_REGESIM` `"2"` · `A2_MINIRF` `"2"` · `A2_TIPCTA` `"1"` · `A2_IMPIP` `"2"` · `A2_MJURIDI` `"2"` · `A2_CONFFIS` `'0'` · `A2_RETISI` `"2"` · `A2_INOVAUT` `"2"` · `A2_INDRUR` `"0"` · `A2_PAGGFE` `"2"` · `A2_FORNEMA` `"2"` · `A2_MINPUB` `"2"` · `A2_MOTNIF` `"1"` · `A2_DEDBSPC` `'1'` · `A2_CPRB` `"2"` · `A2_DTINIR`/`A2_DTFIMR` `CTOD('//')` (vazio) · `A2_DTVAL` `A100ReDV()` · `A2_NOMFAV` `A020NomFav()` (virtual) · `A2_PAISDES` `E_Field("A2_PAIS","YA_DESCR")` (virtual) · `A2_DTPAWB` `Tabela("MF",...)` (virtual).

**OPTIONAL (VALID começa com `Vazio() .Or.` ou sem VALID):** demais campos — incluindo todos os dados bancários (A2_BANCO/AGENCIA/DVAGE/NUMCON/DVCTA/SWIFT/TIPCTA), fiscais avançados, representante, exterior, RNTRC etc.

**SYSTEM_GENERATED / DO-NOT-SEND:** `A2_FILIAL` (conforme contexto de empresa/filial da ponte), virtuais (`A2_DTPAWB`, `A2_NOMFAV`, `A2_PAISDES`), `D_E_L_E_T_`, `R_E_C_N_O_`, `R_E_C_D_E_L_`, `S_T_A_M_P_`, `I_N_S_D_T_`, acumuladores de estatística mantidos por gatilhos/rotinas (`A2_LC, A2_MATR, A2_MCOMPRA, A2_METR, A2_MSALDO, A2_NROCOM, A2_PRICOM, A2_SALDUP, A2_SALDUPM, A2_ULTCOM, A2_DESVIO, A2_MNOTA, A2_DATBLO`).

**UNKNOWN (não determinável por metadata/dados):** obrigatoriedade efetiva de campos `OBRIG1` no create (TEL/CONTATO/EMAIL/FORMPAG/YROHS); validações dentro de funções não introspectáveis (`A020CGC`, `A020VldUCod`, `Ctb105Cta`, `A060Valid`, `GCP200VldF` etc.).

# 9. Validation Rules (cadeia campo → lookup)

| Campo SA2 | Validação (X3_VALID) | Lookup | Condição |
|---|---|---|---|
| A2_COD | `IIF(Empty(A2_LOJA),.T.,ExistChav("SA2",cod+loja,"EXISTFOR")) .And. A020CarEsp()` | unicidade SA2 | sempre |
| A2_LOJA | `existchav("SA2",cod+loja,"EXISTFOR") .And. A020CarEsp()` | unicidade SA2 | sempre |
| A2_CGC | `Vazio() .Or. IIF(A2_TIPO='X',.T.,CGC().And.A020CGC().And.A020VldUCod())` | dígito + dedup CGC | se informado |
| A2_INSCR | `IE(A2_INSCR,A2_EST) .And. A020VldUCod()` | IE por UF | se informado |
| A2_EST | `ExistCpo("SX5","12"+EST)` | SX5 tab.12 (UF) | sempre |
| A2_COD_MUN | `ExistCpo("CC2", EST+COD_MUN)` | CC2 IBGE | depende de A2_EST |
| A2_CODPAIS | `ExistCpo("CCH")` | CCH BACEN | sempre |
| A2_PAIS | `Vazio() .Or. ExistCpo("SYA")` | SYA | se informado |
| A2_COND | `Vazio() .Or. ExistCpo("SE4")` | SE4 | se informado |
| A2_NATUREZ | `FinVldNat(.T.,,2) .And. Vazio() .Or. ExistCpo("SED")` | SED | se informado |
| A2_BANCO | (F3=SA6; SX9 tripla `A6_COD+A6_AGENCIA+A6_NUMCON`) | SA6 | conjunto banco+ag+conta |
| A2_TRANSP | `Vazio() .Or. ExistCpo("SA4")` | SA4 | se informado |
| A2_CONTA | `Vazio() .Or. Ctb105Cta()` | CT1 | se informado |
| A2_GRUPO | `Vazio() .Or. ExistCpo("SX5","Y7"+GRUPO)` | SX5 'Y7' | se informado (0% preenchido; grupos vivem em SAD) |
| A2_FORMPAG | `Vazio() .Or. ExistCpo("SX5","58"+FORMPAG)` | SX5 '58' | se informado |
| A2_SATIV1 | `ExistCpo("SX5","T3"+SATIV1)` | SX5 'T3' segmento | se informado |
| A2_TIPO | `Pertence("FJX")` | enum F/J/X | sempre |
| A2_MSBLQL | `Pertence("12")` | 1=Bloqueado/2=Não | default "2" |
| A2_CIVIL | `naovazio()` | enum 1-5 | WHEN `A2_TIPO='F'` |
| A2_CBO | — | — | WHEN `A2_TIPO $ 'F,X'` |
| A2_CNAE | — | — | WHEN `A2_TIPO $ 'J,X'` |
| A2_CLIENTE / A2_LOJCLI | `ExistCpo("SA1", ...)` | SA1 | par (cliente+loja) |
| A2_NUMRA | `Vazio() .Or. (ExistCpo("SRA") .And. A020NUMRA())` | SRA | fornecedor-funcionário |
| A2_CODFAV/A2_LOJFAV | F3=FOR (auto-ref SA2) | SA2 | favorecido divergente |
| A2_CONREG/A2_SIGLCR | `ExistChav("BA4",SIGLCR+CONREG,"PLASOL")` | **BA4 — tabela inexistente fisicamente** | ⚠ gap |
| A2_ZTABPRC | F3=AIA | AIA (tabela preço forn.) | DELPI custom |
| A2_CATEFD | F3=S049BR | eSocial categoria | se informado |
| A2_IBGE | F3=AM1 | AM1 | se informado |
| A2_DDI | `IIF(!EMPTY(DDI),ExistCpo("ACJ"),.T.)` | ACJ | se informado |
| A2_TPESSOA | CBOX `CI/PF/OS` | enum | opcional (0,08% preenchido) |

# 10. Supplier Identity and Keys

| Pergunta | Resposta | Evidência |
|---|---|---|
| Chave técnica | `R_E_C_N_O_` (PK física) | sys.indexes |
| Chave de negócio | `A2_COD` + `A2_LOJA` (+ `A2_FILIAL` em branco na base compartilhada) | X2_UNICO + `SA2010_UNQ` físico |
| Código sozinho identifica? | **Não** — 143 códigos com múltiplas lojas | profiling |
| Código+loja identifica? | **Sim** — 0 duplicados `(COD,LOJA)`; índice único físico garante | profiling + sys.indexes |
| Filial participa? | Da chave única sim, mas 100% dos registros têm `A2_FILIAL=''` (compartilhada) | profiling |
| CNPJ/CPF é chave? | Não — índice não-único; 32 valores duplicados; 159 vazios | SIX + profiling |
| Mesmo documento em múltiplos registros? | Sim — casos de mesmo CGC em CODs diferentes (ex.: 1 CGC aparecendo com 2 códigos distintos — valor mascarado neste relatório) | profiling |
| Como localizar para UPDATE | `WHERE A2_COD=@cod AND A2_LOJA=@loja AND D_E_L_E_T_<>'*'` | — |

# 11. Code / Store Generation

| Item | Evidência | Status |
|---|---|---|
| Quem gera `A2_COD` | Default de dicionário `GETSXENUM("SA2")` (empresas 01 e 05) | PROVEN (metadata) |
| Empresas 03/04 | Sem default — entrada manual na MATA020 | PROVEN (SX3 diff) |
| Formato do sequencial | numérico 6 dígitos zero-padded; maior atual `003929`; 3.623/3.644 numéricos | PROVEN (dados) |
| Códigos manuais | 21 ativos não-numéricos (VIAGEM, VIAGF2/3, FISCO, INPS, MUNIC, UNIAO, CONSUM, CONFRA, ESTADO, DPRF...) | PROVEN (dados) |
| Onde fica a sequência | Tabela `SXE*` **inexistente** nas bases acessíveis (DELPI, DELPI_TST01, DELPI_TST_WS; TSS sem permissão) | TO_INVENTORY — mecanismo interno do appserver |
| `A2_LOJA` default | Inexistente no dicionário; `'01'` é convenção dominante (3.266/3.644) | PROVEN |
| Retorno pós-CREATE | sem evidência de contrato — decisão da ponte | UNKNOWN → §39 |

# 12. Related Tables Inventory

Materialidade medida por dados reais (empresa 01). "Dict-only" = existe no SX3/SX2 mas sem tabela física.

| Tabela física | Alias | Descrição | Papel | Linhas | Para CREATE? |
|---|---|---|---|---|---|
| SA2010 | SA2 | Fornecedores | MASTER | 3.663 | alvo |
| SA5010 | SA5 | Amarração Produto × Fornecedor | PRODUCT_RELATION | 40.671 | não — chamada separada |
| SAD010 | SAD | Amarração Grupo × Fornecedor | RELATION | 5.512 | opcional pós-create |
| AIA010/AIB010 | AIA/AIB | Tabela de Preços do Fornecedor / itens | PURCHASE | 329 / 8.616 | opcional |
| AIC010 | AIC | Tolerância na Entrada Material | CONFIGURATION | 636 | opcional |
| DKI010 | DKI | Contatos × Fornecedores | CONTACT | 0 | não usada (contato fica na SA2) |
| D30010 | D30 | Complemento de Fornecedor (SIMP/import.) | FISCAL | 0 | não usada |
| DD1010 | DD1 | Docs Exigidos × Fornecedor | CONFIGURATION | 0 | não usada |
| FV6010 | FV6 | Dados Pagamento Favorecidos | FINANCIAL | 0 | não usada |
| G4R010 | G4R | Complemento de Fornecedores (Turismo) | CONFIGURATION | 0 | não usada |
| AI5010 | AI5 | "Fornecedores" (módulo vertical, não é SA2) | — | 0 | não confundir |
| **Lookups** | | | | | |
| SA6010 | SA6 | Bancos | LOOKUP (A2_BANCO) | 26 | validar se enviado |
| SE4010 | SE4 | Condições de Pagamento | LOOKUP (A2_COND) | 239 | validar se enviado |
| SED010 | SED | Naturezas | LOOKUP (A2_NATUREZ) | 174 | validar se enviado |
| SA4010 | SA4 | Transportadoras | LOOKUP (A2_TRANSP) | 163 | validar se enviado |
| SYA010 | SYA | Países | LOOKUP (A2_PAIS) | 253 | validar se enviado |
| CC2010 | CC2 | Municípios IBGE | LOOKUP (A2_EST+A2_COD_MUN) | 5.572 | validar se enviado |
| CCH010 | CCH | Países BACEN | LOOKUP (A2_CODPAIS) | 240 | validar se enviado |
| SX5010 | SX5 | Tabelas genéricas | LOOKUP (12/Y7/58/T3/48/83/MF...) | — | validar se enviado |
| ACJ010 | ACJ | Códigos DDI | LOOKUP (A2_DDI) | 4 | validar se enviado |
| CT1 | CT1 | Plano de Contas | LOOKUP (A2_CONTA) | — | validar se enviado |
| SA1010 | SA1 | Clientes | LOOKUP (A2_CLIENTE+A2_LOJCLI) | — | validar se enviado |
| SRA010 | SRA | Funcionários | LOOKUP (A2_NUMRA) | — | validar se enviado |
| SA3010 | SA3 | Vendedores | LOOKUP | — | opcional |
| SA7010 | SA7 | Amarração Produto × **Cliente** | — | — | NÃO é de fornecedor |
| Dict-only (sem físico) | D2C, COP, DD5, FTG, BA4, G4S, SS3, SU6* | vários | — | — | ignorar |

*SU6010 existe ("Itens das Listas de Contatos") mas não tem chave de fornecedor direta no recorte analisado.

## 12.x — Schemas completos das tabelas materiais

Schemas extraídos de SX3010 (empresa 01). Tabelas com **0 linhas** estão documentadas para referência mas **não participam** do fluxo atual de cadastro na DELPI.

### SA6 — Bancos (lookup de A2_BANCO)
Chave: `A6_COD+A6_AGENCIA+A6_NUMCON` (SX9 rels 021/083 — a trinca banco+agência+conta é validada em conjunto). 26 bancos cadastrados. Campos PIX existem na SA6 (`A6_CFGPIX`, `A6_DIASEXP`, `A6_PIXMULT`) mas referem-se à configuração PIX **da empresa** (recebimento), não do fornecedor.

### DKI010 — Contatos × Fornecedores (0 linhas — disponível, não usada)
Permite **N contatos por fornecedor** (chave `DKI_FILIAL+DKI_FORNEC+DKI_LOJA+DKI_ITEM`):

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `DKI_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `DKI_FORNEC` | C | 6 | 0 | Cod. Fornece | V: R: F3: |
| 03 | `DKI_LOJA` | C | 2 | 0 | Loja | V: R: F3: |
| 04 | `DKI_ITEM` | C | 4 | 0 | Item | V: R: F3: |
| 05 | `DKI_NOME` | C | 30 | 0 | Nome | V: R: F3: |
| 06 | `DKI_DEPART` | C | 30 | 0 | Departamento | V: R: F3: |
| 07 | `DKI_CARGO` | C | 20 | 0 | Cargo | V: R: F3: |
| 08 | `DKI_DDD` | C | 3 | 0 | DDD | V: R: F3: |
| 09 | `DKI_TEL` | C | 15 | 0 | Telefone | V: R: F3: |
| 10 | `DKI_RAMAL` | C | 4 | 0 | Ramal | V: R: F3: |
| 11 | `DKI_CEL` | C | 15 | 0 | Celular | V: R: F3: |
| 12 | `DKI_EMAIL` | C | 40 | 0 | E-mail | V: R: F3: |
| 13 | `DKI_OBS` | M | 10 | 0 | Observa��o | V: R: F3: |
| 14 | `DKI_WFNFC` | C | 1 | 0 | Env. WF NFC? | V:Pertence("12") R:"2" F3: |

### D30010 — Complemento de Fornecedor — SIMP/importação (0 linhas)

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `D30_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `D30_CODFOR` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->D30_CODFOR) R: F3:FOR |
| 03 | `D30_LOJFOR` | C | 2 | 0 | Loja | V:EXISTCPO("SA2",M->D30_CODFOR+M->D30_LOJFOR) .Or. Vazio() R: F3: |
| 04 | `D30_ATVSIM` | C | 6 | 0 | Atv Eco SIMP | V:ExistCpo("SX5","HB"+M->D30_ATVSIM) .OR. Vazio(M->D30_ATVSIM) R: F3:HB |
| 05 | `D30_CODSIM` | C | 10 | 0 | Cod. ARI | V:ExistCpo("D33", M->D30_CODSIM) .OR. Vazio (M->D30_CODSIM) R: F3:D33 |
| 06 | `D30_INSTSI` | C | 7 | 0 | Cd Inst SIMP | V:ExistCpo("D36", M->D30_INSTSI) .OR. Vazio (M->D30_INSTSI) R: F3:D36 |
| 07 | `D30_MUNSIM` | C | 6 | 0 | Cod.Mun.SIMP | V:ExistCpo("CC2", M->D30_MUNSIM,5) .OR. Vazio(M->D30_MUNSIM) R: F3:CC2ANP |
| 08 | `D30_PAISIM` | C | 6 | 0 | Cd Pais SIMP | V:ExistCpo("SX5", "HC"+M->D30_PAISIM) .OR. Vazio(M->D30_PAISIM R: F3:HC |
| 09 | `D30_CLTRIB` | C | 3 | 0 | Clas. Trib | V:ExistCpo("SX5","HH"+M->D30_CLTRIB) R: F3: |

### DD1010 — Documentos Exigidos × Fornecedor (0 linhas)

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `DD1_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `DD1_CODFOR` | C | 6 | 0 | Fornecedor | V:ExistCpo('SA2',M->DD1_CODFOR) .And. ExistChav('DD1',M->DD1_C R: F3:FOR |
| 03 | `DD1_LOJFOR` | C | 2 | 0 | Loja | V:ExistCpo('SA2',M->(DD1_CODFOR+DD1_LOJFOR)) .And. ExistChav(' R: F3: |
| 04 | `DD1_NOMFOR` | C | 50 | 0 | Nome Fornec. | V: R:IF(!INCLUI,POSICIONE('SA2',1,xFilial('SA F3: |
| 05 | `DD1_PESSOA` | C | 1 | 0 | Fisica/Jurid | V: R:IF(!INCLUI,POSICIONE('SA2',1,xFilial('SA F3: |
| 06 | `DD1_DTCALC` | D | 8 | 0 | Dt. p/ Calc. | V:TMSAD20Vld() R: F3: |
| 07 | `DD1_DIATRB` | N | 3 | 0 | Trabalhados | V:TMSAD20Vld() R: F3: |
| 08 | `DD1_DTAAFA` | D | 8 | 0 | Dt.Afastam. | V: R: F3: |
| 09 | `DD1_DIAAFA` | N | 3 | 0 | Afastados | V:TMSAD20Vld() R: F3: |
| 10 | `DD1_DTARET` | D | 8 | 0 | Dt. Retorno | V: R: F3: |
| 11 | `DD1_NUMLIB` | N | 2 | 0 | Num. Liber. | V: R: F3: |
| 12 | `DD1_CTRLIB` | C | 1 | 0 | Controla lib | V: R: F3: |
| 13 | `DD1_STATUS` | C | 1 | 0 | Status | V: R:"1" F3: |

### AIA010 / AIB010 — Tabela de Preços do Fornecedor + itens (329 / 8.616 linhas)
`AIA`: `AIA_FILIAL+AIA_CODFOR+AIA_LOJFOR+AIA_CODTAB` — cabeçalho; valida fornecedor via `ExistCpo("SA2", CODFOR+LOJFOR)`. `AIB`: itens com produto (`ExistCpo("SB1")`), preço, faixas, moeda. Referenciada por `A2_ZTABPRC` (campo DELPI) e `AD_CODTAB` (SAD).

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `AIA_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AIA_CODFOR` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->AIA_CODFOR+AllTrim(M->AIA_LOJFOR)).And.Com R: F3:FOR |
| 03 | `AIA_LOJFOR` | C | 2 | 0 | Loja Fornec. | V:ExistCpo("SA2",M->AIA_CODFOR+M->AIA_LOJFOR).And.Com010Pk() R: F3: |
| 04 | `AIA_NOMFOR` | C | 50 | 0 | Nome | V:.F. R:IIF(!INCLUI,Posicione("SA2",1,xFilial("S F3: |
| 05 | `AIA_CODTAB` | C | 3 | 0 | Tab.Preco | V:ExistChav("AIA",M->AIA_CODFOR+M->AIA_LOJFOR+M->AIA_CODTAB).A R: F3: |
| 06 | `AIA_DESCRI` | C | 30 | 0 | Descric�o | V:Texto() R: F3: |
| 07 | `AIA_DATDE` | D | 8 | 0 | Dt.Vld.Ini. | V:Com010Data() R: F3: |
| 08 | `AIA_DATATE` | D | 8 | 0 | Dt.Vld.Final | V:Com010Data() R: F3: |
| 09 | `AIA_CONDPG` | C | 3 | 0 | Cond.Pagto | V:Vazio().Or.ExistCpo("SE4") R: F3:SE4 |
| 01 | `AIB_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AIB_CODFOR` | C | 6 | 0 | Fornecedor | V: R: F3: |
| 03 | `AIB_LOJFOR` | C | 2 | 0 | Loja Fornec. | V: R: F3: |
| 04 | `AIB_CODTAB` | C | 3 | 0 | Tabela Preco | V: R: F3: |
| 05 | `AIB_ITEM` | C | 4 | 0 | Item | V: R: F3: |
| 06 | `AIB_CODPRO` | C | 15 | 0 | Produto | V:ExistCpo("SB1") R: F3:SB1 |
| 07 | `AIB_DESCRI` | C | 120 | 0 | Descric�o | V:Texto() R:If(!INCLUI,Posicione("SB1",1,xFilial("SB F3: |
| 08 | `AIB_PRCCOM` | N | 14 | 7 | Preco Unit. | V:Positivo() R: F3: |
| 09 | `AIB_QTDLOT` | N | 14 | 3 | Faixa | V:Positivo() R:999999.99 F3: |
| 10 | `AIB_INDLOT` | C | 20 | 0 | Faixa | V: R: F3: |
| 11 | `AIB_MOEDA` | N | 2 | 0 | Moeda | V:M->AIB_MOEDA > 0 .And. M->AIB_MOEDA <= MoedFin() R:1 F3: |
| 12 | `AIB_DATVIG` | D | 8 | 0 | Vigencia | V: R:DATE() F3: |
| 13 | `AIB_FRETE` | N | 13 | 5 | Frete | V:Positivo() R: F3: |
| 14 | `AIB_CODPRF` | C | 15 | 0 | Cod.Prd.Forn | V:.f. R:If(!INCLUI,Posicione("SA5",1,xFilial("SA F3: |
| 15 | `AIB_ZDTINC` | D | 8 | 0 | Dt Inclusao | V: R:DATE() F3: |

### SAD010 — Amarração Grupo × Fornecedor (5.512 linhas — **em uso**)
Chave `AD_FILIAL+AD_FORNECE+AD_LOJA+AD_GRUPO`. Valida `ExistCpo("SA2")` + unicidade.

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `AD_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AD_FORNECE` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->AD_FORNECE) .And. ExistChav("SAD",M->AD_FO R: F3:FOR |
| 03 | `AD_LOJA` | C | 2 | 0 | Loja | V:ExistCpo("SA2",M->AD_FORNECE+M->AD_LOJA) .And. Existchav("SA R: F3: |
| 04 | `AD_NOMEFOR` | C | 50 | 0 | Nome | V: R: F3: |
| 05 | `AD_GRUPO` | C | 4 | 0 | Grupo | V:ExistChav("SAD",M->AD_FORNECE+M->AD_LOJA+M->AD_GRUPO) .And.  R: F3:SBM |
| 06 | `AD_NOMGRUP` | C | 120 | 0 | Descricao | V: R: F3: |
| 07 | `AD_CODTAB` | C | 3 | 0 | Tab. Pre�o | V:Vazio().OR.ExistCpo("AIA",M->AD_FORNECE+M->AD_LOJA+M->AD_COD R: F3:AIA |

### AIC010 — Tolerância na Entrada de Material (636 linhas)
Parâmetros de tolerância por fornecedor/produto no recebimento.

### CPW010/CPX010 — Grupo de Fornecedor + itens (Compras Públicas, 1 linha)

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `CPW_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `CPW_CODIGO` | C | 6 | 0 | Codigo | V:COM001VldF(a) .And. COM001VldI('CPW') R: F3:FOR |
| 03 | `CPW_LOJA` | C | 2 | 0 | Loja | V:COM001VldF(a) .And. COM001VldI('CPW') R: F3: |
| 04 | `CPW_NOME` | C | 50 | 0 | Nome | V: R:IF(INCLUI,'',Posicione("SA2",1,xFilial(" F3: |
| 01 | `CPX_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `CPX_CODIGO` | C | 6 | 0 | Codigo | V: R: F3: |
| 03 | `CPX_LOJA` | C | 2 | 0 | Loja | V:COM001VldF(a) .And. COM001VldI('CPX') R: F3: |
| 04 | `CPX_ITEM` | C | 3 | 0 | Item | V: R: F3: |
| 05 | `CPX_CODFOR` | C | 6 | 0 | Fornecedor | V:COM001VldF(a) .And. COM001VldI('CPX') R: F3:FOR |
| 06 | `CPX_LOJFOR` | C | 2 | 0 | Loja | V:COM001VldF(a) .And. COM001VldI('CPX') R: F3: |
| 07 | `CPX_NOME` | C | 50 | 0 | Nome Fornec. | V: R:IF(INCLUI,'',Posicione("SA2",1,xFilial(" F3: |

### FV6010 — Dados Pagamento Favorecidos (0 linhas — refere favorecido SA2 + CNPJ + valor)

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `FV6_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `FV6_ITEM` | C | 4 | 0 | Item | V: R: F3: |
| 03 | `FV6_FAVORE` | C | 6 | 0 | Favorecido | V:Vazio() .Or. ExistCpo("SA2") R: F3:FOR |
| 04 | `FV6_LOJA` | C | 2 | 0 | Loja | V:Vazio() .Or. ExistCpo("SA2",FWFldGet("FV6_FAVORE")+M->FV6_LO R: F3: |
| 05 | `FV6_NFAVOR` | C | 50 | 0 | Desc. Fav. | V: R:IIF(!INCLUI,Posicione("SA2",1,xFilial("S F3: |
| 06 | `FV6_TIPO` | C | 1 | 0 | Tipo | V:Pertence("123") R: F3: |
| 07 | `FV6_CGC` | C | 14 | 0 | CNPJ/CPF | V:Vazio() .Or. Cgc(M->FV6_CGC) R: F3: |
| 08 | `FV6_VLREAL` | N | 16 | 2 | Vlr. Realiz. | V: R: F3: |
| 09 | `FV6_CODPRO` | C | 6 | 0 | ID Processo | V: R: F3:FV0 |
| 10 | `FV6_VALOR` | N | 16 | 2 | Valor Pag. | V: R: F3: |

### G4R010 — Complemento de Fornecedores Turismo (0 linhas — módulo SIGATUR)

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `G4R_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `G4R_FORNEC` | C | 6 | 0 | C�d. Fornec. | V:Vazio() .Or. ExistCpo("SA2",M->G4R_FORNEC) R: F3:SA2A |
| 03 | `G4R_LOJA` | C | 2 | 0 | Loja | V:(Vazio() .Or. ExistCpo("SA2",M->G4R_FORNEC+M->G4R_LOJA)) .an R: F3: |
| 04 | `G4R_NOME` | C | 40 | 0 | Fornecedor | V: R:IF(!INCLUI,POSICIONE("SA2",1,XFILIAL("SA F3: |

### D2C — Contatos × Fornecedores (dict-only, sem tabela física — módulo ausente)

| # | Campo | Tipo | Tam | Dec | Título |
|---|---|---|---|---|---|
| 01 | `D2C_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `D2C_CODFOR` | C | 6 | 0 | C�digo | V: R: F3: |
| 03 | `D2C_LOJA` | C | 2 | 0 | Loja | V: R: F3: |
| 04 | `D2C_ITEM` | C | 4 | 0 | Item | V: R: F3: |
| 05 | `D2C_NOME` | C | 50 | 0 | Nome | V: R: F3: |
| 06 | `D2C_DDI` | C | 6 | 0 | DDI | V: R: F3:ACJ |
| 07 | `D2C_DDDTEL` | C | 3 | 0 | DDD Telefone | V: R: F3: |
| 08 | `D2C_TEL` | C | 40 | 0 | Telefone | V: R: F3: |
| 09 | `D2C_DDDCEL` | C | 3 | 0 | DDD Celular | V: R: F3: |
| 10 | `D2C_CEL` | C | 40 | 0 | Celular | V: R: F3: |
| 11 | `D2C_EMAIL` | C | 40 | 0 | E-mail | V: R: F3: |
| 12 | `D2C_UTCOT` | C | 1 | 0 | Utiliza Cot? | V: R: F3: |
| 13 | `D2C_DEPTO` | C | 40 | 0 | Departamento | V: R: F3: |

# 13. Product × Supplier Model — SA5 / SA5010

- **Descrição**: "Amarração Produto x Fornecedor"; rotina owner **MATA061** (Compras).
- **Chave única (X2_UNICO)**: `A5_FILIAL+A5_FORNECE+A5_LOJA+A5_PRODUTO+A5_FABR+A5_FALOJA+A5_REFGRD+A5_CODPRF`.
- **Fornecedor**: `A5_FORNECE` (6) + `A5_LOJA` (2) → valida SA2 (`A060VldCpo()`+`A060Valid()`, F3=FOR).
- **Produto**: `A5_PRODUTO` (15) → `ExistCpo("SB1")`.
- **Fabricante**: `A5_FABR`+`A5_FALOJA` → **também é fornecedor SA2** (F3=SA2).
- Part-number do fornecedor: `A5_CODPRF`; catálogo: `A5_CODPRCA`; barcode: `A5_CODBAR`; lead time: `A5_LEAD_T`; MOQ: `A5_LOTEMIN`; embalagem: `A5_LOTEMUL`; UM: `A5_UNID`→SAH; situação: `A5_SITU`→QEG; tabela preço: `A5_CODTAB`→AIA.
- Índices lógicos (SIX010): 15 índices (ver dump); físicos espelham + `SA5010_PK` + `SA5010_UNQ`.
- Uso DELPI: lida por `product_suppliers_repository.py` (api-delpi) — `A5_FORNECE, A5_LOJA, A5_CODPRF, A5_CODPRCA, A5_CODBAR, A5_LEAD_T`.

**Perguntas respondidas:**
- SA5 é criada automaticamente com SA2? **Não** — não há relação SX9 dizendo isso; são rotinas distintas (MATA020 × MATA061) e podem existir 3.6k fornecedores para 40k amarrações. **[PROVEN por ausência de vínculo de criação]**
- SA5 exige chamada separada? **Sim** — tabela/rotina própria. Se a ponte precisar amarrar produto, é operação distinta. **[PROVEN]**
- Pode existir fornecedor sem SA5? **Sim** — denominador: 3.644 fornecedores vs subconjunto com SA5. **[PROVEN]**
- Quando SA5 passa a ser necessária? Quando o fornecedor precisa ser vinculado a produto (compras/cotação). Momento exato no processo DELPI: **TO_INVENTORY**.

### SA5010 — schema completo (SX3010)

| # | Campo | Tipo | Tam | Dec | Título | Metadata |
|---|---|---|---|---|---|---|
| 01 | `A5_FILIAL` | C | 2 | 0 | Filial | V  |
| 02 | `A5_FORNECE` | C | 6 | 0 | Fornecedor | V F3=FOR  |
| 03 | `A5_LOJA` | C | 2 | 0 | Loja | V  |
| 04 | `A5_NOMEFOR` | C | 50 | 0 | Nome |  |
| 05 | `A5_NOMERED` | C | 20 | 0 | Nome Reduz. | DEF  |
| 06 | `A5_PRODUTO` | C | 15 | 0 | Produto | V F3=PRO WHEN  |
| 07 | `A5_NOMPROD` | C | 120 | 0 | Descricao | DEF  |
| 08 | `A5_CODPRF` | C | 50 | 0 | Cod.Prod.For |  |
| 09 | `A5_CODPRCA` | C | 18 | 0 | Cod.Prod.Cat |  |
| 10 | `A5_SITU` | C | 1 | 0 | Situacao | V DEF F3=QEG WHEN  |
| 11 | `A5_FABREV` | C | 1 | 0 | Fab/Rev/Perm | V DEF CBOX  |
| 12 | `A5_PE` | N | 5 | 0 | Entrega | V  |
| 13 | `A5_TIPE` | C | 1 | 0 | Tipo Prazo | V DEF CBOX  |
| 14 | `A5_EMBAL` | N | 5 | 0 | Qtde Embalag |  |
| 15 | `A5_FABRRED` | C | 20 | 0 | Nome Fabric. | DEF  |
| 16 | `A5_MOE_US` | C | 3 | 0 | Moeda Utiliz | V F3=SYF  |
| 17 | `A5_VLCOTUS` | N | 15 | 5 | Vlr.Cota�ao | V WHEN  |
| 18 | `A5_ULT_ENT` | D | 8 | 0 | Ult. Entrega |  |
| 19 | `A5_QT_COT` | N | 13 | 3 | Quant.Cotada | V  |
| 20 | `A5_ULT_FOB` | N | 15 | 5 | Vlr.Ult.FOB |  |
| 21 | `A5_PARTOPC` | C | 48 | 0 | Part-Num.Opc |  |
| 22 | `A5_UNID` | C | 2 | 0 | Unidade | V F3=SAH  |
| 23 | `A5_SKPLOT` | C | 2 | 0 | Skip-Lote | V F3=QSL WHEN  |
| 24 | `A5_RIAI` | C | 8 | 0 | RIAI |  |
| 25 | `A5_DTRIAI` | D | 8 | 0 | Data RIAI |  |
| 26 | `A5_VALRIAI` | D | 8 | 0 | Valid. RIAI |  |
| 27 | `A5_CHAVE` | C | 8 | 0 | Cod. Ligacao |  |
| 28 | `A5_ATUAL` | C | 1 | 0 | Atualiza | V CBOX  |
| 29 | `A5_INCOTER` | C | 8 | 0 | Incoterm | V F3=SYJ  |
| 30 | `A5_TR_COST` | N | 15 | 5 | Transf. Cost | V  |
| 31 | `A5_CODGRP` | C | 4 | 0 | Grupo | V DEF F3=SBM WHEN  |
| 32 | `A5_CODITE` | C | 27 | 0 | Cod. Produto | V DEF F3=B00 WHEN  |
| 33 | `A5_CODBAR` | C | 15 | 0 | Cod.Barras |  |
| 34 | `A5_TIPOCOT` | C | 1 | 0 | Tipo Cotacao | V CBOX  |
| 35 | `A5_STATUS` | C | 1 | 0 | Status | V  |
| 36 | `A5_SKIPLOT` | N | 4 | 0 | Contr. Lote | V  |
| 37 | `A5_DTCOM02` | D | 8 | 0 | 2a. Data |  |
| 38 | `A5_DTCOM03` | D | 8 | 0 | 3a. Data |  |
| 39 | `A5_DTCOM04` | D | 8 | 0 | 4a. Data |  |
| 40 | `A5_DTCOM05` | D | 8 | 0 | 5a. Data |  |
| 41 | `A5_DTCOM06` | D | 8 | 0 | 6a. Data |  |
| 42 | `A5_DTCOM07` | D | 8 | 0 | 7a. Data |  |
| 43 | `A5_DTCOM08` | D | 8 | 0 | 8a. Data |  |
| 44 | `A5_DTCOM09` | D | 8 | 0 | 9a. Data |  |
| 45 | `A5_DTCOM10` | D | 8 | 0 | 10a. Data |  |
| 46 | `A5_DTCOM11` | D | 8 | 0 | 11a. Data |  |
| 47 | `A5_DTCOM12` | D | 8 | 0 | 12a. Data |  |
| 48 | `A5_ENTREGA` | N | 4 | 0 | Entregas |  |
| 49 | `A5_FABR` | C | 6 | 0 | Fabricante | V F3=SA2  |
| 50 | `A5_FALOJA` | C | 2 | 0 | Loja Fabric. | V WHEN  |
| 51 | `A5_QUANT01` | N | 12 | 2 | 1a. Quant. |  |
| 52 | `A5_QUANT02` | N | 12 | 2 | 2a. Quant. |  |
| 53 | `A5_QUANT03` | N | 12 | 2 | 3a. Quant. |  |
| 54 | `A5_QUANT04` | N | 12 | 2 | 4a. Quant. |  |
| 55 | `A5_QUANT05` | N | 12 | 2 | 5a. Quant. |  |
| 56 | `A5_QUANT06` | N | 12 | 2 | 6a. Quant. |  |
| 57 | `A5_QUANT07` | N | 12 | 2 | 7a. Quant. |  |
| 58 | `A5_QUANT08` | N | 12 | 2 | 8a. Quant. |  |
| 59 | `A5_QUANT09` | N | 12 | 2 | 9a. Quant. |  |
| 60 | `A5_QUANT10` | N | 12 | 2 | 10a. Quant. |  |
| 61 | `A5_QUANT11` | N | 12 | 2 | 11a. Quant. |  |
| 62 | `A5_QUANT12` | N | 12 | 2 | 12a. Quant. |  |
| 63 | `A5_PRECO01` | N | 16 | 2 | 1o. Preco |  |
| 64 | `A5_PRECO02` | N | 16 | 2 | 2o. Preco |  |
| 65 | `A5_PRECO03` | N | 16 | 2 | 3o. Preco |  |
| 66 | `A5_LEAD_T` | N | 5 | 0 | Lead Time | V  |
| 67 | `A5_PRECO04` | N | 16 | 2 | 4o. Preco |  |
| 68 | `A5_PRECO05` | N | 16 | 2 | 5o. Preco |  |
| 69 | `A5_TIPATU` | C | 1 | 0 | Tipo Atualiz | V DEF CBOX  |
| 70 | `A5_LOTEMIN` | N | 8 | 2 | MOQ | V  |
| 71 | `A5_LOTEMUL` | N | 8 | 2 | Embalagem | V  |
| 72 | `A5_PRECO06` | N | 16 | 2 | 6o. Preco |  |
| 73 | `A5_PRECO07` | N | 16 | 2 | 7o. Preco |  |
| 74 | `A5_MSBLQL` | C | 1 | 0 | Bloqueado? | DEF CBOX  |
| 75 | `A5_PRECO08` | N | 16 | 2 | 8o. Preco |  |
| 76 | `A5_PRECO09` | N | 16 | 2 | 9o. Preco |  |
| 77 | `A5_PRECO10` | N | 16 | 2 | 10o. Preco |  |
| 78 | `A5_PRECO11` | N | 16 | 2 | 11o. Preco |  |
| 79 | `A5_PRECO12` | N | 16 | 2 | 12o. Preco |  |
| 80 | `A5_PLAM1` | C | 2 | 0 | Pl. Amost. a | F3=Q5  |
| 81 | `A5_NIVEL1` | C | 2 | 0 | Nivel a | V CBOX  |
| 82 | `A5_NQA1` | C | 5 | 0 | NQA a | V F3=Q1  |
| 83 | `A5_PLAM2` | C | 2 | 0 | Pl. Amost. b | F3=Q5  |
| 84 | `A5_NIVEL2` | C | 2 | 0 | Nivel b | V CBOX  |
| 85 | `A5_NQA2` | C | 5 | 0 | NQA b | V F3=Q1  |
| 86 | `A5_COND01` | C | 3 | 0 | 1a. Cond. |  |
| 87 | `A5_COND02` | C | 3 | 0 | 2a. Cond. |  |
| 88 | `A5_COND03` | C | 3 | 0 | 3a. Cond. |  |
| 89 | `A5_COND04` | C | 3 | 0 | 4a. Cond. |  |
| 90 | `A5_COND05` | C | 3 | 0 | 5a. Cond. |  |
| 91 | `A5_TEMPLIM` | N | 2 | 0 | Tempo Limite | V DEF WHEN  |
| 92 | `A5_NOTA` | N | 1 | 0 | Nota |  |
| 93 | `A5_COND06` | C | 3 | 0 | 6a. Cond. |  |
| 94 | `A5_COND07` | C | 3 | 0 | 7a. Cond. |  |
| 95 | `A5_COND08` | C | 3 | 0 | 8a. Cond. |  |
| 96 | `A5_COND09` | C | 3 | 0 | 9a. Cond. |  |
| 97 | `A5_COND10` | C | 3 | 0 | 10a. Cond. |  |
| 98 | `A5_COND11` | C | 3 | 0 | 11a. Cond. |  |
| 99 | `A5_COND12` | C | 3 | 0 | 12a. Cond. |  |
| A0 | `A5_REFGRD` | C | 14 | 0 | Ref Grd Cfg | V F3=SB4 WHEN  |
| A1 | `A5_DESREF` | C | 30 | 0 | Desc. Ref Gr | DEF  |
| A2 | `A5_DTCOM01` | D | 8 | 0 | 1a. Data |  |
| A3 | `A5_TEMPTRA` | N | 3 | 0 | Tempo Transi | WHEN  |
| A4 | `A5_PESO` | N | 11 | 4 | Peso Liquido | V  |
| A5 | `A5_ENTSIT` | N | 2 | 0 | Num.Ent.Sit. |  |
| A6 | `A5_CCUSTO` | C | 9 | 0 | C.Custo | V F3=CTT  |
| A7 | `A5_DIASSIT` | N | 4 | 0 | Entradas Sit |  |
| A8 | `A5_TESBP` | C | 3 | 0 | TE p/ Bonif. | V F3=SF4  |
| A9 | `A5_CODFIS` | C | 15 | 0 | Cod.Fis.Forn | V  |
| AA | `A5_CONV` | N | 16 | 4 | Conv Forn NF |  |
| AB | `A5_TPCONV` | C | 1 | 0 | Tipo Convers | CBOX  |

# 14. Banking Model

Dados bancários do fornecedor moram **na própria SA2** (conta única — não há tabela filha de contas bancárias de fornecedor em uso):

| Campo | Conteúdo | Lookup | Fill (emp01) |
|---|---|---|---|
| `A2_BANCO` C(3) | código do banco | SA6 (`A6_COD`) | 44/3.644 |
| `A2_AGENCIA` C(5) | agência | SA6 trinca | 80 |
| `A2_DVAGE` C(1) | DV agência CNAB | — | — |
| `A2_NUMCON` C(10) | conta corrente | SA6 trinca | 82 |
| `A2_DVCTA` C(2) | DV conta CNAB | — | — |
| `A2_TIPCTA` C(1) | tipo conta (1=CC,2=Poupança) | CBOX | 2.619 |
| `A2_TPCONTA` C(1) | tipo conta (CBOX 1=CC/2=Poup.) | — | — |
| `A2_SWIFT` C(30) | SWIFT | — | — |
| `A2_CODFAV`+`A2_LOJFAV`+`A2_NOMFAV` | favorecido divergente | SA2 self | 0 |

PIX: **não existe chave PIX no cadastro** — PIX é dado de pagamento (F70/F71/F72) ou config de recebimento na SA6. Sensibilidade: dados bancários = **SENSITIVE** (não retornar valores; só metadados).

Múltiplas contas: **não suportado** no modelo usado na DELPI (FV6 tem 0 linhas; não é conta bancária, é favorecido por pagamento).

# 15. Contact Model

Contato principal **na SA2**: `A2_CONTATO`(15), `A2_CONTCOM`(15 contato comercial), `A2_TEL`(50), `A2_DDD`(3), `A2_DDI`(6→ACJ), `A2_FAX`(15), `A2_TELEX`(10), `A2_EMAIL`(50), `A2_HPAGE`(30), `A2_NOMRESP`(45)+`A2_CARGO`(40) — responsável. Bloco representante: `A2_REPRES`(52), `A2_REPCONT`, `A2_REPRTEL`, `A2_REPRFAX`, `A2_REPR_EM`, endereço do representante (`A2_REPR_EN/BAIR/MUN/EST/CEP/PAIS`), `A2_REPR_BA/AG/CO` (banco do representante), `A2_REPRCGC`.

Múltiplos contatos: DKI010 suporta (`DKI_FORNEC+DKI_LOJA+DKI_ITEM`) mas **0 linhas** — múltiplos contatos não são prática atual.

# 16. Address Model

| Campo | Conteúdo | Lookup/validação |
|---|---|---|
| `A2_END` C(40) | logradouro | A020CarEsp |
| `A2_NR_END` C(6) | número | — |
| `A2_ENDCOMP` C(21) / `A2_COMPLEM` C(50) | complemento | — |
| `A2_BAIRRO` C(20) | bairro | A020CarEsp |
| `A2_CEP` C(8) | CEP | — |
| `A2_MUN` C(25) | município (texto) | A020CarEsp |
| `A2_COD_MUN` C(5) | código IBGE município | `ExistCpo("CC2", EST+COD_MUN)` / F3=CC2SA2 |
| `A2_MUNSC` C(5) / `A2_CODSIAF` C(4) | cód. mun. SC / SIAF | — |
| `A2_IBGE` C(11) | código IBGE | F3=AM1 / SX9→VAM |
| `A2_EST` C(2) | UF | `ExistCpo("SX5","12"+EST)`; 'EX'=exterior |
| `A2_ESTADO` C(20) | nome do estado | — |
| `A2_PAIS` C(3) | país (SYA) | `ExistCpo("SYA")` — 127 preenchidos (estrangeiros) |
| `A2_CODPAIS` C(5) | país BACEN | `ExistCpo("CCH")` — `01058`=Brasil (3.576), domina |
| `A2_PAISDES` | descrição país | **virtual** (`E_Field`) |
| `A2_TPLOGR` C(3) | tipo logradouro | — |
| `A2_CX_POST` C(5) | caixa postal | — |
| Endereço exterior | `A2_LOGEX/NUMEX/COMPLR/BAIEX/POSEX/CIDEX/ESTEX`, `A2_PAISEX`→SYA | quando `A2_EST='EX'` (`A2_UFFIC` WHEN) |

# 17. Fiscal Model

| Campo | Conteúdo | Validação |
|---|---|---|
| `A2_CGC` C(14) | CNPJ/CPF | dígito `CGC()` + `A020CGC` (dedup) + `A020VldUCod` |
| `A2_PFISICA` C(18) | RG/cédula estrangeira | `A020VldUCod` |
| `A2_INSCR` C(18) | inscrição estadual | `IE(INSCR, EST)` por UF |
| `A2_INSCRM` C(18) | inscrição municipal | — |
| `A2_TIPO` C(1) | F/J/X (física/jurídica/outros) | `Pertence("FJX")`; default derivado do CGC |
| `A2_TPESSOA` C(2) | CI/PF/OS | CBOX |
| `A2_CONTRIB` C(1) | contribuinte | `Pertence('12')` |
| `A2_GRPTRIB` C(3) | grupo tributação | — |
| `A2_RECCSLL/RECCOFI/RECPIS/RECISS/RECINSS/RECFET/RECSEST/RECCIDE/RECFMD/RFACS/RFABOV/RFUNDES/RFASEMT/RIMAMT/INCULT/FOMEZER/CONTPRE/IRPROG/CALCIRF/CALCINP/DEDBSPC/CPRB/GROSSIR/MINIRF/CPFIRP` | flags de retenção/recolhimento | `Pertence("12")` ou `SN`; defaults "1"/"2" |
| `A2_SIMPNAC`, `A2_TPJ` (ME/EPP/MEI/coop), `A2_REGESIM`, `A2_REGPB`, `A2_RESPTRI` (SX5 '83'), `A2_TPCON`, `A2_CTARE`, `A2_TIPORUR`, `A2_INDRUR`, `A2_INDCP`, `A2_CPFRUR` | regime/enquadramento | diversos |
| `A2_CNAE` C(9) | CNAE | WHEN `TIPO$'J,X'` |
| `A2_CBO` C(7) | CBO | WHEN `TIPO$'F,X'` |
| `A2_CODNIT`/CEI/NIT C(11), `A2_CATEG` (SEFIP), `A2_NUMDEP`, `A2_DTNASC`, `A2_CIVIL` | dados PF/vínculo | — |
| `A2_NATUREZ` C(10) | natureza financeira | SED |
| `A2_CONFFIS` | conf. física/pré-nota | CBOX 0-3 |
| Exterior/fiscal internacional | `A2_NIFEX`, `A2_MOTNIF`, `A2_CGCEX`, `A2_NEMPR`, `A2_BREEX`, `A2_TPREX`, `A2_TRBEX`, `A2_UFFIC`, `A2_PAISEX`, `A2_PAISSUB`, `A2_PABCB` | — |
| `A2_SATIV1` C(6) | segmento atividade | SX5 'T3' (indústria/serviço) |
| `A2_CODMUN` C(5) | município ZF | F3=S1 |

**FIELD_EXISTS ≠ FIELD_REQUIRED_FOR_CREATE ≠ FIELD_REQUIRED_FOR_OPERATION** — a maioria é opcional no cadastro; exigências fiscais efetivas dependem do tipo de documento emitido depois (não do create).

# 18. Payment / Commercial Model

| Campo | Conteúdo | Lookup |
|---|---|---|
| `A2_COND` C(3) | condição de pagamento | SE4 |
| `A2_FORMPAG` C(2) | forma de pagamento | SX5 '58' (PIX=45/47, TED=41/43...) |
| `A2_NATUREZ` C(10) | natureza fin. | SED |
| `A2_CONTA` C(20) | conta contábil | CT1 |
| `A2_PLGRUPO` C(3) | classe fornecedor | F3=B9? (SX5) |
| `A2_GRUPO` C(3) | grupo | SX5 'Y7' — **não usado** (0 preenchido; grupos reais em SAD) |
| `A2_ZTABPRC` C(3) | tabela preço compra (DELPI) | AIA |
| `A2_TRANSP` C(6) | transportadora | SA4 |
| `A2_LC`, `A2_FATAVA`, `A2_DTAVA`, `A2_DTVAL`, `A2_RISCO`, `A2_STATUS` | crédito/homologação | — |
| `A2_FILDEB`/`A2_FILTRF` | filial débito/transferência | F3=DLB |
| `A2_CODADM` | administrador | SAE |
| `A2_ORIG_1/2/3` | origem | SYR |

# 19. Purchase Transaction References (consumidores — não fazem parte do CREATE)

| Tabela | Papel | Campo fornecedor | Campo loja |
|---|---|---|---|
| SC1010 | Solicitações de Compra (272k) | `C1_FORNECE` | `C1_LOJA` (+`C1_FABRLOJ`,`C1_LOJFABR`) |
| SC7010 | Pedidos de Compra / Aut. Entrega (196k) | `C7_FORNECE` | `C7_LOJA` (+`C7_LOJAEXP`,`C7_LOJFABR`) |
| SC8010 | Cotações (67k) | `C8_FORNECE`+`C8_FORNOME` | `C8_LOJA` |
| SCY010 | Histórico Pedidos Compras | `CY_FORNECE` | `CY_LOJA` |
| SCE | — | `CE_FORNECE` | `CE_LOJA` |
| SFJ | Sugestão de Compra | `FJ_FORNECE` | — |
| COP (dict-only) | Fornecedores×Produtos (licitação) | `COP_CODFOR` | `COP_LOJFOR` |

# 20. Inbound / Fiscal Transaction References

| Tabela | Papel | Campo fornecedor | Campo loja |
|---|---|---|---|
| SF1010 | Cabeçalho NF Entrada (105k) | `F1_FORNECE` | `F1_LOJA` (+`F1_LOJAENT`,`F1_LOJDEST`...) |
| SD1010 | Itens NF Entrada (281k) | `D1_FORNECE` | `D1_LOJA` |
| SF3/SFT | Livros fiscais / por item | `F3_*` | `F3_LOJA` etc. |
| SE2010 | Contas a Pagar (127k) | `E2_FORNECE` (+`E2_FORNISS`,`E2_FORNPAI`,`E2_FATLOJ`) | `E2_LOJA` |
| SE5 | Mov. Bancárias | `E5_FORNECE`(+`E5_FORNADT`) | `E5_LOJA` |
| SDS | Cabeçalho importação XML NFe | `DS_FORNEC` | `DS_LOJA` |

Estas tabelas apenas **consomem** SA2 — não são necessárias ao create/update do cadastro.

# 21. DELPI Customizations

| Item | Tipo | Detalhe | Status |
|---|---|---|---|
| `A2_YROHS` C(1) | campo usuário | "RoHS?" — CBOX; usado 2.459/3.644; `OBRIG1` no bitmap | DELPI_CUSTOMIZATION |
| `A2_YFGEN` C(1) | campo usuário | "For Generico" — 6 preenchidos | DELPI_CUSTOMIZATION |
| `A2_ZTABPRC` C(3) | campo usuário | "Tab Prc Comp" → F3=AIA (61 preenchidos) | DELPI_CUSTOMIZATION |
| índice `SA2010B` / `SA2010_A01` | índice usuário | PROPRI=U / extra físico `FILIAL+LOJA`, `COD+LOJA+NOME` | DELPI_CUSTOMIZATION |
| `SA2010_TTAT_LOG` + trigger STAMP | auditoria/CDC | estrutura TTS pronta, 0 registros | plataforma |
| Tabelas Z de fornecedor | — | **não existem** (SBC/SBX/SBZ são de outros domínios: perda OP, conjuntos, indicadores) | PROVEN |
| Empresas 03/04 | dicionário reduzido | sem `YROHS/YFGEN/PABCB/ECDTEX/ECSEQ/ECFLAG`; sem default GETSXENUM em A2_COD | PROVEN |

# 22. Relationship Matrix (material)

| source | campo | target | campo alvo | tipo | obrigatória | significado | evidência |
|---|---|---|---|---|---|---|---|
| SA2 | A2_COD+A2_LOJA | SA2 | — | identidade | sim | chave de negócio | SX2/X9/SIX/sys |
| SA2 | A2_EST | SX5 | tab '12' | N:1 | se UF BR | UF | X3 |
| SA2 | A2_EST+A2_COD_MUN | CC2 | EST+CODMUN | N:1 | se informado | município IBGE | X3/SX9 |
| SA2 | A2_CODPAIS | CCH | CODIGO | N:1 | se informado | país BACEN | X3/SX9 |
| SA2 | A2_PAIS | SYA | CODGI | N:1 | se informado | país | X3/SX9 |
| SA2 | A2_COND | SE4 | CODIGO | N:1 | se informado | cond. pagto | X3/SX9 |
| SA2 | A2_NATUREZ | SED | CODIGO | N:1 | se informado | natureza | X3/SX9 |
| SA2 | A2_BANCO(+AGE+CONTA) | SA6 | COD(+AGENCIA+NUMCON) | N:1 | trinca | banco | SX9/X3 |
| SA2 | A2_TRANSP | SA4 | COD | N:1 | se informado | transportadora | X3 |
| SA2 | A2_CONTA | CT1 | CONTA | N:1 | se informado | conta contábil | X3/SX9 |
| SA2 | A2_FORMPAG | SX5 | tab '58' | N:1 | se informado | forma pgto | X3 |
| SA2 | A2_GRUPO | SX5 | tab 'Y7' | N:1 | se informado | grupo (não usado) | X3 |
| SA2 | A2_SATIV1 | SX5 | tab 'T3' | N:1 | se informado | segmento | X3 |
| SA2 | A2_CODFAV+A2_LOJFAV | SA2 | COD+LOJA | N:1 self | se informado | favorecido | SX9 |
| SA2 | A2_CLIENTE+A2_LOJCLI | SA1 | COD+LOJA | N:1 | se informado | fornecedor=cliente | X3/SX9 |
| SA2 | A2_NUMRA | SRA | RA_MAT | N:1 | se informado | fornecedor=funcionário | X3/SX9 |
| SA2 | A2_CODADM | SAE | COD | N:1 | se informado | administrador | SX9 |
| SA2 | A2_DDI | ACJ | DDI | N:1 | se informado | DDI | X3/SX9 |
| SA2 | A2_ORIG_1/2/3 | SYR | ORIGEM | N:1 | se informado | origem | SX9 |
| SA2 | A2_SIGLCR+A2_CONREG | BA4 | — | N:1 | ⚠ tabela ausente | conselho | X3/SX9 |
| SA5 | A5_FORNECE+A5_LOJA | SA2 | COD+LOJA | N:1 | sim | produto×fornecedor | SX9/X3 |
| SA5 | A5_PRODUTO | SB1 | COD | N:1 | sim | produto | X3 |
| SA5 | A5_FABR+A5_FALOJA | SA2 | COD+LOJA | N:1 | opcional | fabricante é fornecedor | X3 |
| SA5 | A5_UNID | SAH | UNIDADE | N:1 | se informado | UM | X3 |
| SA5 | A5_REFGRD | SB4 | — | N:1 | se informado | ref. grade | X3 |
| SA5 | A5_SITU | QEG | — | N:1 | se informado | situação qualidade | X3 |
| SA5 | A5_CODTAB | AIA | CODFOR+LOJFOR+CODTAB | N:1 | se informado | tabela preço | X3 |
| SAD | AD_FORNECE+AD_LOJA | SA2 | COD+LOJA | N:1 | sim | grupo×fornecedor | SX9/X3 |
| AIA | AIA_CODFOR+AIA_LOJFOR | SA2 | COD+LOJA | N:1 | sim | tabela preço header | X3 |
| AIB | AIB_CODFOR+AIB_LOJFOR+AIB_CODTAB | AIA | — | N:1 | sim | itens | X3 |
| AIB | AIB_CODPRO | SB1 | COD | N:1 | sim | produto | X3 |
| DKI | DKI_FORNEC+DKI_LOJA | SA2 | COD+LOJA | N:1 | sim | contatos (não usada) | SX9/X3 |
| D30 | D30_CODFOR+D30_LOJFOR | SA2 | COD+LOJA | N:1 | sim | complemento (não usada) | SX9/X3 |
| DD1 | DD1_CODFOR+DD1_LOJFOR | SA2 | COD+LOJA | N:1 | sim | docs exigidos (não usada) | SX9/X3 |
| FV6 | FV6_FAVORE+FV6_LOJA | SA2 | COD+LOJA | N:1 | sim | favorecido pgto (não usada) | X3 |
| G4R | G4R_FORNEC+G4R_LOJA | SA2 | COD+LOJA | N:1 | sim | compl. turismo (não usada) | X3 |
| SC1/SC7/SC8/SD1/SF1/SE2/SE5/SF3/SFT/SCY/SDS/SCE/SFJ | *_FORNECE* | SA2 | COD+LOJA | N:1 | transacional | consumidores | SX9/SX3 |

# 23. Supplier Data Flow (reconstruído de evidências)

```text
CREATE (referência MATA020):
  entrada identidade fiscal (CGC/CPF)     → A2_CGC VALID: dígito + A020CGC dedup [PROVEN]
  resolver lookups                        → SX5/CC2/CCH/SE4/SED/SA6/CT1/SYA... [PROVEN]
  código                                  → GETSXENUM("SA2") (emp 01/05) ou manual [PROVEN/TO_INVENTORY]
  loja                                    → default operacional '01' [PROVEN convenção]
  gravar SA2010 (X2_UNICO + SA2010_UNQ)   → [PROVEN]
  defaults RELACAO preenchidos            → [PROVEN]
  SA5/auxiliares                          → NÃO criadas automaticamente [PROVEN]
  retorno identidade (COD+LOJA)           → contrato da ponte [UNKNOWN]

UPDATE (referência MATA020 alteração):
  localizar por COD+LOJA                  → [PROVEN]
  revalidar campos alterados (VALID)      → [PROVEN]
  regravar; S_T_A_M_P_ por trigger        → [PROVEN]
  tabelas filhas não sincronizadas        → SA5/SAD/etc. são manutenção separada [PROVEN]
```

# 24. CREATE Dependency Flow (matriz)

| Step | Tabela | Campo | Dependência | Deve existir antes | Criado durante | Status |
|---|---|---|---|---|---|---|
| 1 | SA2 | A2_COD | GETSXENUM('SA2') | numerador (appserver) | sim | TO_INVENTORY (local do numerador) |
| 2 | SA2 | A2_LOJA | convenção '01' | — | enviado | PROVEN |
| 3 | SX5 | — | UF `12` | sim | — | PROVEN |
| 4 | CC2 | — | município por UF | sim | — | PROVEN |
| 5 | CCH | — | país BACEN `01058` | sim | — | PROVEN |
| 6 | SE4 | — | cond. pagto | se enviado | — | PROVEN |
| 7 | SED | — | natureza | se enviado | — | PROVEN |
| 8 | SA6 | — | banco | se enviado | — | PROVEN |
| 9 | CT1 | — | conta contábil | se enviado | — | PROVEN |
| 10 | SYA | — | país | se enviado | — | PROVEN |
| 11 | SA1 | — | cliente | se enviado | — | PROVEN |
| 12 | SA2 | — | gravação | itens 1–11 | sim | PROVEN |
| 13 | SA5 | — | amarração produto | pós-create, chamada separada | não | PROVEN |
| 14 | SAD/AIA/AIC | — | grupos/preços/tolerância | pós-create, separado | não | PROVEN |

**Conclusão**: para `CREATE` mínimo não há tabela obrigatória a ser escrita além da SA2. Obrigatórias a **consultar/validar**: lookups conforme campos enviados.

# 25. UPDATE Dependency Flow

```text
IDENTITY (A2_COD+A2_LOJA)
→ LOAD SA2010 WHERE D_E_L_E_T_<>'*' (índice SA2010_UNQ)
→ VALIDATE mudanças (mesmas regras X3_VALID; A2_COD/A2_LOJA são chave — mudança de chave é operação especial)
→ lookups conforme campos alterados
→ UPDATE SA2010 (S_T_A_M_P_ atualizado por trigger)
→ nenhuma tabela filha é escrita pela alteração cadastral
```

Restrito/imutável por convenção: `A2_COD`, `A2_LOJA`, `A2_FILIAL` (identidade), `D_E_L_E_T_`/`R_E_C_*`/`S_T_A_M_P_`/`I_N_S_D_T_` (sistema), acumuladores estatísticos (A2_MCOMPRA, A2_ULTCOM, A2_LC...).

# 26. Duplicate Detection

Sinais comprovados na base:

- `A2_COD+A2_LOJA` — único garantido fisicamente (`SA2010_UNQ`). **Chave de dedupe forte.**
- `A2_CGC` — **não** único: 32 valores duplicados (ex.: mesmo CNPJ com 2 códigos distintos) e 159 vazios. Índice 3 existe para pesquisa — usar como **sinal de possível existência**, não como identidade.
- `A2_NOME` — 106 razões sociais repetidas — sinal fraco.
- Recomendação de dedupe para POSSIBLE_EXISTING_SUPPLIER: `CGC normalizado` (alto sinal) + `NOME` (apoio) + `COD+LOJA` (identidade pós-existência). Bloqueios: `A2_MSBLQL='1'` (104 registros); deletados logicamente `D_E_L_E_T_='*'` (19) — considerar se o candidato deve incluir registros bloqueados/excluídos (decisão de contrato — ver §39).

# 27. Data Quality Findings

| Achado | Evidência | Impacto |
|---|---|---|
| `A2_LOJA` sujo: `'1 '`, `' 1'`, `'2 '` além de `'01'`..`'15'` | profiling | normalização `RTRIM`/padding obrigatória na ponte |
| `A2_COD` com espaços à direita ('00157 ') | profiling | normalizar trim |
| `A2_CGC` vazio em 159 registros (4,4%) | profiling | não assumir preenchido |
| `A2_MSBLQL` vazio em 158 (4,3%) | profiling | tratar branco como "não bloqueado"? → validar com Gabriel |
| `A2_TIPO` vazio em 1 registro; `A2_TPESSOA` 99,9% vazio | profiling | campos mal povoados |
| `A2_PAIS` só preenchido p/ estrangeiros; `A2_CODPAIS` universal (`01058`) | profiling | modelo canônico deve usar código BACEN |
| `A2_GRUPO` 0% — grupos reais em SAD | profiling | não mapear grupo→A2_GRUPO sem decisão |
| `A2_CODFAV` 0% — favorecido divergente não usado | profiling | omitir do contrato mínimo |
| `A2_NR_END` 0% / `A2_ENDCOMP` 0,1% | profiling | número/complemento quase nunca preenchidos — risco de quebra se contrato exigir |
| `A2_INSCR` 50% | profiling | IE só quando aplicável |

# 28. Full Business-to-TOTVS Mapping (de-para proposto)

Campos do modelo canônico → SA2. Somente campos com evidência de uso ou materialidade.

| api_field | business_label | totvs | descrição SX3 | type/len | create | update | lookup | sensitivity |
|---|---|---|---|---|---|---|---|---|
| supplier.identity.code | Código | A2_COD | Codigo | C6 | SYSTEM_GENERATED (GETSXENUM emp 01/05) | identity | — | interno |
| supplier.identity.store | Loja | A2_LOJA | Loja | C2 | REQUIRED (conv '01') | identity | — | interno |
| supplier.identity.branch | Filial | A2_FILIAL | Filial | C2 | SYSTEM_GENERATED (branco=compartilhado) | identity | — | interno |
| supplier.company.legal_name | Razão social | A2_NOME | Razao Social | C50 | REQUIRED_BY_PROCESS | mutable | — | — |
| supplier.company.trade_name | Nome fantasia | A2_NREDUZ | N Fantasia | C20 | REQUIRED_BY_PROCESS | mutable | — | — |
| supplier.tax.document | CNPJ/CPF | A2_CGC | CNPJ/CPF | C14 | CONDITIONAL (validação dígito+dedup quando enviado) | mutable c/ validação | CGC() | fiscal |
| supplier.tax.person_type | Tipo pessoa | A2_TIPO | Tipo | C1 | DEFAULTED (deriva do CGC) | mutable | enum F/J/X | fiscal |
| supplier.tax.state_registration | Inscr. estadual | A2_INSCR | Ins. Estad. | C18 | CONDITIONAL (IE por UF) | mutable | IE() | fiscal |
| supplier.tax.city_registration | Inscr. municipal | A2_INSCRM | Ins. Municip | C18 | OPTIONAL | mutable | — | fiscal |
| supplier.tax.cnae | CNAE | A2_CNAE | Cod CNAE | C9 | CONDITIONAL (TIPO J/X) | mutable | — | fiscal |
| supplier.tax.contributor | Contribuinte | A2_CONTRIB | Contribuinte | C1 | OPTIONAL (CBOX 1/2) | mutable | — | fiscal |
| supplier.address.street | Logradouro | A2_END | Endereco | C40 | REQUIRED_BY_PROCESS | mutable | — | — |
| supplier.address.number | Número | A2_NR_END | Numero | C6 | OPTIONAL (0% uso) | mutable | — | — |
| supplier.address.complement | Complemento | A2_ENDCOMP / A2_COMPLEM | Compl. End./Complemento | C21/C50 | OPTIONAL | mutable | — | — |
| supplier.address.district | Bairro | A2_BAIRRO | Bairro | C20 | REQUIRED_BY_PROCESS (97,6%) | mutable | — | — |
| supplier.address.postal_code | CEP | A2_CEP | CEP | C8 | REQUIRED_BY_PROCESS (94,6%) | mutable | — | — |
| supplier.address.city | Município | A2_MUN | Municipio | C25 | REQUIRED_BY_PROCESS | mutable | — | — |
| supplier.address.city_ibge_code | Cód. município | A2_COD_MUN | Cod. Municip | C5 | REQUIRED_BY_PROCESS (99,8%) + valida CC2 | mutable | CC2 | — |
| supplier.address.state | UF | A2_EST | Estado | C2 | REQUIRED_BY_PROCESS + valida SX5 '12' | mutable | SX5-12 | — |
| supplier.address.country_code_bacen | País BACEN | A2_CODPAIS | Paìs Bacen | C5 | REQUIRED (100%; default '01058' Brasil) | mutable | CCH | — |
| supplier.address.country | País | A2_PAIS | Pais | C3 | CONDITIONAL (estrangeiro) | mutable | SYA | — |
| supplier.contact.phone_ddd | DDD | A2_DDD | DDD | C3 | OPTIONAL (88%) | mutable | — | — |
| supplier.contact.phone | Telefone | A2_TEL | Telefone | C50 | OPTIONAL (91%; OBRIG1?) | mutable | — | — |
| supplier.contact.email | E-mail | A2_EMAIL | E-Mail | C50 | OPTIONAL (55%; OBRIG1?) | mutable | — | dados de contato |
| supplier.contact.person | Contato | A2_CONTATO | Contato | C15 | OPTIONAL (44%; OBRIG1?) | mutable | — | — |
| supplier.contact.website | Site | A2_HPAGE | Home-Page | C30 | OPTIONAL | mutable | — | — |
| supplier.payment.condition_code | Cond. pagto | A2_COND | Cond. Pagto | C3 | OPTIONAL (17,5%) | mutable | SE4 | — |
| supplier.payment.method | Forma pgto | A2_FORMPAG | Form. Pgto | C2 | OPTIONAL (30%; OBRIG1?) | mutable | SX5-58 | — |
| supplier.payment.finance_nature | Natureza | A2_NATUREZ | Natureza | C10 | REQUIRED_BY_PROCESS (99,9%) | mutable | SED | — |
| supplier.payment.ledger_account | Conta contábil | A2_CONTA | C Contabil | C20 | REQUIRED_BY_PROCESS (99,9%) | mutable | CT1 | — |
| supplier.banking.bank_code | Banco | A2_BANCO | Banco | C3 | OPTIONAL (1,2%) | mutable | SA6 | **sensível** |
| supplier.banking.branch | Agência | A2_AGENCIA | Cod Agencia | C5 | OPTIONAL | mutable | SA6 trinca | **sensível** |
| supplier.banking.branch_digit | DV agência | A2_DVAGE | DV Ag Cnab | C1 | OPTIONAL | mutable | — | **sensível** |
| supplier.banking.account | Conta | A2_NUMCON | Cta Corrente | C10 | OPTIONAL | mutable | SA6 trinca | **sensível** |
| supplier.banking.account_digit | DV conta | A2_DVCTA | DV Cta Cnab | C2 | OPTIONAL | mutable | — | **sensível** |
| supplier.banking.account_type | Tipo conta | A2_TIPCTA / A2_TPCONTA | Tp. Cta./Tipo Conta | C1 | OPTIONAL (72%) | mutable | CBOX | **sensível** |
| supplier.banking.swift | SWIFT | A2_SWIFT | Swift | C30 | OPTIONAL | mutable | — | **sensível** |
| supplier.flags.blocked | Bloqueado | A2_MSBLQL | Bloqueado | C1 | DEFAULTED '2' (não bloq.) | **restricted** | CBOX 1/2 | — |
| supplier.flags.rohs | RoHS | A2_YROHS | RoHS ? | C1 | OPTIONAL (67% uso; OBRIG1?) | mutable | CBOX | DELPI |
| supplier.flags.generic | Forn. genérico | A2_YFGEN | For Generico | C1 | OPTIONAL | mutable | — | DELPI |
| supplier.commercial.price_table | Tab. preço | A2_ZTABPRC | Tab Prc Comp | C3 | OPTIONAL (1,7%) | mutable | AIA | DELPI |
| supplier.links.customer | Cliente vinculado | A2_CLIENTE+A2_LOJCLI | Cód. Cliente+Loja | C6+C2 | OPTIONAL | mutable | SA1 | — |
| supplier.links.employee | Funcionário vínculo | A2_NUMRA | Cód Func | C6 | OPTIONAL | mutable | SRA | — |
| supplier.links.carrier | Transportadora | A2_TRANSP | Transp. | C6 | OPTIONAL | mutable | SA4 | — |

# 29. CREATE_REQUIRED_PROVEN

- `A2_LOJA` — chave única, sem default → enviar ('01' convenção).
- Identidade efetiva: o par COD+LOJA é gravado na inclusão; `A2_COD` pode ser gerado (abaixo).

# 30. CREATE_CONDITIONAL

- `A2_CGC` — enviar quando houver; se enviado, dígito válido + não-duplicado conforme A020CGC.
- `A2_INSCR` — quando contribuinte de ICMS (IE por UF).
- `A2_CIVIL` — quando `A2_TIPO='F'` (WHEN `naovazio()`).
- `A2_CNAE`/`A2_CBO` — condicionais a TIPO (J,X / F,X).
- `A2_PAIS`, endereço exterior — quando `A2_EST='EX'`.
- `A2_BANCO`+`AGENCIA`+`NUMCON` — trinca conjunta.
- Lookups — qualquer campo enviado deve existir na tabela lookup.
- `OBRIG1` fields (TEL/CONTATO/EMAIL/FORMPAG/NATUREZ/COD_MUN/CODPAIS/CONTA/YROHS): dicionário sinaliza obrigatoriedade contextual; dados provam não-bloqueio universal → confirmar com a rotina/ponte.

# 31. CREATE_SYSTEM_GENERATED

- `A2_COD` — `GETSXENUM("SA2")` (emp 01/05); manual em 03/04. **Recomendação: não enviar; deixar a ponte/Protheus gerar e retornar.**
- `A2_FILIAL` — contexto de filial da sessão (branco na base atual).
- Virtuais: `A2_NOMFAV`, `A2_PAISDES`, `A2_DTPAWB` — não enviar.
- Técnicos: `D_E_L_E_T_`, `R_E_C_N_O_`, `R_E_C_D_E_L_`, `S_T_A_M_P_`, `I_N_S_D_T_` — nunca enviar.
- Estatísticos: `A2_LC, A2_MATR, A2_MCOMPRA, A2_METR, A2_MSALDO, A2_NROCOM, A2_PRICOM, A2_SALDUP, A2_SALDUPM, A2_ULTCOM, A2_DESVIO, A2_MNOTA, A2_DATBLO` — mantidos por processos (não enviar).

# 32. UPDATE_IDENTITY

- `A2_COD` + `A2_LOJA` (+ `A2_FILIAL` implícito branco) — chave de lookup. `R_E_C_N_O_` pode ser usado internamente pela ponte.

# 33. UPDATE_MUTABLE

Todos os campos de negócio do de-para (§28) salvo identidade e sistema — com revalidação das mesmas regras.

# 34. UPDATE_RESTRICTED

- `A2_MSBLQL` — bloqueio é decisão governada (não um campo "a atualizar" livremente).
- `A2_COD`, `A2_LOJA`, `A2_FILIAL` — identidade.
- `A2_CGC` — mudança de documento é operação sensível (re-dispara dedup; potencial exigência de aprovação).
- Acumuladores estatísticos — nunca atualizar via API.

# 35. SYSTEM_OWNED_DO_NOT_SEND

`D_E_L_E_T_`, `R_E_C_N_O_`, `R_E_C_D_E_L_`, `S_T_A_M_P_`, `I_N_S_D_T_`, virtuais (`A2_DTPAWB`, `A2_NOMFAV`, `A2_PAISDES`), `A2_OK` (flag interna de tela), `A2_INCLTMG`.

# 36. Proposed Canonical Supplier Model

```json
{
  "supplier": {
    "identity": { "code": null, "store": "01", "company": "01" },
    "company": { "legal_name": "", "trade_name": "", "person_type": "J" },
    "address": {
      "street": "", "number": "", "complement": "", "district": "",
      "postal_code": "", "city": "", "city_ibge_code": "", "state": "",
      "country_bacen_code": "01058", "country_code": null,
      "foreign_address": null
    },
    "tax": {
      "document": "", "state_registration": "", "city_registration": "",
      "cnae": "", "contributor": null
    },
    "contact": { "person": "", "ddd": "", "phone": "", "email": "", "website": "" },
    "payment": {
      "condition_code": null, "method": null,
      "finance_nature": "", "ledger_account": ""
    },
    "banking": {
      "bank_code": null, "branch": null, "branch_digit": null,
      "account": null, "account_digit": null, "account_type": null, "swift": null
    },
    "flags": { "blocked": null, "rohs": null, "generic_supplier": null },
    "links": { "customer_code": null, "customer_store": null, "employee_code": null, "carrier_code": null }
  },
  "actor": { "portal_user_email": "", "protheus_user": null },
  "products": []
}
```

`products` vazio — amarração SA5 é operação separada. `actor` separado de `supplier` (ver §ator).

# 37. Proposed CREATE Contract

- Sem `identity.code` (geração no Protheus via GETSXENUM — emp 01; confirmar comportamento para 03/04/05).
- `identity.store` default `"01"`; `company`/`branch` = empresa alvo (SA2010 vs SA2030/40/50).
- Obrigatórios propostos: `legal_name`, `trade_name`, `person_type`, `address.state`, `address.city`, `address.city_ibge_code`, `address.country_bacen_code`, `payment.finance_nature`, `payment.ledger_account` — marcar como `REQUIRED_BY_PROCESS` até validação com rotina/ponte.
- `tax.document` com normalização (apenas dígitos) + dedupe sugerido (CGC+loja).
- Idempotência/upsert: decisão da ponte (§39).
- Resposta mínima: `supplier_code`, `supplier_store`, `operation`, `status`, `correlation_id`, read-back da SA2010 criada (prova de pós-condição).

# 38. Proposed UPDATE Contract

- `PATCH`-semântica: somente campos presentes são alterados; `null` NUNCA deve "limpar" (documentar semântica explícita — decisão §39).
- Identidade por `code`+`store` (+`company` quando multi-empresa).
- Campos restritos: `blocked`, `document` — fluxo governado.
- Retorno idem CREATE + lista de campos efetivamente alterados.

# 39. Questions for Gabriel

1. Qual endpoint/operação executa CREATE e qual executa UPDATE? Existe UPSERT separado?
2. A ponte executa a rotina MATA020 (ExecAuto/REST Job) ou grava direto na SA2010? Se direto, quais validações da MATA020 serão reimplementadas?
3. Quem gera `A2_COD` na ponte (GETSXENUM/rotina) e como funciona para empresas 03/04 (sem default)?
4. Idempotency: chave de idempotência do request? Comportamento em retry?
5. Semântica de `null` (limpar campo?) e de campo ausente (não alterar)?
6. Retorno: inclui `A2_COD`+`A2_LOJA` criados e read-back? Formato de erro (código+mensagem+campo)?
7. Boundary transacional: create falha como unidade única? Como é feito rollback se auxiliares falharem?
8. Actor: como o usuário Minha DELPI é propagado (USR_EMAIL→SYS_USR)? Onde fica registrado (campo, log, auditoria)?
9. Multi-empresa: a ponte escreve só em SA2010 (emp 01) ou recebe empresa alvo?
10. `A2_LOJA`: convenção '01' assumida pela ponte ou campo do request?
11. Duplicidade de CNPJ: a ponte bloqueia ou apenas sinaliza `POSSIBLE_EXISTING_SUPPLIER`?
12. Confirmação do conjunto efetivamente obrigatório da rotina (TEL/EMAIL/CONTATO/FORMPAG marcados OBRIG1 mas não universalmente preenchidos)?
13. `A2_MSBLQL`: criação sempre '2' (não bloqueado)? Bloqueio/desbloqueio é operação separada?
14. Códigos manuais (VIAGEM, FISCO...) — a ponte deve suportar código explícito ou só sequencial?

# 40. Unknown / To Inventory

| Item | Estado | Motivo |
|---|---|---|
| Mecanismo físico do numerador GETSXENUM (SXE ausente) | TO_INVENTORY | provável appserver/licença TOTVS |
| Nomes das empresas 03/04/05 (sem SM0 na base) | TO_INVENTORY | registro fora do SQL acessível |
| Validações internas das funções ADVPL (A020CGC, A020VldUCod, A060*, Ctb105Cta...) | UNKNOWN | código fonte não introspectável |
| Semântica exata das posições do bitmap X3_OBRIGAT | TO_INVENTORY | metadata ambígua |
| Se a ponte escreve via rotina ou SQL direto | UNKNOWN | decisão de implementação futura |
| Tabela `BA4` referenciada por validação A2_SIGLCR/CONREG mas ausente fisicamente | PROVEN gap | validação pode estar desativada por módulo |
| Origem dos códigos manuais e da política de lojas | TO_INVENTORY | processo de negócio |
| Por que X2_UNICO inclui `A2_FILIAL` mas todos os registros têm filial em branco | PROVEN por dados (MODO=C) | comportamento esperado |

# 41. Capability Gaps

| CAPABILITY_GAP | capability | informação buscada | impacto |
|---|---|---|---|
| CG-1 | introspecção ADVPL/MATA020 | validações efetivas no create (além do X3) | conjunto REQUIRED_BY_PROCESS permanece inferência estatística até confirmar com rotina/ponte |
| CG-2 | acesso à base TSS/licença | local da sequência GETSXENUM | não impede create (default existe); afeta compreensão do mecanismo |
| CG-3 | metadados SM0/empresas | nomes das empresas 03/04/05 | cosmético — códigos conhecidos |
| CG-4 | contrato da ponte Gabriel | endpoints, verbos, idempotência, erros | bloqueia fechamento do de-para público |
| CG-5 | SX6 parâmetros | MV_* que afetam obrigatoriedade (ex.: MV_PLORDA2) | obrigatoriedades condicionais de parâmetros não avaliadas |

---
*Auditoria gerada via leitura read-only (SX2/SX3/SIX/SX9/SXB/sys.\*/agregações com NOLOCK). Nenhuma escrita executada. Evidências brutas em `scripts/_supplier_audit/out/`.*
