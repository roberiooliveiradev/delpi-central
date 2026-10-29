# ENGINEERING.LMP.UX.NAV.R1 — Separação da navegação LMPs / Não Conformidades

**Tipo:** plano de implementação para Devin — NÃO implementação  
**Owner funcional:** Portal Engenharia / Engenharia  
**Coordenação:** EVA — Architecture / Coordination  
**Estado:** PLANNED — execução requer missão própria  
**Data:** 2026-10-29  
**Base de evidência:** G5, G5.V, DEPLOY.01 (docs 41, 43, 44); inspeção do código em `origin/main`; captura de produção fornecida pela Coordenação.

## 1. Decisão aprovada e resultado esperado

A página **Acompanhamento de LMPs** deve ser um destino direto de **Início → LMPs**, sem navegação local em abas **Dashboard** e **Registro de não conformidades**. O próprio contexto, título e breadcrumb identificam a página. A área **Não Conformidades** será funcionalidade independente, acessada por caminho próprio no **Início / catálogo do Portal Engenharia**, quando seu contrato e workflow forem autorizados. Não anunciar a área como funcional enquanto não estiver pronta. Não levar o usuário do novo Portal ao CRUD legado como atalho de uma aba LMP.

Preservar integralmente dados, indicadores, filtros, visualizações, tabela, exportações, detalhe de proposta, URL compartilhável e autenticação. O dashboard legado `/apps/dashboard-lmps` e seu CRUD de NC continuam operacionais e independentes até gates de migração/cutover específicos. **Este plano não autoriza cutover, deploy, mudança de permissão, alteração de banco ou migração de NC.**

### Fluxo alvo

- **Início → LMPs:** `/apps/engineering/lmps` → página geral diretamente, sem tabs intermediárias.
- **LMPs → proposta:** `/apps/engineering/lmps/ov/{sale_number}` com filtros/branch preservados e retorno à lista.
- **Início → Não Conformidades (futuro):** entrada própria no catálogo, inicialmente omitida ou marcada `comingSoon` não clicável se esse for o padrão autorizado do Portal. Contrato e rota definitiva ficam `TARGET` até gate NC; não antecipar `/apps/engineering/lmps/nonconformities` como rota funcional final.
- **Legado:** `/apps/dashboard-lmps` e `/apps/dashboard-lmps/nonconformities` permanecem como estão.

## 2. Evidência do código atual — PROVEN

| Fonte canônica | Observação |
|---|---|
| `plugins/engineering/src/features/lmps/components/LmpsNav.tsx` | Constrói exatamente dois itens: `Dashboard` (interno) e `Registro de não conformidades` (href externo legado). |
| `plugins/engineering/src/features/lmps/pages/DashboardLmpsPage.tsx` | Importa e renderiza `LmpsNav`; localizar JSX exato no HEAD antes de editar. |
| `plugins/engineering/src/features/lmps/LmpsFeature.tsx` | Reconhece caminhos de NC com `NcLegacyRedirectNotice` e mantém dashboard montado no detalhe para preservar estado. |
| `features/lmps/constants/routes.ts` | Define `LMPS_BASE_PATH`, `LEGACY_NONCONFORMITIES_HREF`, `LMPS_ROUTES.nonconformities` e helpers do detalhe. |
| `features/lmps/utils/routeParser.ts` | Aceita `nonconformities`, `nonconformity-detail`, `nonconformity-new`, `ov-detail`. |
| `plugins/engineering/src/content/engineeringRouteCatalog.ts` | Item `lmps` já é `target: { kind: "internal", view: "lmps" }`, protegido na visibilidade por `engineering.access`. |
| `plugins/engineering/src/app/openCatalogRoute.ts` | Destinos internos usam o roteador do Portal, externos usam href governado. |
| `plugins/engineering/src/app/engineeringRoutes.ts` | Reconhece `/apps/engineering/lmps` e subcaminhos. |
| Documento 43, §4 | Descreve as tabs como remanescente visual do MFE legado. |
| Documento 44 | Produção validada; não há autorização de alterar registro/manifest neste trabalho. |

