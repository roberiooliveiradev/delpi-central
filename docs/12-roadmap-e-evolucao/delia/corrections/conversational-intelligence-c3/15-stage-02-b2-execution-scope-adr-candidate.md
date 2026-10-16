# 15 — ADR candidata: execution scope, ACT eligibility e comandos tipados (B2)

**TASK:** `DELIA-C3-STAGE-02-B2-EXECUTION-SCOPE-ADR-CONTRACT-01`
**DATA:** 2026-10-16
**BASE_HEAD:** `7234a3ccf03e43196894932cd11fd392b996fe8a` (origin/main, fast-forward verificado)
**MODE:** `ARCHITECTURE_AND_CONTRACT_DESIGN_ONLY` — zero alteração de runtime, contratos produtivos, APIs, frontend, prompts ou policies.
**STATUS:** `ADR_CANDIDATE / NOT_APPROVED`. `PRODUCT_PRINCIPLE=APPROVED` (§6.179); `TECHNICAL_CONTRACT=NOT_APPROVED` (§6.180). Este documento **estende e formaliza** a proposta preliminar do relatório [14](./14-execution-scope-contract-security-review.md), que permanece referência de design, não decisão congelada. D1/D2/D3 requerem decisão expressa do Product Master.

## 1. Contexto

B2 está provado por diagnóstico isolado ([11](./11-stage-02r2-execution-bound-diagnosis.md), §6.177): a elegibilidade de ACT no caminho direto governado depende exclusivamente de `execution_bound`, um campo da proposta do LLM. Quando o modelo retorna `unrestricted` — errado, ausente (coagido) ou inválido (coagido) — sobre texto explícito "não aplique", o runtime pode alcançar ACT com `max_execution_stage=None` + owner `explicit_user_confirmation=false`. 10 casos `xfail(strict)` documentam a violação; 6 controles passam.

Decisão de produto já aprovada ([13](./13-product-principle-intent-and-act-scope.md), §6.179): autonomia governada preservada, ACT direto permitido quando legitimamente autorizado, sem confirmação universal — mas o pedido limitado a PREPARE não pode virar ACT por erro do LLM.

## 2. Problema (reafirmado como questão de contrato)

Não existe hoje, no contrato do turno, **evidência independente e verificável do escopo de execução declarado pelo usuário**. Os únicos sinais de escopo são:

1. `max_execution_stage` — reduction-only, client-declared, correto mas binário e nunca populado pelo MFE atual (PROVEN: nenhum uso em `plugins/`).
2. `_TurnGoal.execution_bound` — hipótese do LLM, fail-open para `unrestricted` (PROVEN, §6.177).
3. `confirmation` — decisão sobre proposta já preparada; não recebe nem interpreta o texto do turno (PROVEN: branch em `orchestration.py` antes de `_understand_goal`; `_attempt_confirmation` sem parâmetro `input_text`).

O LLM é, portanto, **ponto único de falha** para liberar ACT a partir de texto livre. A pergunta arquitetural: qual contrato mínimo fornece `ACT_ELIGIBILITY` com origem distinta da interpretação do modelo, sem confirmação universal e sem segundo gate semântico?

## 3. Autoridades

Precedência verificada: Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → specs 60/69/70 → personality/02 → ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.180 → relatórios 11/12/13/14 desta pasta. Regras materiais: `delia-execution-protocol.mdc`, `platform-security-identity-authorization.mdc`, `platform-api-contracts-integration.mdc`, `contract-evolution-backward-compatibility.mdc`, `ai-external-tools-security.mdc`, `platform-quality-testing.mdc`.

## 4. Evidência (fatores do runtime — PROVEN por leitura de código)

