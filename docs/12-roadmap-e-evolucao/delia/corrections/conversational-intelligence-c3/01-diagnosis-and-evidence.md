# 01 — Diagnóstico e evidências de origem

**Status:** INVENTORY_SNAPSHOT / PARTIAL_EVIDENCE; não é laudo end-to-end de produção.  
**Data:** 2026-10-15  
**HEAD consultado:** 40d7d3c0fc04a62795298fb5e45ef00434f51345  
**Classificações:** PROVEN | TO_INVENTORY | PLANNED | TARGET; testes = PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE.

## Problema de produto

A DÉLIA já consulta e orquestra capabilities, mas demonstra dificuldades em transformar a intenção do usuário e a evidência dos owners numa conversa que resolva o objetivo. Exemplos reportados:

- “Qual o último processo cadastrado no Transforma+?” — resposta enumera campos de um registro sem comprovar ordenação de cadastro. Dez registros retornados não provam qual é o último. **Sintoma reportado; causa e resposta correta ainda TO_INVENTORY.**
- “Como criar um processo?” — experiência reportada não orientou satisfatoriamente, apesar de existir guidance consultável.
- “Crie um processo chamado processo teste délia” — trace apresentado pelo Devin: seleção TÉO/PREPARE correta, proposal READY com campo interno status_processo ausente; ACT tentou commit e recebeu validação de ProcessoCreateBody. **Trace reportado pelo usuário, não reproduzido sob SHA/config nesta trilha**. Não confundir essa observação com aceitação de política de confirmação.

O Product Master explicitou: o foco não é corrigir apenas TÉO. Ele é um caso de reprodução de uma deficiência transversal da camada de interação DÉLIA. Não concluir root cause owner-side sem inspeção.

## Inventário direto de código DÉLIA — PROVEN no HEAD consultado

| Boundary | Evidência | Alcance / limitação |
| --- | --- | --- |
| Application interaction | delia-api/app/application/interaction/handle_interactive_turn.py | Invoca orquestração governada; SUCCESS grounded tem caminho próprio; falha/negação não vira resposta operacional fabricada; fallback modelo geral separado |
| Instrução de interação | delia-api/app/application/interaction/instruction.py | Instrução base v3 enfatiza limites, dados não verificados, AuthZ e contexto não confiável; não demonstra sozinha personalidade completa |
| Model invocation | delia-api/app/application/model_invocation/invoke_model.py | Port/use case e lineage; não prova qualidade do provider nem direção semântica |
| Orquestração central | delia-api/app/application/capability_provision/orchestration.py | Seleção de grupo/capability, goal, argumento, resolver, clarificação, síntese, governed write; provider-neutral em desenho e contratos |
| Apresentação | delia-api/app/application/interaction/presentation.py | presentation.v1, kinds/blocks com allowlist; consumer UI não vira owner de resposta |
| Personalidade | docs/12-roadmap-e-evolucao/delia/personality/02..04 | Direção editorial aprovada em 2026-10-10; RUNTIME_IMPLEMENTATION=NOT_PROVEN e BEHAVIORAL_EVAL=TEST_NOT_RUN |

Em orchestration.py existem instruções especializadas distintas (goal, group, capability, arguments, resolver, clarification, grounded_synthesis etc.), não ausência total de prompts. Os métodos _understand_goal, _build_arguments, _resolve_missing_inputs, _clarification_question e _synthesize_content já são equivalentes a reutilizar. A função _build_arguments valida o schema de input da tool; esse schema pode aceitar changes como objeto sem demonstrar completude do schema **interno da entidade**. Não duplicar Domain authority na DÉLIA; investigar contrato vivo e validação precoce com o owner.

A síntese seleciona record_index/fields e utiliza rendering determinístico; o contrato proíbe MODEL_AUTHORED_FACTUAL_PROSE. Uma composição tecnicamente válida pode não responder ao significado de “último cadastrado” ou ser natural. O problema é de suficiência semântica e apresentação, não licença para inventar prosa.

**Limites já presentes observados em código:** MAX_OPERATIONAL_PLAN_STEPS=3; MAX_REPLAN_ROUNDS=1; MAX_SURFACE_CHARS=6000; MAX_ARGUMENTS_BLOCK_CHARS=14000; SELECTION_INSTRUCTION_VERSION=7. São limites factuais da implementação, não novos valores normativos congelados pela trilha.

## MCPs — evidência externa de descoberta, não prova runtime DÉLIA

Consultas read-only nesta conversa ao TÉO conectado:
- get_catalog retornou entity_schemas.process.required = [nome_processo, status_processo], enums de status_processo = [ativo, descontinuado, em_implantacao], defaults de process = {}.
- get_product_guide(topic=process) retornou orientação para diferenciar processo/instância/revisão, consultar duplicados e campos válidos.
- record_read(action=search, entity=process, q=processo teste délia) retornou zero matches naquele momento; 0 results NÃO prova ausência global.
- Não foi executado prepare_record_change, commit_proposal nem mutação real nesta auditoria.

Superfícies inspecionadas mostram: DAVI discover_delpi_information → candidate_token → execute; TÉO catálogo/guidance/read/prepare/commit; VISTA catálogo/guidance/análise/prepare/commit. **Não assumir que todos os MCPs tenham get_product_guide ou o mesmo schema.** A seleção deve usar semântica/capabilities vivas, sem branches por nome.

## Gaps prioritários — não apresentar hipóteses como fatos

| Gap | Estado | Evidência exigida |
| --- | --- | --- |
| Qual passo perde a intenção de orientar em vez de agir | TO_INVENTORY | trace goal→seleção→resultado e regressão com guia disponível/ausente |
| Como runtime usa guidance/catálogo owner | TO_INVENTORY | payload sanitizado, disponibilidade/contrato e escolha semântica |
| Validação suficiente em changes aninhado antes de ACT | PARTIAL_EVIDENCE / TO_INVENTORY | schema real owner, PREPARE e Decision gates, sem duplicação de autoridade |
| Inferência legítima vs default vs decisão humana | TO_INVENTORY | classificação com proveniência, materialidade, enum e confirmação |
| Conclusão “último” com data e ordem verificáveis | TO_INVENTORY | campo de criação, ordenação authoritative, cobertura de página e falhas |
| Integração runtime da personalidade | TO_INVENTORY | composition root, instruções efetivamente enviadas, multi-turn e evals |
| Evals reais no SHA/model/config/policy/dataset | TEST_NOT_RUN nesta trilha | suite positiva, negativa, adversarial, providers renomeados e outcome |

Não presuma git status local, deploy, modelos ativos, permissões ou backend de TÉO com base neste documento. GitHub remoto não informa working tree do Cursor. **Se o código atual divergir, STOP e classificar STALE_EVIDENCE.**

## Reuse-before-design — direção preliminar

EXISTING_EQUIVALENT=YES para Interaction Application, Model Invocation, instruções especializadas, capability orchestration, resolver, presentation, grounded synthesis e matriz canônica de testes. REUSE_DECISION=REUSE; EXTEND somente para gaps comprovados. Novo port/engine/provider/registry/prompt é TO_INVENTORY e exige Abstraction Gate e aceitação arquitetural. Ausência de resultado de busca nunca justifica NEW automaticamente.
