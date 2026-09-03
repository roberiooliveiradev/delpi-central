# Biblioteca de padrões TOTVS — produto Delpi

Convenções de **negócio** da Delpi no Protheus (SQL Server), usadas por rotas da **api-delpi**, dashboards e alinhamento com Power BI.

Esta pasta é a **biblioteca canônica** de padrões do produto. Inclui seções curtas (consulta rápida) e **playbooks** (detalhe de implementação).

| Camada | Documento | Conteúdo |
|--------|-----------|----------|
| **Negócio / SQL de domínio** | **Esta biblioteca** (`padroes-totvs/`) | Armazém, filial, custo, cadastro, unidades + playbooks |
| **Infra / Docker / datasource** | [integracao-totvs.md](../../../../docs/07-api-delpi/integracao-totvs.md) | Compose, variáveis `TOTVS_*`, papel da api-delpi |
| **Ops / CI / console** | `api-delpi/docs/roadmaps/` | Coverage HTTP, console API, PAC, LMP settings (não domínio produto) |

Código transversal: `api-delpi/app/domain/totvs/`.  
Regras Cursor: **`totvs-product-patterns.mdc`** (quando **usar** e como **enriquecer**) · `totvs-warehouse-cost-standards.mdc` (armazém/custo).

---

## Índice de seções (consulta rápida)

| Seção | Arquivo | Quando consultar |
|-------|---------|------------------|
| Armazém e custo unitário | [armazem-custo.md](./armazem-custo.md) | Valoração em R$ (`B2_CM1`), locais `01`/`99`/`98`/`50` |
| Filiais | [filiais.md](./filiais.md) | SC/ES, RBAC por filial, não confundir com armazém |
| Princípios SQL Protheus | [principios-sql.md](./principios-sql.md) | `D_E_L_E_T_`, NOLOCK, `*010`, bind, joins |
| Unidades de medida | [unidades-medida.md](./unidades-medida.md) | `MI`, BOM — resumo; detalhe no playbook |
| Cadastro de produto | [cadastro-produto.md](./cadastro-produto.md) | `B1_TPMAT`, `B1_CUSTD`, `B1_REFEREN`, campos SB1 recorrentes |
| Cadastro de cliente (SA1) | [cadastro-cliente.md](./cadastro-cliente.md) | `A1_NREDUZ` vs `A1_NOME`, bloqueio, loja `1`/`01`, busca carteira |
| CRM TOTVS (SIGATEC) | [crm-sigatec.md](./crm-sigatec.md) | Censo vivo + OV `AD1`, funis 000001/000002/000003, `AIJ`/`ADY`; colunas no playbook |
| Materiais de terceiros / SB6 | [materiais-terceiros-sb6.md](./materiais-terceiros-sb6.md) | Remessa/retorno `B6_PODER3`, chave sem `B6_TPCF`, saldo atual |
| Tempo padrão / eficiência | [apontamentos-tempo-padrao.md](./apontamentos-tempo-padrao.md) | `HY_TEMPAD` vs `HY_TEMPOM`; KPI OEE/SI/EF compartilham a mesma expressão |
| Produção — entrada em estoque | [producao-entrada-estoque.md](./producao-entrada-estoque.md) | Última operação do roteiro do PA (`SG2`) vs inspeção / `SD3` PR0 |
| Chave da OP e alocação SH8 | [ordem-producao-chave.md](./ordem-producao-chave.md) | `C2_OP` 11 posições, OP mãe `001`, `H8_FERRAM`, `H8_QUANT` não é quantidade |
| Apontamento de operação HZA | [apontamento-operacao-hza.md](./apontamento-operacao-hza.md) | `HZA010`, "em produção agora" vs status aberto, operador em `SYS_USR` |
| Pedido de venda — criador | [pedido-venda-criador.md](./pedido-venda-criador.md) | SC5 sem usuário criador resolvível; `C5_MSUIDT` = UUID técnico |
| Pedido de venda — postergação | [pedido-venda-postergacao.md](./pedido-venda-postergacao.md) | Sem campo TOTVS; heurística BFF `availability` (entrega após o mês) |
| Transportadoras | [transportadora.md](./transportadora.md) | `SA4` / `A4_NREDUZ` na emissão de NF |
| ROL financeiro (receita líquida) | — | Campo HTTP canônico **`rol`** = vendas − devoluções (`VLR_VENDA − VLR_DEVOLUCAO`); identificador legado `rol_with_ipi` removido (breaking). Expressão reutilizável: `CommercialRolReturnSql` em `app/domain/services/commercial/commercial_rol_return_sql.py` (billing líquido da carteira / série `nature=net`). Bruto de NF = `F2_VALBRUT`; bruto no envelope by-customer = `gross_revenue`. |
| ROL — mercado interno/externo | [rol-mercado-cfop.md](./rol-mercado-cfop.md) | CFOP `5`/`6` = interno; `7` = exportação; países via `A1_PAIS` |

---

## Playbooks (detalhe)

Pasta: [`playbooks/`](./playbooks/).

