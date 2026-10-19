# 35 — A15: Contratos Semânticos, RQ/AC e Matriz de Testes V1

> **Estado vigente em 19/10/2026:** `A15=PASS_DOCUMENTAL`, `TEST_STRATEGY_FREEZE=PASS_PLANNED`. Nenhum script ou teste de Portal foi executado nesta revisão: `RUNTIME_TESTS=TEST_NOT_RUN`. A especificação é a base para escrever contratos físicos e validar o outcome no **slice owner**, não é OpenAPI existente. Fonte do gate: [33](./33-plano-mestre-fechamento-documental.md), [44](./44-a16-revalidacao-final-transversal-2026-10-16.md).

## 1. Fontes de teste, requisitos e contrato

| Famílias | RQ/AC e semântica | Source de implementação futura |
|---|---|---|
| A01 perfil usuário | RQ-USER-01..09, D1=B/D2=A, same-app membership e privacidade RBAC | [31 — Página do usuário](./31-pagina-do-usuario.md), [Core contracts no 44](./44-a16-revalidacao-final-transversal-2026-10-16.md) |
| A02 Home | RQ-HOME-01..09; H01–H04 | [32](./32-inicio-home.md) |
| A03 Visão geral | RQ-OVW-01..10; O04/O05, ownership de indicadores | [25](./25-visao-geral-indicadores-financeiros.md) |
| A04 Minhas tarefas | RQ-TASK-01..12, projection self-only, owners P2/P4 e P5 por área | [27](./27-minhas-tarefas.md) |
| A05 Sala | RQ-ROOM-01..12, ACL/contexto/mensagens, sem task automática | [26](./26-sala-de-interacao.md) |
| A06/A13 Administração/P6 | RQ-ADM-01..12, RQ-P6, MANAGE+administrative_scope, version/OCC/snapshot | [28](./28-administracao.md), [13](./13-p6-administracao-e-configuracao.md) |
| A07 Ajuda | RQ-HELP-01..12, manual kit, runtime-feature gating e mesma PR | [29](./29-ajuda.md) |
| A08–A11 P1–P4 | RQ-P1..P4, snapshot/evidência/P3 R$ 0,00/`STOCK_CLOSED`/P4 owner | [08](./08-p1-cockpit-da-competencia.md)–[11](./11-p4-classificacoes-e-pendencias.md) |
| A12 P5 | RQ-P5-01..12, RQ-P5-AREA-01..06, RQ-P5-TERM-01..03, C2/P5-A..J/DEC-01..04/D-FINAL-02 | [12](./12-p5-pacote-finalizacao-e-envio.md), [37](./37-p5-submissao-e-revisao-no-portal.md) |

**Ledger íntegro:** [23 — RQ/AC/Tests](./23-ledger-rq-ac-testes.md) é o índice de IDs e postconditions. [41 — matriz detalhada](./41-estrategia-validacao-e-gates-implementacao-v1.md) define positivo, sibling/isolamento, negativo, UX, segurança e smoke. Scripts listados em documentos antigos `validate-p5-*`, `validate-user-*` etc. são **PLANNED**, não pressupor arquivos ou CI jobs existentes.

## 2. Contratos transversais já decididos

1. **AuthN/AuthZ:** JWT validado para identidade, Core como authority final de `access/manage`; backend exige permission efetiva **AND** scope/ownership **AND** regra de negócio. Não criar permission por área, reviewer, página, botão ou filial. Falha Core = fail-closed.
2. **Fronteira:** MFE→BFF própria; BFF integra por adapters HTTP/contrato; Core, api-delpi e strategic-indicators-api mantêm domínio e armazenamento. Domain não importa HTTP/ORM/SDK.
3. **P5:** `Finalizar` congela PackageVersion imutável; `Enviar` submete no Portal; notificação não é conclusão. C2 exige pacotes aplicáveis submetidos, **aceite humano real por pacote/versão**, um aceite por área obrigatória existente, sem esclarecimentos abertos nem rejeição terminal. **Sem revisor o processo permanece pendente**, sem trava adicional antes da submissão/publicação e sem aprovação automática por conjunto vazio.
4. **Rejeição P5:** rejeição de reviewer não encerra competência; coordenador com ACCESS/vínculo/scope confirma com motivo (DEC-01/02); estado pendente na recusa; `REJECTED` terminal ≠ `MONTHLY_CLOSING_COMPLETED`. Reatribuição não reescreve autoria; nova versão não herda aceites; nenhuma reversão UI/API na V1 (DEC-03).
5. **P6:** configuração versionada por tipo de pacote, snapshot no envio, publicação com MANAGE + scope administrativo + justificativa/audit prospectivamente (DEC-04).
6. **P3:** `STOCK_CLOSED` terminal Portal V1 e diferença de conciliação **exatamente R$ 0,00**. Fonte canônica TOTVS via owner api-delpi, T03 como stop local na P3.
7. **Frontend:** reusar `@delpi/plugin-ui`, uma árvore para claro/escuro; PT-BR, mobile/desktop, teclado/foco e Help atualizada **no mesmo diff user-facing**.

