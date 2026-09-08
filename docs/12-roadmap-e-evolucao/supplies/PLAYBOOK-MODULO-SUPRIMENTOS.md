# PLAYBOOK — Portal Suprimentos (Minha DELPI)

> **Status:** baseline oficial de produto/arquitetura · set/2026 · **não implementado**  
> **Readiness:** bloqueado até E1 + gates P0  
> **Nome:** Portal Suprimentos · **id:** `supplies` · **basePath:** `/apps/supplies` · **API:** `supplies-api`

Complementos: [README](./README.md) · [INVENTARIO](./INVENTARIO-ATIVOS.md) · [DESIGN-IA](./DESIGN-IA-SUPRIMENTOS.md) · [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md) · ADRs.

---

## 1. Propósito

Hub operacional, analítico e gerencial do domínio de Suprimentos. Não é launcher de links nem segundo dashboard isolado.

```text
vários BIs + plugins + Sheets + filtros diferentes
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
2. Compras — SC, PC, entregas/atrasos, importações/alçadas quando validadas.
3. Fornecedor 360 — TOTVS + OTD + Qualidade projetada + estado Delpi.
4. Produto/MP 360 — estoque, ESTSEG, onde usado, fornecedores, preços.
5. Estoques — valor, saldos, segurança, giro e consumo.
6. Negociações — savings e inteligência de preço.
7. Gestão — Overview 6–8 KPIs + SI.
8. Administração — mappings, scopes e settings homologados.

---

## 2. Decisões irrevogáveis enquanto os ADRs vigentes não forem substituídos

1. Identidade `supplies`, API `supplies-api`, CSS `.dashboard-supplies-portal` — ADR-004.
2. `supplies-api` em **Flask** pela precedência das instruções oficiais — ADR-001.
3. MFE fala somente com supplies-api.
4. JWT = identidade; **Core API resolve effective permissions**. Não autorizar por claims de permission do JWT.
5. RBAC = **menor catálogo suficiente**, sem permission por CRUD — ADR-007.
6. Unidade = eixo B `supplies.unit.filial-{TOTVS}` — ADR-006.
7. Autorização real = capability + unit scope + resource scope/ownership + business rule.
8. Purchase Requests: C0 coexistência → C1 composição → C2 ownership/jobs → paridade final → C3 cutover.
9. Home ≠ Overview.
10. Identificadores novos em inglês; UI em PT-BR.
11. Kit `@delpi/plugin-ui`; zero CSS que sobrescreva primitivas do kit.
12. Ajuda acompanha feature user-facing.
13. Sem escrita TOTVS neste roadmap.
14. Sem espelho TOTVS no Postgres.
15. BIs evidenciados pelo PO exigem dump Core e destino explícito antes do cutover.

---

## 3. Arquitetura

```text
Portal
  → MFE supplies
    → supplies-api
      → Core /me
      → api-delpi → TOTVS
      → purchase-requests-api (C1)
      → SI
      → contextos irmãos autorizados
      → PG supplies
