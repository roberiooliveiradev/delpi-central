# EVA — Full CRUD Production Activation & User-Delegated Authentication Evidence

> **Missão:** `EVA.MCP.FULL.CRUD.PROD.FINAL`
> **Decisão funcional:** APPROVED — EVA suporta CRUD completo (Coordenação EVA)
> **Status final:** `PRODUCTION_CRUD_OPERATIONAL` — create/update/delete
> governados provados ponta a ponta em produção com OAuth humano real;
> import destrutiva permanece fail-closed sob gate do owner.

---

## 1. Baseline e SHAs

| Item | Valor |
|---|---|
| BASE_HEAD | `4ede7ffa9b` |
| TARGET/DEPLOYED_SHA (código ACT tiers + elicitation) | `d709338dc8` (deploy anterior) → **`d63ef89e69`** (este deploy: transporte stateful+SSE) |
| FINAL_HEAD | `c6cd3a60d8` (inclui commit DÉLIA não relacionado) |
| NC baseline prod | **53** (antes e depois do smoke — verificado) |
| Procedimento | `operador@192.168.1.237` · `~/projetos/delpi-central` · `git pull --ff-only` + `up-prod-sequential.sh --build engineering-api` |

## 2. Causa raiz encontrada e corrigida nesta missão

A homologação DEV revelou o defeito real que bloqueava DELETE: o transporte
MCP era `json_response=True, stateless_http=True` (`asgi.py`). Nesse modo
**não existe back-channel** para requisições servidor→cliente, logo
`ctx.elicit()` falhava instantaneamente (`NoBackChannelError`) e todo commit
destrutivo devolvia `confirmation_unavailable` — mesmo com consumidor
compatível. Era defeito de transporte, não de contrato.

**Correção (`d63ef89e69`):**

- `engineering-api/engineering_app/interface/mcp/asgi.py` —
  `json_response=False, stateless_http=False` (sessão stateful + resposta
  SSE: o request-scoped channel carrega a elicitation dentro do POST da
  `tools/call`, exatamente como o protocolo Streamable HTTP prescreve).
- `semantic_bridge.py` — log do erro de elicitation inclui `repr(exc)`.
- `test_eva_mcp_semantic.py` — helpers de tier determinísticos
  (delenv das flags irmãs), independente do env ambiente.
- `infra/docker-compose.yml` — mapeia `ENG_EVA_ACT_DELETE_ENABLED` e
  `ENG_EVA_ACT_IMPORT_ENABLED` (antes só o master era repassado).

## 3. Flags ACT por classe de risco (estado final em prod)

| Flag | Valor prod | Classe |
|---|---|---|
| `ENG_EVA_ACT_ENABLED` | `true` | WRITE (create/update + prepare) |
| `ENG_EVA_ACT_DELETE_ENABLED` | `true` | DELETE (commit destrutivo) |
| `ENG_EVA_ACT_IMPORT_ENABLED` | *(ausente)* | IMPORT replace-all |
| `ENG_NC_IMPORT_REPLACE_ENABLED` | `false` | gate do owner (inalterada) |

Master flag **não** destrava delete nem import — tiers independentes,
verificado no container em execução. Backup do `.env`:
`infra/.env.bak-eva-crud-<timestamp>` no host de produção.

## 4. Autenticação delegada do usuário (fluxo provado)

```text
USER → Keycloak OAuth (auth-code + PKCE, client mcp-engineering confidencial)
     → EVA MCP (aud exata do resource + scope mcp:tools)
     → Engineering API (JWT validado: iss/aud/scope/azp)
     → Core live AuthZ (engineering.access via role)
     → use case NC → audit com ator humano
```

- Token de prova: `azp=mcp-engineering`,
  `aud=[https://minhadelpi.com.br/apps/engineering-api/mcp, …]`,
  `scope` inclui `mcp:tools`; sub = usuário humano temporário de smoke.
- Identidade técnica não substitui humano: service principal → 403
  (`engineering_human_required`), testado em DEV.
- Ator humano registrado no histórico da NC ("ACT Smoke" no smoke prod;
  "Rober Dev" em DEV) — campo `actor` real, não inferência.

## 5. Evidência de execução — DEV (sandbox `nc_sandbox`)

Client MCP real (`streamable_http_client` + `elicitation_callback`), token
OAuth humano de DEV, 20/20 checks:

- `tools/list` = 29 (6 semânticas + 23 legacy deprecated)
- `get_context.act_tiers = {write:true, delete:true, import:false}`
- `read nonconformity.search` = dados reais do sandbox
- `execute create` → id oficial + `postcondition read_back verified`
- create replay com mesmo `idempotency_key` → **mesmo id** (sem duplicar)
- `execute update` com `expected_version` → aplicado + read-back
- update com version stale → **`concurrency_conflict`** (409 semântico)
- `read history` → ator humano presente nos eventos
- `delete` commit sem proposta → `proposal_required`
- `delete` prepare → proposta selada com impacto do alvo
- commit com handle forjado → `proposal_not_found`
- commit com alvo divergente → `proposal_mismatch`
- commit com elicitation aceita (echo do alvo) → `deleted` +
  `postcondition read_back_gone`
- replay da proposta → `proposal_not_found` (single-use)
- read após delete → 404
- modo `ELICIT_MODE=decline` → **`confirmation_declined`**, registro
  preservado, proposta **não** consumida (retry possível)
- `execute import` prepare → proposta selada (dry-run sem mutação)
- import commit → `act_disabled` (tier import off)
- entidade inválida → `not_implemented`; filtro injeção → tratamento tipado
- cleanup: todas as NCs sintéticas removidas pelo fluxo governado
  (prepare→elicit→commit), sandbox retornou ao baseline (3 registros)

