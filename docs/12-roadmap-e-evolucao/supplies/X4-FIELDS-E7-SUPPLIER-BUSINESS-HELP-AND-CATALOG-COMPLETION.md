# X4.FIELDS.E7 — Supplier Business Help, Linked Customer Mutation & Remaining Catalogs

**Data:** 2026-10-23 · **Status:** `ACCEPT_WITH_RESIDUAL`
**Owner de implementação:** Portal Suprimentos (`api-delpi` → `supplies-api` → `plugins/supplies`)
**Autorização PO:** investigação, implementação nos owners corretos, consultas read-only de metadados TOTVS, testes locais, homologação controlada de escrita exclusivamente em `DELPI_TST01`, documentação, commit/push e deploy canônico. **Não autorizado:** escrita em `DELPI`, alteração direta de SA2/SA1 por SQL, mudança em MATA020, novas permissões, exposição de dados sensíveis, ativação permanente dos gates de escrita produtivos, workaround que simule persistência.

---

## 1. Baseline e authorities

- HEAD base: `5747665a84` (E6). Revalidado com `git fetch origin` — `origin/main` em `5747665a84`, worktree limpa.
- Históricos revalidados: E3 `8fb120f25a`, E5 `2808ceb9ce`, E6 `5747665a84`, review GPT `5c18e33beb…`, aceite visual E6.V1 `ecfad9d996…` (PO-reported).
- Authorities: `.cursor/rules/` (índice + transversais), `AGENTS.md`, dicionário canônico `api-delpi/docs/api/padroes-totvs/cadastro-fornecedor.md`, playbook `playbook-cadastro-fornecedor-sa2.md`, contrato `protheus-rest-supplier-api-contract.md`, evidências E2/E5/E6.
- Gates produtivos OFF confirmados: `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false`.

## 2. FRENTE A — Help funcional completo

### 2.1 Inventário

- **54 campos** no `SUPPLIER_FIELD_REGISTRY` (identidade, endereço, contato, fiscal/tributário, compras/relacionamentos, protegidos e com catálogo).
- 100% já possuíam `help` (teste E5 existente); 0% tinham referência física validada uniforme.

### 2.2 Matriz de-para (fonte: `cadastro-fornecedor.md`, de-para canônico + SX3)

