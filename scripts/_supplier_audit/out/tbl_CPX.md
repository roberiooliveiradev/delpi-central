| 01 | `CPX_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `CPX_CODIGO` | C | 6 | 0 | Codigo | V: R: F3: |
| 03 | `CPX_LOJA` | C | 2 | 0 | Loja | V:COM001VldF(a) .And. COM001VldI('CPX') R: F3: |
| 04 | `CPX_ITEM` | C | 3 | 0 | Item | V: R: F3: |
| 05 | `CPX_CODFOR` | C | 6 | 0 | Fornecedor | V:COM001VldF(a) .And. COM001VldI('CPX') R: F3:FOR |
| 06 | `CPX_LOJFOR` | C | 2 | 0 | Loja | V:COM001VldF(a) .And. COM001VldI('CPX') R: F3: |
| 07 | `CPX_NOME` | C | 50 | 0 | Nome Fornec. | V: R:IF(INCLUI,'',Posicione("SA2",1,xFilial(" F3: |
