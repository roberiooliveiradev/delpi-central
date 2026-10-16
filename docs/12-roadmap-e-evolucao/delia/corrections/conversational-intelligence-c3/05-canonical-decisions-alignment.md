# 05 — Alinhamento canônico do plano de inteligência conversacional C3

**Task:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-PLAN-ALIGNMENT-01
**Data:** 2026-10-16. **BASE_HEAD remoto:** 7b3b6af3f337b2d5240e6a8234c31a3a4bef3e10. **Estado:** DOCUMENTATION_ONLY; sem mudança de runtime, autorização, fase ou aceite.

## Autoridades revalidadas e precedência

Project Instructions/.cursor → [16](../../16-execution-master-plan.md) → [50](../../50-standalone-copilot-application-architecture.md) → [17](../../17-component-and-contract-map.md) → [49](../../49-architecture-and-design-patterns-standard.md) → [51](../../51-platform-integration-baseline.md) → [52](../../52-standalone-repository-and-bootstrap-plan.md) → [21](../../21-data-and-state-model.md) → [20](../../20-testing-and-acceptance-matrix.md) → [25](../../25-requirements-traceability.md) → [02](../../02-arquitetura.md) → [24](../../24-product-specification.md) → [60](../../60-agent-interoperability-mcp-a2a-and-tool-protocols.md) → [69](../../69-conversation-experience-ux-wireframes-and-activity-plan.md) → [70](../../70-tool-activity-and-source-transparency-ux-specification.md) → [personality/02](../../personality/02-behavior-and-interaction.md), [03](../../personality/03-decision-record.md), [04](../../personality/04-behavioral-quality-evaluation.md) → [ledger](../../evidence/execution-ledger.md).

Revisão de cláusulas aplicáveis; não significa aceite integral de CP/RQ nem prova de todos os componentes. HEAD remoto não comprova git status local.

## Decisões vinculantes já aprovadas

| Fonte | Decisão superior | Restrição à trilha |
| --- | --- | --- |
| 24 §5; 50 §6; ledger §6.130 | Uma DÉLIA standalone, OPERATIONAL_CAPABILITY_ORCHESTRATOR provider-neutral | Reusar Interaction/Orchestrator; sem segundo planner/agent, importação do runtime Chat ou if-branch por provider |
| ledger §6.126, §6.141; 60 §5 | Specialist detém tools/classes/schemas/availability/vocabulário; tools/list autenticado e fresco é superfície primária | Sem catálogo local MCP; get_catalog/guidance são adicionais quando o owner os disponibiliza, não obrigação de todo MCP |
| ledger §6.133 | Superfície do owner inclui inteligência de domínio/qualidade, READ/ANALYSIS/guidance conforme contrato | Consumir owner knowledge; não copiar regras de negócio nem torná-lo nova autoridade da DÉLIA |
| ledger §6.140 | Resolver genérico SAME-OWNER não-mutante (DISCOVERY/READ/ANALYSIS), ambiguidade→CLARIFICATION_REQUIRED, ids inventados bloqueados, máximo 3 steps | Não criar novo resolver, planner livre ou expansão cross-owner fora do escopo |
| ledger §6.140 | ANALYSIS first-class OBSERVATION; pode alimentar PREPARE; ACT é continuação governada | Orientação não implica write; nenhuma classe metadata/LLM autoriza ACT |
| ledger §6.140 | confirmation_requirement.explicit_user_confirmation selado no PREPARE rege confirmação adicional; true→confirmar, false→direto governado, inválido→WRITE_REJECTED | Sem confirmação universal; Core/Domain live AuthZ e Policy/Decision obrigatórios permanecem |
| ledger §6.145; 21 §4B | MODEL_AUTHORED_FACTUAL_PROSE=NONE, owner é fonte factual, runtime renderiza deterministicamente | Sem LLM redigindo fatos livremente; melhorar suficiência e evidência dentro do freeze |
| 24 §6; personality/02..04; 69/70 | Personalidade/conversa natural aprovadas editorialmente; runtime/evals não comprovados integralmente | Sem novo personality engine, memória implícita, autorização por estilo ou respostas factuais fabricadas |
| ledger §6.171 | Etapa 01: 15 testes fake/scripted, 1069/1069 relatados; independent review não registrado | Teste pytest PASS para reprodução de comportamento FAIL não equivale a sucesso real ou aceite |

