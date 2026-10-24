# E11.S7 — Decisão do PO: detalhe em página e seleção explícita de filial

**Data:** 2026-10-24 · **Status:** DECIDED / PLANNED (não implementado) · **Owner UX:** `plugins/supplies` · **Produto:** Portal Suprimentos, WF-16 / E11.

## Decisão vinculante do Product Owner

1. **O detalhe de Estoque de Segurança deve abrir em uma página própria**, não em modal, overlay ou drawer. Reutilizar o padrão de páginas internas do MFE, com caminho navegável, botão Voltar, estados completos, URL/F5/back/forward e Help.
2. Na listagem com filtro **Todas as Filiais** (`branch=all`), a linha é um **agregado legítimo por produto**, segundo a verificação `materials_base_cte`/`stock_agg_cte`. Ao clicar em **Ver detalhes**, primeiro exibir uma escolha explícita de filial **Santa Catarina (01)** ou **Espírito Santo (02)**; somente após a escolha, navegar para a página de detalhe usando `product_code` e filial concreta.
3. Nas listagens filtradas por `01` ou `02`, a ação abre diretamente a página de detalhe dessa filial. **Não escolher filial automaticamente no escopo consolidado.**
4. A escolha da filial **não altera o filtro da listagem nem os indicadores agregados**. Ao voltar, preservar filtros, paginação, ordenação e scroll quando viável no padrão atual; deep link e F5 devem restaurar o detalhe de filial concreta.
5. A página de detalhe consome exclusivamente as duas rotas BFF já contratadas: `GET /safety-stock/items/{code}/details?branch=01|02` e `GET /safety-stock/items/{code}/suppliers?branch=01|02`. Não enviar `all`, não realizar N+1, não adicionar endpoint/SQL/cálculo.
6. **Filial permanece filtro de dados, nunca permission**: capability `supplies.access` no BFF via Core. Não criar `supplies.unit.*`, não inferir permissão por filial.
7. Toda UX é em PT-BR: **Estoque de Segurança**, **Todas as Filiais**, **Selecionar filial**, **Ver detalhes**. Identificadores internos e parâmetros HTTP permanecem em inglês.

## Navegação e desenho contratual

- O Cursor deve inspecionar `App.tsx`, `pluginRoutes.ts`, manifest vigente, padrões reais de detalhe e rotas federadas **antes** de escolher a codificação do caminho. **Não inventar rota no manifest ou presumir `/:id` suportado**. Preferir página interna endereçável via estado de URL (ex.: `item` + `itemBranch`, se compatível) no path registrado, com renderização de tela inteira em vez de modal. Uma nova rota no manifest requer inventory de Core/produtores/consumidores e decisão específica antes de alteração.
- A seleção de filial pode ser uma etapa de seleção contextual leve (kit-first) antes da navegação. **O conteúdo do detalhe nunca deve ser exibido em modal**. Se precisar selecionar filial na própria página intermediária, essa etapa deve ter URL/navegação coerentes e não carregar dados de detalhe até a filial ser escolhida.
- Manter as seções já implementadas em E11.S3/S4: identificação, saldos, cobertura de compras, SC/PC/empenhos, projeção, consumo mensal/anual embutido, fornecedores. Reutilizar componentes/formatadores, migrando a composição do `SafetyStockDetailModal` para tela inteira sem recriar regras.
- Tratar 401/403/404/422/502, loading/empty/partial/error, payload inválido, troca rápida de identidade, cancelamento, resposta tardia, retry independente de fornecedores, acessibilidade, temas e mobile.
- Não antecipar E12, E17, E18, export ou `peer_branch_stock`.

## RQ/AC e testes

| AC | Critério |
|---|---|
| AC-01 | Em `all`, clicar ação pede seleção explícita entre `01` e `02`; não existe escolha automática |
| AC-02 | Em `01`/`02`, clicar navega diretamente à página de detalhe da mesma filial |
| AC-03 | Detalhe em página inteira, sem modal/drawer; reuso kit-first |
| AC-04 | `product_code + branch` concreto identifica tanto a URL quanto as chamadas BFF |
| AC-05 | F5/deep link/back/forward preservam a identidade e permitem voltar ao recorte |
| AC-06 | Lista consolidada não muda de filial ao abrir detalhe; URLs mantêm filtros e paginação |
| AC-07 | Dois GETs sob demanda, sem N+1 e sem chamada direta à `api-delpi` |
| AC-08 | Seções e estados existentes preservados, sem recálculo ou escrita ERP |
| AC-09 | Positive/sibling/negative: `all`, `01`, `02`, filial inválida, item ausente, falha parcial, cancelamento, troca rápida |
| AC-10 | Ajuda PT-BR sincronizada, teclado/foco, desktop/mobile e claro/escuro verificados ou INCONCLUSIVE declarado |
| AC-11 | Testes/build/regressão e smoke federado antes do gate final |

## Autoridade, drift e aceite

Esta decisão do PO **substitui a decisão anterior de apresentar o detalhe em `SuppliesModal` como UX-alvo**, sem apagar o fato histórico de E11.S3/S4/S5/S6, nem invalidar o deploy técnico realizado. Também resolve o `EXECUTION_DRIFT` identificado na revisão GPT de E11.S6, cuja causa era a premissa falsa de filial concreta em cada linha consolidada.

**Estado:** `E11.S7 = PLANNED / READY_TO_IMPLEMENT` sob autorização expressa; `E11_DEPLOY = PASS_DEPLOYED`; `GATE-FEATURE E11 = INCONCLUSIVE` até mudança publicada e smoke autenticado/visual. Nenhuma implementação de S7 é comprovada por este documento.

**Stop condition:** caso a página própria exija alteração material no manifest/Core ou novo contrato BFF, interromper subescopo e registrar `EXECUTION_DRIFT`; não abrir permissões, alterar produtor ou criar rotas externas silenciosamente.
