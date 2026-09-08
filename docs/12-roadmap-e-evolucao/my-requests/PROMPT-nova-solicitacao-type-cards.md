# Prompt de implementação — Nova solicitação por cards + unidade no tipo

> **Módulo:** Minhas Solicitações (`plugins/my-requests` + `requests-api`)  
> **Superfície:** `/apps/my-requests/new`  
> **Status:** prompt de produto/engenharia — **ainda não implementado**  
> **Docs irmãs:** [WIREFRAMES.md](./WIREFRAMES.md) (WF-03) · [PLAYBOOK.md](./PLAYBOOK.md) · [MANUAL-USUARIO.md](./MANUAL-USUARIO.md) · [plugin README](../../../plugins/my-requests/README.md)

Use este arquivo como **brief único** para um agente ou desenvolvedor implementar a UX de criação. Não improvisar fora deste escopo.

---

## Objetivo

Substituir o `SelectField` de **Tipo** (+ Filial no shell genérico) por um **grid de cards** com ícones. Cada card abre o formulário daquele tipo (`specialized` ou `schema_driven`), com **regras e validações do próprio tipo**. A seleção de **unidade/filial** fica **dentro da camada do tipo**, conforme `branch_scope` — apps com multi-unidade e apps sem unidade coexistem no mesmo `/new`.

---

## Contexto confirmado (não redecidir)

| Fato | Evidência |
|------|-----------|
| Página atual | `plugins/my-requests/src/pages/NewRequestPage.tsx` — Select Tipo + Select Filial + botão Abrir |
| Catálogo dinâmico | `GET /apps/requests-api/v1/request-types` · tabela `my_requests.request_types` |
| Modos de apresentação | `presentation_mode`: `specialized` \| `schema_driven` (+ fallback genérico) |
| Tipos seed | `invoice-issuance` (wizard) · `raw-material-creation` (SchemaFormPage) |
| Escopo de unidade | `branch_scope` ∈ `required` \| `optional` \| `none` (CHECK na migration V002) |
| Deep link | `?type=` / `?type_code=` em `newRequestDeepLink.ts` |
| Kit-first | `plugins/my-requests/src/ui/mrUi.tsx` — **proibido** primitivo CSS de card só no MFE |

---

## Decisões travadas

| # | Decisão |
|---|--------|
| 1 | `/new` lista **apenas** cards de tipo (sem Filial no shell). |
| 2 | Clique no card → entra no form daquele tipo (mesmo ramo de hoje: wizard / schema / create genérico). |
| 3 | Unidade/filial: **só** dentro do form do tipo, se `branch_scope` ≠ `none`. |
| 4 | `branch_scope=required` → campo/passo obrigatório + gate API; `optional` → campo opcional; `none` → sem UI de unidade e sem exigir `branch_code`. |
| 5 | Ícones: mapa MFE `code → LucideIcon` **ou** metadado opcional no tipo (`ui`/`icon`); label = `name` (sem `(code)` na UI). |
| 5b | **Kit canônico do card:** `createDashboardNavigationCard` + `navigationCardBemClasses` via `mrUi` (`MyRequestsNavigationCard`). **Não** usar `SectionRouteCard` (lista de rotas internas) nem card BEM solto no MFE. Grid: CSS utilitário do kit / layout já usado em hubs (`travel-expenses` / `commercial`) — sem inventar BEM `type-card`. |
| 6 | Validação canônica permanece na **requests-api** (validators specialized + schema); MFE não inventa regra de negócio. |
| 7 | Novo tipo = seed/registry + feature se `specialized`; shell abre form por **`presentation_mode`** (`specialized` \| `schema_driven` \| genérico) — **não** `if (code === …)` no grid. |
| 8 | Sync Ajuda (`helpTooltips`) + Manual + WF-03 no **mesmo** entregável (`feature-help-sync`). |

---

## Fluxo alvo

