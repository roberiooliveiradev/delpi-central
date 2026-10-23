# X4.FIELDS.E1.P1 — Diagnóstico REST × SQL + Reconciliação de Campos + Readiness E1.H1

**Status:** `P1_DONE / E1.H1_READY = NO` — diagnóstico read-only executado com provas novas; homologação permanece bloqueada por pré-condições de owner/autorização, não por incógnita técnica de ambiente.

| Item | Valor |
|---|---|
| BASE HEAD | `3fd88ec163` → rebase |
| ORIGIN MAIN | `cc096cc7d3` (pré-push) |
| E1 implementation | `b77d1be3a6` |
| Execução | read-only; zero POST/PUT/PATCH/DELETE; zero escrita SQL |
| Gates | `PROTHEUS_SUPPLIER_CREATE/UPDATE_ENABLED=false` (env do container confirmado) |

## 1. Diagnóstico REST × SQL — provas novas (2026-10-23)

### A1. REST_ENVIRONMENT = `PROVEN`

Resolvido via `PARAMETROS_MINHADELPI` (`AMBIENTE=1`, mesmo valor de `INTRANET_PARAMS_AMBIENTE` do container):

| Parâmetro | Valor |
|---|---|
| `URL_REST` | `http://192.168.1.233:8701/rest` |
| `PATH_AUTH` | `/api/oauth2/v1/token` |
| `PATH_SUPPLIERS` | `/delpi/api/v1/suppliers` |
| `USR_PROTHEUS` / `PSW_PROTHEUS` | `<set>` — não impressos |
| Status use case | `configuration=ok`, `authentication=ok`, `connection=ok`, `transport=http_cleartext`, `path_label_mismatch=false` |

### A2. SQL_ENVIRONMENT = `PROVEN`

`TOTVS_DB_HOST=192.168.1.230`, `TOTVS_DB_DATABASE=DELPI` (base da listagem do Portal). O mesmo servidor hospeda **`DELPI`, `DELPI_TST01`, `DELPI_TST_WS`**.

### A3. REST_SQL_MAPPING = `PROVEN` (divergência mapeada e confirmada)

| Prova | Resultado |
|---|---|
| REST GET `00387801` | `ZZ HOMOLOG F4 FORNECEDOR TESTE`, `tax_id=98887766000134` |
| SQL `DELPI_TST01.SA2010` `003878/01` | `A2_NREDUZ='ZZ HOMOLOG F4'` — **idêntico** → REST↔TST01 mesmo dataset |
| SQL `DELPI.SA2010` `003874/01`, `003878/01` | `AMEF CONSULTORIA DE`, `CELEBRE STORE` — **fornecedores reais, dataset distinto** |

**Conclusão:** o endpoint REST `ambiente=1` escreve no Protheus cuja base é **`DELPI_TST01`** (homologação). O Portal lê **`DELPI`** (produção). Os códigos `003874`/`003878` colidem entre as bases apenas por sequência independente — nomes provam datasets distintos. `REST_SQL_BASE_DIVERGENCE` permanece `BLOCKED` **para produção**; para homologação o par correto é `REST ambiente=1 ↔ DELPI_TST01`. `DELPI_TST_WS` existe como terceira base — identificar dono/uso com o owner TOTVS antes de qualquer ensaio.

## 2. Divergência `tax_id` → `A2_CGC`

`TAX_ID_DIVERGENCE = PARTIALLY_RESOLVED`

| Hipótese | Veredito |
|---|---|
| Ambientes REST×SQL diferentes para o registro | **Descartada** — GET REST live (2026-10-23) de `00387401` retorna o registro TST01 com `tax_id=""`; a leitura SQL correta é TST01 e mostra `A2_CGC` vazio — consistente |
| Perda dentro da api-delpi | **Descartada** (F4.3) — `outbound_payload` provou envio da chave contratual |
| Perda upstream (Execauto MATA020 / endpoint do Gabriel) | **Confirmada como boundary** — sibling `003878/01` (POST 20/10) persistiu `A2_CGC=98887766000134` com a mesma chave; `003874/01` (POST 21/10) não. Suspeita de deploy upstream entre as datas (retorno `supplier_code` novo é coerente) |

