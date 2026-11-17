# EVA / Portal Engenharia — Routing Study Workspace V2: evidência

**TASK_ID:** `EVA-PORTAL-ROUTING-STUDY-WORKSPACE-V2-E2E-01`
**Estado:** `HML_VALIDATED + PROD_DEPLOYED — verificador oficial INCONCLUSIVE (bloqueio de auth do motor); smoke autenticado de produção PENDING_USER_SMOKE`

## 1. Reancoragem

| Item | Valor |
|---|---|
| BASE_HEAD | `b01fc12ca6` (main concorrente na reancoragem) |
| FINAL_HEAD | `1ab99493f9` |
| ORIGIN_MAIN | `1ab99493f9` (⊃ `9e3445a53a`, `6e9edf8ca3`) |
| HML checkout | `~/projetos-teste/delpi-central` @ `9e3445a53a` |
| PROD checkout | `~/projetos/delpi-central` @ `36e1e3631a` (⊃ V2; bundle idêntico) |
| Autoridades | `ux/routing/routing-study-workspace-v2-visual-contract.md`, `routing-study-session-state-contract.md`, `routing-study-v2-acceptance.md`, Doc 61, Doc 126, AGENTS.md |

## 2. Implementação (menor diff, zero mudança de contrato)

| Decisão V2 | Implementação |
|---|---|
| Página única scrollável (RQ-01/02) | `ProductRoutingTab.tsx` reescrito: `EngineeringTabs` removido da aba; seções na ordem cabeçalho→KPIs→operações→estudo→resultados→análise visual. Tabs da ficha do produto preservadas. |
| Análise rápida (RQ-06/17) | Mesmo `POST /v1/products/{code}/line-balance`; prévia local de takt/tempo produtivo marcada como estimativa de entrada. |
| Configurar postos (RQ-07..10, 18) | `PostConfigurator.tsx`: `EngineeringDetailCard` por posto + `EngineeringMultiSelectField` (operações oficiais), `EngineeringIconButton` (mover/remover), operadores/paralelismo como hipótese — **nunca enviados ao contrato**; aviso explícito `DRAFT_LOCAL/SIMULATION` e "análise rápida não valida a distribuição manual". |
| Rascunho de sessão (RQ-11..13) | `routingStudyDraft.ts` (schemaVersion=2, chave `sub+produto+filial+estágio`, fingerprint de inputs, save/load/clear puros) + `useRoutingStudyDraft.ts` (autosave honesto, restore com validação de contexto/fonte, status Salvando/Salvo/Rascunho recuperado/Falha). `sessionStorage`; zero `localStorage`; zero JWT/resultados persistidos. |
| Limpar + Novo cenário (RQ-14/15) | `EngineeringConfirmDialog` no Limpar (escopo: só a chave do contexto); cenários A/B/C…≤4 via `EngineeringScopeChipBar`. |
| Resultados STALE (RQ-16) | Resultados transientes em estado; `inputsFingerprint` compara parâmetros atuais × calculados → selo STALE, nunca restaurados como CALCULATED. |
| Gráficos contextuais (RQ-19) | `ConfigurableSeriesChart`: tempo por peça sempre; tempo×takt e distribuição simulada só com resultado compatível — sem painéis vazios. |

Identidade de usuário: `httpClient.getTokenSubject()` (sub do JWT — não sensível) para isolamento do rascunho.

## 3. Verificação

| Camada | Resultado |
|---|---|
| Vitest | **505/505** (`routingStudyDraft.test.ts` 14 novos; `ProductRoutingTab.test.tsx` 23 reescritos para V2 — sem tabs internas, sem localStorage, sem algoritmo local, sem campos avançados no POST) |
| Typecheck / build | `tsc --noEmit` limpo; `vite build` OK |
| E2E HML (SSO real `hml-tester`) | **30/30** — desktop/tablet/mobile/390/320 × 6 cenários (página única, estudo+cenários, postos, rascunho refresh/restore/clear, análise visual, vazio honesto, zero `/apps/api-delpi` direto, zero pageerrors) |
| Evidência visual | ~100 capturas `e2e/artifacts/routing-contract/v2-*` inspecionadas: dark/light com paridade, postos, cenários, resultado, gráficos temáticos |
| Verificador oficial | `verify.py` → **INCONCLUSIVE** (`devin auth login` exige intervenção humana — mesmo bloqueio das rodadas anteriores; registrado em `.git/delpi-verifier/verdicts.jsonl`) |

## 4. Deploy

| Ambiente | SHA | Resultado |
|---|---|---|
| HML (`delpi-hml-engineering`) | `9e3445a53a` | rebuild via `up-hml-sequential.sh --fase mfe --build engineering`; bundle `App-Bvvu1rh1.js` com V2 verificado; 30/30 e2e autenticado |
| PROD (`delpi-engineering`, srv-api) | `36e1e3631a` | rebuild via `up-prod-sequential.sh --fase mfe --build engineering`; remoteEntry/expose `DVmCnXSx` e `App-Bvvu1rh1.js` servidos via `minhadelpi.com.br` (asset referenciado com `?v=14` — CF-cache-safe); BFF fail-closed |

Nota operacional: a stack `delpi-*` local é réplica; a produção real roda em srv-api junto à stack `delpi-hml-*`. Cloudflare pode reter 404/remoteEntry antigos por minutos — o remoteEntry referencia assets com `?v=`, imune a esse cache.

## 5. Limitações honestas registradas

- Distribuição manual de postos **não é validada pelo motor** — `DRAFT_LOCAL/SIMULATION` declarado na UI; ampliação do domínio exige decisão de arquitetura.
- `PROD_AUTHENTICATED_SMOKE = PENDING_USER_SMOKE` — requer principal humano Keycloak (mesmo gate do AC-18 anterior).
- Verificador oficial INCONCLUSIVE por infra de auth — não convertido em PASS; evidência alternativa = 30/30 e2e reais + inspeção visual.
