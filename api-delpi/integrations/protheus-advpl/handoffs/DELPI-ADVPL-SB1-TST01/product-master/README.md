# Module: product-master (SB1)

**Responsabilidade:** fontes de integração do **cadastro de produtos** (`SB1`)
via rotina oficial `MATA010`. Workspace de entrega de fontes — não é runtime.

## Referências

| Item | Valor |
|---|---|
| Rotina oficial | `MATA010` (ExecAuto/`MSExecAuto`) |
| Fonte de referência upstream | `04. Estoque/DLP04I01.PRW` — repo `Delpi-ti/protheus-erp` (`master`) |
| SHA upstream | `INCONCLUSIVE` — repo privado inacessível nesta sessão; registrar no handoff |
| Espelho verificável | `docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW` @ blob `cdb68b0487222823a96162c0e493e442648e21f7` (commit `be614649b7`) |
| Contrato REST publicado | `DELPIPRODUTO` — `POST/PUT /v1/IncProduto/incluir|alterar` (`PROVEN_RUNTIME` PRD+TST01) |
| Fonte candidato | `src/DLP04I01.PRW` — **SOURCE_CANDIDATE** (22 campos, representação completa; ver `contracts/create-update-contract.md`) |

## Operações

- `CREATE` / `UPDATE`: fonte existente upstream (22 campos `B1_*`, representação completa).
- `READ`: avaliar reaproveitamento da API DELPI existente.
- `DELETE`: contrato e política pendentes — **nunca** implementar sem semântica ERP aprovada.

**Não copiar automaticamente o fonte legado** — a versão candidata deve
definir conteúdo e compatibilidade na task de desenvolvimento própria.
