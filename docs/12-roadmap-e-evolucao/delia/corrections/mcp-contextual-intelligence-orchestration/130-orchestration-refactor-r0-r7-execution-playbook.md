# 130 — Playbook de execução integral R0–R7: prompts, provas, rework e limpeza de legado

**Plano:** [125](./125-orchestration-complete-refactoring-finite-plan.md) · **Protocolo de antipadrões:** [129](./129-refactor-implementation-conformance-and-antipattern-gates.md) · **Produto/RPA:** [128](./128-cross-application-intelligence-and-rpa-capability-review.md)  
**Data:** 2026-10-23 · **Estado:** PLANNED / NÃO AUTORIZA R0–R7 · **Executor:** Devin · **Reviewer:** Architecture/Coordination · **Branch:** main (ff-only após gates).
**Aplicação:** DÉLIA standalone; **proibido reutilizar runtime/tabelas/agents do Minha DELPI Chat**.

## 1. Destino final verificável (não é objetivo de LOC)

Ao final do plano, o arquivo `orchestration.py` conserva a coordenação de propostas tipadas, seleção semântica provider-neutral, orçamento, seleção e revalidação de capabilities, fluxo PREPARE/ACT governado e despacho por ports. Evidência, avaliação de sufficiency/Outcome, composição conversacional, sanitização, validação e instruções declarativas estarão em seus **owners existentes**, ou em novos arquivos somente quando o Abstraction Gate provar contrato/consumidor real/ausência de equivalente. Nenhum arquivo novo deve ser outro god module.

Uma mesma inteligência de application pode atender conversação DÉLIA, Work/Event e consumidores externos **futuros**, mediante contratos adequados; nunca deve depender intrinsecamente de Markdown/ConversationTurn/React/DOM/RPA selectors. Reuso entre apps requer HTTP/eventos e owner/autorização governados em tarefa própria; **RPA technical execution pertence ao Automation Hub**, Domain mantém verdade e pós-condição. Não criar Work/RPA/external endpoints neste refactor.

**DoD simultâneo:** (1) responsabilidades coesas e acoplamento menor; (2) contrato e dependências corretos; (3) **zero legado comprovadamente obsoleto no escopo DÉLIA**; (4) todas as regressões materiais avaliadas e ausentes nos casos cobertos; (5) outcomes D4/D5/D8 e negativos preservados; (6) segurança/Policy/Domain intocados; (7) README/ledger e review independente. Nem 'mais simples', nem menos LOC, nem testes verdes isoladamente justificam desvios.

## 2. Ordem, bloqueios e autorizações

```text
FUNCIONAL-STABILIZATION: execução independente do Devin
  → parecer independente e baseline PASS/aceito
  → autorização explícita do PO para R0
  → R0 contrato/funções/legado, READ-ONLY → review coordenação
  → R1 recursos → review
  → R2 projeção/trust → review
  → R3 Outcome/CRI → review
  → R4 apresentação/guidance → review ou SKIP_WITH_DECISION
  → R5 schema/model contracts → review
  → R6 core + legacy purge → review
  → R7 full acceptance → review independente
  → eventual release PROD em task/autorização operacional separada
```

**R0–R7 continuam NOT_AUTHORIZED por este documento.** Todos os prompts estão PRONTOS, mas somente a etapa cujo gate/phase estiver liberado pode ser executada. Dentro de uma etapa aprovada o Devin deve executar sem pausas administrativas e tratar automaticamente falhas que permaneçam dentro do contrato, conforme §4; **o executor não se autoaceita nem avança para etapa ainda não liberada**. Se autoridade superior mudar, reancorar e STOP no escopo afetado.

## 3. Condições invioláveis / AP-01…AP-20

Aplicar [129 §6](./129-refactor-implementation-conformance-and-antipattern-gates.md) integralmente. Em particular: god modules/AP01, NEW sem owner/consumer/AP02, imports reversos/AP03, duplicação/AP04, planner específico/AP05–06, autoridade ilegítima/AP07–11, evidence/CRI impróprios/AP12–13, JSON com lógica/AP14, quebra de contrato/AP15, diff concorrente/AP16, teste insuficiente/AP17, segredo/AP18, fake consumer/AP19, violar decisão congelada/AP20. Todos os checks aplicáveis precisam de evidência concreta e classificação; check não implementado não pode ser declarado PASS.

