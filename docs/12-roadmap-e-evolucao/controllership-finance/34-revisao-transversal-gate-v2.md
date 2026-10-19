# 34 — A14: Revisão Transversal de Contratos e Experiência V1

> **Estado em 19/10/2026:** `A14_TRANSVERSAL_REVIEW=PASS_DOCUMENTAL`. É revisão de especificações e boundaries, não teste nem implementação. A sequência histórica de rebaselines foi consolidada neste parecer; histórico anterior permanece no Git. Ver [33 — gate](./33-plano-mestre-fechamento-documental.md) e [44 — evidências](./44-a16-revalidacao-final-transversal-2026-10-16.md).

## 1. Matriz transversal de coerência

| Eixo | Contrato vigente / provas documentais | Resultado |
|---|---|---|
| Naming/rotas | Plugin `controllership-finance`, MFE `plugins/controllership-finance`, `/apps/controllership-finance`; BFF `controllership-finance-api`, `/apps/controllership-finance-api`. Página do usuário é deep route | **PASS documental** — [01](./01-visao-produto-naming-e-escopo.md), [31](./31-pagina-do-usuario.md) |
| Ownership | Core = identidade/RBAC/permissões/usuários/notificações; api-delpi = ERP/TOTVS; strategic-indicators-api = indicadores; BFF = regra operacional do Portal CF | **PASS documental** — [21](./21-boundaries-produtos-e-owners.md) |
| Segurança | Só `controllership-finance.access` e `controllership-finance.manage`; JWT identifica, BFF exige permission efetiva Core + scope/ownership + regra; ACCESS != MANAGE | **PASS modelo** — [14](./14-seguranca-rbac-auditoria-e-ia.md) |
| Context boundaries | MFE consome somente BFF própria; domain isolado de DB/framework/HTTP; entre contexts por contrato, sem import application/domain ou DB do vizinho | **PASS documental** — [06](./06-arquitetura-funcional-to-be.md), [21](./21-boundaries-produtos-e-owners.md) |
| UI families | Reuso `@delpi/plugin-ui` primeiro; topbar comum, Admin com scope, Página do usuário como deep route; CSS isolado e nenhuma duplicação de chrome | **PASS documental** — [30](./30-plugin-ui-reuse-map.md), [24](./24-inicio-e-navegacao-principal.md) |
| UX e estados | PT-BR, claro/escuro mesma árvore, desktop/mobile, teclado/foco/a11y, LOADING/EMPTY/PARTIAL/UNAVAILABLE/ERROR/FORBIDDEN/NOT_FOUND quando aplicável | **PASS especificação** — docs 07, 24–32 |
| Help | Manual kit `createDashboardUserManual` + links de feature só após implementação; Ajuda atualizada **na mesma PR user-facing** | **PASS documental** — [29](./29-ajuda.md), regra `feature-help-sync` |
| Tarefas/colaboração | TaskProjection dos owners, self-only; P5 por área obrigatória para pessoas elegíveis; Sala não cria TaskEntity nem altera estado P1–P5 | **PASS semântico** — [26](./26-sala-de-interacao.md), [27](./27-minhas-tarefas.md) |
| P3 | `STOCK_CLOSED` terminal Portal V1; paridade monetária R$ 0,00; T03 owner ERP como stop local na P3 | **PASS semântico** — [10](./10-p3-estoque-cutoff-e-conciliacao.md), [15.1](./15.1-p3-criterios-paridade-monetaria.md) |
| P5 | portal-first, PackageVersion, aceite humano por área/versão, C2, rejeição confirmada por coordenador; zero revisor mantém pendência sem trava adicional de envio | **PASS semântico** — [37](./37-p5-submissao-e-revisao-no-portal.md), [23](./23-ledger-rq-ac-testes.md) |
| P6 | MANAGE+escopo administrativo, configuração versionada prospectiva, snapshots P2/P5 preservados | **PASS semântico** — [13](./13-p6-administracao-e-configuracao.md) |
| RQ/AC/testes | Ledger 23, matriz 35/41, casos positivos/sibling/negativos e Help por slice | **PASS de planejamento** — testes runtime ainda `TEST_NOT_RUN` |

## 2. Dependência técnica não invalida gate de desenho

A14 verifica o **modelo**, não uma chamada real que só existirá quando MFE/BFF forem implementadas.

**Core T05 P5:** o Core continua owner da identidade e das permissões. O BFF do Portal é consumer da elegibilidade operacional por grupo/função e valida resource scope/área, sem criar RBAC. Seu contrato físico S2S ainda é `TO_INVENTORY`; **stop apenas para ações do IMP-12/P5**.

**P3 T03:** source ERP não comprovada impede implementação de estado `STOCK_CLOSED` no IMP-10, não a A01.

**A01/IMP-01:** o source atual comprova existência de S2S effective access, directory lookup/by-app, person profiles/foto e reuso da página no `plugin-ui`; integração final ao BFF e verificações de segurança ainda deverão ser testadas no próprio slice. A01 **não** importa regras ou dados P5/P3.

Se um source futuro contradizer owner, permission model ou semântica aprovada, classificar `EXECUTION_DRIFT` e bloquear o subgrafo afetado. Search miss não é ausência. HTTP 200 não é outcome.

## 3. Critério de saída e início de execução

```text
A14_TRANSVERSAL_REVIEW   = PASS_DOCUMENTAL
SECURITY_MODEL_FREEZE    = PASS_MODEL
PORTAL_DESIGN_FREEZE     = PASS_DOCUMENTAL
DOCUMENTATION_CLOSURE   = PASS  (ver 33)
IMPLEMENTATION_AUTHORIZED= NO  (até comando explícito no novo chat)
RUNTIME_AUTHZ_SMOKE      = TEST_NOT_RUN
```

No novo chat abrir **IMP-01** conforme [18](./18-readiness-e-handoff-de-implementacao.md) e [42](./42-playbook-brief-cursor-execution-report-v1.md); inventariar Core/API/MFE/kit e validar `READY_TO_EXECUTE` antes de editar. Não criar novas permissions nem corrigir P5 fora do slice.
