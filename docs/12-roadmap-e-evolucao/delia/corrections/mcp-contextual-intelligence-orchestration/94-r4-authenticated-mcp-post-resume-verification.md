# 94 — R4: verificação pós-resume com MCP autenticado real

**TASK_ID:** `DELIA-C3-GOVERNED-RESUME-R4-AUTHENTICATED-MCP-VERIFICATION-01`
**Data:** 2026-10-22 · **Escopo:** fechar o resíduo material R4 do doc 92 —
`REAL_MCP_AUTHENTICATED_POST_RESUME=TEST_NOT_RUN` — provando a cadeia
governada completa com credencial delegada legítima de usuário dev.
**Não é** uma nova implementação de retry: o mecanismo CP4/CP5 foi apenas
exercitado; os limites aprovados foram preservados
(`DELIA_MAX_GOVERNED_ATTEMPTS=2`, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS=60`,
teto por estágio de 30s, `PERSISTENCE=NONE`, `PRODUCTION_ACTIVATION=NO`).

## 1. Credential gate

| Item | Evidência |
|---|---|
| Identidade de teste legítima | `DEV_PORTAL_*` provisionada pelo `keycloak-dev-bootstrap.sh`; password grant no client público `delpi-central` → HTTP 200, `expires_in=300`, `scope=openid email profile` (nunca impresso) |
| Keycloak dev | `delpi-keycloak` healthy, realm `delpi` live |
| Troca delegada (RFC 8693) | `delia-api` (client confidencial) → token resource-bound; `sub` preservado, `azp=delia-api`, `scope` inclui `mcp:tools`, `aud` inclui `delpi-central`, URL do recurso e `mcp-api-delpi` |
| Contexto do usuário no worker | `bind_subject_bearer`/`unbind_subject_bearer` via `ContextVar`; binding reset em `finally` |
| Credenciais administrativas | usadas **somente** para o cenário de revogação (toggle `enabled` do usuário); nunca como substituto de usuário |

## 2. Defeito ambiental reproduzido e corrigido (RED → GREEN)

**RED:** com credencial delegada válida, `tools/list` em DAVI/TÉO/VISTA falhava
fechado com `mcp_authentication_failed` — a troca retornava token, mas o
endpoint MCP rejeitava.

**ROOT CAUSE:** mismatch de issuer. `DELIA_TOKEN_EXCHANGE_URL` apontava para o
backchannel interno (`keycloak:8080`); com `KC_HOSTNAME=localhost` e sem
`KC_PROXY_HEADERS` no dev, o Keycloak estampa `iss` com a porta do request
(`http://localhost:8080/auth/realms/delpi`), enquanto todo resource server
valida `KEYCLOAK_ISSUER=http://localhost/auth/realms/delpi`. Em produção
`KC_PROXY_HEADERS` resolve isso via host encaminhado; em dev não há proxy
interno no caminho.

**Fix candidato descartado:** `KC_HOSTNAME_STRICT=true` +
`KC_HOSTNAME_BACKCHANNEL_DYNAMIC=false` — verificado empiricamente, o `iss`
interno continuou com `:8080`; alteração revertida.

**MINIMAL DIFF (owner: `platform-delivery-runtime-operations`, escopo dev-only):**
`infra/docker-compose.dev.yml` — `DELIA_TOKEN_EXCHANGE_URL` passa a ter default
pela rota pública do gateway (`http://delpi-gateway/auth/...`), que carrega o
mesmo path público usado pelo portal e produz `iss=http://localhost/...`.
Permanece env-overridable (mesmo padrão do compose produtivo, que preserva
`${KEYCLOAK_URL}` como default — em prod o `KC_PROXY_HEADERS` já mantém o
issuer canônico).

**GREEN:** troca via gateway → `iss=http://localhost/auth/realms/delpi` para o
subject token e para o token trocado; `tools/list` autenticado PASS nos três
MCPs (DAVI=2 tools, TÉO=23, VISTA=12). Sem bypass: signature, iss, aud, exp,
`mcp:tools` continuam validados pelos resource servers.

## 3. Execução — harness

`delia-api/scripts/r4_authenticated_resume_eval.py` compõe a cadeia real:
`Settings` (com o gate fail-closed de egress local) →
`OpenAICompatibleModelInvocationAdapter` (Ollama `qwen2.5:3b`, único provider
permitido) → `InvokeModel` → `_compose_turn_handler` → `McpSpecialistAdapter`
→ `_wire_delegated_credential_provider` (Keycloak real) → `SpecialistInterop`.
O subject bearer é um token real do usuário dev obtido por password grant e
bound pelo mesmo seam do worker NDJSON. Contadores de instrumentação medem
chamadas de modelo por estágio e chamadas `tools/list`/`tools/call`; timeouts
de estágio são injetados deterministicamente como
`ModelInvocationError(TIMEOUT)` — o mesmo tipo produzido pelo provider real —
mapeado para `_StageDeadlineExceeded` no boundary governado.

Pergunta semântica usada para S1–S4: `use o mcp vista para listar as
playlists` — roteia para `vista.list_playlists` (READ, sem argumentos
obrigatórios). A seleção permaneceu semântica e governada; nenhum MCP foi
chamado artificialmente.

## 4. Resultados por cenário (wire real)

| Cenário | Resultado | Evidência |
|---|---|---|
| S1 READ real sem timeout injetado | `GROUNDED`, `COMPLETED` | `vista.list_playlists` invocado; resposta contém playlist real (`id/name/revision`); `mcp_invoke_calls=1`; 60,03s ≤ budget; `CONTINUING=1` (um timeout real de estágio resumido) |
| S2 READ após retry do LLM | `GROUNDED`, `COMPLETED` | timeout injetado em `select_capability` → `CONTINUING` → 2ª tentativa → READ real com credencial delegada → outcome autoritativo; `mcp_invoke_calls=1` |
| S3 timeout após outcome READ | `GROUNDED`, `COMPLETED` | READ concluído → timeout injetado em `grounded_synthesis` → `mcp_invoke_calls` permaneceu **1** (READ nunca reexecutado) → resposta completada com o outcome checkpointado |
| S4 revogação antes da retomada | `COMPLETED` (comportamento documentado — ver §5) | usuário desabilitado entre tentativas; a 2ª tentativa reusou a credencial já trocada (cache process-local por sujeito+recurso) → invoke real sucedeu |
| S5 bearer forjado | `BLOCKED`, honesto | as 3 trocas recusadas no wire; surface vazia; `mcp_invoke_calls=0` |
| S6 capability indisponível | `unknown_capability` | catalog live listado; invoke de capability inexistente recusado antes do wire; `mcp_invoke_calls=0` |
| S7 falha real do MCP | `mcp_unavailable` | base URL morta (`:9`) → surface listing falha fechado; `mcp_invoke_calls=0` |
| S8 PREPARE/ACT sem repetição | guard confirmado | surfaces live incluem PREPARE (`teo.prepare_*`, `vista.prepare_change`) e ACT (`commit_proposal`); **zero** invocações PREPARE/ACT em todos os cenários; invoke forjado → `unknown_capability`; `mcp_invoke_calls=0` |
| S9 cancelamento durante processamento | `BLOCKED` <1s | `cancel_check` disparado no 2º check → terminal honesto único e bounded |
| S10 argumentos inválidos | `mcp_protocol_error` | `davi.discover_delpi_information` invocado de verdade com args inválidos → owner recusou (contrato autoritativo no wire); `mcp_invoke_calls=1` |

## 5. Finding: janela de revogação intra-interação

Probe direto (presence-only) separa dois seams:

- grant de senha com usuário **desabilitado** → `invalid_grant` (400) ✓
- troca RFC 8693 com subject token emitido **antes** do disable →
  `invalid_request` (400) ✓ — a plataforma **falha fechado** numa troca nova.

Mas dentro de uma interação em curso a 2ª tentativa não re-troca:
`InMemoryDelegatedTokenCache` (process-local, chave por fingerprint de
sujeito+recurso, TTL ≤ token, hard cap) reutiliza a credencial legítima obtida
na 1ª tentativa. Consequência honesta: desabilitar o usuário **mid-turn**
(<60s) não propaga para a retomada — o credential foi adquirido enquanto o
usuário estava válido e não há verificação de revogação por tentativa.

**Classificação:** `REVOCATION_BEFORE_RESUME=EXECUTED — OBSERVED_BEHAVIOR`.
Fechado contra novas trocas e grants; aberto dentro da janela de credencial
já emitida na interação (≤ TTL residuais dentro do budget de 60s). Não é
defeito corrigível por patch pontual — alterar o ciclo de vida do token
delegado (re-exchange por tentativa ou probe de revogação) é decisão de
arquitetura. Resíduo contratual do doc 92 preservado: revogação invisível a
`tools/list` segue não observável por desenho.

## 6. Evidência sanitizada consolidada

```text
IDENTITY_CONTEXT=delpi:dev-portal-user (sub preservado; azp=delia-api;
                 mcp:tools; aud=delpi-central|mcp-api-delpi|resource-url)
CORE_AUTHZ_RESULT=delia.access exigido e presente; troca confidencial OK
MCP_OWNER=tv-dashboard-api (VISTA) — seleção semântica do modelo
CAPABILITY=vista.list_playlists — DISCOVERY-class publicada
OPERATION_CLASS=READ(efetiva no invoke)/DISCOVERY(owner-typed)
ATTEMPT_COUNT=2 (S1/S2/S4); 1 (S3) — nunca 3
RESUMED_STAGE=select_capability (S2/S4); native_assessment (S1);
              grounded_synthesis falhou pós-outcome sem replay (S3)
REPLAYED_STAGES=somente propostas tipadas do checkpoint; READ nunca reexecutado
MCP_INVOKE_COUNT=1 por cenário que alcançou invoke; 0 nos negativos
MCP_OUTCOME=real (S1/S2/S3/S4); mcp_protocol_error owner-side (S10);
            ausente nos bloqueados
EVIDENCE_STATUS=GROUNDED nos cenários que completaram; NON_GROUNDED nos honestos
GROUNDING_STATUS=GROUNDED S1–S4; NON_GROUNDED S5/S9
TOTAL_LATENCY=0.96s–60.03s (budget 60s respeitado)
SINGLE_TERMINAL=YES em todos os cenários
```

## 7. Limites preservados

`MAX_ATTEMPTS=2` · `TOTAL_BUDGET_SECONDS=60` · `PER_ATTEMPT_MAX_SECONDS=30` ·
`PERSISTENCE=NONE` · `PRODUCTION_ACTIVATION=NO` · sem scheduler/fila/engine/
registry/segundo planner · ACT nunca reexecutado nem invocado.

## 8. Veredito

`R4=EXECUTED` — recuperação governada real comprovada: timeout recuperável de
estágio LLM → checkpoint tipado → 2ª tentativa governada → autorização live →
MCP READ autenticado com identidade delegada legítima → evidence → outcome →
resposta na interação original. `REAL_MCP_AUTHENTICATED_POST_RESUME=YES(dev)`.

Resíduos materiais:
1. **Janela de revogação intra-interação** (§5) — credencial delegada emitida
   no turno é reutilizada; desabilitar o usuário mid-turn não propaga.
   Decisão de arquitetura exigida (re-exchange por tentativa vs cache por
   turno).
2. Modelo local ≤3B CPU-only mantém as limitações do doc 93 (latência de
   estágio ocasionalmente >cap → honest `PROCESSING_TIMEOUT`; outputs
   não-JSON parciais) — classificadas, não compensadas.
3. Cobertura de `partial_result`/`insufficient_evidence` exercida via
   terminais honestos observados; schema-changed exercido via rejeição de
   argumentos no owner (S10).

`PRODUCTION_ENABLED=NO` — ativação continua exigindo release separado.
`I04_ACCEPTED=NO` · `C3_EXECUTED=YES` · `PRODUCTION_LLM_CONFIGURATION=UNCHANGED`
· `EXTERNAL_MODEL_CALLS=0` · `COST_EXTERNAL=0`.


## 9. Revisão de coordenação — 2026-10-22

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (DEV ONLY).** A entrega `DELIA-C3-GOVERNED-RESUME-R4-AUTHENTICATED-MCP-VERIFICATION-01` foi revisada documentalmente a partir do relatório 94 e do HEAD vigente; os cenários de runtime são evidências reportadas pelo executor, não reexecutadas de forma independente nesta revisão (`INDEPENDENT_RUNTIME_REEXECUTION=TEST_NOT_RUN`). R4 encerra a lacuna **funcional** de MCP autenticado pós-resume em dev: S2 demonstrou um timeout de seleção, segundo attempt, consulta real `vista.list_playlists` GROUNDED, terminal único e orçamento aprovado; nenhum modelo externo pago foi usado. Config de produção não alterada.

**Gate de segurança material:** S4 mostrou que um usuário desabilitado entre tentativas ainda pode ter invocação bem-sucedida por `InMemoryDelegatedTokenCache` do token obtido antes da revogação. Um **novo** token exchange com sujeito desabilitado falha; o cache evita a nova troca no resume. Logo `AUTHZ_LIVE_AFTER_MID_TURN_REVOCATION=FAIL_OBSERVED` sob essa semântica estrita, e `REVOKED_USER_BLOCKED_ON_RESUME=NO`. O resultado S4 é uma observação correta e não deve ser rebatizado como PASS por existir validação no tools/list da credencial antiga. O contrato canônico de revogação/credencial por boundary deve ser consultado antes de definir mitigação: `REUSE` token legitimamente emitido dentro TTL pode ser comportamento aprovado da plataforma para READ, mas **não** atende ao requisito mais forte de revogação imediata; decidir explicitamente, não assumir. Evitar solução improvisada na DÉLIA; verificar owner de token exchange/cache e Core/Domain live AuthZ, custo/latência e efeitos sobre fluxo READ versus PREPARE/ACT.

**Decisão de coordenação:** `R4_DEV_FUNCTIONAL=ACCEPT`; `CP1_CP5_DEV_RECOVERY=ACCEPT_WITH_RESIDUAL`; `REVOCATION_POLICY=ARCHITECTURE_DECISION_REQUIRED`; `RECOVERY_PRODUCTION_ENABLE=BLOCKED` até decisão e teste negativo correspondente; `I04_ACCEPTED=NO`. O próximo bounded step de segurança é review de ownership/contrato de cache/revogação (não nova refatoração de orquestração). Depois release separado com SHA/config, rollback, observabilidade e smoke real. Continuar em frente com a task de **CRI runtime efetivo em produção / prosa natural**, sem misturar essa investigação com CP4/R4 ou com os incidentes contextuais DAVI e painel Contexto. Nenhum deploy autorizado neste parecer.
