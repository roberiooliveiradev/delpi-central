# Portal Controladoria & Finanças — Minha DELPI

> **Contrato vigente, 19/10/2026.** Primeira funcionalidade: **Central de Fechamento**, processo **PROC-0072 — Gestão do Fechamento Mensal da Controladoria**. Este README é o **ponto de entrada**; não duplicar aqui as especificações de cada página ou anexar novos relatórios para reiterar decisões fechadas.

## Estado único da fase documental e próximo passo

| Controle | Estado | O que significa |
|---|---|---|
| A01–A13 (13 superfícies) | **PASS documental** | Especificações, RQ/AC, UX/Help e owners definidos; nenhum runtime inferido |
| A12 / A14 / A15 / A16 | **PASS documental — com inventários vinculados ao slice** | Produto/segurança/testes definidos; os bindings físicos são verificados **no slice que os consome** |
| `PORTAL_DESIGN_FREEZE` | **PASS documental** | Páginas, navegação, `@delpi/plugin-ui`, estados e Ajuda |
| `PRODUCT_CONTRACT_FREEZE` | **PASS semântico** | P1–P6 e C2/P5/P6 definidos; dados de produtor/DTO/OCC ainda são `TO_INVENTORY` por slice |
| `SECURITY_MODEL_FREEZE` | **PASS modelo** | Core governa identidade/RBAC; BFF autoriza capability + scope + regra, fail-closed |
| `TEST_STRATEGY_FREEZE` | **PASS planejamento** | Positive/sibling/negative, contrato, UX, segurança e smoke descritos, **não executados** |
| `DOCUMENTATION_CLOSURE_COMPLETE` | **PASS — escopo documental V1** | Não equivale a OpenAPI materializado, scaffold, CI/smoke ou deploy |
| `IMPLEMENTATION_AUTHORIZED` | **NO — até comando explícito no novo chat** | Brief IMP-01 pronto; nenhuma escrita runtime nesta revisão |
| `RUNTIME_TESTS` | **TEST_NOT_RUN** | MFE/BFF do Portal ainda não implementados |

**Regra de progresso:** `TO_INVENTORY` de P3 (T03) ou P5/P6 (Core T05, coordenação, snapshot, OCC) bloqueia **somente o respectivo slice** quando material. **Não bloqueia A01 Página do usuário**, que depende de outros contratos do Core já identificados. Nova escolha material/owner não provado ao iniciar um slice → `DECISION_REQUIRED` ou `EXECUTION_DRIFT`, sem implementação especulativa. Ver [18 — readiness](./18-readiness-e-handoff-de-implementacao.md), [33 — critérios de fechamento](./33-plano-mestre-fechamento-documental.md) e [44 — evidência de revalidação](./44-a16-revalidacao-final-transversal-2026-10-16.md).

## Identidade e limites congelados

| Dimensão | Contrato |
|---|---|
| Plugin ID / MFE | `controllership-finance` / `plugins/controllership-finance` |
| MFE basePath | `/apps/controllership-finance` |
| BFF / baseUrl | `controllership-finance-api` / `/apps/controllership-finance-api` |
| Únicas permissions | `controllership-finance.access` e `controllership-finance.manage` |
| Frontend | React MFE, reuso `@delpi/plugin-ui`, UX PT-BR, mobile/desktop, teclado/foco, claro/escuro |
| Arquitetura | Clean Architecture/Ports & Adapters; browser → BFF própria; integração entre contexts por contrato |
| Core API | **Único owner de identidade, usuários, RBAC e effective permissions**; Portal não cria/concede/revoga permissões |
| Outros owners | `api-delpi` = SQL/TOTVS/Protheus; `strategic-indicators-api` = indicadores/metas; P5/P6 = estado operacional deste produto |

JWT identifica, **não** autoriza sozinho. Backend exige permission efetiva do Core **AND** resource scope/ownership **AND** business rule, sem bypass por `manage`. Filial é dimensão do dado, não permission code. MFE não acessa `api-delpi` diretamente.

**Navegação comum:** Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda. A **Página do usuário** é deep route `/apps/controllership-finance/users/{userId}`, não item de topbar. Ajuda acompanha a mesma PR da feature; só descreve rotas implementadas e autorizadas.

## Decisões de negócio vigentes — sem rediscutir

- **P3:** `STOCK_CLOSED` terminal V1, tolerância de paridade **R$ 0,00**, T03 owner ERP a inventariar no IMP-10.
- **P5 portal-first:** Finalizar congela PackageVersion imutável; Enviar submete internamente à Minha DELPI, sem anexos por e-mail. Notificação via Core não é outcome de negócio.
- **C2/P5-A..J:** todos pacotes aplicáveis submetidos, aceite **humano real** por pacote na versão vigente, um aceite de cada área obrigatória existente e nenhuma clarification aberta; não pode haver rejeição terminal. Nova versão exige novos aceites, reatribuição preserva autoria.
- **D-FINAL-02 (19/10/2026):** sem pessoas para revisar não existe aceite; o fechamento **aguarda naturalmente**. **Não** travar a submissão/publicação por quantidade de revisores nem concluir automaticamente quando o conjunto de áreas estiver vazio.
- **DEC-01/02:** rejeição de área não encerra competência; somente coordenador formal com ACCESS/vínculo/scope confirma terminalmente com motivo; ausência de confirmação mantém pendência.
- **DEC-03:** sem reversão ou correção de aceite P5 por UI **ou endpoint** na V1.
- **DEC-04:** publicação P6 somente com `manage` efetivo + escopo administrativo, motivo, auditoria e vigência prospectiva; snapshots preservados.
- **D-FINAL-01:** **inventário Core/T05**, não decisão para criar RBAC no Portal. Grupos/funções elegíveis são obtidos por integração governada; backend valida recurso/área/regra; nenhum novo permission code.

