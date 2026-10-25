# 148 — R7: decisão de arquitetura, remediação de drift e fechamento de Outcome

**DATA:** 2026-10-25  
**TASK_ID:** `DELIA-R7-ARCHITECTURE-DRIFT-AND-GROUNDED-OUTCOME-REMEDIATION-01`  
**ESTADO:** `COORDINATION_PLAN / DESIGN_PROPOSAL / IMPLEMENTATION_GATED`. Nenhuma solução nova foi implementada por este documento.  
**BASE INSPECIONADA:** HEAD `657c0923dd902f5ffc24b579b65e5ea011eb96e1`; implementação v19 `6e51626b1b`; reviews `dcfee3d1` e `657c0923`; spec 146, plano 147, evidências R7 e ledger. Reancorar antes da execução.

## 1. O que foi comprovado e por que ainda não funciona

**Reportado pelo executor, sujeito a reexecução:** v19 mudou admission de `0/10` para quase `10/10` owner-path em parte da avaliação, mas **business Outcome seguiu `0/10`** em batches locais. A cadeia multiestágio continua sujeita a divergência em `select_group`, `foreign_selection`, `candidate_arguments`, `arguments`, timeouts/model-output e `goal_evidence_relevance`. Um falso positivo apresentou metadados de rotas VISTA como registros empresariais `GROUNDED`, apesar de a pergunta exigir produtos reais. O problema não se resolve com a média de acerto de uma etapa: falhas de vários estágios se compõem e a pertinência final é uma fronteira de segurança/correção.

**A1 (TO_INVENTORY):** `owner_surface_kinds` é taxonomia hardcoded no admission, não projetada de catálogo vivo; pode driftar do ownership real.  
**A2 (PROVEN no diff):** `business_subject` passou a ser transportado para foreign leg e candidate arguments. É **âncora semântica fornecida por modelo**, não autoridade.  
**A3 (EXECUTOR_REPORTED material failure):** control-plane (rota, operationId/capability) foi aceito como business answer. É gate bloqueante até reprodução e correção comprovadas.  
**A4:** `delia-json` 3B/GPU/config local apresenta variância; o tamanho do modelo não prova a causa isolada. Nenhum benchmark externo está autorizado.

## 2. Referência de padrões consolidados (benchmark arquitetural, não autorização de framework)

- **Typed tool calls e typed outputs:** o produtor do modelo escolhe a capacidade/argumentos; o software valida schemas e efetua chamadas autorizadas. Fonte: OpenAI, Agent Definitions — https://developers.openai.com/api/docs/guides/agents/define-agents .
- **Tool/output guardrails + owner review:** validar argumentos e resultados na fronteira de tools, distinto de autorização para side effect. Fonte: OpenAI, Guardrails — https://developers.openai.com/api/docs/guides/agents/guardrails-approvals .
- **Manager/orchestrator mantém ownership do outcome e chama especialistas como tools:** fronteiras claras, não handoffs que entreguem autoridade paralela. Fonte: OpenAI, Orchestration — https://developers.openai.com/api/docs/guides/agents/orchestration .
- **Workflow mínimo e context engineering antes de multiagent complexity:** usar padrões sequenciais e evaluator-optimizer apenas quando justificados. Fonte: Anthropic, Building Effective AI Agents — https://resources.anthropic.com/building-effective-ai-agents .
- **Evals por etapa:** medir tool selection, inputs, usage e grounding separadamente. Fonte: Microsoft Foundry, Agent Evaluators — https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators .
- **Stateful recovery com checkpoints** é padrão de referência, não motivo para instalar LangGraph: https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx .

**Decisão:** adotar os **princípios/contratos**, não importar frameworks, agentes novos, planner paralelo, memória de autoridade, segunda state machine ou novo evaluator. Preservar owner DÉLIA e capabilities/CRI/Policy/Outcome atuais.

## 3. Arquitetura-alvo (contrato lógico, sem criar módulos)

