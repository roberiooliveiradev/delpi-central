# X4.FIELDS.E6 — Supplier Editing Completion & Reference Catalogs

**Data:** 2026-10-23 · **Status:** `ACCEPT_WITH_RESIDUAL`
**Owner de implementação:** Portal Suprimentos (`api-delpi` → `supplies-api` → `plugins/supplies`)
**Autorização PO:** implementação, testes locais, consultas aos catálogos TOTVS, ensaio controlado de PUT exclusivamente em `DELPI_TST01`, documentação e deploy canônico. **Não autorizado:** escrita em `DELPI`, ativação permanente de escrita Protheus, SQL INSERT/UPDATE/DELETE, novas permissões, alteração de identidades, fabricação de massa SA1/SA2, publicação de campo sem contrato/evidência.

---

## 1. Objetivo

Concluir a experiência de cadastro e edição de fornecedores:

1. Resolver os três campos PUT pendentes de E5 (`simp_regime_code`, `linked_customer_code`, `linked_customer_store`).
2. Substituir inputs de códigos Protheus por seleção assistida `código — descrição` onde houver catálogo válido.
3. Reutilizar os mesmos controles na inclusão (novo fornecedor) e na edição (E14).

## 2. Rebaseline

- HEAD base: `2808ceb9ce` (E5) + `b3a7644191` (review doc E5).
- Gates produtivos confirmados OFF antes e depois: `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false`.
- Alvos de ensaio: REST `ambiente:1@192.168.1.233:8701` · SQL `DELPI_TST01` · `DELPI` fora do alvo em todas as operações.
- Registry único preservado: `SUPPLIER_FIELD_REGISTRY` — nenhum segundo registry criado.

## 3. E6.P0 — Matriz de contrato (campos pendentes + catálogos)

### 3.1 Campos PUT pendentes

| FIELD | SA2_COLUMN | OWNER | LOOKUP_TABLE | KEY_STRUCTURE | BRANCH_SCOPE | REST_GET | REST_POST | REST_PUT | VALIDATION | AUTHZ | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `simp_regime_code` | `A2_REGESIM` | api-delpi | — (enum SX3 CBOX) | escalar | n/a | OK | OK | **PROVEN (6a)** | CBOX `{1=Sim;2=Não}` | `supplies.access` | put-homologated | **EDITABLE** |
| `linked_customer_code` | `A2_CLIENTE` | api-delpi | SA1 | par composto c/ `A2_LOJCLI` | `A1_FILIAL=''` | OK | OK | **IGNORED (6d)** | código ∈ SA1 | `supplies.access` | post-matrix | **READONLY** (companion) |
| `linked_customer_store` | `A2_LOJCLI` | api-delpi | SA1 | par composto c/ `A2_CLIENTE` | `A1_FILIAL=''` | OK | OK | **PROVEN (6c)** | loja ∈ SA1 do código vigente | `supplies.access` | put-homologated | **EDITABLE** (via par) |

### 3.2 Catálogos inventariados

| CATALOG | TABELA | KEY_STRUCTURE | BRANCH_SCOPE | FIELD(S) | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|
| `carriers` | SA4010 | `A4_COD` | `A4_FILIAL=''` | `carrier_code` | X3_F3 `SA4` | IMPLEMENTED |
| `segments` | SX5010 (`X5_TABELA='T3'`) | `X5_CHAVE` | `X5_FILIAL=''` | `segment_code` | X3_F3 `T3` | IMPLEMENTED |
| `administrators` | SAE010 | `AE_COD` | `AE_FILIAL=''` | `administrator_code` | X3_F3 `SAE` | IMPLEMENTED |
| `customers` | SA1010 | `A1_COD`+`A1_LOJA` (composta) | `A1_FILIAL=''` | `linked_customer_code`, `linked_customer_store` | SA1 TST01 257 registros | IMPLEMENTED |
| `employees` | SRA010 | `RA_MAT` | `RA_FILIAL IN ('','01')` | `linked_employee_code` | evidência E2 | IMPLEMENTED |
| `price-tables` | AIA010 | `AIA_CODTAB` | `AIA_FILIAL IN ('','01')` | `purchase_price_table_code` | X3_F3 `AIA` | IMPLEMENTED |
| `tax-groups` (`A2_GRPTRIB`) | de-para incerto | — | — | `tax_group_code` | sem tabela TOTVS confirmada | **BLOCKED** — handoff owner TOTVS |
| `risk-codes` (`A2_RISCO`) | sem X3_F3 | — | — | `risk_code` | sem lookup confirmado | **BLOCKED** — permanece input honesto |
| `legal-entity-types` (`A2_TIPRJ`) | enum SX3 CBOX | — | — | `legal_entity_type` | CBOX domínio fechado | IMPLEMENTED (enum estático, não catálogo) |

