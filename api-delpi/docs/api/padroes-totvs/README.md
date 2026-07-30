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
| Cadastro de produto | [cadastro-produto.md](./cadastro-produto.md) | `B1_TPMAT`, `B1_CUSTD`, campos SB1 recorrentes |

---

## Playbooks (detalhe)

Pasta: [`playbooks/`](./playbooks/) — paths antigos em `docs/roadmaps/playbook-*.md` redirecionam para cá.

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

Permanece em `docs/roadmaps/` (fora desta biblioteca): `playbook-api-delpi-console`, `playbook-route-test-coverage-100`, `playbook-contrato-respostas-ia`, `playbook-pac-plan-revisions-jun2026`, `playbook_correcao_lmp_repositorio_settings`.

---

## Mapa código ↔ doc

| Constante / módulo | Seção |
|--------------------|--------|
| `app/domain/totvs/protheus_warehouses.py` | [armazem-custo.md](./armazem-custo.md) |
| `REFUGOS_COST_WAREHOUSE` / `refugos_scope.py` | [armazem-custo.md](./armazem-custo.md) · [cadastro-produto.md](./cadastro-produto.md) |
| `PRIMARY_WAREHOUSE` (estoque de segurança) | [armazem-custo.md](./armazem-custo.md) (alinhar semanticamente) |

Padrão: **novo padrão transversal** → preferir constante em `app/domain/totvs/` + seção nesta pasta + link na doc da rota.

---

## Como contribuir (padrão novo)

Diretriz completa para agentes/PRs: **`.cursor/rules/totvs-product-patterns.mdc`** (§ Quando USAR / Quando ENRIQUECER / Como enriquecer).

Resumo:

1. Seção curta: `padroes-totvs/<tema>.md` com tabela + **o que fazer** / **não fazer**.
2. Detalhe longo: `padroes-totvs/playbooks/playbook-<tema>.md` (+ stub em `docs/roadmaps/` se houver path legado).
3. Constante estável → `app/domain/totvs/` + teste mínimo.
4. Incluir no índice deste `README.md`.
5. Doc da rota nova **só referencia** a seção/playbook — não reescreve o padrão.
6. Regra descoberta num bugfix transversal → enriquecer a lib **no mesmo PR** (não só o fix pontual).

---

## Backlog de padrões (ainda sem seção curta)

- Apontamentos / OP (`SC2`, sufixo mãe `001`, datas `C2_DATRF`) — ver playbooks de produção
- Compras válidas / frete MP — changelog + diretivas
- Datas Protheus `YYYYMMDD` / `YYYYMM` e janelas closed-open
- Motivos de refugo (`CYO` / `BC_MOTIVO`)
- Faixas de eficiência OEE (convenção Delpi)

---

## Checklist rápido (rota nova com SQL TOTVS)

- [ ] Consultei o índice desta biblioteca para o domínio da rota.
- [ ] Valoração em R$? → [armazem-custo.md](./armazem-custo.md) (local `01`, sem `AVG` entre locais).
- [ ] Filtro por site? → [filiais.md](./filiais.md).
- [ ] Exclusão de produto / cadastro? → [cadastro-produto.md](./cadastro-produto.md).
- [ ] Playbook de domínio existe? → pasta [`playbooks/`](./playbooks/).
- [ ] Doc da rota aponta para a seção/playbook (não copia tabelas inteiras).
