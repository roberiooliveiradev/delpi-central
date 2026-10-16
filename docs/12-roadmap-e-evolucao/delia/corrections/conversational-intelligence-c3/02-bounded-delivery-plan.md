# 02 — Plano das seis entregas bounded

**Status:** PLAN_REANCHORED_2026-10-16: Etapa 01 EVIDENCE_RECORDED (§6.171) + INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL (§6.172); 02 IMPLEMENTATION_REWORK (§§6.174/6.176); B1 PASS estrutural e B2 REWORK; diagnóstico R2 ACCEPT_WITH_RESIDUAL somente como evidência (§6.178), ARCHITECTURE_DECISION_REQUIRED; 03–06 PLANNED/NOT_AUTHORIZED.  
**Umbrella:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01.  
**Regra:** uma etapa por entrega e review, sem “um prompt corrige tudo”; implementação só após reanchor e autorização; nenhum novo planner/agent/engine por conveniência.

**PRECEDÊNCIA:** [05 — Revisão canônica](./05-canonical-decisions-alignment.md) registra as decisões superiores dos §§6.126/6.130/6.133/6.140/6.141/6.145. Um problema de conversa NÃO autoriza reabrir ownership/contratos congelados. Contradição → STOP / ARCHITECTURE_DECISION_REQUIRED / EXECUTION_DRIFT.

## Resultado esperado

Uma única DÉLIA que entende o pedido, descobre capacidades autorizadas, verifica conhecimento e dados do owner, resolve o que é resolúvel, pergunta só o essencial, comunica inferências como inferências e entrega respostas úteis, naturais, fundamentadas e governadas. Não é objetivo tornar o LLM fonte de dados empresariais ou autoridade de execução.

## Etapa 01 — Baseline factual e harness de eval

**ESTADO REAL:** Relatório [04](./04-stage-01-baseline-report.md) + harness registrados no ledger §6.171; 15 testes fake/scripted e 1069/1069; INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL (§6.172, [06](./06-stage-01-independent-review.md)). O texto abaixo conserva o escopo original, não afirma qualidade real do modelo nem autoriza reiniciar a etapa.

**Problema:** não há baseline único reproduzível dos defeitos de intenção, orientação, argumentos e síntese no mesmo SHA/config.  
**Ação candidata:** inventariar instruções realmente enviadas ao modelo e caminhos de fallback; reproduzir casos de TÉO sem mutação e owners fake, com logs redigidos, traces e expected outcomes; mapear CP/RQ/AC reais à matriz 25/20; reutilizar harness existente.  
**Entrega:** relatório por falha com stage/call contract/expected/actual/root cause PROVEN ou TO_INVENTORY; conjunto de testes baseline; thresholds só depois da medição.  
**Gate:** não iniciar refactor sem distinguir falha de intent, selection, discovery, schema, evidence, response e apresentação. **Sem ACT real.**

## Etapa 02 — Intenção, finalidade e instruções bounded

**ESTADO:** implementação publicada em [07](./07-stage-02-implementation-report.md), commit `4a9f05e5b9bd2b40332638d5bec49678de050bdd`, review independente [08](./08-stage-02-independent-review.md) = **REWORK** (§6.174). Bloqueios B1 (interpretação ausente ainda permite PREPARE) e B2 ('prepare, mas não aplique' não prova teto sob owner direct). R1 foi implementado ([09](./09-stage-02r1-rework-implementation-report.md)) e revisado ([10](./10-stage-02r1-independent-review.md)): B1 passou estruturalmente, B2 depende exclusivamente da proposta de bound correto do LLM e ainda permite ACT direto se `execution_bound=unrestricted` em texto 'não aplique'. `REWORK` (§6.176), com ARCHITECTURE_DECISION_REQUIRED se solução envolver novo contrato/gate. Não avançar para Etapa 03 nem alterar owner confirmation policy. O diagnóstico R2 [11](./11-stage-02r2-execution-bound-diagnosis.md) e sua revisão [12](./12-stage-02r2-independent-review-and-decision-request.md) confirmam ACT sob texto negativo quando modelo retorna `unrestricted`. C (ausente/inválido fail-closed) é mitigação parcial; não resolve misclassification positiva. Decisões D1/D2/D3 do relatório 12 pendentes, sem autorização de novo gate. A revisão de contrato/segurança [14](./14-execution-scope-contract-security-review.md) registra proposta de separação TASK_INTENT / ACT_ELIGIBILITY / OWNER_CONFIRMATION, com trade-off explícito de §6.140; `CONTRACT_PROPOSAL=NOT_APPROVED`, nenhuma implementação autorizada. O Product Master aprovou **apenas a regra** `TEXT_ONLY_AND_NO_OPERATION_BOUND_EXECUTION_CHOICE → MAX_MATERIAL_STAGE=PREPARE` (§6.183, [17](./17-product-decision-text-only-prepare-until-scoped-execution-choice.md)); D1 contrato técnico, D2/D3 e gaps G1–G5 permanecem sem freeze e sem implementação autorizada.

