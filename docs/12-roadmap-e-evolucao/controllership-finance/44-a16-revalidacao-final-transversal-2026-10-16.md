# 44 — A16: Revalidação transversal final com evidências (16/10/2026)

> **Parecer:** `INCONCLUSIVE` para o fechamento documental **integral**. As escolhas C2, P5-A..J e DEC-01..04 permanecem `TARGET / PO_APPROVED`. Esta revisão corrige divergências históricas sem tocar runtime, mas não aprova produto, novo contrato Core, scope ou implementação por inferência.
>
> **Gate vigente:** `A12=INCONCLUSIVE`; `A14=INCONCLUSIVE`; `A15=INCONCLUSIVE`; `A16=INCONCLUSIVE`; `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`; `RUNTIME_TESTS=TEST_NOT_RUN`. O roadmap [39–43](./39-roadmap-mestre-implementacao-v1.md) segue documentado, não executado.

## 1. Baseline, authorities e escopo de prova

- **HEAD de código/docs inspecionado:** `d8457ef3e78776e49675cc370ced0b800cc29192` na `main` (16/10/2026). Reconsulta subsequente observou `88b796e153ad5bb76f9dbf4ebde9d7bb2f664705`; compare mostrou apenas alterações em DELIA, plugin-ui *markdown lexer/probe* e Production Control, sem mudança dos controllers/modelos Core ou docs do Portal inspecionados. Revalidar o HEAD fresco após este PR; não reutilizar evidência se nova alteração material ocorrer.
- **Git status local:** `INCONCLUSIVE` — revisão por GitHub API sem checkout/worktree; o merge de PR não é prova de worktree clean.
- **Fonte de autoridade:** [instruções oficiais](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md), regras aplicáveis de `.cursor` (centralized/evidence/architecture/security/API contracts/testing/frontend/help), contratos P5/P6, Core no HEAD, testes do Core, docs técnicas vigentes e roadmap. O documento 33 `133–168` estabelece: inventários físicos podem ser `TO_INVENTORY` somente quando não ocultarem escolha material de produto, integração, ownership, state ou AuthZ.
- **TÉO/AS-IS:** consulta read-only de `PROC-0072` (processo `21f70cd0-d513-46f5-bfcf-29ae5573f2f6`) confirma processo ativo, uma instância de fechamento e baseline aprovado; resumo da instância registra `AS-IS=CLOSED/ACCEPTED` e `IMPLEMENTATION=NOT_STARTED`. ID e provenance conferem com [19](./19-rastreabilidade-teo.md). A diferença entre AS-IS e submissão portal-first TARGET é redesign aprovado, não drift. Não reescrever o AS-IS no GitHub.
- **Inventário de runtime:** árvore Git da `main` inspecionada sem caminhos `plugins/controllership-finance/` ou `controllership-finance-api/`. Isto prova somente a ausência nos paths examinados do HEAD, não a inexistência em branches ou a ausência futura.
- **CI de plataforma:** no SHA `d8457ef3...`, `api-tests`, `console-build` e `architecture-gate` passaram (GitHub Actions). Esses jobs são da plataforma e **não** comprovam um teste de runtime do Portal, porque o runtime ainda não foi implementado. Smoke Portal = `TEST_NOT_RUN`.

## 2. Core T05 — producer/consumer, o que é e não é PROVEN

