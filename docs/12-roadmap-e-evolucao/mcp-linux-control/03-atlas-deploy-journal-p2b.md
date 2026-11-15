# ATLAS P2.2b | Leitores de evidencias e projeto do journal de deploy

> Data: 2026-11-15 | Estado: **CODIGO DOS LEITORES NA MAIN / JOURNAL SOMENTE PROPOSTO**
>
> **NAO existe rota PREPARE/ACT, journal implantado ou deploy automatico.** Este documento nao e migration SQL nem autorizacao para executar operacoes.

## 1. Fontes e fronteiras

- **GitHub:** `linux-ops-mcp/linux_ops_mcp/deploy_evidence_readers.py::GithubReleaseReader` consulta exclusivamente `https://api.github.com/repos/roberiooliveiradev/delpi-central` por GET; nao aceita repositorio, ref flutuante ou URL externa como entrada. Valida SHA completo, HEAD de `main`, ancestry Git compare e workflow runs `push` do SHA exato. Response limitado a 256.000 bytes, timeout de 5s, sem redirects/proxy env, erros sanitizados. Token GitHub opcional e **somente de leitura, provisionado server-side**, nunca vindo da tool MCP. `workflow_ids` obrigatorios pertencem a policy por servico/ambiente, nunca a prompt.
- **Core:** `CorePermissionReader` chama `delpi_auth.middleware.fastapi_auth.load_user_rbac(token, force_refresh=True)` para eliminar fallback de RBAC stale. Identidade, principal humano e token devem vir do middleware validado, nao da entrada de usuario. Compara `id` da resposta com o subject autenticado. Projeta somente as permissoes explicitas `linux_ops.deploy.view` e `linux_ops.deploy.prepare`; nem `is_superadmin=true` equivale a autorizacao. **Os grants ainda nao foram provisionados no Core**.
- **Host:** `HostProof` P2.2a continua sem produtor confiavel. HEAD de GitHub e `git rev-parse HEAD` do checkout **nao provam** qual SHA esta em execucao por container. Nao se deve preencher `deployed_commit_sha` sinteticamente nem ler Docker via MCP. P2.2c deve definir leitor local restrito que confronte release manifest do executor, hash da imagem/servico e saude, expondo somente dados tipados; ate la `HOST_PROOF_MISSING` bloqueia preflight.
- **Ate o presente lote:** nenhum desses leitores esta registrado no `server.py` do ATLAS e nenhum endpoint HTTP os invoca. Os quatro MCP READ existentes nao foram ampliados.

## 2. Ownership de persistencia (decisao arquitetural proposta)

Reusar a infraestrutura PostgreSQL e a politica de migrations `it_portal`, que ja possui:
- runner `it-portal-api/it_portal_app/infrastructure/persistence/migrations_runner.py` com checksum imutavel, transacao por migration e advisory lock;
- trilhas de eventos de infra e os tickets inertes `V014__workstation_bootstrap_tickets.sql` (apenas **padrao de transacao/ledger**, jamais mesma entidade ou permissao);
- `run_migrations_on_startup` sob flag existente.

**Nao criar V016 agora:** o modulo IT Portal evolui em paralelo (Delpi Remote), e um novo numero de migration exige coordenacao de owners; a tabela nao seria utilizada por nenhuma API nesta fase. A proposta deve ser revisada antes de editar migrations. O journal de ATLAS deve manter ownership de dominio distinto do suporte remoto a desktops.

## 3. Modelo de tabelas candidato (NAO EXECUTAVEL / nao aplicado)

### `it_portal.atlas_deploy_proposals`

| Campo | Tipo / regra |
|---|---|
| `id` | UUID PK, gerado pelo backend |
| `requester_subject` | UUID NOT NULL, vindo de Core, sem nome/e-mail no ledger publico |
| `idempotency_key` | UUID NOT NULL; UNIQUE `(requester_subject, idempotency_key)` |
| `environment` | `hml` ou `prod`, CHECK estrito |
| `service_id` | identificador fechado do catalogo de servicos autorizados |
| `approved_commit_sha` | `char(40)`, CHECK `^[0-9a-f]{40}$` |
| `base_deployed_sha` | `char(40)`, CHECK estrito e obrigatorio antes de PREPARED |
| `proposal_hash` | `char(64)`, CHECK SHA-256 canonico, imutavel apos preparo |
| `status` | `pending_approval`, `approved`, `revoked`, `expired`, `executing`, `verified`, `failed_needs_operator`, `rolled_back` |
| `created_at`, `expires_at` | UTC `timestamptz`, expira no maximo em 10 minutos |
| `approved_by`, `approved_at` | preenchidos **apenas** pela API/UI corporativa autenticada apos permissao fresca |
| `execution_id` | UUID unico, apenas depois de executar; nunca definido pelo ChatGPT |