Catálogos pré-existentes preservados: `states`, `countries`, `bacen-countries`, `payment-conditions`, `payment-methods`, `financial-natures`, `accounting-accounts`, `municipalities`.

## 4. E6.S1 — Reteste PUT em DELPI_TST01 (script `protheus_supplier_put_extended_homologation.py`, lotes 6a–6d)

| Lote | Registro | Operação | Resultado |
|---|---|---|---|
| 6a | `003879/01` | PUT `simp_regime_code: "1"→"2"` | **PASS** — REST read-back = `2`, SQL `A2_REGESIM='2'`. **PUT_PERSISTENCE_PROVEN** |
| 6b | `003882/01` | PUT `linked_customer_code: "000002"` (sozinho) | upstream **400** — código isolado rejeitado |
| 6c | `003882/01` | PUT par `{code:"000001", store:"06"}` | **PASS** — `A2_LOJCLI` persistiu `"06"` (REST+SQL). **PUT_PERSISTENCE_PROVEN** |
| 6d | `003882/01` | PUT par `{code:"000002", store:"01"}` | `A2_CLIENTE` **inalterado** (upstream ignora novo código no par); loja seguiu o par. **Código = PUT_IGNORED para alteração** |

Descoberta de inventário: SA1 TST01 tem **257 clientes** (E5 supôs apenas `000001`) — `000002/01` (EBERLE) é referência válida e foi usada como prova de ignorância upstream, sem fabricação de massa.

### Semântica final do par composto

- `linked_customer_store` sozinha é **ignorada** upstream — a loja só persiste quando o par viaja junto.
- `linked_customer_code` **nunca** é alterável via PUT — enviado divergente, é silenciosamente ignorado (6d).
- Contrato adotado: a loja é editável; o código viaja como **companion imutável** injetado pela `api-delpi` a partir do cadastro vigente (REST GET); divergência enviada pelo cliente é rejeitada com `PROTHEUS_SUPPLIER_LINKED_CUSTOMER_IMMUTABLE` (422).
- Fornecedor sem cliente vinculado: loja rejeitada com `PROTHEUS_SUPPLIER_LINKED_CUSTOMER_REQUIRED` — não se cria vínculo via edição.
- Código sozinho (sem loja) rejeitado no normalizador: `PROTHEUS_SUPPLIER_LINKED_PAIR_REQUIRED` (422).

## 5. E6.S2 — Catálogos `api-delpi`

Fonte canônica estendida: `totvs_supplier_catalogs_repository.py` (`_SOURCES` +6 kinds), `catalog_supports_code_filter()` para o filtro exato `code=` (somente `customers`), `store` propagado nos itens compostos. Use case e router aceitam `code` apenas para catálogos com `code_filter_col` (rejeição `ValueError` nos demais).

Garantias mantidas: SQL parametrizado, `TOP (limit+1)` com cap 500, `D_E_L_E_T_=''`, zeros à esquerda preservados (`code`/`store` como texto), busca prefixo-código + substring-descrição accent-insensitive, ordenação sem coluna duplicada (regressão F5-UX-R3.1 coberta).

## 6. E6.S3 — BFF `supplies-api`

- `_CATALOG_KINDS` espelhado (+6 kinds); `code` propagado como query param forward para `/supplies/supplier-catalogs/<kind>`.
- `PUT_SUPPLIER_FIELDS` 48→51 (+`simp_regime_code`, +`linked_customer_store`, +`linked_customer_code` como companion do par) — o BFF encaminha o par; a api-delpi fixa o código vigente e rejeita divergência. `PUT_EDITABLE_FIELDS` espelhado em 51.
- Sem permissão nova; `supplies.access` + AuthZ fail-closed inalterados; erros upstream (403 S2S, 422) propagados com código.

## 7. E6.S4 — MFE `plugins/supplies`

