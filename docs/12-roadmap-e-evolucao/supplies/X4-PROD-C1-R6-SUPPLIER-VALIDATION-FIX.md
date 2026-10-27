# X4.PROD-C1.R6 — SUPPLIER CREATE VALIDATION AND ERROR CONTRACT

Correção full-stack da divergência de obrigatoriedade do cadastro de
fornecedores e da degradação de mensagens de erro (`api-delpi client error`)
identificadas no RCA R5 (`7e314c2be2`).

- **Owners:** `api-delpi`, `supplies-api`, `plugins/supplies`
- **Base:** RCA `docs/12-roadmap-e-evolucao/supplies/X4-PROD-C1-R5-SUPPLIER-CREATE-FAILURE-RCA.md`
- **Escopo:** validação canônica pré-envio (POST), projeção segura de erros no
  BFF, UX de obrigatoriedade/validação no MFE, testes, Help, documentação.
- **Fora de escopo:** alterar REST produtivo, BASE_PATH, credenciais, gates
  CREATE/UPDATE, RBAC, PUT parcial, executar cadastro real.

## 1. Causa raiz (recap R5)

POST `/integrations/protheus/suppliers` em produção chegou ao Protheus sem os
campos que a rotina TOTVS exige → HTTP 400
`PROTHEUS_SUPPLIER_WRITE_REJECTED` («Campos Obrigatorios Não Preenchidos»).
Tracking: `CREATED → SENDING → REJECTED`. O BFF descartava o `detail`
sanitizado e o MFE exibia apenas `api-delpi client error`.

## 2. Obrigatoriedade comprovada (contrato vigente)

### 2.1 Incondicionais — POST

| Campo | Campo TOTVS | Regra |
|---|---|---|
| `supplier_store` | A2_LOJA | 2 dígitos (já era `required` antes do R6) |
| `rohs_indicator` | A2_YROHS | enum `S`/`N` |
| `bacen_country_code` | A2_CODPAIS | dígitos, catálogo BACEN |
| `payment_condition_code` | A2_COND | catálogo condições de pagamento |
| `payment_method_code` | A2_FORMPAG | catálogo formas de pagamento |
| `accounting_account` | A2_CONTA | catálogo plano de contas |
| `financial_nature_code` | A2_NATUREZ | catálogo naturezas financeiras |

Os seis campos do R5 foram promovidos a `required: True` em
`SUPPLIER_FIELD_SPECS` — mesma fonte canônica usada por POST e, por spec de
campo, pela validação de valor do PUT.

### 2.2 Condicionais comprovadas

- `cnae_code`: não se aplica a `person_type=F` (regra SX3 WHEN) → erro
  `conditional`, código `PROTHEUS_SUPPLIER_FIELD_CONDITIONAL` preservado.

### 2.3 Pendentes do owner TOTVS

- Obrigatoriedades adicionais por perfil de fornecedor continuam
  `TO_INVENTORY` (handoff Gabriel) — nenhuma regra inventada.

## 3. Contrato de erro (api-delpi)

Validação agregada em `normalize_supplier_fields` — executada **antes** de
gate CREATE, resolução de `codusr` no Core, token OAuth, tracking e POST
upstream. Nenhuma chamada de integração ocorre em payload inválido.

Envelope 422 (`error_response`):

```json
{
  "success": false,
  "message": "Preencha os campos obrigatórios do fornecedor para continuar.",
  "error": {
    "code": "SUPPLIER_REQUIRED_FIELDS_MISSING",
    "recoverable": false,
    "fields": [
      {"field": "rohs_indicator", "code": "missing_required",
       "message": "Campo obrigatório ausente: Indicador ROHS."}
    ]
  }
}
```

Códigos de topo:

| Código | Quando |
|---|---|
| `SUPPLIER_REQUIRED_FIELDS_MISSING` | somente campos obrigatórios ausentes |
| `PROTHEUS_SUPPLIER_FIELD_CONDITIONAL` | somente violação condicional |
| `PROTHEUS_SUPPLIER_PAYLOAD_INVALID` | valores inválidos / mixto |

Códigos por campo: `missing_required`, `invalid_value`, `conditional`.
`ProtheusRestError.fields` transporta a lista; `error_response` serializa em
`error.fields` — aditivo, sem breaking change.

## 4. Projeção segura no BFF (supplies-api)