Authority temática: [37 — revisão P5](./37-p5-submissao-e-revisao-no-portal.md), [13 — P6](./13-p6-administracao-e-configuracao.md), [23 — RQ/AC](./23-ledger-rq-ac-testes.md). Arquivos de delivery externo (36) e rebaselines antigos (38) são **históricos**, não bloqueios ativos.

## Ordem de implementação — só com autorização no novo chat

```text
IMP-01/A01 Página do usuário  →  Início  →  Visão geral
→ Minhas tarefas  →  Sala de interação  →  Administração  →  Ajuda
→ P1 Cockpit → P2 Checklist → P3 Estoque → P4 Pendências
→ P5 Pacote/Revisão → P6 interface completa → regressão/release
```

A sequência pode ter micro-slice de **contrato owner** como predecessor (ex.: P6 antes de P5), mas não criar scaffolds genéricos nem alterar ordem por conveniência. A primeira interação de implementação começa pelo **IMP-01: revalidar HEAD e `git status` no checkout do Cursor, patterns reais de APIs/MFEs, contratos Core S2S, exports do `plugin-ui`, RQ-USER-01..09 e matriz de testes; implementar o menor diff somente após READY_TO_EXECUTE**. Não passar automaticamente a IMP-02 sem report/review.

## Navegação da documentação (fonte vigente vs histórico)

### Produto, AS-IS e arquitetura

- [Authorities/evidências](./00-governanca-e-authorities.md) · - [Produto/naming](./01-visao-produto-naming-e-escopo.md) · - [PROC-0072 AS-IS](./02-proc-0072-as-is-e-baseline.md) · - [Proveniência](./03-evidencias-proveniencia-e-rastreabilidade.md) · - [Regras TARGET](./04-regras-de-negocio-consolidadas.md) · - [Gaps](./05-diagnostico-gaps-e-oportunidades.md) · - [Boundaries TO-BE](./06-arquitetura-funcional-to-be.md) · - [Experiência](./07-ux-jornadas-e-estados-de-experiencia.md)

### Central de Fechamento P1–P6

- [P1](./08-p1-cockpit-da-competencia.md) · - [P2](./09-p2-checklist-e-documentos.md) · - [P3](./10-p3-estoque-cutoff-e-conciliacao.md) · - [P4](./11-p4-classificacoes-e-pendencias.md) · - [P5 pacote](./12-p5-pacote-finalizacao-e-envio.md) · - [P6](./13-p6-administracao-e-configuracao.md) · - [P3 paridade](./15.1-p3-criterios-paridade-monetaria.md) · - [P5 revisão](./37-p5-submissao-e-revisao-no-portal.md)

### Segurança, requisitos e integração

- [AuthZ](./14-seguranca-rbac-auditoria-e-ia.md) · - [AC transversal](./15-requisitos-criterios-de-aceite-e-testes.md) · - [Catálogos/aviso](./16-configuracoes-catalogos-e-notificacoes.md) · - [E/T e decisões](./17-backlog-de-confirmacoes-e-inventarios.md) · - [TÉO](./19-rastreabilidade-teo.md) · - [Transforma+](./20-transforma-plus-coverage.md) · - [Owners](./21-boundaries-produtos-e-owners.md) · - [RQ/AC/tests](./23-ledger-rq-ac-testes.md)

### Páginas comuns e kit

- [Navegação](./24-inicio-e-navegacao-principal.md) · - [Visão geral](./25-visao-geral-indicadores-financeiros.md) · - [Sala](./26-sala-de-interacao.md) · - [Tarefas](./27-minhas-tarefas.md) · - [Admin](./28-administracao.md) · - [Ajuda](./29-ajuda.md) · - [Reuse map](./30-plugin-ui-reuse-map.md) · - [**A01: Página do usuário**](./31-pagina-do-usuario.md) · - [Início](./32-inicio-home.md)

### Execução e provas

- [**Readiness vigente**](./18-readiness-e-handoff-de-implementacao.md) · - [P1–P6 handoff](./22-handoff-implementacao-p1-p6.md) · - [Gate documental](./33-plano-mestre-fechamento-documental.md) · - [A14](./34-revisao-transversal-gate-v2.md) · - [A15](./35-contratos-regras-scripts-test-matrix-gate-v2.md) · - [Roadmap mestre](./39-roadmap-mestre-implementacao-v1.md) · - [Backlog IMP](./40-matriz-dependencias-e-slices-v1.md) · - [Matriz de testes](./41-estrategia-validacao-e-gates-implementacao-v1.md) · - [Brief/Report Cursor](./42-playbook-brief-cursor-execution-report-v1.md) · - [Operação/release](./43-rollout-operacao-e-handoff-v1.md)

### Histórico e evidência arquivada

- [Delivery externo superseded](./36-e04-t04-package-delivery-decision-packet.md) · - [Evidência histórica](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md) · - [A16 atualizado (e histórico)](./44-a16-revalidacao-final-transversal-2026-10-16.md)

## Protocolo

`USER GOAL → GPT BRIEF → CURSOR INVENTORY/EXECUTION → EXECUTION REPORT → GPT REVIEW → VERIFY → DOCS/HELP/EVIDENCE → COMMIT/SHA → NEXT SLICE`. Resultado de review: `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Script apenas planejado = `TEST_NOT_RUN`; merge não é prova de runtime. **Não criar outro “rebaseline” só para repetir o estado acima.**
