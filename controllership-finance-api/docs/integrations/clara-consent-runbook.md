# Runbook — Consentimento CLARA (consent challenge, V014)

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
