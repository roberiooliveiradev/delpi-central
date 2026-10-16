# 17 — Decisão do Product Master: texto livre pode preparar, ACT exige escolha vinculada à operação

**TASK:** DELIA-C3-STAGE-02-B2-TEXT-ONLY-ACT-SCOPE-PRODUCT-DECISION-01  
**DATA:** 2026-10-16  
**HEAD remoto na revisão:** `8626e874822bb1b4cf3523f559c9b8cc3993a54c` (não equivale a git status local)  
**MODE:** PRODUCT_DECISION / DOCUMENTATION_ONLY  
**STATUS:** `PRODUCT_RULE_TEXT_ONLY_PREPARE_UNTIL_OPERATION_BOUND_EXECUTION_CHOICE=APPROVED`; `TECHNICAL_CONTRACT=NOT_APPROVED`; `IMPLEMENTATION=NOT_AUTHORIZED`.

## 1. Autorização expressa e escopo exato

O Product Master recebeu a pergunta: **"Você concorda que, para pedidos feitos somente por texto livre, a DÉLIA pode preparar tudo automaticamente, mas deve obter uma escolha explícita de execução vinculada à operação antes de aplicar a mudança?"** e respondeu **"concordo"**.

É aprovação de **regra de comportamento do produto**, NÃO aprovação irrestrita da ALT-A do documento [15](./15-stage-02-b2-execution-scope-adr-candidate.md), do formato `command.execution_scope`, da UX, da implementação ou do contrato técnico. O parecer independente [16](./16-stage-02-b2-adr-independent-architecture-review.md), ledger §6.182, permanece relevante.

## 2. Regra de produto APPROVED

1. Pedidos realizados **somente em linguagem natural**, sem escolha explícita e válida de EXECUTAR associada à operação específica, podem seguir por investigação, leitura, análise, descoberta e **PREPARE**, desde que fase/policy/owner autorizem, mas não por ACT material. É proibido inferir elegibilidade a ACT exclusivamente de `goal_class`, `execution_bound=unrestricted` ou resultado MCP.
2. Uma mudança preparada requer **escolha explícita de execução vinculada à operação** para aplicação material. O usuário não precisa confirmar todas as etapas da investigação/preparação. Não foi aprovada confirmação universal; a origem, forma, escopo e validação da escolha ainda exigem contrato.
3. Pedido "prepare, mas não aplique" permanece PREPARE-only mesmo se LLM disser `unrestricted` e owner disser `explicit_user_confirmation=false`. `PREPARE_ONLY`/teto `max_execution_stage='prepare'` prevalece sobre qualquer sinal permissivo.
4. A regra do owner `confirmation_requirement.explicit_user_confirmation` (§6.140) mantém seu significado: declara necessidade de **confirmação adicional** da proposta, não substitui escopo/eleição do usuário. Quando houver escolha válida de ACT previamente vinculada à operação e todas as permissões/gates estiverem satisfeitos, a continuação direta **poderá** ser elegível com owner `false` (o contrato para tal vinculação não foi decidido).
5. Escopo informado pelo usuário ≠ autorização efetiva: Keycloak identidade, Core RBAC efetivo, Domain API autoridade final, DÉLIA Policy/Decision/Outcome, idempotência e audit continuam exigidos. JWT, UI state, tool metadata, output de LLM, memória ou cache não concedem permissão.

**Invariante conceitual, não implementado:** `TEXT_ONLY_AND_NO_OPERATION_BOUND_EXECUTION_CHOICE => MAX_MATERIAL_STAGE=PREPARE`.

## 3. Aprovação limitada e gaps remanescentes

