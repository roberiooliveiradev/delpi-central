# Doc 125 — CLARA-MCP-SEMANTIC-002: relatório de execução

**Status:** `PROVEN` — implementação, testes, deploy e evidências de
runtime concluídos em uma iteração.
**Autoridade:** decisão do PO `CLARA-MCP-SEMANTIC-002` (execução direta
proporcional ao risco, orquestração multi-op e deploy produtivo), sobre
a base `CLARA-MCP-SEMANTIC-001` (doc 119, `3f36137dc3`).
**Contrato publicado:** [Documento 124](./124-clara-write-execution-risk-policy.md)
— política de escrita por risco; [Documento 106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md)
Adendo 3 registra a supersession prospectiva.

## FINAL EXECUTION REPORT

```text
CLARA-MCP-SEMANTIC-002 — EXECUTION REPORT

BASE HEAD:        f9b238f40e (origin/main após fetch — inclui o fix
                  R06/R07 concorrente)
FINAL HEAD:       06f6de9b6e — feat: CLARA-MCP-SEMANTIC-002
COMMIT SHA:       06f6de9b6e (rebase do 3490d16c51 sobre f9b238f40e)
DEPLOYED SHA:     06f6de9b6e — prod, tree limpa, container healthy
PREVIOUS IMAGE:   sha256:52cd488b8ed75d3ee0dfd856cb0a8c4e07c43af2a7fbbed6aaba663fa36aa147
NEW IMAGE:        sha256:a7d2194a73c3a70f2dff5a225da598b55b1614b230009f5ee57ef6009c7e46b5

CONTRACT POLICY BEFORE/AFTER:
  antes: consentimento verificável universal para TODA escrita MCP
         (doc 106 §3 + V013/V014); phase=direct rejeitado tipado.
  depois: política por risco (doc 124) — 11 DIRECT_ALLOWED executam
         já (mesmo núcleo governado menos o desafio); 37
         CONFIRMATION_REQUIRED inalterados; BLOCKED = erro tipado.
         Doc 106 Adendo 3 + matriz SEMANTIC-001 atualizadas.

CAPABILITIES DIRECT_ALLOWED (11):
  clarification.open, pendency.create, pendency.claim,
  pendency.transition, item.mark_not_applicable,
  item.revert_not_applicable, item.request_correction,
  document.post_message, document.answer_adjustment,
  received.post_message, received.create_adjustment
  (efeitos: registro/transição/mensagem/resposta — reversíveis ou
  corriqueiros; OCC por expected_revision onde aplicável)

CAPABILITIES CONFIRMATION_REQUIRED (37):
  todas as decisões de fechamento, workflow de pacote/competência,
  catálogo/template de governança, operações sobre terceiros,
  confirmação DRE e as 6 destrutivas roteadas a `delete`:
  catalog.entry_deactivate, checklist.version_discard,
  checklist.version_inactivate, document.cancel, item.cancel,
  package.confirm_terminal_rejection.

CAPABILITIES BLOCKED:
  não é lista — resultado tipado por pré-condição
  (not_implemented, forbidden, validation_error,
  snapshot_unavailable, proposal_stale, idempotency_conflict,
  consent_required). Nenhum caminho BLOCKED aplica efeito.

MIGRATION MATRIX:
  matriz SEMANTIC-001 atualizada com coluna de risco e apontamento
  ao doc 124; tabela completa por efeito no doc 124 §3.

SIX MCP TOOLS:
  inalteradas — get_context, read, analyze, knowledge, execute,
  delete (tools/list prod = 6; caps = 48 no runtime).

AUTHZ / CORE / RESOURCE SCOPE:
  _check_gate revalidado na execução direta (access/manage/dre);
  e2e PG prova: identidade sem vínculo dre falha `forbidden` antes
  de qualquer efeito — proposta nunca selada.

IDEMPOTENCY / OCC / AUDIT:
  V019 — coluna idempotency_key + índice único parcial
  (actor,capability,key): proteção de repetição física, não
  semântica; key explícita ou derivada do plano canônico; retry
  devolve `replayed:true` (e2e PG: mesmo pendency_id); UNKNOWN é
  bloqueio honesto; OCC por expected_revision (e2e: conflito tipado,
  sem overwrite); auditoria CLARA_DIRECT_ATTEMPT/ACT/REJECTED.

BATCH / DEPENDENCIES / PARTIAL OUTCOME:
  execute(batch,phase omitida/direct/run) orquestra N ops:
  diretas executam já em ordem; governadas voltam
  pending_confirmation com confirmation_url e bloqueiam
  dependentes (dependency_not_executed); falhas são parciais e
  honestas; phase=prepare mantém o consentimento consolidado do
  doc 106. Sem transação global implícita.

CONSENTMENT REGRESSION:
  prepare/commit/batch/consent e _require_consent inalterados;
  desafio V014 continua emitido só no caminho governado (e2e PG:
  zero challenges para execução direta); confirmed=true / texto do
  modelo jamais é consentimento.

TESTS PASSED/FAILED:
  PASS — 998 testes (suíte inteira, incluindo PG dedicada):
  27 novos test_clara_direct_execution (núcleo direto, replay,
  conflito, gates, orquestração, catálogo) + 5 e2e PG
  (sem consentimento, replay real, governed segue exigindo,
  gate negado sem mutação, OCC) + 35 PG clara + regressões.

ARCHITECTURE AUDITS:
  architecture-phase3, platform-guardrails, openapi-contracts,
  fastapi-authz, backend-boundaries: 0 findings no diff real.

PRODUCTION HEALTH:
  container healthy (health check OK); V019 aplicada no startup
  (migrations_startup_applied count=1); demais serviços intactos
  (delpi-external-data-scheduler unhealthy — preexistente).

PRODUCTION SMOKE:
  tools/list = 6 no runtime; caps=48 (11 direct/6 destructive);
  edge 401 + WWW-Authenticate RFC 9728 íntegro; corpus
  da7f375a-ba46-47b5-ae63-fa0bf02bab54 (70 fontes/2037 itens,
  doc-126 lido no runtime). Mutação produtiva: NENHUMA (somente
  smokes de leitura) — demonstrações de escrita foram no banco PG
  de teste, conforme exigido.

ROLLBACK STATUS:
  git reset --hard f9b238f40e + up-prod-sequential --build
  controllership-finance-api; imagem anterior retida no host
  (52cd488b); V019 é aditiva — rollback não exige drop (a coluna
  fica ociosa; caminho governado não a usa). Corpus anterior
  permanece no histórico (supersede não destrói).

RESIDUAL RISKS:
  - smoke autenticado com usuário real: TEST_NOT_RUN (requer sessão
    host real, como em execuções anteriores);
  - cache de catálogo no host ChatGPT pode exibir a política antiga
    até o refresh do conector;
  - _audit_mcp é best-effort por design (falha de trilha não reabre
    efeito) — invariante pré-existente, não alterada.

EXECUTION_DRIFT:
  - WSL transitório morreu 3× (documento 106 adendo, git ops); o
    append ao doc 106 foi refeito via ferramenta de edição;
  - push inicial rejeitado (origin/main avançou com f9b238f40e R06/
    R07); rebase limpo aplicado — diferença em região disjunta
    (READ_ACTIONS) — e working tree alheio restaurado integralmente;
  - nenhuma premissa de plano invalidada.

FINAL STATUS:
  PROVEN (implementação, testes, deploy, catálogo, corpus);
  TEST_NOT_RUN somente para smoke autenticado host-side.

NEXT STEP FOR CHATGPT PLUGIN REFRESH:
  reconectar o conector CLARA no ChatGPT para re-descobrir o
  tools/list e o catálogo com as flags direct/phase_policy novas;
  rodar aceite apenas em dados de teste autorizados.
```

## Evidências de runtime coletadas

- `tools: ['analyze','delete','execute','get_context','knowledge','read']`
  e `caps: 48` no container produtivo (listagem real).
- `direct:` 11 capabilities e `destructive:` 6 — conferido no
  runtime.
- Logs de startup: `migration_applied name=V019...` +
  `migrations_startup_applied count=1` + `Uvicorn running`.
- Edge: `HTTP/2 401` + `www-authenticate` RFC 9728 (`invalid_token`).
- Corpus: `corpus_version_id da7f375a` publicado; query DB confirma
  `doc-126` com 11 itens ativos.
