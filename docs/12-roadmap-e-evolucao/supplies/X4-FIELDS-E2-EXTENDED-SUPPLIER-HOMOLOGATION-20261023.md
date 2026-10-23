# X4.FIELDS.E2 — Extended Supplier Fields Implementation & Homologation

**Data:** 2026-10-23 · **Executor:** Devin (Backend/Integrations) · **Base:** `c7586034f0` → `f95c7213eb` (rebase)
**Status:** `ACCEPT_WITH_RESIDUAL` — CNPJ `PROVEN`, 29/33 campos `PERSISTENCE_PROVEN`, 4 `IGNORED`, 3 `TEST_NOT_RUN`.

---

## 1. Baseline e authorities

- HEAD inicial `c7586034f0bd8e6378c3259d677ead5c2985ea08` = origin/main; `git status` limpa.
- Ancestralidade revalidada: E1 `b77d1be3a6`, E1.P1 `c666e96af0`, E1.P1 review `792fc70d75` — todos ancestrais do HEAD.
- Authorities lidas: instruções oficiais GPT Arquiteto, `supplies/README.md`, `IMPLEMENTATION-PLAN.md`, E1, E1.P1, `cadastro-fornecedor.md`, `playbook-cadastro-fornecedor-sa2.md`, `protheus-rest-supplier-api-contract.md`, `protheus-rest-supplier-post-field-matrix.md`, regras `.cursor` materiais (evidence-driven, api-contracts, data-persistence, sql-query, security, quality, delivery, totvs-product-patterns, root-cause, test-and-commit, local-first-deploy).

## 2. Autorização e gate de escrita

| Gate | Resultado |
|---|---|
| TARGET_DATABASE | `DELPI_TST01` — provado em runtime: `environment_key=ambiente:1@192.168.1.233:8701` + read-back SQL |
| TARGET_REST | `VERIFIED` — `URL_REST=http://192.168.1.233:8701/rest`, `PATH_SUPPLIERS=/delpi/api/v1/suppliers` via `PARAMETROS_MINHADELPI`/`AMBIENTE=1` |
| PRODUCTION_SQL | `NOT_TARGET` — guard de script aborta se env divergir; `_delpi_safety_check` pós-escrita `true` em todos os lotes; varredura final `A2_NREDUZ LIKE 'ZZ HOMOLOG E2%'` em `DELPI` = 0 linhas |
| ERP_WRITE_GATE | `CONTROLLED` — flag `PROTHEUS_SUPPLIER_CREATE_ENABLED=true` apenas no `docker exec` do ensaio; env dos containers permaneceu `CREATE=false`/`UPDATE=false` (verificado pós-ensaio) |
| AUTHORIZED_ACTOR | `VERIFIED` — `3bfdd634-a3a5-41af-b6b3-607025c2bdf5` → Core `mapping_status=mapped`, `verified=true`, `protheus_user_id=000311` (codusr resolvido no backend) |
| TEST_SUPPLIER | `APPROVED` — fictício `ZZ HOMOLOG E2 B* TESTE`, CNPJs `98.887.766/02xx-xx` com DV mod-11 válido |
| CLEANUP_PLAN | Padrão dos resíduos anteriores: registros permanecem identificados `ZZ HOMOLOG E2*` em TST01; bloqueio `A2_MSBLQL` pelo owner se necessário (sem DELETE via API) |

Execução técnica isolada: script auditável versionado (`api-delpi/scripts/protheus_supplier_extended_homologation.py`), executado dentro do container `delpi-api-delpi` com flag efêmera — **nenhuma alteração de env/config/imagem**, nenhum POST por SQL direto, nenhuma alteração MATA020.

## 3. Contrato atual

- Publicado: **24 campos** POST (`fornecedor` objeto), `{codusr, fornecedor}` upstream; `codusr` resolvido no backend; identidade do cliente rejeitada; desconhecidos rejeitados; `tax_id` ≤14 dígitos com zeros à esquerda.
- Experimental: `EXPERIMENTAL_SUPPLIER_FIELD_SPECS` = **60 campos** (24 publicados + **36 candidatos**). Nota: o doc E1 citava 35 — o spec vigente tem 36 (`municipal_registration` está no superset fora dos 24 publicados). TO_INVENTORY: reconciliar a contagem documental E1.
- Descoberta operacional nova: o endpoint upstream exige como **obrigatórios** `rohs_indicator`, `accounting_account`, `bacen_country_code`, `payment_method_code`, `financial_nature_code`, `payment_condition_code` (1ª tentativa do Lote 0 → 400 "Campos Obrigatorios Não Preenchidos"). Todos são campos do contrato publicado; o create `003875` histórico já os enviava.