**Limitação da evidência:** capturas comprovam a presença das abas na página produtiva, não validam todas as origens possíveis de links. O executor deve fazer residual search antes e depois.

## 3. Boundaries e ownership — invariantes

1. **Core API:** permissões efetivas e registro de apps; Keycloak: autenticação.
2. **Engineering API:** única autoridade funcional da nova superfície; `engineering.access` operacional, `engineering.manage` administração, sem hierarquia implícita.
3. **API DELPI:** facts e integração técnica protegidos, sem `engineering.*` em guards; S2S em backend, nunca no navegador.
4. **Portal Engenharia:** composição visual, catálogo, rotas e UX.
5. **NC:** workflow independente e ainda não migrado; persistência e writes exigem gate próprio com owner, AuthZ live, contratos e rollback.
6. **Strategic Indicators:** metas/IDD; não modificar.
7. **EVA e demais consumidores:** sem alteração nesta missão.

Nenhuma alteração de AuthN/AuthZ, Core grants, Keycloak, manifests, gateway, Engineering API, API DELPI, PostgreSQL ou legacy MFE é necessária para o comportamento solicitado, salvo evidência contrária → `ARCHITECTURE_DECISION_REQUIRED`.

## 4. Plano de implementação do Devin

### Etapa P0 — Reancorar e inventariar (READ)

- `git fetch origin; git rev-parse HEAD; git rev-parse origin/main; git status --short; git log -10 --oneline`.
- Ler `AGENTS.md`, authorities frontend/MFE, routing, accessibility, tests, docs 40–44.
- Inspecionar os arquivos da tabela §2 e todos os usos reais via busca de `LmpsNav`, `LEGACY_NONCONFORMITIES_HREF`, `LMPS_ROUTES.nonconformities`, `nonconformity-new`, `nonconformity-detail`, `NcLegacyRedirectNotice`, `Registro de não conformidades`, `Dashboard`.
- Classificar cada uso como `ACTIVE_UI`, `LEGACY_COMPAT_DEEP_LINK`, `TEST`, `DOC`, `UNRELATED`. Não remover código por coincidência textual.
- Inventariar o catálogo e a política atual de itens `comingSoon`; identificar se entrada NC separada já existe. Não criar duplicatas.

### Etapa P1 — Remover as duas abas da página LMPs

- Retirar a renderização de `LmpsNav` em `DashboardLmpsPage.tsx`.
- Remover import, props, estilos e wrappers que só existam para essas abas **se** comprovadamente não possuírem outros consumidores.
- Se `LmpsNav.tsx` ficar sem uso, removê-lo com seus testes/estilos exclusivamente associados; preservar helpers compartilhados e comentários relevantes.
- Manter `PagePath`, `PageHero`, filtros, hero actions, KPIs, gráficos, tabela, exports e detalhe inalterados em semântica.
- Ajustar espaçamentos resultantes da retirada da faixa de tabs respeitando tokens `--en-*` e wrappers `engineeringUi`; não introduzir CSS global.
- **Não** transformar a remoção em redesign amplo, não alterar valores ou fórmulas.

### Etapa P2 — Entrada autônoma de NC no Início, sem habilitação prematura

- Rever a seção **Trabalho** de `ENGINEERING_CATALOG` e convenção de `comingSoon`.
- Estado desejado do produto: **LMPs** e **Não Conformidades** são destinos conceitualmente irmãos, não tabs de LMP.
- Se adequado ao padrão atual, preparar entrada de NC com `comingSoon: true`, **sem destino executável**, sem requiredPermission legado e sem rota fictícia funcional. Se o tipo do catálogo exigir um target válido, não inventar uma rota que possa ser aberta: preferir registrar a entrada como `TARGET` documental até o gate NC ou manter disabled com prova de não execução.
- Não apontar o novo item para `/apps/dashboard-lmps/nonconformities` por conveniência.
- Sem criação de Core app, grants, manifest ou menu corporativo nesta etapa.

