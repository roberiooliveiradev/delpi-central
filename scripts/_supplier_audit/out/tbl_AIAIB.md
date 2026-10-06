| 01 | `AIA_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AIA_CODFOR` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->AIA_CODFOR+AllTrim(M->AIA_LOJFOR)).And.Com R: F3:FOR |
| 03 | `AIA_LOJFOR` | C | 2 | 0 | Loja Fornec. | V:ExistCpo("SA2",M->AIA_CODFOR+M->AIA_LOJFOR).And.Com010Pk() R: F3: |
| 04 | `AIA_NOMFOR` | C | 50 | 0 | Nome | V:.F. R:IIF(!INCLUI,Posicione("SA2",1,xFilial("S F3: |
| 05 | `AIA_CODTAB` | C | 3 | 0 | Tab.Preco | V:ExistChav("AIA",M->AIA_CODFOR+M->AIA_LOJFOR+M->AIA_CODTAB).A R: F3: |
| 06 | `AIA_DESCRI` | C | 30 | 0 | Descricäo | V:Texto() R: F3: |
| 07 | `AIA_DATDE` | D | 8 | 0 | Dt.Vld.Ini. | V:Com010Data() R: F3: |
| 08 | `AIA_DATATE` | D | 8 | 0 | Dt.Vld.Final | V:Com010Data() R: F3: |
| 09 | `AIA_CONDPG` | C | 3 | 0 | Cond.Pagto | V:Vazio().Or.ExistCpo("SE4") R: F3:SE4 |
| 01 | `AIB_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AIB_CODFOR` | C | 6 | 0 | Fornecedor | V: R: F3: |
| 03 | `AIB_LOJFOR` | C | 2 | 0 | Loja Fornec. | V: R: F3: |
| 04 | `AIB_CODTAB` | C | 3 | 0 | Tabela Preco | V: R: F3: |
| 05 | `AIB_ITEM` | C | 4 | 0 | Item | V: R: F3: |
| 06 | `AIB_CODPRO` | C | 15 | 0 | Produto | V:ExistCpo("SB1") R: F3:SB1 |
| 07 | `AIB_DESCRI` | C | 120 | 0 | Descricäo | V:Texto() R:If(!INCLUI,Posicione("SB1",1,xFilial("SB F3: |
| 08 | `AIB_PRCCOM` | N | 14 | 7 | Preco Unit. | V:Positivo() R: F3: |
| 09 | `AIB_QTDLOT` | N | 14 | 3 | Faixa | V:Positivo() R:999999.99 F3: |
| 10 | `AIB_INDLOT` | C | 20 | 0 | Faixa | V: R: F3: |
| 11 | `AIB_MOEDA` | N | 2 | 0 | Moeda | V:M->AIB_MOEDA > 0 .And. M->AIB_MOEDA <= MoedFin() R:1 F3: |
| 12 | `AIB_DATVIG` | D | 8 | 0 | Vigencia | V: R:DATE() F3: |
| 13 | `AIB_FRETE` | N | 13 | 5 | Frete | V:Positivo() R: F3: |
| 14 | `AIB_CODPRF` | C | 15 | 0 | Cod.Prd.Forn | V:.f. R:If(!INCLUI,Posicione("SA5",1,xFilial("SA F3: |
| 15 | `AIB_ZDTINC` | D | 8 | 0 | Dt Inclusao | V: R:DATE() F3: |
