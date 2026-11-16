# Prompt para o Cursor — Fusão do Portal Financeiro, M0 (inventário somente leitura)

> Versão 2 (16/11/2026): o owner já decidiu D1–D10 ([ADR-004](../../adr/ADR-004-fusao-portal-financeiro.md)).
> O M0 não serve mais para decidir permissões; levanta o que a implementação precisa e o impacto do corte.

```text
PROMPT CURSOR — FUSÃO DO PORTAL FINANCEIRO · M0 — inventário somente leitura

CONTEXTO
O Portal Financeiro (plugins/financial + financial-api) entra no Portal Controladoria & Finanças.
Decisões do owner em docs/12-roadmap-e-evolucao/controllership-finance/adr/ADR-004-fusao-portal-financeiro.md
e financial-merge/plan.md §6–§8: tudo sob controllership-finance.access (export incluso), todas as
filiais, rotas na controllership-finance-api, duas páginas de despesas por centro de custo (Financeiro e
R10 não são equivalentes), Questor fica na financial-api por ora, apps legados e /apps/financial seguem
no ar até autorização. NADA muda em runtime no M0.

ESCOPO (somente leitura — sem alterar código, rota, permissão, banco, container ou deploy)
I1 Contratos: por página do MFE (plugins/financial/src/pages) → rotas da financial-api → rotas
   upstream (api-delpi, strategic-indicators-api, Questor). DTOs de entrada/saída, paginação, export,
   e onde o gate de filial e de permissão por área acontece hoje (para remover na migração).
I2 O que a CF-API precisa para hospedar as rotas: clientes HTTP já existentes (api-delpi,
   strategic-indicators-api?), escopos S2S, cache, testes; o que falta.
I3 Dependências da financial-api que FICAM (Questor): rotas S2S usadas pelo LNF e pela Auditoria;
   garantir que nada delas muda. Consumidores externos (tv-dashboard-api, minha-delpi-ai-api): usam a
   financial-api ou a api-delpi direto?
I4 Quem ganha acesso novo (D1/D2): contagem de usuários com controllership-finance.access que hoje
   NÃO têm financial.access; com financial.access mas sem controllership-finance.access (perderiam o
   caminho no corte se o redirect exigir access do Portal); com só uma filial. No repositório só
   contagens; lista nominal só no report ao owner, fora do git.
I5 Uso: acessos por página do Portal Financeiro e dos três legados nos últimos 30 dias (logs do
   gateway/BFF). Se não houver log que permita, INCONCLUSIVE com motivo.
I6 Despesas por centro de custo, 2026-10, filial 01 e 02: total e nº de linhas no Financeiro × R10
   (seleção oficial e investigação), e a explicação da diferença pelos três motivos já conhecidos
   (eixo D1_EMISSAO × D1_DTDIGIT; centro de custo obrigatório na view; exclusões oficiais do R10). Serve
   para a ajuda das duas páginas — não para escolher motor.
I7 Visual: por página do Financeiro, o que muda para o padrão do Portal (hero com filtros, PagePath,
   tabelas do kit com ordenação/colunas, gráficos no padrão do Comercial: ChartViewShell +
   ChartTypeSegmentToggle + MultiTypeSeriesChart).
I8 Redirect: mapa /apps/financial/<área> → rota nova no Portal; o host suporta redirect por manifest?

ENTREGA
docs/12-roadmap-e-evolucao/controllership-finance/financial-merge/inventory.md com I1–I8, cada fato
PROVEN (arquivo:linha ou comando) · TO_INVENTORY · INCONCLUSIVE (motivo), e «O que isso muda no M2».

VERIFICAÇÃO
Pedido ao verificador (AGENTS.md § Verificação): objetivo = M0 I1–I8; escopo = inventory.md;
alegações = cada fato com evidência; o verificador confere amostras. Até 3 rodadas; veredito sem edição.

REGRAS
main sem branch; git add só do inventory.md; nenhum dado pessoal ou financeiro detalhado no repositório
(contagens e totais agregados de I6 podem ir; nomes, CNPJ e valores por cliente não); somente leitura em
PROD; nunca imprimir token/segredo. Parar ao concluir.
```