**Legacy cleanup obrigatória:** toda função movida tem origem removida no mesmo lote após troca de callers ou shim **temporário aprovado com owner, consumer real, período de compatibilidade, plano de remoção e teste**. Levantar aliases, wrappers, branches unreachable, filtros lexicais históricos, dead exports, prompts duplicados, flags sem consumers, imports, testes/fixtures mortas, registros paralelos e scripts antigos. Para cada item: `PATH/SYMBOL → CONSUMERS_STATIC_DYNAMIC → OWNER → CLASS CURRENT|DEPRECATED_ACTIVE|OBSOLETE_PROVEN|TO_INVENTORY → ACTION DELETE|REPLACE|KEEP_WITH_CONTRACT → SHA/TEST → ROLLBACK`. Prova de ausência = search residual + call graph/AST + runtime tests; `0 results` isoladamente não prova ausência. **Obrigatório retirar OBSOLETE_PROVEN no escopo até R6**. Mecanismo com contrato ativo ou SKIP/117 não vira 'legacy' por parecer grande; se não removível sem quebra de API, não remover e registrar BLOCKED/ADR, jamais ocultar sob COMPLETE. **Fora de escopo:** código ativo Chat/Portal/Core/Domain/Automation Hub e história de migrations/ledger.

## 4. Auto-detecção de regressão e auto-rework bounded

Para cada etapa com diff: antes gravar `BASE_SHA`, comandos reais suportados, goldens e matriz de cobertura. Depois executar focused RED→GREEN / parity, full backend, arquitetura/imports, segurança/negativos, generalização, outcomes do caminho impactado no SHA/config testado. Comparar com baseline inclusive mensagem/contrato/reason/grounding, não só status HTTP. Evidência `NO_REGRESSION_FOR_EVALUATED_SCOPE=YES` só com rastros; isso **não** é prova universal de ausência de bugs.

**Máquina obrigatória:**
```text
IMPLEMENT → RUN FOCUSED + FULL + SECURITY + ARCH + OUTCOME
  ├─ ALL GATES PASS + no violation → residual search → scoped diff audit
  │    → commit/push ff-only → report + independent review
  ├─ REPRODUCIBLE REGRESSION or AP reparável within authorized contract
  │    → NO MERGE/DEPLOY → capture failing baseline/first divergence
  │    → add/retain RED → automatic MINIMAL REWORK (max 1 per stage)
  │    → rerun ENTIRE matrix in identical SHA/config
  │       ├─ PASS → evidence/review gate
  │       └─ FAIL → REWORK_EXHAUSTED → STOP, do not greenwash
  └─ Authority/ownership/Policy/security/contract broken, missing authorization,
       identity unavailable or evidence inadequate
       → STOP with EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED /
          INCONCLUSIVE or TEST_NOT_RUN as applicable, never arbitrary workaround
```

**Nunca:** baixar exigência/teste, alterar benchmark, apagar negative case, pular suite, marcar N/A sem causa, esconder falha sob retry infinito, reexecutar ACT ambíguo, fazer push de quebra conhecida, dizer PASS em deploy por health HTTP200. Regredir segurança/autoridade = BLOQUEADOR; aplicar correção só se for dentro da autoridade/contrato e sem efeito colateral não consentido. Comportamento LLM variável isolado exige múltiplas tentativas/traços controlados antes de alegar causa e aplicar patch.

## 5. Documentos que Devin OBRIGATORIAMENTE preencherá

O arquivo de cada etapa já contém o **prompt pronto para executar**, contrato, provas específicas e bloco de **relatório a preencher no próprio arquivo**, mantendo `NOT_STARTED` até execução factual. Preencher mesmo se etapa for `SKIP_WITH_DECISION`, `BLOCKED` ou `INCONCLUSIVE`; nunca preencher com PASS hipotético.

