# PLAYBOOK — Portal Suprimentos (Minha DELPI)

> **Status (2026-09-10):** arquitetura/produto congelados e implementação incremental em andamento. **E1–E5 concluídas; E6 C1 funcional concluída; WF-04 em revalidação de DoD.**  
> **Próxima página candidata:** WF-05 Pedidos de Compra, somente após fechamento do WF-04 e autorização explícita do Product Owner.  
> **Nome:** Portal Suprimentos · **id:** `supplies` · **basePath:** `/apps/supplies` · **API:** `supplies-api`

Complementos: [README](./README.md) · [INVENTARIO](./INVENTARIO-ATIVOS.md) · [DESIGN-IA](./DESIGN-IA-SUPRIMENTOS.md) · [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md) · [WIREFRAMES](./WIREFRAMES.md) · ADRs.

---

## 1. Propósito

Hub operacional, analítico e gerencial do domínio de Suprimentos. Não é launcher de links nem segundo dashboard isolado.

```text
experiências legadas / BIs / plugins / Sheets
        ↓
Portal Suprimentos
  → Meu trabalho
  → Compras
  → Fornecedores
  → Produtos/MP
  → Estoques
  → Negociações
  → Gestão
```

### Pilares

1. Minhas atividades — worklist/follow-ups.
2. Compras — SC, PC, entregas/atrasos, importações/alçadas somente quando validadas.
3. Fornecedor 360 — TOTVS + OTD + estado Delpi; Qualidade somente após contrato/autorização definidos.
4. Produto/MP 360 — estoque, ESTSEG, onde usado, fornecedores e preços.
5. Estoques — valor, saldos, segurança, giro e consumo.
6. Negociações — savings e inteligência de preço.
7. Gestão — Overview com KPIs homologados + SI.
8. Administração — mappings, scopes e settings homologados.

---

## 2. Decisões travadas enquanto os ADRs vigentes não forem substituídos

1. Identidade `supplies`, API `supplies-api`, CSS `.dashboard-supplies-portal` — ADR-004.
2. `supplies-api` em Flask — ADR-001 + instrução oficial vigente.
3. MFE fala somente com `supplies-api`; browser não chama `api-delpi` diretamente.
4. JWT identifica/autentica; Core API resolve effective permissions.
5. RBAC usa menor catálogo suficiente; não criar permission por CRUD/tela/botão.
6. Unidade = eixo ortogonal `supplies.unit.filial-{TOTVS}`.
7. AuthZ real = capability + unit scope + resource scope/ownership + business rule.
8. Purchase Requests = C0 coexistência → C1 composição → C2 ownership/jobs → paridade final → C3 cutover.
9. Home ≠ Overview.
10. Identificadores técnicos novos em inglês; UI em PT-BR.
11. `@delpi/plugin-ui` é fonte canônica de componentes reutilizáveis; não copiar CSS/componente do Comercial.
12. Ajuda acompanha cada feature user-facing; etapa de help global é apenas auditoria/consolidação.
13. Sem escrita TOTVS neste roadmap.
14. Sem espelho TOTVS no Postgres.
15. BIs/apps externos precisam de classificação final antes do cutover.
16. O Core atual não possui contrato canônico `/me/routes`; as rotas autorizadas são validadas em `/me/apps` (`apps[].routes`).
17. Uma página user-facing por vez até GATE-FEATURE fechado.

---

## 3. Arquitetura

```text
Portal
  → MFE supplies
    → supplies-api
      → Core /me + /me/apps
      → api-delpi → TOTVS
      → purchase-requests-api (C1 até C2)
      → strategic-indicators-api
      → contextos irmãos autorizados
      → PostgreSQL supplies
```

Boundaries completos: [MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md) e [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md).

---

## 4. Capabilities de produto

Flags de UX não são necessariamente permission codes 1:1.

