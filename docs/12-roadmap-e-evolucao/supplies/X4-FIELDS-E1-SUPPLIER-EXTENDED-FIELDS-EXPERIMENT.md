# X4.FIELDS.E1 — Supplier Extended Fields — Local Contract & Homologation Experiment

**Escopo:** `api-delpi` apenas — inventário, protótipo isolado, testes locais, documentação.
**Status:** `LOCAL_EXPERIMENT_PROVEN` — serialização/validação local comprovada para os 35 candidatos; **nenhum campo novo entrou no contrato público**; homologação REST `TEST_NOT_RUN` (sem autorização de escrita).

| Item | Valor |
|---|---|
| BASE HEAD | `6df86f5a32` (pós-S9) |
| Escopo alterado | `api-delpi` — 1 módulo novo + 1 refactor compatível + 1 suite de testes |
| Gate ERP | `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` — **intocados** |

## 1. Autoridades e fontes

- `api-delpi/docs/api/padroes-totvs/cadastro-fornecedor.md` — PUBLIC_DICTIONARY (71 campos mapeados) + convenção de nomenclatura.
- `api-delpi/docs/api/padroes-totvs/playbooks/playbook-cadastro-fornecedor-sa2.md` §44.3 — 248 campos SX3 (REFERENCE_ONLY não enumerados aqui).
- `api-delpi/docs/integrations/protheus-rest-supplier-api-contract.md` — contrato REST do Gabriel + evidências F4/F4.3.
- `api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md` — matriz POST/PUT vigente.
- Código HEAD: `SUPPLIER_FIELD_SPECS` (`protheus_supplier_create_payload.py`), PUT allowlist (`protheus_supplier_update_payload.py`), projeção GET BFF (`supplies-api/suppliers_dto.py::_DETAIL_SECTION_FIELDS`), projeção SQL E13 (`totvs_supplier_repository.py`).

## 2. Inventário — matriz campo a campo

GET = exposto hoje (seção BFF detail; list = só campos E13). POST/PUT = allowlist vigente. Candidato = entra no experimento local. Classificação `PROVEN|TO_INVENTORY|PLANNED|TARGET` refere-se à evidência de **persistência/aceite upstream**, não à existência física.

### Contrato vigente (24 POST / 22 PUT / 26 GET)

| Campo SA2 | Campo DELPI | GET | POST | PUT | Candidato | Evidência | Classificação |
|---|---|---|---|---|---|---|---|
| A2_LOJA | supplier_store | ✓ | required | protegido | — | contrato+SX3 | PROVEN |
| A2_TIPO | person_type | ✓ | ✓ | ✓ | — | SX3 enum | PROVEN |
| A2_CGC | tax_id | ✓(mask CPF) | ✓ | imutável | — | SX3; **divergência upstream** (persistiu vazio em 003874; funcionou em 003878) | PROVEN+TO_INVENTORY |
| A2_NOME | supplier_name | ✓ | ✓ | ✓ | — | PUT persistido F4 | PROVEN |
| A2_NREDUZ | supplier_short_name | ✓ | ✓ | ✓ | — | PUT persistido F4/F4.3 | PROVEN |
| A2_END | address | ✓ | ✓ | ✓ | — | SX3 | PROVEN local / PEND homolog |
| A2_BAIRRO | district | ✓ | ✓ | ✓ | — | PUT persistido F4 | PROVEN |
| A2_CEP | postal_code | ✓ | ✓ | ✓ | — | SX3 | PROVEN local |
| A2_MUN | city | ✓ | ✓ | ✓ | — | SX3 | PROVEN local |
| A2_COD_MUN | city_code | ✓ | ✓ | ✓ | — | SX3/CC2 | PROVEN local |
| A2_EST | state | ✓ | ✓ | ✓ | — | SX3/SX5-12 | PROVEN |
| A2_PAIS | country_code | ✓ | ✓ | ✓ | — | SX3/SYA | PROVEN local |
| A2_CODPAIS | bacen_country_code | ✓ | ✓ | ✓ | — | OBRIGAT upstream F4 | PROVEN |
| A2_INSCR | state_registration | ✓ | ✓ | ✓ | — | SX3/IE() | PROVEN local |
| A2_INSCRM | municipal_registration | ✓ | ✓ | ✓ | — | SX3 | PROVEN local |
| A2_CONTATO | contact_name | ✓ | ✓ | ✓ | — | PUT persistido F4 | PROVEN |
| A2_DDD | area_code | ✓ | ✓ | ✓ | — | SX3 | PROVEN local |
| A2_TEL | phone | ✓ | ✓ | ✓ | — | OBRIGAT upstream F4 | PROVEN |
| A2_EMAIL | email | ✓ | ✓ | ✓ | — | SX3 | PROVEN local |
| A2_COND | payment_condition_code | ✓ | ✓ | ✓ | — | PUT persistido F4 | PROVEN |
| A2_FORMPAG | payment_method_code | ✓ | ✓ | ✓ | — | SX3/SX5-58 | PROVEN local |
| A2_CONTA | accounting_account | ✓ | ✓ | ✓ | — | SX3/CT1 RESTRICTED | PROVEN local |
| A2_NATUREZ | financial_nature_code | ✓ | ✓ | ✓ | — | OBRIGAT upstream F4 | PROVEN |
| A2_YROHS | rohs_indicator | ✓ | ✓ | ✓ | — | PUT persistido F4 | PROVEN |

