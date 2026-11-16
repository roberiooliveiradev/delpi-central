# Prompt para o Cursor — Fusão do Portal Financeiro, M0 (inventário somente leitura)

```text
PROMPT CURSOR — FUSÃO DO PORTAL FINANCEIRO · M0 — inventário somente leitura

CONTEXTO
O owner decidiu fundir o Portal Financeiro (plugins/financial + financial-api) no Portal Controladoria
& Finanças, com as permissões do Portal (controllership-finance.access e .manage). Plano e decisões
pendentes em docs/12-roadmap-e-evolucao/controllership-finance/financial-merge/plan.md (doc 172).
O M0 levanta os fatos que o owner precisa para decidir D1–D7. NADA muda em runtime.

ESCOPO (somente leitura — sem alterar código, rota, permissão, banco, container ou deploy)
I1 Portal Financeiro: páginas do MFE (plugins/financial/src/pages) × rotas da financial-api × rotas da
   api-delpi/strategic-indicators-api/Questor que cada uma chama; contratos (DTOs); gates de permissão
   e de filial no código (onde e como financial.view.filial-01/02 restringem dado).
I2 Consumidores da financial-api: gateway (nginx.conf, nginx.dev.conf, hml-proxy-locations.conf),
   infra/docker-compose*.yml, shared/delpi_auth (S2S), controllership-finance-api (LNF e Auditoria —
   quais rotas, quais escopos S2S), tests/contracts, scripts/ci; tv-dashboard-api e
   minha-delpi-ai-api (apontam para a financial-api ou para a api-delpi direto?).
I3 Plugins legados dashboard-financial, financeiro-centro-custo, financeiro-inadimplencia: ainda
   estão no compose/gateway/menu de PROD? Qual BFF/rota usam?
I4 Usuários e permissões (Core de PROD, só leitura, pela API do Core ou consulta read-only): para cada
   permissão financial.* e dos três legados, QUANTOS usuários a têm; quantos têm só uma filial; quantos
   têm financial.* mas não têm controllership-finance.access (e o inverso). No repositório só contagens
   — nenhum nome, e-mail ou id de pessoa. A lista nominal vai só no report ao owner, fora do git.
I5 Uso: acessos por rota da financial-api e por página do MFE nos últimos 30 dias (logs do gateway/
   BFF), em PROD; e dos três legados. Se não houver log que permita, dizer INCONCLUSIVE e por quê.
I6 Paridade Despesas por centro de custo (Financeiro) × R10 (Controladoria): mesmo mês fechado
   (2026-10), mesma filial, mesmo filtro — total, por centro de custo e nº de lançamentos; explicar
   cada diferença pela regra (eixo de data, universo, filtros). Ler as duas BFFs como o usuário lê.
I7 Questor: quem é dono hoje da integração (credenciais, cache, rotas S2S); o que quebraria no LNF e na
   Auditoria se a financial-api mudasse ou saísse.
I8 Padrão visual das páginas atuais do Financeiro × padrão do Portal (hero, PagePath, plugin-ui,
   gráficos no padrão do Comercial) — lista do que precisaria mudar por página.

ENTREGA
docs/12-roadmap-e-evolucao/controllership-finance/financial-merge/inventory.md com I1–I8, cada fato
classificado (PROVEN com arquivo:linha/comando · TO_INVENTORY · INCONCLUSIVE com motivo), e uma seção
«Fatos para as decisões D1–D7» com o que cada fato muda em cada decisão. Sem recomendar implementação.

VERIFICAÇÃO
Pedido ao verificador (AGENTS.md § Verificação) com objetivo = M0 I1–I8, escopo = o inventory.md,
alegações = cada fato com a evidência. O verificador confere amostras de arquivo:linha e comandos.
Até 3 rodadas. Veredito sem edição no report.

REGRAS
main sem branch; git add só do inventory.md; nenhum dado pessoal ou financeiro real no repositório
(contagens e totais agregados de paridade podem ir; nomes, CNPJ, valores por cliente não); somente
leitura em PROD (Core, logs, BFFs); nunca imprimir token/segredo. Parar ao concluir.
```