| Item | Fato |
| --- | --- |
| Wire request | `POST /interaction/turns`, body allowlist estrita `{input, context, confirmation, workspace, max_execution_stage}`; chaves extras → 400 (`interaction_routes.py` `ALLOWED_BODY_KEYS`) |
| `confirmation` wire | allowlist `{decision, proposal_digest, preview_fingerprint, session_id}`; digests não-reversíveis; handle owner nunca exposto |
| `max_execution_stage` | `_parse_execution_ceiling` aceita apenas `"prepare"`; vocabulário de escalada rejeitado na fronteira sintática; `_validate_execution_ceiling` reaplica na application layer |
| `InteractiveTurnRequest` | `access_context` vem de `g.platform_access` (Core), nunca do body; `input_text`/`prior_turns`/`workspace`/`confirmation` são untrusted |
| Frontend | `plugins/delia/src/App.tsx` `sendTurn(value, confirmation)`; `handleConfirmation` envia label fixa PT (`"Confirmação da operação solicitada."` / `"Cancelamento da operação solicitada."`) como `input` + payload estruturado — **payload misto legado existente (C8)** |
| Orquestração | `confirmation is not None` → `_attempt_confirmation` **antes** de `_understand_goal`; texto do turno nunca interpretado nesse caminho; binding actor/session/digest/fingerprint/`PendingWrite` + live gates |
| Escopo efetivo | `prepare_only = max_execution_stage == "prepare" or goal.execution_bound == "prepare_only"`; reduction-only; compõe com ceiling |
| Consumers | `/interaction/turns`: `plugins/delia` (interactionClient + demoMode) + scripts/tests `delia-api` (evals). Consumers não-MFE/automação: `TO_INVENTORY` |

## 5. Invariantes do contrato candidato

1. Ausência de escopo positivo **nunca** converte em autorização de ACT (`NOT_ASSERTED` ≠ `ACT_ELIGIBLE`).
2. `PREPARE_ONLY` prevalece sobre qualquer sinal mais permissivo — composição "most restrictive wins".
3. Nenhuma saída de modelo amplia escopo: `execution_bound` pode **somente reduzir**.
4. Nenhum owner/capability/metadata amplia escopo; `explicit_user_confirmation=false` dispensa confirmação **adicional**, não evidência de escopo.
5. Escopo é bound do turno/comando, não grant: Core RBAC/Domain/Policy/Decision permanecem autoridade.
6. Escopo é não-reutilizável: vinculado ao turno (MESSAGE) ou à proposta (decisão tipada); stale/replay/contraditório falha fechado.
7. Caminho direto legítimo preservado: `ACT_ELIGIBLE` + todos os gates + owner `false` → ACT sem confirmação adicional.
8. Cliente é transporte de escolha do usuário, nunca autoridade: um `ACT_ELIGIBLE` forjado concede nada além de elegibilidade, e todo o restante do pipeline decide.

## 6. Inventário — RESPONSIBILITY→OWNER→SOURCE→CONSUMERS→CONTRACT→TRUST→IMPL→TEST

| Mecanismo | Resp / Owner | Source | Consumers | Trust boundary | Evidência |
| --- | --- | --- | --- | --- | --- |
| `InteractiveTurnRequest` | contrato do turno / DÉLIA Application | `contracts.py:34` | `HandleInteractiveTurn` | montado na borda HTTP; `access_context` ≠ body | `test_interaction_runtime*` |
| `max_execution_stage` | teto reduction-only / DÉLIA | routes `_ALLOWED_EXECUTION_CEILINGS` | `_attempt` | reduction-only, escalada rejeitada | `test_execution_ceiling_turn_budget.py` |
| `_TurnGoal`/`_understand_goal` | interpretação semântica / DÉLIA | `orchestration.py` | gate de seleção, ceiling | **HYPOTHESIS**, fail-open em `unrestricted` | 10 xfail (§6.177) |
| `confirmation`/`_attempt_confirmation` | decisão sobre proposta / DÉLIA | routes `CONFIRMATION_KEYS` | `PendingWrite` backend | digests+session+actor+fingerprint+TTL; sem `input_text` | baseline confirmation tests |
| `evaluate_write_continuation`/Decision | policy de continuação / DÉLIA | orchestration | prepared ACT | live gates | suíte 1091 |
| `sendTurn`/`handleConfirmation` | UX do turno / MFE DÉLIA | `App.tsx` | interactionClient | transporte; nunca autoridade | `interaction.test.tsx` |
| `submitInteractionTurn` | client HTTP / plugin | `interactionClient.ts` | App/demo | JSON+NDJSON | `interactionClient.ndjson.test.ts` |

## 7. Reuse Gate

