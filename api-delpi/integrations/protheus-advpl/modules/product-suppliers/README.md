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

## Inventário G2-B (concluído — sem implementação)

- `contracts/official-model-inventory.md` — modelo `DMATA061` completo
  (ModelDef/ViewDef/MenuDef, `SetPrimaryKey` 7 campos, `a060LinOk`/`a060VldGrv`).
- `contracts/mvc-lifecycle-investigation.md` — CREATE/READ/UPDATE/DELETE por
  operação; **achado crítico:** `a060VldGrv` bloqueia excluir o último vínculo.
- `contracts/sa5-field-matrix.md` — matriz de campos com status.
- `contracts/crud-contract-candidate.md` — superfície REST conceitual (PLANNED).
- `contracts/architecture-decision-candidate.md` — recomendação `EXTEND`
  (façada sobre `FWLoadModel('DMATA061')`), `DECISION_REQUIRED` dos owners.

**Nenhum `.PRW` criado** — contrato MVC segue `TO_INVENTORY`/`VALIDAR NO TST01`.
