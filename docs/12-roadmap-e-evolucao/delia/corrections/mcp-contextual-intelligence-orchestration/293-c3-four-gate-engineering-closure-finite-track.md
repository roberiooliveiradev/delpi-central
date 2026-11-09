# 293 — DÉLIA · trilha finita de fechamento de engenharia: LEGACY / OWNERSHIP / FLOW / REGRESSION

**Data:** 2026-11-09. **Tipo:** COORDINATION PLAN / DOC_ONLY. **Estado:** PLANNED, nenhum gate aceito por este registro. **HEAD visto durante a preparação:** `6d8536bc205822d857691c3eb4e1dfe1b7e318d4` (revalidar na execução; mudanças concorrentes possíveis). **Owner:** coordenação DÉLIA; implementadores Cursor/Devin sob task autorizada. **Objetivo do PO:** **ZERO resíduo material não resolvido nos quatro gates**, antes de novas funcionalidades ou troca de foco para experimentos de inteligência/modelos; não declarar sucesso por documentação ou testes isolados. **Production deploy:** NOT_AUTHORIZED.

## 0. Precedência e preservação

Reancoragem obrigatória em **cada etapa**: `HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger`. Buscar fase e NEXT reais em 16+ledger no HEAD; este roteiro não avança C3 nem substitui decisões congeladas. Preservar 21/C3-T4 Structured Understanding; foundation C3-T5 OpenAPI de 16/20/25; owner/contrato do snapshot; AuthZ Core/Domain, Keycloak, MCP provider boundary, Evidence/Policy/Outcome; `read!=write`, `PREPARE!=ACT`, `tool!=permission`, `GROUNDED!=Outcome`. Conflitos: STOP + `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`, nunca reconciliação implícita.

**Fontes de entrada:** doc256 (plano mestre G0–G8, inventário 246–255 e anexos de execução), docs 239–255, 125/129/130 (refactor e antipadrões), doc292 (estabilização funcional; snapshot histórico, **não prova de HEAD**), ledger oficial, backlog R01–R07, e evidência E2E v42 `delia-api/.battery/r01-v42-e2e/matrix-summary.json` (DEV only; Kimi e Qwen14B C1 GROUNDED, Qwen4B C1 admission FAIL; Qwen14B B1/OPS alguns outcomes parciais; G4 fixture fail de suíte ampla). Código/teste/resultado real no SHA vigente prevalecem sobre histórico apenas como evidência de implementação — autoridade documental prevalece nas decisões.

**Proibição de varredura infinita:** NÃO repetir auditoria completa de 66 arquivos nem reabrir G0–G8 como trabalho novo. Consumir matriz doc256, ledger e commits aceitos, atualizar somente itens de risco com diff no HEAD. Um único mapa residual congelado em T0 e buscas residuais dirigidas por etapa; no máximo **5 tasks de execução + 1 revisão final** (T0–T5), com **até 1 rework técnico bounded por etapa**, sem geração recursiva de planos. Pedido fora do universo congelado ou necessidade de novo owner = STOP e decisão superior, não extensão silenciosa. Trabalho concluído não é refeito.

## 1. Contrato da trilha, critérios de fim

Gates independentes e cumulativos:

