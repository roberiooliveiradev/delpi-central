# Biblioteca de padrões TOTVS — produto Delpi

Convenções de **negócio** da Delpi no Protheus (SQL Server), usadas por rotas da **api-delpi**, dashboards e alinhamento com Power BI.

Esta pasta é a **biblioteca canônica** de padrões do produto. Cresce por seção (um arquivo por tema).

| Camada | Documento | Conteúdo |
|--------|-----------|----------|
| **Negócio / SQL de domínio** | **Esta biblioteca** (`padroes-totvs/`) | Armazém, filial, custo, cadastro, unidades, anti-padrões |
| **Infra / Docker / datasource** | [integracao-totvs.md](../../../../docs/07-api-delpi/integracao-totvs.md) | Compose, variáveis `TOTVS_*`, papel da api-delpi |
| **Playbooks longos** | `api-delpi/docs/roadmaps/` | Detalhe profundo (ex.: conversão de unidades) — linkados daqui, não duplicados |

Código transversal: `api-delpi/app/domain/totvs/`.  
Regras Cursor: `totvs-product-patterns.mdc` (hub) · `totvs-warehouse-cost-standards.mdc` (armazém/custo).

---

## Índice de seções

| Seção | Arquivo | Quando consultar |
|-------|---------|------------------|
| Armazém e custo unitário | [armazem-custo.md](./armazem-custo.md) | Valoração em R$ (`B2_CM1`), locais `01`/`99`/`98`/`50` |
| Filiais | [filiais.md](./filiais.md) | SC/ES, RBAC por filial, não confundir com armazém |
| Princípios SQL Protheus | [principios-sql.md](./principios-sql.md) | `D_E_L_E_T_`, NOLOCK, `*010`, bind, joins |
| Unidades de medida | [unidades-medida.md](./unidades-medida.md) | `MI`, BOM, conversões produtivas |
| Cadastro de produto | [cadastro-produto.md](./cadastro-produto.md) | `B1_TPMAT`, `B1_CUSTD`, campos SB1 recorrentes |

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

1. Criar `padroes-totvs/<tema>.md` com tabela + **o que fazer** / **o que não fazer**.
2. Se houver literal de negócio estável → constante em `app/domain/totvs/` + teste mínimo.
3. Incluir a seção neste `README.md` (índice).
4. Se a regra for frequente em PRs → entrada em `development-standards-index.mdc` e/ou regra Cursor dedicada.
5. Doc da rota nova **só referencia** a seção — não reescreve o padrão.

---

## Backlog de padrões (ainda sem arquivo)

Temas candidatos a virar seção quando estabilizarem:

- Apontamentos / OP (`SC2`, sufixo mãe `001`, datas `C2_DATRF`)
- Compras válidas / frete MP
- Datas Protheus `YYYYMMDD` / `YYYYMM` e janelas closed-open
- Motivos de refugo (`CYO` / `BC_MOTIVO`)
- Faixas de eficiência OEE (convenção Delpi)

---

## Checklist rápido (rota nova com SQL TOTVS)

- [ ] Consultei o índice desta biblioteca para o domínio da rota.
- [ ] Valoração em R$? → [armazem-custo.md](./armazem-custo.md) (local `01`, sem `AVG` entre locais).
- [ ] Filtro por site? → [filiais.md](./filiais.md).
- [ ] Exclusão de produto / cadastro? → [cadastro-produto.md](./cadastro-produto.md).
- [ ] Doc da rota aponta para a seção (não copia tabelas inteiras).
