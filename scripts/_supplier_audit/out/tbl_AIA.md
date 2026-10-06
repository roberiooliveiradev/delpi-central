| 01 | `AIA_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AIA_CODFOR` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->AIA_CODFOR+AllTrim(M->AIA_LOJFOR)).And.Com R: F3:FOR |
| 03 | `AIA_LOJFOR` | C | 2 | 0 | Loja Fornec. | V:ExistCpo("SA2",M->AIA_CODFOR+M->AIA_LOJFOR).And.Com010Pk() R: F3: |
| 04 | `AIA_NOMFOR` | C | 50 | 0 | Nome | V:.F. R:IIF(!INCLUI,Posicione("SA2",1,xFilial("S F3: |
| 05 | `AIA_CODTAB` | C | 3 | 0 | Tab.Preco | V:ExistChav("AIA",M->AIA_CODFOR+M->AIA_LOJFOR+M->AIA_CODTAB).A R: F3: |
| 06 | `AIA_DESCRI` | C | 30 | 0 | Descricäo | V:Texto() R: F3: |
| 07 | `AIA_DATDE` | D | 8 | 0 | Dt.Vld.Ini. | V:Com010Data() R: F3: |
| 08 | `AIA_DATATE` | D | 8 | 0 | Dt.Vld.Final | V:Com010Data() R: F3: |
| 09 | `AIA_CONDPG` | C | 3 | 0 | Cond.Pagto | V:Vazio().Or.ExistCpo("SE4") R: F3:SE4 |
