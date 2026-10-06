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
