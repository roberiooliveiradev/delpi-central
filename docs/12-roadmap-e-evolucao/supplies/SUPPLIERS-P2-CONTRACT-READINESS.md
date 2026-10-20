# Suppliers P2 — Contract Freeze & Integration Readiness

> **Estado:** `ACCEPT_WITH_RESIDUAL` candidato — contrato de leitura E13/WF-09 e fundação E14/WF-10 completos e revisáveis; E13 permanece **BLOCKED** na fila (E10 GATE INCONCLUSIVE). Documento de contrato, **não** autorização de implementação, escrita ou promoção.
>
> **Base:** `origin/main` @ `9985914d85` (2026-10-20+). Fontes: código e testes no HEAD (PROVEN), ADR-008/009/010, contratos REST fornecedores, playbook SA2, catálogo plugin-ui.
>
> **Escopo deste documento:** contratos de consulta (lista paginada + detalhe), contratos BFF, consumo de S2S individual, escopo empresa/filial, projeção/LGPD, RQ/AC, matriz de testes e dependências. POST/PUT e E14 permanecem `TARGET / BLOCKED`.

## 1. Roadmap e estado da fila (revalidado em HEAD)

| Etapa | Estado provado | Evidência |
|---|---|---|
| E9 / WF-07 Entregas | `PASS` (federated smoke 2026-09-21) | `README.md`; evidência `e9-wf07-federated-runtime-gate.md` |
| E10 / WF-15 Controle de Estoques | `IN PROGRESS` — GATE-FEATURE **INCONCLUSIVE** | `README.md` status; `e10-wf15-s4-final-acceptance.md` (`DEPLOY_REQUIRED=YES`) |
| E11 / WF-16 Estoque de Segurança | `BLOCKED` (`dependsOn e10-inventory`) | `IMPLEMENTATION-PLAN.md` DAG |
| E12 / WF-17 Análise de Consumo | `BLOCKED` (`dependsOn e11`) | idem |
| E13 / WF-09 Fornecedores (lista) | `BLOCKED` (`dependsOn e12`) — contrato deste documento | idem + §3 |
| E14 / WF-10 Fornecedor 360 | `BLOCKED` (`dependsOn e13`) — fundação contratual em §6 | idem + §6 |

`E13_AUTHORIZATION = NOT_READY` — nenhuma autorização do Product Owner para promoção consta em HEAD. A conclusão do contrato **não** promove a etapa. Rota reservada `/apps/supplies/suppliers` existe no manifest (`showInMenu: false`, `supplies.access`); `:code/:store` reservado por `DIRECTORY-OBJECTS.md` — ambos permanecem `not_found` até implementação.

## 2. Inventário de contrato — o que já existe (PROVEN em código)

| Capacidade | Local | Estado | Consumidores atuais |
|---|---|---|---|
| `search_suppliers(query, limit≤50)` — OR em `A2_COD`/`A2_NOME`/`A2_NREDUZ`/`A2_CGC` + par código+loja | `api-delpi/.../totvs_supplier_repository.py:11` | PROVEN read-only; **sem paginação, sem filtro empresa/filial** | LNF (`search_lancamento_notas_fiscais_suppliers`, perm `LANCAMENTO_NOTAS_FISCAIS_CREATE`), invoice issuance |
| `get_supplier(code, store)` — lookup TOP 1 | mesmo arquivo :60 | PROVEN read-only | LNF, invoice issuance |
| `GET /integrations/protheus/suppliers/{supplier_id}` — REST Protheus (8 dígitos `A2_COD`+`A2_LOJA`) | `protheus_router.py:84` | PROVEN; perm `api-delpi.integrations.protheus.read` | diagnóstico; sem consumidor BFF |
| `POST /integrations/protheus/suppliers` | `protheus_router.py:127` | PROVEN código; gate `PROTHEUS_SUPPLIER_CREATE_ENABLED=false` | nenhum (bloqueado) |
| `PUT /integrations/protheus/suppliers/{supplier_id}` | `protheus_router.py:187` | PROVEN código; gate `false`; allowlist `supplier_name`/`supplier_short_name` | nenhum (bloqueado) |
| S2S individual (OAuth2 client credentials) | `shared/delpi_auth`, `api-delpi/.../s2s_service_access.py`, `supplies-api/.../delpi_s2s_gateway.py` | PROVEN código+produção (P1.SEC.5) | gateway disponível, **nenhuma rota migrada** |
| Envelope paginado `build_paged_list_envelope` | `api-delpi/.../paged_list_envelope_service.py` | PROVEN (dual keys `page_size`/`pageSize`) | famílias supplies atuais |
| Tiers de paginação (`pagination_tiers.json` + `PAGE_*_QUERY`) | `api-delpi/app/interface/http/pagination_query.py` | PROVEN; `page_20_100` disponível | convenção vigente |

