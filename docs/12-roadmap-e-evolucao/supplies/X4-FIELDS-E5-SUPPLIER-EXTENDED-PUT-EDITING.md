# X4.FIELDS.E5 — Extended Supplier Fields Editing Enablement

**Status:** `ACCEPT_WITH_RESIDUAL`
**Base:** E3 `8fb120f25a` (POST 53 / GET +29 / PUT 22 congelado)
**Objetivo:** habilitar a edição (PUT) dos 29 campos adicionais promovidos em E3,
com evidência de persistência comprovada em `DELPI_TST01` campo a campo.

---

## 1. Matriz de edição — resultado do ensaio E5.H1

Destino exclusivo `DELPI_TST01` (REST `ambiente:1@192.168.1.233:8701`,
SQL `DELPI_TST01`, produção `DELPI` confirmada fora do alvo a cada lote).
Fornecedores controlados: `003877/01`, `003879/01`, `003880/01`, `003882/01`.
Critério: `PUT_PERSISTENCE_PROVEN` somente com mudança de valor comprovada por
leitura posterior independente (REST read-after-write **e** SQL TST01).
`untouched_preserved: true` e `delpi_untouched: true` em todas as operações.

### 1.1 PUT_PERSISTENCE_PROVEN — 26 campos

| Campo (REST) | Coluna SA2 | Evidência |
|---|---|---|
| `address_number` | A2_NR_END | REST+SQL changed |
| `po_box` | A2_CX_POST | REST+SQL changed |
| `commercial_contact_name` | A2_CONTCOM | REST+SQL changed |
| `fax` | A2_FAX | REST+SQL changed |
| `website` | A2_HPAGE | REST+SQL changed |
| `responsible_name` | A2_NOMRESP | REST+SQL changed |
| `icms_contributor` | A2_CONTRIB | REST+SQL changed |
| `simples_nacional` | A2_SIMPNAC | REST+SQL changed |
| `inss_withholding` | A2_RECINSS | REST+SQL changed |
| `iss_withholding` | A2_RECISS | REST+SQL changed |
| `csll_withholding` | A2_RECCSLL | REST+SQL changed |
| `cofins_withholding` | A2_RECCOFI | REST+SQL changed |
| `pis_withholding` | A2_RECPIS | REST+SQL changed |
| `irf_calculation` | A2_CALCIRF | REST+SQL changed |
| `inp_calculation` | A2_CALCINP | REST+SQL changed |
| `tax_group_code` | A2_GRPTRIB | REST+SQL changed |
| `legal_entity_type` | A2_TPJ | REST+SQL changed |
| `pb_regime_code` | A2_REGPB | REST+SQL changed |
| `swift_code` | A2_SWIFT | REST+SQL changed |
| `purchase_price_table_code` | A2_ZTABPRC | REST+SQL changed |
| `carrier_code` | A2_TRANSP | REST+SQL changed |
| `segment_code` | A2_SATIV1 | REST+SQL changed |
| `administrator_code` | A2_CODADM | REST+SQL changed |
| `cnae_code` | A2_CNAE | REST+SQL changed |
| `linked_employee_code` | A2_NUMRA | REST+SQL changed |
| `risk_code` | A2_RISCO | REST+SQL changed |

### 1.2 PUT_INCONCLUSIVE — 2 campos

| Campo | Motivo |
|---|---|
| `simp_regime_code` | Valores `"1"`/`"2"` aceitos mas sem prova de mudança controlada; `"0"` rejeitado upstream (400). Drift de comportamento observado — não houve altered-value proof. |
| `linked_customer_code` | SA1 TST01 só possui cliente `000001` — impossível provar mudança de valor; PUT do par `linked_customer_code`+`linked_customer_store` rejeitado (400 MATA020). Precisa de 2º cliente válido em TST01. |

### 1.3 PUT_IGNORED — 1 campo

| Campo | Motivo |
|---|---|
| `linked_customer_store` | Enviado `"02"`/`"03"`; coluna permaneceu `"01"` — upstream ignora o campo. Rejeitado também no PUT do par (lote 5c). |

**Total:** 26 `PUT_PERSISTENCE_PROVEN` · 2 `PUT_INCONCLUSIVE` · 1 `PUT_IGNORED`.
Operações rastreadas (ProtheusWriteTracker): `24aae7b8`, `094435f8`,
`021d9682`, `faf3d1cb`, `94c3a987`, `108a159d`, `db6649c5` (prefixos).

---

## 2. Contratos alterados

### api-delpi — `protheus_supplier_update_payload.py`
- `PUT_EDITABLE_FIELDS`: 22 (F3.3) → **48** (F3.3 + 26 E5-homologados).
  Allowlist **explícita** — não derivada de `SUPPLIER_FIELD_SPECS`/POST.
- Normalização reutiliza as specs canônicas SX3 (enums, tamanho, dígitos).
- Regra condicional adicionada: `cnae_code` rejeitado quando `person_type == "F"`
  no mesmo PUT parcial (`PROTHEUS_SUPPLIER_FIELD_CONDITIONAL`, 422).
- Os 3 campos sem prova seguem rejeitados com
  `PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE` — fail-closed preservado.
- Identidade inalterada: `supplier_code`, `supplier_store`, `tax_id`, `codusr`
  protegidos; identidade do ator resolvida no backend.

### supplies-api — `suppliers_dto.py`
- `PUT_SUPPLIER_FIELDS`: 22 → **48**, espelhando exatamente os 26 homologados.
- AuthZ inalterada (`supplies.access` + regras core-first); nenhuma permissão
  nova; campos não homologados seguem rejeitados (não descartados
  silenciosamente).

