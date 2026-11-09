# Runbook — Consentimento CLARA (consent challenge, V014)

> **ATUALIZAÇÃO R-CLARA-01 V2 (09/11/2026):** este runbook descreve o caminho V014 legado quando `CLARA_CONSENT_CHANNEL=portal` ou `dual`. A CLARA também suporta o canal `conversational` explicitamente selecionado no backend, conforme doc 124 §11. Nesse modo não há desafio V014 nem URL Portal obrigatória; a confirmação de proposta selada acontece na conversa. O parâmetro `CLARA_CONVERSATIONAL_SECURITY_ACK` foi descontinuado no código; não preenchê-lo para simular aprovação de Segurança. O risco operacional foi aceito pelo owner no doc 150 §20.16. A distinção de garantia humana permanece documentada.


Contrato físico de autorização humana para writes governados da
CLARA (single-op e lote). Authority: Documento 106, Adendo 4;
Documento 14 (segurança). Implementado em
`CF-PROC0072-CLARA-CONSENT-FINAL-REWORK-001`.

## Modelo

```text
PREPARE (prepare / prepare_batch)
  → plano selado: plan_hash + plan_version
  → clara_consent_challenge PENDING (actor_sub, batch_id OU
    proposal_id, plan_hash, plan_version, origin, correlation_id,
    expires_at)
  → resposta MCP: challenge_id + confirmation_url + apresentação

Portal — /apps/controllership-finance/closing/clara-consent
  → GET  /clara/{batches|proposals}/{id}   → plano completo + challenge
  → usuário lê cada operação (descrição funcional, efeito, motivo,
    dependências, impedimentos) e as bloqueadas
  → POST /clara/{batches|proposals}/{id}/consent {challenge_id}
    com token step-up fresco (Keycloak updateToken)

BFF (clara_consent_routes + step_up_consent)
  → validate_token canônico (iat/jti) + authorized_user
  → approve_atomically: binding ator/artefato/plan_hash/version/
    origem/expiração/status — primeira aprovação vence corrida

confirm_batch / commit_proposal (MCP)
  → exige consent_record + challenge APPROVED vinculado ao plano
  → claim transacional consome o desafio (single-use)
  → execução revalida permissões/regras por operação
```

## Invariantes de segurança

- JWT fresco prova **sessão**, nunca aprovação — sem challenge
  `APPROVED`, nenhuma execução.
- `iat` do step-up deve ser ≥ `challenge.created_at` — token
  emitido antes do desafio é rejeitado (`step_up_token_stale`).
- Um desafio autoriza **exatamente** o `plan_hash`/`plan_version`
  selado; plano alterado ⇒ novo desafio.
- Desafio é single-use: `CONSUMED` na transação de claim;
  reuso/expirado/ator divergente ⇒ rejeição tipada.
- `challenge_id` nunca sai para o canal MCP — o modelo não recebe
  nem pode forjar o artefato.
- Consentimento **nunca** substitui autorização: Core/eligibility/
  assignment/scope/business rules revalidados por operação na
  execução (revogação pós-aprovação ⇒ falha tipada).
- Operação sem descrição funcional suficiente é exibida como
  **bloqueada** — nunca autorizada implicitamente.
- Schemas MCP não têm parâmetro de confirmação — `confirmed=true`
  ou texto "sim" no chat não autorizam nada.

## Falhas e diagnóstico

| Sintoma | Causa provável | Ação |
|---|---|---|
| `consent_required` no `confirm_batch` | usuário não aprovou no Portal (ou desafio pendente) | abrir `confirmation_url`, autorizar |
| `consent_challenge_required` (400) | POST consent sem `challenge_id` | cliente deve enviar o `challenge_id` do GET |
| `step_up_token_stale` (403) | `iat` anterior à criação do desafio | reemitir token fresco (Portal já faz `updateToken`) |
| `consent_challenge_expired` | aprovação após `expires_at` | repreparar (PREPARE emite novo desafio) |
| `consent_challenge_mismatch` | ator/artefato/plan_hash/versão divergentes do selado | plano foi alterado ou desafio de outro artefato — repreparar e reapresentar |
| `consent_challenge_consumed` | desafio já consumido por um claim | single-use — repreparar se necessário |
| `BatchActorMismatch` / 403 no GET | sessão de outro usuário | abrir a página com o ator que pediu o lote |
| lote `CONFIRMED` mas execução falha por permissão | autorização revogada após aprovação | esperado — revalidar permissões e repreparar |

