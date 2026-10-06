

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
