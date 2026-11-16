# ADR — Consentimento humano para ACT do DAVI (W012)

> **Status:** `DECIDIDA` — ver §0 (decisão congelada pela Coordination em
> `DAVI-SI-W012-TEO-CONVERSATIONAL-CONFIRMATION-PRODUCTION-01`).
> **TASK_ID original:** `DAVI-SI-W012-TRUSTED-CONSENT-CONTRACT-01`
> **Base:** `main` @ `9e0f92c0de`.
> O corpo deste documento preserva a investigação VISTA/CLARA como histórico
> e evidência — a recomendação da §9 **não é mais a decisão vigente**.

## 0. Decisão congelada (supersede §9)

| Item | Status |
|---|---|
| Página externa Portal/MFE para consentimento (§9 original) | `SUPERSEDED` |
| Confirmação conversacional explícita — padrão TÉO `confirm_before_act` | `APPROVED` |
| Consent challenge externo VISTA como fluxo obrigatório para DAVI | `REJECTED_FOR_DAVI` |
| `confirm=true` mediado pelo modelo não é prova independente do ato humano | `ACCEPTED_RESIDUAL` — risco aceito e documentado para o fluxo conversacional, sem equivalência ao step-up VISTA |
| Confirmação explícita em turno **posterior** ao PREPARE (pedido inicial nunca confirma) | `REQUIRED` |
| JWT individual, AuthZ SI, OCC, auditoria persistente, HMAC dedicado, single-use, postcondition | `REQUIRED` |

Fluxo aprovado: usuário solicita → PREPARE apresenta diff completo (inclusive
efeitos indiretos) → DAVI pede confirmação explícita → usuário responde
afirmativamente em novo turno → ACT com handle selado → verificação no owner.
Sem página externa, sem segundo MCP, sem consent challenge.

A investigação abaixo permanece válida como referência de padrões; a opção
"canal externo" fica documentada como alternativa futura caso o residual
conversacional seja revisto.

## 1. Problema

O ACT do DAVI aceita `confirm=true` produzido pelo próprio modelo via MCP.
Esse booleano não é prova independente de consentimento humano: o mesmo canal
que poderia ser induzido a executar a escrita é o canal que a "confirma".

O padrão comprovado na plataforma (CLARA → VISTA) substitui o booleano por um
objeto de autorização de primeira classe:

```text
PREPARE → consent_challenge (backend-minted) → aprovação humana em canal
confiável (Portal + step-up token) → consent_artifact → COMMIT verificado
```

## 2. Matriz comparativa — TÉO × CLARA × VISTA × DAVI (evidência em código)

| Aspecto | TÉO | CLARA | VISTA | DAVI (atual) |
|---|---|---|---|---|
| Proposta selada | `tm_app/.../proposal.py` + store in-process | `clara_proposal_repository` (persistente) | `proposal_store` + `content_hash` | `proposal_store.py` in-process + HMAC dedicado |
| Confirmação | `confirmation_policy` (confirm/auto) | challenge Portal step-up (V014) | challenge Portal step-up (V019) | `confirm=true` (modelo) |
| Canal humano | — | `ClaraConsentPage` (plugin CF) → `/clara/*` BFF | rotas `/vista/consent/*` (BFF) | **inexistente** |
| Step-up | — | `iat >= challenge.created_at` via `keycloak.updateToken(-1)` | idem CLARA | — |
| Persistência consent | — | `controllership_finance.clara_consent_challenge` | `tv_dashboard.vista_consent_challenge` | — |
| Idempotência | `idempotency_store` | persistente | `tv_dashboard.gpt_actions_idempotency_keys` (V016/V017) | consume-before-write in-process |
| Auditoria | `transformometro.audit_logs` | owner-local | owner-local | `strategic_indicators.settings_audit` (736bf7cd18) |
| Fallback sem canal | confirmação modelo | `CONFIRMATION_UNAVAILABLE` | `CONFIRMATION_UNAVAILABLE` | — |

