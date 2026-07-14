# Roadmap — Central de Agendamento

> **Escopo:** plugin `central-agendamento` + rotas `api-delpi/scheduling` + schema `scheduling`

## Fases

| Fase | Status | Entrega |
|------|--------|---------|
| **1** | Concluída | MFE, API CRUD recursos/reservas, migrations V001, compose dev, smoke homolog |
| **2** | Concluída | Compose prod, constraint anti-conflito V002, homolog API fase 2, testes unitários |
| **3.1** | Concluída | Aprovação prévia (`requires_approval`), `approve.filial-*`, hold até `start_at`, notificações, fila MFE |
| **3** | Planejada | Reagendar reserva, seed demo por filial, aprovação de série recorrente |

## Checklist produção

- [x] Serviço `central-agendamento` em `infra/docker-compose.yml`
- [x] `gateway.depends_on` inclui `central-agendamento`
- [x] Build CI: `./scripts/ci/build-central-agendamento.sh`
- [x] Smoke: `./scripts/homologacao/check-central-agendamento.sh`
- [x] API E2E: `./scripts/homologacao/check-scheduling-api.sh` (requer `TOKEN` com permissão manage)
- [ ] Registro Core API + RBAC (`register-manifest.sh`) — reexecutar para registrar `approve.*`
- [ ] Migration em prod: `run_plugins_migrations.py --plugin scheduling` (inclui V004)
- [ ] Atribuir `approve.filial-*` nos papéis aprovadores (combinar com `view`)

## Comandos úteis

```bash
# Dev — da raiz do repositório
docker compose -f infra/docker-compose.dev.yml up --build -d api-delpi central-agendamento

# Migrations
docker compose -f infra/docker-compose.dev.yml exec api-delpi \
  python scripts/run_plugins_migrations.py up --plugin scheduling

# Build plugin
./scripts/ci/build-central-agendamento.sh
```

## Permissões

| Código | Uso |
|--------|-----|
| `central-agendamento.view.filial-es` | Ver calendário e reservar/solicitar (ES) |
| `central-agendamento.view.filial-sc` | Ver calendário e reservar/solicitar (SC) |
| `central-agendamento.manage.filial-es` | CRUD recursos (ES) |
| `central-agendamento.manage.filial-sc` | CRUD recursos (SC) |
| `central-agendamento.approve.filial-es` | Aprovar/rejeitar pendências (ES) |
| `central-agendamento.approve.filial-sc` | Aprovar/rejeitar pendências (SC) |