**OWNER_ACTION pendente (handoff F4.3, 3 perguntas):** mapeamento `tax_id`→`A2_CGC` e condições de descarte; deploy do endpoint entre 20–21/10; shape formal de `code_error`/`details`.
`MISSING_EVIDENCE:` resposta do owner + re-teste autorizado de POST fictício.

## 3. Reconciliação dos 35 candidatos

| Classe | Campos | Lote H1 |
|---|---|---|
| **READY_FOR_HOMOLOGATION (18)** — sem lookup nem semântica pendente | `address_number`(A2_NR_END), `po_box`(A2_CX_POST), `icms_contributor`(A2_CONTRIB), `simples_nacional`(A2_SIMPNAC), `inss_withholding`(A2_RECINSS), `iss_withholding`(A2_RECISS), `csll_withholding`(A2_RECCSLL), `cofins_withholding`(A2_RECCOFI), `pis_withholding`(A2_RECPIS), `irf_calculation`(A2_CALCIRF), `inp_calculation`(A2_CALCINP), `tax_group_code`(A2_GRPTRIB), `commercial_contact_name`(A2_CONTCOM), `fax`(A2_FAX), `website`(A2_HPAGE), `responsible_name`(A2_NOMRESP), `risk_code`(A2_RISCO), `swift_code`(A2_SWIFT) | 1 |
| **CONDICIONAL (1)** | `cnae_code`(A2_CNAE — WHEN TIPO J/X; regra local implementada) | 2 |
| **NEEDS_REVIEW (5)** — semântica a congelar com owner | `legal_entity_type`(A2_TPJ), `person_category`(A2_TPESSOA), `simp_regime_code`(A2_REGESIM, default SX3 "2"), `pb_regime_code`(A2_REGPB), `generic_supplier`(A2_YFGEN, DELPI custom, só empresas 01/05) | 2/4 |
| **LOOKUP-dependent (11)** | `country_calling_code`→ACJ, `esocial_category_code`→S049BR, `payee_code`+`payee_store`→SA2(self), `purchase_price_table_code`→AIA, `carrier_code`→SA4, `segment_code`→SX5-T3, `link_type_code`→CC1, `administrator_code`→SAE, `linked_customer_code`+`linked_customer_store`→SA1, `linked_employee_code`→SRA(+A020NUMRA) | 3 |
| **BLOCKED (12)** — nunca entram em ensaio | 7 bancários (SENSITIVE/LGPD), `address_complement` (conflito A2_ENDCOMP×A2_COMPLEM), `credit_limit_amount` (DO_NOT_SEND), `branch`/`supplier_code`/`blocked` (SYSTEM_GENERATED), `group_code` (autoridade SAD) | — |

Todos: tipo/tamanho SX3 validados em teste local (E1: 55 testes PASS); `POST REST` e `Persistência` = `TEST_NOT_RUN` para todos — nenhum campo pode receber `PERSISTENCE_PROVEN` nesta etapa.

## 4. Lookups e referências

Adapter de catálogos existente (`totvs_supplier_catalogs_repository`) cobre apenas SX5 '12'/'58' — **nenhum** dos lookups dos candidatos tem adapter de leitura. Valores válidos para o ensaio devem vir de consulta read-only em `DELPI_TST01` (autorizada) ou do owner — nunca valores inventados que violem `ExistCpo`.

| Lookup | Tabela | Regra SX3 (de-para) | Valor de ensaio |
|---|---|---|---|
| `country_calling_code` | ACJ | `ExistCpo("ACJ")` | ler ACJ010 em TST01 |
| `esocial_category_code` | S049BR | tabela fixa eSocial | confirmar com owner |
| `payee_code`/`payee_store` | SA2 | `Vazio().or.ExistCpo("SA2")` | fornecedor existente TST01 |
| `purchase_price_table_code` | AIA | lookup AIA | ler AIA010 em TST01 |
| `carrier_code` | SA4 | `vazio().or.existcpo("SA4")` | ler SA4010 em TST01 |
| `segment_code` | SX5-T3 | `ExistCpo("SX5","T3"+...)` | ler SX5010 filial T3 |
| `link_type_code` | CC1 | `ExistCpo("CC1")` | ler CC1010 em TST01 |
| `administrator_code` | SAE | `Vazio().Or.ExistCpo("SAE")` | ler SAE010 em TST01 |
| `linked_customer_code`/`store` | SA1 | `ExistCpo("SA1")` composta | ler SA1010 em TST01 |
| `linked_employee_code` | SRA | `ExistCpo("SRA")+A020NUMRA` | ler SRA010 em TST01 |

