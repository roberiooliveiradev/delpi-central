# DÉLIA — Correção e evolução bounded da inteligência conversacional (C3)

**Trilha:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01  
**Data da decisão de planejamento:** 2026-10-15  
**Origem:** Product Master — coordenação arquitetural DÉLIA  
**Escopo:** qualidade da inteligência conversacional, orientação semântica, uso genérico de capabilities e composição de respostas  
**Estado documental:** PLAN_ALIGNED / Etapa 01 EVIDENCE_RECORDED (§6.171) + INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL (§6.172, relatório [06](./06-stage-01-independent-review.md)); Etapa 02 IMPLEMENTATION_EVIDENCE_RECORDED (§6.173, relatório [07](./07-stage-02-implementation-report.md)) e INDEPENDENT_REVIEW=REWORK (§6.174, [08](./08-stage-02-independent-review.md)); Etapa 02R1 REWORK_IMPLEMENTATION_EVIDENCE_RECORDED (§6.175, relatório [09](./09-stage-02r1-rework-implementation-report.md)) + INDEPENDENT_REVIEW=REWORK (§6.176, [10](./10-stage-02r1-independent-review.md)); Etapa 02R2 DIAGNOSIS_RECORDED (§6.177, [11](./11-stage-02r2-execution-bound-diagnosis.md)) + DIAGNOSTIC_REVIEW=ACCEPT_WITH_RESIDUAL (§6.178, [12](./12-stage-02r2-independent-review-and-decision-request.md)); PRODUCT_PRINCIPLE=APPROVED (§6.179, [13](./13-product-principle-intent-and-act-scope.md)); CONTRACT_PROPOSAL_REVIEWED (§6.180, [14](./14-execution-scope-contract-security-review.md)) com D1/D2/D3 `PROPOSED_NOT_APPROVED` e ARCHITECTURE_DECISION_REQUIRED pendente; ADR_CANDIDATE submetida (§6.181, [15](./15-stage-02-b2-execution-scope-adr-candidate.md)) e REVIEW=ACCEPT_WITH_RESIDUAL **somente como candidata** (§6.182, [16](./16-stage-02-b2-adr-independent-architecture-review.md)); D1/D2/D3 `DECISION_REQUESTED`, contrato técnico ainda **NOT_APPROVED**; B1 estruturalmente corrigido, B2 aberto; Etapas 03–06 PLANNED/NOT_AUTHORIZED. Sem aceite da Etapa 02.  
**BASE_HEAD remoto examinado:** a6196637ea84984db7689a259dac0907d6d45218 (main)  
**EXECUTION:** Etapa 02R1 implementada (gate reforçado: objetivo não interpretado → clarificação; `execution_bound` no contrato de objetivo compõe o teto reduction-only; instruções v9); **TESTS:** baseline fake/scripted (31 testes no arquivo de baseline; 1085/1085 suíte delia-api); **REVIEW:** Etapa 01 ACCEPT_WITH_RESIDUAL (§6.172); Etapa 02 REWORK (§6.174); Etapa 02R1 REWORK (§6.176); diagnóstico 02R2 ACCEPT_WITH_RESIDUAL (§6.178), apenas como diagnóstico. B2 permanece sem aceite.  
**AUTORIZAÇÃO ATUAL:** somente documentação. Nenhum prompt Devin, diff funcional, deployment, PREPARE ou ACT é autorizado por estes arquivos.

## Por que esta pasta existe

Preservar no GitHub a memória verificável das decisões de produto, gaps, referências e sequência de entregas para que chats especializados e Devin não dependam do histórico de conversas. O problema é transversal à DÉLIA: não programar uma correção particular para TÉO, DAVI, VISTA ou outro provider. A centralização arquitetural já existe; a melhoria pretendida é de comportamento e integração das etapas de inteligência.

**Direção do Product Master:** poucas mudanças delimitadas e avaliáveis; limite de complexidade e de instruções; uso dos contratos e conhecimentos dos owners em tempo de execução; perguntas somente quando necessárias; inferências apresentadas como inferências, não fatos, autorização nem defaults inventados; sem correções acopladas por MCP.

