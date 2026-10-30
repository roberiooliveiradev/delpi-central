# ENGINEERING.NC.UX.R1 — Native UX Refinement & Visual Evidence

**Missão:** `ENGINEERING.NC.UX.R1` — refinamento nativo da experiência de Não
Conformidades no Portal Engenharia (hero com indicadores, coluna de produtos,
detalhe reorganizado, timeline oficial, avatares, cadastro/edição consistente,
help nos textos dos labels) sem alterar regras, persistência, permissões ou
contratos.

**Status:** `PASS` — implementado, testado no SHA final e homologado em
navegador real (desktop, mobile, tablet, light/dark).

**Base:** `5c1b939600` (= `origin/main` na reancoragem, pós-T7).
**SHA testado:** ver `FINAL_HEAD` no relatório de execução — testes de
navegador e CI rodados sobre o worktree exato que foi commitado.

---

## 1. Autoridades lidas

- `AGENTS.md` (git workflow: commit direto em `main`, ff-only, staging por escopo).
- `.cursor/rules/development-standards-index.mdc`, `centralized-rules-first.mdc`,
  `clean-code-architecture-guardrails.mdc`, `english-code-identifiers.mdc`.
- `.cursor/rules/feature-help-sync.mdc` — sync obrigatório da Ajuda in-app.
- Docs 46–51 (master plan NC, T1–T6, T6.R1, handoff produtivo T7).
- `platform-frontend-mfe-experience` / `platform-quality-testing` (responsabilidades materiais).
- Inventário `@delpi/plugin-ui`: `Timeline`, `InitialsAvatar`, `UnifiedAvatar`,
  `FieldLabel`, `HelpTooltip`, `PageHero.highlights`, `DetailField.hint`,
  `SectionCard.hint`, `DataTableColumn.headerHint`, `DetailCard.titleHint`.
- Referências visuais nativas: `features/home/HomePage.tsx` (hero com
  `highlights`), `features/overview`, `plugins/commercial` (`createTimeline` →
  `CommercialActivityTimeline`, `createInitialsAvatar`, mapper
  `portfolioAuditTimeline.ts`).

## 2. Decisões de design (Abstraction Gate)

| Requisito | Componente canônico reutilizado | Nada novo criado? |
|---|---|---|
| Indicadores no hero | `PageHero.highlights` (mesmo slot da Home) | sim |
| Timeline de histórico | `createTimeline({ prefix: "engineering" })` | sim |
| Avatares de usuários | `createInitialsAvatar("engineering")` | sim |
| Help no texto do label | `FieldLabel`, `HelpTooltip wrap`, `DetailField.hint`, `DataTableColumn.headerHint`, `SectionCard.hint` | sim |
| KPI cards soltos | removidos — `EngineeringKpiCard` substituído pelo slot oficial do hero | sim |

Novos exports no wrapper `ui/engineeringUi.ts` (mesma fonte `@delpi/plugin-ui`):

```ts
export const EngineeringTimeline = createTimeline({ prefix: ENG_UI_PREFIX });
export const EngineeringInitialsAvatar = createInitialsAvatar(ENG_UI_PREFIX);
export const EngineeringFieldLabel = FieldLabel;
```

O shim tipado `shims/plugin-ui.d.ts` foi atualizado para refletir a API real
da `Timeline` (`tone`, `meta`, `loading`, `layout`, `aria-label`,
`parentId`, `branchKey`) — o kit já suportava tudo; só a declaração estava defasada.

## 3. Arquivos inspecionados vs. alterados

**Inspecionados (sem alteração):** `api/nonconformityApi.ts`, `types.ts`,
`nonconformityRoutes.ts`, `features/lmps/components/DataTable*`,
`plugins/plugin-ui` (Timeline, PageHero, DetailFieldGrid, SectionCard,
InitialsAvatar, HelpTooltip, DataTable), `features/home`, `features/overview`,
`plugins/commercial` (padrões audit timeline/avatar), `personProfileApi.ts`
(contrato de foto é `/me`-only).

**Alterados:**