### Etapa P3 — Compatibilidade de deep links históricos

- Verificar `LmpsFeature.tsx`, `routeParser.ts`, `routes.ts` e testes atuais.
- **Não apagar automaticamente** o reconhecimento das rotas internas históricas `/apps/engineering/lmps/nonconformities{,/new,/{id}}`: elas podem existir em favoritos, links e histórico.
- Preferência de menor diff: manter temporariamente `NcLegacyRedirectNotice` **somente para acesso direto a um deep link histórico**, nunca como aba, card novo ou caminho principal. Seu texto deve indicar explicitamente que NC não está disponível na nova experiência e que o legado continua separado; qualquer link de coexistência deve permanecer governado e não representar um novo workflow NC.
- Caso telemetria/consumidores demonstrem inexistência e seja aprovado remover essa compatibilidade, registrar evidência e impacto antes da remoção.
- Preservar `/apps/engineering/lmps/ov/{sale_number}`, filtros e navegação Voltar.
- Não criar redirect automático amplo LMP → Dashboard legado ou NC legado.

### Etapa P4 — Acessibilidade, UX e regressão

- Remover os elementos da árvore de acessibilidade junto com a UI, inclusive `aria-current`, `nav` e labels de `LmpsNav` se extintos.
- Garantir breadcrumb e título `Acompanhamento de LMPs` distinguindo claramente o local; evitar cabeçalhos redundantes.
- Preservar busca, filtro temporal, status, unidade, tipo, select múltiplo, tabs de agrupamento **dos gráficos** (dia/semana/mês/ano) — estes NÃO são as tabs a remover.
- Verificar tema claro/escuro, desktop/tablet/mobile, sem barra vazia ou espaço residual.
- Garantir que entrada NC separada, se exibida, não gere navegação ou fetch indevido.

## 5. Escopo permitido e exclusões

**Permitido:** diff mínimo em `plugins/engineering` para a navegação da feature, teste regressivo, documentação/help contextual somente se impactados, imagens de verificação não sensíveis.

**Proibido:** alterar `plugins/dashboard-lmps`; migrar NC READ/WRITE; expor CRUD no Portal; criar API NC; alterar autorização; criar rota executável para NC; mexer em BOM, KPIs, metas, IDD, dados LMP, exportações, S2S, Core ou Keycloak; alterar manifesto, fazer deploy ou cutover sem gate operacional. Não remover `Dias sem NC` do Dashboard LMP: é indicador, não navegação.

## 6. Matriz de testes e evidência

| ID | Caso | Resultado exigido |
|---|---|---|
| UXNAV-01 | Acesso pelo Início → LMPs | `/apps/engineering/lmps`, página renderizada |
| UXNAV-02 | Página geral sem `Dashboard` tab | Tab ausente DOM e accessibility tree |
| UXNAV-03 | Página geral sem `Registro de não conformidades` tab | Tab/link ausente da página |
| UXNAV-04 | Indicador `Dias sem NC` | Presente, dado oficial inalterado |
| UXNAV-05 | KPIs, gráficos, 6 filtros, tabela e exports | Sem regressão |
| UXNAV-06 | Detalhe da OV e retorno | Preserva pathname, branch e filtros |
| UXNAV-07 | URL direta/refresh | Pass |
| UXNAV-08 | Início → NC | Entry ausente ou `comingSoon` não executável, conforme decisão P2 |
| UXNAV-09 | Deep link NC histórico | Estado governado compatível, sem abrir NC nova |
| UXNAV-10 | Legado `/apps/dashboard-lmps` | Intacto |
| UXNAV-11 | Tema light/dark + viewports | Sem gaps, overflow ou layout quebrado |
| UXNAV-12 | AuthZ | `engineering.access` permanece exclusiva no novo Portal; backend fail-closed |
| UXNAV-13 | Network no browser | Apenas Engineering API para nova feature, nenhum bypass direto API DELPI |
| UXNAV-14 | Build/lint/typecheck/unit | PASS ou findings classificados |
| UXNAV-15 | Sem alteração de backend/manifests | Diff restrito, salvo decisão nova |