## 5. Plano E1.H1 (preparado — não autorizado)

### Pré-condições (todas pendentes)
1. Confirmação do owner TOTVS de que o ensaio ocorre em `ambiente=1` ↔ `DELPI_TST01` (ou URL correta de homologação) — par agora comprovado.
2. Autorização operacional de escrita + usuário técnico (`codusr`) identificado.
3. Fornecedor fictício designado + política de limpeza acordada (sem DELETE na API: bloqueio `A2_MSBLQL` + reconciliação pelo owner — padrão dos resíduos 003874/003878).
4. Resposta do owner ao handoff `tax_id` (obrigatória antes do Lote 0 — o campo é identidade do cadastro).
5. Flags de escrita controladas por env, habilitadas só na janela do ensaio.
6. Lote 1 de campos aprovado pelo owner.

### Lotes
- **Lote 0 — controle:** payload atual (24 campos) + read-after-write + reconciliação `tax_id`.
- **Lote 1 — simples:** os 18 READY_FOR_HOMOLOGATION.
- **Lote 2 — enumerados/condicionais:** `cnae_code` + NEEDS_REVIEW após resposta do owner.
- **Lote 3 — referências:** os 11 lookup-dependent, com valores lidos de TST01.
- **Lote 4 — DELPI custom:** somente semântica confirmada (`generic_supplier`).

### Verificação por lote
POST rastreado → captura `supplier_code`/`supplier_store` → GET REST → SQL TST01 independente → classificação `PERSISTED|TRANSFORMED|IGNORED|REJECTED|INCONCLUSIVE` campo a campo → efeitos colaterais MATA020 → reconciliação/limpeza. HTTP 200 nunca é prova de persistência.

## 6. Testes read-only executados

| Escopo | Resultado |
|---|---|
| `test_protheus_supplier_extended_fields.py` + payload + path_resolver | 80 PASS |
| Suite `supplier|protheus` (raiz do repo) | 437 PASS; 2 falhas = artefato de cwd (`FileNotFoundError` de path relativo — passam no diretório `api-delpi`), não-regressão |
| Status REST live | configuration/authentication/connection = ok |
| SQL read-only | databases listadas; resíduos DELPI×TST01 comparados |
| REST GET live | `00387801`, `00387401` — datasets correlacionados |

## 7. AC COVERAGE

AC-01 `PASS` · AC-02 `PASS` (lacuna explícita prod↔tst mapeada) · AC-03 `PASS` (`PARTIALLY_RESOLVED`, causa-boundary provada) · AC-04 `PASS` (35 reconciliados) · AC-05 `PASS` · AC-06 `PASS` (12 bloqueados fora) · AC-07 `PASS` (5 lotes) · AC-08 `PASS` · AC-09 `PASS` · AC-10 `PASS` (zero escritas) · AC-11 `PASS` (contrato intacto — 80 testes) · AC-12 `PASS` · AC-13 `PASS` (este doc) · AC-14 `PASS`.

## 8. Gaps, owners e decisão

| Gap | Owner |
|---|---|
| `tax_id`→`A2_CGC` descartado no POST 21/10 | Gabriel/TOTVS (handoff F4.3) |
| Qual `URL_REST` corresponde à base produtiva DELPI | Owner TOTVS — **bloqueio de produção** |
| Uso/dono da base `DELPI_TST_WS` | Owner TOTVS |
| Semântica: `generic_supplier`, `legal_entity_type`, `person_category`, `simp_regime_code`, `pb_regime_code` | Owner funcional |
| Conflitos físicos `A2_ENDCOMP`, `A2_TIPCTA` | Owner funcional |
| Classificação LGPD dos 7 campos bancários | Segurança/DPO + owner |
| Autorização de escrita para o ensaio | PO + owner Protheus |

**`E1.H1_READY = NO`** — pré-condições 2–6 pendentes; nenhuma incógnita técnica de ambiente restante.