| Arquivo | Mudança |
|---|---|
| `src/features/nonconformities/ncPresentation.ts` | **novo** — modelo de apresentação puro: formatação tipada de histórico, highlights do hero, resumo de produtos, label de ator |
| `src/features/nonconformities/ncPresentation.test.ts` | **novo** — 16 testes |
| `src/features/nonconformities/ncCopy.ts` | `NC_HELP` ampliado: filtros, colunas, todos os campos, indicadores, seções, ator |
| `src/features/nonconformities/pages/NonconformitiesListPage.tsx` | KPIs dentro do hero (`highlights`), coluna "Produtos associados", `headerHint`s, `FieldLabel` nos filtros |
| `src/features/nonconformities/pages/NonconformityDetailPage.tsx` | ordem de cards obrigatória, hints nos fields, `NcUserIdentity` com avatar, `EngineeringTimeline` no histórico |
| `src/features/nonconformities/pages/NonconformityFormPage.tsx` | `FieldLabel`+hint em todos os labels, ordem de seções = detalhe |
| `src/index.css` | removido `.engineering-nc-history*` ad hoc; adicionados `.engineering-nc-user`, `-products-cell/-item/-more`, `-change-list` |
| `src/ui/engineeringUi.ts` | exports `EngineeringTimeline`, `EngineeringInitialsAvatar`, `EngineeringFieldLabel` |
| `src/shims/plugin-ui.d.ts` | tipos reais da Timeline |
| `src/features/help/HelpPage.tsx` | Manual: produtos na listagem, indicadores no hero, ajuda nos rótulos |
| `e2e/specs/nonconformities.spec.ts` | asserções UX.R1 (hero KPIs, coluna produtos, ordem de cards, timeline, sem `[object Object]`, avatares, help hover/focus, dark, overflow) |
| `e2e/playwright.config.ts` | project `tablet` (Galaxy Tab S4 — Chromium) |

## 4. R1-A — Indicadores dentro do hero

Os dois `EngineeringKpiCard` soltos abaixo do hero foram removidos e os
mesmos valores passaram ao slot `highlights` do `EngineeringPageHero` —
o mesmo padrão da Home (`buildHeroHighlights`).

- `Dias sem NC` → `indicators.current_days_without_nc` + `Última NC em DD/MM/AAAA`
  (ou `Sem ocorrências registradas`).
- `Recorde de dias sem NC` → `indicators.record_days_without_nc` +
  `N NC(s) registrada(s)` (`nc_count` do contrato).
- `loading: true` mantém placeholder `…` honesto até o fetch — **nenhum
  valor é recalculado no frontend** (`buildNcHeroHighlights` só formata).
- Hero contém: identidade (eyebrow/título/descrição), ações (Nova/Exportar/
  Importar), indicadores e filtros no mesmo bloco visual.

## 5. R1-B — Coluna "Produtos associados"

O contrato de listagem (`NcListResult.items[].products`) **já retorna** os
produtos — **nenhuma extensão contratual foi necessária** e nenhuma chamada
adicional por linha é feita.

- `NcProductsCell`: até 2 produtos por célula (`código — descrição`,
  `text-overflow: ellipsis`, `title`/`aria-label` com a lista completa) +
  contador `+N` para excedentes. Lista vazia → `—`.
- Lista completa acessível: a linha inteira navega para o detalhe (card
  "Produtos associados" com todos os itens), além do `title`/aria-label.
- `headerHint` no cabeçalho: ajuda no texto "Produtos associados".

## 6. R1-C — Ordem do detalhe

Ordem implementada (assertiva no E2E por índice de `<h2>`):

1. **Identificação** — `EngineeringDetailCard` + `EngineeringDetailFieldGrid`
   com todos os campos originais preservados e `hint` em cada label.
2. **Produtos associados** — `SectionCard` com código + descrição honestos
   (`—` quando sem descrição; "Nenhum produto associado." quando vazio).
   O enriquecimento TOTVS permanece **somente** no card de Contexto — sem
   duplicação.
