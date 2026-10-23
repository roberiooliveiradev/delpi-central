# X4.UX-R1.S9.D1 — Supplier Creation UX Polish — Federated Deploy & Visual Acceptance

**Status:** `DEPLOY_VERIFIED / GATE-FEATURE INCONCLUSIVE` — o bundle S9 já estava publicado e saudável quando o inventário rodou (rebuild dispensado por regra explícita da task); aceite visual/interativo **TEST_NOT_RUN** sem navegador autenticado.

| Item | Valor |
|---|---|
| BASE HEAD (local) | `b77d1be3a6` → rebase `86294797d1` |
| ORIGIN MAIN | `86294797d1` (pré-push) |
| SOURCE S9 SHA | `71ffc32ce8` (impl) / `6df86f5a32` (doc) |
| PRODUCTION HOST | srv-api `192.168.1.237` — SSH operador OK |
| PRODUCTION CHECKOUT SHA | `43d5c61965` — **contém** `71ffc32ce8` (`merge-base --is-ancestor` PROVEN) |
| PRODUCTION GIT STATUS | limpo |

## 1. Inventário produtivo (pré-deploy)

| Item | Valor |
|---|---|
| MFE IMAGE | `infra-supplies` `1eb05c40f27f` — criada **2026-10-23T14:22:51Z** (~11:22 -03:00), compose `infra/supplies` |
| CONTAINER | `delpi-supplies` Up (nginx, sem healthcheck próprio) |
| supplies-api | `acc772fa65fa` (S8.D1, healthy) — **skipped** (S9 não tocou backend) |
| api-delpi / external-data / core / keycloak | **skipped** — sem mudança S9 |
| ERP WRITE GATE | `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` — **confirmado no env de `delpi-api-delpi` e `delpi-supplies-api`** |
| Containers unhealthy | **0** |

## 2. Decisão: deploy dispensado

A imagem `infra-supplies` já havia sido reconstruída minutos antes do inventário, a partir do checkout `43d5c61965` (que contém S9). Regra da task: *«Se a imagem ou o bundle já estiver atualizado, dispensar rebuild e registrar evidência. Não executar deploy desnecessário.»* — **nenhum comando de deploy executado por esta tarefa**.

## 3. Gate do bundle federado — `PASS`

Cadeia real verificada no container e publicamente:

```
remoteEntry.js (200)
  └─ expose_App-Brmm4idS.js
        └─ App-DJfMgiUV.js  (271.177 bytes, 200 público)
```

Marcadores materiais S9/S8 presentes no bundle compilado: `America/Sao_Paulo` ×5, `horário de Brasília` ×4, `BrasilAPI`/`dados públicos de terceiros`, `existing-suppliers`, `creation-preview`, `inputMode` ×2.
Marcadores proibidos **ausentes** (0 ocorrências): `api-delpi`, `brasilapi.com.br`, `s2s_`, `client_secret`, `Service-Authorization` — MFE segue BFF-only.

> Observação: o hash final `App-DJfMgiUV.js` difere do build local `App-KA33PBbe.js` — hash de build não é prova de conteúdo; a verificação foi por marcadores no artefato publicado, conforme instruído.

## 4. Smoke HTTP read-only — `PASS`

| Check | Resultado |
|---|---|
| `GET /apps/supplies/remoteEntry.js` | 200 |
| `GET /apps/supplies/assets/App-DJfMgiUV.js` | 200 (271 KB) |
| `POST /apps/supplies-api/suppliers/creation-preview` sem token | 401 (fail-closed) |
| `GET /apps/supplies-api/suppliers/existing-suppliers` sem token | 401 (fail-closed) |
| Logs nginx 30 min | 0 `error/crit`; tráfego real servindo o bundle S9 (200) |
| Escritas supplier (POST/PUT reais) | **0 executadas** — gate OFF |

## 5. Testes visuais/interativos (A–E)

| Grupo | Resultado |
|---|---|
| A1–A5 máscara CNPJ assistido | `TEST_NOT_RUN` |
| B caret/edição no meio | `TEST_NOT_RUN` |
| C formulário CPF/CNPJ por tipo | `TEST_NOT_RUN` |
| D data/hora Brasília vs `retrieved_at` | `TEST_NOT_RUN` |
| E fonte humanizada/proveniência | `TEST_NOT_RUN` |
| Regressão S8 interativa | `TEST_NOT_RUN` |
| Mobile/temas/teclado/foco | `TEST_NOT_RUN` |

