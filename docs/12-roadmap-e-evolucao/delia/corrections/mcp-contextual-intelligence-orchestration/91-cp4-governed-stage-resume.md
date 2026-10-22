# 91 — CP4 Governed Stage Resume (implementação)

**TASK_ID:** `DELIA-C3-GOVERNED-STAGE-RESUME-01`
**Data:** 2026-10-22
**Base:** `c4cad18724` (origin/main na reancoragem)
**Autoridades:** doc 88 (§8 plano CP4, §10.2 decisão Option B, aprovação de
orçamento 22/10/2026 registrada em `71585d7cd1`), doc 89 (classificação
PROCESSING_TIMEOUT), doc 90 (inventário CP3 + contrato proposto), ADR 58,
`delia-execution-protocol.mdc`.

## 1. O que foi implementado

Continuidade efêmera e governada de uma interação DÉLIA diante de timeout
recuperável de estágio de modelo — **sem persistência, sem fila, sem
scheduler, sem worker persistente, sem nova engine**.

O usuário pergunta uma única vez. Quando um estágio de modelo falha por
`model_timeout` ou `turn_budget_exhausted`, a fronteira de `attempt()` pode
iniciar **uma** segunda tentativa governada na mesma interação (mesmo
worker NDJSON, mesmo `correlation_id`, mesmo sink de atividade), dentro de
um único orçamento monotônico.

### Mecanismo — replay de propostas tipadas (Option B refinada)

Em vez de reentrar `_attempt` "no meio", cada tentativa reexecuta a cadeia
determinística completa e as **propostas de modelo já concluídas são
repetidas de graça** a partir de um checkpoint interno:

- `_AttemptCheckpoint` (novo, `orchestration.py`): dataclass interno
  request-scoped, transportado por ContextVar `_RESUME_STATE` (mesmo
  padrão do `_ACTIVITY_SINK` — estado por interação nunca vive em `self`).
  Contém somente:
  - `proposals`: `sha256(instruction_id, input_text, block_tag,
    block_payload)` → proposta tipada crua que sobreviveu ao estágio;
  - `invoke_outcomes`: `sha256(group_id, remote_name, canonical_args)` →
    `SpecialistOutcome` de invocação **não-mutante** que provou completar;
  - `mutating_invoke_started`: frontier flag.
- `_model_stage_proposal`: após o `deadline.check` obrigatório, consulta o
  checkpoint. Hit = retorna a proposta registrada (`decision=resumed` no
  log). Miss = executa o modelo normalmente e registra a saída tipada.
  **Nada** muda na validação: a proposta reexecutada passa por todas as
  portas determinísticas (`_propose`, seleção contra superfície viva,
  validação de argumentos contra schema fresco) — dado, nunca autoridade.
- `_invoke` (única seam de dispatch): resolve a capability a partir do
  grupo **fresco** re-listado; se a classe não é allowlisted
  (`_RESUMABLE_OPERATION_CLASSES` = DISCOVERY|READ|ANALYSIS — PREPARE/ACT
  e qualquer classe desconhecida caem fechado no material) marca
  `mutating_invoke_started` e prossegue uma única vez; se é não-mutante e
  a fingerprint bate, retorna o outcome registrado sem re-emitir eventos
  falsos. Outcomes não-mutantes são registrados **antes** do
  `deadline.check` pós-invoke — uma deadline tardia não transforma um READ
  concluído em READ duplicado.
- `attempt()`: loop bounded (máx `self._max_governed_attempts`, teto duro
  `MAX_GOVERNED_ATTEMPTS=2`). Em cada falha de deadline-class
  (`_StageDeadlineExceeded`/`TurnBudgetExhausted`), re-tenta somente se:
  checkpoint existe (feature ligada, turno não-confirmação), tentativas
  restantes > 0, **nenhum** invoke mutante já começou, `cancel_check()`
  não sinalizou, e `min(30s, orçamento_restante) >= MIN_VIABLE(2s)`.
  A nova tentativa recebe `TurnDeadline` fresco com teto
  `GOVERNED_ATTEMPT_MAX_SECONDS=30` sobre o restante do orçamento de
  interação — o relógio **nunca reinicia**.

### Orçamento aprovado (22/10/2026) → constantes de código

```text
MAX_GOVERNED_ATTEMPTS=2                    (hard cap no construtor)
GOVERNED_ATTEMPT_MAX_SECONDS=30.0          (teto por tentativa — nunca configurável acima)
DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS=60.0
DELIA_MAX_GOVERNED_ATTEMPTS                (env; default 1 = legacy OFF; clamp 1..2)
DELIA_INTERACTION_TOTAL_BUDGET_SECONDS     (env; default 60)
```

