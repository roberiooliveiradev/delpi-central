# 121 — EVA MCP: execução E2E autenticada (runbook operacional)

**RUNBOOK_VERSION:** `2.0` — 2026-11-13 (revisão de segurança IAM)
**OWNER:** Engenharia / EVA (docs canônicos `119`/`120`; Issue #131)
**CAPABILITY:** `product.drawing_understanding` (tool MCP `analyze`)
**RUNBOOK_STATUS:** `PENDING_IAM_SECURITY_APPROVAL`
**APPROVED_OPERATIONAL_FLOW:** `NOT_YET_ESTABLISHED`

> **Aviso de governança:** a execução de 13/11/2026 comprovou a
> capacidade técnica dos dois E2Es reais (§2). O mecanismo de
> autenticação utilizado — impersonation administrativa — **não está
> aprovado como procedimento permanente**. A aprovação formal dos
> owners (IAM + Segurança) é pré-condição para uso recorrente.
> Enquanto isso, o fluxo aprovado é `NOT_YET_ESTABLISHED`.

## 1. Contrato MCP (verificado)

| Camada | Contrato real |
|---|---|
| Endpoint MCP | `https://minhadelpi.com.br/apps/engineering-api/mcp` (PROD) · gateway DEV `:80` |
| Audience exigida | URL exata do recurso (`MCP_RESOURCE_URL`) |
| Scope exigido | `mcp:tools` (+ `openid`) |
| Client OAuth oficial | `mcp-engineering` — confidencial, PKCE obrigatório, redirect `chatgpt.com/connector_platform_oauth_redirect`, `directAccessGrants=false`, implicit off |
| Permissão | `engineering.access` **ou** `is_superadmin` via Core `/me` RBAC |
| Principal | humano — `principal_type=="user"` obrigatório (`_require_engineering_human`) |
| Token exchange | `delia-api→mcp-engineering`: permitido em DEV, **negado por política deliberada em PROD** |

## 2. HISTORICAL_EXECUTION — E2Es de 13/11/2026 (evidência)

Jobs reais concluídos e validados — evidência **preservada**:

- PROD `aj-fc70e1324afd47b6` (imagem `e3fc852e…`): COMPLETED, 13/13,
  `AE|1|10010028→50225702` IDENTIFIED, negativos UNKNOWN.
- DEV `aj-1f2297e1a74d42d5`: COMPLETED, 13/13, resultado idêntico.

**Fluxo executado (registro histórico, não recomendação):**

- **PROD:** impersonation admin (`rober`/`inovacao@delpi.com.br`,
  `is_superadmin` legítimo) → authorization-code + PKCE em
  `mcp-engineering` → MCP.
- **DEV:** impersonation → implicit `delpi-central` →
  token-exchange `delia-api` → `mcp-engineering` → MCP.

## 3. SECURITY_REVIEW_PENDING — avaliação de risco

| Mecanismo | Risco | Evidência |
|---|---|---|
| **Impersonation admin** | ALTO como rotina: exige credencial **master realm admin** → quem executa o runbook detém controle total do IAM (viola least-privilege); exige assumir identidade humana (`rober` = superadmin — superfície de teste super-privilegiada); precedente documental (§77/§78/Doc 56) **nunca recebeu aprovação formal como procedimento permanente**. Auditoria KC registra o evento admin, mas ações downstream logam como o usuário impersonado — accountability difusa para uso automatizado. | §6.1 task IAM-01 |
| **Credenciais admin** | ALTO: lidas do env do container KC; qualquer `docker exec` no host as expõe; passagem via env a `docker exec` deixa traço em process args; sem rotação observada. | §6.2 |
| **Client secret `mcp-engineering`** | MÉDIO: recuperável via kcadm (admin) — legítimo para owner; inadequado como insumo rotineiro de agentes. | §6.2 |
| **Authorization-code + PKCE** | O fluxo **em si** é o contrato oficial (ChatGPT connector). O problema é a origem da sessão (impersonation), não o fluxo. | §6.3 |
| **Implicit flow `delpi-central` (DEV)** | `implicitFlowEnabled=true` vigente em DEV (consumidores existentes dependem). Implicit é prática depreciada; **não alterar** sem inventário de consumidores — classificado `TO_INVENTORY`, não como ação. | §6.4 |
| **Token exchange prod** | Denied by policy — limitação **deliberada** de delegação cross-client. Não habilitar para smoke. | §6.5 |

## 4. Matriz de alternativas (Fase B/C)

| Critério | A — usuário eval dedicado | B — service account | C — delegação oficial | D — impersonation c/ aprovação |
|---|---|---|---|---|
| Contrato atual suporta | **SIM** (`principal_type=user`) | NÃO — contrato exige humano → ARCHITECTURE_DECISION | Não existe mecanismo de delegação/actor-claim na plataforma | SIM tecnicamente |
| Alteração Keycloak | user eval (criar/restaurar) + grant ROPC em client dedicado ou `mcp-engineering` | novo client + contrato | novo mecanismo de delegação | nenhuma |
| Alteração Core | grant `engineering.access` mínimo | nova policy | nova policy | nenhuma |
| Least privilege | **ALTO** — usuário só tem `engineering.access` | alto | médio | **BAIXO** — exige master admin |
| Auditoria | identidade própria nos logs | identidade técnica | cadeia delegada | difusa (ações como o impersonado) |
| Revogação | desabilitar user | revogar secret | revogar grant | — |
| Repetibilidade | **SIM** sem mutações | sim | sim | sim mas privilegiada |
| Aprovação owner | necessária (IAM+Core) | necessária | necessária | necessária (IAM+Segurança) |

**Recomendação: Alternativa A** — identidade humana de avaliação
dedicada, com `engineering.access` como única permissão relevante.

## 5. Plano mínimo de operacionalização (Fase G)

Decisão única necessária dos owners (menor bloco possível):

1. **IAM owner:** provisionar/restaurar o usuário Keycloak
   `deploy01.smoke@delpi.local` — identidade técnica de avaliação
   já governada: linha Core `b069ead1` com `engineering.access`
   via role **já existe** (criada na DEPLOY-01 autorizada).
   Alternativa equivalente: conceder `engineering.access` a um dos
   usuários eval existentes (`devin-smoke-g16`).
2. **IAM owner:** habilitar `directAccessGrants` (ROPC) **em um
   client dedicado** `eva-eval-mcp` (recomendado — não toca o client
   oficial ChatGPT) ou em `mcp-engineering`, com os client-scopes
   `mcp:tools` + audience do recurso MCP. Alternativa sem nova flag:
   login interativo assistido + code+PKCE (não repetível por agente).
3. **Core owner:** confirmar que a role `engineering.access` de
   `deploy01.smoke` segue aprovada (zero grants novos se restaurado).
4. **Segurança:** registrar o principal como identidade de
   avaliação aprovada, com senha em cofre/mecanismo seguro (não em
   `/tmp` nem `.env` de repositório), política de rotação/revogação.
5. Resultado: `password grant` (ou fluxo aprovado) do usuário eval
   → token `aud=MCP URL, scope=mcp:tools` → MCP — **sem
   impersonation, sem admin, sem mutações por execução**.

`REPEATABLE_E2E_PATH` pós-aprovação:

```text
eval user (engineering.access, senha em cofre)
  → token endpoint (grant aprovado, client dedicado)
  → aud=…/engineering-api/mcp, scope=mcp:tools
  → POST /mcp initialize → tools/call analyze
  → poll parameters.job_id → occurrences
```

## 6. Execução e diagnóstico (válidos para qualquer fluxo aprovado)

- MCP streamable-HTTP: `initialize` → `notifications/initialized` →
  `tools/call analyze` `{analysis_type, parameters:{product_code}}`
  → `job_id`; poll com `parameters.job_id` (store processo-local —
  restart descarta jobs → `job_not_found`).
- Erros comuns: `401` = aud/iss incorretos; `403` no tools/call =
  sem `engineering.access`/superadmin (**não conceder grant ad
  hoc**); `Missing code_challenge` = PKCE; `source_unavailable` =
  fonte PDF.

## 7. Proibições permanentes do runbook

- Não registrar tokens, secrets, cookies ou senhas.
- Não criar/alterar usuários, roles, permissions ou clients para
  executar um E2E — exceções exigem aprovação do owner.
- Não usar impersonation administrativa como rotina sem aprovação
  documentada IAM+Segurança.
- Não usar contas de terceiros ou superadmin para teste quando uma
  identidade de avaliação mínima bastar.