```
USER GOAL
 -> SEMANTIC INTENT/ADMISSION [LLM, dynamic allowed surface projection]
 -> SELECT SEMANTIC CAPABILITY [LLM over live catalog, not hardcodes]
 -> OWNER INPUT SCHEMA + TRUST BOUNDARY [backend validation]
 -> PREPARE PROPOSAL/REFERENCE [LLM selection; code validates literal integrity]
 -> GOVERNED MCP / DOMAIN READ [live AuthZ, candidate/token, timeout, read policy]
 -> OWNER BUSINESS EVIDENCE [separate from control-plane metadata]
 -> GOAL RELEVANCE [semantic judgment + deterministic structural invariants]
 -> OUTCOME / BOUNDED RECOVERY [existing path or truthful insufficiency]
```

**Invariantes:**
1. Catalog discovery não é approval; hints, schemas e metadata são UNTRUSTED DATA, não autorização ou FACT.
2. A escolha do **significado** e de qual produto/registro é pertinente continua do LLM; o backend verifica **apenas** contratos estruturais de owner/type/provenance/quantity e não declara pertinência semântica por palavras.
3. Domain API é autoridade de registros; mesmo quando DAVI encontra nomenclatura, documento não vira produto/estoque. VISTA `route catalog`/operationId/control-plane nunca satisfaz postcondition de produtos sem resultado de Domain API correspondente.
4. `GROUNDED` não decorre de HTTP 200 nem de `judge=corresponds` isolados; exige role `business_evidence`, origem/owner legítimo, tipo de registro, cardinalidade verificada e ligação à solicitação. Se não comprovado, `INSUFFICIENT/UNVERIFIED`, sem apresentar dado como registro real.
5. Corrigir falha técnica recuperável via existing bounded recovery; não inventar consulta ampla sem filtro, token, provider, instrução ou ACT.
6. Não forçar uma solução genérica a depender do modelo local 3B. Modelo local deve ser avaliado honestamente; capacidade insuficiente gera bloqueio de release ou autorização específica para runtime/modelo local já aprovado, nunca regra hardcoded.

## 4. Work packages ordenados e gates

### WP0 — Reancorar e congelar contratos e matriz de falhas
Revalidar HEAD/status; Project Instructions/.cursor; 16→50→17→49→51→52→21→20→25; arquitetura; product spec; 125,129,130,146,147, ledger; observar SHA/instructions v19/model/CRI. Instrumentar trace **existente** por correlation_id (sem dados sensíveis), gerar fixtures sanitizados de A1/A3 e baseline de outros domínios. `EXISTING_EQUIVALENT`/`REUSE_DECISION` por mecanismo.

### WP1 — Eliminar drift de admission (A1)
Auditar por que catálogo live não está disponível antes da admission; identificar projeção vigente `_group_summaries` ou descritor canônico de superfícies/permission-scoped. Escolher solução **mínima** baseada em fonte autorizada e dinâmica, sujeita a custo/latência/budget, ou admission neutra agnóstica da lista quando for impossível fornecer catálogo (sem afirmar “no owner catalog”). **Não** inserir novo array de categorias, cópia de doc canônico, if/elif por produto/provider ou consultar catálogo sob credencial privilegiada antes do AuthZ. Se contrato/custo/segurança exigir novo owner, STOP → ADR/coordenação, não improvisar. Testes: superfície adicionada/removida muda contexto sem código; greeting/hipótese não acionam READ indevido; business lookup segue caminho; owner unavailable não inventa owner.