`DelpiApiGatewayError` agora carrega `upstream_message` e `fields` extraídos
do envelope `{success, message, error:{code, fields}}`. A rota republica
`detail`/`fields` **somente** para códigos allowlisted
(`PROTHEUS_SUPPLIER_*`, `PROTHEUS_IDENTITY_*`, `SUPPLIER_REQUIRED_FIELDS_*`,
`PROVENANCE_*`) — mensagens já sanitizadas pelo produtor.

- `fields` projetado com chave `^[a-z][a-z0-9_]{0,39}$`, mensagem ≤200 chars,
  ≤25 entradas; entradas malformadas descartadas.
- Código desconhecido → `detail` genérico preservado (nenhum texto bruto do
  ERP alcança o navegador).
- `outcome: "rejected"` mantido em writes; `indeterminate` preservado para
  timeouts/resultado desconhecido — nunca convertido em rejeição.
- 4xx de validação continua 4xx; 5xx não vira validação.

## 5. MFE (plugins/supplies)

- `SUPPLIER_FIELD_REGISTRY`: 7 specs `post+required` com `requiredMessage`
  PT-BR por campo; marca `*` já renderizada por `showRequiredMark` + legenda
  «* Campos obrigatórios».
- `validateCreateDraft` (query.ts): agrega todos os erros na ordem canônica
  do registry antes de abrir a revisão — **zero chamada HTTP** em rascunho
  incompleto.
- `SupplierCreatePage`: resumo `role="alert"` com foco, lista completa de
  campos pendentes, `sp-supplier-field__error` por campo, limpeza do erro ao
  editar o campo, rascunho preservado em qualquer falha.
- `ApiRequestError`: carrega `detail`/`fields`/`code`/`outcome` do envelope;
  banner distingue validação local, rejeição determinística (detail
  sanitizado), auth de integração (`validationAuthMessage`) e indeterminado
  (sem sugestão de reenvio).
- Catálogos canônicos reutilizados — nenhuma lista fixa inventada.

## 6. PUT parcial — compatibilidade

`protheus_supplier_update_payload.py` usa specs por campo e permanece
parcial: campos omitidos não são enviados, nenhuma obrigatoriedade de POST
foi imposta, semântica de clear inalterada. `flag required` atua só na
normalização de criação.

## 7. Segurança

- AuthZ/S2S/`codusr` Core-resolved/guards de destino/gates CREATE+UPDATE:
  **inalterados** (`PROTHEUS_SUPPLIER_CREATE_ENABLED=false`,
  `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` em `infra/docker-compose.yml`).
- Sem nova permission; tracking/outcomes preservados; zero retry automático.
- Superfície de erro sanitizada em duas camadas (allowlist api-delpi →
  allowlist BFF); sem host interno, SQL, stack trace, secret ou payload bruto.

## 8. Testes

| Suíte | Resultado |
|---|---|
| api-delpi payload+use case+extended (foco) | 80 pass |
| api-delpi suíte completa | 6190 pass / 21 fail pré-existentes* |
| supplies-api | 627 pass / 21 skip |
| plugins/supplies vitest | 517 pass (51 arquivos) |
| tsc --noEmit / vite build / eslint | limpo / ok / 0 erros |

\* `tests/unit/planejamento_orcamentario/*` falha por `mkdir /app` negado —
problema de ambiente local, fora do escopo, sem relação com o diff.

Cobertura adicionada: agregação dos 7 ausentes, ausência de cada obrigatório,
valor inválido com preservação de zeros à esquerda, condicional `person_type=F`,
validação antes de gate/token/tracking, PUT parcial intacto, projeção 422 com
fields, 400 business reject sanitizado, código desconhecido sem vazamento,
sanitização de entries malformadas, `TOKEN_INVALID` → indeterminate, resumo
MFE + erro por campo + zero POST local.

## 9. Help e documentação

- `helpTooltips.suppliersCreate`: obrigatórios `*`, validação pré-envio,
  resumo de pendências, preservação de dados, rejeição sanitizada e
  indeterminado sem reenvio automático.
- `userManualContent` («Como cadastro um novo fornecedor?»): mesma narrativa.
- RCA R5: solução registrada sem apagar histórico.

## 10. Residuais / TO_INVENTORY

- Lista oficial completa de obrigatórios TOTVS por perfil: pendente Gabriel —
  a validação local cobre os 7 comprovados; novos campos exigem só spec.
- Reteste controlado em homologação (`DELPI_TST01`) permanece dependente de
  autorização de escrita separada — **nenhum cadastro real executado**.