| Evidência no HEAD | Fato verificável | Classificação |
|---|---|---|
| [Core S2S effective-access controller](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/interfaces/http/integrations_effective_access_controller.py), [use case](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/application/use_cases/get_effective_access_by_subject_use_case.py) | S2S autenticado e dedicado; `GET /integrations/effective-access/subjects/{keycloak_sub}` retorna `userId`, `keycloakSubject`, `permissions`, `isSuperadmin`. Resolver Core é authority; 404/503 são diferentes de lista vazia e não há fallback email. | `PROVEN` em source; live request não executado |
| [Core S2S directory](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/interfaces/http/integrations_directory_controller.py), [search use case](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/application/use_cases/search_directory_users_use_case.py) | Busca/roster por app e permission, identidade ativa; payload observado `id/name/email`, **não atributo funcional corporativo de área**. | `PROVEN` para payload inspecionado |
| [Core RBAC Group model](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/infrastructure/db/models/group.py) e [User model](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/infrastructure/db/models/user.py) | Existem grupos RBAC e memberships de usuários; o modelo `Group` tem `id/name/description/active`, sem dimensão tipada de “área corporativa obrigatória”. Grupo RBAC **não é automaticamente** função organizacional P5. | `PROVEN` estrutura; equivalência corporativa `TO_INVENTORY` |
| [Core access-profile use case](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/application/use_cases/get_user_access_profile_use_case.py) | Devolve grupos/roles/effectivePermissions para perfil de acesso, inclusive fluxo `/me/access-profile`. Isto **não** autoriza o BFF a usar endpoint self ou consultar tabelas internas como API S2S. | `PROVEN` contrato self; integração P5 `TO_INVENTORY` |
| [Core testes effective access](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/tests/test_integrations_effective_access.py) | Há cobertura de 401/403/404/503, identidade/sujeito e resolver; testes existentes não são contract tests de grupo/função→área P5. | `PROVEN` source dos testes; não foram reexecutados isoladamente nesta revisão |
| [Core person profiles](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/interfaces/http/integrations_person_profiles_controller.py), [notifications](https://github.com/roberiooliveiradev/delpi-central/blob/d8457ef3e78776e49675cc370ced0b800cc29192/core-api/app/interfaces/http/notifications_controller.py) | Leitura de perfil/foto S2S e entrega de notificações possuem contratos existentes, sem conferir acesso ao pacote nem alterar estado de submissão P5. | `PROVEN` source; consumers Portal não implementados |

**STOP de integração material:** nenhuma das respostas S2S inspecionadas fornece hoje o contrato corporativo tipado **`required_area ← Core group/function eligibility`** que P5-C/H exigem. Não criar permission `.review`, não confiar em grupo arbitrário pelo nome, JWT, diretório autocomplete ou BFF SQL direto na base Core. Primeiro inventariar quem é owner do atributo corporativo e quem publica o contrato S2S; uma escolha arquitetural/material posterior deve receber decisão e testes de producer/consumer. `T05_CORPORATE_ELIGIBILITY_BINDING=TO_INVENTORY / STOP_BEFORE_P5_WRITES`.

## 3. A12 — P5: semântica aprovada × residual material

**TARGET validado contra 04, 12, 13, 14, 23, 27, 29, 35 e 37:**

- `Finalizar != Enviar`. Finalizar cria PackageVersion imutável; submissão é **in-portal**, reviewer autenticado na Minha DELPI; Core email é notificação opcional e falha de delivery não altera business state.
- `C2`: todos pacotes aplicáveis submetidos, **um aceite por área obrigatória do snapshot para PackageVersion atual**, nenhuma clarification aberta e competência não rejeitada terminalmente. Nova versão reinicia os aceites; reatribuição conserva autoria e aceite anterior.
- `P5-C`: ACCESS efetivo via Core **AND** grupo/função corporativa elegível **AND** área e versão **AND** resource scope/ownership **AND** business rule, backend fail-closed.
- `P5-I/DEC-01/02`: rejeição por reviewer de área/pacote gera decisão pendente, não conclusão/rejeição mensal automática. Coordenador formal da competência com ACCESS/vínculo/scope confirma terminalmente com reason/audit; se não confirmar, permanece pendente e pode devolver para esclarecimento/correção em transição auditada.
- `DEC-03`: nenhum endpoint/UI de reversão/retificação do aceite P5 na V1; incidentes fora do fluxo. `DEC-04`: MANAGE + escopo administrativo publica P6 versionado com reason e vigência prospectiva; snapshots anteriores preservados. TaskProjections ficam não acionáveis após rejeição terminal, histórico mantido.

**Reparos documentais nesta revisão:** substituídos adendos que ainda pediam DEC-01/02/03 já decididas, corrigida unanimidade de indivíduos para áreas, corrigida projeção P5 individual para obrigação por área, corrigida a regra C2 em 04/12/17/18/29/35 e incluído scope de publicação P6 em 13/23/28; ver diff desta PR. **Não** inventar identificador físico para o estado de competência rejeitada.

**Pendências antes de A12 PASS / freeze:** (i) source/contrato Core de grupo/função e mapeamento P6↔área; (ii) designação formal do coordenador e prova de vínculo por competência; (iii) semântica não explicitada para **configuração P6 vazia ou sem áreas obrigatórias** — pode permitir conclusão C2 vacuamente, exige decisão de produto; (iv) estados/DTOs, callbacks/events/OCC e snapshot físico como `TO_INVENTORY`, com stop nos slices. Estas lacunas não são resolvidas por testes genéricos ou supor grupo RBAC como corporate function.

**A12 = INCONCLUSIVE para fechamento completo** (contrato semântico aprovado, documentação mais consistente; decisões/integração material pendentes). Testes de Portal = `TEST_NOT_RUN`.

## 4. A14 — coerência transversal

| Eixo | Evidência | Resultado documental |
|---|---|---|
| Naming e paths | README/18/21/39: plugin `controllership-finance`, MFE e BFF base paths congelados | `PASS` para coerência de documentos; nenhum runtime |
| Permissions e boundaries | 14/21/34/39: somente `controllership-finance.access/manage`, JWT não authority, MFE→BFF, Core/api-delpi/strategic owners | `PASS` para contrato abstrato; Core P5 corporate binding `INCONCLUSIVE` |
| UX/navegação/plugin-ui | 24–32, 30; exports no `plugins/plugin-ui/src/index.ts` (PortalUserProfile, TaskWorkspace, InteractionRoom, UserManual), mesmas famílias/light-dark/mobile/a11y | `PASS` de rastreabilidade documental; build MFE Portal `TEST_NOT_RUN` |
| Ajuda/Help | 29 e regra `feature-help-sync`, catalogo só runtime real, P5 tarefas por área e status | `PASS` para alinhamento do plano; Help runtime `NOT_IMPLEMENTED` |
| Owners/integrações | 21/34 e source controllers Core; estado P5 owned BFF, TOTVS owner api-delpi, strategic scores owner estratégico | `PASS` nos boundaries definidos; binding corporativo S2S `TO_INVENTORY` |

**A14 = INCONCLUSIVE** global por fronteira Core T05 de elegibilidade corporativa ainda não contratada/provada; “PASS documental” da interface não vira segurança runtime. Se fonte corporativa real contrariar o owner/permission model aprovado, classificar `EXECUTION_DRIFT` e parar.

## 5. A15 — RQ/AC, contratos e testes PLANNED

- [23](./23-ledger-rq-ac-testes.md) cobre RQ-P1..P6, RQ-USER/HOME/OVW/TASK/ROOM/ADM/HELP, RQ-SEC-01..06 e RQ-UX-01..06; identificadores de RQ nas páginas individuais examinadas constam no ledger. P3/P6 usam AC em suas páginas e ledger, mesmo onde não repetem “RQ-” no texto.
- [35](./35-contratos-regras-scripts-test-matrix-gate-v2.md), [41](./41-estrategia-validacao-e-gates-implementacao-v1.md) e [40](./40-matriz-dependencias-e-slices-v1.md) definem cenários **positive/sibling/negative**, state/UX, permissions e boundaries por slice.
- RQ-P5-AREA-01..04, RQ-P5-TERM-01..03, RQ-P5-F..J e DEC-01..04 agora mapeiam quórum, nova versão, reatribuição, authz, rejeição pendente/confirmada, incidentes, tarefas e P6 scope.
- Scripts `validate-p5-*` são **PLANNED**, não executados nem presumidos existentes. Source tests Core observados não verificam outcome P5. Smoke Portal não executado.
- Contract tests de eligibility Core (sujeito, grupo/função, vínculo, área, scope, 404/403/503) e P6 snapshot/version/OCC devem ser derivados **após** o contract owner/caller binding acordado e inventariado.

**A15 = INCONCLUSIVE** para freeze de contratos/testes de integração, embora a estratégia de testes documental esteja mapeada. `TEST_STRATEGY_DESIGN=COVERED` não é `TEST_STRATEGY_FREEZE=PASS`.

## 6. A16 — checklist normativo do documento 33

| Critério do doc 33 `681–699` | Evidência / exceção | Situação |
|---|---|---|
| Todas as superfícies V1 e P1–P6 possuem authorities | páginas 08–13, 24–32, mapa 30; roadmap 39–43 | `PASS` documental |
| Páginas comuns, UX, Help e kit coerentes | 23/24–32 e 30; corrigidos legacy P5 e links | `PASS` documental |
| Regras TARGET consolidadas / AS-IS separado | 04 corrigido; TÉO vigente e mapa 19 conferidos | `PASS` documental |
| E01–E06 e T01–T05 classificados | 17, 33; E04/T04 SUPERSEDED; T03 e T05 com stop de owner | `PASS` para classificação; `TO_INVENTORY` material |
| Segurança 14, configuração 16, boundaries 21, RQ/AC 23 | cruzamento de documentos corrigido; source Core inspecionado | `PASS` de rastreabilidade documental |
| Nenhuma escolha material disfarçada de inventário | corporative group/function mapping Core e **zero mandatory areas P6** alteram AuthZ e C2 | **`INCONCLUSIVE / DECISION_REQUIRED`** |
| Nenhum state conflitante ou capability antecipada | scan temático corrigido; não há MFE/BFF no HEAD examinado | `PASS` scoped documental; não é runtime |
| README/18 status final e residual auditável | atualizar para referenciar este relatório e o SHA da PR | `PENDING` até merge |
| `IMPLEMENTATION_AUTHORIZED=NO` | preservado em docs | `PASS` |

**A16 = INCONCLUSIVE.** Não emitir `DOCUMENTATION_CLOSURE_COMPLETE=PASS` por checklist parcialmente satisfeito. Quatro freezes: `PORTAL_DESIGN_FREEZE=REVALIDATE`; `PRODUCT_CONTRACT_FREEZE=PENDING`; `SECURITY_MODEL_FREEZE=PENDING_T05`; `TEST_STRATEGY_FREEZE=PENDING_CONTRACT_TESTS`.

## 7. DECISION_REQUIRED — lacunas materiais novas comprovadas

### D-FINAL-01 — fonte corporativa de elegibilidade por área (Core T05)

**Achado:** Core possui grupos RBAC com nomes/descrições, mas os contratos S2S effective-access/directory atuais não expõem função/área corporativa tipada ao BFF. A authority de elegibilidade **não pode ser inferida** de grupo de permissão, email ou perfil self. A regra P5-C exige efetivamente grupo/função.

- **Opção A:** Core adota grupo RBAC explicitamente designado e governado como representação da elegibilidade corporativa P5; requer contrato S2S específico, vínculo tipado P6↔grupo e testes; risco de confundir grupo de permission com função.
- **Opção B:** usar a fonte corporativa **já canônica**, se encontrada no inventário de RH/Core/identidade, integrando ao Core S2S; requer owner/contrato e possível adaptação. Melhor semântica quando essa fonte existir.
- **Opção C:** atribuição operacional manual P5 sem fonte grupo/função; **mudaria P5-C** e exige decisão explícita de produto, não é fallback técnico silencioso.

**Recomendação condicionada a evidência:** inventariar source corporativo com owner, depois preferir **B se PROVEN**, senão submeter A versus nova capability Core à decisão. Não criar endpoint/token/permission antes dessa decisão e da revisão de segurança.

### D-FINAL-02 — tipo de pacote sem área obrigatória válida

**Achado:** regra C2 exige um aceite por cada área obrigatória, mas documentos não resolvem explicitamente se P6 pode publicar configuração com zero áreas obrigatórias para um tipo de pacote, nem o que fazer quando não há configuração válida na submissão.

- **Opção A (recomendada V1 para segurança e integridade):** não permitir publicação/submissão sem ao menos uma área obrigatória válida, recusando submit com erro de configuração, até regularização P6.
- **Opção B:** permitir explicitamente tipo sem review obrigatório, com exceção P6 versionada e autorizada, evidência de motivo e C2 ajustada para não exigir área nesse tipo; risco de fechamento sem revisão.
- **Opção C:** separar “ausência de configuração” de “configuração intencional com conjunto vazio”, proibindo ausência mas permitindo vazio só sob política especial; contrato mais complexo, exige novos AC/testes.

**Não selecionar por este relatório.** Owner de decisão: PO; impacto material em quórum C2, P6 snapshot, UX de submit, audit e test matrix.

## 8. Residuais técnicos e próxima passagem

| ID | Quem é owner | Ação/verificação exigida (sem runtime neste gate) | Evidência de saída |
|---|---|---|---|
| T05 corp function | Core owner + função corporativa + P5 consumer | Fonte org, API S2S e vínculo tipado, service caller binding, scopes/403/503 | contrato aprovado pelo owner, testes planejados, decisão D-FINAL-01 se necessária |
| P5 coordinator | P5 operational owner, Core identidade/permissão | vínculo de coordenador por competência, reatribuição auditada, fail-closed | contrato de assignee e RQ-TERM/DEC-01/02 |
| P6 snapshot/empty | P6 owner e PO para regra de vazio | D-FINAL-02, requiredAreas por package type, vigência e imutabilidade; OCC | acordo de produto + DTO/versioned policy e AC |
| T03 ERP | api-delpi / owner canônico TOTVS | source de `STOCK_CLOSED` e leitura sem reabertura Portal V1 | T03 PROVEN ou STOP no IMP-10 |
| P5 DTO/eventos/OCC | BFF do Portal após gate de design | requests/responses/states canonizados sem inventar service; tests P5/P6 | contract inventory e matrix atualizada |
| CI/runtime | owners + executor no slice autorizado | teste do Portal e smoke real, ledger por SHA, Help feature-gated | `PASS` apenas após execução; agora `TEST_NOT_RUN` |

**Stop line:** sem decisão sobre a regra de conjunto vazio e fonte autorizada de elegibilidade, não liberar submissão/revisão P5 nem fechar os freezes globais. A primeira página candidata de implementação continua **Página do usuário**, **somente após** gate transversal completo e autorização explícita posterior do usuário; aprovação do roteiro ou merge deste documento nunca são esse gate.

**Veredito final: INCONCLUSIVE**. Está documentado o que é `PROVEN`, o que é `TARGET`, o que é `PLANNED/TO_INVENTORY` e o que exige decisão de autoridade. Nenhuma mudança de runtime, endpoint, schema, manifest, migration ou permission foi efetuada por esta revisão.