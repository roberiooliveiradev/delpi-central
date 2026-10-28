# DÉLIA — Secret Exposure Cleanup and Permanent Prevention

**TASK_ID:** `DELIA-C3-SECRET-EXPOSURE-CLEANUP-AND-PREVENTION-01`
**Data:** 2026-10-28
**Branch:** `main`
**Fase:** C3 (não avançada)
**Decisão:** `CLEANUP_EXECUTED_LOCAL; PREVENTION_DEPLOYED; RISK_ACCEPTANCE_PENDING_SECURITY_OWNER`

## 1. Reancoragem

```text
BASE_HEAD=c370a7fa2b
ORIGIN_MAIN=93ded7d593 (puxada durante a tarefa; inclui revisão independente do Doc 173)
WORKTREE_STATUS=clean em delia-semrel-wt; worktrees irmãos não tocados
CURRENT_PHASE=C3   CP_RQ=NOT_ADVANCED
AUTHORITIES_READ=16→50→17→49→51→52→21→20→25 + docs 170–173 + revisão 93ded7d593
```

A revisão independente do Doc 173 (`93ded7d593`) rebaixou `SECURITY_GATE` para `BLOCKED/PENDING_REMEDIATION` e classificou a exposição da chave como prioridade. Esta task é a remediação autorizada: **limpeza local + prevenção permanente — sem rotação** (rotação exige owner de segurança).

## 2. Escopo e owners

| Superfície | Owner | Ação |
|---|---|---|
| `history_*.md` em `%APPDATA%\devin\cli\summaries\` | usuário/executor local | sanitizado |
| `sessions.db` + WAL (`%APPDATA%\devin\cli\`) | plataforma Devin (CLI) | `EXTERNAL_ARTIFACT_REMEDIATION_REQUIRED` |
| Cache de overflow `%TEMP%\devin.exe-overflows\` | plataforma Devin | verificado, 0 matches |
| Contexto no provider OpenRouter | OpenRouter | fora de alcance — residual externo |
| Repositório/worktrees/histórico git | repo | verificado limpo |
| srv-api host e container `delpi-delia-api` | infra | verificado limpo |

## 3. Inventário da exposição (sem valores)

Padrão detectado: chave de API do provider OpenRouter (formato `sk-or-v1-…`, 73 chars). Nenhum valor foi impresso, copiado ou enviado a modelo nesta task; detecção por match/presença/contagem apenas.

| ARTIFACT_ID | LOCATION_CLASS | MATCH_COUNT | CLEANUP_ALLOWED |
|---|---|---|---|
| `history_*.md` (29 arquivos) | histórico local de sessões do executor | ≥1 por arquivo | YES — executor-controlled |
| `sessions.db` | DB SQLite gerenciado pela plataforma Devin CLI | 120 | NO — plataforma |
| `sessions.db-wal` | WAL do mesmo DB | 7 | NO — plataforma |
| `devin.exe-overflows\*` (74.679 arquivos) | cache de saídas de ferramenta | 0 | n/a |
| `cli\logs\` | logs da plataforma | 0 | n/a |
| PSReadLine history | histórico PowerShell do usuário | 0 | n/a |
| WSL `/tmp`, `~`, `.bash_history` | filesystem local | 0 | n/a |
| worktrees (3) + histórico git | repo | 0 (apenas placeholders de 13 chars) | n/a |
| srv-api `/tmp`, `~operador` | host de produção | 0 | n/a |
| container `delpi-delia-api` `/tmp`,`/app` | runtime produtivo | 0 | n/a |

A contagem subiu de 18→29 arquivos de histórico porque novas sessões foram registradas entre o Doc 173 e esta task — evidência de que a exposição se repetia enquanto a chave permanecia ativa e era lida por dumps de ambiente.

## 4. Sanitização executada

- **29 arquivos** `history_*.md` sob controle legítimo do executor: valor substituído por `[REDACTED_SECRET]` via regex presença-only, conteúdo não sensível preservado (preferência por sanitização sobre apagamento integral, conforme task).
- **Verificação residual:** re-scan no diretório → `REMAINING_FULL=0`, `REDACTED_MARKERS=29`.
- Permissões/integridade preservadas (edição in-place via PowerShell nativo).

## 5. Residual externo / fora de alcance

```text
sessions.db + WAL        → EXTERNAL_ARTIFACT_REMEDIATION_REQUIRED
   (DB SQLite gerenciado pela plataforma Devin CLI; edição de bytes
    corromperia o arquivo; remediação = rotação da chave + limpeza
    de sessões pelo mecanismo da plataforma)