**Proibição preservada:** a permissão `LANCAMENTO_NOTAS_FISCAIS_CREATE` e a rota LNF `/lancamento-notas-fiscais/suppliers` **não** são reutilizáveis como autorização/contrato do Portal Suprimentos. Reuso fica no nível repository/adapter dentro de `api-delpi` com contrato próprio de Suprimentos.

## 3. SUPPLIER SEARCH CONTRACT — lista paginada `api-delpi` (E13)

### 3.1 Semântica SA2 decidida

| Decisão | Valor | Evidência |
|---|---|---|
| `SUPPLIER_DATA_SOURCE` | `SA2010` (empresa 01) via SQL read-only; REST Protheus **não** é fonte de listagem (contrato upstream só tem GET por ID) | playbook SA2 §:10 |
| `COMPANY_SCOPE` | **empresa 01 apenas**; `SA2030/40/50` (empresas 03/04/05) fora do escopo inicial | playbook SA2 — bases distintas |
| `BRANCH_FILTER_REQUIRED` | **Não** — `MODO=C` compartilhada; `A2_FILIAL` vazio em 100% dos registros; criar filtro por unidade seria artificial | playbook SA2 :10,:69 |
| `A2_FILIAL_SEMANTICS` | sempre `''` em SA2010; a query deve fixar `A2_FILIAL = ''` explicitamente para alinhar aos índices `SA20101/02/03` (todos prefixados por `A2_FILIAL`) | playbook SA2 §6 |
| Identidade | `A2_COD` (6 díg, zeros à esquerda) + `A2_LOJA` (2 díg); `supplier_id` = concatenação 8 dígitos. **CNPJ/CPF não é chave** (32 duplicados) | playbook SA2 :12 |
| Soft-delete | `D_E_L_E_T_ = ''` obrigatório | repo vigente |
| Bloqueio | `A2_MSBLQL = '1'` → `blocked=true` | repo vigente :101 |
| Unidade Portal `01`/`02` | **filtro de dados operacional (filiais SC/ES), não mapeia para `A2_FILIAL`** — SA2 é compartilhada; fornecedor é visível a ambas as unidades | ADR-009 + playbook |

### 3.2 Operação candidata

```
GET /supplies/suppliers        operationId: list_supplies_suppliers
meta.entity: supplies_supplier  kind: paged_list  (route_contract_registry)
```

- Sem colisão: `list_supplies_suppliers`/`supplies_supplier` ausentes do registry em HEAD (grep vazio).
- Família `/supplies/*` segue convenção `operation_id` snake_case + prefixo `supplies_`.

### 3.3 Request (query params)

| Param | Tipo | Regra |
|---|---|---|
| `query` | string, opcional, `min_length=2` quando presente | OR: `A2_COD LIKE q%` · `A2_NOME`/`A2_NREDUZ` contains CI_AI · `A2_CGC` contains só dígitos · par `cod loja` (split `\s-/`) — **mesma semântica do repo vigente** |
| `state` | string 2 chars, opcional | filtro exato `A2_EST` |
| `blocked` | bool, opcional | `A2_MSBLQL = '1'` / `<> '1'` |
| `page` | int `ge=1`, default 1 | convenção `paged_list` |
| `page_size` | tier `page_20_100` (default 20, 1–100) | `pagination_tiers.json` |
| `sort_by` | enum: `supplier_name` (default), `supplier_code`, `tax_id`, `state` | mapeamento allowlist server-side, nunca SQL livre |
| `sort_dir` | enum `asc`/`desc`, default `asc` | tiebreak determinístico `A2_COD, A2_LOJA` |

Regras: `query` ausente → lista não filtrada paginada (válido); `query` presente com `<2` chars → `422`; página fora do intervalo → `items=[]` + `total`/`total_pages` reais (não erro); params desconhecidos → rejeitados (422) ou ignorados conforme convenção FastAPI do router — **decisão: rejeitar**, consistente com fail-closed.