| Playbook | Tema |
|----------|------|
| [playbook-conversao-unidades-protheus.md](./playbooks/playbook-conversao-unidades-protheus.md) | MI / milheiro, BOM, fiscal, impacto nas rotas |
| [playbook-estrutura-produto-exclusividade-mp.md](./playbooks/playbook-estrutura-produto-exclusividade-mp.md) | Estrutura / exclusividade MP |
| [playbook-catalogo-exclusividade-mp.md](./playbooks/playbook-catalogo-exclusividade-mp.md) | Catálogo MP exclusiva × PA |
| [playbook-simulador-impacto-custos-pa.md](./playbooks/playbook-simulador-impacto-custos-pa.md) | Simulador de custo PA |
| [playbook-analise-preco-materia-prima.md](./playbooks/playbook-analise-preco-materia-prima.md) | Análise de preço de MP |
| [playbook-diretivas-produto.md](./playbooks/playbook-diretivas-produto.md) | Diretivas de produto / compras |
| [playbook-situacao-de-producao-pa.md](./playbooks/playbook-situacao-de-producao-pa.md) | Situação de produção PA |
| [playbook-visaostatus-produto.md](./playbooks/playbook-visaostatus-produto.md) | Visão status produto |
| [playbook-producao-consumo-compras-perdas-op.md](./playbooks/playbook-producao-consumo-compras-perdas-op.md) | Produção, consumo, compras, perdas, OP |
| [playbook-pa-inspecao-expedicao.md](./playbooks/playbook-pa-inspecao-expedicao.md) | PA inspeção / expedição |
| [playbook-correcao-estoque-supplies-inventario.md](./playbooks/playbook-correcao-estoque-supplies-inventario.md) | Correção estoque supplies × inventário |
| [playbook-crm-totvs-dicionario.md](./playbooks/playbook-crm-totvs-dicionario.md) | SX3/SIX/SX9; volumes e funis em [crm-sigatec.md](./crm-sigatec.md) |

Permanece em `docs/roadmaps/` (fora desta biblioteca): `playbook-api-delpi-console`, `playbook-route-test-coverage-100`, `playbook-contrato-respostas-ia`, `playbook-pac-plan-revisions-jun2026`, `playbook_correcao_lmp_repositorio_settings`.

---

## Mapa código ↔ doc

| Constante / módulo | Seção |
|--------------------|--------|
| `app/domain/totvs/protheus_warehouses.py` | [armazem-custo.md](./armazem-custo.md) |
| `app/domain/totvs/protheus_product_types.py` | [cadastro-produto.md](./cadastro-produto.md) · OTD PC MP |
| `production_appointments_scope.PA_STOCK_ENTRY_PRODUCT_TYPE` | [producao-entrada-estoque.md](./producao-entrada-estoque.md) |
| `app/domain/totvs/protheus_third_party_materials.py` | [materiais-terceiros-sb6.md](./materiais-terceiros-sb6.md) |
| `app/domain/totvs/protheus_production_orders.py` | [ordem-producao-chave.md](./ordem-producao-chave.md) |
| `app/domain/totvs/protheus_operation_appointments.py` · `protheus_users.py` | [apontamento-operacao-hza.md](./apontamento-operacao-hza.md) |
| `REFUGOS_COST_WAREHOUSE` / `refugos_scope.py` | [armazem-custo.md](./armazem-custo.md) · [cadastro-produto.md](./cadastro-produto.md) |
| `PRIMARY_WAREHOUSE` (estoque de segurança) | [armazem-custo.md](./armazem-custo.md) (alinhar semanticamente) |
| `production_meta_por_hora` / `production_tempo_previsto` | [apontamentos-tempo-padrao.md](./apontamentos-tempo-padrao.md) |

Padrão: **novo padrão transversal** → preferir constante em `app/domain/totvs/` + seção nesta pasta + link na doc da rota.

---

## Como contribuir (padrão novo)

Diretriz completa para agentes/PRs: **`.cursor/rules/totvs-product-patterns.mdc`** (§ Quando USAR / Quando ENRIQUECER / Como enriquecer).

Resumo:

1. Seção curta: `padroes-totvs/<tema>.md` com tabela + **o que fazer** / **não fazer**.
2. Detalhe longo: `padroes-totvs/playbooks/playbook-<tema>.md`.
3. Constante estável → `app/domain/totvs/` + teste mínimo.
4. Incluir no índice deste `README.md`.
5. Doc da rota nova **só referencia** a seção/playbook — não reescreve o padrão.
6. Regra descoberta num bugfix transversal → enriquecer a lib **no mesmo PR** (não só o fix pontual).

---

## Backlog de padrões (ainda sem seção curta)

- Datas de OP (`C2_DATRF`, `C2_DATPRF`) — ver playbooks de produção; chave e sufixo mãe já cobertos em [ordem-producao-chave.md](./ordem-producao-chave.md); tempo padrão → [apontamentos-tempo-padrao.md](./apontamentos-tempo-padrao.md)
- Compras válidas / frete MP — changelog + diretivas
- Datas Protheus `YYYYMMDD` / `YYYYMM` e janelas closed-open
- Motivos de refugo (`CYO` / `BC_MOTIVO`)
- Faixas de eficiência OEE — ver [regras-faixa-eficiencia-producao.md](../regras-faixa-eficiencia-producao.md) (já documentado; não é backlog de fórmula)


---

## Checklist rápido (rota nova com SQL TOTVS)

- [ ] Consultei o índice desta biblioteca para o domínio da rota.
- [ ] Valoração em R$? → [armazem-custo.md](./armazem-custo.md) (local `01`, sem `AVG` entre locais).
- [ ] Filtro por site? → [filiais.md](./filiais.md).
- [ ] Exclusão de produto / cadastro? → [cadastro-produto.md](./cadastro-produto.md).
- [ ] Playbook de domínio existe? → pasta [`playbooks/`](./playbooks/).
- [ ] Doc da rota aponta para a seção/playbook (não copia tabelas inteiras).