**Problema:** a seleção pode perder a finalidade do usuário; pedir orientação não é solicitar uma escrita.
**Investigação/correção candidata:** avaliar a coerência entre _select_target, _understand_goal, _assess_native_path, instruções e gates atuais. No runtime presente, seleção precede goal estruturado; **novo goal_class orient e reorder goal-before-selection NÃO são decisões aprovadas**. Reutilizar contratos existentes e provar necessidade/impacto antes de propor mudança de contract ou ordem.
**Entrega:** testes com orientação, criação, formulações ambíguas, multi-turn e owners/tools renomeados; comparar baseline e candidate, segurança, custo, latência e generalização.
**Gate:** não iniciar PREPARE por mera palavra 'criar'; sem novo planner, agent, instruction ID, superprompt ou branch por provider; nenhuma alteração de discovery, Domain contract, synthesis ou personalidade nesta etapa.

## Etapa 03 — Discovery e guidance provider-neutral

**Problema:** o conhecimento/vocabulário disponível do owner pode não ser apresentado às etapas que precisam dele; string sem enum não implica vocabulário fechado.
**Investigação/correção candidata:** consumir authenticated live tools/list como superfície primária (§6.126); quando houver capabilities pertinentes e autorizadas de DISCOVERY/get_catalog/guidance, buscar somente contexto necessário. Não criar um get_product_guide obrigatório para todos os MCPs, catálogo local nem tratar erro/texto owner como instrução confiável.
**Entrega:** guidance disponível/ausente, campo string livre vs enum owner, tool renomeada, live add/remove/reclassify, falso quarto owner, orçamento bounded.
**Gate:** zero hardcode TÉO/DAVI/VISTA; zero discovery universal de strings, authority do owner preservada, nenhum ACT por guia.

## Etapa 04 — Completude, resolução e diálogo mínimo

**Problema:** validar input_schema externo não comprova completude de changes internos; o resolver já aprovado pode não receber o gap.
**Investigação/correção candidata:** estender _build_arguments, _resolve_missing_inputs e _clarification_question com contratos autoritativos recebidos do owner, sem copiar Domain rules; usar resolver non-mutating same-owner (DISCOVERY|READ|ANALYSIS) com no máximo três steps (§6.140); preservar invented-id fail-closed e ambiguidade→CLARIFICATION_REQUIRED. Distinguir dados explícitos, defaults declarados, propostas de inferência e decisão humana.
**Entrega:** casos nested required, contratos incompletos, fallback seguro, preferência de perguntar apenas o necessário, PREPARE READY/NOT_READY, validação final owner e postcondition.
**Gate:** confirmar conforme PREPARE selado: true→confirmação; false→direct governado; inválido→WRITE_REJECTED. **Não** confirmação universal, default inventado, Domain validator paralelo ou ACT sem Core/Domain/AuthZ/Policy/Decision/idempotência/audit.

## Etapa 05 — Resposta fundamentada, conversa e personalidade

