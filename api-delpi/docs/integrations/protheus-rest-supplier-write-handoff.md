# Handoff — evolução da integração REST de fornecedores Protheus (POST/PUT)

**Registro:** 2026-10-19  
**Atualização:** implementação backend do POST (feature-gated); PUT permanece fora de escopo.  
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
| Feature gate `PROTHEUS_SUPPLIER_CREATE_ENABLED` | PROVEN default `false` |
| Matriz REST→SA2 | PROVEN doc `protheus-rest-supplier-post-field-matrix.md` |
| Payload sucesso / `A2_COD` / idempotência / `codusr≡USR_ID` | TO_INVENTORY |
| PUT | FORA_DO_ESCOPO |
| Live write produção | BLOCKED (2026-10-20): código implantado com gate off; POST real não autorizado nesta janela |

## Critérios de homologação live (bloqueados)

1. Owner TOTVS confirma shape de sucesso e geração de `A2_COD`.
2. Confirmação formal `codusr` ≡ `SYS_USR.USR_ID`.
3. Ambiente controlado + rotação de credenciais OAuth + aceite de risco de transporte.
4. Feature gate ligado **somente** após aceite explícito.
5. Reconciliação definida para timeout pós-envio (sem retry automático).

## Referências

- `protheus-rest-supplier-api-contract.md`
- `protheus-rest-supplier-post-field-matrix.md`
- `protheus-rest-read.md`
- `docs/11-padroes-de-desenvolvimento/core-protheus-identity-ownership.md`
- playbook SA2 §44.3
