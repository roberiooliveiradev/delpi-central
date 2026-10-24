# E11.S7 — Implementação: detalhe em página completa + seleção de filial

**Data:** 2026-10-24 · **Status:** IMPLEMENTADO (deploy registrado abaixo) · **Owner:** `plugins/supplies` · **Produto:** Portal Suprimentos, WF-16 / E11.

Decisão vinculante: [E11-S7-DETAIL-PAGE-PO-DECISION.md](./E11-S7-DETAIL-PAGE-PO-DECISION.md) (commits `178de6b128…` e `4ac352476a…`, ancestrais de `main`).

## O que mudou

### Página própria de detalhe

- Nova view `safety_stock_detail` resolvida pelo roteador interno do MFE em `safety-stock/{branch}/{productCode}` — mesmo padrão de `purchase-orders/{branch}/{order}`, `purchase-requests/{branch}/{request}` e `suppliers/{code}/{store}`. **Sem rota nova no manifest/Core, sem `EXECUTION_DRIFT`.**
- `SafetyStockDetailPage.tsx` recebeu a composição completa migrada de `SafetyStockDetailModal.tsx` (arquivo removido — sem detalhe paralelo): identificação, saldos por armazém, cobertura do déficit, pedidos de compra, solicitações, empenhos, projeção, consumo mensal/anual e fornecedores vinculados.
- Shell de página canônico: `SuppliesPagePath` («Estoque de Segurança» → retorno à listagem) + `SuppliesPageHero` (título `Material {código}`, descrição cadastrada, identidade produto+filial) + seções/tabelas existentes.
- Os mesmos invariantes da E11.S3/S4 permanecem: dois canais independentes (detalhe × fornecedores), `AbortController` por troca de identidade, estado chaveado por `branch|productCode`, retry por canal, 401/403/404/502 e payload malformado tratados, `detailMatchesTarget` exigindo `product_code + branch` exatos (zeros à esquerda significativos), zero N+1.

### Seleção explícita de filial (escopo consolidado)

- Linha com `branch=all` (recorte «Todas as Filiais») → clicar na linha ou em «Ver detalhes» abre `SafetyStockBranchChoiceDialog`: «Selecionar filial», «Escolha a filial para consultar os detalhes deste material.», opções **Santa Catarina — 01** e **Espírito Santo — 02** (`role="radiogroup"`), «Cancelar» e «Ver detalhes desta filial» (desabilitado até a escolha — **nenhuma filial é pré-selecionada**).
- A etapa de escolha é um componente contextual do kit (`SuppliesModal`) e **não executa nenhum request de detalhe** — o conteúdo do produto só existe na página.
- Linha com `01`/`02` → navegação direta para a página de detalhe da filial.

### Navegação e URL

- `?item=..&itemBranch=..` **legado** (E11.S3) ainda é parseado e redireciona (replace) para a rota canônica de detalhe; `buildUrlSearch` não emite mais esses parâmetros.
- O recorte da listagem é carregado para o detalhe em `?from=<query-codificada>` — «Voltar» restaura filtros, ordenação e paginação exatos, **inclusive `branch=all`** (a escolha de filial do detalhe nunca altera o filtro da lista).
- F5/deep link restauram `safety-stock/{branch}/{code}`; back/forward funcionam via `navigatePluginPath` + `popstate`.
- `safety-stock/all/{code}` ou filial inválida na URL → página de detalhe exibe estado «Filial não identificada» com retorno à listagem — **o BFF nunca recebe `all`**.

## Contratos, segurança e produtor

- Apenas os dois GETs contratados: `items/{code}/details?branch=01|02` e `items/{code}/suppliers?branch=01|02`. Nenhum endpoint, DTO, SQL, permission ou mudança de produtor.
- `branch` segue filtro de dados; autorização continua central (`supplies.access` via BFF/Core). `canAccessView("safety_stock_detail")` usa a mesma capability — nenhum grant novo.
- Cálculo consolidado do produtor intacto; ERP writes permanecem OFF.

## Evidências de verificação