**VISUAL = `INCONCLUSIVE`** — sem sessão de navegador autenticada disponível nesta execução; nenhum PASS visual inferido do bundle.

## 6. Rollback

| Item | Valor |
|---|---|
| Imagem anterior (`6b3130be529f`, S8.D1) | **não presente** em `docker images` (pruned) |
| Rollback real | rebuild a partir do SHA `1c7a96ce33` (S8.D1) ou `a172180890` (S8 impl) via procedimento oficial — caminho conhecido |
| Rollback executado | Não — sem necessidade |

## 7. AC COVERAGE

| AC | Resultado |
|---|---|
| AC-01 bundle S9 publicado | `PASS` (marcadores no artefato) |
| AC-02 MFE saudável | `PASS` (Up, 0 unhealthy, tráfego 200) |
| AC-03–07 máscara/colagem/caret/CPF-CNPJ | `TEST_NOT_RUN` (interativo) |
| AC-08 inválido bloqueia consulta | `TEST_NOT_RUN` (lógica unitária já PASS em S9) |
| AC-09/10 horário Brasília + timestamp íntegro | `TEST_NOT_RUN` visual; `PASS` unitário em S9 |
| AC-11/12 fonte amigável + proveniência | `PASS` marcadores + contrato intacto; visual `TEST_NOT_RUN` |
| AC-13 regressão S8 | `PASS` estrutural (marcadores S8 + endpoints 401); interativo `TEST_NOT_RUN` |
| AC-14 AuthZ | `PASS` (401 fail-closed) |
| AC-15 escrita ERP OFF | `PASS` (env ×2 containers) |
| AC-16 mobile/temas/teclado | `TEST_NOT_RUN` |
| AC-17 rollback conhecido | `PASS` (rebuild por SHA; imagem antiga pruned — registrado) |
| AC-18 doc/commit/push | `PASS` (este documento) |

## 8. Residuais / próximos passos

- Aceite visual/interativo (A–E + caret + mobile/temas) — pendente de sessão de navegador autenticada (PO ou execução com ferramenta de browser).
- Imagem de rollback anterior não sobrevive no host — reversão exige rebuild por SHA; registrar se política de retenção de imagem for exigida.
- `GATE-FEATURE S9 = INCONCLUSIVE` — deploy técnico saudável, promoção integral pendente de evidência visual.


## 9. Revisão GPT — aceite arquitetural do runtime (2026-10-23)

**Decisão: `ACCEPT_WITH_RESIDUAL` para a publicação técnica S9.D1**, baseada no relatório e nas evidências versionadas no GitHub (execução Cursor, commit `3fd88ec163`). O GPT não reexecutou SSH, Docker nem sessão autenticada no navegador. A imagem MFE já continha S9 antes desta tarefa, portanto **deploy/rebuild executado nesta tarefa = nenhum**. Bundle federado S9 publicado/HTTP 200, endpoints sem token 401, serviços saudáveis reportados e ERP write gate OFF são suficientes para aceite do gate técnico, **não** para aceitar o comportamento visual.

**Residuais:** testes A1–A5 (máscara/colagem), B (caret e edição no meio), C (CPF/CNPJ por pessoa), D (hora baseada em `retrieved_at` e fuso de Brasília), E (fonte amigável), regressão visual S8 e mobile/temas/teclado = `TEST_NOT_RUN`. `GATE-FEATURE S9 = INCONCLUSIVE` até evidência interativa. A imagem anterior `6b3130be529f` foi pruned: rollback por rebuild a partir de SHA histórico **é procedimento possível declarado**, mas não equivale a rollback imediato por imagem retida; confirmar dependências, procedimento e política de retenção antes de próxima mudança produtiva.

**Próxima ação:** validação manual pelo PO no navegador autenticado, sem gravação de fornecedores. Capturar resultados por cenário, URL/bundle, hora de verificação e evidências sanitizadas; não inferir `PASS` de marcadores do bundle. Nenhuma alteração de BFF/api-delpi, RBAC ou gates de escrita autorizada por esta revisão.