| Candidato | EXISTING_EQUIVALENT | REUSE_DECISION |
| --- | --- | --- |
| Comando tipado de turno (MESSAGE vs decisão) | `confirmation` payload já discrimina decisão; ausência de tipo explícito | **EXTEND** — envelope `command` opcional sobre o body existente |
| Evidência de escopo do usuário | `max_execution_stage` (só reduz; sem valor positivo); `execution_bound` (modelo — inelegível como fonte) | **EXTEND** — campo `execution_scope` user-declared |
| Pedido de escopo/decisão ao usuário | `confirmation_request` bounded surface + PendingWrite | **REUSE** — mesma mecânica de decisão pendente |
| Confirmação tipada com binding | `decision`+digests+session+fingerprint+TTL | **REUSE** |
| Fail-closed bound | `_propose` validation + `declared` semantics | **EXTEND** mínima |
| Novo executor/planner/parser/regex | — | **NEW=NOT_AUTHORIZED** |

## 8. Alternativas comparadas (máx. 3)

### ALT-A — Comando tipado + `execution_scope` user-declared (RECOMENDADA)

**Descrição:** estender o body com `command.type ∈ {MESSAGE, CONFIRM_PREPARED, REJECT_PREPARED}` e `execution_scope ∈ {PREPARE_ONLY, ACT_ELIGIBLE}` (opcional; ausente = `NOT_ASSERTED`). `NOT_ASSERTED` limita qualquer seleção write-class a PREPARE; a resposta pede decisão de escopo reusando a superfície de confirmação. `execution_bound` do modelo vira reduction-only.

- **Owner:** DÉLIA Application (contrato); MFE expressa controle; Core/Domain/owner MCP intocados.
- **Contratos alterados:** body `/interaction/turns` (+`command`), `InteractiveTurnRequest` (+`execution_scope`, +command type), `interactionClient`/`App.tsx` (afordância de escopo; label legada deprecada).
- **Consumers:** plugins/delia + scripts/evals delia-api; demais `TO_INVENTORY`.
- **Segurança:** fecha DIAG-01/02/03/07/09 **sem depender de classificação correta do LLM** — sem sinal positivo não há ACT; forjar `ACT_ELIGIBLE` só concede elegibilidade sob todos os gates.
- **Reuse Gate:** EXTEND sobre mecanismos existentes; nenhum componente novo.
- **Complexidade:** média — borda + handler + orquestrador (gate de escopo) + client + migração.
- **§6.140 impacto:** caminho direto passa a exigir `ACT_ELIGIBLE` estruturado → texto livre "crie X" sozinho produz PREPARE+decisão; **mudança de elegibilidade — exige aprovação explícita**.
- **Latência/modelo:** +0 chamadas de modelo.
- **UX:** uma decisão estruturada adicional quando o usuário não declarou escopo; afordância "executar agora" preserva 1-clique para quem declara.
- **Falsos bloqueios:** pedidos de escrita sem escopo viram PREPARE (seguro por construção, fricção aceitável e reversível na conversa).
- **Migração:** clientes legados sem `command` → `NOT_ASSERTED` (safe); labels fixas de confirmação toleradas por allowlist exact-match até deprecação.
- **Rollback:** escopo default `NOT_ASSERTED` já é o comportamento fail-closed; reverter = reintroduzir tratamento de texto → volta o defeito; preferir manter e ajustar UX.
- **Residuais:** usuário declara `ACT_ELIGIBLE` + texto contraditório não detectável → protocolo de conflito (§11.C3/C10); nenhuma garantia absoluta sobre texto arbitrário.

### ALT-B — Somente D3 fail-closed no `execution_bound`

**Descrição:** bound ausente/inválido → não coagir a `unrestricted`; tratar como não-declarado → clarificar/cap PREPARE.
- **Insuficiente isolada:** `unrestricted` positivo porém errado (DIAG-01) permanece FAIL — o LLM continua ponto único de falha para o valor que importa.
- **Valor:** defense-in-depth barata, zero mudança de UX/contrato; recomendada **como componente de A**, nunca como resolução de B2 (exigência explícita §6.178).

### ALT-C — Consentimento vinculado à proposta apenas (sem escopo de turno)