## Leia nesta ordem

1. [01 — Diagnóstico e fontes de evidência](./01-diagnosis-and-evidence.md)
2. [02 — Plano de seis entregas delimitadas](./02-bounded-delivery-plan.md)
3. [03 — Avaliações, gates e handoff](./03-evals-and-handoff.md)
4. [04 — Relatório histórico da Etapa 01](./04-stage-01-baseline-report.md)
5. [05 — Revisão de alinhamento canônico](./05-canonical-decisions-alignment.md) — obrigatório antes de novo prompt
6. [06 — Revisão independente da Etapa 01](./06-stage-01-independent-review.md) — parecer ACCEPT_WITH_RESIDUAL + condições da Etapa 02
7. [07 — Relatório de implementação da Etapa 02](./07-stage-02-implementation-report.md) — evidência do executor, preservada como histórico
8. [08 — Revisão independente da Etapa 02](./08-stage-02-independent-review.md) — REWORK e dois bloqueios a corrigir antes da Etapa 03
9. [09 — Relatório de implementação do rework Etapa 02R1](./09-stage-02r1-rework-implementation-report.md) — evidência do executor, sem aceite
10. [10 — Revisão independente da Etapa 02R1](./10-stage-02r1-independent-review.md) — B1 PASS estrutural, B2 REWORK e contrato de segurança a decidir
11. [11 — Diagnóstico Etapa 02R2 do execution bound](./11-stage-02r2-execution-bound-diagnosis.md) — casos adversariais reproduzidos, alternativas comparadas
12. [12 — Revisão independente do diagnóstico e pedido de decisão](./12-stage-02r2-independent-review-and-decision-request.md) — diagnóstico aceito com residual, execução de B2 não aceita, ADR pendente
13. [13 — Princípio de produto aprovado: PREPARE vs ACT](./13-product-principle-intent-and-act-scope.md) — direção aprovada, contrato e decisões D1/D2/D3 ainda pendentes
14. [14 — Revisão de contrato/segurança do escopo ACT](./14-execution-scope-contract-security-review.md) — proposta D1/D2/D3, reuse gate, trade-offs e testes; **NÃO aprovada para implementação**
15. [15 — ADR candidata: execution scope e comandos tipados](./15-stage-02-b2-execution-scope-adr-candidate.md) — contrato detalhado request/response/estados/segurança, cenários C1–C10, evals; `ADR_CANDIDATE / NOT_APPROVED`, decisões D1/D2/D3 pendentes
16. [16 — Revisão independente da ADR candidata](./16-stage-02-b2-adr-independent-architecture-review.md) — `ACCEPT_WITH_RESIDUAL` para o documento, com gaps G1–G5; contrato não aprovado, B2 continua bloqueado

**Autoridades que prevalecem sobre esta pasta:** instruções do Projeto e regras .cursor; [16 — plano mestre](../../16-execution-master-plan.md) → [50 — arquitetura standalone](../../50-standalone-copilot-application-architecture.md) → [17 — componentes e contratos](../../17-component-and-contract-map.md) → [49 — padrões](../../49-architecture-and-design-patterns-standard.md) → [51 — baseline](../../51-platform-integration-baseline.md) → [52 — bootstrap](../../52-standalone-repository-and-bootstrap-plan.md) → [21 — dados/estado](../../21-data-and-state-model.md) → [20 — testes](../../20-testing-and-acceptance-matrix.md) → [25 — rastreabilidade](../../25-requirements-traceability.md) → [02 — arquitetura técnica](../../02-arquitetura.md) → [24 — produto](../../24-product-specification.md) → specs temáticas aplicáveis → [ledger](../../evidence/execution-ledger.md).