**Fato PROVEN:** CLARA e VISTA implementam o **mesmo** contrato — challenge
emitido no PREPARE, vínculo `actor_sub + proposal_id + plan_hash + target_ref
+ expiry + origin`, estados `PENDING → APPROVED → CONSUMED | EXPIRED | REVOKED`,
aprovação apenas por rota BFF autenticada com step-up token, artifact =
`challenge_id`, consumo atômico no COMMIT. VISTA adaptou o desenho CLARA **sem
import cross-context**.

## 3. Inventário do canal humano confiável (RQ-02)

| Candidato | Owner | Identidade | Autenticação | Evidência |
|---|---|---|---|---|
| **Portal Minha DELPI — sessão Keycloak** | `portal/` | usuário individual | Keycloak/OIDC; `AuthContext.getFreshAccessToken()` força `keycloak.updateToken(-1)` → JWT novo com `iat` fresco; refresh token vive na sessão do Portal, **inalcançável pelo transporte MCP/agente** | `portal/src/state/AuthContext.tsx:332-338` |
| **MFE do bounded context** | `plugins/<ctx>` | mesmo `sub` | recebe `getFreshAccessToken` via `configureHttpClient` injetado pelo AppHost | `AppHost.tsx:443,497,516` |
| **BFF consent routes do owner** | `<ctx>-api` | `sub` do Bearer | `validate_token` (delpi_auth) + `iat >= challenge.created_at` | `vista_consent_routes.py`, `clara_consent_routes.py` |
| Canal conversacional (chat) | CLARA | — | `consent_channel` config; aceite de risco documentado pelo owner (R-CLARA-01) — **não é prova independente** | `consent_channel.py` |

**Respostas às 8 perguntas do brief:**

1. Tela autenticada para revisar: **SIM** — padrão `ClaraConsentPage`.
2. Independente do modelo: **SIM** — Portal + Keycloak, fora do transporte MCP.
3. Backend identifica aprovador: **SIM** — `actor_sub` do step-up JWT.
4. Vínculo à proposta exata: **SIM** — `proposal_id + plan_hash`.
5. Step-up: **SIM** — `iat >= challenge.created_at`, já implementado 2×.
6. Prazo e uso único: **SIM** — `expires_at`, `CONSUMED` atômico, índice
   parcial `PENDING` por proposta.
7. Sem alterar OAuth do DAVI: **SIM** — o canal é HTTP autenticado do Portal;
   o MCP continua user-JWT verbatim.
8. Retorno ao ChatGPT: usuário aprova no Portal; o modelo apresenta o
   `consent_artifact` (challenge_id) no próximo ACT — ou, no fluxo assistido,
   o ACT é re-chamado após o usuário dizer "aprovei" e o backend verifica o
   estado APPROVED (o artifact é verificado no servidor, não confiado).

## 4. Contrato proposto (RQ-03/RQ-05)

```text
A. PREPARE (execute phase=prepare)
   api-delpi: valida actor, lê SI (JWT do usuário), valida capacidade,
   sela proposta (actor, capability, exact_change, fingerprint, TTL).
   → api-delpi chama SI: POST /strategic-indicators/consent/challenges
     (JWT do usuário) com {proposal_id, plan_hash, target_ref, action,
      expires_at, plan_display, origin='davi-mcp', correlation_id}
   SI: mint PENDING challenge (actor_sub = sub do JWT).
   Resposta MCP: resumo + consent_url (Portal/MFE) + challenge_id.

B. REVISÃO HUMANA (Portal)
   MFE strategic-indicators abre página de consentimento:
   GET /strategic-indicators/consent/challenges/{id} (JWT da sessão)
   → exibe operação, indicador, exercício, filial, versão, antes/depois,
     curva mensal, efeitos indiretos (superseded_goal_ids), solicitante.
   Usuário aprova/rejeita explicitamente.

C. APPROVE
   MFE: POST .../challenges/{id}/approve com step-up token
   (getFreshAccessToken → iat > challenge.created_at).
   SI: revalida sub, PENDING, não expirado → APPROVED + consent_record.

D. ACT (execute phase=act)
   modelo envia proposal_handle + consent_artifact (challenge_id).
   api-delpi: consume proposal (atômico) → pede a SI:
   POST .../consent/challenges/{id}/verify-consume (JWT do usuário)
   SI: exige APPROVED, actor_sub == sub, proposal_id casado, plan_hash
   íntegro → CONSUMED atômico (idempotente a replay).
   api-delpi: confere plan_hash == proposal.content_hash (a prova de que
   o plano aprovado É o plano selado — o modelo não pode trocar payload).
   → executa write no SI (JWT do usuário, OCC, correlation_id=proposal_id)
   → read-back + postcondition → resposta.
```

