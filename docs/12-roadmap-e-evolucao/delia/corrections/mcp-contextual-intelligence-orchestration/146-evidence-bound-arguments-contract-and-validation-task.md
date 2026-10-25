# 146 — Evidence-bound arguments: especificação bounded para Devin (R7/O2)

**STATUS:** PLANNED / AUTHORIZATION_REQUIRED_FOR_PRODUCT_DIFF  
**TASK_ID:** `DELIA-R7-EVIDENCE-BOUND-ARGUMENTS-CONTRACT-REMEDIATION-01`  
**OWNER PROPOSTO:** DÉLIA, Application / capability orchestration + validação de argumentos já existente; confirmar no HEAD.  
**BASELINE DOCUMENTAL:** main `7e9d23115b1e6711a966f8c18810d411e4cfc24b` (reancorar no início).  
**ORIGEM:** revisão independente R7/v16 `7e9d23115b1e6711a966f8c18810d411e4cfc24b`, evidência `a225e632b8`, correção `17dc08b9c8`.  
**DECISÃO:** não implementar nova engine/planner/registry. Investigar e, se autorizado pelas authorities e contrato, estender mecanismo existente para vincular valores de argumentos a evidências sem exigir regeneração textual livre. `REUSE_DECISION=TO_INVENTORY` até prova.

## 1. Problema, evidência e limite

Na avaliação congelada v16 (kimi-k3, temp 0.2, corpus DAVI V2, token novo por run), o pedido O2 **“Me dê dois exemplos de terminal bala”** alcançou outcome correto **1/10**. Consultas foreign terminaram 8/9, mas a designação documental `TERM. BALA` chegou ao argumento da Domain API corretamente em apenas 1/9; nas demais execuções, o estágio `arguments` propôs variantes livres de linguagem. Esses números são **EXECUTOR_REPORTED**, não reexecutados nesta especificação. O resultado da produção em baseline antigo foi insuficiência honesta, não sucesso de negócio.

A hipótese a testar **não** é que `foreign_evidence` garanta semanticamente uma única designação ou que todo texto documental deva se tornar filtro. É que um valor *já selecionado semanticamente e comprovadamente presente em evidência elegível* poderia ser transportado com identidade literal e provenance por mecanismo existente, em vez de pedir sua reescrita pelo modelo. `MCP result != FACT`, `GUIDANCE_NOT_DOMAIN_TRUTH`; Domain API permanece fonte de verdade dos produtos. A prova 1/10 não autoriza deploy nem fechamento R7.

## 2. Reancoragem / stop gate (antes de qualquer código)

1. HEAD, origin/main, git status, worktrees, diff e SHA efetivo avaliado.
2. Project Instructions / .cursor / AGENTS, autoridades **16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25**, arquitetura técnica, product spec, temática aplicável, ADR58/S4-117, plano 125, gates 129, runbook 130, ledger, relatórios R0–R7 e reviews recentes.
3. `RESPONSIBILITY → OWNER → SOURCE → CONSUMERS → CONTRACT → IMPLEMENTATION → TEST → OUTCOME`.
4. Confirmar fase, CP/RQ e se esta task possui autorização canônica de execução de código. **Esta especificação permite inventário e desenho contratual; implementação depende de gate explícito.** Em conflito: STOP → `ARCHITECTURE_DECISION_REQUIRED` ou `EXECUTION_DRIFT`. Não corrigir silenciosamente decisões congeladas.

## 3. Inventário obrigatório antes do desenho

Inspecionar os caminhos e consumidores reais, com callers e testes:
- `delia-api/app/application/capability_provision/orchestration.py`: `_recover_relevance`, `_invoke_foreign_evidence`, `_build_arguments`, `_propose_candidate_arguments`, validação/binding de candidate-token, `_select_foreign_capability` e projection das evidências.
- `delia-api/app/application/interaction/argument_validation.py` (schema/defaults/gaps), `outcome_assessment`, composição de evidência/CRI; contratos `ProviderCapability`, `EvidenceFacts`, `GoalEvidenceJudgment`, reference/proposal lineage e eventuais seletores/normalizadores existentes.
- DAVI `read_governed_technical_knowledge` e resposta `topic/subject/section/items/heading_path/text/provenance`, **apenas pelo boundary público**, sem imports internos/banco alheio.
- `inputSchema` e allowlists existentes de `search_products` e de outras capabilities READ; nenhum campo novo presumido.
- testes de schema, owner/foreign evidence, candidate arguments, injection, negativos de AuthZ, PREPARE/ACT, R7 real-model.

Registrar matriz por símbolo: `PATH | RESPONSIBILITY | OWNER | CALLERS | CONTRACT | EXISTING_EQUIVALENT | REUSE_DECISION | GAP`.
Emitir obrigatoriamente `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`, com justificativa. “Parecido”, “mais fácil” e “útil no futuro” não legitimam duplicação. Se solução requer novo boundary/owner não aprovado, **STOP**, produzir ADR/gate, sem código.

## 4. Contrato-alvo: seleção semântica, transporte exato e validação

