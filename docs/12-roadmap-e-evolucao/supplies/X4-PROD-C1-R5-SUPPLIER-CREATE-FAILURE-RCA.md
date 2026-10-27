# X4.PROD-C1.R5 — RCA: falha no cadastro produtivo de fornecedores

**Data:** 2026-10-27 · **Tipo:** investigação read-only · **Status:** CONCLUÍDO
**BASE HEAD:** `5fa85fd6bb` → rebase `d0f124c96b` · **Owner da correção proposta:** `api-delpi` (contrato) + `plugins/supplies` (UX)

## 1. Sintoma observado

Em `/apps/supplies/suppliers/new`, após consulta pública de CNPJ e revisão
cadastral, o submit retornou:

```
Operação rejeitada [PROTHEUS_SUPPLIER_WRITE_REJECTED] api-delpi client error
```

O navegador também apresentou respostas HTTP 400, 422 e 404 (sem HAR —
associação individual verificada nos logs do gateway).

## 2. Linha do tempo comprovada (2026-10-27, BRT = UTC-3)

| Horário | Evidência | Fonte |
|---|---|---|
| 15:10:39–15:10:44 | `GET /apps/supplies-api/suppliers?query=w` e `?query=t` → **422** (busca da lista, `min_length=2` do api-delpi) | gateway `delpi-gateway` |
| 15:13:11.20 | `integration_operation_created` `02ba4718-c6f1-4be1-a47e-e1b724ea932b` (integration=protheus, resource=supplier, action=create, caller_app=supplies-api) | `integration_tracking.integration_operation_events` |
| 15:13:11.66 | transição `CREATED→SENDING` — token já obtido, POST partindo | evento `send_started` |
| 15:13:18.79 | transição `SENDING→REJECTED` (`upstream_response`) | evento `upstream_response` |
| 15:13:19.13 | api-delpi responde **400** `create_protheus_rest_supplier` (369 ms); gateway registra `POST /apps/supplies-api/suppliers → 400` | logs `delpi-api-delpi` + `delpi-gateway` |

Somente **um** POST de criação existe em toda a retenção de logs
(`--since 2026-10-20`) — não houve reenvio.

## 3. Fluxo e evidência por camada

### Frontend (`plugins/supplies`) — PROVEN

- `buildCreateFornecedor` (`query.ts:118`) envia **somente campos
  preenchidos** — strings vazias são omitidas do body.
- `POST /suppliers` (`api.ts:50`) → `classifyWriteOutcome(response, 200)`;
  no `catch`, `err.outcome`/`code`/`status` do `ApiRequestError` decidem o
  banner. O texto exibido é `detail` + `code` devolvidos pelo BFF —
  `api-delpi client error` é a mensagem genérica do gateway, não a causa
  técnica real (ver §5).

### BFF (`supplies-api`) — PROVEN

- `POST /suppliers` (`suppliers_routes.py:316`) → `can_use_operations` →
  `sanitize_post_body` (allowlist `POST_SUPPLIER_FIELDS`, identidade
  proibida) → `POST /integrations/protheus/suppliers`.
- `DelpiApiGatewayError` (status 400, code `PROTHEUS_SUPPLIER_WRITE_REJECTED`)
  → `_gateway_error_response(write=True)` →
  `{"detail": "api-delpi client error", "code": "PROTHEUS_SUPPLIER_WRITE_REJECTED", "outcome": "rejected"}` → HTTP 400.
