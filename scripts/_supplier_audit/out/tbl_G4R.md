| 01 | `G4R_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `G4R_FORNEC` | C | 6 | 0 | Cód. Fornec. | V:Vazio() .Or. ExistCpo("SA2",M->G4R_FORNEC) R: F3:SA2A |
| 03 | `G4R_LOJA` | C | 2 | 0 | Loja | V:(Vazio() .Or. ExistCpo("SA2",M->G4R_FORNEC+M->G4R_LOJA)) .an R: F3: |
| 04 | `G4R_NOME` | C | 40 | 0 | Fornecedor | V: R:IF(!INCLUI,POSICIONE("SA2",1,XFILIAL("SA F3: |
