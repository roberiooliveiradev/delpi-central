# X4.FIELDS.E3 — Expansão Full-Stack de Campos de Fornecedor

**Data:** 2026-10-23
**Autorização:** Product Owner — implementação full-stack nos owners corretos, com testes e documentação. **Não autorizado:** deploy produtivo, ativação de escrita Protheus, POST/PUT real, ampliação de permissões, escrita direta na SA2, promoção sem evidência, alteração das conexões DELPI/DELPI_TST01.
**Status:** `ACCEPT_WITH_RESIDUAL`

## 1. Baseline e rastreabilidade

| Item | Valor |
|---|---|
| Base HEAD | `12a142877d` (X4.FIELDS.E2) |
| Referências | E2 `12a142877d`; revisão arquitetural E2 `d8e3818609` |
| Owners tocados | `api-delpi`, `supplies-api`, `plugins/supplies` |
| Escrita ERP executada | **nenhuma** — implementação + testes locais apenas |

## 2. E3.P0 — Congelamento da matriz (programático)

Reconciliação executada contra os conjuntos reais — **não** contra contagens documentais. `COUNT_DRIFT` do E1 resolvido:

| Conjunto | Cardinalidade | Conteúdo |
|---|---|---|
| `PUBLISHED_POST_FIELDS` (antes) | 24 | `SUPPLIER_FIELD_SPECS` pré-E3 |
| `EXPERIMENTAL_ONLY_FIELDS` (após) | 7 | 4 IGNORED + 3 TEST_NOT_RUN |
| `PERSISTENCE_PROVEN_FIELDS` | 29 | ver §3 — evidência E2 lote a lote |
| `IGNORED_FIELDS` | 4 | `person_category`, `payee_code`, `payee_store`, `generic_supplier` |
| `TEST_NOT_RUN_FIELDS` | 3 | `country_calling_code`, `link_type_code`, `esocial_category_code` |
| `PROTECTED_FIELDS` (PUT) | 3 | `tax_id`, `supplier_code`, `supplier_store` |
| `PUT_HOMOLOGATED_FIELDS` | 22 | allowlist F3.3 congelada — **inalterada** |

Soma verificada: 36 candidatos E1 = 29 PERSISTED + 4 IGNORED + 3 TEST_NOT_RUN. Zero duplicação entre `SUPPLIER_FIELD_SPECS` (api-delpi), `SUPPLIER_EXTENDED_FIELD_SPECS`, `POST_SUPPLIER_FIELDS`/`PUT_SUPPLIER_FIELDS` (BFF) e `SUPPLIER_FIELD_REGISTRY` (MFE).

**Derivação perigosa neutralizada:** antes do E3, `_UPDATE_SPECS` derivava de `SUPPLIER_FIELD_SPECS` menos documento/identidade — promover os 29 abriria PUT sem homologação. A allowlist PUT foi congelada em constante explícita (`PUT_EDITABLE_FIELDS`) **antes** da promoção. O mesmo congelamento foi aplicado em `PUT_SUPPLIER_FIELDS` (BFF) e `SUPPLIER_PUT_EDITABLE_KEYS`/`SupplierEditableFieldKey` (MFE, via `SupplierPostOnlyFieldKey` excluído da derivação).

## 3. Campos promovidos (29) — evidência E2

| Campo | Coluna SA2 | Lote E2 | Seção UX |
|---|---|---|---|
| `address_number` | A2_NR_END | 1a | address |
| `po_box` | A2_CX_POST | 1a | address |
| `icms_contributor` | A2_CONTRIB | 1a | fiscal |
| `simples_nacional` | A2_SIMPNAC | 1a | fiscal |
| `inss_withholding` | A2_RECINSS | 1b | fiscal |
| `iss_withholding` | A2_RECISS | 1b | fiscal |
| `csll_withholding` | A2_RECCSLL | 1b | fiscal |
| `cofins_withholding` | A2_RECCOFI | 1b | fiscal |
| `pis_withholding` | A2_RECPIS | 1b | fiscal |
| `irf_calculation` | A2_CALCIRF | 1b | fiscal |
| `inp_calculation` | A2_CALCINP | 1b | fiscal |
| `tax_group_code` | A2_GRPTRIB | 1b | fiscal |
| `commercial_contact_name` | A2_CONTCOM | 1c | contact |
| `fax` | A2_FAX | 1c | contact |
| `website` | A2_HPAGE | 1c | contact |
| `responsible_name` | A2_NOMRESP | 1c | contact |
| `risk_code` | A2_RISCO | 1c | purchasing |
| `swift_code` | A2_SWIFT | 1c | purchasing |
| `cnae_code` | A2_CNAE | 2 | fiscal |
| `legal_entity_type` | A2_TPJ | 2 | identification |
| `simp_regime_code` | A2_REGESIM | 2 | fiscal |
| `pb_regime_code` | A2_REGPB | 2 | fiscal |
| `carrier_code` | A2_TRANSP | 3 | purchasing |
| `segment_code` | A2_SATIV1 | 3 | purchasing |
| `administrator_code` | A2_CODADM | 3 | purchasing |
| `linked_customer_code` | A2_CLIENTE | 3 | purchasing |
| `linked_customer_store` | A2_LOJCLI | 3 | purchasing |
| `linked_employee_code` | A2_NUMRA | 3 | purchasing |
| `purchase_price_table_code` | A2_ZTABPRC | 4 | purchasing |