## 4. Implementação realizada

1. **`CreateProtheusRestSupplierUseCase`**: novo parâmetro injetável `field_normalizer` (default = normalizador publicado). Permite compor o normalizador experimental apenas no ensaio, sem alargar a rota pública. Zero alteração de contrato/rota/RBAC.
2. **`scripts/protheus_supplier_extended_homologation.py`** (novo, versionado): guard de ambiente → normalização (publicada ou experimental) → `resolve_actor_codusr` → `build_upstream_create_body` → tracking fail-closed (`begin` antes do POST, `record_ack`, `confirm`) → POST → read-back SQL `DELPI_TST01.dbo.SA2010` → veredito por campo → `_delpi_safety_check`. Sem retry automático.
3. Testes: +1 caso de injeção de normalizador; suíte supplier/protheus focada **74 PASS**.

## 5. CNPJ — causa raiz `PROVEN`

| Registro | CNPJ enviado | DV | Resultado |
|---|---|---|---|
| `003874/01` (F4.3) | `98887766000396` | **inválido** (correto `...304`) | `A2_CGC` vazio |
| `003878/01` | `98887766000134` | válido | persistiu |
| `003875/01` | `98887766000215` | válido | persistiu |
| `003874/01` (2ª tentativa) | `98887766000477` | **inválido** (correto `...487`) | `A2_CGC` vazio |
| **`003876/01` (E2 Lote 0)** | `98887766020089` | **válido** | **persistiu** |

**Causa raiz:** a `api-delpi` serializa `tax_id` corretamente (prova: outbound payload no tracking + persistência de todos os CNPJs válidos). O endpoint upstream/Execauto **descarta silenciosamente** `tax_id` com dígito verificador inválido — retorna 200 + código, sem erro. Não há defeito a corrigir na `api-delpi`; o comportamento upstream é `TO_INVENTORY` para Gabriel/TOTVS (validação silenciosa de DV de CNPJ).

**Evidência Lote 0 (`003876/01`, op `53db8e47-a35f-4f7a-bd4d-a102321fc756` → `CONFIRMED`):**
- REST GET: `tax_id=98887766020089`, `supplier_name=ZZ HOMOLOG E2 B0 TESTE`.
- SQL `DELPI_TST01.SA2010`: `A2_CGC=98887766020089` + todos os obrigatórios (`A2_YROHS=N`, `A2_CONTA=21101559`, `A2_NATUREZ=2094`, `A2_COND=166`, `A2_FORMPAG=45`, `A2_CODPAIS=01058`).

## 6. Resultados por lote

| Lote | Fornecedor | Operação | Resultado |
|---|---|---|---|
| 0 (controle/CNPJ) | `003876/01` | `53db8e47` CONFIRMED | **MATCH** — CNPJ + 22 campos base `PERSISTED` |
| 1a (simples) | `003877/01` | `9ba53cac` CONFIRMED | **MATCH** — 6/6 estendidos `PERSISTED` |
| 1b (simples) | `003879/01` | `84ef993f` CONFIRMED | **MATCH** — 6/6 `PERSISTED` |
| 1c (simples) | `003880/01` | `a68ebc4d` CONFIRMED | **MATCH** — 6/6 `PERSISTED` |
| 2 (condicionais) | `003881/01` | `d8f52d6f` CONFIRMED | `PARTIAL` — 4/5 `PERSISTED`; `person_category` `IGNORED` |
| 3 (lookups) | `003882/01` | `24809a73` CONFIRMED | `PARTIAL` — 7/9 `PERSISTED`; `payee_*` `IGNORED`; 3 não enviados |
| 4 (custom) | `003883/01` | `24e1c67f` CONFIRMED | `PARTIAL` — `purchase_price_table_code` `PERSISTED` (2ª evidência); `generic_supplier` `IGNORED` |
| 0 (1ª tentativa) | — | `b6185441` REJECTED | 400 "Campos Obrigatorios Não Preenchidos" — faltavam obrigatórios upstream |

