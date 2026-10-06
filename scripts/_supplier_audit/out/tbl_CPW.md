| 01 | `CPW_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `CPW_CODIGO` | C | 6 | 0 | Codigo | V:COM001VldF(a) .And. COM001VldI('CPW') R: F3:FOR |
| 03 | `CPW_LOJA` | C | 2 | 0 | Loja | V:COM001VldF(a) .And. COM001VldI('CPW') R: F3: |
| 04 | `CPW_NOME` | C | 50 | 0 | Nome | V: R:IF(INCLUI,'',Posicione("SA2",1,xFilial(" F3: |
