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
| CRM TOTVS (SIGATEC) | [crm-sigatec.md](./crm-sigatec.md) | OV `AD1`, funil `AC1`/`AC2`/`AIJ`, proposta `ADY`/`ADZ`; catálogo completo no playbook |
| Materiais de terceiros / SB6 | [materiais-terceiros-sb6.md](./materiais-terceiros-sb6.md) | Remessa/retorno `B6_PODER3`, chave sem `B6_TPCF`, saldo atual |
| Tempo padrão / eficiência | [apontamentos-tempo-padrao.md](./apontamentos-tempo-padrao.md) | `HY_TEMPAD` vs `HY_TEMPOM`; KPI OEE/SI/EF compartilham a mesma expressão |
| Pedido de venda — criador | [pedido-venda-criador.md](./pedido-venda-criador.md) | SC5 sem usuário criador resolvível; `C5_MSUIDT` = UUID técnico |
| Pedido de venda — postergação | [pedido-venda-postergacao.md](./pedido-venda-postergacao.md) | Sem campo TOTVS; heurística BFF `availability` (entrega após o mês) |
| Transportadoras | [transportadora.md](./transportadora.md) | `SA4` / `A4_NREDUZ` na emissão de NF |

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
| [playbook-crm-totvs-dicionario.md](./playbooks/playbook-crm-totvs-dicionario.md) | Dicionário CRM TOTVS — tabelas, SX3, SIX, SX9 |

Permanece em `docs/roadmaps/` (fora desta biblioteca): `playbook-api-delpi-console`, `playbook-route-test-coverage-100`, `playbook-contrato-respostas-ia`, `playbook-pac-plan-revisions-jun2026`, `playbook_correcao_lmp_repositorio_settings`.

---

## Mapa código ↔ doc

| Constante / módulo | Seção |
|--------------------|--------|
| `app/domain/totvs/protheus_warehouses.py` | [armazem-custo.md](./armazem-custo.md) |
| `app/domain/totvs/protheus_product_types.py` | [cadastro-produto.md](./cadastro-produto.md) · OTD PC MP |
| `app/domain/totvs/protheus_third_party_materials.py` | [materiais-terceiros-sb6.md](./materiais-terceiros-sb6.md) |
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

- Apontamentos / OP (`SC2`, sufixo mãe `001`, datas `C2_DATRF`) — ver playbooks de produção; tempo padrão → [apontamentos-tempo-padrao.md](./apontamentos-tempo-padrao.md)
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
