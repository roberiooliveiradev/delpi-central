PEDIDO DE VERIFICAÇÃO
objetivo: DELIA-C3-T2-ENTITY-SUFFICIENCY-HTTP-MULTITURN-AND-VERIFIER-ACCEPTANCE-01 — fechar três gaps: (1) congruência de entidade empresarial na agregação de apresentação; (2) E2E HTTP real de dois turnos via POST /interaction/turns + context canônico (não harness prior_turns); (3) verificação independente com texto integral RQ-1 até RQ-14 e AC-1 até AC-22 + pytest executável. COMMIT/PUSH autorizados no escopo. PRODUCTION_DEPLOY / TWO_AGENT_PROMOTION / PHASE_ADVANCEMENT / Agents 3–4 NOT_AUTHORIZED. WIP concorrente preservado.

# 4. REQUISITOS NUMERADOS

## RQ-1 — Reancoragem e inventário

Identificar a implementação efetiva no HEAD, seus contratos, owners, consumers, testes e decisões congeladas.

## RQ-2 — Congruência da entidade empresarial

Garantir que uma evidência somente satisfaça uma obrigação quando comprovar o mesmo objeto de negócio solicitado, além dos filtros materiais e da métrica.

## RQ-3 — Equivalência contratual de representações

Preservar equivalências legítimas de apresentação, operação e containers de argumentos, sem permitir equivalência entre entidades diferentes.

## RQ-4 — Negativos de suficiência

Demonstrar que resultados de outra entidade, outro escopo, outro owner, outro filtro ou métrica sem pertinência permanecem `INCONCLUSIVE` ou `UNSATISFIED`, conforme contrato.

## RQ-5 — Grounding e Outcome

Preservar a distinção entre evidência fundamentada, obrigação demonstrada e resultado completo. Nenhuma declaração do modelo pode promover falsamente a resposta.

## RQ-6 — Boundary conversacional real

Executar dois turnos através da interface HTTP real da DÉLIA, utilizando o mecanismo de contexto conversacional da aplicação, não apenas o harness de avaliação.

## RQ-7 — Persistência e recuperação de contexto

Comprovar que a segunda requisição recupera o contexto correto pelo mecanismo canônico, com a mesma identidade autorizada e vínculo legítimo entre turnos.

## RQ-8 — Segurança conversacional

Comprovar que conteúdo do assistant não autoriza identificadores novos, que outro usuário não recupera contexto alheio e que permissões são revalidadas.

## RQ-9 — Generalização

Executar casos positivos, negativos e metamórficos, sem hardcodes de produto, especialista, pergunta ou resposta.

## RQ-10 — Regressão verificável

Executar os testes direcionados, integração, suíte DÉLIA aplicável e audits, com comandos, exit codes, contagem e logs completos.

## RQ-11 — Avaliação com modelo real

Executar a variante experimental de dois Agents com modelo e owners autorizados, coletando evidence, decisões e resposta publicada.

## RQ-12 — Verificação independente integral

Entregar ao `delpi-verifier` todos os textos dos RQ/AC desta task, executar até três rodadas e resolver as OCs sem editar o relatório do verificador.

## RQ-13 — Evidência autocontida

Publicar no GitHub os testes, os traces sanitizados, os contratos, os logs e a correlação entre afirmações e resultados.

## RQ-14 — Commit, push e CI

Publicar o estado verificado em `origin/main`, comprovar o SHA entregue, o status de CI e a integridade do escopo, sem deploy.

---

# 8. CRITÉRIOS DE ACEITE NUMERADOS

## AC-1 — Reancoragem

**RQ-1:** HEAD, origin/main, fase, NEXT, contratos e WIP comprovados.

## AC-2 — Ownership

**RQ-1, RQ-2:** owners, consumers e contratos identificados; `EXISTING_EQUIVALENT` e `REUSE_DECISION` registrados.

## AC-3 — Entidade correta

**RQ-2:** uma obrigação de processos não é satisfeita por métrica de pedidos, produtos ou outro objeto de negócio.

## AC-4 — G2 positivo

**RQ-2, RQ-3:** `teo.read` autoritativo demonstra a contagem de processos ativos com filtro material correto.

## AC-5 — Equivalência legítima

**RQ-3:** `summary/analysis` versus READ e `params/arguments` somente são equivalentes dentro de contrato legítimo.

## AC-6 — Negativos de suficiência

