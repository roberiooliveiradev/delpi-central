# Status atual — Transformômetro

Atualizado após importação da planilha em produção (43 processos).

## Entregue

| Área | Status |
|------|--------|
| API + migrations V001–V003 | ✅ Produção |
| CRUD + UI cadastro + datas de vigência | ✅ |
| Dashboard + recálculo materializado | ✅ |
| Import planilha (CLI + UI + merge por código) | ✅ |
| Dados migrados da planilha Transforma+ | ✅ |

## Pendente (Fase 3)

| Item | Responsável |
|------|-------------|
| Registrar/atualizar manifesto na Core API + RBAC | Ops / admin portal |
| Planilha somente leitura | Google Workspace |
| Doc deploy | [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md) |
| SI/engineering consumir `transformometro-api` | Backlog opcional |

## Comandos úteis (srv-api)

```bash
cd ~/projetos/delpi-central
git pull
docker compose build transformometro-api transformometro
docker compose up -d transformometro-api transformometro

docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --preview
```

## Referências

- [ROADMAP.md](./ROADMAP.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [ESPECIFICACAO.md](./ESPECIFICACAO.md)