`DELIA_TURN_BUDGET_SECONDS` continua sendo o orçamento da **primeira**
tentativa (30s) — semântica existente preservada.

### Cancelamento (G2)

`_stream_interaction_turn` cria `threading.Event` `disconnect` por
request: `GeneratorExit`/close do gerador → `disconnect.set()` →
`handler.execute(cancel_check=disconnect.is_set)` → a fronteira recusa
qualquer nova tentativa. Fechar a stream **não** mata o worker — ele
termina bounded pelo deadline e seu terminal é descartado. Terminal
único garantido pela fila existente (inalterado).

### Experiência

Novo `ActivityPhase.CONTINUING` (estado `RUNNING`, intermediário — fora
de `_TERMINAL_ACTIVITY_PHASES`): emitido **somente** quando uma segunda
tentativa realmente inicia — fronteira observada, nunca promessa. MFE:
fase adicionada ao vocabulário aceito + labels
"Continuando a consulta" / "Continuando sua consulta…" — MFEs antigos
descartam a fase desconhecida sem efeito (parse tolerante comprovado).

### Habilitação

- `infra/docker-compose.dev.yml`: `DELIA_MAX_GOVERNED_ATTEMPTS:-2` —
  dev é o ambiente autorizado pós-gates.
- `infra/docker-compose.yml` (prod/base): `:-1` — **OFF por default**;
  produção não é ativada automaticamente.
- `gateway/nginx.dev.conf`: `proxy_read_timeout 120s` na location
  delia-api — margem defensiva (o timeout é por-gap; eventos fluem
  continuamente). Produção (`proxy_read_timeout 86400`) inalterada.

## 2. Gates

**G1 Transporte (PASS):** gunicorn roda `--threads 4` (gthread — o
heartbeat do worker process não morre com request longo; `--timeout 60`
aplica-se ao loop de aceitação, não à request em voo). Nginx
`proxy_read_timeout` é timeout de inatividade entre reads — eventos
NDJSON fluem continuamente durante os ≤60s, então dev (60s default) já
cobria; o `120s` dev é margem defensiva. Cloudflare ~100s é o teto
externo real; 60s de interação + terminal entregue com folga. Frontend
aceita fase desconhecida sem falhar.

**G2 Cancelamento (PASS):** `disconnect` Event + `cancel_check` na
fronteira — nenhuma tentativa nova após disconnect; nenhuma operação
modelo/provider inicia após cancelamento (a tentativa em voo termina
bounded e é descartada); terminal único por construção.

**G3 Autoridade e efeitos (PASS):** propostas reexecutadas são dados,
não autoridade — revalidação determinística contra superfície viva
fresca em cada tentativa (capability ausente/schema mudado → terminal
honesto, provado por teste); `_invoke` resolve do grupo fresco, AuthZ
de owner/domain roda dentro do invoke (revogação → AUTHZ_DENIED real);
frontier material fail-closed (`mutating_invoke_started` → nenhuma
nova tentativa; PREPARE/ACT executa no máximo uma vez; turnos de
confirmação nunca fazem checkpoint/resume). `READ != PREPARE != ACT`
preservado; classificação `PROCESSING_TIMEOUT` vs `SOURCE_UNAVAILABLE`
preservada.

**G4 Checkpoint tipado (PASS):** reusa orchestrator, `TurnDeadline`,
`ActivityEvent`, sink e worker NDJSON existentes. `_AttemptCheckpoint`
é o estado interno mínimo (EXISTING_EQUIVALENT=NO comprovado no CP3 —
todos os resultados morriam no raise). Preserva somente propostas
tipadas e outcomes não-mutantes fingerprinted; nunca CoT, tokens,
secrets, permissões presumidas ou payload MCP cru. Revalidação no
resume via fingerprint byte-idêntica + portas determinísticas frescas.

## 3. Testes

`tests/test_governed_stage_resume.py` — 14 testes, todos PASS:

- **Obrigatório (CP4 §8):** arguments `model_timeout` → checkpoint →
  2ª tentativa → `interactions_admission`/`group_selection`/
  `capability_selection` contados **1× cada** (replayed), arguments
  **2×**, READ `analyze` executado **1×**, SUCCESS, um resultado.
