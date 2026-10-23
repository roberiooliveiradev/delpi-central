# X4.UX-R1.S8 — Conferência de cadastros existentes por CNPJ

**Data:** 2026-10-23
**Autoridade:** autorização explícita do Product Owner («PORTAL SUPRIMENTOS — X4.UX-R1.S8»)
**Escopo:** `supplies-api` (application/gateways/routes/tests) + `plugins/supplies` (creation flow, content, CSS, testes) + docs. `api-delpi` apenas inventariada — **nenhuma alteração**.

## Baseline e baseline SHAs

- **BASE HEAD:** `06a2cc73a54dd377c9d620b1f39593b7f8b45ba1` (pós-rebase sobre `origin/main` `54989bda6f23d3aed153f1cf974f67d3c90ce3ad`)
- Ancestralidade confirmada: S1 `1cdfa4a85a`, S2 `b7f4a51ce6`, S2.R1 `cda28e6b9f`, S2.R2 `ddc5abb81d`, S7 `06a2cc73a5`.
- **FINAL HEAD / COMMIT:** ver rodapé do commit escopado.

## Decisão do Product Owner (R1–R10 aplicada)

- CNPJ repetido **não** é erro cadastral e **não** bloqueia o preenchimento.
- Todos os registros do CNPJ consultado devem ser visualizáveis, com conferência individual por `supplier_code` + `supplier_store`.
- Conferência é **read-only**, reutiliza a ficha E14 e não edita/cria nada.
- Rascunho do novo fornecedor deve ser preservado.
- Sem escrita ERP, sem nova permission, sem regra de unicidade, sem deploy.

## Inventário (S8.P0 → contrato congelado)

### Contrato canônico `api-delpi` (PROVEN, sem mudança)

- `GET /supplies/suppliers?tax_id=<digits>&page=<n>&page_size=<n≤100>` — filtro `tax_id` **exato** normalizado em `SuppliersListRequest` (`suppliers_request.py`).
- Envelope paginado: `items` + `total` (`build_paged_list_envelope`).
- Ordenação estável: `ORDER BY <sort_col> <dir>, SA2.A2_COD, SA2.A2_LOJA` (`totvs_supplier_repository.py`) — determinística mesmo com nomes repetidos.
- `search_suppliers_paged` executa `COUNT(*)` + página — `total` confiável sem varrer registros.
- Conclusão: o contrato canônico **atende integralmente**; nenhum gap de owner.

### BFF antes de S8

- `DelpiSupplierDuplicateSearch.search_by_tax_id` já devolvia `(items, total)`, mas pedia só `page=1&page_size=20` e o preview cortava em `matches[:10]` sem expor `total`. Risco real de omissão silenciosa acima de 10 registros.

### MFE antes de S8

- Banner `POSSIBLE_MATCH` em `variant="error"` com até 10 links que navegavam a própria aba (rascunho em risco), sem total nem paginação.

### Auditoria (RQ-07) — GAP registrado

- Não existe contrato canônico para eventos de visualização (`supplier_creation_duplicate_check_viewed` / `supplier_existing_record_opened` são apenas candidatos de inventário).
- O trail de auditoria existente cobre **decisões de enriquecimento** (E14), não visualização de duplicidade.
- Owner provável: Core/segurança (auditoria de acesso) — **nenhum evento/tabela/log novo criado** em S8; lacuna documentada para decisão futura.
- Nenhum CNPJ bruto, token ou payload externo novo em logs.

## Contrato final (S8.S1 — menor diff, aditivo)

1. `DelpiSupplierDuplicateSearch.search_by_tax_id(tax_id, *, access_token, page=1, page_size=20)` — ganhou `page`/`page_size` opcionais; chamadas existentes intactas.
2. `POST /suppliers/creation-preview` → `duplicate_check` ganhou `"total": <int|null>` (aditivo; `null` só em `INCONCLUSIVE`). `matches` continua sendo a **semente da página 1** (≤10 itens na mesma ordenação canônica).
3. **Novo** `GET /suppliers/existing-suppliers?tax_id=<14 dígitos>&page=<n>&page_size=<n≤50>` — read-only, mesma capability `can_use_operations` (sem permission nova), responde `{items, page, page_size, total}` com a mesma projeção mínima do preview. Só consulta `api-delpi` — **nunca** a BrasilAPI.

## MFE (S8.S2)

