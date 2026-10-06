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