| FIELD_KEY | LABEL | TABELA | COLUNA | EVIDENCE |
|---|---|---|---|---|
| tax_id | CNPJ/CPF | SA2 | `A2_CGC` | PROVEN |
| person_type | Tipo de pessoa | SA2 | `A2_TIPO` | PROVEN |
| supplier_code | Código | SA2 | `A2_COD` | PROVEN |
| supplier_store | Loja | SA2 | `A2_LOJA` | PROVEN |
| supplier_name | Razão social | SA2 | `A2_NOME` | PROVEN |
| supplier_short_name | Nome fantasia | SA2 | `A2_NREDUZ` | PROVEN |
| address | Endereço | SA2 | `A2_END` | PROVEN |
| address_number | Número | SA2 | `A2_NR_END` | PROVEN |
| district | Bairro | SA2 | `A2_BAIRRO` | PROVEN |
| postal_code | CEP | SA2 | `A2_CEP` | PROVEN |
| city | Cidade | SA2 | `A2_MUN` | PROVEN |
| city_code | Cód. município | SA2 | `A2_COD_MUN` | PROVEN |
| state | UF | SA2 | `A2_EST` | PROVEN |
| country_code | País | SA2 | `A2_PAIS` | PROVEN |
| bacen_country_code | País BACEN | SA2 | `A2_CODPAIS` | PROVEN |
| po_box | Caixa postal | SA2 | `A2_CX_POST` | PROVEN |
| contact_name | Contato | SA2 | `A2_CONTATO` | PROVEN |
| commercial_contact_name | Contato comercial | SA2 | `A2_CONTCOM` | PROVEN |
| responsible_name | Responsável | SA2 | `A2_NOMRESP` | PROVEN |
| area_code | DDD | SA2 | `A2_DDD` | PROVEN |
| phone | Telefone | SA2 | `A2_TEL` | PROVEN |
| fax | Fax | SA2 | `A2_FAX` | PROVEN |
| email | E-mail | SA2 | `A2_EMAIL` | PROVEN |
| website | Site | SA2 | `A2_HPAGE` | PROVEN |
| state_registration | Inscrição estadual | SA2 | `A2_INSCR` | PROVEN |
| municipal_registration | Inscrição municipal | SA2 | `A2_INSCRM` | PROVEN (conflito A2_INSCMU descartado — SX3 autoritativo) |
| rohs_indicator | RoHS | SA2 | `A2_YROHS` | PROVEN |
| icms_contributor | Contribuinte ICMS | SA2 | `A2_CONTRIB` | PROVEN |
| simples_nacional | Simples Nacional | SA2 | `A2_SIMPNAC` | PROVEN |
| cnae_code | CNAE | SA2 | `A2_CNAE` | PROVEN |
| legal_entity_type | Natureza jurídica | SA2 | `A2_TPJ` | PROVEN (CBOX 1–5) |
| simp_regime_code | Regime SIMP | SA2 | `A2_REGESIM` | PROVEN |
| pb_regime_code | Regime PIS/COFINS | SA2 | `A2_REGPB` | PROVEN |
| tax_group_code | Grupo tributário | SA2 | `A2_GRPTRIB` | PROVEN (sem lookup — ver §4) |
| inss_withholding | Retenção INSS | SA2 | `A2_RECINSS` | PROVEN |
| iss_withholding | Retenção ISS | SA2 | `A2_RECISS` | PROVEN |
| csll_withholding | Retenção CSLL | SA2 | `A2_RECCSLL` | PROVEN |
| cofins_withholding | Retenção COFINS | SA2 | `A2_RECCOFI` | PROVEN |
| pis_withholding | Retenção PIS | SA2 | `A2_RECPIS` | PROVEN |
| irf_calculation | Cálculo IRRF | SA2 | `A2_CALCIRF` | PROVEN |
| inp_calculation | INSS patronal | SA2 | `A2_CALCINP` | PROVEN |
| payment_condition_code | Cond. pagamento | SA2 | `A2_COND` | PROVEN (SE4) |
| payment_method_code | Forma pagamento | SA2 | `A2_FORMPAG` | PROVEN (SX5-58) |
| accounting_account | Conta contábil | SA2 | `A2_CONTA` | PROVEN (CT1) |
| financial_nature_code | Natureza | SA2 | `A2_NATUREZ` | PROVEN (SED) |
| purchase_price_table_code | Tabela de preços | SA2 | `A2_ZTABPRC` | PROVEN (AIA) |
| risk_code | Risco | SA2 | `A2_RISCO` | PROVEN (sem lookup — ver §4) |
| swift_code | SWIFT | SA2 | `A2_SWIFT` | PROVEN |
| carrier_code | Transportadora | SA2 | `A2_TRANSP` | PROVEN (SA4) |
| segment_code | Segmento | SA2 | `A2_SATIV1` | PROVEN (SX5-T3) |
| administrator_code | Administrador | SA2 | `A2_CODADM` | PROVEN (SAE) |
| linked_customer_code | Cliente vinculado | SA2 | `A2_CLIENTE` + `A2_LOJCLI` | PROVEN (SA1 composta) |
| linked_customer_store | Loja do cliente | SA2 | `A2_LOJCLI` | PROVEN |
| linked_employee_code | Funcionário vinculado | SA2 | `A2_NUMRA` | PROVEN (SRA) |

**UNRESOLVED_MAPPING:** nenhum — os 54 campos têm coluna física comprovada no dicionário canônico.

### 2.3 Padrão aplicado

Formato: `<explicação funcional>. <orientação ao usuário quando necessária>. (TOTVS: SA2.A2_XXXX)`.
- Linguagem PT-BR orientada a Suprimentos; zero jargão de implementação (teste novo bloqueia `contrato REST|API REST|payload|BFF|DTO|serializer|backend|field mapping|normalizado`).
- `linked_customer_code` usa referência composta `(TOTVS: SA2.A2_CLIENTE + SA2.A2_LOJCLI)`.
- Overrides legados `SP_HELP.suppliersEditName/ShortName` (formato técnico `"(A2_NOME), até 50 caracteres"`) removidos de `SupplierDetailPage` — inclusão e edição agora usam o mesmo help do registry; o tamanho máximo segue como orientação adicional via `supplierFieldMaxLengthHint`.
- `helpTooltips.suppliersEdit` atualizado para mencionar a referência física TOTVS nos helps.

### 2.4 Acessibilidade (AC-06)

O help usa o componente canônico `FieldLabel`→`HelpTooltip` (`plugin-ui`): `tabIndex=0` no label (foco por teclado), `onFocus/onBlur`, `Escape` fecha, `role="tooltip"`, clamp horizontal com margem de viewport e `max-width: min(280px, 100vw-24px)` — sem overflow lateral, legível em mobile e temas claro/escuro. Nenhuma alteração de componente necessária.

## 3. FRENTE B — Alteração do cliente vinculado (`A2_CLIENTE`)

### 3.1 Evidências consolidadas (DELPI_TST01)

| Ensaio | Payload | REST | Resultado |
|---|---|---|---|
| E6-6b | `linked_customer_code:"000002"` isolado | 400 `PROTHEUS_SUPPLIER_UPDATE_MATA020_FAILED` — "Falha ao alterar fornecedor" | Código isolado rejeitado pelo MATA020 |
| E6-6d | par `{code:"000002",store:"01"}` divergente | 200 | `A2_CLIENTE` **inalterado** (REST+SQL) — código descartado silenciosamente |
| E7-B | `vincula_flag:"2"` + par `{code:"000002",store:"01"}` | 200 | `A2_CLIENTE`/`A2_LOJCLI` **inalterados** — `A2_VINCULA` não habilita a mutação |