- **Testes MFE:** 437 pass (+4 sobre S6) — resolução da rota de detalhe (concreta/inválida/encodada), guarda de `all`, seletor sem default/sem fetch/cancelável, remoção do modal, serialização de URL sem `item`/`itemBranch`, deep link legado.
- **TypeScript:** `tsc --noEmit` limpo. **Build:** Vite/federation OK.
- **Lint:** feature `safety-stock/` zerada; baseline global inalterada (10 erros / warnings pré-existentes de outros escopos).
- **Regressão:** E10 (inventory), E13/E14 (purchase orders/requests/suppliers) — suíte completa 45 arquivos verde.
- `git diff --check` limpo; busca residual sem `ESTSEG` na UX, sem `SafetyStockDetailModal`, sem `branch=all` para endpoints de detalhe, sem acesso direto a `api-delpi`.

## Deploy e gate

- **Deploy canônico:** `srv-api` → `git pull --ff-only` (`d525dcec01`) → `up-prod-sequential.sh --fase mfe --build supplies` (somente o MFE afetado).
- **Imagem:** `sha256:ffa2e9e492ff` (anterior `cde6ec36fa76`, S6). **Bundle servido:** `App-BdqsXiwp.js` no container `delpi-supplies`, contendo a rota `safety-stock/{branch}/{code}` e o seletor de filial (`branch-choice`). Logs nginx limpos.
- **Rollback:** `git pull` para `023c53efee` + imagem `cde6ec36fa76` (S6) — não executado.
- **AUTHENTICATED_SMOKE / QA visual:** `INCONCLUSIVE` — requer sessão real autorizada; não simulado.
- **GATE-FEATURE E11:** permanece `INCONCLUSIVE` até jornada autenticada + homologação visual do PO.

- **AUTHENTICATED_SMOKE / QA visual:** `INCONCLUSIVE` — requer sessão real autorizada; não simulado.
- **GATE-FEATURE E11:** permanece `INCONCLUSIVE` até jornada autenticada + homologação visual do PO.

## Arquivos

- `plugins/supplies/src/app/pluginRoutes.ts` (+test) — view/rota/builder/nav.
- `plugins/supplies/src/App.tsx` — dispatch `safety_stock_detail`.
- `plugins/supplies/src/features/safety-stock/SafetyStockDetailPage.tsx` — **nova** (migração do modal).
- `plugins/supplies/src/features/safety-stock/SafetyStockBranchChoiceDialog.tsx` — **nova** (seleção explícita).
- `plugins/supplies/src/features/safety-stock/SafetyStockDetailModal.tsx` — **removido**.
- `SafetyStockPage.tsx`, `query.ts` (+test), `content.ts`, `SafetyStock.structural.test.ts`, `index.css`, `content/helpTooltips.ts`, `content/userManualContent.ts`.


## Revisão GPT — E11.S7 (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para código e publicação técnica, sem fechar `GATE-FEATURE E11`. Inspecionados no source `3039f729c8`: este documento, `pluginRoutes.ts`, `SafetyStockPage.tsx` e `SafetyStockBranchChoiceDialog.tsx`. Confirmados página interna de detalhe `safety-stock/{branch}/{productCode}`, seletor explícito de filial para linha consolidada com confirmação desabilitada antes de escolha, e ausência de filial default no seletor. A remoção do modal de detalhe, testes 437 PASS/build e deploy MFE `d525dcec01` são evidências reportadas pelo executor, não reexecutadas nesta revisão.

**Residuais de aceite:** smoke autenticado e QA visual em produção ainda `INCONCLUSIVE`; verificar fluxo `all → escolher filial → página inteira → Voltar`, `01/02` diretos, F5/deep links e telas mobile/temas. O seletor implementa `role='radiogroup'` com `button role='radio'`, mas a navegação semântica completa de teclado (setas/Tab/foco, além de Enter/Espaço) ainda precisa ser comprovada por teste funcional e corrigida se não aderir ao padrão do kit. Não inferir acessibilidade PASS a partir da presença de ARIA. Nenhuma mudança em BFF, Core, manifest, API TOTVS ou RBAC é justificada por esta revisão.

**Estados:** `E11_S7=ACCEPT_WITH_RESIDUAL` em código; `E11_DEPLOY_STATUS=PASS_DEPLOYED` conforme relatório; `GATE-FEATURE E11=INCONCLUSIVE` até evidências reais.