### Evolução do schema da tool `execute` (compatível)

| Campo | Mudança |
|---|---|
| `phase` | já existe (`prepare`/`act`) |
| `proposal_handle` | já existe |
| `confirm` | **deprecado para ACT produtivo** — mantido apenas para capabilities `auto_act`/teste local |
| `consent_artifact` | **novo, obrigatório** quando a política selada exigir consentimento |
| `target_echo` | opcional — anti wrong-object (eco do alvo exibido ao humano) |
| erros tipados | `CONFIRMATION_REQUIRED`, `CONSENT_MISMATCH`, `CONSENT_CHALLENGE_CONSUMED`, `CONSENT_CHALLENGE_EXPIRED`, `CONSENT_CHALLENGE_NOT_FOUND`, `CONFIRMATION_UNAVAILABLE`, `STEP_UP_TOKEN_STALE` |

Operações `confirm_before_act` **nunca** aceitam `confirm=true` isolado em
produção — mesma política VISTA (artifact mandatório, sem fallback silencioso).

## 5. Boundaries (RQ-04/RQ-09 — Abstraction Gate)

| Responsabilidade | Owner proposto | Justificativa |
|---|---|---|
| Proposta selada | api-delpi | já é o owner (in-process, bounded) — inalterado |
| Emissão/estado do challenge | **strategic-indicators-api** | precedente CLARA/VISTA: consent vive no bounded context dono da mutação; SI já persiste `settings_audit` |
| Aprovação humana | Portal MFE `plugins/strategic-indicators` → SI BFF | mesma forma do `ClaraConsentPage`; plugin já consome sua própria API |
| Persistência consent | `strategic_indicators` schema (nova tabela) | migration V036+, template V019 — **requer aprovação arquitetural** |
| Validação artifact + consume | SI (rota verify-consume) + api-delpi (checa plan_hash) | vínculo cruzado sem estado compartilhado |
| Execução da meta | SI | inalterado |
| Auditoria de negócio | `settings_audit` | já correlacionada por `proposal_id` (736bf7cd18) |
| Auditoria da aprovação | `consent_record` JSONB no challenge (mesmo padrão VISTA) | sem duplicar evento de meta |

Alternativa considerada: challenge no api-delpi — rejeitada porque (a) foge
do precedente owner-local, (b) api-delpi é BFF/orquestrador, não autoridade de
dados, (c) a página de consentimento ficaria sem MFE natural (não existe
plugin DAVI).

## 6. Modelo de dados (gap)

Nova tabela `strategic_indicators.consent_challenge` (espelho V019):
`challenge_id UUID PK, proposal_id TEXT, actor_sub, plan_hash, target_ref,
action, status CHECK(PENDING|APPROVED|CONSUMED|EXPIRED|REVOKED),
origin CHECK('davi-mcp'|'portal'), correlation_id, plan_display JSONB,
approved_by, approved_token_jti, approved_token_iat, consent_record JSONB,
created_at, approved_at, consumed_at, expires_at` + índice parcial único
`PENDING` por `proposal_id`. **Não presumir aplicação — migration depende da
aprovação desta ADR.**