**Responsabilidades distintas:**
1. **LLM:** decide se precisa do conhecimento, qual trecho/termo documentado representa a intenção e a qual campo permitido do schema ele se destina; pode abster-se/solicitar clarificação.
2. **Evidência:** fornece trecho/documento versionado, proveniência e trust classification; é dado não confiável para instruções, **não** permissão empresarial.
3. **Validação determinística existente:** confere referência à evidência recebida **nesta execução**, autorização de uso da capability, que o valor selecionado ocorre no trecho aprovado sem normalização destrutiva, tipo/campo/schema/constraints, limites, proposal lineage e ausência de conflito; resolve valor literal na borda de argumentos, **sem decidir semântica no código**.
4. **Domain API:** consulta registros com seus contratos e AuthZ atuais; `search_products` só confirma produtos depois do READ real.
5. **Outcome:** verifica pertinência e fatos retornados; mera coincidência textual e HTTP 200 não bastam.

Forma **ilustrativa, NÃO aprovada como novo DTO**:
```json
{
  "argument": "description",
  "source_ref": "turn-evidence/section-reference",
  "selected_value": "TERM. BALA"
}
```
Preferir o identificador de referência/valor selecionado **já existente**; se houver campos de proposta/lineage ou `selected_argument` equivalentes, reutilizá-los. Não criar registry persistente de evidência, nova credencial, nova ferramenta MCP ou nova authority. A referência é bounded por turno, identidade e consulta: não aceitar `source_ref` arbitrário do usuário, cache ou provider metadata como certificado.

**Invariantes fail-closed:**
- Referência inválida/stale, valor ausente do trecho, escolha ambígua, provenance inconsistente, campo não autorizado, tipo inválido, schema incompatível, injection, ausência de elegibilidade ou conflito entre evidências → **não vincular automaticamente**; devolver erro tipado, missing input, clarificação ou insuficiência conforme mecanismo existente.
- Preserve exact bytes/valor autorizado para campos textuais quando apropriado; não remover pontuação significativa (`TERM. BALA` ≠ `TERMINAL BALA`). Permitir normalização **apenas** quando contrato do campo a autorizar e registrar o valor final efetivo.
- Para identificadores/códigos numéricos, moeda, datas e enums, tipo e restrições vêm do owner contract; não generalizar coerção livre.
- Documentation `GUIDANCE_NOT_DOMAIN_TRUTH` pode fundamentar **candidato de busca READ**, nunca substituir `Domain API` como fato e nunca autorizar WRITE/PREPARE/ACT.
- Não transformar seleção referenciada em auto-lookup compulsório em toda pergunta; planner conserva decisão semântica e políticas de budget/recovery.
- Não criar heurística `if "terminal bala"`, mapa de sinônimos por produto, provider branching, novo planner/engine/loop, novo RAG, import interno de `api-delpi`, banco de outro bounded context, extensão de AuthZ ou bypass de confirmation.

## 5. Plano Devin — milestones e arquivos

**Milestone A — Characterization, SEM PRODUCT DIFF:** Capturar payloads sanitizados da fronteira `foreign_evidence → arguments` em cenário sucesso e falha; verificar se a string literal e a referência realmente sobrevivem ao trimming/serialization; observar o valor final passado ao owner, inclusive em partial/ambiguous evidence. Fixar SHA/model/config/CRI, denominadores e IDs correlacionados. Encontrar o mecanismo de validação/ref existente ou registrar `TO_INVENTORY`.

**Milestone B — Contract-first, gate:** Definir owner/consumers, request/response tipados, erro e fallback, security/AuthZ, idempotência/READ, limites, observabilidade, compatibilidade e postcondition. Classificar `REUSE` ou `EXTEND` fundamentadamente. Contrato deve distinguir **referenciar** de **autorizar** e **valor textual observado** de **fato de negócio**. Se novo contrato estrutural ou port obrigatório: STOP e devolver `ARCHITECTURE_DECISION_REQUIRED`, sem implementação especulativa.

**Milestone C — RED tests:** Exercitar o path real de construção/validação/execução, não somente helper inventado. Testar que proposta de valor referenciado `TERM. BALA` resulta em `description=TERM. BALA` literal no `search_products` com evidência válida; RED quando modelo altera a string sem prova. Casos equivalentes **não específicos**: outra designação MP, PI/código, variação de nome técnico, trecho multiopção e ausência de fonte. Negativos: injection de documento; `source_ref` forjado; cross-turn/cross-user; stale; value não presente; schema field não autorizado; enum; owner changed; conflicting designation; missing source; timeout/budget; fallback seguro; adversarial MCP metadata; candidate-token inválido. PREPARE/ACT e AuthZ devem permanecer fechados.

**Milestone D — Minimal implementation, SE AUTHORIZED:** Implementar somente extensão do owner/código já existente demonstrado em B, sem mudar o planner. Preferência: validação e materialização na fronteira de argumentos com referência bounded; nenhum código específico DAVI ou de O2. Alterar apenas arquivos allowlisted pelo gate B; capturar diffs, reduzir acoplamento e manter compatibilidade de propostas legadas sem referências.

