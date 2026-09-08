# Portal Suprimentos — documentação mestra

> **Status (set/2026):** baseline de produto e arquitetura concluída · **implementação produtiva não iniciada**  
> **Readiness:** **BLOQUEADO PARA IMPLEMENTAÇÃO até conclusão de E1 + gates P0**  
> **Nome ao usuário:** **Portal Suprimentos**  
> **Id técnico:** `supplies` · **basePath:** `/apps/supplies`  
> **API:** `supplies-api` · gateway `/apps/supplies-api/`  
> **Classe CSS root:** `.dashboard-supplies-portal`

O Portal Suprimentos é o hub operacional, analítico e gerencial do domínio de Suprimentos na Minha DELPI. Substitui progressivamente a experiência fragmentada por jornadas coesas, preservando bounded contexts, RBAC central, paridade e rollback.

**Esta pasta é contrato de produto/arquitetura. Não autoriza implementação, cutover ou remoção de legados sem pedido explícito do Product Owner.**

---

## 1. Readiness atual

| Item | Estado |
|---|---|
| Baseline de produto | concluída |
| Arquitetura alvo | concluída |
| RBAC alvo | revisado; menor catálogo suficiente (ADR-007) |
| Authz Core-first | decisão congelada; implementação compartilhada ainda precisa de gate |
| Framework supplies-api | Flask pela precedência das instruções oficiais |
| BIs externos | pendentes de dump Core E1.S1 |
| Papéis SC/ES | comprador ES ainda pendente E1.S2 |
| KPIs | parte ainda requer homologação E1.S3 |
| Manifest draft | obrigatório antes do scaffold |
| Implementação | não iniciada |

### Bloqueios P0 antes de E2

- **GATE-AUTHZ:** permissions efetivas resolvidas pelo Core; nenhuma autorização nova confia em claims de permission do JWT.
- **GATE-E1:** dump dos BIs externos, papéis e fichas KPI pendentes.
- **GATE-ARCH:** ADRs e manifest draft revisados/aceitos.
- **GATE-RBAC:** catálogo mínimo + provisionamento de coexistência definido.

---

## 2. Identidade congelada

| Superfície | Valor |
|---|---|
| Plugin id | `supplies` |
| basePath MFE | `/apps/supplies` |
| API | `supplies-api` · `/apps/supplies-api` |
| Framework API | **Flask** conforme instrução oficial vigente |
| CSS root | `.dashboard-supplies-portal` |
| Prefixo tokens | `--sp-*` → `--delpi-ui-*` |
| Permission de entrada | `supplies.portal.access` |

ADRs principais: [ADR-001](./adr/ADR-001-supplies-api.md) · [ADR-004](./adr/ADR-004-plugin-identity-and-css-root.md) · [ADR-006](./adr/ADR-006-unit-permissions.md) · [ADR-007](./adr/ADR-007-permission-minimization.md).

---

## 3. Arquitetura alvo

```text
Browser
  → Minha DELPI Portal
    → plugins/supplies
      → supplies-api
          ├── Core API /me (effective permissions)
          ├── PostgreSQL próprio (estado Minha DELPI)
          ├── purchase-requests-api (C1, até absorção C2)
          ├── strategic-indicators-api
          ├── contextos irmãos quando autorizado
          └── api-delpi → TOTVS
```

Regras:

- MFE nunca chama api-delpi direto;
- JWT identifica/autentica; Core resolve permissions efetivas;
- autorização = capability + unidade + resource scope/ownership + business rule;
- SQL/regra TOTVS permanecem na api-delpi;
- estado do produto pertence à supplies-api;
- capabilities não devem espelhar CRUD.

---

## 4. Documentos

