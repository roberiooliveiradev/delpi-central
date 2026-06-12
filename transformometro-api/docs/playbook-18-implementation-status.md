# Playbook 18 — status de implementação (API)

Referência: [`docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-18-instancias-filial-setor-escopo.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-18-instancias-filial-setor-escopo.md)

Última atualização: jun/2026

## Sprints concluídos

| Sprint | Migrations | Entrega |
|--------|------------|---------|
| **S1 — Filiais UUID** | V011 | Tabela `filiais`, CRUD `/filiais`, options do banco, `bootstrap_filiais_from_cadastro.py` |
| **S2 — Setores UUID** | V012 | PK UUID + `codigo_setor`, `setor_filiais` com FKs UUID, import/export JSON 1.1 preservado |
| **S3 — Instâncias** | V013–V014 | `processo_instancias`, `revisoes.instancia_id`, backfill legado, rotas de instância |

## Migrations disponíveis

V001–V010 (legado) · **V011** filiais · **V012** setores UUID · **V013** instâncias · **V014** revisões → instância

Ver [migrations/README.md](../migrations/README.md).

## Rotas novas (S1–S3)

| Método | Rota | Notas |
|--------|------|-------|
| GET/POST | `/transformometro/filiais` | CRUD filial |
| GET/PUT/DELETE | `/transformometro/filiais/{id}` | Aceita UUID ou `codigo_filial` |
| GET/POST | `/transformometro/processos/{id}/instancias` | Par operacional `(filial × setor)` |
| GET | `/transformometro/instancias/{id}` | Detalhe com `codigo_filial`, `codigo_setor` |

## Compatibilidade MFE / JSON 1.1

- **`GET /options`:** `filiais[].id` e `setores[].id` permanecem **códigos de negócio** (`01`, `engenharia`); campos UUID adicionais: `filial_id`, `setor_id`.
- **Import cadastro:** `setores.setor_id` slug no JSON continua válido; serviço gera UUID + `codigo_setor`.
- **`processos.filial_id` / `setor_id`:** ainda presentes na tabela até **V015 (S4)**; revisões já usam `instancia_id`.

## Procedimento pós-migration (ambiente existente)

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a

python -m tm_app.infrastructure.persistence.plugins.migrations_runner up

python scripts/bootstrap_filiais_from_cadastro.py \
  -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json

# Validar cadastro (opcional)
python scripts/import_cadastro_json.py preview \
  -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json --mode replace
```

## Próximo (S4+)

| Sprint | Foco |
|--------|------|
| **S4** | V015 — processo mestre sem `filial_id`/`setor_id`; cadastro via instâncias |
| **S5** | V016 — `escopo_recurso` híbrido |
| **S6** | V017 — `dashboard_calculos` UUID |
| **S7–S10** | Visões dashboard, duplicar instância, api-delpi, RBAC |

## Testes

```bash
./scripts/ci-transformometro-api.sh   # raiz do monorepo
```

Suíte atual: **92 testes** (unitários; sem Postgres obrigatório no CI).