**Descrição:** todo write material → PREPARE + preview + decisão tipada CONFIRM/REJECT; elimina o caminho direto.
- **Segurança:** máxima — elegibilidade de ACT existe somente sobre uma proposta concreta mostrada ao usuário.
- **Custo:** confirmação universal de fato → **contradiz o princípio aprovado** (§6.179: sem confirmação universal; owner-direct preservado). Mantida como fallback caso o Product Master prefira segurança máxima a UX direta.

## 9. Contrato proposto — A. Request (candidato, não wire-congelado)

```jsonc
{
  "input": "string",                       // MESSAGE: texto livre; decisão tipada: omitido/vazio
  "context": [...],                        // inalterado
  "workspace": {...},                      // inalterado
  "max_execution_stage": "prepare",        // inalterado, reduction-only
  "command": {                             // NOVO candidato — opcional
    "type": "MESSAGE | CONFIRM_PREPARED | REJECT_PREPARED",
    "execution_scope": "ACT_ELIGIBLE | PREPARE_ONLY",   // só em MESSAGE
    "confirmation": {                      // só em CONFIRM/REJECT; shape atual
      "decision": "CONFIRM | REJECT",
      "proposal_digest": "...",
      "preview_fingerprint": "...",
      "session_id": "..."
    }
  }
}
```

| Regra candidata | Semântica |
| --- | --- |
| `command` ausente | compat: `type=MESSAGE`, `execution_scope=NOT_ASSERTED`; `confirmation` top-level legado tratado como decisão (período de migração) |
| `execution_scope` ausente | `NOT_ASSERTED` — nunca `ACT_ELIGIBLE` implícito |
| `execution_scope=PREPARE_ONLY` | ≡ `max_execution_stage="prepare"`; ambos presentes → composição mais restritiva; redundância permitida |
| `execution_scope=ACT_ELIGIBLE` | declaração de escopo do usuário **neste turno**; remove apenas o cap `NOT_ASSERTED`; não é grant, não contorna gate, expira com o turno |
| `execution_scope` + `confirmation` no mesmo comando | inválido → `turn_command_conflict` (decisão e escopo são mutuamente exclusivos) |
| valor fora do enum | `execution_scope_invalid` (fail-closed → 400) |
| `confirmation` + `input` não-vazio | legado: exact-match allowlist das labels registradas → tolerado (migração); qualquer outro texto → `confirmation_text_conflict` |
| modelo `execution_bound` | reduction-only: `prepare_only` reduz; `unrestricted`/ausente/inválido → sem efeito sobre elegibilidade |

**Versionamento:** campo aditivo opcional → backward-compatible na borda (clientes antigos = `NOT_ASSERTED`, comportamento fail-closed). Avaliar `contract_version`/`X-DELIA-Contract` se a migração de labels exigir faseamento observável — `TO_DECIDE` na implementação.

## 10. Contrato proposto — B. Response

| Situação | Resposta candidata |
| --- | --- |
| PREPARE com escopo suficiente | preview + `confirmation_request` atual (owner `true`) ou resultado PREPARE (owner `false`, scope presente) |
| Write-class + `NOT_ASSERTED` | PREPARE executado + **decisão de escopo pendente** — reusar `confirmation_request`/presentation bounded surface: o usuário decide aplicar a proposta mostrada (decisão tipada CONFIRM/REJECT). Sem novo tipo persistente na v1; se a UX exigir distinção "scope vs confirm", candidato `pending_decision.kind=execution_scope` — `TO_DESIGN` |
| `ACT_ELIGIBLE` + gates OK + owner `false` | ACT direto + Outcome (caminho §6.140 preservado) |
| `ACT_ELIGIBLE` + owner `true` | PREPARE + `confirmation_request` (owner policy intocada) |
| Comando misto/contraditório | erro `turn_command_conflict` / `confirmation_text_conflict` — nenhuma execução |
| Confirmação válida | ACT + Outcome (inalterado) |
| REJECT | cancelamento da proposta pendente (inalterado) |
| Teto `prepare` excedido | `execution_ceiling` (inalterado) |
| Resultado inconclusivo | status inconclusivo existente — sucesso de ferramenta ≠ Outcome (inalterado) |

Códigos de erro: **candidatos**, nenhum criado em produção nesta task; mapear no contrato canônico de erros antes de implementar.

