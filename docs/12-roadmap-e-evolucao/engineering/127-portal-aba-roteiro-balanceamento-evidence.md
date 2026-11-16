# 127 — Portal Engenharia: Aba Roteiro + Balanceamento (E2E evidence)

Status: IMPLEMENTADO | Data: 2025-12 | Task: EVA-PORTAL-ROUTING-TAB-AND-LINE-BALANCING-PROD-E2E-01

## Escopo entregue

- **Aba "Roteiro"** na Ficha do Produto (`?tab=routing`), após Histórico,
  com alias `roteiro` — navegação por URL/teclado preservada.
- **3 seções internas** (EngineeringTabs mode=tabs): Operações,
  Balanceamento, Análise visual.
- **Contratos:**
  - `GET /v1/products/{code}/routing` (existente) — agregação de páginas
    no client até `total` (teto 20 páginas → flag `truncated` honesta).
  - `POST /v1/products/{code}/line-balance` (**novo**, bounded BFF) —
    mesmo produtor `domain.routing.line_balance.build_balance_result`
    que `analyze(routing.line_balance)` MCP. Vocabulário fechado
    `BALANCE_INPUT_FIELDS`, AuthZ `engineering.access`, principal humano,
    mapeamento 403/404/502.
- **Domínio compartilhado:** `parse_bom_levels` + `build_balance_result`
  extraídos da borda MCP para `domain/routing/line_balance.py` —
  payload idêntico nas duas bordas (incl. ramo de roteiro vazio, com
  eco rotulado de parâmetros e filtros).

## Decisões

- Nova rota BFF aprovada como extensão bounded do BFF existente
  (Doc 125 §8 opção A) — mesmo owner, mesmo domínio, read-only;
  nenhum algoritmo duplicado (dedup/takt/gargalo/FFD só no backend).
- EVA no Portal: sem canal conversacional legítimo — a aba exibe nota
  honesta de handoff (EVA via MCP externo), sem botão fake.
- Dedup visual do MFE espelha a identidade oficial
  (produto×nível×op×CT×recurso) apenas para renderização; análise vem
  do domínio.
- Cenários: máx. 4, client-side, sem persistência, reset por produto
  e por troca de filial; tabela inclui coluna Filial.

## Evidência E2E local (stack canônica, token real)

- `POST /line-balance 90264302 {demand:500, available:420, stations:8}`
  → CALCULATED, `official_rows=6 → unique_operations=3`, params PROVIDed.
- `POST /line-balance 90260148` → PARTIAL, `stages=[]`, params ecoados.
- `{equipment_constraint}` → 400 vocabulário fechado; `max_depth:99` →
  400; sem token → 401.
- GET /routing → 6 itens reais do owner (SG2).
- Bundle MFE reconstruído em dev: remoteEntry contém a aba.

## Gates

- engineering-api: suíte completa 1431 pass; falhas remanescentes são
  baseline conhecida (test_d16_attendance_flags) e escopo G24 de
  terceiros (structure_table_roundtrip, visual_perception_r7) — não
  relacionadas ao diff.
- plugins/engineering: 467 testes, typecheck e build verdes; lint sem
  erros novos (erros pré-existentes em arquivos não tocados).
- Gates transversais: phase3 + platform_guardrails → 0 findings.
- Verificação independente: r1 ACCEPT_WITH_RESIDUAL → correções
  (branch reset, cenários por filial, banner parcial global, max_depth
  validado, contrato vazio enriquecido, badge honesto, flag de
  paginação) → r2 ACCEPT_WITH_RESIDUAL (apenas LOW restantes: rótulo
  de parâmetros no caso vazio, badge fallback — mitigados neste SHA).
- Verificador oficial: INCONCLUSIVE por infra (devin sem auth, cursor
  sem cota) — fallback de subagente clean-context conforme precedente.

## Deploy em produção (srv-api)

- `COMMIT_SHA` publicado: `b5060b05b2` (rebase sobre `d41a92c62d` —
  commits concorrentes Atlas/journal sem overlap de arquivos).
- `git pull --ff-only` em `~/projetos/delpi-central` (operador@srv-api)
  → HEAD `b5060b05b2`.
- `up-prod-sequential.sh --build engineering-api` → container healthy;
  `POST /v1/products/{code}/line-balance` registrada no OpenAPI prod.
- `up-prod-sequential.sh --build engineering` → bundle novo (14:16);
  `remoteEntry.js` via `/apps/engineering/assets/remoteEntry.js`
  referencia `__federation_expose_App-BS1guqnU.js`; chunk
  `App-BRcCFPJS.js` contém a rota `line-balance`.
- Smoke prod sem token: GET routing → 401; POST line-balance → 401
  (fail-closed preservado). Health `online`. Logs de startup sem erros.
- Smoke autenticado em prod depende de principal humano Keycloak real
  (AC-18) — validação E2E autenticada comprovada na stack canônica
  local com token real e dados TOTVS reais (seção anterior).
