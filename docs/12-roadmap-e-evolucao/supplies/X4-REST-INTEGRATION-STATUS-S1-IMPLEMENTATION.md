# X4.REST-STATUS.S1 — Implementação do diagnóstico REST de fornecedores

**Data:** 2026-10-26 · **Task:** `X4.REST-STATUS.S1` · **Tipo:** full-stack
bounded implementation + runtime verification · **Base histórica:**
X4.PROD-C1.R4 (`cd50b85610` código / `3792969b3d` docs).

**Requisito central respeitado:** nenhuma verificação cadastra, altera ou
exclui fornecedores no ERP. O diagnóstico executa apenas: leitura de
parâmetros → resolução de configuração → solicitação de token técnico
(autenticação, não escrita) → GET único no fornecedor sentinela `00000000`
apenas após token válido → leitura de flags/guard. Zero POST/PUT/DELETE de
fornecedor.

## 1. Owners e fluxo

```text
Portal → MFE supplies (plugins/supplies) — card, interação, composição
  → supplies-api — endpoint BFF, AuthZ efetiva, sanitização
    → api-delpi — diagnóstico técnico: params, resolver, token, GET probe
      → REST Protheus — disponibilidade e autenticação upstream
```

Nenhuma lógica de resolução Protheus foi copiada para o BFF; nenhuma
permission nova foi criada; nenhuma API paralela de integração existe.

## 2. Contratos

### api-delpi — `GET /integrations/protheus/status` (estendido, aditivo)

Autorização: `require_s2s_or_any_permission` com
`PROTHEUS_INTEGRATION_READ_PERMISSIONS`, scope `suppliers.read`, client
`supplies-api` — mesmo padrão do `GET /suppliers/{id}` (E14). Campos
anteriores (`integration`, `configuration`, `authentication`,
`connection`, `config_path_label_mismatch`, `transport`) preservados;
novos campos aditivos:

| Campo | Valores | Fonte |
|---|---|---|
| `checked_at` | ISO-8601 UTC | gerado por execução |
| `environment` | `production`/`homologation`/`unknown` | `AMBIENTE` (label, nunca host) |
| `connectivity` | `not_checked`/`ok`/`failed` | resposta HTTP upstream existiu ou não |
| `authentication` | `ok`/`failed`/`not_checked`/`unavailable` | token técnico |
| `authentication_http_status` | int ou `null` | status HTTP sanitizado (ex.: 401) |
| `suppliers_read` | `not_checked`/`ok`/`failed` | probe GET sentinela pós-auth |
| `create_gate`/`update_gate` | `enabled`/`disabled` | flags efetivas |
| `write_target_guard` | `ok`/`mismatch`/`unverified` | `assert_protheus_write_target` |
| `write_validation` | `not_tested` (sempre) | nunca há prova de escrita |
| `overall` | `unavailable`/`upstream_pending`/`ready_for_attempt` | classificação composta |

Semântica: 401/404 de autenticação ⇒ `upstream_pending`; falha de
transporte/config/segurança ⇒ `unavailable`; auth + GET + guard íntegros ⇒
`ready_for_attempt` (pronto para tentativa, **não** prova de escrita);
`PROTHEUS_SUPPLIER_NOT_FOUND` no probe prova canal (`suppliers_read=ok`)
sem confundir ausência de cadastro com indisponibilidade.

### supplies-api — `GET /suppliers/integration-status` (novo, read-only)

`require_policy(can_administer)` → capability `supplies.manage` existente.
Encaminha via `DelpiApiGateway.get` (token do usuário + headers S2S) e
republica somente a allowlist `project_integration_status`: nunca URLs,
hosts, tokens, credenciais, headers ou internals. Erros upstream seguem a
convenção `_gateway_error_response`; a falha do próprio diagnóstico é
erro do endpoint, não PASS fabricado.

### MFE — `SupplierIntegrationStatusCard` (compartilhado)

`getSuppliersIntegrationStatus()` via `httpGet` + `suppliesApiUrl`
(`/suppliers/integration-status`) — `api.ts`, tipado em `types.ts`.
Montado em `SuppliersPage` e `SupplierDetailPage` sob
`capabilities.manage` (visibilidade apenas; autoridade é server-side).
Verificação manual, abort de resposta obsoleta, bloqueio de cliques
concorrentes, sem polling. Lista SQL e retry da ficha permanecem
independentes do diagnóstico.

## 3. Estados e apresentação

- Desktop: card discreto recolhível na área de conteúdo; mobile: painel
  inline recolhível após o cabeçalho — sem overlay de controles.
- `aria-live` nas regiões de status, botões acessíveis, foco visível,
  tema claro/escuro via variáveis `--sp-*`, CSS isolado em
  `.dashboard-supplies-portal`.
- "Inclusão habilitada"/"Alteração habilitada" nunca é apresentado como
  gravação comprovada; `write_validation` exibe "Não testada".

## 4. Testes

- **api-delpi:** 615/615 (suíte protheus/supplier/integration) — novos
  casos em `test_protheus_rest_routes.py`: config ok, auth failed com
  `upstream_status`, GET ok/failed, guard ok/mismatch/unverified,
  `checked_at`, gates, `overall`.
- **supplies-api:** 60/60 — novos casos em `test_suppliers_routes.py`:
  autorizado com projeção allowlist, sem bearer 401, sem capability 403,
  erro de gateway propagado, nenhum campo sensível repassado.
- **MFE:** 471/471 (49 arquivos) — suíte estrutural nova
  `SupplierIntegrationStatusCard.structural.test.ts` (8 testes): fala só
  com supplies-api via `httpClient`, read-only, montagem nas duas páginas
  sob `capabilities.manage`, refresh manual sem polling, nunca
  "gravação comprovada", diferenciação upstream × indisponibilidade,
  nota de independência SQL.
- TypeScript `tsc -b` limpo; `npm run build` ok; eslint 0 erros
  (2 warnings `set-state-in-effect` pré-existentes); `git diff --check`
  limpo; busca residual sem hosts/segredos/`fetch`/`api-delpi` no MFE.

## 5. Segurança

- Nenhum token, senha, URL interna, header `Authorization` ou dado fiscal
  sai do api-delpi para o browser; `environment` expõe apenas label.
- Token técnico nunca entra na resposta nem no estado do frontend.
- Probe é um único GET no sentinela `00000000`, somente após auth válida;
  não enumera fornecedores.
- Falha de autorização no BFF não consulta a REST (fail-closed).

## 6. Deploy e runtime

_Preenchido após deploy canônico (ver Execution Report no chat)._
Serviços materialmente afetados: `api-delpi` (contrato aditivo),
`supplies-api` (rota nova), MFE `supplies` (bundle federado).

## 7. Rollback

- Código: `git revert` do commit S1 + rebuild dos três serviços.
- BFF: remover rota/projeção (git revert) — sem estado persistido.
- MFE: bundle anterior pelo deploy sequencial; card é additive-only.
- Nenhuma migration, parâmetro ou flag foi alterada nesta task
  (configuração R4 intocada); rollback não exige desfazer dados.

## 8. Residuais conhecidos

- Credencial upstream produtiva: `authentication=failed` (HTTP 401) —
  dependência Gabriel/janela Michael; classificada `upstream_pending`,
  nunca PASS.
- Rota suppliers produtiva pendente de publicação → `suppliers_read`
  permanece `not_checked` enquanto auth falhar.
- `WRITE_VALIDATION=not_tested` por design — primeira escrita real exige
  autorização operacional distinta e reconciliação.
- Smoke visual autenticado: `INCONCLUSIVE` sem sessão autenticada.
