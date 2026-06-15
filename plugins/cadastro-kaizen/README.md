# Cadastro de Kaizens

Microfrontend para cadastro operacional de kaizens no módulo qualidade.

## API (api-delpi)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/quality/kaizens/records` | Lista paginada |
| POST | `/quality/kaizens/records` | Cria registro |
| GET | `/quality/kaizens/records/{id}` | Detalhe |
| PUT | `/quality/kaizens/records/{id}` | Atualiza |
| DELETE | `/quality/kaizens/records/{id}` | Exclusão lógica |
| POST | `/quality/kaizens/records/import-from-sheet` | Importa kaizens ativos da planilha para PostgreSQL |

As rotas de leitura do dashboard (`/quality/kaizens/summary` e `/quality/kaizens/{kaizen_id}`) continuam na planilha Google Sheets até integração futura com PostgreSQL.

## Permissões

- `cadastro-kaizen.view` — consulta
- `cadastro-kaizen.manage` — criar/editar/excluir

## Desenvolvimento

```bash
npm install
npm run dev
```

## Build e registro no portal

```bash
npm run build
TOKEN=<jwt> ./scripts/register-manifest.sh
```

## Migrations

As tabelas ficam em `api-delpi/migrations/plugins/quality/` (V026 submodules, V027 kaizens).

```bash
cd api-delpi
python scripts/run_plugins_migrations.py --plugin quality
```