### plugins/supplies — `types.ts` + registry
- `SUPPLIER_FIELD_REGISTRY`: os 26 homologados mudaram de
  `put: "readonly"` para `put: "editable"` com `evidence: "put-homologated"`
  (novo membro da union `SupplierFieldEvidence`).
- `SupplierPostOnlyFieldKey`: 29 → **3** (`simp_regime_code`,
  `linked_customer_code`, `linked_customer_store`); `SupplierEditableFieldKey`
  exclui-os automaticamente via `Exclude`.
- Novo `SupplierExtendedFieldKey` (os 29) para testes/fixtures.
- Fluxo inteiramente registry-driven: `draftFromDetail`,
  `diffEditableFields`, `buildUpdateFornecedor`, formulário de edição e revisão
  passam a cobrir os 26 sem código adicional. Enums com `options` renderizam
  select automaticamente; campos de referência sem catálogo contratado seguem
  input+help (residual documentado).
- Help/manual: respostas de edição e de campos somente-leitura atualizadas.

## 3. Comportamento de edição (E14)

- PUT parcial: somente campos modificados são enviados; omitidos preservados
  (comprovado por `untouched_preserved` nos 7 lotes do ensaio).
- Revisão antes/depois existente cobre os novos campos automaticamente.
- Resultado indeterminado continua não apresentado como sucesso; erros
  preservam o rascunho.
- Campo ignorado/pendente não recebe controle de edição — sem falsa affordance.

## 4. Testes

| Camada | Resultado |
|---|---|
| api-delpi | `124 passed` (matriz 26 aceitos / 3 rejeitados / identidade protegida / condicional CNAE×person_type) |
| supplies-api | `439 passed, 21 skipped` (allowlist, forwarding, rejeição dos 3 pendentes) |
| plugins/supplies | `371 passed` — 70 no arquivo focado; novos casos E5 (editable/pending/draft) |
| typecheck `tsc -b` | PASS |
| `vite build` | PASS |
| eslint escopado `features/suppliers` | 0 erros (3 warnings pré-existentes fora do diff) |

## 5. Segurança

- Zero permissão nova; `supplies.access` inalterado; AuthZ core-first.
- `PROTHEUS_SUPPLIER_CREATE_ENABLED=false` / `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false`
  confirmados — publicação de código **não** ativa escrita ERP produtiva.
- Zero escrita na base `DELPI`; todas as provas em `DELPI_TST01`.
- Tracking de operações conservador mantido; payload sanitizado.
- CPF/identidade seguem protegidos e mascarados.

## 6. Residuais explícitos

| Item | Estado |
|---|---|
| `simp_regime_code` | `PUT_INCONCLUSIVE` — aguarda novo ensaio com evidência de mudança |
| `linked_customer_code` | `PUT_INCONCLUSIVE` — precisa 2º cliente válido em SA1 TST01 |
| `linked_customer_store` | `PUT_IGNORED` — contrato upstream não persiste; excluído de PUT |
| Catálogos de referência (8 campos) | input+help — pendente contrato de busca |
| Aceitação visual/interativa E14 | `INCONCLUSIVE` — requer sessão autenticada |
| 7 registros `ZZ HOMOLOG E2*` em TST01 | cleanup via procedimento aprovado |

## 7. Próximos passos

1. Reteste dedicado de `simp_regime_code`/`linked_customer_code` com massa
   TST01 adequada (2º cliente SA1) → promoção se `PUT_PERSISTENCE_PROVEN`.
2. Decisão PO sobre `linked_customer_store` (campo morto upstream no PUT).
3. Catálogos de referência: contrato de busca para selects.


## 8. Revisão GPT — E5 (2026-10-23)

**Decisão: `ACCEPT_WITH_RESIDUAL` para implementação em código; `E5_VISUAL = INCONCLUSIVE`.** O relatório do executor indica 26 campos PUT com mudança de valor e read-back em `DELPI_TST01`, 2 inconclusivos e 1 ignorado. Os resultados de ensaio e de deploy são **reportados pelo executor**; o GPT inspecionou código/script/documentação no GitHub, mas não reexecutou chamadas REST, consultas SQL, testes, SSH ou navegador autenticado.

**Correção documental deste review:** a tabela original §1.1 atribuía colunas SA2 diferentes do `SA2_COLUMN` efetivamente empregado pelo script `api-delpi/scripts/protheus_supplier_put_extended_homologation.py`. 14 referências de coluna foram ajustadas para coincidir com o script de ensaio e de-para do E2; nenhum teste foi reexecutado e nenhum contrato alterado. A tabela original **não era evidência confiável de mapeamento**; a trilha de execução deve se apoiar no script e nos registros por operação. Caso haja inconsistência entre script, SX3 real e dados, classificar `EXECUTION_DRIFT` e investigar antes de nova escrita.

**Escopo provado:** a allowlist PUT contém 48 campos (22 anteriores + 26 novos), com proteção de `tax_id`, código e loja; BFF acompanha a allowlist. `simp_regime_code` e `linked_customer_code` seguem inconclusivos; `linked_customer_store` permanece ignorado e excluído. Flags produtivas OFF conforme relatório. O predicado `_delpi_safety_check` do script detecta resíduos `ZZ HOMOLOG%` na base `DELPI`, mas **não prova por si só ausência de toda alteração** em outros registros de produção; essa conclusão exige roteamento e evidência operacional independentes.

**Residuais:** o teste visual autenticado na E14 não ocorreu; `PUT` pela UI permanece bloqueado pelos gates produtivos desabilitados, mesmo com controles editáveis. Rollback por `git checkout` e rebuild **não é reversão imediata por imagem pronta**; conferir política de deploy/rollback no próximo ciclo. Não autorizar ativação geral da escrita de produção por este aceite.
