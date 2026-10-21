# Handoff — evolução da integração REST de fornecedores Protheus (POST/PUT)

**Registro:** 2026-10-19  
**Atualização:** F3/F3.1 2026-10-20 — registry compartilhado `SUPPLIER_FIELD_REGISTRY` no MFE passa a ser a fonte única de campos/seções para criação, consulta e edição (25 specs: 24 POST + `supplier_code` system-generated). Cada campo carrega capacidade POST, capacidade PUT (`editable` somente com evidência `put-contract`), origem do valor no GET (`section`/`top`/`identity`) e evidência contratual. A ficha em modo edição exibe todas as seções do formulário de inclusão; campos sem evidência PUT aparecem somente leitura. PUT envia **somente campos alterados** (parcial, sem read-modify-write) e a verificação "Conferir gravação" compara o GET posterior. Feature gates de POST/PUT continuam avaliados antes da identidade Core. Live write continua bloqueado.  
**Base:** reancorar sempre em `origin/main`.

> Documento de continuidade. Não autoriza live write em produção. Lacunas de contrato permanecem `TO_INVENTORY`.

## Objetivo

Permitir **criação (POST)** de fornecedores via REST Protheus com `api-delpi` como owner da integração, identidade via **Core API**, feature gate fechado até homologação. PUT fica para entrega futura.

## Reuse gate

| Conceito | Decisão |
|---|---|
| OAuth / token cache / gateway GET / params Intranet | `EXISTING_EQUIVALENT=YES` → `REUSE_DECISION=EXTEND` |
| Identidade Protheus Core | `EXISTING_EQUIVALENT=YES` → `REUSE_DECISION=EXTEND` (S2S read) |
| POST fornecedor | `EXISTING_EQUIVALENT=NO` → novo use case + método gateway sem retry |

## Estado

| Tema | Estado |
|---|---|
| `POST /integrations/protheus/suppliers` | PROVEN no código (gate default off) |
| `operationId` `create_protheus_rest_supplier` | PROVEN |
| Permissão `api-delpi.integrations.protheus.suppliers.create` | PROVEN (manifest 1.0.2) |
| Feature gate `PROTHEUS_SUPPLIER_CREATE_ENABLED` | PROVEN default `false`; avaliado antes do Core |
| Matriz REST→SA2 | PROVEN doc `protheus-rest-supplier-post-field-matrix.md` |
| Payload sucesso / `A2_COD` / idempotência / `codusr≡USR_ID` | TO_INVENTORY |
| PUT `update_protheus_rest_supplier` | PROVEN no código; gate `PROTHEUS_SUPPLIER_UPDATE_ENABLED` default `false`; allowlist ampliada (F3.3, decisão PO) para **todos os campos cadastrais do POST exceto `tax_id`, `supplier_code`, `supplier_store`** — campos além de name/short_name marcados `po-decision`, upstream pendente |
| Live write produção | BLOCKED (2026-10-20): POST real não autorizado; PUT live TEST_NOT_RUN |
| Integration Tracking (F4) | PROVEN código+migrations V001/V002; runtime TST01 registrou CREATED→SENDING→ACKNOWLEDGED/REJECTED/RECONCILIATION_REQUIRED com `attempt_count=1`, sem retry |
| F4.3 correções | `confirm()` com `evidence` corrigido (defeito `confirmation_record_failed`); parser REST passa a extrair `details`/`detail` e classifica 4xx com evidência como REJECTED (era UNKNOWN/502); divergência `tax_id→A2_CGC` é boundary upstream — `CREATE_CONTRACT=PENDING_UPSTREAM` (handoff em `evidence/protheus-rest-supplier-f43-homologation-2026-10-21.md`) |
| POST retorno `supplier_code`/`supplier_store` | PROVEN runtime 2026-10-21 (upstream evoluiu); contrato formal PENDING owner |

## Critérios de homologação live (bloqueados)

Gate específico para habilitação real de POST/PUT — **todos** os itens exigidos antes de qualquer escrita no ERP:

1. Owner TOTVS confirma a **matriz de campos** (POST e PUT) e a **obrigatoriedade real do MATA020** por campo.
2. Owner TOTVS confirma shape de sucesso do POST e a **regra de geração de `A2_COD`**.
3. Confirmação formal `codusr` ≡ `SYS_USR.USR_ID` (equivalência identidade Core↔Protheus).
4. **PUT por campo**: evidência upstream de editabilidade para cada campo além da allowlist atual — sem evidência, o campo permanece `READ_ONLY`/bloqueado e a dependência fica registrada com o owner TOTVS.
5. Semântica de omissão e de **limpeza explícita** confirmadas (hoje string vazia/null é rejeitada com `PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED`).
6. Ambiente homologado + credenciais e transporte aprovados (rotação de credenciais OAuth + aceite de risco de transporte).
7. **Política de timeout/idempotência** definida: reconciliação para timeout pós-envio; nunca retry automático de POST/PUT.
8. **Teste controlado de persistência**: POST/PUT em homologação seguido de GET de conferência comparando os campos enviados.
9. **Autorização explícita** do PO + owner TOTVS; feature gate ligado **somente** após esse aceite.

Se as evidências não existirem, a entrega permanece com código e interface prontos e **escrita bloqueada** (`write_disabled`).

## Referências

- `protheus-rest-supplier-api-contract.md`
- `protheus-rest-supplier-post-field-matrix.md`
- `protheus-rest-read.md`
- `docs/11-padroes-de-desenvolvimento/core-protheus-identity-ownership.md`
- playbook SA2 §44.3


## F4.4 — Fechamento do cenário CREATE com 18 campos (2026-10-21)

O owner Gabriel **já entregou** `Campos Obrigatorios.xlsx` (18 mapeamentos). A homologação POST `003875/01` na `DELPI_TST01` retornou **código `003875` e loja `01`**, com **18/18 MATCH** por SQL, incluindo `tax_id→A2_CGC`. Tracking ficou `CONFIRMED` e gates CREATE/UPDATE OFF ao final. Ver [evidência F4.4](../../../docs/12-roadmap-e-evolucao/supplies/evidence/suppliers-f44-create-18-field-sql-confirmation-2026-10-21.md).

A pendência `A2_CGC vazio` do teste `003874/01` permanece **caso histórico divergente**, não bloqueio do cenário F4.4. O documento inválido pelo DV é hipótese forte de explicação, **não causa raiz upstream definitivamente provada**. Recomendação: nova fatia de validação CNPJ/DV antes do envio, retornando 422, sem nova escrita real. Registros `003874/01` e `003875/01` bloqueados, a tratar pelo owner TOTVS. GET upstream incompleto; paridade 18/18 confirmada por SQL, não via GET. Endpoint produtivo informado mas **não ativado**; manter REST de teste `:8701` e gates OFF fora de janelas homologadas.