## 4. Capacidade por campo (READ × CREATE × EDIT)

Capacidades separadas formalmente — `creatable` **não** implica `editable`.

| Conjunto | READ (GET) | CREATE (POST) | EDIT (PUT) |
|---|---|---|---|
| 24 campos F3.3 | READABLE | CREATE_ENABLED_BY_CONTRACT | 22 PUT homologados* + 2 PROTECTED |
| 29 campos E3 | READABLE** | CREATE_ENABLED_BY_CONTRACT | **EDIT_CANDIDATE_NOT_HOMOLOGATED** |
| 4 IGNORED | UNAVAILABLE | — | — |
| 3 TEST_NOT_RUN | UNAVAILABLE | — | — |
| bancários/LGPD, acumuladores, system, outros owners | UNAVAILABLE | — | — |

\* upstream PUT homologado apenas para `supplier_name`/`supplier_short_name`; o restante da allowlist F3.3 é decisão funcional do PO (`po-decision`) com gate de escrita OFF — mesma postura preservada.
\*\* inventário GET executado no E3.S1: REST GET de `003877/01` (TST01) retorna os 29 campos; a projeção pública permanece curada no BFF (E3.S2) — ausência upstream nunca vira valor inventado.

Modelo auditável: `evidence` no `SUPPLIER_FIELD_REGISTRY` (`put-contract` / `po-decision` / `post-matrix`) + `put: editable|readonly|protected`.

## 5. Implementação por owner

### E3.S1 — api-delpi

- `protheus_supplier_create_payload.py`: 29 specs SX3 promovidas ao `SUPPLIER_FIELD_SPECS` canônico (max/enum/digits/upper/`conditional: person_type_jx` para `cnae_code`). Regra condicional generalizada no normalizador publicado.
- `protheus_supplier_update_payload.py`: `PUT_EDITABLE_FIELDS` explícito (22, F3.3) — derivação removida; `_UPDATE_SPECS` montado a partir da allowlist congelada; `_IMMUTABLE_FIELDS`/`_FORBIDDEN_IDENTITY` preservados; clear explícito continua rejeitado (`PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED`).
- `protheus_supplier_extended_fields.py`: reduzido aos 7 sem evidência + `EXPERIMENTAL_BLOCKED_FIELDS`; `EXPERIMENTAL_*` deriva do canônico — **uma fonte de specs, zero duplicação**.
- GET: pass-through upstream; BFF é o owner da minimização (sem nova projeção interna).

### E3.S2 — supplies-api

- `suppliers_dto.py`: `POST_SUPPLIER_FIELDS` += 29; `PUT_SUPPLIER_FIELDS` congelado em 22 com comentário E3; `_DETAIL_SECTION_FIELDS` estendido — os 29 distribuídos nas 5 seções canônicas (identification/address/contact/fiscal/purchasing). LGPD minimization preservada; `tax_id` CPF segue mascarado.
- Testes: filtros POST/PUT, outcome de escrita, projeção de detalhe — **438 pass / 21 skip**.

### E3.S3 — plugins/supplies

- `types.ts`: `SupplierCreateDraft` += 29 chaves; `SupplierPostOnlyFieldKey` (união das 29) excluído de `SupplierEditableFieldKey` — type-level impede edit sem homologação; `SUPPLIER_FIELD_REGISTRY` += 29 specs `F()` (`get:"section"`, `put:"readonly"`, `evidence:"post-matrix"`) com labels PT, spans, `digitsOnly`/`uppercase`, enums como `options` e `help` contextual.
- `SupplierCreatePage.tsx`: `EMPTY_DRAFT` += 29 — renderização, seções, revisão e `buildCreateFornecedor` são registry-driven (sem tela nova, sem bloco único desorganizado: identification 1 / address 2 / contact 4 / fiscal 13 / purchasing 9).
- `userManualContent.ts`: FAQ ampliada — seções do formulário + resposta nova sobre campos somente-leitura na edição.
- Catálogos: **nenhum inventado** — os 7 campos de referência (`carrier_code`, `segment_code`, `administrator_code`, `linked_customer_code`, `linked_customer_store`, `linked_employee_code`, `purchase_price_table_code`, `tax_group_code`) ficam como input com help que registra a pendência de catálogo contratado.
- Testes: bloco dedicado E3 (5 casos) + 2 fixtures atualizadas — **370 pass**; `tsc -b` limpo; `vite build` OK; eslint escopado 0 problemas novos.

## 6. E3.S4 — Matriz de preparação PUT (sem escrita)