| Documento | Conteúdo |
|---|---|
| [00-DIAGNOSTICO.md](./00-DIAGNOSTICO.md) | cenário atual e dores |
| [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) | ativos e decisões |
| [PERSONA-EXPERIENCE-MAP.md](./PERSONA-EXPERIENCE-MAP.md) | personas × apps × permissions |
| [DUPLICIDADES-E-SOBREPOSICOES.md](./DUPLICIDADES-E-SOBREPOSICOES.md) | overlaps e drifts |
| [MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md) | ownership |
| [PLAYBOOK-MODULO-SUPRIMENTOS.md](./PLAYBOOK-MODULO-SUPRIMENTOS.md) | playbook mestre |
| [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md) | fronteira BFF × TOTVS |
| [DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md) | IA/UX |
| [WIREFRAMES.md](./WIREFRAMES.md) | wireframes |
| [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) | RBAC mínimo + unidade + aliases |
| [MANIFEST-DRAFT.md](./MANIFEST-DRAFT.md) | contrato futuro do plugin |
| [API-ROUTES.md](./API-ROUTES.md) | contratos BFF |
| [DATA-MODEL.md](./DATA-MODEL.md) | estado Postgres |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | indicadores |
| [INTEGRACOES.md](./INTEGRACOES.md) | HTTP, authz, observabilidade |
| [HELP-AND-ONBOARDING.md](./HELP-AND-ONBOARDING.md) | Ajuda |
| [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) | plano executável; deve obedecer C1→C2→C3 |
| [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) | paridade mensurável |
| [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md) | target-first, redirect-last |
| [DECISOES_FUNCIONAIS_PENDENTES.md](./DECISOES_FUNCIONAIS_PENDENTES.md) | pendências reais |

### ADRs

| ADR | Decisão |
|---|---|
| ADR-001 | supplies-api, Flask, authz Core-first |
| ADR-002 | absorção progressiva purchase-requests-api C0→C3 |
| ADR-003 | coexistência/cutover |
| ADR-004 | identidade do plugin/CSS |
| ADR-005 | BIs externos precisam de dump Core |
| ADR-006 | unidade ortogonal |
| ADR-007 | minimização de permissions |

---

## 5. Decisões travadas

1. `supplies` + `supplies-api` + `/apps/supplies`.
2. supplies-api em Flask enquanto a instrução oficial vigente assim determinar.
3. MFE fala apenas com supplies-api.
4. Authz real usa effective permissions do Core; não claims de permission do JWT.
5. RBAC usa **menor catálogo suficiente**, não CRUD por permission.
6. Unidade é eixo ortogonal `supplies.unit.filial-{TOTVS}`.
7. `purchase-requests-api`: C0 coexistência → C1 composição → C2 ownership/jobs → paridade final → C3 cutover.
8. Home ≠ Overview.
9. Kit-first e CSS isolado.
10. Cutover só após paridade e BIs externos classificados.

---

## 6. Gates

| Gate | Critério |
|---|---|
| **GATE-AUTHZ** | Core-first; fail-closed na fronteira; não copiar `flask_auth.py` nem fallback FastAPI; testes positivo/negativo/filial |
| **GATE-E1** | BIs + papéis + KPIs fechados ou explicitamente bloqueados |
| **GATE-ARCH** | ADRs + Manifest Draft revisados |
| **GATE-RBAC** | permissions canônicas + migração de papéis + `/me/apps`/`/me/routes` planejados |
| **GATE-API** | supplies-api saudável e MFE sem api-delpi direto |
| **GATE-MFE** | shell kit-first e CSS isolado |
| **GATE-FEATURE** | contrato + authz + Ajuda + testes |
| **GATE-C2** | ownership SC/jobs reconciliado antes de C3 |
| **GATE-PARITY** | dados/funcionalidades comparados com evidência quantitativa |
| **GATE-CUTOVER** | todos os legados/BIs em estado final + target saudável + RBAC + rollback |

---

## 7. Fora de escopo nesta documentação

- implementação produtiva;
- escrita no TOTVS;
- remoção de legados;
- ativação de redirects;
- mudança de RBAC real;
- migrations produtivas.
