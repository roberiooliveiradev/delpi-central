# Plano — fusão do Portal Financeiro no Portal Controladoria & Finanças

Classificação: `PLANNED`. AS-IS conferido no código (`origin/main` de 16/11/2026); números de uso, usuários e paridade são `TO_INVENTORY` (M0).

## 1. AS-IS (conferido no código)

### 1.1 Portal Financeiro — `plugins/financial` + `financial-api`

| Área (rota) | Permissão hoje | Fonte (via `financial-api`) |
|---|---|---|
| Gestão à vista (`/apps/financial`, `/home`) | `financial.access` | api-delpi `/financial/{rol,ebitda_pct,fixed_cost_pct,pmr}`, `/commercial/rol/*`; strategic-indicators-api (IDD/IGD) |
| Faturamento (`/billing`) | `financial.access` | api-delpi `/commercial/rol/*` |
| Inadimplência (`/delinquency`) | `financial.delinquency.view` | api-delpi `/financeiro/inadimplencia/*` |
| Despesas por centro de custo (`/cost-centers`) | `financial.cost-centers.view` | api-delpi `/financeiro/despesas-centro-custo/*` |
| Frete das compras (`/freight`) | `financial.freight.view` | api-delpi (frete × CT-e) |
| Notas Fiscais (`/invoices`) | `financial.invoices.view` | Questor Zen (NF-e de entrada; DANFE/DACTE/XML) |
| Indicadores (`/indicators`) | `financial.indicators.view` | strategic-indicators-api |
| Exportar Excel | `financial.export` | — |
| Filial | `financial.view.filial-01`, `financial.view.filial-02` | gate por `branch` na BFF |

São **9 permissões** no manifesto (`plugins/financial/financial.manifest.json`). BFF: `financial-api` (`/apps/financial-api`), com rotas de overview, aging, customers, titles, series, ranking de CC e fornecedores, entries, inconsistencies, `received/*` (Questor: lista, detalhe, DANFE, DACTE, XML, XML por chave, export) e `subplugins`.

### 1.2 Plugins legados ainda no repositório

`dashboard-financial` (`dashboard-financial.view`), `financeiro-centro-custo` (`.access/.view/.export`), `financeiro-inadimplencia` (`.access/.view`). O README do Portal Financeiro diz que foram **absorvidos** por ele, mas **não desativados** («decisão operacional futura»). Mais 6 permissões.

### 1.3 Dependência que a fusão não pode quebrar

A `controllership-finance-api` **já consome a `financial-api`** para o Questor:
- LNF: `infrastructure/invoice_posting/financial_received_invoice_gateway.py`, `application/invoice_posting/preflight.py`, `received_nfe_item_service.py`;
- Auditoria de Entradas: `infrastructure/entry_audit/sources.py` (XML por chave).

Também referenciam a `financial-api`: gateway (`nginx.conf`, `nginx.dev.conf`, `hml-proxy-locations.conf`), `infra/docker-compose*.yml`, `shared/delpi_auth` (token S2S), `scripts/ci/test_audit_backend_boundaries.py`, contrato do LNF. Consumidores externos do domínio financeiro: `tv-dashboard-api` (`tv_data_routes.json`), `minha-delpi-ai-api` (catálogo de rotas e KPIs), `api-delpi` (catálogos) — `TO_INVENTORY` se apontam para a `financial-api` ou para a api-delpi direto.

### 1.4 Sobreposições com o que o Portal Controladoria já tem

| Financeiro | Controladoria | Situação |
|---|---|---|
| Despesas por centro de custo | R10 Despesas por Centro de Custo (Fechamento mensal, eixo `D1_DTDIGIT`, CLARA) | mesma pergunta de negócio, motores possivelmente diferentes → paridade `TO_INVENTORY` |
| Notas Fiscais (Questor) | Auditoria de Entradas (XML × Protheus) e LNF (notas recebidas) | mesma fonte; propósitos diferentes |
| Inadimplência / baixas | R01/R02 baixas a pagar e a receber | dados vizinhos (SE1/SE5), perguntas diferentes |
| Indicadores (IDD/IGD) | — | só no Financeiro |

## 2. Alvo (TARGET)

