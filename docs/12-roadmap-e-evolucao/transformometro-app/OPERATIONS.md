# Operações — Transformômetro

Runbook para equipe após go-live (Postgres como fonte de verdade).

## URLs

| Recurso | URL |
|---------|-----|
| Portal | `https://www.minhadelpi.com.br/apps/transformometro` |
| Dashboard | `/apps/transformometro/dashboard` |
| Processos | `/apps/transformometro/processos` |
| Import (admin) | `/apps/transformometro/import` |
| API health | `/apps/transformometro-api/transformometro/health` |

## Rotina diária

1. Cadastro e alterações somente pela **UI** ou API (`transformometro-api`).
2. Após mudanças relevantes (revisão ativa, vigências, medições): **Dashboard → Recalcular**.
3. Não editar a planilha Transforma+ em produção (somente leitura ou desligada).

## Importação / reimportação

### Primeira carga (já feita)

```bash
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --apply --replace
```

### Atualizar da planilha (contingência)

```bash
# Pré-visualizar
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --preview

# Merge (mantém UUIDs por codigo_processo)
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --apply

# Substituir tudo (cuidado)
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --apply --replace
```

Validar no JSON de saída: `diff.all_match: true` (economia líquida/bruta vs planilha).

## Registro Core API e RBAC

```bash
export TOKEN="<jwt com apps.manage>"
export BASE_URL="https://www.minhadelpi.com.br"
./plugins/transformometro/scripts/register-manifest.sh
```

Atribuir ao perfil de engenharia/gestão, no mínimo:

- `transformometro.view`
- `transformometro.processes.manage`
- `transformometro.revisions.manage`
- `transformometro.dashboard.recalculate`
- `transformometro.admin` (somente quem importa)

## Desligar escrita na planilha Google

Checklist (manual, Google Workspace):

1. Comunicar que o cadastro oficial é o **Transformômetro** no portal.
2. Na planilha `TRANSFORMA_MAIS_SHEET_ID`: restringir edição (visualizador para consulta histórica) ou mover para pasta arquivada.
3. Remover links de edição em procedimentos internos / Apps Script de escrita.
4. Manter `TRANSFORMA_MAIS_*` no `.env` só se ainda usar import de contingência.
5. `dashboard-engineering` / SI continuam podendo ler Sheets até migrar indicador (Fase 3 opcional).

## Troubleshooting

| Sintoma | Ação |
|---------|------|
| `db_ready: false` | `TM_RUN_MIGRATIONS_ON_STARTUP=true`, reiniciar API, ver logs `tm_migrations_*` |
| POST processo 500 | Rebuild API (fix `SimpleNamespace` no audit); ver logs |
| Dashboard zerado | Cadastrar revisões + medições → **Recalcular** |
| Import `uq_processos_codigo` | Usar `--replace` ou `git pull` com reconcile por `codigo_processo` |
| Números ≠ planilha antiga | Esperado: spec usa delta de recursos na bruta; ver [OVERVIEW.md](./OVERVIEW.md) |

## Auditoria

Mutações gravam em `transformometro.audit_logs` (entity_type, action, user_id, payload_json).

## Integração com api-delpi e Strategic Indicators

Não duplicar leitura SQL nem calculador: consumir a API oficial.

| Consumidor | Rotas públicas (inalteradas) | Upstream interno |
|------------|------------------------------|-------------------|
| dashboard-engineering | `/apps/api-delpi/engineering/transforma-mais/*` | `transformometro-api` |
| strategic-indicators | snapshot engenharia | `transformometro-api` |

Endpoints de integração (contrato legado engenharia):

- `GET /transformometro/integrations/engineering/transforma-mais/processes`
- `GET /transformometro/integrations/engineering/transforma-mais/processes/summary`

Cliente compartilhado: `shared/transformometro_client` (`TransformometroApiClient`).

Variáveis:

- `TRANSFORMOMETRO_API_BASE_URL` — ex.: `http://transformometro-api:8000/apps/transformometro-api/transformometro`
- `TRANSFORMOMETRO_SERVICE_BEARER` — opcional, jobs SI sem usuário no contexto
