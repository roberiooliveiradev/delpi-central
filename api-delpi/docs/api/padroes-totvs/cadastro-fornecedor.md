# Cadastro de fornecedor (SA2)

Convenções Delpi ao buscar / identificar fornecedor TOTVS. Detalhe completo (248 campos, índices, relações, dependências de CREATE/UPDATE): [playbook-cadastro-fornecedor-sa2.md](./playbooks/playbook-cadastro-fornecedor-sa2.md).

# Dicionário canônico Minha DELPI ↔ TOTVS

Este é o **de-para oficial** do cadastro de fornecedores. Dois consumidores: handoff técnico de integração e a futura API DELPI de fornecedores. Evidência técnica completa (248 campos, índices, validações, profiling): [playbook-cadastro-fornecedor-sa2.md](./playbooks/playbook-cadastro-fornecedor-sa2.md) §44.

## Convenção de nomenclatura (Minha DELPI)

Definida no owner global [openapi-bilingue-catalogo-canonico.md](../openapi-bilingue-catalogo-canonico.md) § "Convenção de nomes de campos":

- inglês, `snake_case`, sem prefixos Protheus (`A2_*`, `B1_*`…) no nome público;
- prefixo `supplier_` somente onde distingue identidade ou já faz parte de contrato publicado (`supplier_code`, `supplier_store`, `supplier_name`, `supplier_short_name`); atributos intrínsecos sem prefixo (`email`, `phone`, `blocked`, `state`);
- sufixos: `_code` código de negócio · `_id` somente identificador técnico real · `_date`/`_datetime` data/hora · `_days` duração · `_quantity` quantidade · `_percent` percentual · `_amount` montante;
- `1 conceito = 1 nome canônico` — reutilizar nome publicado antes de criar outro;
- `label_pt_br` e `business_description` são campos separados do nome técnico; texto SX3 original é preservado na coluna `notes` quando diverge da semântica real.

`naming_status`: `REUSED_PROVEN` (nome já publicado com a mesma semântica) · `NEW_CANONICAL` (nome criado nesta rodada) · `LEGACY_CONFLICT` (nome legado concorrente) · `NEEDS_REVIEW` (semântica insuficiente para congelar).

## PUBLIC_DICTIONARY

Campos relevantes ao cadastro/integração do fornecedor. Os demais campos SA2 são `REFERENCE_ONLY` (técnicos, estatísticos, módulo específico ou sem consumer previsto) — permanecem documentados apenas no playbook §44.3.