### 3.4 Response — envelope `paged_list` canônico

```json
{
  "success": true,
  "data": {
    "items": [{
      "supplier_id": "00000101",
      "supplier_code": "000001",
      "supplier_store": "01",
      "supplier_name": "...",
      "supplier_short_name": "...|null",
      "tax_id": "...|null",
      "state": "..|null",
      "blocked": false
    }],
    "page": 1, "page_size": 20, "pageSize": 20,
    "total": 0, "total_pages": 0, "totalPages": 0,
    "pagination": { "page":1, "page_size":20, "total":0, "total_pages":0, "is_complete": true }
  },
  "meta": { "operation_id": "list_supplies_suppliers", "entity": "supplies_supplier" }
}
```

- `COUNT(*)` exato mantido (índices cobrem; volume SA2 moderado). Se perfil de custo provar inviável, migrar para `has_next` envelope — **trade-off registrado, sem mudança preventiva**.
- `supplier_id` preserva zeros à esquerda (string 8 díg). `tax_id` só dígitos (já normalizado no mapper).

### 3.5 Erros

| HTTP | code | Situação |
|---|---|---|
| 400/422 | `VALIDATION_ERROR` | params inválidos, `query` curta, sort inválido |
| 401 | `UNAUTHORIZED` | sem credencial válida |
| 403 | `FORBIDDEN`/`S2S_*` | usuário sem permissão do contrato ou S2S negado |
| 503 | `S2S_UNAVAILABLE`/upstream | JWKS/TOTVS indisponível — fail-closed |

## 4. BFF CONTRACT — `supplies-api` (E13)

```
GET /suppliers        MFE → supplies-api (JWT usuário) → api-delpi (S2S + Bearer usuário)
```

Cadeia obrigatória: `require_policy(can_use_operations)` (`supplies.access` efetivo do Core) → validação dos params publicados (mesmo shape do contrato api-delpi, exceto `branch` — **não exposto**, fornecedor não é filtrado por unidade) → `DelpiS2SApiGateway.get("/supplies/suppliers", access_token=user_jwt, params=...)` → `unwrap_delpi_envelope` → `jsonify`.

Erros: `DelpiApiGatewayError` → `_gateway_error_response` (padrão vigente); `AuthorizationError` → 403; sem token → 401.

**Decisão AuthZ:** `supplies.access` é a única permissão funcional. `supplies.manage` não é atalho (pode não ter `access`). Nenhuma permission CRUD criada. Unidade `01`/`02` (ADR-009) **não se aplica** a fornecedores — `require_units` **não** decora esta rota; documentado como exceção consciente ao padrão de listagens (SA2 compartilhada por empresa, não por filial operacional).

## 5. S2S CONTRACT — consumo do mecanismo existente

| Elemento | Valor |
|---|---|
| Mecanismo | `DelpiS2SApiGateway` (herda transporte do `DelpiApiGateway`: timeout, request-id, sem retry de escrita) |
| Credencial técnica | Keycloak client `supplies-api`, client credentials, aud `api-delpi` — **já provisionado em produção** |
| Headers | `Authorization: Bearer <user_jwt>` (delegação) + `X-Delpi-Service-Authorization: Bearer <s2s_jwt>` + `X-Delpi-Caller-App: supplies-api` (**telemetria**, nunca identidade) |
| Fallback legado | **proibido** — provider indisponível → `DelpiApiGatewayError` (fail-closed) |
| Decorator api-delpi | `require_s2s_or_any_permission(required_scopes=[...], allowed_clients=["supplies-api"])` — **não** `require_any_permission_or_supplies_bff` (que usa token compartilhado legado + caller self-asserted com superadmin implícito) |
| Scopes técnicos candidatos | `suppliers.read` (lista+detalhe); `suppliers.create`, `suppliers.update` (futuro, gate separado). **Não criados nesta etapa** — dependem de client scope no Keycloak na implementação |
| Permissão de rota (path usuário direto) | read list: reutilizar `api-delpi.access` ou criar `api-delpi.supplies.suppliers.read`? → **UNRESOLVED U-03** (ver §10) |
| JWT usuário | ainda exigido na rota (delegação e auditoria); ausência → negação mesmo com S2S válido |

## 6. SUPPLIER DETAIL CONTRACT — fundação E14 (TARGET, não implementa)