- `SupplierFieldSpec` +3 metadados: `catalogCodeParam` (filtro exato), `catalogValueField` (`"code"|"store"`), `catalogPairField` (preenchimento do par na seleção).
- `SupplierCatalogOption` +`store`; `catalogUrl`/`useCatalogSearch` +`code` (cache key inclui `code`).
- `SupplierCatalogField`: combo remoto dedup por `catalogValueField`; seletor de loja desabilita até haver código; mesma instância reutilizada em `SupplierCreatePage` e `SupplierDetailPage` — sem duplicação de busca.
- Registry: `simp_regime_code` e `linked_customer_store` → `put:"editable"`, `evidence:"put-homologated"`; `linked_customer_code` permanece `put:"readonly"`/`evidence:"post-matrix"` (`SupplierPostOnlyFieldKey` = 1). `legal_entity_type` → enum select (CBOX). Seis campos ganham `catalog` (carrier/segment/administrator/employee/price-table/customer).
- Em E14, selecionar loja envia somente `linked_customer_store` no PUT — o companion é injetado no backend. Na inclusão, selecionar o cliente preenche código **e** loja (par atômico SA1).
- Help sync: FAQ manual e tooltip E14 atualizados (Regime SIMP editável; loja do cliente editável; código do cliente protegido; lista de catálogos ampliada).

## 8. Testes

| Camada | Resultado |
|---|---|
| api-delpi (`-k "supplier or catalog"`) | **441 pass**, 4 falhas fora de escopo (DAVI/GPT Actions — regressões externas pré-existentes) |
| api-delpi focado E6 (payload + use case + catalogs) | 84 pass |
| supplies-api | **442 pass / 21 skip** |
| MFE vitest | **372 pass** |
| MFE `tsc -b` | PASS |
| MFE eslint (arquivos do diff) | 0 erros (1 warning pré-existente `set-state-in-effect`) |
| MFE `vite build` | PASS |

Cobertura adicionada: allowlist E6 (51 PUT nas duas camadas), par composto (pair-required, inject-code, immutable-code, required-customer), catálogos (SX5-T3 pin, customers `store`/`code`, code-param rejeitado em catálogo simples, registry-kind parity), BFF (6 kinds proxy, `code` forward, loja sozinha, PUT E6), MFE (CATALOGED map +7, pending=1, draft carrega loja e ignora código, par spec).

## 9. Segurança / AuthZ

- Zero permissão nova; `supplies.access` inalterado; `codusr` backend-resolved.
- Sem SQL write; ensaios somente REST PUT + read-after-write com tracking.
- `DELPI` produtivo fora do alvo; `untouched_preserved` mantido nos lotes.
- Catálogos read-only, allowlistados, minimizados (code/label/store/disabled) — sem dados pessoais desnecessários (employees retorna matrícula+nome apenas).
- Frontend não consulta api-delpi diretamente; structural tests reforçados.

## 10. Residuais e handoffs

| Item | Estado | Próximo passo |
|---|---|---|
| `linked_customer_code` alteração | `PUT_IGNORED` upstream (veredito 6d) | handoff TOTVS/PO — decidir se criação de vínculo será via endpoint dedicado ou rotina MATA020 |
| `tax_group_code` lookup | `BLOCKED` | confirmar tabela/de-para com owner TOTVS antes de expor catálogo |
| `risk_code` lookup | `BLOCKED` | confirmar SX5/tabela F3 válida |
| Aceite visual/interativo E14 (seletores) | `INCONCLUSIVE` | sessão autenticada no navegador |
| Registro `003882/01` em TST01 | loja `06` persistida | cleanup conforme política conhecida |

## 11. Arquivos

**api-delpi:** `protheus_supplier_update_payload.py`, `update_protheus_rest_supplier_use_case.py`, `totvs_supplier_catalogs_repository.py`, `list_supplier_catalog_items_use_case.py`, `supplier_catalogs_router.py`, `scripts/protheus_supplier_put_extended_homologation.py` (lotes 6a–6d), `scripts/protheus_supplier_e6_investigation.py` (novo), tests ×3.
**supplies-api:** `suppliers_routes.py`, `suppliers_dto.py`, `tests/test_suppliers_routes.py`.
**MFE:** `types.ts`, `supplierCatalogs.ts`, `SupplierFormFields.tsx`, `SupplierCreatePage.tsx`, `SupplierDetailPage.tsx`, `suppliers.test.ts`, `helpTooltips.ts`, `userManualContent.ts`.
**Docs:** este arquivo + `IMPLEMENTATION-PLAN.md`.