- **L — LEGACY_CLEANUP = PASS**: zero `OBSOLETE_PROVEN` com consumer ativo/alias/shim/flag/import no runtime DÉLIA; remoções de docs244–255/256 comprovadas em HEAD e consumidores/contratos substituídos; nenhum parser/retry/tool loop próprio duplicando Pydantic AI sem função legítima; componentes aprovados mantidos. `0 rg results` sozinho não é prova.
- **A — ARCHITECTURE_OWNERSHIP = PASS**: nenhuma violação de dependência/boundary ativa conhecida no escopo congelado, zero segunda autoridade Core/Domain, zero planejamento/tool mechanics hardcoded por provider, snapshots e OpenAPI com owner/contrato/fase decididos; interfaces reais pelos Ports & Adapters existentes, sem duplicação.
- **O — ORCHESTRATION_FLOW = PASS**: caminhos de admissão, owner selection, MCP native Pydantic AI, evidence/grounding/outcome e negativos provados no SHA/config da trilha, incluindo casos de sucesso, parcial, não encontrado, unauthorized, compare, multi-owner, multi-turn, NDJSON/timeouts; **sem defeito material do fluxo não corrigido**. Limitações de capacidade de modelo continuam rastreáveis e exigem veredicto explícito se impedem DoD; não renomear falha de fluxo como limitação do modelo sem prova da primeira fronteira divergente.
- **R — FULL_REGRESSION = PASS**: suíte completa DÉLIA backend e focused security/architecture tests com exit 0 e provas live DEV autorizadas de Outcome; falha G4 fixture resolvida ou classificada/isolada por owner com justificativa canônica e suite real reproduzível; TÉO suite R07 e prod tools/list R06 são **dependências externas** com owner, não podem ser escondidas sob PASS DÉLIA. Se critérios canônicos exigirem tais provas para produto, mantê-los bloqueadores até owner os encerrar.

**CLOSE=ACCEPT** somente se L=A=O=R=PASS, entregas e provas fechadas em SHA/config sem drift, zero residual MATERIAL conhecido no escopo, avaliação independente aprovada e ledger atualizado. `ACCEPT_WITH_RESIDUAL` é **não encerrado** para este objetivo, mesmo se residual parecer pequeno. Falta de credenciais/infra/authority = PENDING/BLOCKED (não PASS). Problemas de modelos externos ficam separados somente se não contaminarem o aceite obrigatório do fluxo; nenhuma falsa universalização de Kimi/Qwen14B para Qwen4B.

## 2. Sequência fixa e não recursiva

```text
T0  FREEZE (HEAD, autoridades, baseline, matriz residual L/A/O/R)
  → T1  LEGACY (remoções e consumers: legado obsoleto comprovado)
  → T2  OWNERSHIP (dependências, snapshot/OpenAPI, boundaries)
  → T3  FLOW (first-divergence + correção dos defeitos do fluxo DÉLIA)
  → T4  REGRESSION (full suites, AuthZ, real Outcome, negatives)
  → T5  INDEPENDENT CLOSE (audit diff, gate L/A/O/R, ledger, handoff)
  → END: ACCEPT | REWORK bounded (1) | BLOCKED/ADR
```

Cada etapa é **um task ID**, um escopo congelado e um relatório. Não avançar automaticamente para a seguinte: coordenação revisa `ACCEPT|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`; T5 é a única decisão global. Rework máximo 1 por etapa, limitado aos testes/arquivos do defeito; depois STOP com relatório e owner responsável — sem novos prompts em cascata. T0 é 1 pass de reconciliação residual, não inventário total.

### T0 — Freeze factual e decisão de escopo

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T0-BASELINE-RESIDUAL-FREEZE-01`. **Owner:** coordenação DÉLIA. **Inputs:** 16/ledger/256, commits aceitos, R01–R07, E2E DEV e 292 como histórico. **Artefato único:** `engineering-closure-residual-register.md` (ou anexo com path/consumer/owner/contract/test/SHA) com classificação de cada item `CLOSED_PROVEN | OPEN_MATERIAL | EXTERNAL_DEPENDENCY | KEEP_APPROVED | TO_VERIFY`; no máximo uma linha por defeito real/contrato, não por arquivo já limpo. Evidência existente validada sem reexecução. Revalidar baseline sintaxe/import/target suites e classificar falha G4 e as dependências TÉO R06/R07, cronograma de gate. **Sem refactor/código nesta etapa.**
**Exit:** universo congelado, ordem e conjuntos mínimos de testes, CP/RQ, blockers, `EXISTING_EQUIVALENT/REUSE_DECISION`. Se autoridade contraditória, STOP somente slice; sem inventário ad hoc infinito.

### T1 — LEGACY CLEANUP (somente candidatos abertos T0)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T1-LEGACY-CONSUMER-PURGE-01`. **Owner:** DÉLIA application/infrastructure por arquivo real. Conferir exclusões doc244/245 (paginated semantics, outcome assessment), G1–G8 doc256, wrappers/flags CRI e shims, import reverso de snapshot quando relevante (decisão T2). Para cada `OBSOLETE_PROVEN`: rastrear consumidores static+dynamic, preservar contratos/authority, RED→minimal DELETE/consumer migration→GREEN→full focused regressão→residual AST/import/rg. Se função ainda tem consumidor legítimo: `KEEP_APPROVED` documentado, não chamar legado. Não mover 1.800 LOC para helper; não criar engine novo. **Exit:** `L=PASS` preliminar com evidência de paths removidos, consumer count 0 e paridade, ou BLOCKED com owner e decisão — sem tarefa extra.