## Pontos do plano que precisaram ser requalificados

1. **Novo goal_class orient:** ausência literal observável não prova necessidade de novo enum, contrato ou prompt. Investigar a semântica já disponível antes de propor mudança formal.
2. **Mover goal antes de target_selection:** o código seleciona o alvo antes do goal estruturado. Reorder não foi aprovado; primeiro provar como preservar finalidade sem novo planner e sem regressão.
3. **DISCOVERY para strings sem enum:** errado como regra universal: string pode ser texto livre. Precisa de contrato/vocabulário legitimamente oferecido pelo owner, com budget bounded.
4. **Validar negócio dentro da DÉLIA:** não duplicar Domain rules. Pode avaliar completude estrutural com schema owner confiável; owner continua responsável por regra, PREPARE/readiness e postcondition.
5. **Exigir confirmação em todas as criações:** contradiz §6.140; preservar requisito estrutural selado e gates live, sem inventar permissões.
6. **Superprompt, prompt por MCP ou engine novo:** não demonstrados; primeiro REUSE/EXTEND de instructions, resolver, seleção e apresentação.
7. **Prosa factual livre para naturalidade:** contraria §6.145; seria ARCHITECTURE_DECISION_REQUIRED, nunca ajuste silencioso.
8. **Fakes = generalização real do LLM:** falso; testes de Etapa 01 demonstram pipeline sob proposals scripted; comportamento do modelo real ainda requer eval.

## Compatibilidade das seis etapas bounded

| Etapa | O que pode ser investigado / evoluído com aprovação | Gate de não-desvio |
| --- | --- | --- |
| 01 | Baseline histórico §6.171, relatório 04 | EVIDENCE_RECORDED, review independente PENDING, sem reescrever evidência anterior |
| 02 | Coerência da finalidade na seleção, goal e instruções atuais | Sem novo goal enum/reorder/prompt por presunção; pergunta de orientação não autoriza PREPARE |
| 03 | Tools/list live, discovery/guidance do owner e vocabulário limitado | Sem mirror, catálogo DÉLIA ou discovery para todo string |
| 04 | Argumentos, completude, resolver same-owner, clarificação mínima | Owner valida regras, confirmação §6.140, inferência não vira default/ACT |
| 05 | Suficiência e respostas determinísticas, integração de personalidade aprovada | §6.145 intacto, Evidence/provenance/limitations preservados |
| 06 | Evals generalizadas com fakes, renamed owners/tools, holdout, modelo real, negativas e outcome | Sem autoaceite, mudança de fase ou rollout por documentação |

EXISTING_EQUIVALENT=YES: Interaction Application, OperationalCapabilityOrchestrator, ModelInvocationPort/InvokeModel, instructions estruturadas, resolver same-owner, live capability projection, grounded synthesis, presentation e harness de evals. REUSE_DECISION=REUSE por padrão; EXTEND após provar o gap; NEW exige NO demonstrado, Abstraction Gate e contrato/owner/consumer legítimos.

## Estado e continuidade

C3_STARTED=YES, C3_EXECUTED=NO, C4/C5 phase-level não autorizadas; NEXT=RETURN_TO_ARCHITECTURE_COORDINATION no snapshot revalidado. Etapa 01 EVIDENCE_RECORDED pelo commit 1f29906dc45726c778e8d133b2fbdbc41f4b9939/ledger §6.171; opinião de review em chat não equivale a aceitação independente canônica. Sem novo prompt de Devin ou autorização das etapas 02–06 por este documento.

Rastreabilidade a revalidar na 25: CP-055, CP-071, CP-073/074, CP-094, CP-151, CP-205, CP-232/233, CP-263, CP-269 se aplicável. **CP-086/087 são sobre Expertise Packs, não substituem os testes de provider/tool rename de §6.141.** Requisito sem mapeamento = TRACEABILITY_GAP; não criar CP local.

A cada etapa: HEAD + git status → authorities → ledger/CP/RQ/AC → owner/contract/consumers → EXISTING_EQUIVALENT/REUSE_DECISION → autorização bounded → testes/evals/outcome → review independente. Conflito novo: STOP, EXECUTION_DRIFT ou ARCHITECTURE_DECISION_REQUIRED.