`PUT_EXTENDED_FIELDS = NOT_AUTHORIZED`. Nenhum dos 29 entrou em allowlist de edição em nenhuma camada.

| FIELD | UPSTREAM PUT SUPPORT | EXPECTED PAYLOAD | VALIDATION | READ_AFTER_WRITE | OMITTED PRESERVATION | CLEAR VALUE | ROLLBACK/RESIDUAL | STATUS |
|---|---|---|---|---|---|---|---|---|
| (todos os 29) | TO_INVENTORY — chave REST por confirmar com Gabriel | `fornecedor` objeto + `codusr` (shape F4 provado) | specs SX3 já canônicas | SQL TST01 + REST GET por coluna SA2 | omitido = não enviado (parcial OK) | `CLEAR_NOT_SUPPORTED` vigente | fornecedor `ZZ HOMOLOG E4*` + cleanup TST01 | `NOT_AUTHORIZED` |

Execução da homologação PUT exige tarefa separada autorizada pelo PO contra `DELPI_TST01`, mesmos gates do E2 (actor `codusr`, tracking, read-after-write, verificação DELPI).

## 7. Contratos e impacto

| Camada | Antes | Depois | Compatibilidade |
|---|---|---|---|
| api-delpi POST allowlist | 24 | **53** | aditiva — campos novos opcionais |
| api-delpi PUT allowlist | 22 | **22** (explícita) | inalterada |
| BFF POST allowlist | 24 | **53** | aditiva |
| BFF PUT allowlist | 22 | **22** | inalterada |
| BFF detail sections | ~26 chaves | **+29** | aditiva |
| MFE registry | ~30 specs | **+29** | aditiva |

Descoberta E2 incorporada ao contrato: upstream exige `rohs_indicator`, `accounting_account`, `bacen_country_code`, `payment_method_code`, `financial_nature_code`, `payment_condition_code` — **não** declarados `required` isoladamente: a rejeição veio de payload incompleto, e a obrigatoriedade formal por perfil de fornecedor permanece `TO_INVENTORY` (handoff Gabriel).

## 8. Segurança e conformidade

- AuthZ server-side inalterada (`supplies.access`); **zero permission nova**; escopo unidade/recurso preservado.
- `PROTHEUS_SUPPLIER_CREATE_ENABLED=false` e `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` — confirmados pós-implementação.
- Identidade Protheus (`codusr`) continua backend-resolved; `_FORBIDDEN_IDENTITY` rejeita identidade client-supplied em POST e PUT.
- LGPD: CPF mascarado na projeção BFF; campos bancários seguem bloqueados (`EXPERIMENTAL_BLOCKED_FIELDS`).
- Zero SQL direto na SA2; zero chamada upstream nesta etapa; zero deploy.
- Tracking/outcomes preservados; `persistence_confirmed` continua exigindo evidência, não ACK.

## 9. Testes executados

| Suíte | Resultado |
|---|---|
| api-delpi contratos/use case (create+update+extended) | **122 pass** |
| supplies-api | **438 pass / 21 skip** (skips env-dependent, pré-existentes) |
| plugins/supplies vitest | **370 pass** (43 arquivos) |
| plugins/supplies tsc -b + vite build | **PASS** |
| eslint escopado (arquivos E3) | **0 problemas** — os 13 erros/21 warnings do plugin são pré-existentes em outros arquivos |
| Smoke federado | `TEST_NOT_RUN` — não declarado sem execução real |

Regressão externa pré-existente: `test_davi_product_master_extensions` (94→95 actions) — drift não relacionado, falha na base limpa.

## 10. Residuais (`TO_INVENTORY` / `UNRESOLVED`)

1. **PUT homologation** — os 29 campos são `EDIT_CANDIDATE_NOT_HOMOLOGATED`; homologação dedicada em `DELPI_TST01` aguarda autorização (matriz §6 pronta).
2. **4 campos IGNORED upstream** — `person_category`, `payee_code`/`payee_store`, `generic_supplier`: confirmar nomes REST com Gabriel/TOTVS.
3. **3 campos TEST_NOT_RUN** — `country_calling_code` (ACJ), `link_type_code` (CC1) sem massa em TST01; `esocial_category_code` (S049BR) semântica de owner pendente.
4. **Catálogos de referência** — 8 campos sem seletor contratado (registrado no help; sem catálogo inventado).
5. **Obrigatórios upstream por perfil** — regra formal dos 6 campos exigidos não foi isolada por tipo de fornecedor.
6. **Resíduos TST01** — 7 fornecedores `ZZ HOMOLOG E2*` permanecem como evidência; política de bloqueio `A2_MSBLQL` herdada.
7. **`tax_id` silencioso** — upstream descarta CNPJ com DV inválido sem erro; handoff Gabriel registrado (E2).

## 11. Próxima etapa

- `E4` (deployment): deploy dos 3 owners via fluxo canônico local→push→pull, com smoke federado autenticado — **não executado nesta etapa**.
- Homologação PUT dedicada (autorização PO) → promoção `EDIT_HOMOLOGATED` campo a campo.
