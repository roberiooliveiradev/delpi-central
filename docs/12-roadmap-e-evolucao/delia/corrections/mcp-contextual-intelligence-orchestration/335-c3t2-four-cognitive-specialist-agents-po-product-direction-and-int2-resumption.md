# 335 — DÉLIA C3/T2 — Direção PO: quatro especialistas cognitivos e retomada delimitada do INT-2

**Data:** 2026-11-14  
**Natureza:** PRODUCT DIRECTION / ARCHITECTURE DECISION REQUEST / DOCUMENTATION_ONLY  
**PO DIRECTION:** quatro responsabilidades cognitivas especializadas, com **quatro Agents especialistas como arquitetura-alvo**, trocando contratos tipados de contexto e evidência sob coordenação da DÉLIA.  
**STATUS:** TARGET RATIFICADO PELO PO; IMPLEMENTAÇÃO MULTIAGENT = NOT_AUTHORIZED; condição prévia do Doc 293 (experimento comparativo e Abstraction Gate) preservada, até decisão arquitetural formal de substituição.  
**REFERENCE DELIA SHA:** `62c33a11027a1407b19b4041e657464803148992` (Doc 334). **HEAD/phase:** revalidar Doc 16 + ledger a cada próxima tarefa; não inferir por este registro.  
**DEPLOY:** NOT_AUTHORIZED. **PHASE ADVANCEMENT:** NO.

## 1. Decisão de direção do produto

O PO confirma a intenção de compor a inteligência da DÉLIA por **quatro agentes especialistas cognitivos colaboradores**, não quatro produtos, autoridades, runtimes departamentais ou serviços obrigatórios. Eles deverão operar com separação de responsabilidade, contexto mínimo e handoffs tipados. A execução poderá ser condicional ao tipo de solicitação; não impor quatro chamadas LLM em série para todo pedido.

| Papel cognitivo alvo | Responsabilidade primária | Entrada/saída alvo | Limite de autoridade |
|---|---|---|---|
| **Especialista em Compreensão (INT-2)** | Entender o objetivo, entrega esperada, restrições, escopo solicitado e obrigações | Pedido e contexto autorizado → `SemanticInvestigationPlan` / objetivos/obrigações tipados | Proposta cognitiva; não comprova verdade, permissão nem cobertura |
| **Especialista em Investigação (INT-1)** | Selecionar capabilities governadas, consultar owners e coletar evidências, avançar por lacunas | Plano aprovado como contrato → tentativas e `Evidence` com provenance | Sem autorização autônoma; Core/Domain/Policy dominam |
| **Especialista em Suficiência (INT-3)** | Examinar lacunas, recomendar continuar/clarificar/parcial/concluir | Plano + evidências + cobertura → recomendação tipada | `_evaluate_material_obligations` / Application/Outcome são veredito autoritativo, não o Agent |
| **Especialista em Síntese (INT-4)** | Redigir resposta relevante, estruturada e fiel às evidências | Objetivo + outcome/evidência verificada → resposta e limitações | Não inventa FACT, não altera Outcome; CRI/structured binding governados |

**INT-5:** aceite integrado, não quinto Agent. A coordenação DÉLIA mantém decisões de percurso, estado e handoff sem duplicar planner. Handoff transmite apenas objetivo/obrigações, evidência necessária, progresso, referências e limitações; não expõe tokens, secretos, contexto excessivo ou chain-of-thought.

## 2. Reconciliar decisões anteriores — sem apagar histórico

- Doc 16 (decisão de 2026-11-10), Doc 293 §T2-INT e Doc 313 declararam **quatro responsabilidades, sem obrigação de quatro Agents** e fixaram **um Agent Pydantic AI como baseline de implementação**. Permanecem fatos históricos corretos, não devem ser reescritos retroativamente.
- **Nova direção PO de 2026-11-14:** arquitetura-alvo de quatro especialistas cognitivos distintos. Isto **altera o alvo de produto**, mas **não prova** que quatro execuções independentes são melhores, não concede novo boundary, não autoriza criação dos Agents 2–4 e não revoga automaticamente os gates de reutilização/experimento do Doc 293.
- Para promover TARGET a APPROVED IMPLEMENTATION: inventário real, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, contrato owner/consumer, comparação agente único versus variante mínima em cenários congelados, melhoria comprovada de task outcome/generalization/safety e custo/latência, Abstraction Gate e coordenação. Se a arquitetura-alvo conflitar com um contrato LOCKED superior, registrar `ARCHITECTURE_DECISION_REQUIRED`, não reconciliar silenciosamente.
- CP-071 (agentes/perfis especialistas selecionáveis ou convidados) é uma direção **distinta** desta especialização interna. Agente cognitivo, perfil user-facing, MCP e Agent delegado A2A não são sinônimos. Não reutilizar runtime/tabelas/services do Minha DELPI Chat.

