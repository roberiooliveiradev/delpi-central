| 01 | `AD_FILIAL` | C | 2 | 0 | Filial | V: R: F3: |
| 02 | `AD_FORNECE` | C | 6 | 0 | Fornecedor | V:ExistCpo("SA2",M->AD_FORNECE) .And. ExistChav("SAD",M->AD_FO R: F3:FOR |
| 03 | `AD_LOJA` | C | 2 | 0 | Loja | V:ExistCpo("SA2",M->AD_FORNECE+M->AD_LOJA) .And. Existchav("SA R: F3: |
| 04 | `AD_NOMEFOR` | C | 50 | 0 | Nome | V: R: F3: |
| 05 | `AD_GRUPO` | C | 4 | 0 | Grupo | V:ExistChav("SAD",M->AD_FORNECE+M->AD_LOJA+M->AD_GRUPO) .And.  R: F3:SBM |
| 06 | `AD_NOMGRUP` | C | 120 | 0 | Descricao | V: R: F3: |
| 07 | `AD_CODTAB` | C | 3 | 0 | Tab. Preço | V:Vazio().OR.ExistCpo("AIA",M->AD_FORNECE+M->AD_LOJA+M->AD_COD R: F3:AIA |