- Banner `POSSIBLE_MATCH`: `variant="error"` → `variant="default"` (informativo), copy PO («Este CNPJ já possui cadastro no Protheus» + «Você pode continuar o preenchimento normalmente.»).
- Novo `CreationExistingSuppliersPanel`: total real do contrato, linhas código/loja/nome/UF/bloqueado, `SuppliesCompactPagination` (design system) quando `total > 10`, cache por página, proteção contra resposta obsoleta (`requestSeq`), estados de erro/página vazia sem perder formulário, remount por `key={activeTaxId}`.
- `Conferir cadastro`: `<a href={buildSupplierDetailPath(code, store)} target="_blank" rel="noopener noreferrer">` — **nova aba** = preservação do rascunho sem persistência no browser. Aba do formulário nunca sai da página (RQ-05).
- Sem `localStorage`/`sessionStorage`/`indexedDB`; sem `fetch` fora do `httpClient`; zero chamada direta a api-delpi/providers.

## E14 / Enriquecimento (RQ-04, RQ-06)

- Reuso total: `buildSupplierDetailPath` → `SupplierDetailPage` existente com `EnrichmentSection` e conferências já implementadas — nenhuma rota/section duplicada.
- Divergências cadastrais continuam visíveis na ficha E14 (enrichment draft-only); S8 não adiciona consultas externas automáticas.

## Testes (S8.S3)

- **supplies-api:** 11 testes novos em `TestExistingSuppliers` (401/403/422, zero registros, página com total>itens, clamp `page_size=50`, página não inteira → 422, falha upstream → 5xx, zero chamada BrasilAPI) + 2 asserts de contrato `total` ajustados. Suíte completa **~230 verdes**.
- **MFE:** 4 testes estruturais S8 (endpoint BFF + componente canônico, nova aba + `noopener`, banner não-`error` + copy PO, total do contrato). Suíte completa **337 verdes** (39 no módulo creation).
- **Typecheck:** `tsc -b` limpo. **Build:** `vite build` OK (bundle `App-CwatapS_.js`).
- **Lint:** diff S8 limpo; suite mantém 13 erros/21 warnings **pré-existentes** fora do escopo (classificados).
- **Federated smoke:** `TEST_NOT_RUN` — sem deploy nem browser autenticado em S8.

## Segurança

- AuthZ server-side inalterada (`require_policy(can_use_operations)` em ambas as rotas).
- Mesma capability do preview; nenhuma permission/rota pública nova.
- Falha upstream propagada via `_gateway_error_response` — fail-closed.
- Nenhum segredo/token no MFE; bundle sem `api-delpi`/providers/`s2s`.

## Arquivos alterados

- `supplies-api/app/infrastructure/gateways/delpi_supplier_duplicate_search.py`
- `supplies-api/app/application/services/supplier_creation_preview/preview_service.py`
- `supplies-api/app/interfaces/http/routes/supplier_creation_routes.py`
- `supplies-api/tests/test_supplier_creation_routes.py`, `tests/application/test_supplier_creation_preview_service.py`
- `plugins/supplies/src/features/suppliers/creation/{CreationExistingSuppliersPanel.tsx,CreationAssistedFlow.tsx,api.ts,types.ts,content.ts,creation.structural.test.ts}`
- `plugins/supplies/src/index.css`
- `plugins/supplies/src/content/{helpTooltips.ts,userManualContent.ts,glossaryContent.ts}`
- `docs/12-roadmap-e-evolucao/supplies/X4-UX-R1-S8-EXISTING-SUPPLIERS-REVIEW-20261023.md` (este doc), `IMPLEMENTATION-PLAN.md`

## AC (1–20)

AC-01 `PASS` · AC-02 `PASS` · AC-03 `PASS` · AC-04 `PASS` · AC-05 `PASS` · AC-06 `PASS` · AC-07 `PASS` · AC-08 `PASS` · AC-09 `PASS` · AC-10 `PASS` (nova aba) · AC-11 `PASS` · AC-12 `PASS` · AC-13 `PASS` · AC-14 `PASS` (gap documentado, owner identificado) · AC-15 `PASS` · AC-16 `PASS` · AC-17 `PASS` · AC-18 `PASS` · AC-19 `PASS` · AC-20 `PASS`.

**Residuais:** visual/browser `INCONCLUSIVE`; contrato de auditoria de visualização `TO_INVENTORY` (owner: Core/segurança); runtime pós-deploy `TEST_NOT_RUN` — depende de autorização operacional separada.
