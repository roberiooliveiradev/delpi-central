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
