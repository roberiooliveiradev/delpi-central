# PAC Qualidade — Planos de Ação

> **Produto:** PAC Qualidade DELPI  
> **Plugin:** `quality-action-plans`  
> **API transacional (agente):** `api-pac-quality`  
> **API consolidada (plugin):** `api-delpi` → `/quality/action-plans`  
> **Banco:** Postgres `postgres-plugins`, schema `quality`

---

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md) | **North star**, pilares, roadmap por ondas e critérios de excelência |
| [status-atual.md](./status-atual.md) | Snapshot do que está implementado (jun/2026) |
| [HOMOLOGACAO.md](./HOMOLOGACAO.md) | Roteiro de homologação com casos reais anonimizados |

## Referências externas

| Arquivo | Repositório |
|---|---|
| `playbook_pac_qualidade_delpi.md` | `api-pac-quality` — especificação funcional v0.1 |
| `docs/Playbook — Tratativa de Não Conformidades.pdf` | `api-pac-quality` — brainstorm da reunião |
| `docs/chatgpt-especialista-qualidade.md` | `api-pac-quality` — instruções do agente GPT |
| `api-delpi/docs/api/quality-action-plans-pac.md` | Contrato HTTP do plugin |

## Aplicar migrations

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality-action-plans
```

## Smoke rápido (dev)

```bash
# Plugin build
cd plugins/quality-action-plans && npm run build

# API PAC (se container ativo)
curl -s -H "Authorization: Bearer $PAC_QUALITY_API_KEY" \
  https://pac-api.minhadelpi.com.br/quality/action-plans?page_size=1
```