## 12. Revisão GPT — E6 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para a implementação E6 em código**, baseado em inspeção do relatório, dos contratos PUT api-delpi/BFF, do use case de composição de par e do componente de seleção no GitHub (source `5747665a84`). Os resultados de PUT em `DELPI_TST01`, testes (441/442/372), deploy e smoke são **reportados pelo executor**, não reexecutados pelo GPT; validação de navegador autenticado = `TEST_NOT_RUN`.

**Capacidade real:** 28/29 campos E3 podem ser apresentados como editáveis (26 E5 + `simp_regime_code` + `linked_customer_store`). O conjunto PUT com 51 chaves inclui `linked_customer_code` **somente como companion imutável** do par, não como campo livremente alterável. `linked_customer_store` só pode mudar para loja válida do cliente já vinculado, com código original reobtido via GET no owner `api-delpi`. Handoff para mutation de `linked_customer_code` permanece aberto junto ao owner TOTVS.

**Catálogos:** seis kinds read-only novos e enum `legal_entity_type` estão implementados; `tax-groups` e `risk-codes` continuam sem fonte/semântica contratadas. Validar em browser autenticado carregamento, filtros, chaves compostas, empty/error, teclado, escopo de filial/unidade e preservação de draft em criação e E14.

**Riscos residuais a verificar:** (1) o código atual resolve o companion usando GET antes do PUT e testa igualdade explícita quando o cliente fornece código; confirmar comportamento sob alterações concorrentes (TOCTOU) com reconciliação pós-escrita; (2) no relatório, `PUT_EDITABLE_FIELDS=51` significa allowlist técnica, não 51 campos editáveis na UI; (3) `_delpi_safety_check` por prefixo de registro fictício é evidência limitada e não substitui verificação de destino REST/SQL; (4) rollback por checkout+rebuild deve ser testado/confirmado em procedimento operacional, não equivale a imagem pronta.

**Conclusão de release:** `E6_CODE=ACCEPT_WITH_RESIDUAL`; `E6_RUNTIME=PASS (executor-reported smoke)`; `E6_VISUAL=INCONCLUSIVE`; `ERP_WRITE_GATES=OFF`; não ativar escrita produtiva por esta revisão. Próxima tarefa: aceitação visual autenticada dos seis catálogos e do par cliente/loja, sem POST/PUT de fornecedor real.


## 13. Aceite visual E6.V1 — retorno do Product Owner (2026-10-23)

**Veredito visual: `PASS (PO-reported, manual)`**. O Product Owner informou explicitamente «tudo funcionando bem. pass» após inspeção autenticada das telas E14 (edição) e Novo fornecedor (criação), com três capturas compartilhadas na conversa (não anexadas ao GitHub). As imagens evidenciam diretamente: catálogo de transportadoras aberto com pesquisa por código/descrição e resultados; controles de catálogo para tabela de preços, segmento, administrador e funcionário; formulário novo com catálogo de clientes vinculados aberto, mostrando resultados e mensagem de limite de pesquisa; loja do cliente exibida em edição, condicionada à existência do código vinculado. A renderização está coerente com o rollout E6.

**Escopo do PASS:** apresentação e operação manual dos seletores conforme declaração do PO. Não afirmar que todas as combinações foram exercitadas ou que as capturas isoladamente demonstram seleção, teclado, mobile, tema claro, estados de erro, mudança de cliente/loja ou persistência. 

**Limites:** 
- `E6_VISUAL = PASS (PO-reported)` com evidência direta parcial de captura.
- `E6_BACKEND_RUNTIME = PASS (executor-reported)`, conforme relatório técnico anterior.
- `ERP_CREATE/UPDATE_GATE = OFF`; `E6_WRITE_VIA_PORTAL = TEST_NOT_RUN` e não foi autorizado alterar fornecedor real na base DELPI.
- `linked_customer_code` permanece protegido para alteração via PUT; `tax-groups`/`risk-codes` seguem bloqueados por falta de catálogo contratado. Esses resíduos não invalidam o aceite visual dos controles efetivamente implementados.

**Decisão arquitetural:** `E6 = ACCEPT_WITH_RESIDUAL` com **subgate visual E6.V1 encerrado como PASS (PO-reported)**. Não promover gate integral de escrita ou paridade total sem evidência adicional. Próxima etapa separada: resolver vínculo de cliente upstream e catálogos pendentes, se priorizados pelo PO.