Rodar testes existentes em `plugins/engineering` (Vitest, typecheck, lint, build); adicionar testes direcionados de renderização sem as tabs, catálogo `comingSoon`, parser/deep-link e preservação do detalhe. Usar browser real Playwright/Chromium em ambiente autorizado: light/dark desktop+mobile, screenshot antes/depois, clique e Network. Se browser não disponível, `TEST_NOT_RUN` e **não** declarar homologação visual. Reexecutar auditorias relevantes e residual search, no SHA final.

## 7. Passos de entrega e gates

1. **PREPARE:** reancoragem e inventário com evidências, RQ/AC; escolher diff mínimo.
2. **IMPLEMENT:** retirar somente a navegação local, definir representação não operacional NC no catálogo se aplicável, preservar deep links.
3. **TEST:** testes específicos + regressão + navegador com host real e credenciais autorizadas, sem publicar dados sensíveis.
4. **VERIFY:** residual search, checagem de boundary, sem alterações em MFE legado, no SHA final.
5. **DOCUMENT:** próximo documento de evidência sequencial, com paths, testes, screenshots referenciadas e pendências.
6. **DELIVER:** commit/push somente conforme autoridade operacional vigente, sem sobrescrever concorrentes; informar SHA e resultado.

Não iniciar NC gate, desativação do legado, deploy produtivo ou cutover automaticamente.

## 8. Critérios de aceite finais

- **AC-01:** Acompanhamento de LMPs acessível diretamente por Início → LMPs.
- **AC-02:** Abas locais `Dashboard` e `Registro de não conformidades` removidas da página geral.
- **AC-03:** Cards (inclusive Dias sem NC), gráficos, filtros, tabela, exports, detalhe e histórico preservados.
- **AC-04:** Sem ação NC executável a partir da página LMP; futuro NC separado no Início com status honesto.
- **AC-05:** Deep links antigos inventariados e tratados sem quebra silenciosa.
- **AC-06:** Design system e acessibilidade do Portal preservados em light/dark e mobile.
- **AC-07:** `engineering.access` permanece a permissão funcional, sem permissões legadas no novo Portal.
- **AC-08:** Engineering API, API DELPI, Core, Keycloak, SI e MFE legado intocados.
- **AC-09:** Testes automatizados e evidência real de navegador ligados ao SHA.
- **AC-10:** Zero cutover/deploy não autorizado e documentação publicada.

Status de execução: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Status de fatos: `PROVEN | TO_INVENTORY | PLANNED | TARGET`.

## 9. Relatório obrigatório do Devin

```text
EVA EXECUTION REPORT
TASK: ENGINEERING.LMP.UX.NAV.R1 — Separate LMP and NC Entry Points
BASE_HEAD:
FINAL_HEAD:
AUTHORITIES_READ:
ROOT_CAUSE:
FILES_INSPECTED:
FILES_CHANGED:
LMPS_NAV_REMOVAL:
NC_ENTRY_DECISION:
NC_HISTORICAL_DEEP_LINKS:
LMP_ROUTES_AND_FILTERS:
DATA_AND_UI_PARITY:
A11Y_AND_RESPONSIVENESS:
AUTHZ_AND_BOUNDARIES:
LEGACY_COMPATIBILITY:
BROWSER_EVIDENCE:
TEST_COMMANDS:
TEST_RESULTS:
TESTED_SHA:
ARCHITECTURE_AUDITS:
RESIDUAL_SEARCH:
DOCUMENT_PATH:
COMMIT_SHA:
AC_RESULTS:
EXECUTION_DRIFT:
ARCHITECTURE_DECISION_REQUIRED:
UNRESOLVED:
NEXT_BOUNDED_STEP:
```

**Saída do gate:** `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | INCONCLUSIVE` pela Coordenação. Este plano é a authority de execução de UX/navegação para o Devin, mas não é autorização para mudar ownership de NC, publicar, ou fazer cutover.