**Milestone E — GREEN/REGRESSION/REAL EVAL:** Focados, suíte backend completa, architecture gates/import DAG, segurança, owner-neutral/metamorphic, CRI ON/OFF local, no mutation of other contexts; DAVI/read-only contract E2E, document evidence and business API postcondition. No AI eval with a different checkout or image than `EVALUATED_SHA`. Congelar matriz ANTES: O2 N definido/denominadores completos, sibling terminal pino, D1 MP/PI/PA, TÉO SIPOC, VISTA, direct READ, irrelevant evidence, negatives, WRITE-ineligible, provider rename/order; baseline v16 versus candidato na mesma config modelo e dados. Reportar **(a) taxa de argumento literal preservado, (b) taxa de business outcome, (c) latência/tokens, (d) falsos fatos/violação de segurança**. Objetivo de 70% é provisório e não aprovação automática de release; threshold final depende da coordenação/autoridade.

**Milestone F — Documentation, commit/push and gate:** Evidência por SHA/config, first divergent stage, owner/contract matrix, testes, residual search, ledger, diff, limites, rollback. Commit/push main ff-only preservando alterações concorrentes. **Não fazer deploy** sem testes/revisão independente e autorização operacional específica por serviço. Se a solução não generalizar ou demonstrar nova autoridade paralela, `REWORK/EXECUTION_DRIFT`; se depender de novo conceito estrutural, `ARCHITECTURE_DECISION_REQUIRED`.

## 6. Critérios de aceite

- `EXISTING_EQUIVALENT` e `REUSE_DECISION` provados por paths e callers reais.
- A escolha semântica permanece do LLM; não existe branching por produto ou provider.
- Valor selecionado de trecho elegível chega ao campo do schema sem regeneração livre e com rastreabilidade, quando essa representação é contratualmente aceita.
- Fonte sem dado suficiente resulta em insuficiência/clarificação, **não** busca falsa nem resposta inventada.
- Invalid refs, cross-identity, injection, enum e candidatos inelegíveis são fail-closed.
- Suíte/arquitetura/segurança/generalização e outcome real verificados no SHA/config identificado.
- O2 é julgado por registros reais da Domain API e pela confiabilidade multirun, não por um sucesso isolado.
- Nenhum release, write produtivo ou encerramento R7 automático. `R7_CLOSED=NO` até revisão independente e gates.

## 7. Entrega obrigatória

```text
TASK_ID=DELIA-R7-EVIDENCE-BOUND-ARGUMENTS-CONTRACT-REMEDIATION-01
BASE_SHA=
FINAL_HEAD=
ORIGIN_MAIN=
PUSH_VERIFIED=
AUTHORITIES_READ=
PHASE_CP_RQ=
EXECUTION_AUTHORIZATION=
RESPONSIBILITY_OWNER_CONSUMERS=
EXISTING_EQUIVALENT=
REUSE_DECISION=
CONTRACT_BEFORE_AFTER=
FIRST_DIVERGENT_STAGE=
EVIDENCE_REFERENCE_MECHANISM=
BOUND_VALUE_PROVENANCE=
AUTHORIZED_FILES=
ACTUAL_FILES=
RED_GREEN=
FULL_BACKEND=
ARCHITECTURE_GATES=
SECURITY_NEGATIVES=
MCP_DOMAIN_OUTCOME=
EVALUATED_SHA_MODEL_CONFIG=
BASELINE_ARGUMENT_PRESERVATION=
CANDIDATE_ARGUMENT_PRESERVATION=
BASELINE_O2_OUTCOME=
CANDIDATE_O2_OUTCOME=
DENOMINATORS=
LATENCY_TOKENS=
GENERALIZATION=
RESIDUALS=
EXECUTION_DRIFT=
ARCHITECTURE_DECISION_REQUIRED=
DEPLOY_AUTHORIZED=NO
R7_FINAL_ACCEPT=NO
FINAL_VERDICT=READY_FOR_INDEPENDENT_REVIEW|BLOCKED_WITH_EVIDENCE
```

**Ordem final ao Devin:** implementar somente após reancoragem, inventário real e contrato aprovado na hierarquia; corrigir a **fidelidade de transporte de valor selecionado** usando mecanismos preexistentes. Não usar tuning sucessivo de prompts ou troca de modelo como substituto de garantia de integridade. Exigir generalização, segurança, outcome e prova reproduzível. Sem evidência, `PENDING/INCONCLUSIVE`, nunca `PASS`.


## 8. Decisão posterior do PO — 2026-10-25

Plano de execução aprovado como direção (prevalece sobre recomendações anteriores de A/B com modelo externo): [147 — referência condicional e avaliação local](./147-conditional-evidence-reference-local-execution-and-release-plan.md). Escolha semântica continua LLM; parâmetros devem respeitar MCP/Domain API owner schema; usar binding referenciado quando o modelo **declarar** uso de valor literal de evidência; não fazer snapping fuzzy. Não realizar novas avaliações com modelos externos nesta task. PO aprova objetivo de deploy **condicionado** a avaliação local, revisão independente e autorização operacional específica por SHA/serviço/rollback. A especificação 146 segue aplicável nos testes/segurança, sem autorizar segundo planner ou novo contrato sem gate.
