# Module: product-suppliers (SA5)

**Responsabilidade:** integração do vínculo **Produto × Fornecedor** (`SA5`)
via rotina oficial `MATA061` (MVC Model-2). Sem handler `.PRW` nesta etapa.

## Identidade SA5 (chave integral)

`A5_FILIAL + A5_FORNECE + A5_LOJA + A5_PRODUTO + A5_FABR + A5_FALOJA + A5_REFGRD`

Read-back inequívoco exige a chave completa — `products.suppliers` (ODBC) hoje
não projeta `FABR`/`FALOJA`/`REFGRD` (gap documentado em G0-C).

## Referências

| Item | Valor |
|---|---|
| Rotina oficial | `MATA061` — **MVC Model-2**; `MSExecAuto` de arrays **não** se aplica |
| Modelo | `Dmata061.prx` — espelho @ blob `b45cc9333c410a58d5836f78b79a140c6056c9c6` |
| Alternativa de reuso | submodelo `Model061` em `MATA010M_DLP.PRW` (avaliar antes de NEW) |
| EAI MATI060 | publicado mas **não configurado** (G0-C) — descartado como menor caminho |
| REST SA5 existente | nenhuma em 527/526 classes RESTALL |
| Fonte candidato | `DLP04I02.PRW` — `SOURCE_NAME_AVAILABLE=INCONCLUSIVE` (sem colisão em delpi-central/espelho; repo ERP inacessível) |

**Pendência:** a chamada de persistência oficial do modelo Model-2 (header+grid)
ainda depende de validação no TST01 antes de qualquer fonte candidato.