## 7. Segurança (RQ-06) — matriz de ameaças

| Ameaça | Controle | Teste negativo |
|---|---|---|
| Modelo forja consent | challenge só transiciona via BFF + step-up | ACT sem artifact → `CONFIRMATION_REQUIRED` |
| Cross-user | `actor_sub == sub` na aprovação e no consume | artifact de outro usuário → `CONSENT_MISMATCH` |
| Token velho | `iat >= created_at` | JWT pré-PREPARE → `STEP_UP_TOKEN_STALE` |
| Expiração/revogação | `expires_at`, status | expirado → `CONSENT_CHALLENGE_EXPIRED` |
| Artifact adulterado/outra proposta | proposal_id + plan_hash bind | mismatch → `CONSENT_MISMATCH` |
| Payload trocado pós-PREPARE | selo HMAC + plan_hash conferido no ACT | fail-closed |
| Replay ACT | consume proposta + consume challenge, ambos atômicos | 2º ACT → NOT_FOUND/CONSUMED |
| Dois ACT simultâneos | mesma atomicidade | 1 vence, 1 falha |
| AuthZ revogada pós-PREPARE | SI revalida `settings.manage` no write | → 403 |
| Concorrência na meta | OCC `expected_xmin`/`max_version` | → 409, sem audit |
| Canal indisponível | `CONFIRMATION_UNAVAILABLE` (503) — nunca fallback | fail-closed |
| Timeout pós-commit | `unknown_result` + reconciliação por leitura | runbook existente |
| Falha auditoria | mesma tx que a mutação | rollback total |
| Postcondition divergente | `outcome_verification_failed` + reconciliação | coberto |

Consentimento **não** é mecanismo de autorização de negócio: AuthZ final
permanece `strategic-indicators.settings.manage` no backend SI.

## 8. UX alvo (RQ-08)

Usuário pede alteração → DAVI apresenta resumo + link Portal → usuário abre a
página autenticada, revisa e aprova → retorna ao chat ("aprovei") → DAVI chama
ACT com o artifact → resultado verificado pelo read-back SI.
Rejeição: challenge `REVOKED`/expira naturalmente → novo PREPARE.
Sessão perdida: re-login no Portal emite novo token (iat renova).
Sem acesso: `CONFIRMATION_UNAVAILABLE` explicado ao usuário.

## 9. ADR — recomendação

**Decisão proposta:** adotar o padrão VISTA/CLARA com challenge persistido no
**schema `strategic_indicators`** (owner da mutação), rotas BFF de consent no
SI, página de aprovação no MFE `plugins/strategic-indicators` via step-up do
Portal, e `consent_artifact` obrigatório no ACT para capabilities
`confirm_before_act`. api-delpi mantém a proposta selada e orquestra
issue→verify-consume pelo JWT do usuário — sem segundo MCP, sem nova
autenticação, sem import cross-context.

**Consequências:** +1 migration (V036+), +3 rotas SI, +1 página MFE, pequena
evolução do schema `execute`. ACT produtivo só após essa cadeia validada.

## 10. Briefing da menor implementação (após aprovação)

1. `V036__consent_challenge.sql` (espelho V019, schema SI).
2. Repositório + service de consent no `si_app` (adaptar contrato VISTA, sem import).
3. Rotas `GET/POST /strategic-indicators/consent/*` com `settings.manage` + step-up.
4. api-delpi: `issue` no PREPARE, `verify-consume` no ACT, `consent_artifact`
   no schema do `execute`, remoção de `confirm=true` como prova nas
   capabilities confirm_before_act.
5. Página de consent no plugin SI (`httpPostStepUp`, `configureHttpClient`).
6. Testes: matriz RQ-06 (18 casos) + regressão portal/READ.

**Bloqueio mantido:** sem aprovação desta ADR e sem o canal implementado,
`PRODUCTION_ACT` permanece bloqueado.