- [R0 — Baseline, inventário finito e contrato de saída](./refactor-r0-r7/r0-execution-and-evidence.md): M01–M10.
- [R1 — Instruções LLM e recursos declarativos](./refactor-r0-r7/r1-execution-and-evidence.md): M01.
- [R2 — Projeção de evidência e sanitização com owner único](./refactor-r0-r7/r2-execution-and-evidence.md): M02–M03.
- [R3 — Outcome e composição CRI coerentes](./refactor-r0-r7/r3-execution-and-evidence.md): M04–M05.
- [R4 — Apresentação, guidance e vocabulário](./refactor-r0-r7/r4-execution-and-evidence.md): M06–M07.
- [R5 — Validação de argumentos e propostas tipadas](./refactor-r0-r7/r5-execution-and-evidence.md): M08–M09.
- [R6 — Coordenador mínimo e limpeza completa do legado comprovado](./refactor-r0-r7/r6-execution-and-evidence.md): M10 + residual M01–M09.
- [R7 — Aceite independente, prova de não regressão e encerramento](./refactor-r0-r7/r7-execution-and-evidence.md): Todos M01–M10.

Cada registro preenchido contém: HEAD/base/current status, autoridades, fase e autorização, CP/RQ, allowed/actual files, mapa origem→destino e classificação de legado, owners/contracts/consumers, equivalence/reuse gate, import DAG before/after, testes e outcomes com SHA/config, AP01–20, auto-rework aplicado (0 ou 1), diff/residual search, rollback e veredito **do executor**, seguido de parecer **independente** em registro separado. Ledger e README somente após resultado factual; o template não altera fase.

## 6. Prova transversal mínima em todos os pacotes runtime

- **Arquitetura:** AST/import DAG sem ciclos, nenhum application/domain→infra framework/SDK, cross-bounded imports, duplicate owner/sanitizer, segundo engine, new god module, fake consumer, legacy morto.
- **Funcionalidade:** D4/D4-R, D5/D5-R/D5-schema, D8/D8-R, SIPOC sem MCP, CRI ON/OFF, conversa e continuidade, cobertura de comparação quando pertinente.
- **Generalização:** provider add/remove/rename/reorder e requests inéditos; usar live local/LLM quando seleção/propostas foram afetadas, não só mocks.
- **Segurança:** Core live/AuthZ negativo, Domain postcondition, identity fail-closed, controle MCP/A2A untrusted, PREPARE≠ACT, idempotência, audit, injections, secrets.
- **RPA/cross-app:** somente contrato existente comprovado; negativa structural de bot/scheduler na DÉLIA; `TECHNICAL_DONE != BUSINESS_VERIFIED` e nenhuma chamada a selectors pelo planner; não criar runtime de teste falso.
- **Observabilidade:** preservar correlation/lineage/timeout/retries/token real vs estimado; model SHA/config do mesmo release testado.
- **Prova:** distinguir `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`, e declarar CHECK_ALREADY_AUTOMATED/CHECK_MANUAL/CHECK_NOT_IMPLEMENTED. R0 apenas documental não recebe PASS de suite não rodada.

## 7. Protocolo de handoff e conclusão

O Devin deve entregar relatório ao fim de cada etapa e aguardar **review de coordenação** antes da próxima. Se outcome falhar, faz rework bounded **na mesma execução**, não envia uma task separada desnecessária. Cada etapa aceita tem prova de que não reintroduziu função legada/duplicação. Critério de conclusão final da refatoração: **R0–R7 revisadas; zero obsoletos comprovados; nenhum AP bloqueador; contrato/consumers iguais ou evoluídos por aprovação; full regressions + business outcomes no SHA; modularidade verificável; rollback; ledger; review independente `ACCEPT`**. `ACCEPT_WITH_RESIDUAL` não pode mascarar material risk ou legado obsoleto e exige decisão explícita se bloquear DoD. R7 não declara `PLAN_COMPLETE=YES` por conta própria.

### Prompt mestre para iniciar a etapa autorizada

> Devin, execute a etapa **R{N}** do plano DÉLIA `DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01`. Leia docs canônicos na ordem, plano 125, protocolo 129, revisão 128, este playbook 130 e o arquivo `refactor-r0-r7/r{n}-execution-and-evidence.md`. A reancoragem e a autorização para ESTA etapa são obrigatórias. Execute todos os passos do prompt daquele arquivo, congele `BASE_SHA`, siga a whitelist/contrato, faça prova de não regressão no escopo, auto-rework bounded (1) quando necessário, limpeza de legado comprovado, commit/push ff-only SOMENTE após gates PASS e relatório integral no arquivo. Não criar serviços/registries/consumers TARGET nem executar deploy sem autorização. Pare na revisão independente; não avance sozinho à etapa seguinte.
