# Padrão de qualidade de rotas (api-delpi)

Referência de implementação: família de OPs [`/production/pcp-orders`](./production-pcp-orders.md) e helper [`paged_list_envelope_service.py`](../../app/application/services/paged_list_envelope_service.py).

**Não** exige o trio `summary` / `items` / `ranking`. O padrão são critérios de qualidade transversais.

## Critérios

### 1. `paged_list` canônico

- Usar `build_paged_list_envelope` (ou equivalente compartilhado).
- `pagination` com `page`, `page_size`, `total`, `total_pages`, **`is_complete`**.
- Aliases flat (`pageSize`, `totalPages`) só se houver consumidor legado.

### 2. DRY

- Filtros comuns em DTO + `Depends` (não repetir `Query` N vezes).
- SQL `build_base_where` único para count/list/agregados da mesma view.
- Mapper (domínio) + assembler (application); UC só orquestra.
- Domain **sem** import de infra; application sem helpers de paginação espalhados em infra.

### 3. Bilíngue OpenAPI / TV

- Paths e query params **EN** (novos e ao alinhar).
- Summary OpenAPI nativo EN; PT em locale; `tv_route_audience` com **EN ≠ pt-BR** (não template genérico).
- Domínio fechado: `enum` + `pattern`; `enumLabels` em `openapi_param_locale.json`.
- Body **snake_case EN**; aliases legados só com consumidor antigo.

### 4. Diretrizes Cursor

- `api_delpi_success` + `operation_id` = OpenAPI = `route_contract_registry` (`entity` + `shape`).
- Smoke Nível A + `route_test_coverage` sem gap.
- Doc dedicada + entrada em [06-modulos-departamentais.md](./06-modulos-departamentais.md).

## Estratégias de migração

| Código | Significado |
|--------|-------------|
| **A** | Qualidade sem breaking — envelope, DRY, TV, `is_complete`; mantém keys/paths atuais |
| **B** | Aliases EN aditivos + consumidor passa a preferir canônico com fallback |
| **C** | Rename breaking — só dual-route + deprecação |

Sempre **A** primeiro; **B** com MFE no mesmo ciclo quando houver acoplamento; **C** evitar sem versionamento.

## Ondas de refatoração

| Onda | Famílias | Estratégia |
|------|----------|------------|
| 1 | `/inspecoes-entrada`, `/supplies/stock-balances`, `/production/unproductive-hours` | A (+ B em UH) |
| 2 | `/retrabalhos`, `/refugos` | A → B com MFE |
| 3 | `/inspecoes-processo` | A (compat flat) + B |
| 4 | `/financeiro/inadimplencia`, `/financeiro/despesas-centro-custo` | A (+ doc despesas); B depois |

Facades `/quality/scrap-cost-pct` e `/quality/rework-cost-pct` ficam fora do rename de path das famílias PT.

## Inventário (dívida residual pós-ondas 1–4)

Estratégia **A** (e **B** aditivo) aplicada. Paths PT e rename (**C**) ficam para ciclo futuro.

| Família | Status |
|---------|--------|
| `/production/pcp-orders` | Referência |
| `/production/unproductive-hours` | A+B — envelope, mapper EN+aliases PT |
| `/supplies/stock-balances` | A — `build_paged_list_envelope` |
| `/inspecoes-entrada` | A — `is_complete` + TV curado |
| `/retrabalhos`, `/refugos` | A+B listagens — envelope + aliases; MFE fallback |
| `/inspecoes-processo` | A+B — `pagination` + aliases EN; MFE `resolveHasNext` |
| `/financeiro/inadimplencia` | A — `is_complete` + `total` |
| `/financeiro/despesas-centro-custo` | A + doc/`06` |

Residual: paths PT e remoção de aliases legados (**C**).

## Checklist por PR de família

1. Envelope canônico (+ aliases se B); DRY; sem domain→infra.
2. Smoke `operationId` + regressão `is_complete`.
3. Mudança de shape/B → MFE no mesmo PR.
4. `tv_route_audience` curado + sync TV se params mudarem.
5. Chat registry `--check` se OpenAPI mudar.
6. Doc + `06-modulos` se faltar.

## Relação com outros docs

- [openapi-bilingue-catalogo-canonico.md](./openapi-bilingue-catalogo-canonico.md) — como construir rota futura
- [api-delpi-response-contract](../../../.cursor/rules/api-delpi-response-contract.mdc) — envelope/`meta`
- [new-api-route-checklist](../../../.cursor/rules/new-api-route-checklist.mdc) — três pacotes