3. **Problema e tratativa** — descrição, ações corretivas, parecer técnico.
4. **Problemas identificados** — tags com `EngineeringStatusBadge`.
5. **Contexto da proposta e produtos** — facts TOTVS via Engineering API,
   estados de indisponibilidade preservados.
6. **Histórico** — Timeline oficial (§7).

## 7. R1-D — Histórico com Timeline oficial

`EngineeringTimeline` (do kit) substituiu a lista ad hoc
(`.engineering-nc-history*` removida do CSS). Mapeamento por evento:

- `title`: "Registro criado" / "Atualização"; `tone`: `success`/`info`.
- `occurredAt`: ISO do contrato; `timeLabel`: `formatNcDateTime`.
- `meta`: avatar de iniciais + nome do ator (`actor_name` → `actor_email` →
  "Usuário do Portal").
- `detail`: lista de linhas `Label: antes → depois` geradas por
  `ncHistoryChangeLines`.
- `loading`/`emptyMessage` oficiais do componente; ordem do contrato
  preservada (mais recentes primeiro).

### Eliminação de `[object Object]` — causa raiz

O renderer anterior fazia `value.join(", ")` em arrays e `JSON.stringify`
em objetos — arrays de produtos viravam `[object Object]`. A correção foi
**generalizada na camada de apresentação** (`formatNcHistoryValue`), por
tipo e por campo:

- `products` (array/objeto `product_code`/`product_description`) →
  `CÓDIGO — descrição`, separados por `; `.
- `problem_tags` e arrays genéricos → itens formatados recursivamente.
- campos de data (`occurrence_date`, `launch_date`, `last_revision_date`) →
  `DD/MM/AAAA`; timestamps (`registered_at`, `created_at`, `updated_at`) →
  `DD/MM/AAAA, HH:MM`.
- objetos genéricos → pares `chave: valor` legíveis (profundidade ≤ 2) —
  nunca JSON bruto, nunca `[object Object]`.
- `null`/`undefined`/`""`/array vazio → `—`.

Persistência append-only **não** foi tocada — a correção é só de
apresentação, como exigido.

## 8. R1-E — Avatares e identidade

- `NcUserIdentity`: `EngineeringInitialsAvatar` (iniciais + cor
  determinística) + nome textual — usado em `Executado por`, `Liberado por`,
  `Criado por`, `Atualizado por` e no `meta` de cada evento da timeline.
- **Fallback honesto:** não existe endpoint de foto por-usuário acessível ao
  MFE (o contrato Core `/integrations/person-profiles/{id}` é S2S-only;
  `/me/person-profile` cobre apenas o usuário logado). Iniciais são o
  fallback correto; **nenhum** URL arbitrário nem claim de JWT é usado.
- `executed_by`/`released_by` permanecem **texto livre** — o avatar renderiza
  iniciais do texto informado, sem presumir identidade Keycloak. `created_by`
  /`updated_by` e `actor_*` do histórico já são identidade governada do
  contrato e exibem o mesmo tratamento visual.
- Evolução futura (documentada, **não implementada**): seletor governado
  vinculando Executado/Liberado por a usuário oficial + resolução S2S de
  foto por-usuário exposta via Engineering API — ambos exigem decisão de
  contrato/ownership própria.

## 9. R1-F — Cadastro e edição

- Mesma ordem de seções do detalhe: Identificação → Produtos associados →
  Problema e tratativa → Problemas identificados (o card de produtos subiu
  de posição para espelhar o detalhe).
- Todos os labels usam `EngineeringFieldLabel` com `hint` — texto clicável/
  focável, sem ícone `?`.
- Campos, validações, `expected_updated_at` (ETag), ações e proteção contra
  perda de alterações **inalterados**; `executed_by`/`released_by` continuam
  texto livre no payload (sem mudança de semântica/contrato).

## 10. R1-G — Help nos textos dos labels

Cobertura via mecanismos oficiais do kit — todos com trigger **no texto**,
`tabIndex={0}`, `aria-describedby`, abertura por hover **e** foco (touch:
toque no texto focável abre o tooltip), fechamento por `Escape`/blur:

