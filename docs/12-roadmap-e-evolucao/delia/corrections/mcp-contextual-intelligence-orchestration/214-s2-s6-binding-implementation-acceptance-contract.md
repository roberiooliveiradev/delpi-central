# 214 — Contrato vinculante de entrega S2–S6: implementação integral e aceite independente

- **Estado:** APPROVED_EXECUTION_SCOPE / NOT_IMPLEMENTED. Critérios fixados pela coordenação; não significam PASS.
- **Data:** 2026-11-01. **Baseline de planejamento:** Documento 213 (Task 37, `9c50cfb580`); revalidar HEAD antes de executar.
- **Autoridades:** Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura técnica, product spec, tema, ledger. Em conflito, superior prevalece e exigir drift.
- **Planos existentes a reutilizar, não duplicar:** 210 (plano vivo), 211 (28 questões congeladas), 212 (comparação Pydantic AI e recovery), 213 (inventário e target).
- **Responsabilidade:** DÉLIA coordena Evidence/Policy/Decision/Work/Outcome; Core AuthZ; Domain APIs facts/rules; MCP owner schema+erro tipado; Keycloak identidade; Automation Hub execução técnica; LangGraph/Pydantic AI adapters de infraestrutura.
- **Objetivo:** concluir *implementação real* S2–S6, com aceite binário baseado em provas, não repetir somente inventário nem renomear código anterior como entrega nova.

## 0. Regras inegociáveis de execução

