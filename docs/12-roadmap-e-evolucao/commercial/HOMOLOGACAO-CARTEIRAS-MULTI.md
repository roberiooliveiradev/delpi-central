# Homologação — carteiras multi-membro (E1–E6)

> Smoke pós-`V005` + UI lista/detalhe/org + escopo união + mercado E6.  
> Docs: [WIREFRAMES.md](./WIREFRAMES.md) WF-05R · [DATA-MODEL.md](./DATA-MODEL.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)

## Pré-requisitos (gate ops)

- [ ] Migration `V005__seller_portfolio_members` aplicada (`commercial.schema_migrations`)
- [ ] `COMMERCIAL_PORTFOLIO_SOURCE=commercial` (Compose / api-delpi)
- [ ] Rebuild sequencial: `plugin-ui` → `commercial` → `commercial-api` (ver `infra/scripts/up-*-sequential.sh`)
- [ ] Papéis: Admin (`seller-portfolios.manage`) e Vendedor / Gestor (`team.view` sem `manage`)

## Suites automatizadas (E5.2)

Rodar a partir da raiz do monorepo:

```bash
# commercial-api — membership, rotas, worklist, realtime
./.venv/bin/python -m pytest commercial-api/tests/test_portfolio_*.py \
  commercial-api/tests/test_seller_portfolio_routes.py \
  commercial-api/tests/test_worklist_*.py \
  commercial-api/tests/test_commercial_realtime*.py -q

# api-delpi — união/dedupe + dual-read
./api-delpi/.venv/bin/python -m pytest api-delpi/tests/test_seller_portfolio_use_cases.py \
  api-delpi/tests/test_dual_read_seller_portfolio_repository.py -q

# MFE commercial — deep link, rotas, estrutural lista/org
(cd plugins/commercial && npm test)
```

| Pacote | Foco | Resultado E5.2 |
|--------|------|----------------|
| commercial-api | members, owner, `/me` portfolios, worklist, realtime | ☑ suites verdes |
| api-delpi | `ResolvePortfolioScope` união+dedupe; dual-read `list_by_user_id` | ☑ suites verdes |
| plugins/commercial | deep link `/:id`, org `view`/`axis`, escopo | ☑ 171 testes |

## Checklist funcional — P0

| # | Caso | Resultado |
|---|------|-----------|
| 1 | Nav: **Meus pedidos**; **Minha Carteira** só com membership ou team/manage; **Carteiras** só com `manage` | |
| 1b | Papel tipo João (accounts+worklist+analytics+proposals+audit+followups, **sem** manage/team, **sem** membership): sem Carteiras; sem Minha Carteira; sem «Todas as carteiras» de equipe | |
| 1c | `api-delpi.access` / PVA.admin **não** elevam mais `is_admin` nem unrestricted | |
| 2 | Chip Escopo: 1 carteira → `Carteira: {nome}`; N → `{N} carteiras` (só identidade) | |
| 3 | Filtro Carteira: team/manage → «Todas as carteiras»; multi-própria → «Todas as minhas carteiras» | |
| 4 | `team.view` sem `manage`: vê todas no filtro; tela `/seller-portfolios` oculta / 404 | |
| 5 | Lista Carteiras full-page (sem split); clique → `/seller-portfolios/{id}` | |
| 6 | Legado `?id=` na lista redireciona para path de detalhe | |
| 7 | Detalhe: seção Usuários — add/remove membro; **Tornar responsável**; picker só `app=commercial` | |
| 8 | Criar carteira com **vários** usuários (`user_ids`); exatamente um owner | |
| 9 | Toggle **Lista \| Organização**; eixo **Por carteira \| Por pessoa**; URL `view`/`axis` | |
| 10 | Usuário em 2+ carteiras ativas: «Todas» deduplica cliente (código+loja) | |
| 11 | Inativar carteira com membros: regra API (sem órfãos indevidos / feedback UI) | |

## Checklist funcional — P1 (smoke ops)

| # | Caso | Resultado |
|---|------|-----------|
| 12 | Transferência de clientes entre carteiras ainda funciona | |
| 13 | Worklist / realtime resolvem display e equipe via **members** (não só `user_id` pai) | |
| 14 | Cutover: com `source=commercial`, escopo não cai no legado vazio | |
| 15 | Tema claro/escuro + mobile na lista/detalhe/org | |

## Checklist E6 (mercado)

| # | Caso | Resultado |
|---|------|-----------|
| 16 | Chip **Com overlapping** filtra carteiras; badge na lista | |
| 17 | Chip **Sem cobertura** (`?filter=uncovered`) lista clientes com pedido aberto fora de qualquer carteira | |
| 17 | Vincular cliente já em outra carteira: vínculo OK + aviso soft | |
| 18 | Lista/org mostram carga (clientes/membros); valor/atenção «—» se stub | |
| 19 | Detalhe: seção Histórico com eventos de members/owner/transfer | |
| 19b | **Minha Carteira:** Histórico da carteira (membro; HTTP 200); estranho → 403 | |
| 19c | Mutação em um browser → outro membro recebe toast `portfolio.changed` sem F5; admin refetch lista/detalhe | |
| 20 | Minha Carteira / Conta: badge **Compartilhado** + «Também em» | |
| 21 | Wizard transfer em massa + **Exportar matriz** Excel | |

## Assinatura

| Papel | Nome | Data | OK |
|-------|------|------|----|
| Comercial | | | |
| QA / Ops | | | |
