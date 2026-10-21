# F4.4 — CREATE fornecedor / verificação SQL dos 18 campos (2026-10-21)

**Fonte de evidência:** relatório de execução Cursor/Devin fornecido pelo Product Owner. **Classificação de revisão GPT:** `ACCEPT_WITH_RESIDUAL` — homologação funcional CREATE aceita no cenário exercitado; hipóteses de causa upstream e limites de cobertura permanecem explícitos. O presente documento é evidência reportada, não uma nova execução de banco ou runtime pelo revisor.

## Baseline da execução reportada

- Repo remoto `main @ ba68c5a306` (clean, conforme executor); API DELPI image `786e8c0221db`, construída com fix F4.3 (`3c0484ec`); supplies-api image `2f920abf`, ambas healthy.
- Runtime de aplicação no `srv-api`; REST `192.168.1.233:8701` → `DELPI_TST01`; SQL de conferência `DELPI_TST01.dbo.SA2010` em `192.168.1.230`; tracking PG `plugins_hub.integration_tracking`.
- Core: operador autorizado mapeado a `codusr=000311` via backend; S2S individual `supplies-api`.
- Gates CREATE/UPDATE **OFF antes**; somente CREATE ligado na janela; **ambos OFF depois** (confirmados no runtime). `DELPI` produtivo não foi destino da escrita.
- PRs documentais #102/#103 ainda não integrados na verificação do executor; receber a planilha de 18 campos **não está pendente**.

## Operação CREATE (uma tentativa)

- REST HTTP **200**, mensagem `Fornecedor Incluido com sucesso.`; `supplier_code=003875`, `supplier_store=01` retornados; `operation_id=2e3f7f3e-9fe6-4a10-a15b-1de6bb9a58dd`.
- SQL `DELPI_TST01.SA2010` encontrou **uma linha** para `003875/01`; registro bloqueado `A2_MSBLQL=2`, `D_E_L_E_T_=' '`.
- GET REST do registro 200; identidade e `tax_id` correspondem ao SQL. GET não expõe o cadastro completo: confirmação dos 18 campos foi por SQL, **não pelo GET**.
- Tracking `CONFIRMED`, `attempt_count=1`, `caller_app=supplies-api`, ator Core validado, `environment_key=ambiente:1@...:8701`; evidência `READ_AFTER_WRITE / MATCH` com **24 checked_fields** reportados; eventos `operation_created → send_started → upstream_response → status_transition`; payload redigido sem CNPJ em claro.

## Matriz reportada: 18/18 MATCH em SQL

| Campo Minha DELPI | Campo SA2 | Resultado |
|---|---|---|
| `supplier_store` | `A2_LOJA` | MATCH (`01`) |
| `supplier_name` | `A2_NOME` | MATCH |
| `supplier_short_name` | `A2_NREDUZ` | MATCH |
| `tax_id` | `A2_CGC` | **MATCH** (CNPJ com dígitos verificadores válidos; valor mascarado na evidência) |
| `address` | `A2_END` | MATCH |
| `district` | `A2_BAIRRO` | MATCH |
| `postal_code` | `A2_CEP` | MATCH |
| `city` | `A2_MUN` | MATCH |
| `city_code` | `A2_COD_MUN` | MATCH |
| `state` | `A2_EST` | MATCH |
| `bacen_country_code` | `A2_CODPAIS` | MATCH |
| `financial_nature_code` | `A2_NATUREZ` | MATCH |
| `contact_name` | `A2_CONTATO` | MATCH |
| `area_code` | `A2_DDD` | MATCH |
| `phone` | `A2_TEL` | MATCH |
| `email` | `A2_EMAIL` | MATCH |
| `payment_condition_code` | `A2_COND` | MATCH |
| `accounting_account` | `A2_CONTA` | MATCH |

Campos adicionais `A2_TIPO=J`, `A2_INSCR=ISENTO`, `A2_PAIS=105` também persistidos conforme relato. A presença na planilha enviada pelo Gabriel prova a **entrega da relação de 18 mapeamentos**, não prova que todos são obrigatórios sem condição em qualquer cenário.

## Comparação com F4 anterior: hipótese sobre CNPJ

- Caso anterior `003874/01`: POST criou cadastro com `A2_CGC` vazio embora `fornecedor.tax_id` constasse do outbound. O documento informado nesse teste tinha DV inválido.
- Caso F4.4 `003875/01`: CNPJ com DV válido; `A2_CGC` persistido (MATCH).
- **Inferência forte, não prova de mecanismo interno:** o comportamento é compatível com validação de DV upstream e descarte silencioso do documento. Não afirmar como causa raiz definitivamente comprovada sem logs/código/declaração do owner TOTVS. Não declarar problema universal de mapeamento resolvido para todos os cenários.
- **Próxima melhoria proposta:** avaliar/implementar validação determinística do DV na `api-delpi` e retorno 422 antes de enviar POST; exige testes, contrato e aprovação de escopo. Não implementada nesta execução.

## Limites e residuais

1. Registros de teste `003874/01` (CGC vazio) e `003875/01` (F4.4) permanecem bloqueados em `DELPI_TST01`, sem limpeza SQL; tratamento via owner TOTVS.
2. GET upstream não projeta todos os 18 campos; não inferir paridade do GET.
3. Sem política aprovada de exposição em PROD para POST/PUT; gates OFF fora das janelas. Endpoint produtivo informado por Gabriel `http://192.168.1.231:8061/restall` **não foi selecionado nem testado**.
4. Validação antecipada de DV de CNPJ continua candidata para próxima fatia.
5. Confirmação específica de obrigatoriedade condicional dos campos ainda `TO_INVENTORY`.

## Classificação por critério (evidência reportada)

| Critério | Resultado |
|---|---|
| CREATE_PERSISTENCE | PASS — cenário F4.4, confirmação SQL |
| CREATE_FIELD_PARITY | PASS — 18/18 MATCH no mesmo registro e ambiente |
| TAX_ID_PERSISTENCE | PASS — `A2_CGC` presente |
| CREATE_TRACKING | PASS — `CONFIRMED`, operation_id e eventos |
| SECURITY | PASS reportado — autorização, S2S, redaction |
| GATE_FINAL | PASS reportado — ambos OFF |
| Produção `DELPI` | TEST_NOT_RUN — intencionalmente fora de escopo |

**Decisão de aceite:** `ACCEPT_WITH_RESIDUAL` do F4.4 com CREATE funcional homologado em TST01; sem liberação de escrita para `DELPI`. **Próximo passo:** validação CNPJ com DV antes do REST e decisão sobre tratamento dos registros de teste.
