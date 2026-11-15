# Report U10 — desempenho BFF e perfis

Data: 2026-11-15. Âncora: `origin/main` ≥ `2421716c` (HEAD de trabalho incluía `aefd74682d`+).

## R1 — `/summary` (G9)

**Causa confirmada (`CONFIRMADO_NO_CODIGO`):**
1. N+1: `status_of(stable_key)` por linha em `_status` / `summary` / `_filtered` / `_previous_kpis`.
2. Nova conexão Postgres em cada `_all()` via `plugins_db_connect()`.
3. `rows(kind)` / `runs_of` re-lidos várias vezes na mesma requisição.

**Correção:** `statuses_of` em lote; memo request-local de rows/runs; pending/resolved em uma passada; sem alterar pool da plataforma.

**Consultas por requisição (teste `test_entry_audit_u10_query_budget.py`):** orçamento fixo — não cresce com N linhas (antes: O(N) `status_of` + conexões).

| Métrica HML análise 01–15/11 (docs=315, occ=159) | Antes (U9) | Depois (U10) | Meta |
|---|---|---|---|
| `GET …/summary` | ≈ 8,3 s | **242–285 ms** | &lt; 500 ms |
| KPIs visíveis (summary no browser) | ≈ 8,4 s | **≈ 271–285 ms** | &lt; 1,5 s |

Evidência: `/tmp/ui-review-u10/r1-timings.json` (`summaryMs=242`, `kpiMs=271`). CLARA usa o mesmo serviço de summary — mesma leitura.

SHA BFF: `aefd74682d`. Tag: `rollback-ui-review-u10-controllership-finance-api`.

## R2 — perfis após LGPD

Playwright aceita ConsentModal (rolar política → Prosseguir → Aceitar e continuar) no 1º login.

| Perfil | Resultado |
|---|---|
| `cf-access` | PASS — entra no portal; sem Administração; **sem** botão LNF (negativo) |
| `cf-manage` | PASS — Administração do checklist acessível |
| `cf-lnf` | PASS — botão «Lançamento de notas fiscais» visível |
| `cf-dre` | PASS — experiência DRE (Documentos/Fechamento); admin negado/redirecionado |

Artefatos: `/tmp/ui-review-u10/r2-cf_*.png`. Spec: `e2e/specs/u10-profiles-axe.spec.ts` (5/5 desktop PASS).

## R3 — axe color-contrast / button-name

Inventário completo em `/tmp/ui-review-u10/r3-axe-inventory.json`. **Nenhuma violação MFE-local** (só `cf-*` sem `delpi-ui`) — nada a corrigir no plugin nesta etapa.

| Página | Regra | Seletor | Componente dono |
|---|---|---|---|
| home, entry | button-name | `.collapse-btn` | **host** — sidebar Portal |
| home, entry | color-contrast | `.avatar` | **host** — avatar shell Portal |
| home, entry | color-contrast | `.sidebar-footer__privacy-link` | **host** — rodapé sidebar |
| home, entry | color-contrast | `.cf-avatar…delpi-ui-avatar` (TopBar) | **plugin-ui** — `Avatar` / TopBarUser |
| home | color-contrast | `…delpi-ui-section-route-card__route-label-text` | **plugin-ui** — `SectionRouteCard` |
| entry | color-contrast | `.delpi-ui-action-btn > .cf-action-with-icon` | **plugin-ui** — `ActionButton` (+ wrapper MFE) |

### Residuais do kit (U13 X1 — não corrigir aqui)

| Página | Seletor (closest) | Componente dono | FG / BG medidos |
|---|---|---|---|
| análise (hero Exportar / ações) | `.delpi-ui-action-btn` | **plugin-ui** — `ActionButton` | `#ffffff` / `#089bdb` (~3.12:1) |
| análise (Tabela/Cards) | `.delpi-ui-segment-toggle` | **plugin-ui** — `SegmentToggle` | `#ffffff` / `#089bdb` (~3.12:1) |
| home, entry, análise | `.delpi-ui-avatar`, `.cf-topbar-user` | **plugin-ui** — `Avatar` / TopBarUser | `#ffffff` / `#089bdb` |
| home, entry, análise | `.avatar` | **host** — shell Portal | (host) |

Decisão U13: Comercial usa `variant="primary"` na ação principal do hero; alinhamos «Exportar» como `primary` (composição do Portal). Contraste restante permanece residual do kit.

## PROD

BFF `controllership-finance-api` publicada após U10. **Parar:** owner envia prints (Início, entrada, análise 01–15/11 desktop+mobile) e o tempo de abertura da análise.