### Campos candidatos à expansão — Classe A (cadastrais de negócio)

Todos: POST/PUT atuais = **não** (fora da allowlist); GET atual = não expostos. Teste local `PASS` em todos (spec + serialização + rejeições); REST homologação `TEST_NOT_RUN`; persistência `INCONCLUSIVE`.

| Campo SA2 | Campo DELPI | Tipo/tam | Validação SX3 | Lookup | Decisão local |
|---|---|---|---|---|---|
| A2_NR_END | address_number | C6 | — | — | candidato PASS |
| A2_CX_POST | po_box | C5 | — | — | candidato PASS |
| A2_CONTRIB | icms_contributor | C1 | Pertence(' 12') | — | candidato PASS (enum) |
| A2_SIMPNAC | simples_nacional | C1 | Pertence(' 12') | — | candidato PASS (enum) |
| A2_CNAE | cnae_code | C9 | WHEN TIPO J/X | — | candidato PASS + **regra condicional implementada** |
| A2_TPJ | legal_entity_type | C1 | Pertence(' 12345') | — | candidato PASS (`NEEDS_REVIEW` semântica SX3) |
| A2_TPESSOA | person_category | C2 | — | — | candidato PASS (99,9% vazio — baixa prioridade) |
| A2_REGESIM | simp_regime_code | C1 | — | — | candidato PASS (default SX3 "2") |
| A2_REGPB | pb_regime_code | C1 | Pertence(' 12') | — | candidato PASS |
| A2_RECINSS | inss_withholding | C1 | pertence('SN') | — | candidato PASS (enum) |
| A2_RECISS | iss_withholding | C1 | Pertence('SN ') | — | candidato PASS (enum) |
| A2_RECCSLL | csll_withholding | C1 | Pertence('12') | — | candidato PASS (enum; default "1") |
| A2_RECCOFI | cofins_withholding | C1 | Pertence('12') | — | candidato PASS (enum; default "1") |
| A2_RECPIS | pis_withholding | C1 | Pertence('12') | — | candidato PASS (enum; default "1") |
| A2_CALCIRF | irf_calculation | C1 | Pertence('1234') | — | candidato PASS (enum) |
| A2_CALCINP | inp_calculation | C1 | Pertence('12') | — | candidato PASS (enum) |
| A2_GRPTRIB | tax_group_code | C3 | — | — | candidato PASS |
| A2_CATEFD | esocial_category_code | C3 | — | S049BR | candidato PASS |
| A2_CONTCOM | commercial_contact_name | C15 | — | — | candidato PASS |
| A2_DDI | country_calling_code | C6 | ExistCpo('ACJ') | ACJ | candidato PASS |
| A2_FAX | fax | C15 | — | — | candidato PASS (digits) |
| A2_HPAGE | website | C30 | — | — | candidato PASS |
| A2_NOMRESP | responsible_name | C45 | — | — | candidato PASS |
| A2_RISCO | risk_code | C3 | — | — | candidato PASS |
| A2_SWIFT | swift_code | C30 | — | — | candidato PASS (upper) |
| A2_CODFAV | payee_code | C6 | ExistCpo('SA2') | SA2 | candidato PASS |
| A2_LOJFAV | payee_store | C2 | ExistCpo('SA2', cod+loja) | SA2 | candidato PASS |
| A2_YFGEN | generic_supplier | C1 | — (DELPI) | — | candidato PASS (sem enum definido no SX3 — TO_INVENTORY) |
| A2_ZTABPRC | purchase_price_table_code | C3 | — | AIA | candidato PASS (DELPI) |
| A2_TRANSP | carrier_code | C6 | existcpo('SA4') | SA4 | candidato PASS |
| A2_SATIV1 | segment_code | C6 | ExistCpo('SX5','T3'+) | SX5-T3 | candidato PASS |
| A2_VINCULO | link_type_code | C2 | ExistCpo('CC1') | CC1 | candidato PASS |
| A2_CODADM | administrator_code | C3 | ExistCpo('SAE') | SAE | candidato PASS |
| A2_CLIENTE | linked_customer_code | C6 | ExistCpo('SA1') | SA1 | candidato PASS |
| A2_LOJCLI | linked_customer_store | C2 | ExistCpo('SA1', par) | SA1 | candidato PASS |
| A2_NUMRA | linked_employee_code | C6 | ExistCpo('SRA')+regra | SRA | candidato PASS |

