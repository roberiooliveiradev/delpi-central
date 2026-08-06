# Homologação — Wave G (Portal Comercial)

> UI Overview + Meu dia + timeline conta + RBAC por capacidade · **sem F2c**  
> Docs: [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

## Pré-requisitos

- [ ] Manifest registrado no Core (`register-manifest.sh`)
- [ ] Papel **Comercial — Vendedor** criado com codes do doc de perfis
- [ ] Migration `V003__tasks_activities` aplicada (`commercial.schema_migrations`)
- [ ] Rebuild: `plugin-ui` → `commercial` → `commercial-api` (script sequencial)

## Checklist funcional

| # | Caso | Resultado |
|---|------|-----------|
| 1 | PVA ainda no launcher (sem redirect F2c) | |
| 2 | Início mostra AlertQueue + atalhos (≤ 2 cliques até ação) | |
| 3 | Nav: Início, Meu dia (se worklist), Pedidos, Carteira; Carteiras só admin | |
| 4 | Criar papel Vendedor → menu sem Carteiras admin | |
| 5 | `/my-day` lista buckets; criar e concluir tarefa própria | |
| 6 | Sem `worklist.view` → Meu dia oculto / 403 API | |
| 7 | Sem `followups.manage` → 403 em POST task/complete | |
| 8 | Conta detalhe: timeline (vazia = empty state) + deep links | |
| 9 | Tema claro/escuro sem regressão; mobile ≤768 utilizável | |
| 10 | Zero CSS de componente kit no MFE (`delpi-ui-*` só no remote) | |

## Testes automatizados (dev)

| Pacote | Comando | Resultado |
|--------|---------|-----------|
| commercial-api | `pytest tests/test_worklist_use_case.py tests/test_health.py tests/test_auth_required.py -q` | **5 passed** (ago/2026) |
| plugin-ui | `npm test -- --run src/components/feedback/worklistSurface.test.tsx` | **3 passed** |
| commercial MFE | `npm run build` | **ok** |

## Smoke pós-rebuild

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/apps/commercial/assets/remoteEntry.js
curl -sS http://localhost/apps/commercial-api/health
curl -sS http://localhost/apps/pedidos-venda-abertos/assets/remoteEntry.js -o /dev/null -w '%{http_code}\n'
```

Esperado: remote commercial `200`; health commercial-api `online`; PVA remote ainda `200`.

**Executado (ago/2026):** commercial `200` · health `online` · plugin-ui `200` · PVA `200` · tabelas `commercial.tasks` / `commercial.activities` criadas (V003).

**Rebuild sequencial (06/08/2026):** `plugin-ui` → `commercial` → `commercial-api` — remotes `200`, health/ready `online`/`db_ready`, OpenAPI com `/me/worklist` `/tasks` `/activities`, migrations V001–V003, testes API **5 passed**.

## Gaps vs plano (não bloqueiam rebuild; backlog)

| Gap | Severidade | Próximo passo |
|-----|------------|---------------|
| Home gestão (KPI ROL/OTD / equipe) | Média | Wave G+ — cards leves api-delpi |
| Testes HTTP 403 worklist/followups | Média | `tests/test_worklist_routes_rbac.py` |
| Wireframes ASCII WF-01R…05R, 11–12 | Baixa | Doc; IA já em DESIGN-IA |
| Overrides `.delpi-ui-*` no MFE (legado F2b) | Baixa | Ondas plugin-ui Fase 7 |
| Manifest no Core + papel Vendedor | Ops | `register-manifest.sh` + Minha Delpi |

## Assinatura

| Papel | Nome | Data | OK |
|-------|------|------|-----|
| Comercial | | | |
| QA / Tech | | | |

**Observações:** Rebuild sequencial `plugin-ui` → `commercial` → `commercial-api`. F2c **não** aplicado. Matriz completa: [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) § Wave G.