1. Um Portal só: as áreas do Financeiro viram páginas do Portal Controladoria & Finanças, no mesmo padrão visual (hero, PagePath, plugin-ui, padrão de gráficos do Comercial), com um card **Financeiro** no Início.
2. Permissões: só `controllership-finance.access` e `controllership-finance.manage` (regra do Portal). Filial é dimensão de dado, não permissão.
3. MFE consome só a BFF do Portal. Integrações entre contextos por HTTP/contrato.
4. `/apps/financial/*` redireciona para as páginas novas por um período; depois, plugin `financial` e os três legados são desativados (com rollback).
5. A CLARA passa a ler as áreas financeiras pelo mesmo catálogo (sem tool nova), com conhecimento citado.

## 3. Decisões do owner (DECISION_REQUIRED)

| # | Decisão | Opções | Impacto | Recomendação |
|---|---|---|---|---|
| **D1** | **Quem vê o quê** — hoje há 1 acesso + 5 permissões por área + export + 2 por filial | (a) tudo com `controllership-finance.access`; (b) `access` vê e `manage` exporta/administra; (c) manter recorte por área (contraria a regra do Portal) | (a)/(b) **ampliam a audiência**: quem hoje só vê Despesas por CC passa a ver Inadimplência, Faturamento etc. | (b), com a lista de usuários do M0 na mão antes de decidir |
| **D2** | **Filial** — hoje `financial.view.filial-01/02` restringem dado | (a) todos com acesso veem as duas filiais; (b) restringir por filial via escopo de dado do Core (sem permission code no Portal) | (a) amplia a audiência por filial; (b) exige contrato de escopo no Core | decidir com o M0 (quantos usuários têm só uma filial) |
| **D3** | **Onde fica o back-end** | (a) `financial-api` continua serviço próprio e a BFF do Portal a consome por HTTP; (b) as rotas migram para a `controllership-finance-api` (como o LNF, ADR-001) e a `financial-api` fica só como integração Questor; (c) tudo migra, inclusive o Questor | (a) menor esforço, mas o MFE do Portal teria duas BFFs atrás de uma; (b) uma BFF por Portal, mantendo o Questor onde já é consumido; (c) maior esforço e mexe no LNF e na Auditoria em PROD | (b) — ADR-004 |
| **D4** | **Despesas por centro de custo duplicada** (Financeiro × R10) | (a) uma página só, com o motor do R10; (b) uma página só, com o motor do Financeiro; (c) manter as duas | (a)/(b) exigem paridade provada (M0) | decidir depois da paridade do M0 |
| **D5** | **Notas Fiscais (Questor)** | (a) vira página do card «Notas fiscais» (junto da Auditoria e do LNF); (b) some, coberta por Auditoria/LNF | (b) tira consulta que alguém pode usar | (a) |
| **D6** | **Plugins legados** (`dashboard-financial`, `financeiro-centro-custo`, `financeiro-inadimplencia`) | (a) desativar junto com o `financial`; (b) antes, já no início | quem ainda usa os legados perde o caminho | desativar na fase final, com redirecionamento e uso medido no M0 |
| **D7** | **Indicadores (IDD/IGD)** e **Gestão à vista** | (a) entram no Portal; (b) ficam no Portal Comercial/Estratégico | — | (a), owner confirma |

## 4. Fases

| Fase | Entrega | Gate |
|---|---|---|
| **M0** Inventário (somente leitura) | rotas e contratos da `financial-api`; consumidores (gateway, compose, TV, IA, CF-API); usuários por permissão `financial.*` e legados no Core (contagem, sem dado pessoal no repo); uso (logs de acesso por rota, 30 dias); paridade Despesas por CC × R10 (mesmo mês, mesma filial); dependências do Questor; padrão visual das páginas atuais | relatório + verificador |
| **M1** Decisões | owner decide D1–D7 com o M0; ADR-004 (hospedagem) | owner |
| **M2** Contratos | rotas novas na BFF do Portal (`/financial/*` ou equivalente), DTOs, AuthZ (access/manage), escopo de filial conforme D2; contrato da CLARA (reads/analyze) | verificador + Claude |
| **M3** Back-end | implementação conforme D3, testes, HML | verificador |
| **M4** Front-end | páginas no Portal (card Financeiro no Início), padrão visual e de gráficos do Comercial, ajuda | verificador + medição visual |
| **M5** CLARA | catálogo e conhecimento das áreas financeiras; perguntas de teste | PROD pela CLARA |
| **M6** Corte | PROD com tags de rollback; `/apps/financial/*` → redireciona; aviso aos usuários; permissões atribuídas conforme D1/D2 antes do corte | owner |
| **M7** Desativação | após o período de convivência: tirar `financial` e legados do menu/compose; revogar permissões antigas; arquivar | owner |