- **Gap de observabilidade:** `_error_code` preserva apenas `code`; o
  `detail` sanitizado do api-delpi ("…Detalhe: Campos Obrigatorios Não
  Preenchidos") é descartado na borda.

### api-delpi — PROVEN

- `create_protheus_rest_supplier_route` → normalizer (apenas
  `supplier_store` é `required` em `SUPPLIER_FIELD_SPECS`) → gate
  `PROTHEUS_SUPPLIER_CREATE_ENABLED` → `resolve_actor_codusr` →
  `assert_protheus_write_target` → `get_valid_token` →
  `write_tracker.begin` → `gateway.create_supplier`.
- `_map_supplier_write_response` (`protheus_rest_gateway.py:379–439`):
  4xx ≠ 401/403/5xx com `code_error` ou texto de erro extraível →
  `PROTHEUS_SUPPLIER_WRITE_REJECTED` (status 400, `recoverable=False`).
- `record_send_failure` → `record_rejected` (4xx determinístico, não
  `outcome_unknown`).

### Protheus REST — PROVEN

Registro `error_details` da operação (sanitizado, `raw_error_stored=false`):

```json
{
  "code": "PROTHEUS_SUPPLIER_WRITE_REJECTED",
  "message": "Escrita rejeitada pelo Protheus. Detalhe: Campos Obrigatorios Não Preenchidos",
  "category": "UPSTREAM_REJECTION",
  "http_status": 400
}
```

O `outbound_payload` comprova o envio de apenas **10 campos**:
`supplier_name, tax_id, person_type, supplier_store, address, district,
city, city_code, state, postal_code` (+ `codusr` resolvido server-side).

## 4. Causa raiz — PROVEN

O endpoint upstream exige como obrigatórios **6 campos** já documentados
na homologação E2 (`X4-FIELDS-E2-...`, linha 32 — mesma mensagem, mesma
descoberta na 1ª tentativa do Lote 0):

| Campo REST | SX3 | Presente no envio? |
|---|---|---|
| `rohs_indicator` | A2_YROHS | não |
| `accounting_account` | A2_CONTA | não |
| `bacen_country_code` | A2_CODPAIS | não |
| `payment_method_code` | A2_FORMPAG | não |
| `financial_nature_code` | A2_NATUREZ | não |
| `payment_condition_code` | A2_COND | não |

O contrato Minha DELPI publica esses 6 campos e oferece
catálogos/opções no formulário, mas **nenhum é `required`** em
`SUPPLIER_FIELD_SPECS` nem marcado como obrigatório no MFE — o usuário
submeteu sem eles e a rotina TOTVS recusou na pré-validação.
O E2 já recomendava "documentar como required no OpenAPI/playbook em
iteração de contrato" — essa evolução ficou pendente.

## 5. Fatores contribuintes

1. **Contrato assimétrico:** upstream exige 6 campos que nossa
   fronteira trata como opcionais — validação local inexistente.
2. **Mensagem degradada:** BFF repõe o detalhe upstream por
   `api-delpi client error`; o usuário não vê o motivo real.
3. **Form sem obrigatórios visuais:** os 6 campos têm catálogo
   (`payment-conditions`, `payment-methods`, `accounting-accounts`,
   `financial-natures`, `bacen-countries`) ou opções (`rohs`), mas sem
   marca de obrigatoriedade.

## 6. Estado do tracking e persistência

- `operation_id` = `02ba4718-c6f1-4be1-a47e-e1b724ea932b`
- `status` = **REJECTED** · `http_status` = 400 ·
  `upstream_error_code` = `PROTHEUS_SUPPLIER_WRITE_REJECTED` ·
  `retry_safe` = false
- **POST_SENT_TO_ERP:** SIM — recusa veio do upstream com mensagem de
  negócio.
- **OAuth:** FUNCIONOU — `get_valid_token` precede `begin()`; a existência
  do registro prova token válido. Resposta 400 (não 401/403) descarta
  `PROTHEUS_TOKEN_INVALID`. O 401 observado no diagnóstico S1 anterior
  não se reproduziu nesta tentativa.
- **PERSISTENCE_STATUS:** *nenhuma gravação provada* — a recusa é
  pré-validação de campos (a mesma recusa no E2 Lote 0 não persistiu
  linha, comprovado por SQL). Risco de duplicidade desta tentativa:
  **desprezível**. Reconciliação por leitura de SA2 via API exige
  token de usuário (não disponível na sessão de investigação) —
  `TO_INVENTORY` residual, sem indício de escrita.

## 7. Matriz 400/422/404

| Request | HTTP | Owner | Código | Relação com o cadastro |
|---|---|---|---|---|
| `POST /apps/supplies-api/suppliers` | 400 | api-delpi → BFF | `PROTHEUS_SUPPLIER_WRITE_REJECTED` | **O erro exibido** — campos obrigatórios upstream ausentes |
| `GET /suppliers?query=w` e `?query=t` (×3) | 422 | api-delpi (FastAPI `min_length=2`) | validação de query | **Sem relação** — digitação na busca da lista antes de abrir `/new` |
| 404 reportado | — | — | — | **Não comprovada** — nenhum 404 em `/apps/supplies*` do IP da sessão na janela; 404s do período são scanners de `.env`, assets antigos e avatares de outro usuário. `TO_INVENTORY` sem HAR |

## 8. Verificação de segurança — PROVEN

- AuthZ BFF `can_use_operations` (supplies.access) + S2S
  `supplies-api`/`suppliers.create` no api-delpi — OK.
- Guard de destino (`assert_protheus_write_target`) executado antes do
  envio — `AMBIENTE=1`, alvo produtivo pin.
- Flags CREATE/UPDATE efetivas (gate não bloqueou).
- Identidade `codusr` resolvida no Core — nenhuma identidade do cliente.
- Zero escrita ERP executada nesta investigação; zero alteração de
  config/flags.

## 9. Correção mínima recomendada (plano — não implementada nesta task)

| # | Owner | Diff | Efeito |
|---|---|---|---|
| 1 | `api-delpi` | `SUPPLIER_FIELD_SPECS`: `required: True` nos 6 campos (só `normalize_supplier_fields`/POST aplica `required`; PUT per-field não é afetado) | Rejeição local 422 com campo nomeado, antes de qualquer round-trip |
| 2 | `plugins/supplies` | Marcar os 6 campos como obrigatórios no formulário de criação + validação de submit (catálogos já existem) | Usuário nunca submete payload incompleto |
| 3 | `supplies-api` | `_error_code` → extrair também `detail`/`message` sanitizado do erro upstream em `_gateway_error_response` | Banner exibe "Campos Obrigatorios Não Preenchidos" em vez de mensagem genérica |
| 4 | `api-delpi` docs/OpenAPI | Registrar os 6 como `required` no contrato publicado (pendência já anotada no E2) | Contrato reflete o upstream |

## 10. Procedimento seguro de reteste

1. Aplicar a correção 1+2 (mesmo deploy MFE + api-delpi).
2. Refazer o cadastro **com os 6 campos preenchidos** via catálogo —
   uma única tentativa.
3. Verificar `integration_operation_events`: esperado
   `CREATED→SENDING→ACKNOWLEDGED` (+ `CONFIRMED` se upstream devolver
   `A2_COD`/`A2_LOJA`).
4. Se nova recusa: `error_details.message` conterá o motivo
   determinístico seguinte (ex.: regra MATA020) — não reenviar antes de
   classificar.
5. Confirmação via `GET /suppliers/operations/<operation_id>` e GET da
   ficha quando `resource_key` existir.

## 11. Pendências externas

- Confirmar com Gabriel/TOTVS a lista oficial de obrigatórios upstream
  (E2 handoff item (c)) — 6 comprovados por evidência, pode haver
  obrigatoriedades condicionais.
- `address` enviado truncado em 40 chars (spec SX3) — revisar origem da
  sugestão de endereço (valor chegou cortado no "KM:").

## 12. Classificação final

| Item | Estado |
|---|---|
| Camada do erro | PROVEN — upstream Protheus (400 business) |
| Endpoint | PROVEN — `POST /integrations/protheus/suppliers` |
| HTTP original | PROVEN — 400 TOTVS |
| Código upstream | PROVEN — mensagem "Campos Obrigatorios Não Preenchidos" |
| Autenticação | PROVEN — token válido na tentativa |
| Envio ao ERP | PROVEN — SENDING→REJECTED com resposta upstream |
| Rastreamento | PROVEN — `02ba4718-…-e1b724ea932b` REJECTED |
| Persistência | PROVEN-sem-escrita (recusa pré-validação); read-back `TO_INVENTORY` |
| 400/422 | PROVEN (write / busca lista) |
| 404 | TO_INVENTORY — sem associação comprovada |
| Escritas na investigação | ZERO |
| Mudanças produtivas | ZERO |


## 13. Revisão GPT / decisão de execução (2026-10-27)

**Veredito: `ACCEPT_WITH_RESIDUAL` para o RCA read-only.** A origem do HTTP 400 e o evento `SENDING→REJECTED` estão fundamentados pelo tracking relatado e pela resposta sanitizada do Protheus. A identidade individual dos seis campos requeridos é sustentada também pelo ensaio E2, não pela mensagem genérica da tentativa produtiva isoladamente; validar o contrato exato no HEAD antes do diff. A autenticação funcionou **nessa tentativa**, não implicando que todos os cenários de GET/status estejam saudáveis.

**Ressalva de persistência:** a recusa anterior ao insert é forte indicativo de não gravação, mas **não declarar `PROVEN` para ausência de linha SA2 na operação produtiva sem read-back independente**. Manter `TO_INVENTORY` quanto à reconciliação deste operation ID; nenhum retry automático nem nova tentativa antes de conferir eventual existência pela chave/documento autorizado.

**Diretriz para correção bounded:** (1) validar os seis campos no backend **antes de obter token ou iniciar tracking de envio**, respeitando semântica de POST versus PUT e sem ativar required indevidamente em atualização parcial; (2) alinhar obrigatoriedade visual e validação de submit no MFE, com catálogos e mensagens PT-BR; (3) revisar propagação de erro sanitizado por allowlist no BFF, sem expor detalhes brutos do upstream, stack traces, CPF/CNPJ, SQL ou secrets; (4) sincronizar schema/OpenAPI e Help no owner devido; (5) testes positive/sibling/negative, sem escrita ERP na verificação automatizada; deploy dos serviços realmente afetados.

**Execução da correção:** ainda requer autorização específica do PO. O registro deste parecer não autoriza novo POST produtivo. Próximo gate: implementação e teste da validação, seguida de uma tentativa real controlada com autorização operacional, tracking e leitura de confirmação.

## 14. Resolução (R6)

Correção implementada em `X4-PROD-C1-R6-SUPPLIER-VALIDATION-FIX.md` (mesma pasta): os seis campos upstream + `supplier_store` viraram `required` no normalizador canônico com validação agregada 422 estruturada antes de token/tracking; o BFF republica `detail`/`fields` sanitizados por allowlist; o MFE ganha obrigatórios visuais, validação agregada pré-submit, resumo e erros por campo com rascunho preservado. PUT parcial inalterado. Nenhum cadastro real executado na correção — reteste controlado segue pendente de autorização operacional.
