# 16 — Revisão arquitetural independente da ADR candidata B2 (documento 15)

**TASK:** `DELIA-C3-STAGE-02-B2-EXECUTION-SCOPE-ADR-INDEPENDENT-REVIEW-01`
**DATA:** 2026-10-16
**REVIEWED_COMMIT:** `9bc367e5ab528e5eef37ff2867cacce6f744944e`
**REVIEW_REMOTE_HEAD:** `58d53f52ca0868983c932a2015f2fedca02102ca` — HEAD adiantado por mudanças concorrentes fora da ADR; git status local **não inspecionado** nesta revisão via GitHub.
**MODE:** código/contrato/documentação, leitura remota; não houve testes independentes ou alteração de runtime.
**VERDICT:** `ACCEPT_WITH_RESIDUAL` **apenas como artefato candidato de decisão**; **`TECHNICAL_CONTRACT=NOT_APPROVED`**, `D1/D2/D3=DECISION_REQUIRED`, `STAGE_02_ACCEPTED=NO`, `STAGE_03_AUTHORIZED=NO`. Não é autorização para implementar ALT-A.

## 1. Autoridades e evidence chain

Reancoragem obrigatória Project Instructions/.cursor → `16` → `50` → `17` → `49` → `51` → `52` → `21` → `20` → `25` → `02` → `24` → specs `60/69/70`/personality → ledger (§§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.181), com foco em cláusulas do B2. Hierarquia canônica e fase em 16 + ledger. O documento 13/§6.179 aprova **somente o princípio de produto**; documentos 14/15 são candidatos, não contrato produtivo.

Commit examinado altera somente `15-stage-02-b2-execution-scope-adr-candidate.md`, README da trilha e ledger §6.181. Confirmei a existência de `InteractiveTurnRequest.max_execution_stage` reduction-only; `_TurnGoal.execution_bound` proposto pelo modelo; `_attempt` executa confirmação antes de `_understand_goal`; `_attempt_prepare` distingue política owner-sealed; o MFE envia label PT gerada junto de confirmação; `_validate_input` hoje **exige input_text não vazio**. Este último item é relevante para a migração de comandos tipados sem texto.

## 2. O que foi corretamente elaborado

1. Definição de três responsabilidades distintas: intenção semântica LLM (HYPOTHESIS), execution scope do pedido (elegibilidade, não autorização), e confirmação adicional do owner (§6.140).
2. Reuse Gate adequado em direção: teto reduction-only, `PendingWrite`/digests/session/fingerprint/TTL e Policy/Decision existentes; nenhuma nova autoridade MCP, outro planner ou engine.
3. Contrato candidato provider-neutral com `NOT_ASSERTED`/`PREPARE_ONLY`/`ACT_ELIGIBLE`, `MESSAGE`/`CONFIRM_PREPARED`/`REJECT_PREPARED`, fail-closed para enum inválido, teto mais restritivo vence, e intenção do modelo nunca **amplia** ACT.
4. Impacto de compatibilidade corretamente **declarado**, não ocultado: texto livre 'crie X' deixa de ter ACT direto salvo escopo tipado; owner policy false não é alterada, mas a elegibilidade de continuar direto muda.
5. Evals negativas e positivas propostas, inclusive as 10 violações strict-xfail do diagnóstico (§6.177), nenhum resultado real de LLM demonstrado; explicitamente sem implantação.

## 3. Questões bloqueantes para CONTRACT FREEZE (não impedir aceitar o desenho como candidato)

### G1 — `ACT_ELIGIBLE` + texto contraditório continua possível

ALT-A afirma fechar os 10 diagnósticos quando `NOT_ASSERTED`, mas o próprio documento 15 reconhece que `ACT_ELIGIBLE` digitado no envelope com texto 'não aplique' que o modelo não percebe **ainda pode resultar em ACT**. Esse é precisamente o requisito de produto do §6.179 em sua forma ampla. **Não declarar `B2_RESOLVED` sem explicitar e aprovar a semântica de precedência.**
**DECISION_REQUIRED:** escolher e justificar a autoridade semântica em turnos com escopo ACT tipado + texto livre arbitrário. Opções a deliberar: (i) assumir que o comando estruturado explícito prevalece com limitação declarada; (ii) tornar ACT um comando sem texto livre concorrente e vinculado a preview/ação específica; (iii) exigir decisão pós-preview para writes quando houver texto livre não verificável. Qualquer escolha deve ter UX/contract/evals e impacto §6.140.

### G2 — request autenticado não prova origem física de uma escolha

`command.execution_scope=ACT_ELIGIBLE` é input autenticado mas untrusted. Core/Domain AuthZ continua, o que limita permission, **não comprova intenção inequívoca do humano ou gesto UI**. O contrato deve chamar esse campo de declaração tipada do solicitante autenticado, não prova inviolável de consentimento humano. Documentar ameaça de API client não-MFE, replay de request, client bug e escopo por turno/proposta. Se a decisão depender de ato humano verificável, especificar binding forte à proposta, em vez de confiar apenas em `source=user_click`.

### G3 — decisão de escopo pendente != confirmação obrigatória do owner