1. Antes de código, reancorar `git status`, HEAD/origin/main/worktrees, Project Instructions/.cursor e autoridades na ordem canônica. Registrar fase CP/RQ e contratos reais.
2. Para qualquer nova capability/port/adapter: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`; `REUSE_DECISION=REUSE|EXTEND|NEW` com prova. `TO_INVENTORY` não autoriza NEW.
3. **Entregue significa código funcional+RED/GREEN+runtime evidence no SHA avaliado.** Documento, teste unitário mockado, protótipo solto ou código prévio sozinho não é entrega S2–S6.
4. Resolver internamente erros de implementação, dependências, builds e regressões dentro dos boundaries aprovados; não reabrir a cada problema. Em falta de credenciais/dados/autoridade, não inventar, não fazer bypass, marcar `INCONCLUSIVE/BLOCKED` e continuar frentes independentes.
5. Não encerrar a tarefa voluntariamente antes dos gates. Se limite de contexto/sessão impedir conclusão, gravar no GitHub handoff factual: estado, paths, SHA, testes, próximos comandos, e registrar `INCOMPLETE`; outro executor continua do checkpoint, sem reiniciar inventário. Nunca declarar ACCEPT unilateralmente.
6. **Nenhum deploy produção, nenhum WRITE empresarial.** Somente READ/ANALYZE e fixtures/sandbox autorizados. Fazer stage explícito dos próprios paths e preservar workstreams concorrentes.
7. Testes GREEN devem incluir regressão e adversariais. Zero AUTHZ bypass, ACT indevido, fabricação, metadata/owner authority spoof, segredos no prompt/log, replay de writes ou persistência de chain-of-thought. Qualquer ocorrência é FAIL eliminatório.
8. Pydantic AI é candidato bounded, não obrigação cega. Sua adoção requer benchmark superior ao baseline ou ganho de manutenção mensurável com não regressão. Decisão `NOT_ADOPT` só após teste A/B executável, não após opinião. LangGraph é candidato principal conforme 213, mas mudanças devem validar locks/autoridades.

## 1. Congelamento de baseline e rastreabilidade

Criar matriz inicial: HEAD/SHA, versões, modelo/quantização/config, perfis autenticados, owners, topologia local, graph paths, custos/tokens/latência, 15 incidentes T34, 28 perguntas do doc 211 (não executar homologação 84 aqui), testes existentes, dead code, contracts. Capturar resposta literal em eval técnico local sob acesso autorizado; não publicar dados sensíveis no GitHub.
Definir oráculos RED antes de alterar os caminhos; estruturar trace com stages `objective/subobjective/discovery/arggen/validation/invoke/owner_error/recovery/evidence/continuation/synthesis`. Não atribuir a LLM ou owner sem comparador causal.

## 2. S2 — Propostas de argumentos tipadas, contrato-aware

**Objetivo obrigatório:** gerar e reparar argumentos respeitando `inputSchema` dinâmico real; não inferir enums no cliente; não forçar função por nome de owner.

Entregas:
- Benchmark A (mecanismo atual T23/T36) vs B (Pydantic AI structured output isolado por adapter existente) usando mesmos 15 incidentes causais, variantes unseen independentes e ao menos 2 modelos/configs quando disponíveis. Capturar inputs, argumentos originais, falha, hint seguro, nova proposta, resultado, tokens, latency e overhead.
- Roda real dos paths de proposta inicial **e** re-proposta, sem segunda agent engine. Escolher backend por composição local (se B adotado), fallback/rollback determinístico. Nenhum import de Pydantic AI em Domain/Application.
- Validar campos required, enum, type, additionalProperties, nested, discriminador, nulidade; quando schema do owner insuficiente, `SCHEMA_INSUFFICIENT`, sem inventar valores. Owner 401/403/policy/business/transporte não é argumento retry.
- Limite global + por ferramenta + dedup + deadline; nenhuma reexecução de ACT/WRITE via retry.

**Aceite S2:** (a) testes RED reais existentes + held-out; (b) testes negativos green; (c) não-regressão de validade/Business Outcome no corpus de argumentação; (d) A/B + decisão `ADOPT_BOUNDED` ou `NOT_ADOPT` justificada por métricas; (e) execução pelo fluxo da DÉLIA, não só harness isolado; (f) ambiente novo pode trocar mechanism/LLM por config sem alterar Application. Não exigir taxa artificial; qualquer piora sem causa resolvida bloqueia aceite.

## 3. S3 — Subobjetivos explícitos e continuidade semântica

**Objetivo obrigatório:** quando o objetivo original tiver múltiplos requisitos, a investigação acompanha subobjetivos com `id/goal/dependencies/evidence_needed/state/attempts/evidence_refs/gaps`; reusa estado canônico se existir.
Estados fechados propostos (ajustar ao contrato canônico, documentando): `PENDING, READY, IN_PROGRESS, COMPLETED, PARTIAL, BLOCKED, FAILED`. Nunca marcar COMPLETED por tool 200/catálogo/resposta genérica.

- Planner LLM propõe passos/capabilities semânticas; Domain/App governam gates/budgets; mechanics ficam nos adapters.
- Após evidência insuficiente/erro recuperável, reavaliar requisitos pendentes e continuar com a capacidade já aprovada ou nova discovery governada. Não fazer keyword regex ou hardcode CAIO etc.
- Proibir nova chamada sem progresso, tratar indisponibilidade legítima como lacuna; cap por investigação e subobjetivo.
- Checkpoints/turnos preservam contexto mínimo e referências verificáveis; não CO T nem chain-of-thought.

**Aceite S3:** E2E READ local de pelo menos (i) pergunta com 2+ subobjetivos em 1 owner, (ii) pergunta 2+ owners autorizados, (iii) resultado parcial sem dados (conclui PARTIAL com lacuna), (iv) erro recuperável segue e completa, (v) erro não recuperável permanece fail-closed; trace confirma plano→progresso→evidence→conclusão sem inventar. Guardar respostas **literais** e oráculos.

## 4. S4 — Paralelismo governado LangGraph

**Objetivo obrigatório:** utilizar ou justificar não utilizar `Send` e reducers nativos para fan-out/fan-in de **subobjetivos independentes**, não apenas fan-out de listas de especialistas. Respeitar a topologia real e legalidade do graph atual.

- Dependências impõem sequencing; zero exec antes da autorização; contexts separados; resultados com refs e merge determinístico; branch errors isolados; budget **global atômico/concorrente**, sem corrida ou reset; concurrency cap configurável.
- Executar cenários técnicos com 3 ramos READ: independente, serial dependente, misto, um timeout e um partial failure; medir baseline sequential/custom e solução nativa: wall time, tokens, invokes, memória, completion/coverage. Não supor ganho GPU 6GB.
- Preservar paths existentes que não beneficiam de paralelo; rollback por config. Se `Send` não puder ser usado legalmente, produzir teste conclusivo e implementação equivalente preferindo recurso nativo aprovado, não apenas "candidato".

**Aceite S4:** prova real no graph DÉLIA de fan-out/fan-in de subobjetivos, ordem correta de dependências, merge estável, resultados parciais corretos, cancelamento/timeouts e limite global sob concorrência; benchmark comparativo; sem ACT.

## 5. S5 — Checkpoint/resume durável

**Objetivo obrigatório:** integrar checkpointer da versão LangGraph efetivamente instalada no composition root existente, com isolamento por thread/investigation/identity/tenant, state version, TTL/retenção e segurança de dados; validar `SqliteSaver` apenas em local apropriado. Antes de adicionar DB/port, provar solução existente e authority.

- Persistir somente IDs de objetivo, estados de subobjetivo, referências de evidência e contadores necessários; não persistir segredos, OAuth/JWT, CoT, metadata não confiável como autoridade.
- Revalidar Core live AuthZ e owner no resume; não reaplicar effects materiais. Provar resume após interrupção com nova instância/processo e estados intactos. Verificar migration/rollback para estado antigo.
- Política de dados de checkpoint e local física precisam estar aprovadas, fail-closed se não.

**Aceite S5:** E2E de interrupção + restart + resume no SHA/config; nenhuma perda indevida dos resultados READ anteriores; tokens não reemitidos desnecessariamente; usuários/tenant diferentes não acessam o estado; TTL/cleanup, authz revocation e corrupted state negativos; rollback.

## 6. S6 — Cobertura de evidências por requisito + síntese fiel

**Objetivo obrigatório:** EvidenceFacts/Outcome oficiais classificam cada subobjetivo como `SATISFIED / PARTIAL / UNSUPPORTED / CONTRADICTED` ou vocabulário canônico equivalente; agregar com referência autoritativa e período/unidade/scope. Não criar segundo Truth Store.

- Testar eventos com 2 MCP owners, amostras paginadas, dados contraditórios, scope divergente, catálogo-only, HTTP200 com payload vazio, ausência de denominador, recomendação vs fato.
- Resposta final deve citar fatos comprovados, declarar lacunas e nunca fabricar prioridades para cumprir número pedido. Output de LLM é proposta, não FACT. Avaliador não pode contar clarificação genérica como sucesso.
- Instrumentar *first divergence* e adequar avaliação empresarial doc 211 sem mudar perguntas congeladas.

**Aceite S6:** golden tests + E2E com respostas literais para cobertura integral, parcial, contraditória e insuficiente; nenhuma conclusão factual sem Evidence; rubrica fixa por subobjetivo e origem, critérios aplicados no SHA/config; regressão zero falsos PASS com catálogo ou clarificação.

## 7. Aceite transversal / release gate

**Obrigatório cumprir simultaneamente:** S2 PASS (ou `NOT_ADOPT` fundamentado com mecanismo atual aperfeiçoado e benchmarks), S3 PASS, S4 PASS, S5 PASS, S6 PASS; regressão backend completa PASS; interop A–F PASS; segurança PASS; pelo menos 10 cenários técnicos E2E com respostas completas e traces; held-out independente; comparação antes/depois ligada ao SHA; relatório de rollback executado; arquivos e artefatos localizáveis. Nenhum "PASS" genérico sem comandos, logs, SHA, config, contagem e resultado.

**Etapa 4 excluída:** 28×3 doc 211 como homologação empresarial final fica para outra task; **preparação** do evaluator/fixtures obrigatória. Se qualquer gate falhar, `TASK_INCOMPLETE` e prosseguir correção interna até limite legítimo; não reclassificar gate como "residual aceitável" sem aprovação explícita da coordenação. `ACCEPT_WITH_RESIDUAL` vale só para riscos não eliminatórios **após** S2–S6 PASS.

## 8. Controle de execução em slices com commit+checkpoint

- Slice 0 reanchor/baseline+RED; Slice 1 S2; Slice 2 S3; Slice 3 S4; Slice 4 S5; Slice 5 S6; Slice 6 integração/segurança/full regression/rollback/docs.
- Cada slice: `BASE_SHA/FINAL_SHA/FILES_CHANGED/CONTRACT/RED/GREEN/E2E/BENCHMARK/BLOCKERS/ROLLBACK`. Não usar contexto esgotado como "concluído"; gravar handoff verificável e continuar de onde parou.
- Não fazer docs-only final como se fosse implementação. Documentos 210–214 e ledger atualizados após evidência; stage só paths da task. Push main legítimo e verify origin/main.
- **Produzir:** (A) código/migrations/configs legítimas, (B) tests/evals, (C) benchmark A/B S2 e graph S4, (D) dez respostas reais E2E, (E) pacote seguro de logs/traces acessível para revisão, (F) matriz gate S2–S6 com prova, (G) runbook rollback/restore, (H) GitHub SHA, (I) relatório final.
- Resultado `INCONCLUSIVE`/ `EXECUTION_DRIFT` somente com impedimento real e avanço das partes independentes. Não afirmar aceite final.

## 9. Formato obrigatório de relatório

```text
TASK_ID=DELIA-C3-AGENTIC-S2-S6-BINDING-IMPLEMENTATION-01
BASE_SHA=
FINAL_SHA=
ORIGIN_MAIN=
PUSH_VERIFIED=
PHASE_CP_RQ=
AUTHORITIES_READ=
DOCUMENTS_210_211_212_213_214_READ=
EXISTING_EQUIVALENT_AND_REUSE_DECISIONS=
S2=PASS|FAIL|INCONCLUSIVE
S2_AB_BENCHMARK=
S2_FRAMEWORK_ADOPTION=
S3=PASS|FAIL|INCONCLUSIVE
S3_SUBOBJECTIVES_E2E=
S4=PASS|FAIL|INCONCLUSIVE
S4_SEND_FANOUT_BENCHMARK=
S5=PASS|FAIL|INCONCLUSIVE
S5_RESUME_ISOLATION_AUTHZ_TEST=
S6=PASS|FAIL|INCONCLUSIVE
S6_EVIDENCE_COVERAGE_TEST=
END_TO_END_SCENARIOS_COUNT=
RAW_RESPONSES_LOCATION_AND_ACCESS=
FULL_BACKEND_REGRESSION=
INTEROP_A_F=
SECURITY_NEGATIVES=
ROLLBACK_PROOF=
PROD_DEPLOY=NO
BUSINESS_WRITES=0
TASK_STATUS=COMPLETE|INCOMPLETE|EXECUTION_DRIFT
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW
BLOCKERS_WITH_EVIDENCE=
```