### T2 — ARCHITECTURE / OWNERSHIP (sem redesenho)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01`. **Owner:** arquitetura DÉLIA + owners dos contratos. Revisar dependências reais do HEAD (Domain/Application sem infra; HTTP/event inter-context, sem imports/banco alheios); anomalia snapshot Application→Infrastructure e destino de experimento, C3-T5 foundation/adapter OpenAPI, C3-T4 approved KEEP, configurações paralelas/providermatics no planner e imports MCP. Não tocar Keycloak/Core/TÉO sem owner autorizado; decisão snapshot/OpenAPI preserva freezing docs. Corrigir **somente** desvio comprovado dentro de ownership; RED→GREEN+arquitetura/segurança. Se decisão superior requerida, `ARCHITECTURE_DECISION_REQUIRED`, sem esconder sob PASS. **Exit:** `A=PASS` preliminar ou BLOCKED formal.

### T3 — ORCHESTRATION / FLOW (correção delimitada)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T3-FLOW-OUTCOME-REMEDIATION-01`. **Owner:** DÉLIA Capability Provision / Interaction. Usar baseline v42 e native Pydantic AI/MCP; não trocar output strategy, recriar planner, alterar budgets R03 por chute ou refazer config por modelo. Matriz canônica mínima: admission operational/conceptual/surface, discovery→execute, cross-owner compare, partial/no-data, invalid tool args, denied, multi-turn, streaming/terminal, timeout/budget e postcondition outcome. Para cada falha: primeira fronteira divergente `ADMISSION|SELECTION|MCP|OWNER|PROJECTION|EVIDENCE|OUTCOME|PRESENTATION`; proibir correção keyword/model-specific; 1 diff bounded + RED/GREEN + real DEV case. Tratar residual Qwen14B B1/OPS sem automaticamente atribuir R02/R03, Qwen4B local como capability limitation somente com evidência; R01 status separado. **Exit:** `O=PASS` preliminar com matriz+truthful outcome, ou BLOCKED/INCONCLUSIVE.

### T4 — FULL REGRESSION / RELEASE READINESS (NO PROD)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T4-FULL-REGRESSION-AND-REAL-EVAL-01`. **Owner:** QA/engenharia DÉLIA, parceiros de teste TÉO quando relevante. SHA de T1–T3 fixado. Suite completa backend no ambiente canônico (sem `pytest -k` como substituto), arquitetura/imports/contract tests, auth negatives 401/403, MCP hostile content, permission changes, PREPARE/ACT, no leakage, deadlines, output grounding and denial; DEV E2E Kimi e Qwen14B fixados, conceptual/operational, 2 owners, multi-turn, Outcome. Separar falha G4 preexistente no mesmo ambiente: reproduzir base e candidato, reparar path/fixture no owner de teste se escopo legítimo, não esconder por skip. R06 prod tools/list e R07 full TÉO suite: owner externo; mapear se bloqueiam aceite do produto ou somente produção; se bloqueiam, STOP sem autoexecutar tarefas em outros serviços. **Exit:** `R=PASS` preliminar só com zero falhas materiais da suíte exigida e Outcomes comprovados; `TEST_NOT_RUN` não substitui PASS.