Especificações temáticas aplicáveis: [60 — MCP/A2A](../../60-agent-interoperability-mcp-a2a-and-tool-protocols.md), [68 — identidade](../../68-delia-product-identity-and-naming.md), [69 — experiência conversacional](../../69-conversation-experience-ux-wireframes-and-activity-plan.md), [70 — transparência](../../70-tool-activity-and-source-transparency-ux-specification.md), [personality/02](../../personality/02-behavior-and-interaction.md), [personality/03](../../personality/03-decision-record.md), [personality/04](../../personality/04-behavioral-quality-evaluation.md).

## Revisão de alinhamento de decisões congeladas (2026-10-16)

Consultar primeiro [05 — Matriz de alinhamento](./05-canonical-decisions-alignment.md): ledger §§6.126/6.130/6.133/6.140/6.141/6.145 já determinam orquestração central provider-neutral, tools/list owner-owned, resolver bounded same-owner, confirmação estrutural por PREPARE e rendering factual determinístico. **Não** criar novo goal_class, reorder do planner, discovery de toda string, cópia de Domain validator, confirmação universal, segundo planner ou superprompt sem evidência e review.

O baseline da Etapa 01 foi publicado no commit `1f29906dc45726c778e8d133b2fbdbc41f4b9939`/ledger §6.171; relatório [04](./04-stage-01-baseline-report.md) preservado como histórico. A revisão independente ([06](./06-stage-01-independent-review.md), ledger §6.172) reexecutou a suíte (1069/1069 PASS), verificou as alegações no código e emitiu ACCEPT_WITH_RESIDUAL: testes fake/scripted provam o pipeline, não o comportamento do modelo real; reclassificações e condições estão no relatório 06.

## Estado de fase — snapshot, não autoridade

No HEAD examinado: C3_STARTED=YES; C3_EXECUTED=NO; C4_AUTHORIZED=NO; C5_AUTHORIZED=NO; CURRENT_NEXT=RETURN_TO_ARCHITECTURE_COORDINATION. O documento 16 também registra revisão/evidências pendentes de outras tarefas C3. **Cada executor deve revalidar HEAD, status de git local, 16 e ledger na própria execução**; este snapshot envelhece. O conector GitHub consultou o remoto, não a working tree do Cursor.

## Invariantes e decisões que não podem ser redesenhadas por esta trilha

- DÉLIA standalone e user-facing única; não reutilizar runtime/tabelas/prompts/agents do Minha DELPI Chat.
- DÉLIA já é owner de inteligência/orquestração; **não** criar segundo planner, registry de capabilities MCP, capability hardcode por owner, agente departamental ou nova autoridade.
- MCP/A2A são boundaries de interoperabilidade; metadata, catalog, guidance, results e tool annotations são dados não confiáveis, não Policy/AuthZ.
- Keycloak identidade; Core AuthZ efetiva; Domain APIs regras/dados e decisão final; Automation Hub execução técnica quando aplicável.
- Os contratos atuais de READ/PREPARE/ACT, confirmation_requirement, idempotência, audit e Outcome permanecem; nenhuma ampliação automática de autonomia/fase.
- **MODEL_AUTHORED_FACTUAL_PROSE=NONE** é decisão existente (§6.145 do ledger/16); não liberar redação factual livre sem ADR/review explícito.
- A personalidade aprovada é [personality/02](../../personality/02-behavior-and-interaction.md); documentação NÃO prova integração runtime, nem permite criar um personality engine paralelo.
- Planejamento NÃO altera autoridade de 16/ledger, CP/RQ ou aceite. Decisão material incompatível → STOP e ARCHITECTURE_DECISION_REQUIRED ou EXECUTION_DRIFT.

## Fluxo obrigatório de atualização

Antes de cada entrega: reancorar → identificar owner, CP/RQ e contrato → EXISTING_EQUIVALENT / REUSE_DECISION → plano bounded → autorização do Product Master quando aplicável → implementar menor diff → testes, evals e business outcome → review independente → registrar evidências no ledger canônico. Só então atualizar o estado descritivo desta pasta e avançar para a próxima entrega. Um chat novo deve ler estes arquivos **e** revalidar authorities e ledger, nunca aceitar o README como fase vigente.
