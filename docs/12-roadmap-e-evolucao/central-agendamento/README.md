# Central de Agendamento — índice

> Plugin `central-agendamento` + API `/apps/api-delpi/scheduling/*` + schema `scheduling` em `postgres-plugins`.

## Documentos

| Arquivo | Conteúdo |
|---------|----------|
| [ROADMAP.md](./ROADMAP.md) | Fases de entrega e checklist de produção |
| [Plugin README](../../plugins/central-agendamento/README.md) | Dev local, API, migrations, registro |
| [Inventário plugins](../../08-plugins/README.md) | CI, homologação, permissões |

## Stack

| Item | Valor |
|------|-------|
| `id` | `central-agendamento` |
| Container | `delpi-central-agendamento` |
| Rotas Portal | `/apps/central-agendamento/filial-es`, `/apps/central-agendamento/filial-sc` |
| Migration plugin | `api-delpi/migrations/plugins/scheduling/` |

## Homologação

```bash
bash ./scripts/homologacao/check-central-agendamento.sh   # Fase 1 — smoke
export TOKEN="<jwt>"
bash ./scripts/homologacao/check-scheduling-api.sh        # Fase 2 — API ponta a ponta
```