```
api-delpi: GET /integrations/protheus/suppliers/{supplier_id}   (PROVEN)
BFF futura: GET /suppliers/{code}/{store}   → supplier_id = code(6)+store(2) com zeros
```

- `code`/`store` validados por regex no boundary BFF; `supplier_id` 8 dígitos no upstream.
- Erros: `PROTHEUS_SUPPLIER_NOT_FOUND` → BFF 404; sem `supplies.access` → 403; usuário direto api-delpi → `api-delpi.integrations.protheus.read`.
- **DTO BFF de detalhe = projeção curada** do payload upstream (que retorna o `fornecedor` completo do ERP). Seções-alvo da ficha: Identificação, Endereço, Contato, Fiscal, Financeiro/Compras — campo-a-campo mapeado da matriz §44.3 do playbook; campos fora da projeção **não** sobem ao MFE.
- Cache: não definido (freshness de cadastro) → decisão na implementação; E14 não é escopo de E13.

## 7. WRITE EPIC — POST/PUT futuros (TARGET / BLOCKED)

| Item | Estado provado |
|---|---|
| POST `create_protheus_rest_supplier` | código+gates PROVEN; perm `api-delpi.integrations.protheus.suppliers.create`; gate `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`; edge rejeita `codusr`/`user_id`/`usr_id`/`protheus_user_id` do cliente |
| PUT `update_protheus_rest_supplier` | código+gates PROVEN; perm `.suppliers.update`; allowlist code-proven: `supplier_name`(≤50), `supplier_short_name`(≤20); clear/null rejeitado (`PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED`); `acknowledged ≠ persisted` |
| BFF `POST /suppliers` / `PUT /suppliers/{code}/{store}` | candidatos documentados (API-ROUTES.md PLANEJADO); exigem `supplies.access` + S2S scope futuro |
| Bloqueios live | handoff: shape sucesso POST, `A2_COD` gerado, `codusr≡USR_ID`, homologação controlada — **TO_INVENTORY owner TOTVS** |

Regras preservadas: payload só com campos alterados; sem retry automático; persistência conferida por GET posterior; `codusr` sempre via Core; SX3 nunca prova editabilidade REST.

## 8. FIELD / LGPD MATRIX — projeção publicada (E13 lista)

| Campo público | Origem SA2 | Tipo | LGPD | Decisão |
|---|---|---|---|---|
| `supplier_id` | `A2_COD+A2_LOJA` | string 8 | não-pessoal | publish |
| `supplier_code`/`supplier_store` | `A2_COD`/`A2_LOJA` | string | não-pessoal | publish |
| `supplier_name` | `A2_NOME` | string ≤50 | empresa (pessoa jurídica); CPF de PF possível | publish |
| `supplier_short_name` | `A2_NREDUZ` | string ≤20, nullable | idem | publish |
| `tax_id` | `A2_CGC` | string ≤14, nullable | **pessoal quando CPF** (pessoa física) | publish com **masking na UI** (decisão documentada; masking server-side = alternativa se owner LGPD exigir — residual R-01) |
| `state` | `A2_EST` | string 2, nullable | não-pessoal | publish |
| `blocked` | `A2_MSBLQL` | bool | não-pessoal | publish |
| demais 240 campos SA2 | — | — | contém dados pessoais (contato, email, IE) | **não publicar na lista**; detalhe E14 via projeção curada com gate LGPD |

**Política:** minimização — lista expõe só os 8 campos; sem dados de contato pessoal; logs sem `tax_id` completo; `tax_id` de pessoa física tratado como dado pessoal na UI (mask `***.***.**-**`).

## 9. RQ/AC LEDGER (candidatos — IDs a confirmar na promoção)

