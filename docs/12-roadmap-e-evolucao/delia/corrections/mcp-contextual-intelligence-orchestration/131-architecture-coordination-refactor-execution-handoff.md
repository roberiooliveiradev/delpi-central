# 131 — Handoff para Architecture / Coordination: review independente do plano R0–R7

**Data:** 2026-10-23  
**SCOPE:** DÉLIA — refatoração modular do orquestrador, inteligência reutilizável e fronteiras de Automation Hub/RPA.  
**PLAN_ID:** DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01.  
**PAPEL:** Architecture / Coordination é reviewer e responsável por gates, ownership, drift e aceite; Devin é executor.  
**STATUS:** HANDOFF_ONLY. Não é autorização de R0–R7, feature, RPA, deploy ou avanço de fase. Não substitui o prompt já recebido pelo chat de coordenação.

## 1. Estado verificável ao preparar o handoff

- GitHub repository: roberiooliveiradev/delpi-central; branch canônica main. HEAD observado antes deste documento: f0fceaba71d1e96b3f9de56aebb2bd6d55614523. Esse SHA é histórico; o novo chat deve revalidar o HEAD atual e sua árvore/ledger. Não houve inspeção local de git status pelo autor do handoff.
- Refactor R0–R7: **NOT_AUTHORIZED / NOT_STARTED** segundo docs 125, 129, 130 e arquivos de etapa (templates). Nenhuma etapa aceita.
- Último review do remediation D5: doc 127, ACCEPT_WITH_RESIDUAL; D5 PARTIAL, D5-R PASS reportado, D8-R PARTIAL naquela amostra, plano 112 não fechado. Código D5 commit ea2f59e930, review doc127 commit 5bd31225fe61.
- Estabilização funcional pré-refactor: existe commit de código 072629e67b78b2b8d48f4c6fa41b0ebb3f286afe. Não confundir commit de runtime com homologação aceita; verificar relatório posterior, evidências e review independente no HEAD antes de liberar R0.
- Docs 128–130 e templates R0–R7 foram criados; todos os templates inspecionados ainda eram NOT_STARTED / NOT_AUTHORIZED quando este handoff foi preparado. Arquivos de template não são prova de execução.
- Fase NEXT canônica continua exclusivamente sob docs 16 + ledger no HEAD; nenhum texto de handoff a altera.

## 2. Autoridades, fontes e decisões congeladas

Reancorar a CADA review/etapa: HEAD/git status/origin-main → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → 24 → 03/60 e specs temáticas → execution ledger. Confrontar CP/RQ, contracts, consumers, status de fase e diff SHA.

Docs vinculantes desta trilha:
- 56/57: auditoria estática e grupos F01–F42.
- 58: ADR — LLM owner da proposta semântica, determinístico de contratos/segurança; selection-only congelado onde aplicável.
- 59: roadmap histórico Q01–Q03 e B1 diferido; não reabrir por refactor.
- 112/113: autoconhecimento/matriz de responsabilidade.
- 117: S4 SKIP_WITH_DECISION para guidance/apresentação sem destino leaf legítimo; não anular silenciosamente.
- 124, 126, 127: D5 — contrato, implementação/report e parecer independente, respectivamente.
- **125:** plano principal R0–R7 e lotes M01–M10, organização, contrato e anti-monólito.
- **128:** arquitetura cross-application e RPA; previsão não é implementação.
- **129:** AP-01…AP-20, allowed-file gates, owners, segurança, shared modules, legado e reviews.
- **130:** playbook integral; sequência, auto-rework bounded, prompts e relatórios por etapa.
- **refactor-r0-r7/r0-execution-and-evidence.md até r7-execution-and-evidence.md:** cada arquivo contém prompt pronto da sua etapa, whitelist preliminar, provas e relatório obrigatório preenchível.
- **.cursor/rules/delia-execution-protocol.mdc**, **platform-architecture-boundaries.mdc**, **architecture-ci-enforcement.mdc** e outras regras aplicáveis.

Nenhum doc inferior reclassifica TARGET em PROVEN, muda owner ou concede autorização. Em conflito, STOP → EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED.

## 3. Destino final (não pode ser reduzido a quantidade de linhas)