## 6. Evidência de execução — PROD (jornada completa)

Mesmo E2E contra `http://localhost:8000/mcp` (Host `minhadelpi.com.br`),
token auth-code+PKCE real mintado internamente (CF bloqueia cliente
não-browser no público — drift já conhecido, doc 56):

### Gate A — fail-closed (todas as flags vazias)

- tools/list 29 · `act_tiers={F,F,F}` · read=53 registros reais
- create/update/delete/import → `act_disabled` honesto · sem crash

### Gate B — WRITE (`ENG_EVA_ACT_ENABLED=true`)

- `act_tiers={write:true, delete:false, import:false}`
- `execute create` → NC `c2ae32ff-…` criada + read-back verificado
- replay idempotente → mesmo id · update ETag → aplicado
- stale → `concurrency_conflict` · histórico com ator humano
- delete prepare → `act_disabled` (tier delete ainda off) ✓

### Gate C — DELETE (`ENG_EVA_ACT_DELETE_ENABLED=true`)

- `act_tiers={write:true, delete:true, import:false}`
- `delete` prepare → proposta selada; forged → `proposal_not_found`;
  wrong-target → `proposal_mismatch`
- **commit com elicitation real aceita → `deleted` +
  `postcondition: read_back_gone`** (`elicits=1`; mensagem exibiu alvo +
  impacto e exigiu echo do identificador)
- replay → `proposal_not_found` · read pós-delete → 404
- `eva_mcp_destructive_confirmed` registrado no log (2×, dois ciclos E2E)

### Gate D — IMPORT (não ativado)

- prepare (dry-run) → proposta selada, **zero mutação**
- commit → `act_disabled` (tier ausente) + owner flag `false`
- Nenhuma substituição em massa executada — correto por design.

### Negativas e regressão

- MCP sem token → 401 · log pós-deploy: **0** tracebacks/5xx
- Portal `/apps/engineering` → 200 · REST sem auth → 401
- Baseline NC: 53 → 54 (create) → 53 (delete governado) ✓

## 7. Identidade de smoke (criada e removida)

- KC user `act57.smoke` (uid `93d185f7-…`) + Core `users`/`user_roles`
  (role "Analista de Engenharia - SC" → `engineering.access`).
- Cleanup verificado: 0 remanescentes em KC e Core. Nenhuma credencial
  ou secret registrada neste documento.

## 8. Operações compostas

A jornada E2E é ela mesma uma operação composta sequencial
(`read → execute → read → execute → read → delete → read`) executada numa
única sessão autenticada — dependentes resolvidos por dados reais, erros
parciais honestos (conflito 409 sem escrita, proposta rejeitada sem
mutação). Não há transação global alegada.

## 9. Residuais e decisões pendentes

1. **Consumidor real (ChatGPT):** o backend implementa elicitation
   MCP-spec e a prova com client compatível passa; o suporte à UI de
   confirmação no conector ChatGPT não foi testado (sem acesso ao
   consumidor). Fail-safe honesto: consumidor sem elicitation recebe
   `confirmation_unavailable` — nada é deletado. → `TEST_NOT_RUN` para
   `REAL_MCP_CONSUMER`.
2. **Sessões stateful:** o transporte agora mantém `mcp-session-id`
   (idle timeout 1800s, max 10000). Multi-réplica futura exigiria
   afinidade ou store compartilhado — irrelevante com 1 réplica atual.
3. **TÉO/VISTA:** o padrão de identidade delegada coincide (OAuth do
   consumidor → token humano → backend com AuthZ live); EVA já estava
   conforme — nenhum código foi copiado deles.
4. **`EVA-FINAL-15` composite:** coberto via orquestração de tools pelo
   consumidor (prova sequencial real), sem batch endpoint dedicado.

## 10. Rollback

| Camada | Ação |
|---|---|
| Flags (instantâneo) | remover `ENG_EVA_ACT_ENABLED`/`_DELETE_` do `infra/.env` + `up -d --no-deps engineering-api` → fail-closed total |
| Código | `git checkout 70e93be21f`/`d709338dc8` + `--build engineering-api` |
| Dados | nenhum dado oficial alterado pelo smoke; baseline 53 preservado |
| `.env` | backup `infra/.env.bak-eva-crud-<timestamp>` no host |

## 11. Testes

| Suíte | Resultado |
|---|---|
| `pytest tests/ -x -q` (container, SHA deployado) | **491 passed, 10 skipped** |
| E2E MCP real DEV (20 checks) | **20/20** |
| E2E MCP real PROD (20 checks) | **19/20** — único FAIL é grep por "rober"; ator humano real era "ACT Smoke" (correto) |
| Decline/cancel elicitation (DEV) | `confirmation_declined`, proposta preservada |

## 12. Capacidade final (ledger)

| Tool | Status |
|---|---|
| `get_context` | PROVEN_PROD (tiers/flags/confirmation_model reais) |
| `read` | PROVEN_PROD (53 NCs oficiais) |
| `analyze` | PROVEN_PROD (deploy anterior; inalterado) |
| `knowledge` | PROVEN_PROD (idem; `not_implemented` honesto p/ ausentes) |
| `execute` create | **PROVEN_PROD** |
| `execute` update | **PROVEN_PROD** (ETag + 409) |
| `execute` import prepare | PROVEN_PROD (dry-run, zero mutação) |
| `execute` import commit | BLOCKED by design (tier off + owner flag) |
| `delete` | **PROVEN_PROD** (proposal+elicitation+single-use+postcondition) |
| legacy 23 tools | compatíveis, deprecated, roteadas aos mesmos tiers |
| operações compostas | PROVEN_PROD (orquestração sequencial real) |
| consumidor ChatGPT UI de elicitation | PENDING (backend pronto) |