| RQ | Escopo | AC-chave | Evidência |
|---|---|---|---|
| RQ-SUP-FOR-01 | lista paginada | GET com page/page_size/sort retorna envelope `paged_list` estável | teste rota+registry |
| RQ-SUP-FOR-02 | busca multi-campo | código/loja/nome/fantasia/documento retornam conjuntos corretos; `<2` chars → 422 | teste repo+rota |
| RQ-SUP-FOR-03 | escopo empresa | `A2_FILIAL=''` fixo; empresas 03–05 ausentes; sem filtro unidade artificial | teste SQL gerado |
| RQ-SUP-FOR-04 | AuthZ Core-first | sem `supplies.access` → 403 BFF; superadmin conforme contrato | teste BFF |
| RQ-SUP-FOR-05 | S2S individual | wrong-client/scope/legacy-token → negado; caller-app falsificado não autentica | teste adapter+prod negativo (já provado P1) |
| RQ-SUP-FOR-06 | minimização/LGPD | item contém só 8 campos; `tax_id` mascarado na UI | snapshot contrato + UI test |
| RQ-SUP-FOR-07 | detalhe/ficha | code+store → 8 díg; inexistente → 404; read-only | teste BFF+api-delpi |
| RQ-SUP-FOR-08 | UX estados | loading/empty/error/URL persist | UI tests |
| RQ-SUP-FOR-09/10/11 | write futuro | TARGET — dependências §7 | gates separados |
| RQ-SUP-FOR-12 | help sync | `feature-help-sync` na implementação | doc+teste |

## 10. UNRESOLVED / RESIDUAL

| ID | Item | Owner necessário | Bloqueia contrato? |
|---|---|---|---|
| U-01 | Permissão da rota api-delpi para **acesso usuário direto** à lista (path não-S2S) — reutilizar `api-delpi.access` ou novo código | Arquitetura | não — S2S path já decidido; opção conservadora `api-delpi.access` registrada |
| U-02 | Masking `tax_id` server-side vs UI-only | owner LGPD/produto | não — UI masking é baseline documentado |
| U-03 | Scope técnico `suppliers.read` — criar client scope Keycloak na implementação (não agora) | Infra | não |
| U-04 | `COUNT(*)` custo real em SA2010 com `contains` em `A2_NOME` (índice 2 não cobre contains) | perf DBA/TOTVS | não — monitorar na implementação |
| U-05 | `codusr≡USR_ID` + shape sucesso POST | owner TOTVS | sim — mas só para write epic (fora de E13) |

## 11. TEST MATRIX (definida, não executada nesta etapa)

- **api-delpi**: filtros (state/blocked/query formas), paginação bounds, ordenação estável (tiebreak code+loja), `A2_FILIAL=''` pinned, documento só dígitos, limites 1–100, 401/403/422/503, S2S positive/negative/wrong-client/scope, **sibling LNF intacto**.
- **supplies-api**: autorizado/sem-access/core-down/upstream-error/S2S-token-fail/envelope/DTO-minimizado/timeout/forged-headers → 401.
- **plugins/supplies**: render lista, filtros↔URL, paginação, sort, deep link, estados, a11y, tema, responsivo.
- **Runtime**: smoke federado pós-deploy; coexistência token legado.

## 12. PLUGIN-UI REUSE MATRIX (inventário em HEAD)

Todos os 24 componentes exigidos existem com exports reais (`PageHero`, `BackLink`, `DataTable`, `DataTableSection`, `CompactPagination`, `CatalogSearchBar`, `SelectField`, `ActionButton`, `IconButton`, `FieldLabel`, `HelpTooltip`, `ScreenLoading`, `EmptyState`, `AlertQueue`, `EntityAvatarLabel`, `ModalShell`, `DrawerShell`, `ClearFiltersButton`, `EmptyGuidance`, `InlineLoadingProgress`, `SectionHintLabel`, `TabularExportButtons`, `createDashboardEntityAvatarLabel`). `SuppliesSupplierIdentity` — `EXISTING_EQUIVALENT=YES` em `plugins/supplies/src/app/SuppliesDirectoryIdentity.tsx` → `REUSE`. **Nenhum componente novo necessário para E13.**

## 13. Referências

- [Roadmap fornecedores](./FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md) · [API-ROUTES](./API-ROUTES.md) · [WIREFRAMES](./WIREFRAMES.md) · [DIRECTORY-OBJECTS](./DIRECTORY-OBJECTS.md)
- [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md) · [ADR-010](./adr/ADR-010-s2s-individual-authentication.md) · [padrão S2S](../../11-padroes-de-desenvolvimento/padrao-autenticacao-s2s-individual.md)
- [Contrato REST Protheus](../../../api-delpi/docs/integrations/protheus-rest-supplier-api-contract.md) · [matriz REST→SA2](../../../api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md) · [handoff write](../../../api-delpi/docs/integrations/protheus-rest-supplier-write-handoff.md) · [playbook SA2](../../../api-delpi/docs/api/padroes-totvs/playbooks/playbook-cadastro-fornecedor-sa2.md)