### Classe B — somente consulta (potencial E14, sem intenção de escrita)

Nenhum campo de escrita nesta classe foi identificado como candidato read-only adicional nesta rodada — os campos somente-leitura úteis à E14 hoje são `supplier_code`/`supplier_store`/`blocked`/`tax_id`, já expostos. Acumuladores (`A2_LC` etc.) permanecem classe D.

### Classe C — gerados pelo Protheus (nunca enviados)

| Campo | SA2 | Motivo |
|---|---|---|
| branch | A2_FILIAL | SYSTEM_GENERATED; branco=compartilhado |
| supplier_code | A2_COD | SYSTEM_GENERATED (GETSXENUM); nunca gerar MAX+1 |
| blocked | A2_MSBLQL | SYSTEM_GENERATED/RESTRICTED |

### Classe D — técnicos/estatísticos (fora de contrato público)

| Campo | SA2 | Motivo |
|---|---|---|
| credit_limit_amount | A2_LC | DO_NOT_SEND — acumulador |
| demais ~177 campos | REFERENCE_ONLY §44.3 | estatísticos/técnicos/outros módulos |

### Classe E — sensíveis (bloqueados sem classificação LGPD/minimização)

| Campo | SA2 | Motivo |
|---|---|---|
| bank_code | A2_BANCO | dado bancário |
| bank_branch | A2_AGENCIA | dado bancário |
| bank_branch_digit | A2_DVAGE | dado bancário |
| bank_account | A2_NUMCON | dado bancário |
| bank_account_digit | A2_DVCTA | dado bancário |
| bank_account_type | A2_TIPCTA | sensível + NEEDS_REVIEW (A2_TIPCTA×A2_TPCONTA) |

### Classe F — outro contexto / pendente de owner

| Campo | SA2 | Motivo |
|---|---|---|
| group_code | A2_GRUPO | 0% povoado; grupos reais em **SAD** — outra autoridade |
| address_complement | A2_ENDCOMP | NEEDS_REVIEW — conflito físico A2_ENDCOMP×A2_COMPLEM (decisão do owner antes de expor) |

## 3. Protótipo local implementado

`api-delpi/app/application/services/integrations/protheus_supplier_extended_fields.py` — **não importado por nenhuma rota/use case**:

- `SUPPLIER_EXTENDED_FIELD_SPECS` — 35 specs (max, digits, enum, upper, conditional).
- `EXPERIMENTAL_SUPPLIER_FIELD_SPECS` — merged com a tabela publicada (readonly para validação).
- `EXPERIMENTAL_POST_ALLOWLIST` / `EXPERIMENTAL_PUT_ALLOWLIST` — PUT espelha a regra F3.3 (exceto `tax_id`/`supplier_store`).
- `EXPERIMENTAL_BLOCKED_FIELDS` — classes C/D/E/F documentadas em código.
- `normalize_experimental_supplier_fields` — mesma semântica do normalizador canônico (unknown→422, identity→422, omitido→omitido, string-only, digits, enum, max) **+ regra condicional CNAE×person_type** (rejeita `person_type=F` + `cnae_code` → `PROTHEUS_SUPPLIER_FIELD_CONDITIONAL`).
- `build_upstream_create_body_experimental` — shape canônico `{codusr, fornecedor:{}}`.