## 3. Estado factual — não renomear estágios como Agents já construídos

| Estágio | Estado no Doc 334 | Agent especialista independente |
|---|---|---|
| INT-1 — investigação | **CLOSED/ACCEPT** (Doc 323) | Baseline Agent Pydantic AI existente (um único Agent) |
| INT-2 — compreensão | Implementação typed goal/delivery/obligation e `required_args` evidenciada, **FINAL ACCEPTANCE PENDING / INCONCLUSIVE** | **NÃO criado como Agent independente**; responsabilidade atualmente executada no Agent existente |
| INT-3 — suficiência | Mecanismos Application existentes; estágio dedicado ainda não autorizado | NÃO criado |
| INT-4 — síntese | Evidência `PROVEN_IN_SAMPLE`, aceite de estágio pendente | NÃO criado |
| INT-5 — aceite integrado | NOT_AUTHORIZED | Não é Agent |

**IMPORTANTE:** “Agent 2 quase pronto” é uma abreviação do **estágio INT-2 quase concluído**, não evidência de um segundo runtime/Agent existente. A mudança-alvo não invalida automaticamente o trabalho dos Docs 325–334. O atual `required_args` é uma proposta do modelo verificada mecanicamente; a integralidade do escopo pedido pelo usuário não é automaticamente provada só pela presença desse campo.

## 4. Próximo passo delimitado: aceitar INT-2 e estudar a variante especializada

**NEXT recomendado para coordenação:** `COORDINATION_C3_T2_INT2_BOUNDED_ACCEPTANCE_AND_FOUR_AGENT_TARGET_RECONCILIATION` — a executar somente após conferência de Doc 16 + ledger no HEAD.

Separar dois gates, sem confundi-los:

**GATE A — INT-2 (baseline existente, sem novos agentes).** Reconciliar AC canônicos (Doc 293/324, Docs 325–334): compreensão do objetivo, `expected_delivery`, `evidence_needed`, filtros/identidades quando declarados, generalização, segurança e proveniência. Marcar com precisão `ACCEPT / ACCEPT_WITH_RESIDUAL / REWORK / INCONCLUSIVE`. Não exigir prova universal da suficiência INT-3 ou quatro Agents para aceitar INT-2. Tratar omissão de `required_args` em pedidos filtrados como risco a delimitar e registrar, nunca como FULL_PASS automático.

**GATE B — Arquitetura-alvo multiagente (ainda sem implementação).** Comparar baseline único com variante mínima **Compreensão ↔ Investigação**, mesmos owners, modelos, permissões, corpus e orçamento; medir compreensão correta, escopo, primeiras ferramentas, resultado empresarial, falsas conclusões, recuperação, generalização, latência/tokens/custo e segurança. Somente se a comparação justificar ganho, propor Agents 2–4/handoffs tipados por decisão separada, sem novos authorities, planners ou providers específicos. Preservar os avaliadores determinísticos de suficiência.

## 5. Contratos antes de implementar delegação

Para qualquer Agent especializado candidato: owner, consumer, input/output, schema/versionamento, origem/freshness do contexto, Provenance/Evidence refs, correlação, errors, retries, timeout/budget, limites de tokens, idempotência, AuthZ/Policy, dados mínimos, observabilidade, isolamento, cancelamento, pós-condição, rollback/revoke e métricas de outcome. Pydantic AI native delegations só se comprovadamente necessárias. Integrar por ports/adapter aprovados; sem imports cruzando bounded contexts nem acesso a banco alheio. MCP/A2A fornecem interoperabilidade, não autoridade. No safety/physical ACT via LLM.

## 6. Matriz de autorização e evidência