```

Boundaries completos: [MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md) e [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md).

---

## 4. Capabilities de produto

Flags de UX não são necessariamente permission codes 1:1.

| Flag de produto | Permission base | Telas/capacidade |
|---|---|---|
| `shell` | `supplies.portal.access` | Home, busca, help, palette, preferências |
| `purchaseRequests` | `supplies.purchase-requests.access` | SC no escopo |
| `purchaseRequestsAll` | `supplies.purchase-requests.view-all` | bypass CC, nunca unidade |
| `purchaseRequestsExport` | `supplies.purchase-requests.export` | export enquanto segregação for necessária |
| `operations` | `supplies.operations.access` | PC, entregas, fornecedor, produto, estoque, ESTSEG, follow-ups/notas |
| `analytics` | `supplies.analytics.access` | Overview, OTD gerencial, CPV, giro, savings |
| `administration` | `supplies.administration.manage` | mappings, scopes, settings |

Não criar `tasks.view/write`, `products.view`, `inventory.view`, `supplier-notes.write` etc. apenas porque existe uma rota/ação distinta. Ver ADR-007.

Unidades não são capability de tela: `allowedUnits[]` é derivado de effective permissions do Core.

---

## 5. Jornadas P0

1. Abrir Home e agir em exceções autorizadas.
2. Filtrar unidade dentro de `allowedUnits`.
3. Consultar SC no escopo de CC e exportar somente se cap separada ainda for necessária.
4. Consultar PC/entregas como operação de compras.
5. Abrir Produto/MP 360.
6. Abrir Fornecedor 360.
7. Ver Overview conforme permission analytics.
8. Criar/concluir follow-up somente quando o recurso referenciado estiver autorizado.
9. Abrir Ajuda/Quero→onde.

---

## 6. Regra de autorização fina

Permission não substitui escopo de recurso.

Exemplo de task:

```text
supplies.portal.access
AND capability do recurso referenciado
AND branch ∈ allowedUnits
AND ownership/regra de equipe
→ pode criar/alterar/concluir
```

Exemplo de nota de fornecedor:

```text
supplies.operations.access
AND branch autorizada
AND fornecedor no escopo
→ pode registrar nota operacional
```

Se houver necessidade real de separar leitura/escrita por públicos distintos, abrir decisão específica em vez de inflar preventivamente o catálogo.

---

## 7. Backlog priorizado

### P0

- shell/Home;
- Overview com KPIs homologados;
- paridade SC via C1;
- pedidos/entregas básicos a partir de contratos existentes;
- estoque + ESTSEG;
- Fornecedor 360 leitura + notas operacionais;
- Produto/MP 360;
- worklist/follow-ups;
- Ajuda;
- RBAC multi-unidade e coexistência.

### P1

- lead time real × cadastrado;
- price variance;
- alertas persistidos se latência/caso de uso justificar;
- importações somente após E1;
- cobertura/slow moving após ficha funcional.

### P2

- scorecard composto;
- concentração/fornecedor único;
- alçadas se houver workflow comprovado;
- comparativo fornecedor;
- obsolescência.

### P3

- previsão de atraso;
- follow-up automático externo;
- escrita ESTSEG no Protheus — fora do ADR vigente.

---

## 8. Multi-unidade

`allowedUnits` vem das **permissions efetivas do Core**, não do JWT.

- uma unit → apenas ela;
- várias → união delas;
- branch omitido → união autorizada, nunca empresa inteira;
- administração não concede automaticamente todas as units;
- superadmin segue política canônica do Core e auditoria.

---

## 9. KPIs

Overview: no máximo 6–8 KPIs. Cada card precisa explicitar sua natureza temporal (snapshot, estado atual, intervalo ou competência) e respeitar only-allowedUnits.

Fichas: [KPI-FICHAS.md](./KPI-FICHAS.md).

---

## 10. UX

Família visual do Comercial, sem copiar domínio/componente local já coberto pelo kit. Rotas internas capability-driven. Mobile ≤768px com cards/stacked quando tabela não couber.

---

## 11. Roadmap causal

Sequência macro obrigatória:

```text
E1 descoberta/gates
→ fundação API + authz
→ shell MFE + RBAC coexistência
→ features P0
→ C1 Purchase Requests
→ C2 ownership/jobs de SC
→ paridade final
→ C3 cutover
→ evoluções futuras
→ verify final
```

O `IMPLEMENTATION-PLAN.md` deve refletir essa causalidade também no bloco `dependsOn`.

---

## 12. Cutover

Target saudável primeiro; redirect por último. Nenhum BI pode chegar ao GO em `LEGADO_A_VALIDAR`: deve estar `PARIDADE_HOMOLOGADA`, `MANTER_EXTERNO`, `DEEP_LINK` ou `FORA_DO_ESCOPO_COM_ACEITE`.

Runbook: [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md).