**RQ-4:** S2–S11 classificados corretamente, sem falso SATISFIED ou COMPLETE.

## AC-7 — Grounding

**RQ-5:** não confundir GROUNDED com obrigação satisfeita ou conclusão completa.

## AC-8 — Publicação factual

**RQ-5:** texto publicado corresponde ao resultado autoritativo demonstrado.

## AC-9 — HTTP real

**RQ-6:** dois requests ao boundary HTTP real são executados e registrados.

## AC-10 — Mesmo contexto

**RQ-6, RQ-7:** segundo turno recupera contexto autorizado da mesma conversa pelo mecanismo real.

## AC-11 — Clarificação correta

**RQ-7:** turno 1 solicita apenas o dado necessário e não executa consulta indevida.

## AC-12 — Recuperação correta

**RQ-7:** turno 2 preserva objetivo, usa identificador informado e executa a capability autorizada.

## AC-13 — Evidência empresarial pós-turno

**RQ-7, RQ-11:** segundo turno entrega resposta fundamentada com evidência real do owner.

## AC-14 — Segurança multi-turno

**RQ-8:** contexto alheio, identificadores inventados e permissões inválidas não ampliam autoridade.

## AC-15 — Negativos conversacionais

**RQ-8, RQ-9:** M1–M10 executados ou bloqueados com classificação fiel ao contrato e à disponibilidade de identidades autorizadas.

## AC-16 — Generalização

**RQ-9:** testes metamórficos e reformulações demonstram comportamento não dependente do corpus.

## AC-17 — Testes

**RQ-10:** suíte direcionada e regressão aplicável verdes, com logs completos e exit codes.

## AC-18 — Modelo real

**RQ-11:** avaliação real com dois Agents no ambiente permitido, SHA e configuração rastreáveis.

## AC-19 — Pedido de verificação integral

**RQ-12:** o arquivo passado ao `verify.py` contém o texto completo dos 14 RQ e 22 AC, sem resumos ou intervalos abreviados.

## AC-20 — Verificação independente

**RQ-12:** veredito ACCEPT ou ACCEPT_WITH_RESIDUAL somente quando não houver residual crítico, omissão nominal de RQ/AC ou divergência de escopo.

## AC-21 — Pacote GitHub

**RQ-13:** traces sanitizados, logs, contratos, resultados e relatório disponíveis no GitHub com URLs reais e hashes.

## AC-22 — Entrega final

**RQ-14:** commit/push comprovados em main, CI aplicável verde no SHA entregue, nenhuma mudança material não verificada, nenhum deploy produtivo.

---


escopo: working tree
alegacoes:
- WS-1:  sob agregação de apresentação em semantic_capability_support.py; negativos S2 e S3 fail-closed; G2 live or-qwen14b-aca443baae46 GROUNDED+SATISFIED entity=process teo.read 109
- WS-2: dois POSTs reais /interaction/turns; context USER_INPUT+DELIA_RESULT; correlation http-mt-42e226d1432a; TURN2_GROUNDED com davi get_product_structure 90260921 CHICOTE; negativos M1, M2, M4, M5, M10 pytest PASS; M3, M6, M7, M8, M9 PENDING
- Env: V024 restaurado ao checksum aplicado 8f9c97 para desbloquear DAVI (DEV restart api-delpi); sem deploy prod
- Testes: directed 29 PASS; regression 119 PASS
- Evidência: docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-entity-sufficiency-http-multiturn-verifier/
- Escopo de stage pretendido: delia-api (support+tests+scripts HTTP) + V024 restore + evidence package; excluir WIP api-delpi/engineering/tv-dashboard concorrente
modelo_executor: Composer
rodada: 1
comandos_verificacao:
- docker exec delpi-delia-api python -m pytest -q tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py tests/test_c3_t2_http_multiturn_boundary.py
- docker exec delpi-delia-api python -m pytest -q tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py tests/test_c3_t2_http_multiturn_boundary.py tests/test_interaction_runtime.py tests/test_mcp_provider_eligibility_revalidation.py
artefatos:
- docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-entity-sufficiency-http-multiturn-verifier/
- delia-api/.battery/c3-t2-http-multiturn-live/http-multiturn-live.json
- delia-api/.battery/int1-secure-decision-trace/or-qwen14b-aca443baae46/INT2_G2_aggregation_active_scope.jsonl
