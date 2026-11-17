# EVA-PROCESSES-HUB-YAMAZUMI-V3-IMPLEMENTATION-01 — Evidência

**Tracker:** GitHub Issue #250
**Owner da experiência:** Portal Engenharia
**Modo:** AUTHORIZED_IMPLEMENTATION / CONTRACT_FIRST / PLUGIN_UI_NATIVE / DOMAIN_REUSE / VERIFY_FIX_LOOP / HML_THEN_PROD

## Escopo entregue

- **Quarto card Processos** no Início do Portal Engenharia (catálogo canônico
  `engineeringRouteCatalog.ts`, mesma estrutura das demais seções).
- **Página independente** `Engenharia de Processos` — catálogo de ferramentas,
  com Balanceamento de Linha funcional e cinco futuras marcadas
  `Em planejamento` (sem ação falsa).
- **Workspace Balanceamento de Linha** — consulta oficial por código de
  produto (`GET /v1/products/{code}/routing`), seleção explícita de filial e
  estágio, operações deduplicadas por identidade de operação.
- **Catálogo M1–M6** preservado: M1 reutiliza o cálculo de domínio via
  `POST /v1/products/{code}/line-balance`; M2–M6 documentados como
  planejado/limitado — nenhum cálculo inerte oferecido.
- **Yamazumi interativo (M5)** — postos hipotéticos DRAFT_LOCAL com
  atribuição de operações oficiais, reordenação por botões acessíveis,
  gráfico `stacked_bar` + linha de takt (`MultiTypeSeriesChart`,
  `allowedTypes` aditivo no kit), cenários, persistência em
  `sessionStorage` com prefixo `engineering:processes`, F5 restore,
  Limpar estudo confirmado, exportações CSV/Excel/PDF (iframe de impressão
  do kit) com contexto, parâmetros, unidade e proveniência.

## Fronteiras preservadas

- Roteiro oficial **nunca alterado**; ordem oficial preservada.
- Hipóteses rotuladas SIMULATION/DRAFT_LOCAL — nunca como aprovação de
  processo nem roteiro aprovado.
- Tempos ausentes exibidos como `UNKNOWN` — nunca zero nem estimativa.
- Sem chamada direta a `/apps/api-delpi` (verificado por listener de rede
  no E2E).
- CT/recurso apresentados como associação, com caveat explícito de que não
  provam posto físico, simultaneidade ou disponibilidade.

## Extrações para reuso (2 consumidores reais)

- `routing/studyInputs.ts` — `numberOrUndefined`, `validateStudyInputs`,
  `SAVE_STATUS_LABEL` (Ficha do Produto + Processos).
- `routing/BalanceResultsSection.tsx` — apresentação de resultados do
  domínio (Ficha do Produto + Processos).
- `useRoutingStudyDraft` — prefixo de storage parametrizado (mesmo hook,
  namespaces isolados por contexto).
- Plugin UI `ChartTypeSegmentToggle` — prop aditiva `allowedTypes`
  (backward-compatible; Yamazumi usa `stacked_bar` + `bar`).

## Commits

| SHA | Conteúdo |
|---|---|
| `ced1a6d3c5` | feat: área Processos + Balanceamento de Linha + Yamazumi V3 |
| `7c6a445c42` | test: e2e FilterSelect via listbox do kit |
| `7875af497a` | fix: prop `chips=` no EngineeringScopeChipBar (crash ao selecionar estágio) |
| `40edd101cf` | test: alvo heading para títulos de posto (strict mode) |
| `6bdd2742b7` | test: PDF corporativo via popup → iframe oculto |
| `d2fa94fcc9` | test: PDF via iframe `data-delpi-document-print-frame` |
| `1e29afc861` | test: tolerar listbox persistente em viewport estreito |

HEAD de referência em produção: `120cd0dfcf` (contém todos os commits
acima — `git merge-base --is-ancestor` verificado nos três).

## Testes

- **Unit/component:** 3 arquivos Processes/Yamazumi, 36 testes +
  suíte engineering completa 557/557; `tsc --noEmit` limpo; builds
  plugin-ui e engineering OK.
- **E2E HML (SSO real, `mcr.microsoft.com/playwright:v1.49.1-noble`,
  base `https://192.168.1.237:18443`):**
  - `processes-yamazumi.spec.ts`: **20/20** — card, hub, consulta oficial,
    contexto explícito, dedup, catálogo M1–M6, análise rápida M1, Yamazumi
    (postos, atribuição, reordenação), gráfico carga × takt, cenário B,
    F5 restore, Limpar estudo confirmado, exportações CSV/XLSX/PDF,
    dark/light, 5 viewports (desktop/mobile/tablet/390/320).
  - `routing-visual.spec.ts` (regressão Ficha do Produto → Roteiro):
    **30/30**.

## Deploy

- **HML** (`projetos-teste` @ `56188a32d0` → `0d4267948b`):
  `up-hml-sequential.sh --build plugin-ui engineering` — containers
  healthy; bundle `App-B9czDN8f.js` com `processes`.
- **PROD** (`projetos` @ `120cd0dfcf`):
  `up-prod-sequential.sh --build plugin-ui engineering` — remoteEntry 200
  via minhadelpi.com.br, expose `__federation_expose_App-BGiEEIj6.js`,
  App `App-bDlLdIxQ.js` contém `processes`.

## Residuais

- Verify oficial INCONCLUSIVE (bloqueio de infra — `devin auth login`),
  não convertido em PASS.
- Smoke visual autenticado em produção: `PENDING_USER_SMOKE` — requer
  principal humano Keycloak (credenciais de teste só existem em HML).
- `products.spec.ts` (E2E legado) contém marcadores de conflito de merge
  commitados — quebra pré-existente, fora do escopo desta task; a suíte
  completa do diretório não coleta até a correção.
- Rollback: `git revert` dos commits da feature + rebuild
  `plugin-ui`/`engineering` (checkout HML/PROD por `git pull --ff-only`).
