# Homologação — Wave G / G+ (Portal Comercial)

> UI Overview + Meu dia CRM + shell UnderlineNav + Home hero · **sem F2c**  
> Docs: [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [WIREFRAMES.md](./WIREFRAMES.md) (WF-00 / 01R / 06R)

## Pré-requisitos (gate ops)

- [ ] Manifest registrado no Core (`register-manifest.sh`)
- [ ] Papel **Comercial — Vendedor** criado com codes do doc de perfis
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
| 11 | Conta 360: **Agendar follow-up** pré-preenche cliente no Meu dia | |
| 12 | Meu dia: Adiar + Abrir conta; tipo Ligar/To-do | |
| 13 | Home gestão (admin): KPIs ROL/OTD/conversão + tabela equipe | |
| 14 | Forms billing/admin com plugin-ui | |
| 15 | Visual QA claro/escuro + mobile no shell e Home | |

## Testes automatizados (dev)

| Pacote | Comando | Resultado |
|--------|---------|-----------|
| commercial-api | `pytest tests/test_worklist_*.py tests/test_health.py tests/test_auth_required.py -q` | **11 passed** (06/08/2026) |
| plugin-ui | `npm test -- --run src/components/layout/UnderlineNav.test.tsx` | **2 passed** |
| commercial MFE | `node --test src/features/my-day/myDayDueDate.test.mjs` + `tsc -b` | **ok** |

## Smoke pós-rebuild

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/apps/plugin-ui/assets/remoteEntry.js
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/apps/commercial/assets/remoteEntry.js
curl -sS http://localhost/apps/commercial-api/health
```

**Rebuild Wave G+ P0 (06/08/2026):** `plugin-ui` → `commercial` → `commercial-api` via `up-dev-sequential.sh` — remotes `200`, health `online`, pytest **11 passed**.

## Gaps / backlog explícito

| Gap | Severidade | Nota |
|-----|------------|------|
| F2c / SavedViewChips / purge CSS espelho | Baixa | Fora desta wave |
| Start tasks HubSpot / auto-tasks pedidos | Média | Wave futura |
| Manifest + papel Vendedor | Ops | Gate acima |

## Assinatura

| Papel | Nome | Data | OK |
|-------|------|------|-----|
| Comercial | | | |
| QA / Tech | | | |

F2c **não** aplicado. Matriz: [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md).