```text
PO_FOUR_SPECIALIST_AGENTS_PRODUCT_DIRECTION = CONFIRMED_TARGET
CURRENT_RUNTIME_AGENTS = 1 (historical baseline; revalidate actual HEAD)
INT1_CLOSED = YES
INT2_ACCEPTED = NO (pending independent bounded acceptance)
INT3_INT4_SPECIALIST_RUNTIME = NOT_IMPLEMENTED / NOT_AUTHORIZED
FOUR_AGENT_ARCHITECTURE_APPROVAL = ARCHITECTURE_DECISION_REQUIRED
EXISTING_EQUIVALENT = YES (Pydantic AI + typed plans + Evidence + Outcome; inspect at implementation HEAD)
REUSE_DECISION = REUSE/EXTEND baseline; NEW requires comparative proof
PRODUCTION_DEPLOY = NOT_AUTHORIZED
PHASE_ADVANCEMENT = NO
EXECUTION_TESTS = TEST_NOT_RUN (DOC_ONLY)
```

**Documentos a reconciliar:** 16, 24, 25, 17, 20, 49, 50, Doc 293, Doc 324, Doc 334, ledger e residual register; manter históricos como registros da decisão de sua data. Atualizações de documentação são crosswalks e não ratificam implementação ou avanço de fase.

## Addendum 2026-11-14 — Veredito de coordenação persistido

A tabela do §3 registra o estado à data do documento e permanece como histórico. **Atualização vigente:** a coordenação revisou o SHA `d6e0c8e7664bf9d22858bc4e522451b4d3951af8` e decidiu `INT2_FUNCTIONAL_ACCEPTANCE = ACCEPT_WITH_RESIDUAL` / `INT2_FUNCTIONAL_CLOSED = YES` — o **estágio** de Compreensão está funcionalmente fechado no baseline de um Agent, o que **não altera** `INT2_INDEPENDENT_AGENT_IMPLEMENTED = NO`. A distinção estágio-aceito × Agent-independente mantém-se. Residuais delimitados no residual-register; próximo passo: `COORDINATION_C3_T2_INT3_BOUNDED_AUTHORIZATION_DECISION` — o INT-3 (Suficiência) teve requisitos, equivalentes existentes e fronteira cognitivo↔determinístico inventariados no Doc 17/Doc 20, **sem implementação autorizada**.

## Addendum 2026-11-14 — PO determina primeira separação física: Compreensão ↔ Investigação

**DECISÃO PO — DIREÇÃO DE IMPLEMENTAÇÃO FUTURA:** o segundo Agent físico desejado será **Compreensão (INT-2)**, separado do Agent Pydantic AI de **Investigação (INT-1)** já existente. A expressão “Agent 2 da investigação” deve ser entendida como o **segundo Agent do conjunto cognitivo**; não existem dois Investigadores autorizados. Os especialistas mantêm responsabilidades delimitadas. INT-3 Suficiência e INT-4 Síntese continuam TARGET de especialistas futuros; INT-5 continua aceite integrado. O usuário deseja desenvolver a especialização ao continuar corrigindo R2–R6, sem deixar todos os trabalhos cognitivos no Investigador.

**Fronteira pretendida:** Compreensão propõe `SemanticInvestigationPlan`/`MaterialObligation`; Application valida objetivo/escopo/contratos e mantém Policy/Decision; Investigação executa discovery e READ por MCPToolset governado com plano aceito; Evidence/Outcome verificam coverage/real business result. Agentes não autorizam, não invocam mecanicamente por nome fixo de provider e não compartilham secrets/CoT/histórico integral.

**Requisitos anteriores permanecem vinculantes:** TARGET confirmado **não é implementação nem autorização de novo Agent**. Doc293 exige comparação A/B (Agent único versus variante Compreensão→Investigação), Abstraction Gate, contracts/consumers, generalization+safety+task outcome+custo/latência antes da decisão de runtime. `EXISTING_EQUIVALENT=TO_INVENTORY` para handoff e `REUSE_DECISION=REUSE/EXTEND` para baseline; STOP se contrato novo/authority for necessário sem aprovação. R1 `ACCEPT_WITH_RESIDUAL` persistido; R2–R6 e resultados integrados ainda pendentes. Nenhum código ou deploy nesta task. **NEXT=`COORDINATION_C3_T2_COMPREHENSION_INVESTIGATION_SPLIT_EXPERIMENT_AUTHORIZATION_AND_R2_DEPENDENCY_GATE`.**