7 fornecedores criados em `DELPI_TST01` (`003876`, `003877`, `003879`–`003883` loja `01`). `003878` é resíduo F4 preexistente.

## 7. Field-by-field persistence (33 candidatos enviados)

**PERSISTED (29):** `address_number`→A2_NR_END · `po_box`→A2_CX_POST · `icms_contributor`→A2_CONTRIB · `simples_nacional`→A2_SIMPNAC · `inss_withholding`→A2_RECINSS · `iss_withholding`→A2_RECISS · `csll_withholding`→A2_RECCSLL · `cofins_withholding`→A2_RECCOFI · `pis_withholding`→A2_RECPIS · `irf_calculation`→A2_CALCIRF · `inp_calculation`→A2_CALCINP · `tax_group_code`→A2_GRPTRIB · `commercial_contact_name`→A2_CONTCOM · `fax`→A2_FAX · `website`→A2_HPAGE · `responsible_name`→A2_NOMRESP · `risk_code`→A2_RISCO · `swift_code`→A2_SWIFT · `cnae_code`→A2_CNAE · `legal_entity_type`→A2_TPJ · `simp_regime_code`→A2_REGESIM · `pb_regime_code`→A2_REGPB · `carrier_code`→A2_TRANSP · `segment_code`→A2_SATIV1 · `administrator_code`→A2_CODADM · `linked_customer_code`→A2_CLIENTE · `linked_customer_store`→A2_LOJCLI · `linked_employee_code`→A2_NUMRA · `purchase_price_table_code`→A2_ZTABPRC (×2)

**IGNORED (4):** `person_category`→A2_TPESSOA (enviou `01`, coluna vazia) · `payee_code`→A2_CODFAV · `payee_store`→A2_LOJFAV (par composto ignorado junto) · `generic_supplier`→A2_YFGEN (campo custom DELPI — provável não mapeado no endpoint do Gabriel)

**TEST_NOT_RUN (3):** `country_calling_code` (ACJ010 sem linha elegível em TST01) · `link_type_code` (CC1010 sem linha elegível) · `esocial_category_code` (semântica S049BR pendente de owner — excluído por precaução)

**Não candidatos / excluídos por contrato:** bancários pendentes LGPD, acumuladores/credit_limit, identidade/sistema (`branch`, `supplier_code`, `blocked`, `codusr`), `group_code`, conflitos físicos (`address_complement`, `bank_account_type`), `DO_NOT_SEND`. Nenhum enviado.

## 8. Testes

- **Unit/regressão:** 74 testes focados PASS (create use-case + extended fields + payload). Suíte ampla: falha pré-existente não relacionada em `test_davi_product_master_extensions.py` (contagem de actions 94→95; falha também na base limpa — drift externo, `TO_INVENTORY`).
- **Contrato:** normalizador publicado inalterado — rota pública continua rejeitando os 36 candidatos; identidade técnica protegida (`codusr` backend-only).
- **Integração real:** 7 POSTs REST + read-back SQL independente + REST GET (Lote 0) + tracking CONFIRMED em todas.

## 9. Segurança e produção

- Secrets nunca impressos (`<set>`); payloads sanitizados; CNPJs fictícios com DV válido.
- Escrita apenas via REST autorizada com tracking fail-closed; zero SQL write; zero alteração MATA020/RBAC/permissões.
- Flags produtivas `PROTHEUS_SUPPLIER_CREATE_ENABLED=false` / `UPDATE=false` **confirmadas** nos containers `delpi-api-delpi` e `delpi-supplies-api` após o ensaio.
- `DELPI.SA2010`: 0 linhas `ZZ HOMOLOG E2*`; nenhuma conexão de leitura do Portal alterada.
- Residual conhecido mantido: transporte `http_cleartext` (documentado desde P1).

## 10. Impacto de contrato