Cada fase com o verificador (`delpi-verifier`) antes do commit e do deploy; AC visual só com medição.

## 5. Riscos

- **Ampliação de audiência** (D1/D2) — dado financeiro sensível; decidir com a lista de usuários.
- **Quebrar o Questor do LNF e da Auditoria** em PROD (D3) — a `financial-api` é dependência viva da CF-API.
- **Números diferentes** entre Despesas por CC do Financeiro e o R10 — usuários comparando telas.
- **Consumidores externos** (TV, IA) apontando para rotas que mudam.

## 6. Decisões do owner (16/11/2026)

| # | Decisão | Status |
|---|---|---|
| D1 | As 9 permissões `financial.*` **não** são herdadas: as áreas financeiras ficam sob `controllership-finance.access`; `manage` segue para gestão. Ampliação de audiência aceita pelo owner | DECIDIDO |
| D2 | Todos com acesso veem as duas filiais (sem permissão por filial) | DECIDIDO |
| D3 | As rotas do Financeiro vão para a `controllership-finance-api` (ADR-004) | DECIDIDO — confirmar se a integração Questor fica na `financial-api` |
| D4 | **Duas páginas**, não uma: o R10 é parte do Fechamento mensal; a do Financeiro é acompanhamento diário. Ver §7 | DECIDIDO (revisto) |
| D5 | Notas Fiscais (Questor) no card «Notas fiscais» | a confirmar |
| D6 | `dashboard-financial`, `financeiro-centro-custo` e `financeiro-inadimplencia` seguem no ar; desativar só com autorização do owner, depois da centralização | DECIDIDO |
| D7 | Indicadores e Gestão à vista entram no Portal | DECIDIDO |
| — | Exportar: `access` ou `manage` | a confirmar |
| — | Plugin `financial` (`/apps/financial`): redireciona no corte; desativar só com autorização | a confirmar |

## 7. Despesas por centro de custo — Financeiro × R10 (conferido no código)

Não seguem o mesmo padrão; são motores diferentes na api-delpi e respondem perguntas diferentes:

| | Financeiro (acompanhamento) | R10 (Fechamento mensal) |
|---|---|---|
| Rota api-delpi | `GET /financeiro/despesas-centro-custo/*` | `GET /financeiro/cost-center-expenses` (+ `/export`) |
| Fonte | view `dbo.vw_fin_despesas_centro_custo` (`despesas_centro_custo_sql.py`) | `SD1010` direto + SB1, SA2, CTT (`cost_center_expenses_sql.py`) |
| Eixo de data | `data_emissao` (D1_EMISSAO) | `D1_DTDIGIT` (data de digitação = competência; BR-R10-001) |
| Seleção | view exige centro de custo preenchido; exclusão de MP opcional | seleção oficial: tira benefícios, 13 TES excluídas e MP; o que sai vai para «investigação», com total separado e nunca somado (`list_cost_center_expenses_use_case.py`) |
| Saídas | resumo, série, ranking de CC e fornecedores, lançamentos, filtros | lista com universo cálculo/investigação, findings `POSSIBLE_DIVERGENCE`, export, CLARA |

O doc 126 §4 já registrava: a view é `REUSE_PARTIAL` — «Não transplantar seleção da view» (set/2026 f01: 448 linhas na view; 269 de 353 do R10 cobertas). Consequência para a fusão: as duas páginas ficam, com nomes e ajuda que deixem claro a diferença (eixo de data e seleção), para o usuário não comparar números que não são comparáveis. O M0 mede a diferença em 2026-10 só para documentar a ajuda, não para escolher motor.