## Addendum 2026-11-14 — Autorização de experimento físico de dois Agents (PO)

**PO EXPLICIT AUTHORIZATION:** implementar **somente variante isolada/flag-gated** do segundo Agent cognitivo, **Compreensão/INT-2**, com o Agent de **Investigação/INT-1 existente** e validação de plano tipado pela Application. `EXPERIMENT_IMPLEMENTATION=AUTHORIZED`; `PRODUCTION_PROMOTION=NOT_AUTHORIZED`; `CURRENT_RUNTIME_AGENT_COUNT=1` até execução comprovada. Gate histórico do Doc 293 permanece aplicável **para promoção**; esta decisão autoriza produzir a evidência comparativa A/B, não a substitui. **TASK=`DELIA-C3-T2-TWO-AGENT-ISOLATED-AB-IMPLEMENTATION-AND-REAL-EVALUATION-01`**, próximo review `COORDINATION_C3_T2_TWO_AGENT_AB_INDEPENDENT_ACCEPTANCE_REVIEW`. Sem mudança de authority, novo planner ou estrutura de domínio; R2–R6 mantidos abertos.

## Addendum 2026-11-17 — Continuidade aprovada pelo PO: quatro camadas, dois Agents experimentais e diagnóstico por fronteira

**DIREÇÃO VIGENTE:** preservar o TARGET de quatro especialistas cognitivos INT-2 Compreensão, INT-1 Investigação, INT-3 Suficiência e INT-4 Síntese, com INT-5 como aceite integrado. A arquitetura-alvo não impede sub-agentes futuros legitimamente aprovados, nem implica quatro invocações em todas as solicitações.

**STATUS ATUAL REVALIDADO PELO CÓDIGO E EVIDÊNCIAS:** dois Agents Pydantic AI em variante experimental, executados sequencialmente: Compreensão propõe e Application aceita SemanticInvestigationPlan/MaterialObligation; Investigação recebe o mesmo plano aceito, contexto autorizado mínimo e budget restante, sem ferramentas owner READ no Agent de Compreensão. Produção permanece em baseline de um Agent com flag experimental OFF; INT-3/INT-4 não possuem Agents independentes. Esta atualização de estado não altera os registros históricos anteriores desta página.

**Mudança na estratégia de evolução:** encerrar a repetição de inventários arquiteturais genéricos. Usar os problemas já conhecidos e a primeira fronteira divergente em cada execução para aperfeiçoar de modo incremental: (1) INT-2 e handoff para INT-1; (2) seleção e continuidade INT-1; (3) distinguir lacunas de investigação de falhas da Suficiência determinística INT-3, preparando futuro especialista sem implementá-lo implicitamente; (4) distinguir problemas da resposta final atribuíveis à Síntese INT-4, sem antecipar seu Agent. Evidência de uma falha numa etapa não autoriza transferir sua responsabilidade para outro especialista.

**Ordem e interações:** Compreensão→Investigação continua serial porque a segunda depende de plano aprovado. INT-3 futuro propõe continuidade/clarificação/parcial/conclusão, mas Application decide e governa eventual novo ciclo de INT-1; INT-4 futuro usa apenas Evidence/Outcome aceitos. Paralelismo e sub-agentes somente se houver tarefas independentes e decisão específica sobre contrato/budget/AuthZ; sem segundo planner, engine, MCP registry ou autorização por output de LLM.

**Problemas-alvo conhecidos:**
- Fechado no escopo comprovado: diferença indevida de envelopes multipágina R2-CONTINUITY-MULTIPAGE-GROUP-SPLIT, parâmetros opacos de required_scope, união R5 em amostra e proteção contra união com filtros materiais divergentes.
- Aberto e prioritário: convergência cognitiva do loop de paginação/no-progress sob budget; confiabilidade do handoff e T2-B-COMPREHENSION-AGENT-ERROR; seleção de capability/argumentos e qualidade do resultado empresarial relativo ao baseline único.
- Distintos, não mascarar: demonstração parcial de âncoras INT-3; AuthZ negativa real R4 dependente de identidade restrita e R6-N6/N7; VISTA TO_INVENTORY; delpi-verifier formal pendente (Devin standalone auth/Cursor quota).

