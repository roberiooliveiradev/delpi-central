# I01 — Proposta arquitetural de continuidade contextual alinhada às autoridades

**DATA:** 2026-10-17. **TRACK:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`. **BASE_HEAD:** `453daa26958f4f0730efb012619e4dbef4e96fc9`. **STATUS:** `PROPOSED_FOR_CONTRACT_REVIEW`; nenhum código/teste/deploy autorizado ou executado.

## Fontes e decisão de alinhamento

Lidas no GitHub: plano [16](../../16-execution-master-plan.md), standalone [50](../../50-standalone-copilot-application-architecture.md), padrões [49](../../49-architecture-and-design-patterns-standard.md), estado [21](../../21-data-and-state-model.md), testes [20](../../20-testing-and-acceptance-matrix.md), rastreabilidade [25](../../25-requirements-traceability.md), ledger §§6.235–6.237 e [I00](./01-i00-independent-context-baseline-acceptance.md). Documentos 17, 51, 52 e specs técnicas/produto aplicáveis devem ser reancorados por **paths reais** na execução; esta revisão não certifica leitura completa de toda a cadeia. Em conflito, autoridade superior prevalece, STOP sem reconciliar silenciosamente.

**PROBLEM PROVEN:** K2 TÉO: `prior_evidence_sufficient=false`, reconsulta desnecessária no cenário, literal replay, 30014ms. K1/K3 `skip_budget` pertencem primariamente a I02. **NOT PROVEN:** ausência de payload estruturado como causa única de K2; cobertura dos demais subsistemas de persistência.

**RESPONSIBILITY / OWNER:** continuidade e seleção de evidência = Application DÉLIA; conteúdo metodológico = MCP owner TÉO/VISTA/etc.; identidade Keycloak, AuthZ Core, fatos e regras Domain API. **CONSUMER:** `HandleInteractiveTurn` / `OperationalCapabilityOrchestrator`, frontend MFE envia contexto transitório. **BOUNDARY:** `ConversationContextTurn` client-supplied untrusted; `SpecialistOutcome` do owner é evidence não authority. `REUSE: EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND_CANDIDATE`. Nenhum port, provider branch, memory engine ou registry novo.

## Métodos existentes / proposta mínima

1. `_understand_goal`: melhorar reconhecimento genérico e evidencial de pedido de transformação/extração de guia anterior, sem texto específico de TÉO/VISTA. Modelo propõe intenção/suficiência; runtime valida adequação. Não definir suficiência por nome de ferramenta nem aceitar declaração livre como FACT.
2. `_prior_result_turn` + `_prior_continuation_attempt`: selecionar trechos efetivamente presentes em `DELIA_RESULT` admissível, projetar/organizar evidência sem replay completo. Se o conteúdo anterior foi truncado ou não contém os dados requisitados, não inventar; honest limitation ou fresh owner READ quando apropriado.
3. `_synthesize_content`: seguir seleção de registros/atributos e renderização determinística; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`. Reserva de síntese/caminho determinístico útil e latência de K1/K3 é I02, não misturar refatoração grande à I01.
4. `TurnDeadline`: 30 segundos globais, headroom explícito antes de consulta adicional, sem aumentar timeout, não iniciar trabalho quando orçamento insuficiente.
5. Frontend/HTTP context: preservar contrato atual `kind/content/epistemic_class` durante I01; `provenance/grounding` não são transportados como refs estruturadas. Se RED provar que a continuidade exige metadados adicionais, STOP `ARCHITECTURE_DECISION_REQUIRED`, definir antes contrato com owner/consumers, privacidade/retention e compatibility. Proibido novo cache persistente por conveniência.

## Deterministic gates / safety

- Classificar follow-up: **transformar evidência anterior** vs **buscar fato novo/atual** vs **clarificar**. O modelo pode propor, não autorizar nem atestar suficiência sozinho.
- `prior_turns` são untrusted; não promovê-los a FACT/GROUNDED atual, não os usar como fonte de id para operação, permissão ou Policy. Continuidade sem owner read novo deve conservar `NON_GROUNDED prior_turn_evidence_only` e limitações.
- Manter discovery/live owner capability para novos fatos, confirmação e ACT governados; `MESSAGE != ACT`; prompt injection inerte.
- Manter owner/provider neutral, nenhum hardcode de specialist, palavra-chave de produto, branch por MCP ou cópia de catálogo/conhecimento.

## Gates de implementação da I01

1. Reancorar HEAD/status, Project Instructions/.cursor, toda a hierarquia 16→50→17→49→51→52→21→20→25→arquitetura técnica→product spec→spec temática→ledger. Inventariar CP/RQ reais e contratos, sem inventar IDs.
2. Caracterizar comportamento atual com teste RED do caso K2 em fixture **provider sintético** contendo guia de metodologia e follow-up “quais informações levantar?”; tratar replay/truncamento/sem evidência como negativos.
3. Implementar menor diff em mecanismos existentes, sem refatorar `orchestration.py` estruturalmente nesta task.
4. Testar: continuidade suficiente → sem owner re-invoke, seleção relevante e sem replay; insuficiente → fresh authorized owner READ ou honest limitation; dados mutáveis → nunca usar contexto stale como fato; históricos manipulados, prompt injection, owner/tool rename, 0 ACT, <=30s.
5. Suite completa + eval real K1/K2 em SHA/config autorizado e independent review; distinguir `PASS`, `FAIL`, `INCONCLUSIVE`, `TEST_NOT_RUN` e business outcome. Atualizar ledger após execução factual.

```text
I01_ARCHITECTURE_DIRECTION=PROPOSED
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND_CANDIDATE
GLOBAL_MCP_KNOWLEDGE_PERSISTENCE=NO
CONTEXT_CONTRACT_CHANGE=NOT_AUTHORIZED
SOURCE_CODE_CHANGED=NO
TESTS=TEST_NOT_RUN
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I01_CONTRACT_CP_RQ_AND_RED_TEST_GATE
```