## 11. Contrato proposto — C. State transitions

```text
OBSERVE   request autenticado; ceiling/escopo normalizado na borda (fail-closed)
   │      [CONFIRM/REJECT tipado → DECIDE sobre proposta, sem interpretar texto]
   ▼
INTERPRET orquestrador: goal/seleção/argumentos — saídas = HYPOTHESIS
   ▼
PREPARE   capability PREPARE invocada se gates de intenção/política passarem
   ▼
DECIDE    escopo efetivo = min(user_scope, ceiling, model_bound_redução)
          NOT_ASSERTED → aguardar decisão tipada | PREPARE_ONLY → fim seguro
          | ACT_ELIGIBLE → owner policy: true → confirmation_request;
          false → continuação direta
   ▼
ACT       live capability + Core/Domain/Policy/Decision + idempotência
   ▼
VERIFY    owner Outcome / source authoritative; inconclusivo em falha
```

Nenhum estado persistente novo: `PendingWrite` já persiste proposta aguardando decisão — a "decisão de escopo" é a **mesma** estrutura (a proposta preparada é a coisa confirmada).

## 12. Contrato proposto — D. Security contract

- **Trust boundary:** `command`/`execution_scope`/`input`/`confirmation` são input autenticado porém untrusted; `access_context` vem do Core, nunca do body.
- **Identity/AuthZ:** identidade Keycloak→`g.platform_access`; escopo positivo é intenção, não permissão; Core/Domain AuthZ permanece gate posterior.
- **Scoped intent evidence:** `ACT_ELIGIBLE` válido somente no turno recebido; não persiste, não herda, não transfere para outra proposta (`SESSION_STICKY` rejeitado por default).
- **Confirmação:** binding existente (actor/session/digest/fingerprint/TTL/PendingWrite/live revalidation) inalterado; decisão tipada é o único caminho de CONFIRM — modelo/cliente não fabricam binding válido (C9: digests inválidos → rejeição).
- **Idempotência/audit/postcondition:** inalterados; decisões de escopo auditáveis.

## 13. Contrato proposto — E. Compatibility / migração

| Consumer | Impacto | Estratégia |
| --- | --- | --- |
| `plugins/delia` App.tsx | `handleConfirmation` passa a enviar comando tipado sem label; `sendTurn` ganha afordância de escopo | faseada: servidor tolera labels exatas (allowlist) durante janela de migração; client publicado primeiro compatível com ambos |
| `interactionClient.ts` | +`command` opcional | aditivo |
| scripts/evals delia-api | passam a declarar `execution_scope` nos cenários de write | atualização de fixtures na task de implementação |
| clientes não-MFE/automação (custom-gpt façade etc.) | `TO_INVENTORY` | comportamento seguro por default: sem `command` → `NOT_ASSERTED` → PREPARE+decisão; nenhum cliente quebra em erro — apenas ganha o passo de decisão |
| OpenAPI/contrato externo | campo aditivo opcional | `contract-evolution-backward-compatibility.mdc` |

## 14. Contrato proposto — F. Observability

Registrar por turno: `command.type`, `execution_scope` efetivo e origem (`client_declared|default`), `model_bound` proposto (para medir divergência LLM×usuário), decisão de gate (`scope_cap_applied`, `direct_act_eligible`), correlation/request_id. **Nunca** logar texto livre integral, digests brutos além de prefixo, tokens, handles ou secrets. Métrica candidata: taxa de `scope_cap_applied` e divergência bound-modelo×escopo-usuário (sinal de misclassification sem depender de labels humanos).

## 15. Contrato proposto — G. Failure and rollback

| Falha | Comportamento |
| --- | --- |
| Modelo indisponível/timeout | erro existente; sem interpretação → nenhuma elegibilidade derivada |
| Escopo ausente | `NOT_ASSERTED` → cap PREPARE |
| Escopo inválido | 400 `execution_scope_invalid` |
| `ACT_ELIGIBLE` + texto contraditório detectado (modelo propõe `prepare_only`) | conflito → resposta de clarificação/`execution_scope_conflict` — **nunca** execução silenciosa em qualquer direção |
| Confirmação contraditória/mista | `confirmation_text_conflict`/`turn_command_conflict` |
| Proposta expirada/stale/digest divergente/replay | rejeição existente |
| Permissão revogada/Core indisponível | gate existente bloqueia |
| Owner/capability reclassificada | live `tools/list` + `operation_class` — sem cache de elegibilidade |
| Rollback da feature | desligar elegibilidade `ACT_ELIGIBLE` (policy/fase existente, **não** flag ad hoc) → tudo cai para `NOT_ASSERTED` = comportamento seguro máximo |