Ao término, orchestration.py mantém sequencing, propostas LLM tipadas, seleção/revalidação provider-neutral, orçamento, contexto governado, invocação por ports e PREPARE/ACT com gates. Evidence/Outcome/presentation/guidance/schema validation/recursos declarativos só se deslocam aos owners legítimos, sem importar orquestrador em leaves ou duplicar sanitizadores. Os contratos de inteligência devem ser utilizáveis internamente por entrypoints legítimos além do chat sem depender desnecessariamente de ConversationTurn/Markdown/React; isso NÃO autoriza novos consumidores fictícios.

Reuso ENTRE aplicativos, quando houver consumidor concreto, exige contrato HTTP/eventos, AuthN/AuthZ/versionamento e decisão separada; jamais import de código interno ou banco alheio. DÉLIA planeja/decide/verifica; Automation Hub executa RPA tecnicamente; Domain API prova regra e pós-condição; Core autoriza; Keycloak identifica. Technical DONE não é business VERIFIED.

**Fins não justificam meios:** teste verde, output correto, HTTP 200 ou LOC reduzido não compensam antipadrões AP, violações de contrato, arquitetura, segurança ou manutenção de código OBSOLETE_PROVEN.

## 4. Sequência de trabalho e gates

1. **Agora:** receber/revisar estabilização funcional e suas provas reais; comparar D4, D5, D5-R, D5-schema, D8, D8-R, N1 e PT-BR; verificar SHA, modelo/config, runtime e outcomes. Emitir review independente no repositório. A existência do commit 072629 NÃO libera R0.
2. **R0 — M01–M10:** somente após baseline aceita e autorização explícita do PO; document-first, inventário finito por símbolo/owner/consumer/contrato/legado, import DAG before/after planejado, destinos condicionais e freeze da matriz. Nenhum novo módulo/runtime no R0.
3. **R1 — M01:** recursos declarativos/instruções, lineage e loaders existentes.
4. **R2 — M02/M03:** projection, sanitização e trust por owner único.
5. **R3 — M04/M05:** Outcome e CRI sem authority de apresentação.
6. **R4 — M06/M07:** apresentação/guidance; honrar SKIP do doc117 até decisão com evidência.
7. **R5 — M08/M09:** argument validation e typed model proposal, sem lexical planner.
8. **R6 — M10 + resíduos M01–M09:** coordenador coeso, cleanup completo do legado comprovadamente obsoleto no escopo DÉLIA.
9. **R7 — todos os lotes:** matriz full/arch/security/generalization/outcome, limpeza e modularidade, revisão independente; release apenas em autorização operacional separada.

**GATE ENTRE ETAPAS:** Devin entrega evidência e preenche arquivo da etapa; coordenação verifica e publica parecer; próxima etapa só segue se PRECONDITIONS satisfizerem e houver autorização correspondente. Uma autorização de R0 não é permissão irrestrita de R1–R7.

## 5. Como revisar cada entrega do Devin

Não fazer review apenas lendo o relatório. No SHA exato:
- Confirmar HEAD, merge-base/base/final SHA, commit/diff e arquivos modificados; comparar ALLOWED_FILES/ACTUAL_FILES, worktree/remote, alterações concorrentes, contracts/interfaces e ledger. GitHub prova código versionado; SSH/prod requer evidência própria.
- Para cada função movida: origem → destino → owner → consumer real → boundary → equivalência existente → REUSE/EXTEND/NEW → contrato/erro/segurança → import/call DAG before/after → remoção da origem e dos callers mortos → regressão/teste → rollback.
- Vetar novo god module, shared sem dois consumidores reais, leaf importando orchestration, imports dinâmicos/ciclos, sanitizer/Policy/registry duplicados, segunda authority, provider/keyword branches, JSON com Policy executável, serviço RPA/worker na DÉLIA, external app acoplado a banco/import DÉLIA, schema tratado como business FACT, e progresso só baseado em LOC.
- Exigir classificação e evidência **AP-01 a AP-20** do doc129. Separar checks automatizados, revisão manual e checks não implementados; nunca declarar que o CI verifica tudo.
- Rodar/verificar focused+full backend, arquitetura, negativos de segurança, CRI ON/OFF, generalização provider add/remove/rename/reorder, model eval e outcomes correspondentes à alteração, no mesmo SHA/model/prompt/config. Para writes, exigir Core live, Domain authority, idempotência/audit/postcondition; nunca repetir ACT ambíguo.
- Distinguir PROVEN/TO_INVENTORY/PLANNED/TARGET e PASS/FAIL/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE. Sem generalização/outcome, CI verde não permite declarar NO_REGRESSION geral. Regressão zero se refere somente ao escopo efetivamente avaliado.
- Verificar legado: CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / TO_INVENTORY; remover no escopo todo OBSOLETE_PROVEN, aliases, wrappers, duplicação, imports/flags/docs/testes mortos com prova de consumers estáticos e dinâmicos. Não apagar ativos de Chat/Portal/Core/Domain/Automation Hub, histórico ou contratos compatíveis exigidos. Um SKIP aprovado não é legacy.