**Problema:** seleção de campos e rendering determinístico podem ser verdadeiros sem responder à intenção ('último', comparações), e a personalidade aprovada não tem runtime integral provado.
**Investigação/correção candidata:** aprimorar suficiência, ordenação/cobertura legítima, limitations, formato de resposta e integração do comportamento personality/02..04 nos componentes já existentes.
**Entrega:** respostas proporcionais, fonte e insuficiência honestas, multi-turn, preferências temporárias e clareza sem exposição desnecessária de campos técnicos.
**Gate:** §6.145 MODEL_AUTHORED_FACTUAL_PROSE=NONE permanece; owner é fonte factual, DÉLIA renderer determinístico, persona não concede FACT, memória, autorização ou ACT.

## Etapa 06 — Generalização, segurança e aceite independente

**Problema:** suite pytest green com model proposals scripted não é prova de qualidade/Outcome do LLM real.
**Ação candidata:** reusar matriz 20, CP/RQ em 25, PERS-AC aplicáveis e provas de §6.141; testar casos positivos, irmãos, negativos, adversariais, holdout, owner/tool renames, MCP e não MCP, sem guidance, AuthZ, PREPARE/ACT e verdadeiro task outcome quando autorizado.
**Entrega:** relatório por SHA/config/model/provider/policy/dataset com denominadores, latência, tokens/custo, falhas honestas, generalização e revisão independente.
**Gate:** não importar harness/runtime do Minha DELPI Chat, não autoaceitar, não liberar C4/C5/C3 por documentação, não trocar segurança por naturalidade.

## Política de orçamento e número de instruções (não criar prompts infinitos)

- Reutilizar os instruction IDs/ports/stages já existentes. O inventário da Etapa 01 reportou 13 instruction IDs + instrução base, mas isso não congela um número ideal; qualquer novo ID exige necessidade demonstrada, contrato, custo e eval. Regra padrão: **zero novos prompts para cada provider ou entidade**; qualquer novo instruction ID depende de equivalente inventariado NO e Abstraction Gate.
- Não criar um “superprompt” que replique todos os owners e esquemas; carregamento de contexto relevante por discovery/owner no momento necessário. Não assumir tool descriptions como instructions system.
- Preservar inicialmente bounds existentes: MAX_OPERATIONAL_PLAN_STEPS=3, MAX_REPLAN_ROUNDS=1, MAX_SURFACE_CHARS=6000, MAX_ARGUMENTS_BLOCK_CHARS=14000. Alterações desses números exigem evidência de qualidade/custo/latência e review — estes limites não foram congelados como política nova.
- Medir por stage chamadas de modelo, custo, latência, truncation, taxa de esclarecimento desnecessário e task outcome. Definir limite superior mensurável do prompt/contexto total **na Etapa 01**, após inventário; não inventar um número agora.
- Critério de otimização: menor path suficiente (FAST determinístico; OPERATIONAL regras + contexto; REASONING somente investigação complexa), sem CoT exposta/persistida.

## Protocolo de cada entrega para Devin

1. Coordenação reancora HEAD/git status/authorities/ledger e identifica a etapa NEXT vigente; confirma objetivo bounded e owner.
2. Especialistas de AI e Backend mapeiam CP/RQ, consumers, instruction contracts, expected fields, Core/Domain gates e fixtures relevantes.
3. Provar EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY e REUSE_DECISION=REUSE|EXTEND|NEW; reusar por boundary. Qualquer ADR ou drift retorna à coordenação.
4. Aprovar prompt de implementação **somente para aquela etapa**; aplicar o menor diff; executar testes/evals com baseline e holdout.
5. Entregar report com base/final SHA, diffs, contract compatibility, reprodutores e regressões, resultados de segurança, limites e evidência de outcome; review independente.
6. Atualizar ledger canônico factual **após** testes/review. Só então refletir status nesta pasta e planejar o próximo prompt bounded.

Códigos de etapa aqui são rótulos documentais (01–06), não tarefas implementadas nem novas autoridades sobre 16/ledger.