### T5 — REVIEW INDEPENDENTE E FECHAMENTO

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T5-INDEPENDENT-ZERO-RESIDUAL-ACCEPTANCE-01`. **Owner:** coordenação/reviewer independente. Comparar registro T0 vs HEAD, commits e consumer graph pós-removal, revalidar `16 + ledger`, tests reais e production status. Uma única tabela `ID|scope|owner|baseline|diff|test|Outcome|final disposition`; auditoria residual **direcionada** aos símbolos/paths congelados, não varredura nova de 66 arquivos. Veredictos L/A/O/R independentes. **ACCEPT somente L=A=O=R=PASS + ZERO_OPEN_MATERIAL + no drift**. Atualizar doc256 como supersession/ponte de T0–T5, anexos e ledger; registrar SHA/config, testes e handoff. Sem advancement C3, feature/model switch nem deploy automática. Se BLOCKED, **fim da execução com blocker formal** (owner/dependency/required decision), sem iniciar novo ciclo infinito; retomada específica exige nova autorização e reancoragem.

## 3. Política de residual ZERO e limites reais

- **ZERO** significa nenhum residual material **no escopo de fechamento DÉLIA aprovado**. Resíduo externo TÉO, dependência de produção ou limitação de modelo não pode ser rotulado `PASS`; determinar explicitamente se é bloqueador da aceitação DÉLIA ou de release. Não declarar que todo monorepo foi limpo.
- É permitido `KEEP_APPROVED` para código vivo ou foundation congelado; não é legado residual. `EXTERNAL_DEPENDENCY` não é solução: acompanha owner, impacto, teste e gate.
- Eventos que invalidem premissa = `EXECUTION_DRIFT`; autoridade contraditória = `ARCHITECTURE_DECISION_REQUIRED`; testes fora do ambiente válido = `INCONCLUSIVE`/ `STALE_EVIDENCE`.
- Proibidos: novos serviços/providers/registries, abstração sem consumer, loops/retries propios de Agent, reclassificação por string para mascarar fail, redução de testes, excluir históricos, fazer ACT sem gate, deploy implícito, fase avançada por documento.
- Critério de esforço: cada task consome apenas o conjunto `OPEN_MATERIAL|TO_VERIFY` atribuído; no máximo 1 rework e então STOP. Não criar T6/T7 automaticamente. Novo problema verdadeiro fora do frozen scope retorna à coordenação como drift, não expande a task.

## 4. Template mínimo de execução por etapa

```text
TASK_ID:
BASE_HEAD:
FINAL_HEAD:
ORIGIN_MAIN:
PUSH_VERIFIED:
HEAD_STATUS:
CANONICAL_REANCHOR:
PHASE_NEXT_16_LEDGER:
CP_RQ:
SCOPE_FROZEN_IDS:
FILES_CHANGED_REMOVED:
EXISTING_EQUIVALENT:
REUSE_DECISION:
CONSUMERS_AND_CONTRACTS:
RED_GREEN:
FOCUSED_TESTS:
FULL_BACKEND_TESTS:
ARCH_SECURITY_GATES:
REAL_EVAL_SHA_PROFILE:
OUTCOME_EVIDENCE:
RESIDUAL_SEARCH:
OPEN_MATERIAL_AFTER:
EXTERNAL_DEPENDENCY:
LEDGER_UPDATED:
PRODUCTION_DEPLOY=NOT_AUTHORIZED
STAGE_VERDICT=ACCEPT|REWORK|EXECUTION_DRIFT|INCONCLUSIVE|BLOCKED
NEXT_STAGE=REVIEW_REQUIRED
```

**Single command to start:** autorizar somente **T0**, sem código. Revisar T0 e então emitir **um único prompt bounded para T1**, sucessivamente até T5. Nenhuma autorização implícita para tarefas seguintes. **Fim inequívoco = T5 ACCEPT ou T5 BLOCKED/ADR documentado; sem loops de prompts.**