- Filtros da listagem (`FieldLabel`), campos de data (`DateField.hint`).
- Todos os campos do formulário — `FieldLabel` em cada label.
- Todos os campos do detalhe — `DetailField.hint` no `DetailFieldGrid`.
- Cabeçalhos de tabela pertinentes — `DataTableColumn.headerHint`
  (Produtos associados, Status, Problema, Tags, Registro).
- Títulos de seção — `SectionCard.hint` (Produtos, Problemas identificados,
  Contexto, Histórico, Importação) e hint da tabela.
- Indicadores — explicados no Manual (conceito) e nos hints de contexto do
  hero; `NC_HELP.daysWithoutNc`/`recordDaysWithoutNc` disponíveis no dicionário.
- **Zero** ícones `?` adicionados pela feature; `NC_HELP` estendido de 7
  para 30 entradas, sempre explicando o dado (não repetindo o label).
- Manual in-app (`HelpPage`) sincronizado — `feature-help-sync` cumprido.

## 11. Testes e evidência

| Camada | Comando / teste | Resultado |
|---|---|---|
| Unit | `npx vitest run` | **157/157** (inclui 16 novos em `ncPresentation.test.ts`: formatação tipada, sem `[object Object]`, highlights, resumo de produtos, ator) |
| Lint | `npm run lint` | 0 erros (14 warnings pré-existentes, inalterados) |
| Typecheck | `tsc -p tsconfig.app.json --noEmit` | limpo |
| Build | `npm run build` | `dist` gerado (mesmo budget de chunks do baseline) |
| Browser | `npx playwright test` — desktop | **6/6** |
| Browser | mobile (Pixel 7) | **6/6** |
| Browser | tablet (Galaxy Tab S4) | **6/6** |

E2E cobre: hero com KPIs oficiais; coluna Produtos associados no thead;
help por hover **e** por foco de teclado com `role="tooltip"` visível;
ordem exata dos 6 cards do detalhe; timeline semântica
(`ol[aria-label="Histórico da não conformidade"]`) com itens; **zero**
`[object Object]` na página; avatares `.engineering-nc-user .delpi-ui-avatar`;
sem overflow horizontal global; light **e** dark; criação/edição sem
regressão; bridge legado; zero pageerrors; **zero** chamadas MFE→api-delpi
(boundary S2S preservado).

Evidência visual em `plugins/engineering/artifacts/`: `nc-list.png`,
`nc-detail.png`, `nc-form.png`, `nc-ux-light.png`, `nc-ux-dark.png`,
`nc-detail-dark.png`, `nc-legacy-bridge.png`.

Nota de ambiente: browsers Playwright exigiram `libnspr4`/`libnss3`/
`libasound2` ausentes no WSL — resolvido **sem sudo** via `apt-get download`
+ `dpkg -x` em `~/.local/lib/pw-deps` + `LD_LIBRARY_PATH`. Tablet iPad
trocado por Galaxy Tab S4 (Chromium) — WebKit não instalado.

## 12. Limites preservados

- **Zero mudança** em: contratos E-NC-*, regras NC, schema Postgres,
  migrations, grants, writer único (Engineering API), freeze legado
  (`LMP_NC_WRITE_MODE=frozen`), permissões (`engineering.access`/
  `engineering.manage`), AuthZ, boundary S2S, EVA READ/PREPARE/ACT, Dashboard
  legado, bridge `/lmps/nonconformities`.
- `api-delpi` e `engineering-api` **não foram tocados** — mudança 100% MFE
  (+ tipos do shim). Deploy: apenas o bundle `delpi-engineering`.
- EVA capability ledger: **sem alteração de capacidades** — superfície de
  tools/contratos inalterada (mudança puramente de apresentação no MFE).

## 13. Residuais e próximos passos

- Foto real por-usuário nos avatares NC exige contrato S2S→MFE (decisão de
  ownership — fora de escopo UX).
- `executed_by`/`released_by` como associação formal a usuário: evolução
  funcional futura com contrato próprio.
- Telemetria 30–60d de writes legados → decisão T8 (independente desta R1).