Contexto OpenRouter      → cópia no provider não eliminável localmente
Backups/snapshots        → fora do alcance desta task
```

**Consequência honesta:** `ZERO_EXPOSURE` universal **não** pode ser declarado. A única remediação que elimina o risco residual é a **rotação/revogação da chave pelo owner de segurança** — enquanto a chave atual permanecer válida, as cópias residuais (DB da plataforma, contexto do provider) são materialmente perigosas.

## 6. Diretrizes permanentes implementadas

| Artefato | Ação |
|---|---|
| `.cursor/rules/secret-handling-diagnostics-safety.mdc` | **NOVO** — filha de `platform-security-identity-authorization.mdc`; proíbe exposição, define diagnósticos seguros, gates pré-execução, tratamento de tool output e resposta a incidente |
| `.cursor/rules/responsibility-map.json` | regra registrada sob o owner transversal de segurança |
| `docs/11-padroes-de-desenvolvimento/inventario-regras-cursor.md` | inventário atualizado |
| `scripts/audit_cursor_rules.py` | `OK: governança das regras Cursor válida` |

## 7. Reuse Gate — prevenção técnica

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Mecanismos inventariados e reutilizados/estendidos:

- `scripts/ci/audit_architecture_phase3.py` — gate CI `SECRET_IN_LOG`/`SECRET_LITERAL` **estendido** com `PROVIDER_CREDENTIAL_RE`: detecção generalizada (não específica de OpenRouter) de `sk-*` (≥20 chars), `gsk_*`, `xox*`, `gh[pousr]_*`, `AKIA*`, JWT `eyJ…` em linhas adicionadas, com isenção de placeholders e escopo de produção preservado. Cobre o gap anterior: `.env` com `KEY=valor` sem aspas e chaves literais soltas.
- `shared/delpi_mcp/errors.py` `redact_error_details` — referenciado pela nova regra (não modificado).
- `observability-standards.mdc` — redaction de logs referenciado (não modificado).
- Nenhum secret manager novo, nenhum filtro duplicado, nenhuma regex específica do incidente.

## 8. Testes (credenciais sintéticas apenas)

`scripts/ci/test_audit_architecture_phase3.py` — 3 testes novos:

- `test_provider_credential_literal_detected` — 6 formatos sintéticos (openrouter-shape, groq, github, aws, jwt, bare `.env` line) → `SECRET_LITERAL`;
- `test_provider_credential_short_placeholder_not_flagged` — placeholder curto não é flagueado;
- `test_provider_credential_safe_text_not_flagged` — texto inócuo com prefixo `sk-` curto não é flagueado.

```text
RESULTADO: 22/22 testes OK (unittest local)
REGRESSÃO: nenhuma — gate só ganhou um detector; isenções preservadas
```

## 9. Decisão sobre rotação

```text
KEY_ROTATED=NO   KEY_REVOKED=NO   (não autorizado nesta task)
RISK_ACCEPTANCE_STATUS=RISK_ACCEPTANCE_PENDING_SECURITY_OWNER
SECURITY_OWNER=infra/security + owner do segredo OpenRouter
```

O owner de segurança deve: rotacionar/revogar a chave OpenRouter; verificar substituição nos consumidores legítimos (`delpi-delia-api` env); avaliar limpeza de sessões/DB da plataforma Devin; e ratificar formalmente a aceitação ou a remediação. **Não há presunção de encerramento do risco.**

## 10. Limitações

- `sessions.db`/WAL continuam contendo o valor até remediação da plataforma/rotação — documentado, não corrigível por byte-edit seguro.
- Cópia no contexto do provider não é alcançável localmente.
- A sessão corrente desta task não contém o valor (nunca impresso) — novos históricos não reintroduzirão o segredo **se** dumps de ambiente deixarem de acontecer; a nova regra `.cursor` normatiza isso, mas regra não é enforcement físico.
- Gate CI cobre apenas código commitado no repo — não cobre artefatos locais fora do repo (a sanitização manual + regra de conduta cobrem essa superfície).

## 11. Execução e drift

```text
PRODUCTION_CODE_MODIFIED=NO   PRODUCTION_CONFIG_MODIFIED=NO
KEYCLOAK_MODIFIED=NO   MODEL_CHANGED=NO   DEPLOY_EXECUTED=NO
AUDIT_EVIDENCE_PRESERVED=YES (doc 173, ledger, revisão — sanitizados já no autor)
EXECUTION_DRIFT=NONE
```

## 12. Veredito

```text
LOCAL_CLEANUP=DONE_AND_VERIFIED (29/29, residual 0)
PREVENTION=DONE (regra .cursor + mapa + inventário + gate CI estendido + testes)
EXTERNAL_RESIDUAL=sessions.db+WAL+provider — pendente de owner
FINAL_VERDICT=STABLE_WITH_RESIDUAL
INDEPENDENT_REVIEW=PENDING
NEXT_BOUNDED_STEP=rotação OpenRouter pelo owner de segurança +
 remediação de sessões da plataforma Devin + ratificação do reset
 de identidade (Doc 173); depois a task de recuperação por descrição.
```