**Teste de aceitação funcional:** mesmo corpus congelado A=Agent único/B=dois sequenciais, com modelo, catálogo, identity, regras de AuthZ, versão de instrução e orçamento comparáveis; analisar em sequência plano proposto→plano aceito→handoff→invocações MCP→cobertura/progresso→Suficiência→resposta publicada; medir acerto de intenção/escopo, primeira capability, paginação, GROUNDED, SATISFIED corretamente, falso COMPLETE, writes/AuthZ, consumo e latência. Não atribuir diferenças estocásticas ao split sem A/B equivalente. Corrigir somente a primeira falha comprovada por RED/GREEN/regressão/eval real; não criar novas abstrações técnicas.

**NEXT CANDIDATO, subordinado a Doc 16 + ledger:** COORDINATION_C3_T2_TWO_AGENT_LAYERED_HANDOFF_AND_FUNCTIONAL_RECOVERY. Não autoriza novo runtime INT-3/INT-4, deploy ou avanço de fase; mantém verifier independente e review de coordenação como gates.


## Addendum 2026-11-18 — Plano PO de cinco frentes: consolidação INT-2/INT-1 antes de novos especialistas

**STATUS: PLANNED / DOCUMENTATION_ONLY.** Remissão obrigatória ao Documento 16 (addendum 2026-11-18), com fase e NEXT regidos por 16+ledger, sem reescrever os parágrafos históricos desta especificação. Direção explicitamente aprovada pelo PO: (F1) qualidade da Compreensão; (F2) continuidade da Investigação; (F3) aprofundamento da responsabilidade de Suficiência; (F4) segurança/generalização/aceite; (F5) estudo de qualidade da Síntese. Cada frente necessita task bounded, CP/RQ, gates e evidências próprias antes de implementar. F4 é também gate transversal de F1, F2, F3 e F5.

**Baseline factual:** INT-2 e INT-1 são dois Agents Pydantic AI sequenciais somente em experimento; Application aceita SemanticInvestigationPlan e MaterialObligation; Evidence/Outcome autoritativos. F3/F5 NÃO autorizam Agents INT-3/INT-4. INT-5 permanece aceite integrado, não Agent; produção continua baseline um Agent, flag two-agent OFF. Última amostra Qwen3-14B 9×2 A=6/9, B=6/9 GROUNDED; INT2_B B recuperado para GROUNDED/SATISFIED (109). Correção de âncora de apresentação e feedback bounded de insufficiency verificadas em amostras; independent verifier Cursor r2 ACCEPT_WITH_RESIDUAL após reconciliação do SHA histórico, ainda com resíduos de pytest independente e CI remota. Evidência: evidence/c3-t2-anchor-recovery/ e ledger. A paridade NÃO prova superioridade do split.

**Boundaries de execução:** F1 só corrige operação/âncora/handoff com falha reproduzida, preservando explicit material constraints; F2 continua READ MCP e orçamento por mecanismos Pydantic AI, sem loop paralelo; F3 aprimora diagnóstico/comunicação de lacunas mas não relaxa Suficiência determinística; F4 depende de Core/Domain para identidade restrita real, R4/R6 negativos, e prova generalização+segurança; F5 mede output de Síntese atual ANTES de qualquer proposta de Agent novo. Não inferir que um nome de operação/capability define autoridade ou satisfaz obrigação; apresentação do usuário vs estratégia do modelo devem permanecer distintas. EXISTING_EQUIVALENT/REUSE_DECISION, Abstraction Gate, RED/GREEN, avaliação real no SHA/config, verificador independente e decisão de coordenação obrigatórios em todas as frentes.

**Próxima task candidata:** COORDINATION_C3_T2_COMPREHENSION_OPERATION_ANCHOR_AND_HANDOFF_RELIABILITY_GATE (F1, diagnóstico primeiro). Residuais: T2-COMPREHENSION-OPERATION-ANCHOR OPEN_LOW, T2-B flake, continuidade/no-progress/budget, INT3-OBLIGATION-DEMONSTRATION-DEPTH OPEN_LOW, R4 identidade restrita e R6-N6/N7 PENDING, VISTA carrier TO_INVENTORY, CI/verifier residual. Não fechar ou reclassificar residuais pela atualização documental. PRODUCTION_DEPLOY=NOT_AUTHORIZED; TWO_AGENT_PROMOTION=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NO.