```text
/apps/my-requests/new
  → grid de cards (listRequestTypes + permissão do tipo)
  → clique no card
       → specialized     → InvoiceIssuanceWizard (unidade conforme branch_scope)
       → schema_driven   → SchemaFormPage (unidade conforme branch_scope / schema)
       → demais          → createRequest (só envia branch_code se o tipo exigir)
```

Deep link `?type=invoice-issuance`: pré-seleciona e **abre** o form do tipo (não só destaca o card), mantendo compatibilidade.

---

## Fazer (receita)

1. **UI `/new`:** grid de `MyRequestsNavigationCard` (factory `createDashboardNavigationCard` em `mrUi.tsx`) — um card por tipo (`title` = `name`, `icon` Lucide, `onClick` abre form).
2. Remover do shell: `SelectField` Tipo e `SelectField` Filial e o botão “Abrir formulário…” como passo intermediário obrigatório.
3. **Mover filial** para dentro de:
   - `InvoiceIssuanceWizard` (já tem noção de filial — alinhar a `branch_scope` do tipo; hoje `lockedBranch` vem do shell);
   - `SchemaFormPage` / schema do tipo quando `required`\|`optional`;
   - create genérico: só pede/envia `branchCode` se `branch_scope` exigir.
4. Respeitar `allowedUnits` / branches do `RequestsPermissionsContext` **dentro** do form, não no grid.
5. Empty/loading/error do catálogo com padrões do kit (`StateBanner` / empty / loading).
6. Testes: deep link **abre** form; tipo `none` não mostra unidade; tipo `required` bloqueia submit sem filial; regressão kit-first; shell sem `if (code === …)`.
7. Atualizar: este prompt (status → implementado), WF-03 (remover bloco “Atual”), MANUAL § Nova, `helpTooltips` `new.*`.

---

## Não fazer

- Enum fixo de tipos só no React (bypass do registry).
- Filial global no shell de `/new` “porque a maioria precisa”.
- Um form monólito com `if (typeCode === …)` para todos os campos.
- Validação só no front.
- Card misturando “tipo” e “unidade” na mesma escolha.
- `SectionRouteCard` / KPI card / primitivo `button`+CSS local como substituto do NavigationCard.
- Chamar api-delpi no MFE.
- Alterar Portal Suprimentos / `docs/.../supplies` — domínio diferente.

---

## Critérios de pronto

- [ ] `/new` mostra cards com ícone + nome; sem select de tipo/filial no shell.
- [ ] Clique em NF abre wizard; clique em MP abre schema form.
- [ ] Tipo com `branch_scope=none` não exibe seletor de unidade.
- [ ] Tipo com `required` exige unidade antes do create (UI + API).
- [ ] Deep link `?type=` continua funcionando (abre o form).
- [ ] Ajuda in-app + Manual + WF-03 atualizados.
- [ ] `npm test` / build do `plugins/my-requests` verdes no escopo.

---

## Prompt colável (agente)

```text
Implemente a UX de Nova solicitação em plugins/my-requests conforme
docs/12-roadmap-e-evolucao/my-requests/PROMPT-nova-solicitacao-type-cards.md.

Substitua o Select de Tipo (+ Filial no shell) por grid de NavigationCard
(createDashboardNavigationCard via mrUi) a partir de listRequestTypes().
Clique no card abre o formulário do tipo por presentation_mode
(specialized | schema_driven | genérico). Unidade/filial só dentro do form,
segundo branch_scope (required | optional | none). Deep link ?type= deve
abrir o form (não só pré-selecionar). Kit-first. Validação na requests-api.
Sync helpTooltips + MANUAL-USUARIO + WIREFRAMES WF-03 no mesmo PR.
Não toque no Portal Suprimentos. Não invente enum de tipos no MFE.
```

---

## Fora deste prompt

- Novos tipos de negócio (além de NF/MP) — só garantir que o grid escale via registry.
- Deprecação E18 lookups legado api-delpi.
- Tags / CreatableMultiSelect (backlog playbook).
- Custo anômalo / outros módulos (chat admin, supplies).