### WP2 — Gate estrutural de business evidence vs. control-plane (A3)
Reproduzir com fixture de `VISTA route/operationId` marcado `corresponds`. Identificar origem e type/provenance na projeção, `goal_evidence_relevance` e publicação. Reutilizar `Evidence/Projection/Outcome` e contratos atuais, não criar juiz paralelo. Gate determinístico para **invariante estrutural**: um pedido de produtos não pode ser satisfeito exclusivamente por catálogo de rotas, independentemente do parecer do LLM. Derivar papel/type da capacidade e schema/structured response do owner, **não** de nome literal de provider/strings em texto. Relevance semântica do LLM continua necessária. Testar: documentos normativos não contam como produtos, catálogo de rotas não conta como dados, Domain READ real conta, multi-record cardinality, ausência de registros, fonte mista, dados maliciosos, falsificação de provenance e metadata injection. Se envelopes atuais não preservam tipo/linhagem suficiente, STOP para contract-first no owner; não atribuir TYPE por heurística de conteúdo.

### WP3 — Revalidar candidate/argument flow e recuperação
Preservar F1/F2 e R1–R3; assegurar `business_subject` como dado do modelo bounded, jamais permissão ou palavra que code force no schema. Garantir parâmetros reais MCP/Domain API; candidate bound só com owner token. Identificar under-filtered (semântica declarada documental sem binding) e retorno do existing resolver sem query; sem segunda engine. Testes com campo opcional, obrigatórios, schema none, unbound, over-limit, payload budget, cross-user, MFE context e no WRITE.

### WP4 — Evals determinísticas, modelo local e generalização
Primeiro fixture-backed eval sem LLM para contratos; depois modelo local autorizado, no mesmo SHA/instructions/config e corpus, para pedidos reais de 3 produtos, O2, pino, MP/PI/PA, TÉO, VISTA, direct READ, negativas. Separate metrics por estágio: admission, group, capability, foreign, argument fidelity, source role, relevance, postcondition, outcome, latency, tokens reais se houver. **Zero falso positivo de business evidence** em fixture suite e multirun local. Não excluir falhas/timeout; nenhuma estatística de n=10 isolada substitui confiabilidade aprovada. Nenhum LLM remoto nem novos downloads não autorizados.

### WP5 — Regression, review e release
Full backend e env-failures caracterizados, AuthZ/PREPARE/ACT/CRI local, architecture/import tests, residual search no código; documentar SHA e provenance das evidências. Reviewer independente com `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`. Deploy condicionado a **business Outcome local confiável**, segurança/generalização, C1 resolvida ou exceção formal, revisão independente favorável e autorização operacional específica por serviço/SHA/digest/rollback. Produção só READ smoke. Se bloqueado, `BLOCKED_WITH_EVIDENCE` e não autopublicar release.

## 5. Critérios de saída / parada

**WP1 PASS:** nenhuma taxonomia estática autoritativa, fonte dinâmica comprovada OU admission neutra comprovadamente compatível com catálogo dinâmico; sem falso roteamento de negativas.  
**WP2 PASS:** controle de tipo/provenance/owner impede VISTA route metadata ou guidance de virar produto real sem hardcodes, com negativos e positivos generalizados.  
**WP3 PASS:** contracts/regression de recuperação preservados.  
**WP4 PASS:** domínio real (3 produtos) com códigos distintos/autoritativos e relevância, multirun local conforme critério aprovado; controle-plane falso-positivo 0; provas separadas por etapa.  
**WP5 PASS:** gates release aceitos, autorização operacional específica e smoke produtivo verificável.

**STOP IMEDIATO:** ownership ou autoridade ambígua, proposta de novo engine/framework/segundo planner, proveniência estrutural não representável, inconsistência de AuthZ, falha de segurança, ausência de hardware/modelo local autorizado, segundo fracasso da mesma hipótese, ou evidência de false-positive business answer. Reportar `ARCHITECTURE_DECISION_REQUIRED` ou `EXECUTION_DRIFT` com causa e diff, não redesenhar em silêncio.

**Estado de partida:** `A1=TO_INVENTORY`, `A3=FAIL_REPORTED`, `O2_LOCAL=FAIL`, `DEPLOY=BLOCKED`, `R7_FINAL_ACCEPT=NO`.