## Operação

- Migrations: V014 é up-only; aplicar via `migrations_runner`
  canônico (mesma pipeline das V001–V013). Não resetar produção.
- Desafios `PENDING` expirados são inertes (rejeitados no approve);
  limpeza periódica pode expirá-los por `expires_at` sem risco.
- Auditoria: decisões de consentimento registradas no canal
  `mcp/clara` com `correlation_id` do desafio.


## Evolução — UX conversacional TÉO (`IMPLEMENTED_NOT_CUTOVER`)

O PO escolheu eliminar a exigência de página externa como experiência alvo e aproximar a CLARA do TÉO (segunda chamada com `confirmation=true`).

| Camada | Estado |
|---|---|
| Contrato MCP (`proposal_pending_confirmation`, `confirmation`) | `IMPLEMENTED` |
| Default produção | `CURRENT_RUNTIME` = `CLARA_CONSENT_CHANNEL=portal` (V014) |
| Bypass Portal por `mcp_tool_confirmation` | Só com ack `R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED` + canal `conversational`/`dual` |
| Cutover sensível | `SECURITY_GATE_PENDING` / `CUTOVER_BLOCKED` |
| Página `clara-consent` | Obrigatória no default; não descontinuada |
| Migration V020 | Permite `consent_mode=MCP_CONFIRMATION` em lote (forward-only) |

**Operação segura:** nunca definir o ack em produção sem o texto de aprovação do doc 150 §20.10. Rollback = `CLARA_CONSENT_CHANNEL=portal` e ack vazio.

**Nota de contrato:** `get_context(topic=schema)` agora descreve PREPARE → `proposal_pending_confirmation` → commit/`confirmation=true` e declara honestamente se Portal V014 ainda é obrigatório. Sem canal armado, ACT continua `consent_required`.


## R-CLARA-01 V2 — runbook de cutover conversacional

**Seleção do canal:** somente configuração de backend do deployment oficial; `CLARA_CONSENT_CHANNEL=conversational` habilita PREPARE → confirmação explícita no chat → ACT. Unset/`portal`/`dual`/inválido preservam a exigência de V014. O campo `CLARA_CONVERSATIONAL_SECURITY_ACK` e o valor antigo são obsoletos; não gravar `security_ack=true` no consent_record.

**Operações individuais:** `execute(entity, action, params, phase='prepare')` retorna proposta selada com `proposal_handle`, apresentação, TTL, política e `portal_consent_required=false`. A CLARA apresenta exatamente objeto/efeito/competência, aguarda confirmação explícita do usuário e só então chama `execute(...phase='commit', proposal_handle=..., confirmation=true)`. O backend persiste consent_record com `confirmation_policy=R-CLARA-01-OWNER-RISK-ACCEPTED-V2`, ator e plan_hash, reivindica a proposta de modo atômico, revalida Core/escopo/regras e verifica o resultado por leitura independente.

**Lotes:** `batch.phase=prepare` sela operações, dependências e plan_hash; após confirmação explícita do plano completo, `batch.phase=confirm/commit` recebe handle, plan_hash e `confirmation=true`. Cada operação revalida autorização e negócio; não há atomicidade global prometida. O consentimento MCP é sinal de modelo, não prova V014 independente.

**Verificações:** `GET /clara/consent-policy` autenticado deve retornar `consent_channel=conversational`, `portal_consent_required=false`, `conversational_act_armed=true`; `get_context(topic=schema)` e `tools/list` não devem exigir `confirmation_url`. Testar falhas: ator diferente, hash divergente, TTL, replay, estado obsoleto, permissão revogada e operação sem apresentação. Não confirmar automaticamente operações reais de publicação/inativação.

**Rollback:** retornar `CLARA_CONSENT_CHANNEL=portal`, reiniciar BFF/MCP e comprovar URL V014 e challenge. Aguardar expiração/drenagem de propostas criadas na janela anterior. Não editar V014 ou V020 já aplicadas. Atualizar a definição do plugin MCP somente se as instruções em cache divergirem.
