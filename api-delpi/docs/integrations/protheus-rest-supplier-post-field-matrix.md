# Matriz REST → SA2 — POST fornecedor Protheus

**Registro:** 2026-10-19  
**Fontes:** `protheus-rest-supplier-api-contract.md` (campos do exemplo POST) × playbook SA2 §44.3  
**Estado:** matriz de implementação; **obrigatoriedade REST runtime = TO_INVENTORY** (não promover `CANDIDATE_REQUIRED` a required no DTO).

| Campo REST | business_field (44.3) | Campo SA2 | Tipo/tam. SX3 | Validação API DELPI | Obrigatoriedade | Evidência |
|---|---|---|---|---|---|---|
| `supplier_store` | supplier_store | `A2_LOJA` | C(2) | string 2 dígitos; preserva zeros | **required** (chave parcial do ID REST) | contrato REST + SX3 PROVEN |
| `person_type` | person_type | `A2_TIPO` | C(1) | enum `F\|J\|X` quando informado | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 `pertence("FJX")` |
| `tax_id` | tax_document | `A2_CGC` | C(14) | só dígitos, ≤14; preserva zeros | **DIVERGENCE_UPSTREAM** — chave contratual enviada (comprovado no tracking), mas `A2_CGC` persistiu vazio em `003874/01` (2026-10-21); `003878/01` da F4 havia persistido → suspeita de regressão/comportamento upstream; handoff Gabriel | SX3 + runtime F4/F4.3 |
| `supplier_name` | legal_name | `A2_NOME` | C(50) | trim, ≤50 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `supplier_short_name` | trade_name | `A2_NREDUZ` | C(20) | trim, ≤20 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `address` | street | `A2_END` | C(40) | trim, ≤40 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `district` | district | `A2_BAIRRO` | C(20) | trim, ≤20 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `postal_code` | postal_code | `A2_CEP` | C(8) | dígitos ≤8; preserva zeros | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `state` | state | `A2_EST` | C(2) | uppercase ≤2 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX5 UF |
| `city` | city | `A2_MUN` | C(25) | trim, ≤25 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `city_code` | city_ibge_code | `A2_COD_MUN` | C(5) | dígitos ≤5; preserva zeros | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `area_code` | phone_ddd | `A2_DDD` | C(3) | dígitos ≤3 | TO_INVENTORY (PROVEN_OPTIONAL) | SX3; exemplo REST usa 2 |
| `phone` | phone | `A2_TEL` | C(50) | ≤50 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 OBRIGAT flag |
| `state_registration` | state_registration | `A2_INSCR` | C(18) | ≤18 | TO_INVENTORY (CONDITIONAL) | SX3 |
| `municipal_registration` | city_registration | `A2_INSCRM` | C(18) | ≤18 | TO_INVENTORY (PROVEN_OPTIONAL) | SX3 |
| `contact_name` | contact_person | `A2_CONTATO` | C(15) | ≤15 | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `email` | email | `A2_EMAIL` | C(50) | ≤50, contém `@` se não vazio | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `payment_condition_code` | payment_condition | `A2_COND` | C(3) | ≤3; preserva zeros | TO_INVENTORY (PROVEN_OPTIONAL) | SX3 / SE4 |
| `country_code` | country_code | `A2_PAIS` | C(3) | ≤3 | TO_INVENTORY (PROVEN_OPTIONAL) | SX3 / SYA |
| `bacen_country_code` | country_bacen_code | `A2_CODPAIS` | C(5) | dígitos ≤5; preserva zeros | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `accounting_account` | ledger_account | `A2_CONTA` | C(20) | ≤20; preserva zeros | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `financial_nature_code` | finance_nature | `A2_NATUREZ` | C(10) | ≤10; preserva zeros | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 / SED |
| `rohs_indicator` | rohs_flag | `A2_YROHS` | C(1) | `S\|N` quando informado | TO_INVENTORY (CANDIDATE_REQUIRED; emp 01/05) — enviado no POST bem-sucedido de 2026-10-21, mas obrigatoriedade **não comprovada** (erros upstream nomearam apenas `A2_TEL`, `A2_NATUREZ`, `A2_CODPAIS`) | SX3 DELPI |
| `payment_method_code` | payment_method | `A2_FORMPAG` | C(2) | ≤2; preserva zeros | TO_INVENTORY (CANDIDATE_REQUIRED) | SX3 |
| `codusr` (backend) | — | `SYS_USR.USR_ID` (hipótese) | C(6) | 6 dígitos; **nunca** do cliente | required no upstream | contrato REST; equivalência USR_ID **TO_INVENTORY** |

## PUT — campos editáveis (F3.3, decisão PO)

| Campo REST | SA2 | Status PUT |
|---|---|---|
| `supplier_name` | `A2_NOME` | editável — comprovado no exemplo contratual; C(50) |
| `supplier_short_name` | `A2_NREDUZ` | editável — **PROVEN em runtime** (2026-10-20 e 2026-10-21: persistência SQL `DELPI_TST01` + read-after-write; campos omitidos preservados); C(20) |
| `person_type` | `A2_TIPO` | editável — decisão PO; upstream **pendente** de homologação |
| `address` … `payment_method_code` (19 campos restantes do POST) | conforme tabela acima | editável — decisão PO; upstream **pendente** de homologação |
| `tax_id` | `A2_CGC` | **protegido** — documento fiscal nunca editável (`PROTHEUS_SUPPLIER_FIELD_IMMUTABLE`) |
| `supplier_code`/`supplier_store` | `A2_COD`/`A2_LOJA` | **protegido** — identidade do cadastro |
| `codusr`, `a2_filial`, demais sistema | — | proibidos na rota (`PROTHEUS_IDENTITY_CLIENT_FORBIDDEN`/imutable) |
| omissão | — | campo não entra no array upstream (PUT parcial preserva) |
| string vazia / null | — | rejeitado (`PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED`); limpeza explícita = TO_INVENTORY |

Preservação dos campos omitidos e a aceitação upstream dos campos liberados por decisão PO permanecem **TO_INVENTORY** até homologação TOTVS — o gate `PROTHEUS_SUPPLIER_UPDATE_ENABLED` segue OFF. Sem read-modify-write.

## Campos proibidos no POST desta entrega

| Item | Motivo |
|---|---|
| `A2_COD` / geração de código | SYSTEM_GENERATED no ERP; API DELPI não inventa código |
| `A2_FILIAL` | SYSTEM_GENERATED / contexto ERP |
| Campos `DO_NOT_SEND` da §44.3 | acumuladores/tela/virtuais |
| `codusr` no body do cliente | identidade resolvida via Core |

## Lacunas explícitas

- Payload de sucesso POST e retorno de `A2_COD`: **TO_INVENTORY**.
- Idempotência nativa do upstream: **TO_INVENTORY**.
- Obrigatoriedade efetiva MATA020: **TO_INVENTORY** (não inferida do SX3).
- Equivalência formal `codusr` ≡ `SYS_USR.USR_ID`: **TO_INVENTORY** (bloqueia live write até homologação).
