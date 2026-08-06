# Homologação — Wave G / G+ (Portal Comercial)

> UI Overview + Meu dia CRM + shell UnderlineNav + Home hero/gestão · **sem F2c**  
> Docs: [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md) · [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [WIREFRAMES.md](./WIREFRAMES.md) (WF-00 / 01R / 06R)

## Pré-requisitos (gate ops)

- [ ] Manifest registrado no Core (`plugins/commercial/scripts/register-manifest.sh`)
- [ ] Papel **Comercial — Vendedor** criado com codes do [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)
- [ ] Migration `V003__tasks_activities` aplicada (`commercial.schema_migrations`)
- [ ] Rebuild: `plugin-ui` → `commercial` → `commercial-api` (script sequencial)

## Checklist funcional — P0

| # | Caso | Resultado |
|---|------|-----------|
| 1 | PVA ainda no launcher (sem redirect F2c) | |
| 2 | Shell: **UnderlineNav** (não pills de ActionButton); badge Meu dia = overdue+hoje | |
| 3 | Início: hero saudação + chips + AlertQueue + KPIs operacionais (`allSettled`) | |
| 4 | Nav: Início, Meu dia (se worklist), Pedidos, Carteira; Carteiras só admin | |
| 5 | Criar papel Vendedor → menu sem Carteiras admin | |
| 6 | `/my-day`: form título + **prazo (default hoje)** + prioridade + cliente; Concluir legível no dark | |
| 7 | Sem `worklist.view` → Meu dia oculto / 403 API | |
| 8 | Sem `followups.manage` → 403 em POST task/complete | |
| 9 | Tema claro/escuro; mobile ≤768 (nav com scroll) | |
| 10 | Zero CSS de componente kit no MFE (`delpi-ui-*` só no remote) | |

## Checklist funcional — P1

| # | Caso | Resultado |
|---|------|-----------|
| 11 | Conta 360: **Agendar follow-up** pré-preenche cliente no Meu dia (`?createTask=1&customer_*`) | |
| 12 | Home AlertQueue vazia: CTA **Criar follow-up** abre Meu dia com form em destaque | |
| 13 | Meu dia: **Adiar +1 dia** + **Abrir conta**; tipo Ligar / Follow-up / To-do | |
| 13b | Tasks P1: admin cria com **Responsável**; chips **Minhas/Equipe**; **Reatribuir** | |
| 14 | Home gestão (admin): KPIs ROL / conversão / OTD + tabela equipe (`allSettled`) | |
| 15 | Forms billing / charts / transferência com plugin-ui (`Commercial*`) | |
| 16 | Visual QA claro/escuro + mobile ≤768 no shell e Home | |
| 17 | Gate ops: manifest + papel Vendedor conferidos | |

## Testes automatizados (dev)

| Pacote | Comando | Resultado |
|--------|---------|-----------|
| commercial-api | `pytest tests/test_worklist_*.py tests/test_health.py tests/test_auth_required.py -q` | **13 passed** (06/08/2026 P1) |
| plugin-ui | `npm test -- --run src/components/layout/UnderlineNav.test.tsx` | **2 passed** (P0) |
| commercial MFE | `node --test src/features/my-day/myDayDueDate.test.mjs` + `tsc --noEmit` | **ok** |

## Smoke pós-rebuild

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/apps/plugin-ui/assets/remoteEntry.js
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/apps/commercial/assets/remoteEntry.js
curl -sS http://localhost/apps/commercial-api/health
```

**Rebuild Wave G+ P0 (06/08/2026):** `plugin-ui` → `commercial` → `commercial-api` via `up-dev-sequential.sh` — remotes `200`, health `online`, pytest worklist/RBAC **11 passed**.

**Rebuild Wave G+ P1 (06/08/2026):** mesmo script sequencial — remotes `200`, health `online`, pytest **13 passed** (inclui defer + RBAC).

## Gaps / backlog explícito

| Gap | Severidade | Nota |
|-----|------------|------|
| F2c / SavedViewChips / purge CSS espelho | Baixa | Fora desta wave |
| Observação (`description`) na UI do Meu dia | — | **Feito** P0 (ago/2026) |
| Filtro por tipo + tipos e-mail/visita | — | **Feito** P0 |
| Responsável / reassign multi-user | — | **Feito** P1 (ago/2026): create assignee + `reassign` + `scope=team` |
| Anexos em tarefa | — | **Feito** P2 (ago/2026): `/attachments` + volume |
| Reminder / checklist / recorrência | Baixa (P3) | Paridade CRM |
| Start tasks HubSpot / auto-tasks pedidos | Média | Wave futura (P3) |
| Manifest + papel Vendedor | Ops | Gate acima — checklist item 17 |

**Rebuild Tasks P1 (ago/2026):** `plugin-ui` → `commercial` → `commercial-api` via `up-dev-sequential.sh` — pytest worklist **15 passed**.

UX polish Home/Meu dia (ago/2026) documentado em [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 1 — não bloqueia assinatura Wave G+.

## Assinatura

| Papel | Nome | Data | OK |
|-------|------|------|-----|
| Comercial | | | |
| QA / Tech | | | |

F2c **não** aplicado. Matriz: [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md).