Refactor compatível em `protheus_supplier_create_payload.py`: `normalize_supplier_field_value(field, value, *, specs=None)` — parâmetro opcional que permite ao experimento reutilizar **a mesma** normalização canônica com a tabela ampliada; o contrato público permanece `SUPPLIER_FIELD_SPECS` por padrão. Zero mudança de comportamento no caminho real.

## 4. Resultados

### LOCAL TEST RESULTS — `tests/test_protheus_supplier_extended_fields.py` (55 testes, PASS)

| Comprovação | Resultado |
|---|---|
| Payload atual (24 campos) idêntico entre publicado e experimental | PASS |
| Cada um dos 35 candidatos serializa/normaliza corretamente (parametrizado) | PASS |
| 9 casos inválidos rejeitados (enum, digits, length) | PASS |
| Tipos numéricos rejeitados (zeros à esquerda) | PASS |
| CNAE condicional: F rejeita, J/X aceitam | PASS |
| Opcionais omitidos permanecem omitidos | PASS |
| Bloqueados (E/C/F) + desconhecidos rejeitados | PASS |
| `codusr`/identidade do cliente rejeitados | PASS |
| Allowlist publicada **continua rejeitando** os 35 candidatos (contrato não alargado silenciosamente) | PASS |
| PUT experimental exclui `tax_id`/`supplier_store`/`supplier_code` | PASS |

Regressão do caminho real: 37 testes (create/update payload, use cases, routes) — **PASS**.

### REST HOMOLOGATION RESULTS

`TEST_NOT_RUN` — nenhuma escrita autorizada; ambiente REST já diverge da base SQL produtiva (`REST_SQL_BASE_DIVERGENCE=BLOCKED`, contrato §3.4).

### PERSISTENCE EVIDENCE

`TEST_NOT_RUN` — HTTP 200 não é evidência; sem ensaio autorizado nenhum campo é promovido.

## 5. Matriz de decisão

| Campo | Teste local | REST homologação | Persistência | Decisão |
|---|---|---|---|---|
| 24 do contrato vigente | PASS | parcial F4/F4.3 | PROVEN (6 PUT + POST obrigatórios) | Manter |
| 35 candidatos classe A | PASS | TEST_NOT_RUN | INCONCLUSIVE | **Candidato** — plano posterior |
| 7 bancários (classe E) | — | TEST_NOT_RUN | INCONCLUSIVE | **Bloqueado** — classificação LGPD primeiro |
| address_complement | — | TEST_NOT_RUN | INCONCLUSIVE | **Bloqueado** — NEEDS_REVIEW owner |
| group_code | — | TEST_NOT_RUN | INCONCLUSIVE | **Bloqueado** — contexto SAD |
| system/DO_NOT_SEND | — | — | — | **Bloqueado** permanente |

## 6. Riscos e gaps

- `generic_supplier` (A2_YFGEN) sem enum SX3 documentado — valores aceitos `TO_INVENTORY`.
- `person_category`/`legal_entity_type`/`simp_regime_code`/`pb_regime_code`/`address_complement`/`bank_account_type` = `NEEDS_REVIEW` no dicionário — semântica a congelar antes de publicar.
- Campos condicionais além de CNAE não foram detectados na WHEN do SX3 — revisar playbook §28 antes da homologação.
- Lookups (SA6/SA4/SED/CT1/SX5) não são validados localmente — upstream rejeita código inexistente; ensaio deve escolher valores reais.
- Divergência `tax_id` (não persistiu em 003874) segue `TO_INVENTORY` com o owner upstream — independente desta expansão.
- `REST_SQL_BASE_DIVERGENCE=BLOCKED` impede qualquer promessa de escrita produtiva.

## 7. Recomendações

**Para E14 (consulta):** os 35 candidatos podem ser avaliados para leitura — o upstream GET já devolve o objeto completo; ampliar `_DETAIL_SECTION_FIELDS` no BFF é decisão de contrato posterior (precisa de inventário do que o GET realmente ecoa).

**Para criação/edição:** nenhum campo entra no contrato público antes de (1) contract evolution aprovada (DTO/OpenAPI), (2) ensaio de homologação autorizado com fornecedor fictício + read-after-write + reconciliação, (3) owner Protheus confirmando resolução da divergência de ambiente REST×SQL.

**Próximos gates:** E1.H1 (ensaio homologação, **NOT_AUTHORIZED**) → contract design público → expansão do Portal.