- **Negativos:** timeout na 1ª e na 2ª (PROCESSING_TIMEOUT, args=2×);
  orçamento total esgotado (59s consumidos → sem 2ª tentativa);
  `cancel_check` → sem 2ª tentativa; outcome READ concluído → replay
  (provider chamado 1× mesmo com retry); frontier PREPARE →
  `prepare_change` executado 1× e nunca reexecutado; capability some
  entre tentativas → revalidação fresca, sem invoke; AuthZ revogada na
  2ª tentativa → AUTHZ_DENIED real; falha real MCP →
  SOURCE_UNAVAILABLE sem resume; modo legado (attempts=1) inalterado;
  CRI ON/OFF (parametrizado); turno de confirmação nunca resume.
- **CONTINUING:** exatamente 1 evento quando a 2ª tentativa inicia.

**Regressão backend:** suíte completa `delia-api/tests/` PASS
(incluindo `test_activity_streaming.py` e `test_interaction_runtime.py`
— stubs atualizados para o novo kwarg `cancel_check` do contrato
`execute`).
**Frontend:** `tsc` limpo + 303 testes PASS.

## 4. Avaliação real (dev, container delpi-delia-api)

Script `scripts/cp4_governed_resume_eval.py` com o handler real
composto (adapter LLM real + providers MCP reais) e adapter contador:

```text
A) resume ON, timeout normal (30s):  3 chamadas de modelo, 0 CONTINUING, COMPLETED.
B) resume ON, stage cap 3s:          select_group=2×, admission=1× (replay),
                                   CONTINUING=1, COMPLETED — o LLM real
                                   estourou 3s em select_group na 1ª
                                   tentativa e a 2ª reexecutou SÓ esse
                                   estágio; admission replayed.
   log: governed_resume decision=continue attempt=2 remaining_ms=55710
   log: model_propose decision=resumed purpose=interaction_admission
B') rodada em que a 2ª também estourou: BLOCKED honesto,
   "processamento demorou além do limite", sem 3ª tentativa.
C) resume OFF (legacy) + cap 3s:     select_group=1×, 0 CONTINUING.
```

`REAL_MODEL_EVALUATION=PASS`. `REAL_MCP_EVALUATION=TEST_NOT_RUN` —
invoke com bearer delegado exige credenciais de usuário dev
(`DEV_PORTAL_*` não provisionadas nesta máquina); o surface-list real
do interop rodou durante as tentativas e a fronteira provider-side é
coberta deterministicamente pela suíte.

## 5. Limites honestos

- Refresh/fechamento/restart perdem a execução — aceito nesta fase.
- A 2ª tentativa re-lista a superfície viva (tools/list) — necessário
  para revalidação fresca; não é "repetição indevida" (é nova
  autoridade de superfície), mas tem custo de rede real.
- Entre tentativas pode haver uma lacuna de segundos sem eventos novos
  — o evento CONTINUING marca o início da nova tentativa.
- `mutating_invoke_started` marca mesmo quando o invoke mutante falha
  depois (mais conservador que o necessário — safe side).
- "Resposta atrasada da tentativa anterior": impossível por construção
  — tentativas são sequenciais no mesmo worker; não há execução
  concorrente. Documentado, sem teste aplicável.
- Terminal duplo: impossível por construção (o loop retorna uma vez; a
  fila tem um slot de terminal). Suíte de streaming cobre unicidade.

## 6. Arquivos

```text
delia-api/app/application/capability_provision/orchestration.py
delia-api/app/application/interaction/activity.py
delia-api/app/application/interaction/handle_interactive_turn.py
delia-api/app/interfaces/http/interaction_routes.py
delia-api/app/infrastructure/config/settings.py
delia-api/app/composition/root_composer.py
delia-api/tests/test_governed_stage_resume.py        (novo)
delia-api/tests/test_activity_streaming.py           (kwarg)
delia-api/tests/test_interaction_runtime.py          (kwarg)
delia-api/scripts/cp4_governed_resume_eval.py        (novo)
infra/docker-compose.yml          (env defaults OFF)
infra/docker-compose.dev.yml      (env dev ON)
gateway/nginx.dev.conf            (margem defensiva dev)
plugins/delia/src/api/interactionClient.ts
plugins/delia/src/activity/activityView.ts
```

## 7. Veredicto

`ACCEPT` — aceite do task atendido: uma pergunta, no máximo duas
tentativas, até 60s totais, máx 30s por tentativa, retomada no estágio
falho, sem reexecução de ações materiais, sem persistência, sem
repetição manual. Produção **OFF** por default — ativação de prod é
decisão separada de coordenação.

`NEXT_COORDINATION_DECISION:` avaliar ativação prod
(`DELIA_MAX_GOVERNED_ATTEMPTS=2`) somente após observar dev; aprovar ou
manter OFF. Residual material: nenhum bloqueante; latência de modelo
permanece a causa-raiz subjacente (CP4 mitiga, não elimina).
