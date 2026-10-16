# 38 — Rebaseline pós-merge, evidências e gate transversal (16/10/2026)

## Estado e alcance

**TARGET / EVIDENCE_REVIEWED / A12+A14+A15 INCONCLUSIVE.**

```text
DOCUMENTED != IMPLEMENTED
GIT_PR78_MERGED_IN_MAIN = PROVEN
PRODUCT_P5_DECISIONS_C2_P5A_TO_J_DEC01_TO_04 = TARGET / PO_APPROVED
PORTAL_PRODUCT_RUNTIME = NOT_IMPLEMENTED (inventário de paths do HEAD examinado)
A12_POSTMERGE = INCONCLUSIVE
A14_POSTMERGE = INCONCLUSIVE
A15_POSTMERGE = INCONCLUSIVE
PRODUCT_CONTRACT_FREEZE = PENDING_CORE_T05_AND_PHYSICAL_BINDINGS
SECURITY_MODEL_FREEZE = REVALIDATE_CORPORATE_ROLE_SCOPE
TEST_STRATEGY_FREEZE = REVALIDATE_MATRIX_AND_CI
DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED = NO
PORTAL_RUNTIME_TESTS = TEST_NOT_RUN
```

**Baseline imutável da investigação:** HEAD observado de `main` `58d53f52ca0868983c932a2015f2fedca02102ca` (16/10/2026), posterior ao merge documental PR #78 em `984e7c964482e87886d60b0d8f1f9798c86c452e`. Novos commits exigem rebaseline antes da implementação ou mudança de status. Não houve checkout local controlado para provar `git status`; estado de worktree é `INCONCLUSIVE`. Este relatório é documental, não smoke de runtime.

Authorities: instruções oficiais do Arquiteto; `.cursor` canônico (oito owners); ADRs/contratos; HEAD; testes; docs técnicas; planos e histórico. Contratos semânticos vigentes: docs 12, 13, 14, 23, 27, 29 e 37; docs 33–35 registram gates e evidência. AS-IS permanece authority do TÉO; nenhum AS-IS foi redefinido nesta auditoria.

## 1. Evidência Git e configuração