## 6. Auto-rework e STOP — uma única tentativa

Se regressão/AP reparável for PROVEN dentro dos arquivos, contrato e authority já autorizados:
1. BLOQUEAR merge/deploy/etapa seguinte.
2. Exigir que Devin **na mesma execução**, sem microconfirmação adicional, localize primeira divergência e crie/retenha RED.
3. Aplicar **um** rework mínimo bounded; reportar AUTO_REWORK_USED=1.
4. Reexecutar matriz integral focused/full/security/arch/generalization/outcomes no SHA final.
5. Só após gates materiais PASS pode haver commit/push ff-only e review independente.

Se persistir FAIL, se limite 1/1 acabar, se owner/contract/Policy/segurança/fase exigir outra autoridade, ou se não existir identidade/evidência governada: STOP com classificação apropriada e decisão da coordenação/PO. Não afrouxar testes, inventar PASS, adicionar retry infinito ou abrir patch fora do escopo.

## 7. Relatórios de etapa e revisão independente

Devin deve preencher o arquivo r{n}-execution-and-evidence.md do próprio estágio: TASK_ID/STEP, AUTHORIZATION_REF, baseline & SHAs, authorities+CP/RQ, whitelist, owner/consumer/contracts, EXIS_EQ/REUSE, files+diff, function map, DAG, AP statuses, suite+AI eval+outcomes+negatives, compare regressions, legacy removido, rework 0/1, rollback, README/ledger e gaps. Templates NOT_STARTED não contam como PASS.

A coordenação **preenche seção reservada de review** (idealmente em commit documental próprio), emite:
ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE,
com evidência concreta, blockers/material residuals, NEXT_ALLOWED_STEP e AUTHORIZATION_STATUS. ACCEPT_WITH_RESIDUAL nunca mascara AP blocker ou outcome material. Publicar doc/ledger somente com fatos, e não autopromover C-phase ou PLAN_COMPLETE.

Relatório de review sugerido:
REVIEW_TASK, STEP, REVIEWED_SHA, CURRENT_HEAD, SCOPE/ALLOWED_DIFF, CONTRACT_PARITY, AP01_AP20, FULL_BACKEND, GENERALIZATION, SECURITY, REAL_OUTCOME, LEGACY_REMAINING, AUTO_REWORK_USED, EXECUTION_DRIFT, RESIDUALS, VERDICT, NEXT_ALLOWED_STEP, AUTHORIZATION_REQUIRED.

## 8. Próxima ação bounded para o novo chat

1. Reancorar no HEAD + authorities + ledger atuais e conferir etapa de estabilização funcional (commit 072629 e sucessores).
2. Receber relatório Devin de estabilização; auditar resultados/SHAs e publicar parecer **antes** de qualquer R0.
3. Após a baseline aceita e autorização de PO, encaminhar Devin ao prompt **já existente** em r0-execution-and-evidence.md, e assim sucessivamente com review por etapa. Não gerar outro prompt mestre duplicado, não reabrir auditorias ilimitadas.
4. Retornar sempre com aceite/rework/gap objetivo e critério de saída; o chat de coordenação não executa nem aceita código por analogia a resultados do executor.

**HANDOFF FINAL:** CHAT=contexto; GitHub=verdade persistente; ledger=estado de execução; authorities=verdade de produto/arquitetura. Este documento é informativo, não uma permissão de execução.
