# Portal Suprimentos — documentação mestra

> **Status (set/2026):** documentação e plano **concluídos** · **implementação produtiva não iniciada**  
> **Nome ao usuário:** **Portal Suprimentos**  
> **Id técnico:** `supplies` · **basePath:** `/apps/supplies`  
> **API:** `supplies-api` · gateway `/apps/supplies-api/`  
> **Classe CSS root:** `.dashboard-supplies-portal` (não colidir com o legado `.dashboard-supplies`)

O **Portal Suprimentos** é o hub operacional, analítico e gerencial do domínio de Suprimentos na Minha DELPI. Substitui progressivamente a experiência fragmentada (vários BIs, plugins, Sheets e filtros diferentes) por jornadas coesas, no mesmo padrão arquitetural e visual do [Portal Comercial](../commercial/README.md).

**Esta pasta é contrato de produto e arquitetura.** Não autoriza cutover, remoção de plugins nem implementação sem pedido explícito do Product Owner.

## Identidade congelada

| Superfície | Valor | Colisão? |
|------------|-------|----------|
| Plugin id | `supplies` | Só fixture de teste (`rbacAccessTree.test.ts`) — **não** há app real |
| basePath MFE | `/apps/supplies` | Livre |
| API | `supplies-api` · `/apps/supplies-api` | Livre (pacote inexistente) |
| CSS root | `.dashboard-supplies-portal` | **Obrigatório** — `.dashboard-supplies` já é o MFE legado |
| Prefixo tokens | `--sp-*` → `--delpi-ui-*` | Livre |
| Departamento SI / chat | `supplies` | Reuso intencional do domínio, não do app |

ADRs: [ADR-001](./adr/ADR-001-supplies-api.md) · [ADR-004](./adr/ADR-004-plugin-identity-and-css-root.md)

## Arquitetura alvo

```text
Browser
  → Minha DELPI Portal
    → plugins/supplies  (MFE · nunca chama api-delpi)
      → supplies-api
          ├── PostgreSQL próprio (estado Delpi)
          ├── Core API (RBAC / me / apps)
          ├── purchase-requests-api (HTTP, até absorção)
          ├── strategic-indicators-api (HTTP)
          ├── contexto Qualidade / Financeiro (HTTP, projeção)
          └── api-delpi → TOTVS (SQL canônico)
```

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| **[00-DIAGNOSTICO.md](./00-DIAGNOSTICO.md)** | Como Suprimentos trabalha hoje; dores; gaps |
| **[INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)** | Apps, BIs, APIs, Sheets, decisões Portal |
| **[PERSONA-EXPERIENCE-MAP.md](./PERSONA-EXPERIENCE-MAP.md)** | Persona × filial × app × permissão × alvo |
| **[DUPLICIDADES-E-SOBREPOSICOES.md](./DUPLICIDADES-E-SOBREPOSICOES.md)** | OTD×atraso, estoques, Sheets×SI, onde-usado |
| **[MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md)** | Owner por capacidade |
| **[PLAYBOOK-MODULO-SUPRIMENTOS.md](./PLAYBOOK-MODULO-SUPRIMENTOS.md)** | Playbook mestre |
| **[PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)** | Fronteira TOTVS × BFF |
| **[DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md)** | Arquitetura de informação e kit |
| **[WIREFRAMES.md](./WIREFRAMES.md)** | WF-01–WF-21 |
| **[PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)** | RBAC capability-driven + aliases |
| **[API-ROUTES.md](./API-ROUTES.md)** | Catálogo supplies-api + reuso api-delpi |
| **[DATA-MODEL.md](./DATA-MODEL.md)** | Postgres Delpi (sem espelho TOTVS) |
| **[KPI-FICHAS.md](./KPI-FICHAS.md)** | Fichas dos indicadores centrais |
| **[INTEGRACOES.md](./INTEGRACOES.md)** | Gateways, filiais, observabilidade |
| **[HELP-AND-ONBOARDING.md](./HELP-AND-ONBOARDING.md)** | Manual, FAQ, glossário, satélite Ajuda |
| **[IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md)** | Plano E1–E20 com receita E\*.S\* |
| **[HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md)** | Checklist por ativo legado |
| **[CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md)** | Coexistência → redirect → unregister |
| **[DECISOES_FUNCIONAIS_PENDENTES.md](./DECISOES_FUNCIONAIS_PENDENTES.md)** | Só o que o repositório não resolve |