Constraints adicionais: no maximo **uma** proposta `executing` por `(environment, service_id)` com indice unico parcial; `approved_by` presente somente com estado compativel; `expires_at>created_at`; bloqueio de updates de SHA/hash/alvo apos preparo; versionamento otimista `revision`; remover nenhuma proposal por API.

### `it_portal.atlas_deploy_events`

`event_id` UUID PK, `proposal_id` FK com `ON DELETE RESTRICT`, `event_seq` integer monotono por proposta, `event_type` enum CHECK, `actor_subject` UUID nullable quando evento tecnico, `occurred_at` UTC, `reason_code` ENUM allowlisted, `evidence_digest` `char(64)` optional, `workflow_id/run_id` quando CI. `UNIQUE(proposal_id,event_seq)`; API apenas INSERT. Sem bearer, logs, body JSON arbitrario, comando executavel, secrets ou payload de `.env`.

### `it_portal.atlas_deploy_executions` (fase posterior)

`execution_id` UUID PK, `proposal_id` UUID UNIQUE, `executor_operation_id` UUID UNIQUE, `target_sha` canonico, `base_sha`, `started_at`, `completed_at`, `result` CHECK. Serve de ledger idempotente e base de recuperacao de execucao interrompida. Nao criar nesta fase.

## 4. Transacoes e concorrencia

1. **PREPARE** (futuro): chamar Core fresh + GitHub SHA/CI + leitor local, `attest_preview_evidence` e `evaluate_deployment_preview`. Somente se todas as provas forem confiaveis, abrir transacao SQL, inserir proposta e evento `prepared` com `requester_subject/idempotency_key` UNIQUE. Retry retorna **mesma** proposta **somente se** payload e hash identicos; mudanca no hash retorna conflito. Se dependencias cairem, nao gravar proposta valida.
2. **APPROVE** (futuro, UI): reconsultar Core, exigindo `linux_ops.deploy.approve` distinto de `prepare`, fazer `SELECT ... FOR UPDATE`, comparar hash/alvo/SHA/TTL/estado, registrar aprovador nominativo e evento na mesma transacao. Confirmacao apenas no chat **nao** e approval.
3. **ACT** (fase P3): reconsultar Core `execute`, proposal/hash, CI/host/health e aprovacoes; registrar `execution_id` sob lock unico por service/environment **antes** de enviar acao ao executor isolado. Se resposta cair, ler ledger/executor pela idempotency key em vez de reenviar.
4. **CANCEL/EXPIRE/REVOKE:** transicoes condicionais com `UPDATE ... WHERE status=... AND revision=...`; evento de auditoria em mesma transacao. Nunca fazer `DELETE` operacional.
5. **Seguranca do banco:** papel de API com INSERT/UPDATE limitado; deny de UPDATE/DELETE em tabela de eventos; conta de migracao separada; sem escrita SQL livre via MCP. Auditoria append-only para a aplicacao, nao alegar imutabilidade absoluta frente ao DBA.

## 5. Etapas pendentes para P2.2c / P2.3

1. Definir owner de DB e sincronizar proxima numeracao de migration com o Portal TI/Delpi Remote; criar migration nova somente apos revisao e CI PostgreSQL descartavel.
2. Implementar `HostProof` de origem **real** e revisao implantada verificavel; ausencia deve falhar fechado.
3. Definir no backend o catalogo por `service_id/environment`, lista de workflow IDs exigidos e o token de leitura GitHub por secret store. Evitar permitir `approved_run` preenchido pelo ChatGPT.
4. Criar services/repositorios/APIs PREPARE com Core fresh, transacoes, testes concorrentes e registros de auditoria antes de habilitar qualquer tool MCP adicional.
5. Testar em HML, revisar `delpi-verifier` e CI, e so entao considerar rotas para aprovacao.

## 6. Evidencia da fatia P2.2b

- Codigo GitHub/Core: `linux-ops-mcp/linux_ops_mcp/deploy_evidence_readers.py`.
- Testes isolados: `linux-ops-mcp/tests/test_deploy_evidence_readers.py`; **31 PASS locais** (Python 3.13, `httpx.MockTransport`, sem rede, banco ou servidor), e bytes reproduzidos sem divergencia no commit GitHub.
- CI GitHub Actions push/main e verificador independente **a confirmar**, nao assumidos a partir dos testes locais. `python -m compileall` local PASS.
- Nenhum deploy, HTTP endpoint novo, migration, grant, socket Docker, shell ou alteracao em Keycloak/Compose/produção.

**Proxima tarefa segura:** P2.2c, com produtor local de HostProof e DB journal sob aprovacoes internas, sem habilitar ACT antes de P3.
