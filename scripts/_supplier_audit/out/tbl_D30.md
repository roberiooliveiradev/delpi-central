| 01 | `D30_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `D30_CODFOR` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->D30_CODFOR) R: F3:FOR |
| 03 | `D30_LOJFOR` | C | 2 | 0 | Loja | V:EXISTCPO("SA2",M->D30_CODFOR+M->D30_LOJFOR) .Or. Vazio() R: F3: |
| 04 | `D30_ATVSIM` | C | 6 | 0 | Atv Eco SIMP | V:ExistCpo("SX5","HB"+M->D30_ATVSIM) .OR. Vazio(M->D30_ATVSIM) R: F3:HB |
| 05 | `D30_CODSIM` | C | 10 | 0 | Cod. ARI | V:ExistCpo("D33", M->D30_CODSIM) .OR. Vazio (M->D30_CODSIM) R: F3:D33 |
| 06 | `D30_INSTSI` | C | 7 | 0 | Cd Inst SIMP | V:ExistCpo("D36", M->D30_INSTSI) .OR. Vazio (M->D30_INSTSI) R: F3:D36 |
| 07 | `D30_MUNSIM` | C | 6 | 0 | Cod.Mun.SIMP | V:ExistCpo("CC2", M->D30_MUNSIM,5) .OR. Vazio(M->D30_MUNSIM) R: F3:CC2ANP |
| 08 | `D30_PAISIM` | C | 6 | 0 | Cd Pais SIMP | V:ExistCpo("SX5", "HC"+M->D30_PAISIM) .OR. Vazio(M->D30_PAISIM R: F3:HC |
| 09 | `D30_CLTRIB` | C | 3 | 0 | Clas. Trib | V:ExistCpo("SX5","HH"+M->D30_CLTRIB) R: F3: |