- **PROVEN:** [PR #78](https://github.com/roberiooliveiradev/delpi-central/pull/78) merged; documentação presente em `main`.
- **PROVEN:** inventário de diretórios `plugins/` e raiz do HEAD examinado não mostrou `plugins/controllership-finance` nem `controllership-finance-api`. Isto prova somente o estado dos paths verificados, não prova de inexistência de qualquer proposta em branches.
- **PROVEN:** [instruções oficiais](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md) exigem JWT validado, Core effective permission, Clean Architecture, manifesto `schemaVersion 1.0.0` e testes.
- **PROVEN:** as regras OpenAI Plugin/MCP e Workspace Agent já declaram `platform-api-contracts-integration.mdc` como owner primário. O mapa e o inventário omitiram ambas, causando falha de `Cursor Rules Governance`; correção mínima de metadata foi preparada nesta branch e **validada pelo CI Cursor Rules Governance na PR #80** ([job 117036525022](https://github.com/roberiooliveiradev/delpi-central/actions/runs/38919816710/job/117036525022), conclusão success).
- **PENDING:** não inferir `git status` local, testes de produto ou smoke a partir de merge/HTTP 200.

## 2. Contratos de plataforma verificados no HEAD

| Capability/owner | Evidência de código (source, não smoke) | Classificação |
|---|---|---|
| Core: permission resolver | [`core-api/app/domain/services/permission_resolver.py`](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/domain/services/permission_resolver.py); resolução por role, group e override | PROVEN |
| Core: effective access S2S | [`GET /integrations/effective-access/subjects/{keycloak_sub}`](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/interfaces/http/integrations_effective_access_controller.py); service token, UUID, `permissions`, `isSuperadmin`, erros 404/503, sem fallback e-mail | PROVEN |
| Core: roster/directory S2S | [`GET /integrations/directory/users`, `/users/by-app`, `POST /users/lookup`](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/interfaces/http/integrations_directory_controller.py); service token | PROVEN |
| Directory eligibility | [`directory_user_eligibility_service.py`](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/application/services/directory_user_eligibility_service.py) filtra por status ativo, app e permission; [`search_directory_users_use_case.py`](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/application/use_cases/search_directory_users_use_case.py) retorna `id/name/email` | PROVEN para esses campos, **TO_INVENTORY para grupo/função corporativa** |
| Core: person profile S2S | [`GET /integrations/person-profiles/{user_id}` e foto](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/interfaces/http/integrations_person_profiles_controller.py); service token | PROVEN |
| Core: notificações | [`POST /integrations/notifications`](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/core-api/app/interfaces/http/notifications_controller.py); service token + rate limit | PROVEN |
| Plugin UI: Página do usuário | [`createDashboardPortalUserProfilePage` exportado](https://github.com/roberiooliveiradev/delpi-central/blob/58d53f52ca0868983c932a2015f2fedca02102ca/plugins/plugin-ui/src/index.ts), além de `TaskWorkspacePage`, `InteractionRoomPage`, `createDashboardUserManual` | PROVEN para exports, runtime Portal TEST_NOT_RUN |

**Limite de T05:** o retorno S2S de effective access comprova permission codes; o diretório consultado comprova app/permission, não um contrato canônico de grupo/função corporativa para determinar elegibilidade de cada área P5. **Search miss não autoriza concluir que esse contrato não existe em todo o Core.** Exigir inventário de owner/produtor/consumidor, fonte e AuthZ antes de criar endpoint, persistência ou chamar Core pelo browser. Não acrescentar permission code ao produto.

## 3. Decisões de produto coerentes — A12

**TARGET / PO_APPROVED:** C2; D-P5-01..05 refinadas por P5-A..J; DEC-01..04. Contrato vigente:

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED_FOR_REVIEW
AND EVERY_REQUIRED_AREA_ACCEPTED_CURRENT_PACKAGE_VERSION
AND NO_OPEN_CLARIFICATION
AND NO_TERMINAL_COMPETENCE_REJECTION
=> MONTHLY_CLOSING_COMPLETED
```

- `P5-A`: um aceite por área obrigatória, não por cada pessoa elegível. P6 versiona áreas por tipo de pacote, P5 congela o snapshot na submissão.
- `P5-C`: ACCESS efetivo **AND** elegibilidade de função/grupo **AND** resource scope/ownership **AND** business rule; avaliação na BFF, fail-closed. `MANAGE != ACCESS`.
- `P5-E/F/G`: nova PackageVersion exige novos aceites; reatribuição não transfere autoria nem invalida aceite já válido; sem retificação/reversão por UI **ou endpoint** na V1.
- `P5-I`/`DEC-01/02`: rejeição por área/pacote ≠ rejeição terminal da competência. Coordenador formal da Controladoria, com ACCESS/vínculo/scope, confirma com auditoria; sem confirmação, fica pendente com justificativa e possível devolução controlada.
- `P5-D/J`: terminal rejeitado ≠ concluído; projections de tarefas não mais acionáveis, histórico preservado.
- `DEC-04`: P6 publica configuração versionada com `manage` e escopo administrativo, prospectivamente.
- `CHANGES_REQUESTED != REVIEW_REJECTED`; package não sai por e-mail; notificação não reverte submissão.

**A12 — INCONCLUSIVE para freeze global**, não por nova escolha de produto conhecida: o contrato semântico agora está rastreado no doc 37 e no ledger 23, mas faltam bindings de elegibilidade corporativa, vínculo de coordenador, transições físicas, idempotência/OCC, eventos, P6 snapshot e testes de integração.

## 4. Revisão A14 — boundaries, frontend e Help

- **Naming** congelado: `controllership-finance`, MFE `plugins/controllership-finance`, BFF `controllership-finance-api`, rotas base `/apps/controllership-finance` e `/apps/controllership-finance-api`.
- **Permissions** somente `controllership-finance.access` e `controllership-finance.manage`. Não criar permission por área, reviewer, botão ou filial. JWT não é authority final.
- **Integração**: MFE → BFF própria → Core/api-delpi/strategic-indicators-api por adapters e contratos; sem import de domain/application alheio.
- **UI**: exports do kit confirmados, UX PT-BR, themes, keyboard/foco, responsividade, Help sincronizada à feature. Ver docs 30/31 e 29.
- **Minhas tarefas**: projeção self-only de trabalho P5 por **área** para cada usuário elegível; um aceite encerra a obrigação daquela área para todos os elegíveis, sem criar task entity.
- **Residual**: revalidar rotas, DTOs, scopes e Help no slice real; não usar PASS visual histórico como teste executado.

**A14 = INCONCLUSIVE / HISTORICAL_PASS_STALE_EVIDENCE.**

## 5. Revisão A15 — RQ/AC, scripts e regressão

Requisitos vigentes e AC detalhados em doc 23, incluindo `RQ-P5-AREA-01..04`, `RQ-P5-TERM-01..03`; scripts `validate-p5-*` no doc 12/35 são **PLANNED**, não arquivos executados. Matriz a executar:
- **Positive:** submissão após FINALIZED, quorum por área/versão, coordinator formal confirma rejeição, notifications/task projections coerentes, P6 snapshot preservado.
- **Sibling:** usuários elegíveis da mesma área não duplicam quorum; área B não herda aceite A; PackageVersion nova não herda aceites; recipient package B não muda por A.
- **Negative:** ACCESS sem elegibilidade; MANAGE sem ACCESS/vínculo; Core indisponível; deep link fora de scope; retificação P5 V1 proibida; conclusão com clarification aberta; rejection pending ≠ terminal; envio externo de anexos proibido.
- **Experience:** desktop/mobile, light/dark, foco/teclado, 403/404, loading/partial/error, deep link/F5, Help.

**CI observado:** `Cursor Rules Governance` falhou por duas regras órfãs (job [117018432945](https://github.com/roberiooliveiradev/delpi-central/actions/runs/38914517433/job/117018432945), teste unitário do auditor 4/4 passou). Correção declarativa no mapa + inventário desta branch foi validada pelo **CI PASS da PR #80**: 4/4 testes do auditor e `audit_cursor_rules.py` concluídos com sucesso.
Outro failure independente: `Architecture Enforcement` no [job 117025481133](https://github.com/roberiooliveiradev/delpi-central/actions/runs/38916581812/job/117025481133) falhou no teste `test_current_repo_artifacts_pass`: `GPT_ACTION_OPAQUE_OBJECT_NOT_EXPLICIT` no schema Transformômetro `POST /transformometro/gpt-actions/v1/governed-operations/prepare.properties.resolutions` sem `x-delpi-gpt-opaque-object`. **Owner = Transformômetro/OpenAPI**, não P5; requer correção do contrato pelo owner, sem enfraquecer assertion nem adicionar marker sem conferir o schema. Rastreio: [issue #81](https://github.com/roberiooliveiradev/delpi-central/issues/81). Reproduzido também no [job PR #80](https://github.com/roberiooliveiradev/delpi-central/actions/runs/38919816701/job/117036523369).

**A15 = INCONCLUSIVE.** Os testes planejados de runtime do Portal não rodaram: `TEST_NOT_RUN`.

## 6. Decisão do gate e próximo passo

| Controle | Estado | Para mudar para PASS |
|---|---|---|
| Decisões produto P5 | TARGET / PO_APPROVED | manter sem regressão no ledger e Help |
| A01 Página do usuário | TARGET / DOCUMENTARY_READY_WITH_INVENTORY | inventário binding Core e plugin-ui na primeira execução autorizada |
| A12 (P5) | INCONCLUSIVE | contrato Core função/grupo + scope/coordenador, P6 snapshot, estados/DTOs/eventos/OCC e AC verificáveis |
| A14 (transversal) | INCONCLUSIVE / STALE_EVIDENCE | rever cruzamento efetivo de páginas/owners, AuthZ, Help e contratos atuais |
| A15 (contratos/testes) | INCONCLUSIVE | artefatos de contrato/validação correspondentes + evidência positiva/sibling/negative, CI governado |
| .cursor governance | **PASS no CI da PR #80** | evidência: [job 117036525022](https://github.com/roberiooliveiradev/delpi-central/actions/runs/38919816710/job/117036525022); revalidar após eventual diff adicional |
| Architecture Enforcement externo | **FAIL reproduzido na PR #80** | [issue #81](https://github.com/roberiooliveiradev/delpi-central/issues/81), correção pelo owner do contrato e reexecução de CI |
| Documentation closure | NO | A12/A14/A15 revalidados + residual search e SHA |
| Runtime autorizada | NO | gate transversal explícito do PO após documentação fechada |

Se surgir materialidade nova de owner, permission, integração, breaking, persistência ou state machine, marcar `DECISION_REQUIRED` com evidência e não implementá-la por preferência.

**Veredito desta revisão: INCONCLUSIVE** para freeze final, com correções documentais propostas nesta branch e **governança Cursor PASS no CI da PR #80**; Architecture Enforcement permanece FAIL por contrato externo. A próxima página candidata continua **Página do usuário**, sem scaffold ou runtime até `IMPLEMENTATION_AUTHORIZED=YES` registrado por gate explícito. A PR #80 permanece sujeita à revisão de CI; CI verde parcial não é aprovação global.