Com `NOT_ASSERTED`, a ADR quer reutilizar `confirmation_request` e `PendingWrite` após PREPARE inclusive quando owner `explicit_user_confirmation=false`. Isso pode ser legítimo como **declaração de escopo ausente**, mas não deve ser rotulado como confirmação adicional **exigida pelo owner**. Definir semanticamente no response e na auditoria a diferença, os consumers e binding (digest/fingerprint/TTL/actor/session), como evitar que PREPARE_ONLY prévio vire ACT sem nova escolha scoped, e como ACT-only capabilities sem PREPARE se comportam. Não inferir `NEW` sem inventário.

### G4 — contrato tipado sem texto exige evolução de validação existente

`InteractiveTurnRequest.input_text` é string obrigatória e `HandleInteractiveTurn._validate_input` rejeita vazio. ADR sugere `CONFIRM_PREPARED`/`REJECT_PREPARED` sem input. Isso **não é somente campo aditivo**, exige modelagem discriminada do request e compatibilidade na application layer, HTTP ingress, métricas e consumidores. A proposta deve especificar como validar comando tipado antes da exigência geral de texto e como migrar labels PT fixas de clientes legados. Não criar bypass que aceite mensagem vazia em MESSAGE.

### G5 — compatibilidade e governança cross-consumer incompletas

Consumers `plugins/delia` e suites foram inventariados, demais `TO_INVENTORY`; a migração 'legacy client→NOT_ASSERTED' é segura em termos de ACT, mas muda semântica e UX, não é plenamente backward-compatible. Definir versionamento, ordem de rollout/rollback, comunicação ao consumidor, tratamento de ACT-only, escopo de autorizações no phase ceiling e revalidação de Consumer/API OpenAPI antes do freeze.

## 4. D1/D2/D3 — parecer da coordenação (não decisão do Product Master)

| Item | Recomendação para submissão | Status |
| --- | --- | --- |
| D1 execution scope tipado | **Direção preferida**, com `NOT_ASSERTED` sem ACT e `PREPARE_ONLY` dominando, mas tratar G1/G2 e o conflito de texto; ACT só pode seguir com declaração tipada legítima + gates reais | `DECISION_REQUIRED`, não congelado |
| D2 command.type tipado e precedência | **Direção preferida**, separar MESSAGE de CONFIRM/REJECT, recusar payload misto conflitante; compatibilizar labels legadas e `_validate_input` | `DECISION_REQUIRED`, não congelado |
| D3 bound fail-closed | **Direção preferida como defense-in-depth**, omisso/inválido não vira irrestrito; positivo incorreto também não deve ampliar elegibilidade | `DECISION_REQUIRED`, não congela B2 sozinho |

**Não recomendado:** segundo LLM como autoridade, parsing/regex de proibições como garantia, prompt por MCP, confirmação universal sem decisão expressa, permissão de user scope sobrepondo Core/Domain/Policy/Decision ou inferência de owner metadata.

## 5. Reuse Gate / boundaries

`EXISTING_EQUIVALENT=YES` para request ceiling, Interaction Application, `PendingWrite`, structured confirmation, capability orchestrator, Policy/Decision e MFE UX. `REUSE_DECISION=REUSE/EXTEND` candidato. Necessidade de nova enum/payload/esquema ainda `TO_INVENTORY` em consumers reais e versionamento. Planner não deve conhecer provider mechanics; MCP tools/list permanece owner-owned e owner confirmation requirement intacta.

## 6. Critérios de retomada e evidência

Antes de `CONTRACT_FREEZE`, obter aprovação explícita do Product Master para (i) trade-off de ACT tipado + texto livre contraditório; (ii) distinguir 'decisão de escopo' de confirmação adicional owner; (iii) D1/D2/D3; (iv) caminho de migração/compatibilidade. Revisar contrato discriminado MESSAGE/CONFIRM/REJECT com shape de erros, owners, consumers, autenticidade, replay, audit, idempotência, versionamento e rollback.

Reusar os 10 `xfail(strict=True)` como RED de segurança; não apenas contornar fakes. Evals propostas: `ACT_ELIGIBLE` + texto 'não aplique' (com modelo cego), `NOT_ASSERTED` + `unrestricted`, explicit PREPARE_ONLY, C1–C10, owner true/false, capability ACT-only, replay, revoked AuthZ, provider rename, legacy label, distinct scope decision; positivo direct governado com escopo válido. `TEST_NOT_RUN` para este review; 1091 PASS + 10 XFAIL apenas reportado pelo executor da Etapa 02R2. Não alterar fase ou CP/RQ por documentação.

## 7. Resultado

`ADR_ARTIFACT_REVIEW=ACCEPT_WITH_RESIDUAL` **apenas como base de deliberação**. `ADR_TECHNICAL_CONTRACT=NOT_APPROVED`; `D1/D2/D3=DECISION_REQUIRED`. G1/G3/G4 impedem freeze sem revisão material; G2/G5 exigem decisão de ameaça/compatibilidade antes de implementação. `B1=PASS_STRUCTURAL`, `B2=REWORK`, `STAGE_02_ACCEPTED=NO`, `STAGE_03_AUTHORIZED=NO`, `C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.

**Review documental somente. Nenhum código, testes, APIs, estado de fase, owner policy ou contratos produtivos modificados por este parecer.**
