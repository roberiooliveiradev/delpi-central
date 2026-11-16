# UX V3 — Toolbar inferior-direita no Hero × 3 páginas — Evidência de execução

**TASK_ID:** `CROSS-MFE-LIST-HERO-LOWER-RIGHT-TOOLBAR-HML-PRD-01`
**Base:** `360d300cf3` · **Implementação:** `5c4977f0e0` + `4bccc31a12` (spec) + `fc5de77e88` (fix overflow) + `0004b1256b` (fix regressão busca)
**Status:** EXECUTED em HML · verificador independente rodada 2

## Escopo real

| Página | Resultado |
|---|---|
| `/apps/my-requests/mine` | ✅ V3 completo, E2E + screenshots |
| `/apps/my-requests/work-queue` | ✅ V3 completo, E2E |
| `/apps/helpdesk` | ⚠️ Código migrado (mesmo contrato); E2E HML `TEST_NOT_RUN` — plugin gated p/ `hml-tester` (ver `06-helpdesk-gated.png`) e serviço ausente do inventário `docker-compose.hml.yml` |

## O que mudou

- **Plugin UI `DataTableSection`**: layout `hero` vira 3 faixas — busca full-width → chips (`toolbarLeading`) → linha de controles à direita (extras + Tabela|Cards). Nova prop `pageSizePlacement="table"` renderiza «itens por página» na região `__table-meta` acima da grade. `searchHint` em modo wrap (sem `?` standalone).
- **CSS kit**: `.table-toolbar--hero` ordena as 3 faixas; host do portal com `min-width:0`; **fix**: `HelpTooltip wrap` (`width:max-content`) dentro das linhas de chips/controles encolhe/quebra — sem o fix os 7 chips travavam 1207px e o toggle era clipado pelo `overflow:hidden` do hero.
- **My Requests**: `pageSizePlacement="table"`; hints `?` removidos da paginationKit; busca dominante; chips; controles na última linha.
- **Helpdesk**: mesma composição 3 faixas (busca → chips+filtros ativos → `[Filtros][Ordenar][Colunas][Tabela|Cards]` à direita); «Por página» migrado do footer para `helpdesk-list-table-meta` acima da lista; footer só navegação; CSS espelha o fix de wrap.

## Evidência runtime HML

- Deploy: plugin-ui `sha256:d6d74f5cf791` (healthy) · my-requests `sha256:82954abb06b6` (healthy) · rollback tags `delpi-hml/*:rollback-ux-v3-*`.
- **E2E Chromium real: 20/20** em 4 viewports (1440/768/390/320) — spec `ux-v2-hero-sort.spec.ts` atualizada p/ V3: rect da toolbar dentro do hero (limite inferior **e superior**), ordem row-major dos 4 controles, busca >50% do hero, chips abaixo da busca, page-size fora do hero na `__table-meta`, grade embedded, sem `?` standalone, header-sort backend + URL + aria-sort, page_size real, sem overflow.
- Geometria medida: `controlsRow.right=1391 ≤ hero.right=1406` (pré-fix era 1546 — toggle invisível).
- Screenshots versionados em `evidence/ux-v3-hero-toolbar-hml-01/`:
  `01-mine-desktop` · `02-queue-desktop` · `03-mine-hero-zoom` · `04-mine-dark` · `05-mine-zoom200` · `06-helpdesk-gated`.

## Bug real encontrado e corrigido durante HML

`HelpTooltip--wrap` (`width: max-content`) encapsulando a `ScopeChipBar` forçava min-content de 1207px → toolbar estourava o host → toggle Tabela|Cards renderizado fora do hero (clipado). O E2E anterior só assertava limite inferior do alinhamento; spec agora exige `controlsRow.right ≤ hero.right` e cada controle dentro do rect. Correções: `fc5de77e88`, `0004b1256b` (restaura busca full-width — o primeiro seletor era amplo demais).

## Resíduos honestos

- Helpdesk: paridade visual inferida de código + CSS espelhado; E2E HML bloqueado por RBAC do usuário de teste — **não afirmar homologação visual do Helpdesk**.
- PRD: pendente de gates G9–G12 nesta thread.

## Deploy controlado PRD (G11–G12)

- **RELEASE_SHA:** `5782cd10dd` (FF em `~/projetos/delpi-central` a partir de `75250f2beb`).
- **Ordem:** plugin-ui → my-requests → helpdesk via `up-prod-sequential.sh --build` (frontend-only; zero migrations, zero RBAC, zero API).
- **Rollback:** `infra-plugin-ui:rollback-ux-v3-20261116` (`d796f2c9d2bc`) · `infra-my-requests:rollback-ux-v3-20261116` (`e3c65b160538`) · `infra-helpdesk:rollback-ux-v3-20261116` (`6516a27df817`) — retag + `up -d` restaura o estado anterior.
- **Digests PRD:** plugin-ui `70b89d6ce531` · my-requests `882dcf2025c0` · helpdesk `6e2c3a1a4930`.
- **Health:** 3 containers `Up`; remoteEntry 200/200/200 via gateway; bundle novo confirmado (`style-DGLwMMH5.css` contém `table-meta`); logs sem erros/5xx; gate de autenticação intacto.
- **Smoke autenticado:** `INCONCLUSIVE` — credencial `ti_delpi` (dev) inválida no Keycloak PRD; nenhuma identidade de teste autorizada para produção foi provisionada (correto: não se cria privilégio artificial). Validação visual PRD fica para usuário legítimo.
- **Helpdesk:** migrado no mesmo contrato e publicado; validação E2E visual permanece bloqueada por RBAC (HML `TEST_NOT_RUN`, PRD `INCONCLUSIVE`).