## 16. Matriz de cenários de confirmação (C1–C10)

| # | Cenário | Esperado candidato | Erro candidato | Segurança |
| --- | --- | --- | --- | --- |
| C1 | CONFIRM válido p/ proposta pendente | ACT + Outcome | — | binding completo |
| C2 | REJECT válido | proposta cancelada | — | nunca executa |
| C3 | CONFIRM + texto "não aplique" | rejeição do turno | `confirmation_text_conflict` | texto fora da allowlist + confirmation → conflito; nenhum ACT |
| C4 | CONFIRM + proposta expirada | rejeição | existente (stale) | inalterado |
| C5 | CONFIRM + proposta de outro usuário | rejeição | existente (actor binding) | inalterado |
| C6 | CONFIRM + fingerprint divergente | rejeição | existente | inalterado |
| C7 | CONFIRM duplicado | rejeição/idempotente | existente | inalterado |
| C8 | cliente legado: label fixa + confirmation | tolerado na migração (exact-match allowlist) → mesmo resultado de C1/C2 | — | label nunca interpretada como instrução; deprecação planejada |
| C9 | modelo/cliente fabrica payload de confirmação | rejeição | existente (binding falha) | digests não batem com PendingWrite |
| C10 | `max_execution_stage=prepare` + CONFIRM | rejeição | `execution_ceiling` | ceiling domina decisão |

## 17. Segurança — avaliação contra os critérios §13 do task

- DIAG-01/02/03/07/09 → **PASS de segurança sob ALT-A sem exigir LLM correto**: sem `execution_scope` declarado, `NOT_ASSERTED` capa qualquer write em PREPARE; `unrestricted`/ausente/inválido do modelo não afeta elegibilidade.
- Owner direct (`explicit_user_confirmation=false`) não substitui escopo: `ACT_ELIGIBLE` e policy são condições independentes e conjuntivas.
- `PREPARE_ONLY` (usuário, ceiling ou bound do modelo) bloqueia ACT em toda continuação — composição mais restritiva.
- ACT legítimo preservado: `execution_scope=ACT_ELIGIBLE` + owner `false` + gates → direto; owner `true` → confirm vinculado.
- CONFIRM contraditório → conflito, nunca execução silenciosa; REJECT nunca executa.
- Model output/metadata MCP/rename não alteram escopo ou permissão — escopo só vem do comando tipado do cliente autenticado.
- **LLM continua ponto único de falha?** Não para autorização: o modelo pode bloquear (falso `prepare_only` → fricção de clarificação, fail-safe) mas não liberar. Residual honesto: o modelo permanece na cadeia de qualidade (intenção/argumentos), não de autoridade de escopo.

## 18. Evals planejadas (não implementar nesta task)

Reusar `test_stage02r2_execution_bound_diagnosis.py`: os 10 xfail devem virar **PASS de segurança** (sem scriptar `prepare_only` no modelo); os 6 controles permanecem. Novos casos exigidos: `ACT_ELIGIBLE`+owner false → ACT (controle positivo do caminho direto); `ACT_ELIGIBLE`+modelo `prepare_only` → conflito; comando misto → `turn_command_conflict`; label legada → tolerância; label arbitrária → conflito; `ACT_ELIGIBLE` forjado sem gates → bloqueado; stale/replay/revogação/rename/provider-neutrality; holdout de formulações (novas frases "não aplique" não treinadas); latência +0 model calls comprovada.

## 19. Trade-offs declarados

