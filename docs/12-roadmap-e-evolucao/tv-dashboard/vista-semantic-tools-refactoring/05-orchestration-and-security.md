# 05 — Orchestration and Security

## 1. Ciclo de write canônico (hoje)

```text
READ CURRENT STATE (tools READ ou contexto do host)
 → PREPARE  (prepare_change / gpt_preview_change)
      mint proposal_handle (opaco, HMAC, actor-bound, single-use, TTL)
      preview com IDs sintéticos + plano topo-sort + risk/confirmation
 → CONFIRM WHEN REQUIRED (confirmationPolicy=confirm ⇒ confirmation=true)
 → COMMIT   (commit_proposal / gpt_commit_change; ou commit_now Actions)
      ACT binding IDs reais, per-op authz re-check, boundary único
 → AUTHORITATIVE READ-BACK → VERIFIED | OUTCOME_NOT_VERIFIED | PARTIAL_COMMIT
```

O backend executa o fluxo completo sem interação humana quando a
política é `direct` (commit_now prova isso no Actions). A única
interação obrigatória hoje é `confirmation=true` para os 3 ops
`confirm` — **declarada pelo modelo, não provada pelo humano**.

## 2. Operações compostas — Casos A–E

### Caso A: criar playlist + adicionar slides + configurar apresentação
- **Suporte hoje: COMPLETO.**
  `ops=[create_playlist as playlist, add_slide..., upsert_section...,
  patch_native_config...]` num único prepare; PlanCompiler resolve
  `playlist_ref` para ID real no ACT; commit aplica na ordem.
  Prova: `add_slide`/`add_slide_from_preset` consomem `playlist`
  produzido por `create_playlist`; `patch_native_config` consome
  `playlist`.
- Ordenação/dependência: topo-sort por produces/consumes; plano
  insatisfatório → `DEPENDENCY_UNSATISFIABLE`.
- Confirmação: nenhuma op desse plano é `confirm` → direto.
- **Limitação**: 1 proposal = 1 commit = "atomicidade de aplicação"
  depende do patch service (sequencial, sem rollback transversal —
  PARTIAL_COMMIT é honestamente reportado se falhar no meio).

### Caso B: localizar apresentação → identificar slide → atualizar conteúdo
- **Suporte hoje: COMPLETO.**
  `list_playlists`/`get_playlist_context` (descobrir) → `suggest_change`
  (materializar ops a partir de intenção NL, com `target` resolvido)
  ou ops diretas → prepare → commit.
- `suggest_change` produz ops prontas com refs corretos; exige
  `playlist_id` e opcionalmente `selected_slide_id`.
- **Limitação**: `get_playlist_context` pode ser pesada
  (`include_blocks=true` bounded); sem `search_playlists` por título.

### Caso C: consultar indicadores → analisar → criar apresentação com resumo
- **Suporte hoje: PARCIAL — gap é de análise, não de dados.**
  - `search_data_routes` → `preview_data_block`/`preview_data_model`
    **executam a rota real** — `TvDataPreviewService.preview_block`
    delega a `SlideDataResolutionService`, o mesmo pipeline do player
    (`tv_data_preview_service.py:44`, com `authorization`,
    `force_refresh` e defaults de playlist propagados).
  - Logo a VISTA *vê* os dados; o que falta é a camada de
    **análise/síntese homologada** (agregações, KPIs, insight
    rotulado FACT/CALCULATION/RECOMMENDATION estilo SURI `analyze`).
  - Montar a apresentação com o resumo: `upsert_block` com
    dataBinding — coberto pelos typed ops.
  - `GET /data/validate-config` e `POST /m/*` existem no REST mas não
    são tools (TO_INVENTORY se exposição é desejável).
- **Classificação**: `EXECUTION_GAP` parcial — execução de rota
  existe; falta `analyze` de insights. Se desejado na fase 2, é nova
  capability homologada sobre o preview existente, não novo acesso
  a dados.

### Caso D: reorganizar vários slides preservando consistência
- **Suporte hoje: COMPLETO.**
  `reorder_slides` + `move_slide_to_section` + `upsert_section`
  num só plano; commit único preserva integridade da playlist
  (mesma mutation, mesma revision).
- Multi-slide recovery/mixed writes já provado nos tasks 025-029 do
  editor; o patch aplica ops na ordem compilada.

### Caso E: solicitar exclusão → confirmar → executar
- **Suporte hoje: COMPLETO mas confirmação fraca.**
  - `delete_block`/`delete_section`/`delete_slide` = `confirm`.
  - Fluxo: PREPARE (preview mostra risco+required_confirmation) →
    host pede ao usuário → COMMIT com `confirmation=true` +
    proposal_handle + idempotency_key.
  - **Garantia atual**: o `true` é *afirmado pelo modelo* — CAIO
    chama isso explicitamente de "not proof". A força atual vem de
    (i) proposal só existe se o prepare foi feito, (ii) preview já
    mostrou o impacto, (iii) AuthZ no commit. EVA é mais forte:
    elicitation com `target_echo` prova que *um humano* digitou o
    alvo.
  - **`delete_data_model` é `direct`** — deleção sem confirmação
    além do envelope de proposta. Inconsistente com a política de
    delete (ver gap G-02): classificar como `CONTRACT_DRIFT`
    candidato para revisão do owner.