| Flag | Permission base | Capacidade |
|---|---|---|
| `shell` | `supplies.portal.access` | Home, busca, help, palette, preferências |
| `purchaseRequests` | `supplies.purchase-requests.access` | SC no escopo |
| `purchaseRequestsAll` | `supplies.purchase-requests.view-all` | amplia CC, nunca unidade |
| `purchaseRequestsExport` | `supplies.purchase-requests.export` | export enquanto segregação for necessária |
| `operations` | `supplies.operations.access` | PC, entregas, fornecedor, produto, estoque, ESTSEG, follow-ups/notas |
| `analytics` | `supplies.analytics.access` | Overview, OTD, CPV, giro, savings |
| `administration` | `supplies.administration.manage` | mappings, scopes, settings |

`allowedUnits[]` deriva das effective permissions do Core e não é capability de tela.

---

## 5. Jornadas P0

1. Abrir Home e agir em exceções autorizadas.
2. Consultar Overview/OTD no recorte autorizado.
3. Consultar SC no escopo de CC e exportar somente quando permitido.
4. Consultar Pedidos de Compra e seu detalhe.
5. Consultar Entregas/Atrasos.
6. Consultar Estoque e ESTSEG/consumo.
7. Abrir Fornecedor 360 e Produto/MP 360.
8. Consultar Savings/Negociações.
9. Criar/concluir follow-up quando o recurso referenciado estiver autorizado.
10. Usar Administração dentro do escopo permitido.
11. Abrir Ajuda/Quero→onde em todas as jornadas entregues.

---

## 6. Backlog por prioridade

### P0

- shell/Home — entregue;
- Overview + OTD analytics — entregues;
- SC via C1 — funcional, WF-04 em revalidação de DoD;
- Pedidos de Compra;
- Entregas/Atrasos;
- Estoque;
- Estoque de Segurança;
- Análise de Consumo;
- Fornecedor 360;
- Produto/MP 360;
- Savings/Negociações;
- Minhas Atividades;
- Administração;
- Ajuda sincronizada;
- paridade e cutover controlado.

### P1+

Só entram em plano executável após evidência/aceite próprios: lead time real × cadastrado, price variance, supplier scorecard, concentração, alçadas, importações, slow moving/obsolescência, previsão de atraso, automações externas.

---

## 7. Regra de execução do roadmap

O roadmap é causal, mas **não autoriza execução em lote**.

```text
página atual
→ contrato/BFF
→ UI kit-first
→ AuthZ + estados
→ Help
→ testes + docs + smoke
→ GATE-FEATURE
→ próxima página
```

Etapas futuras no `IMPLEMENTATION-PLAN.md` são fila/dependências até serem promovidas. Ao promover uma página, revalidar código e contratos, criar ledger RQ-* e preencher receita completa `E*.S*` segundo `plan-construction.mdc`.

---

## 8. Sequência macro atualizada

```text
E1–E5 concluídas
→ E6 fechar GATE-FEATURE WF-04 (SC)
→ E7 Pedidos de Compra
→ E8 Detalhe do Pedido
→ E9 Entregas/Atrasos
→ E10 Estoque
→ E11 Estoque de Segurança
→ E12 Análise de Consumo
→ E13 Fornecedores
→ E14 Fornecedor 360
→ E15 OTD Fornecedores
→ E16 Produtos/MP
→ E17 Produto/MP 360
→ E18 Onde Usado / Histórico de Preços conforme página promovida
→ E19 Negociações
→ E20 Indicadores, se mantido como página distinta
→ E21 Minhas Atividades
→ E22 Administração
→ E23 auditoria final de Help/onboarding
→ E24 paridade inicial C1
→ E25 Purchase Requests C2
→ E26 paridade final
→ E27 preparação cutover
→ E28 C3
→ E29 verify-final
```

A numeração é de programa e pode ser renumerada apenas por uma revisão explícita do plano; o princípio imutável é **uma página por vez + C1→C2→paridade→C3**.

---

## 9. Cutover

Target saudável primeiro; redirect por último. Nenhum BI/app legado chega ao GO como `LEGADO_A_VALIDAR`. Estados finais permitidos:

```text
PARIDADE_HOMOLOGADA
MANTER_EXTERNO
DEEP_LINK
FORA_DO_ESCOPO_COM_ACEITE
```

Runbook: [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md).