1. **Fricção:** pedidos de escrita por texto livre sem escopo ganham um passo de decisão — custo deliberado e aprovado em princípio (§6.179 exige evidência além do texto).
2. **§6.140:** a continuação direta deixa de ser alcançável por texto livre puro; elegível apenas com `ACT_ELIGIBLE` estruturado → **mudança de contrato comportamental, não de política owner**.
3. **Garantia absoluta impossível:** `ACT_ELIGIBLE` explícito + texto contraditório que nenhum mecanismo detecte não é eliminável sem consentimento vinculado à proposta (ALT-C); proposto protocolo de conflito quando detectável + documentação do residual.
4. **UX de escopo:** a afordância que produz `ACT_ELIGIBLE` precisa ser honesta (ação do usuário, não default) — `TO_DESIGN` com specs 69/70/personality.

## 20. Decisões solicitadas (D1/D2/D3)

| Decisão | Recomendação | Pergunta ao Product Master |
| --- | --- | --- |
| **D1** fonte de ACT eligibility | `execution_scope` user-declared tipado (ALT-A); `NOT_ASSERTED` capa writes em PREPARE | Aprovar que texto livre de escrita deixa de executar direto sem sinal estruturado? |
| **D2** precedência CONFIRM | comandos tipados mutuamente exclusivos; `input` em turno de decisão deve ser vazio ou label allowlist; demais → conflito | Aprovar migração do client legado e a regra de conflito? |
| **D3** bound ausente/inválido | aprovar como camada defense-in-depth de A | Aprovar como parte do mesmo bounded implementation? |

## 21. Consequências arquiteturais

- `execution_bound` do modelo rebaixado a reduction-only → `unrestricted` deixa de ter efeito; semanticamente correto (hipótese não é autoridade).
- Nenhum componente/estado persistente novo; nenhuma autoridade realocada; owner policy §6.140 preservada em valor, alterada em **elegibilidade de ativação**.
- `command` introduz distinção formal mensagem×decisão que já existia implicitamente — reduz superfície ambígua.

## 22. Riscos residuais

- Texto contraditório com `ACT_ELIGIBLE` explícito e modelo cego → executa (documentado; mitigável por ALT-C se exigido).
- Labels legadas fora da allowlist em clients desatualizados → `confirmation_text_conflict` até atualização (fail-safe, não fail-open).
- Consumers não-MFE desconhecidos (`TO_INVENTORY`) podem observar novo passo de decisão — comportamento seguro, não erro.
- Medição real (modelo verdadeiro, latência) permanece `TEST_NOT_RUN`.

## 23. Review gate final (auto-verificação)

- Resolve B2 provado? **Sim** — elegibilidade de ACT passa a exigir sinal fora do LLM.
- LLM como ponto único de falha para liberar ACT? **Não** — modelo só reduz.
- Autonomia governada preservada? **Sim** — `ACT_ELIGIBLE`+owner false → direto.
- Confirmação universal? **Não** — decisão só quando escopo não declarado.
- Altera §6.140 silenciosamente? **Não** — mudança de elegibilidade é declarada e condicionada à aprovação.
- Dependência nova do frontend? **Não** — client é transporte; backend valida e o default é seguro sem ele.
- Componente duplicado? **Não** — REUSE/EXTEND apenas.
- Autoridade paralela? **Não**.
- Testes demonstráveis? **Sim** (§18).
- Marcado como não aprovado? **Sim** — `ADR_CANDIDATE / NOT_APPROVED`.

## 24. Próxima task bounded proposta

`DELIA-C3-STAGE-02-B2-EXECUTION-SCOPE-IMPLEMENTATION-01` — **somente após aprovação de D1/D2/D3**: RED tests primeiro (converter os 10 xfail em expectativas de segurança + novos casos §18), EXTEND contrato request/handler/orquestrador, fixtures de escopo, full suite + suíte DÉLIA, revisão independente. Etapa 03 permanece `NOT_AUTHORIZED`.

---

`PRODUCT_PRINCIPLE=APPROVED`; `ADR_CANDIDATE=SUBMITTED`; `D1_SCOPE_CONTRACT=DECISION_REQUESTED`; `D2_CONFIRM_PRECEDENCE=DECISION_REQUESTED`; `D3_FAIL_CLOSED_LAYER=DECISION_REQUESTED`
`B1=PASS_STRUCTURAL`; `B2=REWORK`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`
`NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`

**Nenhum código, teste, API, UI, prompt, policy, contrato produtivo ou fase foi alterado por esta ADR candidata.**