| Item | Estado após esta decisão |
| --- | --- |
| **D1 — regra de produto:** texto livre, sem escolha associada à operação, não permite ACT | **APPROVED** (escopo acima) |
| D1 — contrato `ACT_ELIGIBLE`: transport, origem verificável, vínculo de operação, request/response, validade, UI e integração | **NOT_APPROVED / TO_DESIGN** |
| **G1 — `ACT_ELIGIBLE` tipado + texto livre contraditório ("não aplique")** | **DECISION_REQUIRED** sobre precedência e fail-closed; concordância não aprova ignorar a negação |
| **D2 — comandos MESSAGE/CONFIRM/REJECT**, input livre contraditório, label legado, input vazio e compatibilidade | **NOT_APPROVED / DECISION_REQUIRED** |
| **D3 — bound omitido/inválido fail-closed** | **NOT_APPROVED / DECISION_REQUIRED**; sozinho não corrige `unrestricted` positivo errado |
| **G2** — campo enviado por cliente autenticado vs. prova de intenção humana | **TO_DESIGN**; uma flag de client não é prova absoluta de escolha humana |
| **G3** — decisão de escopo vs confirmação adicional exigida pelo owner | **MUST_REMAIN_DISTINCT** como princípio; reuso de PendingWrite/confirmation_request requer contrato adequado |
| **G4/G5** — request sem texto, consumers não-MFE, versionamento, rollout, rollback | **TO_INVENTORY / DECISION_REQUIRED** |
| Fase, C3 e aceite de Stage 02 | **UNCHANGED**; B2 continua REWORK, Stage03 NOT_AUTHORIZED |

Não interpretar ausência de contrato fechado como aprovação automática de `command.type`, novos endpoints, estado durável, modelo adicional, parser regex, confirmação universal, flags ad hoc ou nova camada de inteligência.

## 4. Exemplos para orientar o contrato

| Solicitação | Direção |
| --- | --- |
| "Como criar um processo?" | Orientar sem escrita |
| "Prepare a alteração, mas não salve." | PREPARE; zero ACT |
| "Crie o processo X" apenas como texto livre | Pode PREPARE; ACT aguarda escolha explícita vinculada à operação |
| Escolha tipada válida de executar operação X e owner dispensa confirmação adicional | ACT pode ser elegível **somente** se os outros gates autorizarem e não houver limite mais restritivo |
| `max_execution_stage='prepare'` com qualquer modelo/owner | ACT bloqueado |
| Escolha ACT e texto contraditório | Requer protocolo seguro de conflito e decisão D2/G1; este documento **não** autoriza ACT silencioso |

## 5. Reuse, evidências e próximo gate

`EXISTING_EQUIVALENT=YES`: `InteractiveTurnRequest.max_execution_stage`, `_TurnGoal`, `OperationalCapabilityOrchestrator`, `PendingWrite`, confirmação estruturada, Decision/Policy, MFE. `REUSE_DECISION=REUSE/EXTEND` é candidata; `NEW=NOT_AUTHORIZED` sem inventário completo.

A motivação já está documentada: **10 strict-xfail** em `test_stage02r2_execution_bound_diagnosis.py` sob FakeProposalModel quando texto "não aplique" se combina com `unrestricted`; executor reportou 1091 PASS + 10 XFAIL na suíte; real-model `TEST_NOT_RUN`. Esta decisão não executa nem corrige esses testes.

Antes de implementation: reanchor 16→50→17→49→51→52→21→20→25→02→24→temáticas 60/69/70/personality→ledger; rever [13](./13-product-principle-intent-and-act-scope.md), [14](./14-execution-scope-contract-security-review.md), [15](./15-stage-02-b2-execution-scope-adr-candidate.md), [16](./16-stage-02-b2-adr-independent-architecture-review.md); resolver G1–G5 e D1 técnico/D2/D3; contrato owner/consumer request/response/errors/security/compat/idempotency/observability/rollback; independent review; aprovação técnica expressa; só então implementação bounded e evals.

**STATUS FINAL:** `PRODUCT_RULE_TEXT_ONLY_PREPARE_UNTIL_OPERATION_BOUND_EXECUTION_CHOICE=APPROVED`; `D1_PRODUCT_DIRECTION=APPROVED_NARROW_SCOPE`; `D1_TECHNICAL_CONTRACT=NOT_APPROVED`; `D2/D3=DECISION_REQUIRED`; `B1=PASS_STRUCTURAL`; `B2=REWORK`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`; `C5_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.

**Nenhum runtime, API, UI, owner policy, migração, teste, contrato técnico ou fase foi alterado por esta decisão documental.**
