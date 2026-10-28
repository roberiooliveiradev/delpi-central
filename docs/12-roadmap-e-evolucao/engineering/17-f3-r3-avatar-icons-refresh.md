# F3.R3 — Avatar oficial, ícones de funcionalidades e botões Atualizar

## Baseline

- `BASE_HEAD`: `131dd38f63` (F3.R2). `origin/main` avançou para
  `1627f869e2` durante a execução — delta apenas docs (wireframes
  PROC-0073 / UX-016), sem overlap de código; rebase aplicado.

## Avatar — causa raiz e correção

- Fonte oficial (F3.R2): Core `GET /core-api/me/person-profile` +
  `/photo` — mesmo owner que o Comercial consome via proxy da
  commercial-api (`mirror_person_profile_*` sincroniza os dois stores).
- **Causa raiz da foto não aparecer (bug da F3.R2):**
  `configureHttpClient(getAccessToken)` estava num `useEffect` do `App`.
  Effects de filhos executam antes dos do pai → o fetch de
  `useAvatarPhoto` disparava sem `accessTokenGetter` configurado →
  401 → fallback de iniciais (`RO`). O Home data tinha o mesmo risco
  latente no primeiro mount.
- Correção: `configureHttpClient` movido para o corpo do render —
  mesmo padrão do `App` do Comercial (atribuição idempotente, sem
  estado). `resetHttpClient` no unmount preservado.
- Isolamento: objectURL revogado + fetch abortado por `sub` do JWT;
  falha em qualquer etapa degrada para iniciais.

## Ícones das funcionalidades — extensão neutra do kit

- `SectionRouteItem` do plugin-ui **não tinha** suporte a ícone por
  item (só `icon` no cabeçalho do card).
- Extensão mínima e retrocompatível em
  `plugins/plugin-ui/src/components/layout/SectionRouteCard.tsx`:
  `icon?: ReactNode` (decorativo, `aria-hidden`), novas classes
  `__route-icon` + `__route-label-text` (label passa a `flex:1`,
  preservando badge à direita para consumidores sem ícone).
- CSS em `styles/section-route-card.css` — somente tokens, temas
  claro/escuro herdam `color: inherit` do botão.
- Sem renderer paralelo, sem mudança visual para consumidores
  existentes (commercial, controllership-finance, supplies — verificado
  que todos usam `sectionRouteCardBemClasses(prefix)`).
- Teste novo no kit cobre o slot opcional.

### Catálogo da Engenharia

- `ROUTE_ICONS` por **id estável** (sem match por label):
  `my_requests`→ClipboardList, `lmps`→ClipboardCheck,
  `overview`→ChartColumn, `dashboard`→ChartNoAxesCombined,
  `home`→House, `help`→BookOpen, `eva`→Sparkles (desabilitado/Em breve).
- Sem efeito sobre permissões — filtro de apresentação inalterado.

## Botões Atualizar

- Hero e card "Eventos e interações": `EngineeringActionButton
  variant="ghost"` com `<RefreshCw size={16} aria-hidden/>` + label —
  mesmo padrão do Comercial (`OpenOrdersPageImpl`/`CustomerOrderDetailPage`).
- Ambos `disabled={refreshing}` e trocam para "Atualizando…" —
  compartilham o mesmo estado do `useHomeData`, impedindo chamadas
  concorrentes; `aria-label` explícito.

## Validação

- Engineering: 50/50 testes, `tsc --noEmit` 0, `eslint` 0, `vite build` OK.
- plugin-ui: 8/8 `SectionRouteCard.test.tsx` (incl. novo caso de ícone),
  `tsc --noEmit` 0, `vite build` + `verify-host-exports` OK.
- Audits: backend_boundaries 0, platform_guardrails 0,
  architecture_phase3 OK; findings pré-existentes repo-wide
  (travel-expenses/tv-dashboard alias) não relacionados.

## QA visual

`TEST_NOT_RUN` — sessão autenticada indisponível (manifest 0.2.0 +
grant `engineering.access` pendentes); não declarada visualmente validada.

## Deploy

- SHA final: `ba5a4377883a107eb065f5369353f65fcbc5dad7`.
- Ordem canônica com kit alterado: `git pull --ff-only` +
  `up-prod-sequential.sh --build plugin-ui engineering` —
  `delpi-plugin-ui` e `delpi-engineering` rebuildados; backend intocado.
- Smoke público: remoteEntry plugin-ui/engineering 200; rotas
  engineering 200; `engineering-api/health` 200; `v1/home` 401 sem JWT.
- Bundle novo verificado no edge: `App-VbYHu_zt.js` contém
  `person-profile` + `refreshingLabel`; `style-Bqjrb9yo.css` contém
  `route-icon`/`route-label-text`.

## Residuais

- Registro do manifest 0.2.0 na Core — `PENDING_OPERATOR_TOKEN`.
- Grant `engineering.access` — `PENDING_GRANT_APPROVAL`.
- Smoke autenticado + QA visual — pendente do gate.