## 3. Falhas, concorrência, idempotência, retry

- **Idempotência**: `Idempotency-Key` header ou body no
  `commit_proposal`/`gpt_commit_change` + proposal single-use →
  replay seguro: handle já usado ⇒ `PROPOSAL_NOT_FOUND` honesto.
- **Partial failure**: ops executam em sequência; falha em op i ⇒
  `PARTIAL_COMMIT` + `partial_commit` em `outcome.data`, read-back
  dos aplicados; sem rollback compensatório — **não há
  transação/rollback** (documentar como limitação conhecida).
- **Concorrência**: writes passam pelo mesmo `TvPresentationWriteService`
  do editor; conflito com edições humanas simultâneas é tratado pela
  camada de playlist revision (CAS/409 no editor; no GPT path o
  write service aplica a patch no estado atual — **TO_INVENTORY**:
  confirmação se o commit path valida base_revision esperada).
- **Proposal store in-process** (`proposal_store.py`): TTL+single-use
  sob lock — documentado `ACCEPT_WITH_RESIDUAL` para runtime
  single-replica; multi-replica exigiria store persistido (CLARA já
  tem Postgres como referência).
- **Retry de commit**: idempotency_key + single-use cobre retry
  seguro; timeout de network *durante* ACT fica honesto via
  `OUTCOME_NOT_VERIFIED`/read-back do host.

## 4. Autorização e casos negativos (fail-closed)

- Identidade: Keycloak JWT via `delpi_mcp.auth`; permisões no Core;
  `TvAccessService`/`PlaylistAccessService` para resource-level.
- `VISTA capability ≤ authenticated user capability` — catalog
  informa, backend autoriza; capability metadata nunca autoriza.
- Endpoints sem auth: catalog 401 (verificado runtime). Actions
  `require_auth=True` com `Idempotency-Key`.
- Casos negativos mapeados no código:
  - usuário sem permissão → backend 403 (write/read igualmente);
  - escopo/filial errado → resource authorization nega (mesma policy
    do editor);
  - token inválido/expirado → 401 no transporte (`delpi_mcp.auth`);
  - proposal inválido/expirado/outro ator → `PROPOSAL_NOT_FOUND`
    (actor-bound, TTL'd, single-use — replay negado);
  - confirmação ausente em op `confirm` → `CONFIRMATION_REQUIRED`
    (commit_service, `test_gpt_actions_facade.py`);
  - ops fora do catálogo → PlanCompiler/validation rejeita
    (`unknown op`/`UNRESOLVED_OPS`);
  - `commit_now` + `confirmationPolicy=confirm` sem `confirmation`
    → CONFIRMATION_REQUIRED antes do commit;
  - ops vazias → `NO_OPS`;
  - principal_type=service_account em writes humanos → negado
    (governed write exige end-user principal);
  - `builder/sessions`/`openapi sync` → INTERNAL ADMIN;
  - copilot/* → 410.

## 5. Confirmação — comparação honesta

| Mecanismo | VISTA | CAIO | EVA | CLARA |
|---|---|---|---|---|
| Modelo | `confirmation=true` declarado | sealed prepare→commit (claim atômico) | elicitation `target_echo` verificável | sealed + step-up consent portal |
| Prova de humano | ✗ | ~ (commit exige handle mintado por prepare que o usuário viu) | ✓ protocolo | ✓ portal step-up |
| Destrutivas | 3 ops confirm no envelope comum | `delete` tool sealed | flagged ops + flag tier | governed writes dedicados |
| Store | in-process | in-process + lock | aplicação-level | **Postgres** |

**Achado**: VISTA tem o *envelope* certo (prepare honesto +
single-use handle + read-back) mas a *prova de confirmação* mais
fraca do grupo. Migração incremental possível sem mudar a
superfície: exigir `target_echo`/elicitation nos 3 ops confirm.

## 6. Auditoria e observabilidade

- VISTA: trilha via `tv_dashboard` + eval telemetry
  (`test_vista_eval_telemetry.py`, `vista_eval_runner.py`) —
  **TO_INVENTORY**: verificar se commits via MCP/Actions gravam
  trilha comparável à `mcp/clara` de CLARA.
- CLARA (referência): `audit_trail.py` + `mcp/clara` audit records +
  consent challenges persistidos — padrão a emular se fase 2
  endurecer governança.