- **Zero mudança pública**: os 33 campos permanecem experimentais; promoção exige decisão de contrato + versionamento. `field_normalizer` é composição interna, não superfície HTTP.
- **Evolução candidata:** 29 campos `PERSISTENCE_PROVEN` fundamentam proposta de contrato público ampliado (próximo passo, com owner).
- **Obrigatórios upstream descobertos** (6 campos) já constam do contrato publicado — documentar como required no OpenAPI/playbook em iteração de contrato.

## 11. Resíduos e limpeza

- 7 fornecedores `ZZ HOMOLOG E2*` em `DELPI_TST01` — mesma política dos resíduos F4 (identificados, bloqueio `A2_MSBLQL` se o owner exigir). Nenhum dado real usado; valores de lookup lidos de TST01 (nunca de produção).

## 12. UNRESOLVED / NEXT STEP

- Handoff Gabriel/TOTVS: (a) descarte silencioso de `tax_id` com DV inválido; (b) `A2_TPESSOA`, `A2_CODFAV`/`A2_LOJFAV`, `A2_YFGEN` ignorados — confirmar nomes de campos REST esperados; (c) lista de obrigatórios upstream.
- `country_calling_code`/`link_type_code`/`esocial_category_code`: semear ACJ/CC1 em TST01 ou obter valores válidos do owner; semântica S049BR.
- Proposta de contrato público ampliado com os 29 campos comprovados — decisão de owner + versioning.
- `DELPI_TST_WS` permanece sem owner identificado (herdado de P1).


## 13. Revisão GPT — aceite arquitetural E2 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para o ensaio de homologação**, com base no relatório de execução e evidências registradas no GitHub (commit de implementação `12a142877d`). O GPT não repetiu operações REST/SQL nem executou os testes no runtime; os resultados por lote são **reportados pelo executor**. O ensaio controlado produziu 7 registros fictícios em `DELPI_TST01`, com tracking, read-back e gates produtivos reportados OFF. **Não há autorização implícita para ativar campos publicamente.**

**Achado de precisão — contagem:** a documentação declara 24 campos publicados e 36 experimentais adicionais, atribuindo a diferença a `municipal_registration`. Porém `municipal_registration` já consta de `SUPPLIER_FIELD_SPECS` publicado; exigir comparação real de conjuntos (set difference) entre especificações publicadas e experimentais, e reconciliar `29 PERSISTED + 4 IGNORED + 3 TEST_NOT_RUN` antes de fixar cardinalidade executiva. Até a reconciliação: `COUNT_DRIFT = TO_INVENTORY`, não promover 36 como total novo comprovado.

**CNPJ:** `003876/01` com DV válido persistiu `A2_CGC` conforme GET REST e SQL TST01; registros históricos sem CNPJ possuíam documentos reportados como DV inválido. A associação é evidência forte da hipótese de rejeição/limpeza upstream por DV, **mas a regra interna exata e o motivo de resposta de sucesso sem erro ainda são `TO_INVENTORY`** (owner Gabriel/TOTVS). Classificar `TAX_ID_PERSISTENCE_VALID_CASE = PROVEN`; `TAX_ID_ROOT_CAUSE_INTERNAL = INCONCLUSIVE`, em vez de atribuir execução específica ao Execauto sem observabilidade.

**Evolução de contrato:** 29 campos relatados como persistidos são candidatos para **proposta** de exposição. Confirmar inventário dos campos, semântica, minimização/LGPD, dependências, AuthZ, GET/PUT e versionamento, antes de promover; quatro ignorados não entram na allowlist e três não testados continuam fora. Os 6 campos relatados como obrigatórios no upstream precisam ser distinguidos entre rejeição geral de payload incompleto e obrigação isolada de cada campo (validar evidência por campo). A `EXPERIMENTAL_PUT_ALLOWLIST` não equivale a PUT homologado.

**Segurança/resíduos:** foram criados sete registros fictícios em homologação. Bloqueio futuro em `A2_MSBLQL` não é rollback reversível e exige ação/critério do owner. Verificar política de limpeza/isolamento e preservar evidência de que a base `DELPI` não foi alvo. O transporte HTTP cleartext permanece risco residual já conhecido.

**Próximo gate sugerido:** E2.R1 de **reconciliação de contagem + evidência por campo + proposta de contrato**, inicialmente documental/read-only. Nenhuma nova escrita, nenhum deploy e nenhuma expansão BFF/MFE nesta revisão.