## 3. Contratos físicos que precisam de prova no seu slice

| Slice | Required inventory antes do primeiro diff daquele contexto | Não fazer |
|---|---|---|
| **IMP-01/A01** | APIs S2S Core effective-access, directory lookup/by-app, person-profile/foto; BFF/auth adapter existentes e padrão MFE/manifest; response/errors, target same-app membership | Criar permission nova, DB local de usuários, browser→Core, trocar padrão API sem authority |
| IMP-03 | strategic-indicators-api KPI owner/source/fórmulas e unidade/freshness | cálculo ou zero inventado |
| IMP-09/P2 | fonte templates/snapshots P6, storage e validação de evidência | upload tratado como aceite |
| IMP-10/P3 | T03 origem ERP e contrato canônico de cutoff/reconciliação | sacramentação local do ERP |
| IMP-12/P5 | **Core T05 corp eligibility**, atribuição do coordenador, areas P6/snapshot, estados/DTO/eventos/OCC/notification/task projection | RBAC local; concluir sem humano; reverter aceite; bloquear Enviar por contagem de pessoas |
| IMP-13/P6 | version/validity, audit, OCC, snapshot e permissões administrativas efetivas | mudar versão existente retroativamente |

**Não usar falta do contrato P5 no Core para barrar IMP-01**, que consome contrato de identidade/perfil diferente já observado no Core. Falta de um contrato material no início de **seu próprio slice** → `TO_INVENTORY/INCONCLUSIVE`, investigação e eventualmente `DECISION_REQUIRED` antes de codificar.

## 4. Matriz obrigatória para a execução

Para cada RQ/AC no slice:

| Grupo | Exigência |
|---|---|
| Positive | autorizado executa ação, response correta e postcondition confirmada no owner |
| Sibling | outro usuário/competência/área/versão não recebe dado ou estado de parente |
| Negative | ACCESS≠MANAGE, 401/403/404/409/503, Core fora, scope indevido, estado inválido, source unavailable |
| Contract | producer/consumer DTO/OpenAPI/evento/schema, serialização, idempotência e OCC conforme write |
| UX e Ajuda | mobile/desktop, light/dark, foco/teclado, deep link/F5, LOADING/PARTIAL/ERROR, Help no mesmo PR |
| CI/smoke | execução real em SHA/ambiente indicado, verificação do objetivo; smoke não executado `INCONCLUSIVE` |

**A15 PASS é apenas a matriz e os requisitos escritos.** Nenhum teste de integração, CI ou smoke do Portal ocorreu; o primeiro comportamento será provado no IMP-01 autorizado. Não mudar testes para “passar” no CI.

## 5. Gate de saída

```text
A15_CONTRACTS_AND_TEST_STRATEGY = PASS_DOCUMENTAL
TEST_STRATEGY_FREEZE            = PASS_PLANNED
PHYSICAL_CONTRACTS_P3_P5_P6    = TO_INVENTORY_PER_SLICE
PORTAL_RUNTIME_TESTS            = TEST_NOT_RUN
IMPLEMENTATION_AUTHORIZED       = NO
```

Próximo trabalho técnico: **IMP-01/A01 Página do usuário** [18](./18-readiness-e-handoff-de-implementacao.md), [31](./31-pagina-do-usuario.md), [42](./42-playbook-brief-cursor-execution-report-v1.md). Sem inventar A17/gate documental adicional.