| minha_delpi_field | label_pt_br | business_description | totvs_alias | totvs_table | totvs_field | data_type | length | decimals | create_class | default_source | default_value | validation | lookup | normalization | company_scope | naming_status | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| branch | Filial | Filial do registro no Protheus (branco = compartilhado, MODO=C). | SA2 | SA2010 | `A2_FILIAL` | C | 2 | 0 | SYSTEM_GENERATED | RUNTIME_RULE | blank=shared | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Filial / Filial do Sistema/system — não enviar |
| supplier_code | Código | Código do fornecedor; gerado por GETSXENUM("SA2") nas empresas 01/05. | SA2 | SA2010 | `A2_COD` | C | 6 | 0 | SYSTEM_GENERATED | SX3_DEFAULT | GETSXENUM("SA2") | IIF(Empty(M->A2_LOJA),.T.,ExistChav("SA2",M->A2_CO | — | RTRIM+zfill | 01,03,04,05 | REUSED_PROVEN | PROVEN | Codigo / Codigo do Fornecedor/totvs_supplier_repository.py |
| supplier_store | Loja | Loja do fornecedor; compõe a identidade junto de supplier_code. | SA2 | SA2010 | `A2_LOJA` | C | 2 | 0 | UNKNOWN | OBSERVED_CONVENTION | '01' | existchav("SA2",M->a2_cod+M->a2_loja,,"EXISTFOR") | — | RTRIM+zfill | 01,03,04,05 | REUSED_PROVEN | PROVEN | Loja / Loja do Fornecedor/padding inconsistente — normalizar |
| supplier_name | Razão social | Razão social do fornecedor. | SA2 | SA2010 | `A2_NOME` | C | 50 | 0 | CANDIDATE_REQUIRED | NONE | — | A020CarEsp() | — | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | Razao Social / Nome ou Razao Social/ |
| supplier_short_name | Nome fantasia | Nome reduzido/fantasia. Conflito: safety_stock_sql usa trade_name para o mesmo campo. | SA2 | SA2010 | `A2_NREDUZ` | C | 20 | 0 | CANDIDATE_REQUIRED | NONE | — | A020CarEsp() | — | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | N Fantasia / Nome de Fantasia/LEGACY_CONFLICT: trade_name |
| tax_id | CNPJ/CPF | CNPJ ou CPF do fornecedor (SX3 diz "do cliente" — metadata TOTVS incorreta preservada em sx3_description). | SA2 | SA2010 | `A2_CGC` | C | 14 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio() .Or. IIF( M->A2_TIPO == 'X', .T., (CGC(M-> | — | digits-only | 01,03,04,05 | REUSED_PROVEN | PROVEN | CNPJ/CPF / CNPJ/CPF do cliente/não é chave; sinal de duplicidade |
| person_type | Tipo de pessoa | F= física, J= jurídica, X= exterior/outros. | SA2 | SA2010 | `A2_TIPO` | C | 1 | 0 | CANDIDATE_REQUIRED | SX3_DEFAULT | IF(LEFT(SA2->A2_CGC,2) == '  ' | pertence("FJX") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Tipo / Tipo do Fornecedor/CBOX/enum |
| address | Endereço | Logradouro. | SA2 | SA2010 | `A2_END` | C | 40 | 0 | CANDIDATE_REQUIRED | NONE | — | A020CarEsp() | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Endereco / Endereco do Fornecedor/ |
| address_number | Número | Número do endereço (0% de uso observado). | SA2 | SA2010 | `A2_NR_END` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | digits-only | 01,03,04,05 | NEW_CANONICAL | PROVEN | Numero / Numero do Endereco/ |
| address_complement | Complemento | Complemento do endereço. Conflito de campo: A2_ENDCOMP × A2_COMPLEM. | SA2 | SA2010 | `A2_ENDCOMP` | C | 21 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Compl. End. / Complemento Endereco/par ENDCOMP/COMPLEM |
| district | Bairro | Bairro. | SA2 | SA2010 | `A2_BAIRRO` | C | 20 | 0 | CANDIDATE_REQUIRED | NONE | — | A020CarEsp() | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Bairro / Bairro do Fornecedor/ |
| postal_code | CEP | Código postal (dígitos). | SA2 | SA2010 | `A2_CEP` | C | 8 | 0 | CANDIDATE_REQUIRED | NONE | — | — | — | digits-only | 01,03,04,05 | NEW_CANONICAL | PROVEN | CEP / Cod Enderecamento Postal/ |
| city | Município | Nome do município. | SA2 | SA2010 | `A2_MUN` | C | 25 | 0 | CANDIDATE_REQUIRED | NONE | — | A020CarEsp() | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Municipio / Municipio do Fornecedor/ |
| city_code | Código do município | Código do município (CC2, por UF). | SA2 | SA2010 | `A2_COD_MUN` | C | 5 | 0 | CANDIDATE_REQUIRED | NONE | — | ExistCpo("CC2", FWFldGet("A2_EST") + FWFldGet("A2_ | CC2 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cod. Municip / Codigo do Municipio/OBRIGAT flag |
| state | UF | Unidade federativa; EX=exterior. | SA2 | SA2010 | `A2_EST` | C | 2 | 0 | CANDIDATE_REQUIRED | NONE | — | ExistCpo("SX5","12"+M->A2_EST) | SX5-12 | uppercase | 01,03,04,05 | REUSED_PROVEN | PROVEN | Estado / Sigla da Federacao/lookup SX5-12 |
| country_code | País | Código do país (SYA) — usado para estrangeiros. | SA2 | SA2010 | `A2_PAIS` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio() .or. ExistCpo("SYA",M->A2_PAIS) | SYA | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Pais / Pais do Fornecedor/ |
| bacen_country_code | País BACEN | Código BACEN do país (CCH); 01058=Brasil observado em 100%. | SA2 | SA2010 | `A2_CODPAIS` | C | 5 | 0 | CANDIDATE_REQUIRED | OBSERVED_CONVENTION | '01058' | ExistCpo("CCH") | CCH | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Pa¡s Bacen / C¢d. pa¡s Banco Central/OBRIGAT flag; OBSERVED_CONVENTION |
| po_box | Caixa postal | Caixa postal. | SA2 | SA2010 | `A2_CX_POST` | C | 5 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Caixa Postal / Caixa Postal/ |
| state_registration | Inscrição estadual | Inscrição estadual (IE() por UF). | SA2 | SA2010 | `A2_INSCR` | C | 18 | 0 | PROVEN_OPTIONAL | NONE | — | IE(M->A2_INSCR,M->A2_EST) .And. A020VldUCod() | — | digits-only | 01,03,04,05 | NEW_CANONICAL | PROVEN | Ins. Estad. / Inscricao Estadual/WHEN condicional |
| municipal_registration | Inscrição municipal | Inscrição municipal. | SA2 | SA2010 | `A2_INSCRM` | C | 18 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | digits-only | 01,03,04,05 | NEW_CANONICAL | PROVEN | Ins. Municip / Inscricao Municipal/ |
| icms_contributor | Contribuinte ICMS | Indicador de contribuinte (CBOX 1/2). | SA2 | SA2010 | `A2_CONTRIB` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence(' 12') | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Contribuinte / Contribuinte do ICMS/ |
| simples_nacional | Simples Nacional | Indicador Simples Nacional. | SA2 | SA2010 | `A2_SIMPNAC` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence(" 12") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Opt Simp Nac / Optante Simples Nacional/ |
| cnae_code | CNAE | Código CNAE (WHEN TIPO J/X). | SA2 | SA2010 | `A2_CNAE` | C | 9 | 0 | CONDITIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cod CNAE / Codigo CNAE do Fornecedor/ |
| legal_entity_type | Tipo jurídico | Tipo de pessoa jurídica. | SA2 | SA2010 | `A2_TPJ` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence(" 12345") | — | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | TPJ / Tipo de Pessoa Jur¡dica/semântica SX3 ampla |
| person_category | Categoria de pessoa | Categoria de pessoa (99,9% vazio). | SA2 | SA2010 | `A2_TPESSOA` | C | 2 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Tipo Pessoa / Tipo de Pessoa/ |
| simp_regime_code | Regime SIMP | Regime tributário SIMP. | SA2 | SA2010 | `A2_REGESIM` | C | 1 | 0 | PROVEN_OPTIONAL | SX3_DEFAULT | "2" | — | — | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Rg. Simp. MT / Reg. Simlificado MT/default SX3 "2" |
| pb_regime_code | Regime PB | Regime PB. | SA2 | SA2010 | `A2_REGPB` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence(" 12" ) | — | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Reg.Para¡ba / Regime Para¡ba/ |
| financial_nature_code | Natureza financeira | Natureza financeira (lookup SED). | SA2 | SA2010 | `A2_NATUREZ` | C | 10 | 0 | CANDIDATE_REQUIRED | NONE | — | FinVldNat( .T. ,,2) .And. Vazio() .Or.  Existcpo(" | SED | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Natureza / Cod Natureza Financeira/OBRIGAT flag; RESTRICTED update |
| inss_withholding | Retenção INSS | Flag de retenção INSS. | SA2 | SA2010 | `A2_RECINSS` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | pertence("SN") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Calc. INSS ? / Calcula INSS p/ Fornec. ?/default SX3 |
| iss_withholding | Retenção ISS | Flag de retenção ISS. | SA2 | SA2010 | `A2_RECISS` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence("SN ") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Recolhe ISS? / Recolhe ISS ?/ |
| csll_withholding | Retenção CSLL | Flag de retenção CSLL. | SA2 | SA2010 | `A2_RECCSLL` | C | 1 | 0 | PROVEN_OPTIONAL | SX3_DEFAULT | "1" | Pertence("12") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Rec.CSLL / Recolhimento da CSLL/default SX3 "1" |
| cofins_withholding | Retenção COFINS | Flag de retenção COFINS. | SA2 | SA2010 | `A2_RECCOFI` | C | 1 | 0 | PROVEN_OPTIONAL | SX3_DEFAULT | "1" | Pertence("12") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Rec.COFINS / Recolhimento da COFINS/default SX3 "1" |
| pis_withholding | Retenção PIS | Flag de retenção PIS. | SA2 | SA2010 | `A2_RECPIS` | C | 1 | 0 | PROVEN_OPTIONAL | SX3_DEFAULT | "1" | Pertence("12") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Rec. PIS / Recolhimento de PIS/default SX3 "1" |
| irf_calculation | Calcula IRRF | Flag de cálculo IRRF. | SA2 | SA2010 | `A2_CALCIRF` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence('1234') | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | C lc. IRRF / C lculo do IRRF./ |
| inp_calculation | Calcula INSS | Flag de cálculo INSS patronal. | SA2 | SA2010 | `A2_CALCINP` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | Pertence("12") | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Calc.INSS.Pt / Calcula INSS Patronal?/ |
| tax_group_code | Grupo tributário | Grupo de tributação. | SA2 | SA2010 | `A2_GRPTRIB` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Grp. Tribut. / Grupo de Tributacao/ |
| esocial_category_code | Categoria eSocial | Categoria eSocial (S049BR). | SA2 | SA2010 | `A2_CATEFD` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | — | S049BR | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cat eSocial / Categoria eSocial/ |
| contact_name | Contato | Pessoa de contato. | SA2 | SA2010 | `A2_CONTATO` | C | 15 | 0 | CANDIDATE_REQUIRED | NONE | — | — | — | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | Contato / Contato na Empresa/OBRIGAT flag |
| commercial_contact_name | Contato comercial | Contato comercial. | SA2 | SA2010 | `A2_CONTCOM` | C | 15 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Contato Com. / Contato Comercial (NNC)/ |
| area_code | DDD | Código de área. | SA2 | SA2010 | `A2_DDD` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | digits-only | 01,03,04,05 | REUSED_PROVEN | PROVEN | DDD / Codigo do DDD/46 ocorrências em código |
| country_calling_code | DDI | Código de país para chamadas (ACJ). | SA2 | SA2010 | `A2_DDI` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | IIF(!EMPTY(M->A2_DDI), ExistCpo("ACJ",M->A2_DDI),. | ACJ | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | DDI / Codigo do DDI/ |
| phone | Telefone | Telefone (dígitos). | SA2 | SA2010 | `A2_TEL` | C | 50 | 0 | CANDIDATE_REQUIRED | NONE | — | — | — | digits-only | 01,03,04,05 | NEW_CANONICAL | PROVEN | Telefone / Numero do Telefone/OBRIGAT flag |
| fax | Fax | Fax. | SA2 | SA2010 | `A2_FAX` | C | 15 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | digits-only | 01,03,04,05 | NEW_CANONICAL | PROVEN | FAX / Numero do FAX do fornec./ |
| email | E-mail | E-mail (lowercase). | SA2 | SA2010 | `A2_EMAIL` | C | 50 | 0 | CANDIDATE_REQUIRED | NONE | — | — | — | lowercase | 01,03,04,05 | REUSED_PROVEN | PROVEN | E-Mail / E-Mail/OBRIGAT flag |
| website | Site | Home-page. | SA2 | SA2010 | `A2_HPAGE` | C | 30 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | Home-Page / Home-Page/ |
| responsible_name | Responsável | Nome do responsável. | SA2 | SA2010 | `A2_NOMRESP` | C | 45 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Nome Resp. / Nome do Responsavel/ |
| payment_condition_code | Condição de pagamento | Condição de pagamento (SE4). | SA2 | SA2010 | `A2_COND` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | vazio().or.existcpo("SE4") | SE4 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cond. Pagto / Condicao de Pagamento/ |
| payment_method_code | Forma de pagamento | Forma de pagamento (SX5-58). | SA2 | SA2010 | `A2_FORMPAG` | C | 2 | 0 | CANDIDATE_REQUIRED | NONE | — | Vazio() .Or. ExistCpo("SX5", "58" + M->A2_FORMPAG) | SX5-58 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Form. Pgto / Forma de pagamento prefer/OBRIGAT flag |
| accounting_account | Conta contábil | Conta contábil (CT1). | SA2 | SA2010 | `A2_CONTA` | C | 20 | 0 | CANDIDATE_REQUIRED | NONE | — | vazio().or. Ctb105Cta() | CT1 | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | C Contabil / Codigo da Conta Contabil/OBRIGAT flag; RESTRICTED |
| credit_limit_amount | Limite de crédito | Limite de crédito (acumulador estatístico). | SA2 | SA2010 | `A2_LC` | C | 14 | 0 | DO_NOT_SEND | NONE | — | — | — | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Lim. Credito / Limite de Credito/provável DO_NOT_SEND |
| risk_code | Risco | Código de risco. | SA2 | SA2010 | `A2_RISCO` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Risco / Nivel de Risco/ |
| bank_code | Banco | Código do banco (SA6). | SA2 | SA2010 | `A2_BANCO` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | — | SA6 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Banco / Codigo do Banco/sensível |
| bank_branch | Agência | Agência bancária (SA6). | SA2 | SA2010 | `A2_AGENCIA` | C | 5 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cod Agencia / Cod Agencia Fornecedor/sensível |
| bank_branch_digit | DV agência | Dígito verificador da agência. | SA2 | SA2010 | `A2_DVAGE` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | DV Ag Cnab / Digito Verific. Agencia/sensível |
| bank_account | Conta bancária | Número da conta (SA6). | SA2 | SA2010 | `A2_NUMCON` | C | 10 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cta Corrente / Conta Corrente Fornecedor/sensível |
| bank_account_digit | DV conta | Dígito verificador da conta. | SA2 | SA2010 | `A2_DVCTA` | C | 2 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | DV Cta Cnab / Digito Verificador Conta/sensível |
| bank_account_type | Tipo de conta | Tipo de conta (CBOX). Conflito: A2_TIPCTA × A2_TPCONTA. | SA2 | SA2010 | `A2_TIPCTA` | C | 1 | 0 | PROVEN_OPTIONAL | SX3_DEFAULT | "1" | Pertence("12") | CBOX | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Tp. Cta. For / Tipo de Conta Fornecedor/par TIPCTA/TPCONTA |
| swift_code | SWIFT | Código SWIFT (exterior). | SA2 | SA2010 | `A2_SWIFT` | C | 30 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | uppercase | 01,03,04,05 | NEW_CANONICAL | PROVEN | Swift / Swift do Fornecedor/uppercase |
| payee_code | Favorecido | Código do favorecido de pagamento (self-SA2). | SA2 | SA2010 | `A2_CODFAV` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio() .Or. ExistCpo("SA2") | SA2 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Cod.Favorec / Codigo do Favorecido/ |
| payee_store | Loja favorecido | Loja do favorecido. | SA2 | SA2010 | `A2_LOJFAV` | C | 2 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio() .Or. ExistCpo("SA2",M->A2_CODFAV+M->A2_LOJ | — | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Loja Favorec / Loja do Favorecido/ |
| blocked | Bloqueado | Flag de bloqueio (1=bloqueado, 2=ativo; ~4% vazio). | SA2 | SA2010 | `A2_MSBLQL` | C | 1 | 0 | SYSTEM_GENERATED | SX3_DEFAULT | "2" | pertence("12") | — | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | Bloqueado / Bloqueia o Fornecedor/SYSTEM_GENERATED; RESTRICTED |
| rohs_indicator | RoHS | Indicador RoHS DELPI (só 01/05). | SA2 | SA2010 | `A2_YROHS` | C | 1 | 0 | CANDIDATE_REQUIRED | NONE | — | — | — | — | 01,05 | NEW_CANONICAL | PROVEN | RoHS ? / RoHS ?/OBRIGAT flag; DELPI |
| generic_supplier | Fornecedor genérico | Flag de fornecedor genérico DELPI (só 01/05). | SA2 | SA2010 | `A2_YFGEN` | C | 1 | 0 | PROVEN_OPTIONAL | NONE | — | — | — | — | 01,05 | NEW_CANONICAL | PROVEN | For Generico / Fornecedor Generico/DELPI |
| purchase_price_table_code | Tabela de preço | Tabela de preço de compra (AIA). | SA2 | SA2010 | `A2_ZTABPRC` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | — | AIA | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Tab Prc Comp / Tab Prc Comp/DELPI |
| carrier_code | Transportadora | Transportadora padrão (SA4). | SA2 | SA2010 | `A2_TRANSP` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | vazio().or.existcpo("SA4") | SA4 | — | 01,03,04,05 | REUSED_PROVEN | PROVEN | Transp. / Codigo da Transportadora/ |
| group_code | Grupo | Código de grupo — 0% povoado; grupos reais em SAD. | SA2 | SA2010 | `A2_GRUPO` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio().or.ExistCpo("SX5","Y7"+M->A2_GRUPO,1) | SX5-Y7 | — | 01,03,04,05 | NEEDS_REVIEW | PROVEN | Grupo / Grupo/não povoado; ver SAD |
| segment_code | Segmento | Segmento de atividade (SX5-T3). | SA2 | SA2010 | `A2_SATIV1` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | ExistCpo("SX5","T3"+M->A2_SATIV1) | SX5-T3 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Segmento 1 / Segmentacao de Ativid. 1/ |
| link_type_code | Vínculo | Tipo de vínculo (CC1). | SA2 | SA2010 | `A2_VINCULO` | C | 2 | 0 | PROVEN_OPTIONAL | NONE | — | ExistCpo("CC1") | CC1 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | P. Vinculo / Pessoa Vinculada/ |
| administrator_code | Administrador | Código do administrador (SAE). | SA2 | SA2010 | `A2_CODADM` | C | 3 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio() .Or. ExistCpo("SAE") | SAE | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | C¢d. Adm. / C¢digo Adm. Financeira/ |
| linked_customer_code | Cliente vinculado | Cliente vinculado ao fornecedor (SA1; par com loja). | SA2 | SA2010 | `A2_CLIENTE` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | ExistCpo("SA1", M->A2_CLIENTE ) | SA1 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | C¢d. Cliente / C¢digo Cliente/ |
| linked_customer_store | Loja do cliente | Loja do cliente vinculado. | SA2 | SA2010 | `A2_LOJCLI` | C | 2 | 0 | PROVEN_OPTIONAL | NONE | — | ExistCpo("SA1", M->A2_CLIENTE + M->A2_LOJCLI ) | SA1 | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | Loja Cliente / Loja Cliente/ |
| linked_employee_code | Funcionário vinculado | Funcionário vinculado (SRA). | SA2 | SA2010 | `A2_NUMRA` | C | 6 | 0 | PROVEN_OPTIONAL | NONE | — | Vazio() .Or. (ExistCpo("SRA") .And. A020NUMRA(M->A | SRA | — | 01,03,04,05 | NEW_CANONICAL | PROVEN | C¢d Func / C¢digo do funcion rio/ |

## De-para para integração externa

Extrato direto para consumo por integração (sem decisões de API):

| campo Minha DELPI | label | campo TOTVS | tabela | tipo | tam | obrigatoriedade | default | validação/lookup | observação |
|---|---|---|---|---|---|---|---|---|---|
| branch | Filial | `A2_FILIAL` | SA2010 | C | 2 | SYSTEM_GENERATED | blank=shared | — | system — não enviar |
| supplier_code | Código | `A2_COD` | SA2010 | C | 6 | SYSTEM_GENERATED | GETSXENUM("SA2") | IIF(Empty(M->A2_LOJA),.T.,ExistChav("SA2 | totvs_supplier_repository.py |
| supplier_store | Loja | `A2_LOJA` | SA2010 | C | 2 | UNKNOWN | '01' | existchav("SA2",M->a2_cod+M->a2_loja,,"E | padding inconsistente — normalizar |
| supplier_name | Razão social | `A2_NOME` | SA2010 | C | 50 | CANDIDATE_REQUIRED | — | A020CarEsp() | — |
| supplier_short_name | Nome fantasia | `A2_NREDUZ` | SA2010 | C | 20 | CANDIDATE_REQUIRED | — | A020CarEsp() | LEGACY_CONFLICT: trade_name |
| tax_id | CNPJ/CPF | `A2_CGC` | SA2010 | C | 14 | PROVEN_OPTIONAL | — | Vazio() .Or. IIF( M->A2_TIPO == 'X', .T. | não é chave; sinal de duplicidade |
| person_type | Tipo de pessoa | `A2_TIPO` | SA2010 | C | 1 | CANDIDATE_REQUIRED | IF(LEFT(SA2->A2_CGC,2) == '  ' | pertence("FJX") | CBOX/enum |
| address | Endereço | `A2_END` | SA2010 | C | 40 | CANDIDATE_REQUIRED | — | A020CarEsp() | — |
| address_number | Número | `A2_NR_END` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | — | — |
| address_complement | Complemento | `A2_ENDCOMP` | SA2010 | C | 21 | PROVEN_OPTIONAL | — | — | par ENDCOMP/COMPLEM |
| district | Bairro | `A2_BAIRRO` | SA2010 | C | 20 | CANDIDATE_REQUIRED | — | A020CarEsp() | — |
| postal_code | CEP | `A2_CEP` | SA2010 | C | 8 | CANDIDATE_REQUIRED | — | — | — |
| city | Município | `A2_MUN` | SA2010 | C | 25 | CANDIDATE_REQUIRED | — | A020CarEsp() | — |
| city_code | Código do município | `A2_COD_MUN` | SA2010 | C | 5 | CANDIDATE_REQUIRED | — | ExistCpo("CC2", FWFldGet("A2_EST") + FWF / CC2 | OBRIGAT flag |
| state | UF | `A2_EST` | SA2010 | C | 2 | CANDIDATE_REQUIRED | — | ExistCpo("SX5","12"+M->A2_EST) / SX5-12 | lookup SX5-12 |
| country_code | País | `A2_PAIS` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | Vazio() .or. ExistCpo("SYA",M->A2_PAIS) / SYA | — |
| bacen_country_code | País BACEN | `A2_CODPAIS` | SA2010 | C | 5 | CANDIDATE_REQUIRED | '01058' | ExistCpo("CCH") / CCH | OBRIGAT flag; OBSERVED_CONVENTION |
| po_box | Caixa postal | `A2_CX_POST` | SA2010 | C | 5 | PROVEN_OPTIONAL | — | — | — |
| state_registration | Inscrição estadual | `A2_INSCR` | SA2010 | C | 18 | PROVEN_OPTIONAL | — | IE(M->A2_INSCR,M->A2_EST) .And. A020VldU | WHEN condicional |
| municipal_registration | Inscrição municipal | `A2_INSCRM` | SA2010 | C | 18 | PROVEN_OPTIONAL | — | — | — |
| icms_contributor | Contribuinte ICMS | `A2_CONTRIB` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence(' 12') | — |
| simples_nacional | Simples Nacional | `A2_SIMPNAC` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence(" 12") | — |
| cnae_code | CNAE | `A2_CNAE` | SA2010 | C | 9 | CONDITIONAL | — | — | — |
| legal_entity_type | Tipo jurídico | `A2_TPJ` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence(" 12345") | semântica SX3 ampla |
| person_category | Categoria de pessoa | `A2_TPESSOA` | SA2010 | C | 2 | PROVEN_OPTIONAL | — | — | — |
| simp_regime_code | Regime SIMP | `A2_REGESIM` | SA2010 | C | 1 | PROVEN_OPTIONAL | "2" | — | default SX3 "2" |
| pb_regime_code | Regime PB | `A2_REGPB` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence(" 12" ) | — |
| financial_nature_code | Natureza financeira | `A2_NATUREZ` | SA2010 | C | 10 | CANDIDATE_REQUIRED | — | FinVldNat( .T. ,,2) .And. Vazio() .Or. / SED | OBRIGAT flag; RESTRICTED update |
| inss_withholding | Retenção INSS | `A2_RECINSS` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | pertence("SN") | default SX3 |
| iss_withholding | Retenção ISS | `A2_RECISS` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence("SN ") | — |
| csll_withholding | Retenção CSLL | `A2_RECCSLL` | SA2010 | C | 1 | PROVEN_OPTIONAL | "1" | Pertence("12") | default SX3 "1" |
| cofins_withholding | Retenção COFINS | `A2_RECCOFI` | SA2010 | C | 1 | PROVEN_OPTIONAL | "1" | Pertence("12") | default SX3 "1" |
| pis_withholding | Retenção PIS | `A2_RECPIS` | SA2010 | C | 1 | PROVEN_OPTIONAL | "1" | Pertence("12") | default SX3 "1" |
| irf_calculation | Calcula IRRF | `A2_CALCIRF` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence('1234') | — |
| inp_calculation | Calcula INSS | `A2_CALCINP` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | Pertence("12") | — |
| tax_group_code | Grupo tributário | `A2_GRPTRIB` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | — | — |
| esocial_category_code | Categoria eSocial | `A2_CATEFD` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | — / S049BR | — |
| contact_name | Contato | `A2_CONTATO` | SA2010 | C | 15 | CANDIDATE_REQUIRED | — | — | OBRIGAT flag |
| commercial_contact_name | Contato comercial | `A2_CONTCOM` | SA2010 | C | 15 | PROVEN_OPTIONAL | — | — | — |
| area_code | DDD | `A2_DDD` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | — | 46 ocorrências em código |
| country_calling_code | DDI | `A2_DDI` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | IIF(!EMPTY(M->A2_DDI), ExistCpo("ACJ",M- / ACJ | — |
| phone | Telefone | `A2_TEL` | SA2010 | C | 50 | CANDIDATE_REQUIRED | — | — | OBRIGAT flag |
| fax | Fax | `A2_FAX` | SA2010 | C | 15 | PROVEN_OPTIONAL | — | — | — |
| email | E-mail | `A2_EMAIL` | SA2010 | C | 50 | CANDIDATE_REQUIRED | — | — | OBRIGAT flag |
| website | Site | `A2_HPAGE` | SA2010 | C | 30 | PROVEN_OPTIONAL | — | — | — |
| responsible_name | Responsável | `A2_NOMRESP` | SA2010 | C | 45 | PROVEN_OPTIONAL | — | — | — |
| payment_condition_code | Condição de pagamento | `A2_COND` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | vazio().or.existcpo("SE4") / SE4 | — |
| payment_method_code | Forma de pagamento | `A2_FORMPAG` | SA2010 | C | 2 | CANDIDATE_REQUIRED | — | Vazio() .Or. ExistCpo("SX5", "58" + M->A / SX5-58 | OBRIGAT flag |
| accounting_account | Conta contábil | `A2_CONTA` | SA2010 | C | 20 | CANDIDATE_REQUIRED | — | vazio().or. Ctb105Cta() / CT1 | OBRIGAT flag; RESTRICTED |
| credit_limit_amount | Limite de crédito | `A2_LC` | SA2010 | C | 14 | DO_NOT_SEND | — | — | provável DO_NOT_SEND |
| risk_code | Risco | `A2_RISCO` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | — | — |
| bank_code | Banco | `A2_BANCO` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | — / SA6 | sensível |
| bank_branch | Agência | `A2_AGENCIA` | SA2010 | C | 5 | PROVEN_OPTIONAL | — | — | sensível |
| bank_branch_digit | DV agência | `A2_DVAGE` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | — | sensível |
| bank_account | Conta bancária | `A2_NUMCON` | SA2010 | C | 10 | PROVEN_OPTIONAL | — | — | sensível |
| bank_account_digit | DV conta | `A2_DVCTA` | SA2010 | C | 2 | PROVEN_OPTIONAL | — | — | sensível |
| bank_account_type | Tipo de conta | `A2_TIPCTA` | SA2010 | C | 1 | PROVEN_OPTIONAL | "1" | Pertence("12") / CBOX | par TIPCTA/TPCONTA |
| swift_code | SWIFT | `A2_SWIFT` | SA2010 | C | 30 | PROVEN_OPTIONAL | — | — | uppercase |
| payee_code | Favorecido | `A2_CODFAV` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | Vazio() .Or. ExistCpo("SA2") / SA2 | — |
| payee_store | Loja favorecido | `A2_LOJFAV` | SA2010 | C | 2 | PROVEN_OPTIONAL | — | Vazio() .Or. ExistCpo("SA2",M->A2_CODFAV | — |
| blocked | Bloqueado | `A2_MSBLQL` | SA2010 | C | 1 | SYSTEM_GENERATED | "2" | pertence("12") | SYSTEM_GENERATED; RESTRICTED |
| rohs_indicator | RoHS | `A2_YROHS` | SA2010 | C | 1 | CANDIDATE_REQUIRED | — | — | OBRIGAT flag; DELPI |
| generic_supplier | Fornecedor genérico | `A2_YFGEN` | SA2010 | C | 1 | PROVEN_OPTIONAL | — | — | DELPI |
| purchase_price_table_code | Tabela de preço | `A2_ZTABPRC` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | — / AIA | DELPI |
| carrier_code | Transportadora | `A2_TRANSP` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | vazio().or.existcpo("SA4") / SA4 | — |
| group_code | Grupo | `A2_GRUPO` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | Vazio().or.ExistCpo("SX5","Y7"+M->A2_GRU / SX5-Y7 | não povoado; ver SAD |
| segment_code | Segmento | `A2_SATIV1` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | ExistCpo("SX5","T3"+M->A2_SATIV1) / SX5-T3 | — |
| link_type_code | Vínculo | `A2_VINCULO` | SA2010 | C | 2 | PROVEN_OPTIONAL | — | ExistCpo("CC1") / CC1 | — |
| administrator_code | Administrador | `A2_CODADM` | SA2010 | C | 3 | PROVEN_OPTIONAL | — | Vazio() .Or. ExistCpo("SAE") / SAE | — |
| linked_customer_code | Cliente vinculado | `A2_CLIENTE` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | ExistCpo("SA1", M->A2_CLIENTE ) / SA1 | — |
| linked_customer_store | Loja do cliente | `A2_LOJCLI` | SA2010 | C | 2 | PROVEN_OPTIONAL | — | ExistCpo("SA1", M->A2_CLIENTE + M->A2_LO / SA1 | — |
| linked_employee_code | Funcionário vinculado | `A2_NUMRA` | SA2010 | C | 6 | PROVEN_OPTIONAL | — | Vazio() .Or. (ExistCpo("SRA") .And. A020 / SRA | — |

## Governança da futura API de fornecedores

Quando a API DELPI de fornecedores for implementada:

1. os nomes deste dicionário são o baseline canônico;
2. qualquer divergência deve ser justificada e documentada;
3. nomes já publicados não devem ser renomeados silenciosamente;
4. novos campos entram primeiro neste dicionário ou são reconciliados durante o contract design;
5. nomes físicos `A2_*` ficam restritos à camada adapter/persistence;
6. Domain/Application não dependem dos nomes físicos `A2_*`.

## Conflitos de nomenclatura legados (registrados, não renomeados)

| conceito | nomes concorrentes encontrados | consumers | decisão do dicionário |
|---|---|---|---|
| `A2_NREDUZ` (nome fantasia) | `supplier_short_name` (`totvs_supplier_repository.py`, OpenAPI baseline) × `trade_name` (`safety_stock_sql.py`) | contracts públicos + queries internas | `supplier_short_name` — já publicado |
| `A2_LOJA` | `supplier_store` × `loja`/`store` (params legados) | query params PT legados | `supplier_store` |
| `A2_MSBLQL` | `blocked` (boolean normalizado) × `msblql` (alias físico interno) | `totvs_supplier_repository.py` | `blocked` |
| `A2_NATUREZ` | `financial_nature_code` × `nature` (baseline) | baseline OpenAPI | `financial_nature_code` — `nature` é nome ambíguo |
| `A2_ENDCOMP` × `A2_COMPLEM` | dois campos físicos para complemento | — | `address_complement` → NEEDS_REVIEW (qual campo físico) |
| `A2_TIPCTA` × `A2_TPCONTA` | dois campos físicos para tipo de conta | — | `bank_account_type` → NEEDS_REVIEW |

`API_DESIGN_QUESTIONS: NONE — OUT OF SCOPE` — este documento não define endpoints, verbos, payload, idempotência, erros, autenticação nem regras da ponte.

## Identidade e chave

| Item | Regra |
|------|-------|
| Chave de negócio | `A2_FILIAL + A2_COD + A2_LOJA` (única física: `SA2010_UNQ`) |
| `A2_CGC` (CNPJ/CPF) | **Não** é chave — duplicado em base (mesmo CGC com códigos distintos) e pode ser vazio |
| `A2_LOJA` | Convenção observada `'01'` (não é default de dicionário); base contém valores sujos (`'1 '`, `' 1'`) — normalizar com `RTRIM`/`zfill(2)`. Quem informa no create (caller/ponte/rotina) é decisão de contrato — não assumir como requisito público |
| `A2_FILIAL` | Branco = cadastro compartilhado entre filiais (MODO=C); nunca filtrar por filial fixa sem tratar branco |

## Geração de código

`A2_COD` default = `GETSXENUM("SA2")` (sequencial 6 dígitos, ex.: `003929`) nas empresas 01 e 05. Empresas 03/04 **não têm** o default, e existem códigos manuais (`VIAGEM`, `FISCO`, `UNIAO`…). A ponte/API de escrita não deve gerar `MAX+1` próprio — delegar à rotina Protheus.

## Bloqueio (`A2_MSBLQL`)

`'1'` = bloqueado (104 registros); `'2'` = ativo; **vazio** em ~4% — tratar branco como "não bloqueado" somente após decisão de contrato (ver playbook §26/§39).

## Obrigatoriedade

Fill-rate alto **não** prova obrigatoriedade. Campos com ~100% de preenchimento (`A2_NOME`, `A2_EST`, `A2_CODPAIS`…) são `CANDIDATE_REQUIRED` até prova de bloqueio na MATA020. Campos marcados `OBRIGAT` no dicionário (`A2_TEL`, `A2_EMAIL`, `A2_CONTATO`, `A2_FORMPAG`…) têm histórico com branco — flag de dicionário ≠ bloqueio comprovado no create. Matriz completa: playbook §8/§28.

## Campos DELPI na SA2

| Campo | Significado |
|-------|-------------|
| `A2_YROHS` | RoHS? (67% preenchido; marcado obrigatório no dicionário) |
| `A2_YFGEN` | Fornecedor genérico |
| `A2_ZTABPRC` | Tabela de preço de compra → `AIA` |

## O que NÃO fazer

- Não assumir `SA2` = todo o cadastro: bancário e contato estão **na própria SA2** (conta única; PIX é dado de pagamento financeiro, não do cadastro).
- Não confundir `SA5` (produto × fornecedor, rotina MATA061) com o cadastro (MATA020) — fornecedor existe sem SA5; amarração é operação separada.
- Não usar `A2_GRUPO` como grupo real — não é povoado; grupos vivem em `SAD` (Grupo × Fornecedor).
- Não enviar campos técnicos (`D_E_L_E_T_`, `R_E_C_*`, `S_T_A_M_P_`, `I_N_S_D_T_`) nem acumuladores (`A2_MCOMPRA`, `A2_ULTCOM`…) em CREATE/UPDATE.

## Lookups frequentes

`A2_EST`→SX5 `'12'`; `A2_COD_MUN`→CC2 (por UF); `A2_CODPAIS`→CCH (`01058` = Brasil); `A2_PAIS`→SYA; `A2_COND`→SE4; `A2_NATUREZ`→SED; `A2_BANCO`→SA6; `A2_CONTA`→CT1; `A2_FORMPAG`→SX5 `'58'`.