### 3.2 Veredito

`LINKED_CUSTOMER_PUT_RESULT = BLOCKED`. Não existe contrato REST upstream que persista a troca de `A2_CLIENTE`: o MATA020 ou falha (6b) ou aceita e descarta (6d/E7-B). HTTP 200 não comprova persistência.

### 3.3 Handoff técnico ao owner TOTVS (Gabriel)

**Pedido:** viabilizar alteração do cliente vinculado (SA2 `A2_CLIENTE` + `A2_LOJCLI`) de um fornecedor existente via contrato REST.

- **Payload sanitizado testado:** `PUT /suppliers/{A2_COD}/{A2_LOJA}` com `{"linked_customer_code":"000002","linked_customer_store":"01"}` (par completo, sem campos de identidade).
- **Observado:** HTTP 200, `A2_CLIENTE` permanece `000001` (confirmado REST GET + SQL `DELPI_TST01.dbo.SA2010`). Payload isolado `{"linked_customer_code":"000003"}` → HTTP 400, detalhe `Falha na rotina MATA020 ao alterar fornecedor`.
- **Hipótese:** o ExecAuto MATA020 em modo alteração trata `A2_CLIENTE` como campo não-atualizável ou exige validação/dependência adicional (candidatos já descartados: `A2_VINCULA`, loja no par). Possíveis causas a confirmar no fonte: `X3_WHEN`, validação de `VldAllGet`, ou bloqueio funcional por movimentos do fornecedor.
- **Mudança necessária no owner:** expor endpoint/operação que altere o vínculo de forma atômica código+loja (ou confirmar a impossibilidade funcional, caso em que o Portal manterá o campo protegido definitivamente).
- **Salvaguarda já implementada no Portal:** tentativa divergente → `PROTHEUS_SUPPLIER_LINKED_CUSTOMER_IMMUTABLE` (422); código isolado → `PROTHEUS_SUPPLIER_LINKED_PAIR_REQUIRED` (422). Nenhum falso sucesso possível.

## 4. FRENTE C — Catálogos pendentes

### 4.1 `tax_group_code` (`A2_GRPTRIB`)

- SX3: `X3_F3`/`X3_VALID`/`X3_WHEN` **vazios** — sem lookup declarado.
- SX5 tabela `21` (suspeita inicial): apenas 6 linhas (`001`,`002`,`003`,`004`,`MC1`,`SN1`) — **não cobre** os valores reais observados em SA2 (`IMP`,`PRO`,`SN*`,`TTD`).
- `CATALOG_STATUS = BLOCKED` — de-para e owner da classificação pendentes com a área fiscal/TOTVS. Campo permanece input honesto; help explica que os códigos em uso não seguem lista fechada.

### 4.2 `risk_code` (`A2_RISCO`)

- SX3: `X3_F3`/`X3_VALID`/`X3_WHEN` **vazios** — sem tabela de validação nem enum.
- `CATALOG_STATUS = BLOCKED` — sem fonte confiável; classificação não é inventada (nenhum "Baixo/Médio/Alto" fabricado). Campo permanece input com help funcional.

## 5. Contratos alterados

Nenhum contrato HTTP alterado. Mudança limitada a textos de help (MFE) e remoção de overrides. api-delpi/supplies-api: **sem diff funcional** — allowlists PUT/POST, catálogos e AuthZ inalterados em E7.

## 6. Segurança e AuthZ

- `supplies.access` inalterado; zero permissão nova.
- AuthN/AuthZ fail-closed preservados; identidade continua resolvida no backend (`codusr`).
- Frontend não chama api-delpi (structural test preservado).
- Sem SQL write; `DELPI` intocado; gates ERP OFF.

## 7. Testes

- MFE: **375 pass** (3 novos E7 — referência TOTVS obrigatória, vocabulário proibido, mesma fonte registry create/edit).
- `tsc -b` PASS; lint escopado 0 erros; `vite build` PASS.
- Backend: sem mudança funcional — regressão coberta pelas suítes existentes.

## 8. Residuais

- `linked_customer_code` mutação: `BLOCKED` → handoff Gabriel (§3.3).
- `tax-groups`/`risk-codes`: `BLOCKED` sem fonte confiável → handoff área fiscal/TOTVS.
- Aceite visual dos novos helps: `INCONCLUSIVE` sem sessão autenticada.
- `003882/01` segue com loja `06` aguardando cleanup TST01.

## 9. Próxima etapa

1. Aceite visual autenticado dos helps e seletores (E14 + inclusão).
2. Resposta do owner TOTVS sobre mutação de vínculo e de-para fiscal.
3. Cleanup do fornecedor de ensaio `003882/01`.
