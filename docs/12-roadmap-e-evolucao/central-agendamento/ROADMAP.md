# Roadmap — Central de Agendamento

> **Escopo:** plugin `central-agendamento` + rotas `api-delpi/scheduling` + schema `scheduling`

## Fases

| Fase | Status | Entrega |
|------|--------|---------|
| **1** | Concluída | MFE, API CRUD recursos/reservas, migrations V001, compose dev, smoke homolog |
| **2** | Concluída | Compose prod, constraint anti-conflito V002, homolog API fase 2, testes unitários |
| **3** | Planejada | Reagendar reserva, notificações, seed demo por filial |

## Checklist produção

- [x] Serviço `central-agendamento` em `infra/docker-compose.yml`
- [x] `gateway.depends_on` inclui `central-agendamento`
- [x] Build CI: `./scripts/ci/build-central-agendamento.sh`
- [x] Smoke: `./scripts/homologacao/check-central-agendamento.sh`
- [x] API E2E: `./scripts/homologacao/check-scheduling-api.sh` (requer `TOKEN` com permissão manage)
- [ ] Registro Core API + RBAC (`register-manifest.sh`)
- [ ] Migration em prod: `run_plugins_migrations.py --plugin scheduling`

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
| `central-agendamento.view.filial-es` | Ver calendário e reservar (ES) |
| `central-agendamento.view.filial-sc` | Ver calendário e reservar (SC) |
| `central-agendamento.manage.filial-es` | CRUD recursos (ES) |
| `central-agendamento.manage.filial-sc` | CRUD recursos (SC) |