### ADRs

| ADR | Decisão |
|-----|---------|
| [ADR-001-supplies-api.md](./adr/ADR-001-supplies-api.md) | Criar `supplies-api` como BFF do Portal |
| [ADR-002-purchase-requests-api.md](./adr/ADR-002-purchase-requests-api.md) | Absorção progressiva pela `supplies-api` |
| [ADR-003-legacy-app-consolidation.md](./adr/ADR-003-legacy-app-consolidation.md) | Coexistência e depreciação dos MFEs/BIs |
| [ADR-004-plugin-identity-and-css-root.md](./adr/ADR-004-plugin-identity-and-css-root.md) | `supplies` + CSS `.dashboard-supplies-portal` |
| [ADR-005-external-bi-core-dump.md](./adr/ADR-005-external-bi-core-dump.md) | BIs do PO ausentes do git — validar no Core |
| [ADR-006-unit-permissions.md](./adr/ADR-006-unit-permissions.md) | Unidade ortogonal (`supplies.unit.filial-{TOTVS}`) — não inflar capabilities |

## Decisões travadas (resumo)

1. Plugin `supplies` + `supplies-api` + `/apps/supplies`.
2. MFE **nunca** chama `api-delpi` direto.
3. `purchase-requests-api` **permanece** na coexistência e é **absorvida** após paridade (não fica BC irmão eterno do Portal).
4. SQL TOTVS permanece na **api-delpi**. Estado Delpi (tarefas, notas, alertas, preferências, e depois escopos CC) na **supplies-api**.
5. Home ≠ Visão Geral. Capability-driven, sem `if role == comprador`.
6. Multi-unidade: eixo B `supplies.unit.filial-{TOTVS}` (hoje `01` SC e `02` ES; futuras sem inflar o eixo A). Aliases `filial-sc`/`filial-es` só no legado. `manage` ≠ todas as unidades.
7. Cutover só após paridade homologada. Nenhum app removido nesta etapa.

## Próximos gates (quando o PO autorizar execução)

| Gate | Critério |
|------|----------|
| **GATE-E1** | Dump Core dos BIs externos + fichas KPI assinadas nas pendências |
| **GATE-ARCH** | ADRs aceitos pelo PO |
| **GATE-API** | `supplies-api` no Compose, grep zero `api-delpi` no MFE |
| **GATE-MFE** | Shell kit-first, CSS `.dashboard-supplies-portal` |
| **GATE-FEATURE** | Feature = contrato + RBAC + Ajuda + testes |
| **GATE-PARITY** | Portal ≥ capacidade legada necessária |
| **GATE-CUTOVER** | Redirects + aliases + rollback homologados |

## Fora desta pasta

- Implementação de MFE/API/Compose/Gateway/RBAC/migrations.
- Remoção de `dashboard-supplies`, `purchase-requests`, `estoque-seguranca`.
- Escrita no TOTVS.

## Referências de padrão (não copiar regra comercial)

- [Portal Comercial](../commercial/README.md)
- [Checklist novo MFE](../../05-plugin-system/novo-plugin-mfe-checklist.md)
- [Catálogo plugin-ui](../../../plugins/plugin-ui/docs/component-catalog.md)
- Contrato SC: [solicitacoes-compras/01-contrato-api.md](../solicitacoes-compras/01-contrato-api.md)
- ESTSEG: [api-delpi/docs/api/estoque-seguranca.md](../../../api-delpi/docs/api/estoque-seguranca.md)
