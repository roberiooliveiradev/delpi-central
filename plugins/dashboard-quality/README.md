# Dashboard Qualidade

Microfrontend (Module Federation) para visualização de **métricas de qualidade** expostas pela **api-delpi** (dados TOTVS / planilhas).

## Escopo

| Incluído | Excluído (fases futuras / outro produto) |
|---|---|
| PPM interno e externo (resumo + detalhe) | Módulo NC PostgreSQL (`/quality/internal-nc`, `/quality/external-nc`) |
| Kaizens (resumo) | Cadastro / workflow de NC fora do TOTVS |
| Auditoria 5S (resumo) | |
| Listagem de NC do Protheus (`/quality/nonconformities`) | |

## Documentação

| Arquivo | Conteúdo |
|---|---|
| [docs/ROADMAP.md](./docs/ROADMAP.md) | Fases de desenvolvimento, critérios de pronto, dependências |
| [docs/API_MAPPING.md](./docs/API_MAPPING.md) | Rotas api-delpi consumidas pelo plugin |
| [docs/STRUCTURE.md](./docs/STRUCTURE.md) | Árvore de pastas e convenções |

## Backend

Todas as chamadas HTTP usam o prefixo do gateway:

```text
/apps/api-delpi/quality/*
```

Permissão exigida hoje na API: `api-delpi.quality.access`.  
O roadmap prevê permissão de plugin `dashboard-quality.view` com `require_any_permission` na api-delpi (mesmo padrão de LMPs).

## Referência

Implementação espelhada em `plugins/dashboard-lmps` (cliente HTTP, federation, Docker, compose).

## Status

**Fase 0 concluída:** Vite + Module Federation, Docker/compose, shell placeholder.  
**Fase 1 concluída:** `qualityApi.ts`, tipos DTO, hooks (`useQualityQueries`).  
**Fase 2 concluída:** home executiva com filtros, KPIs PPM, resumos Kaizen/5S.

```bash
cd plugins/dashboard-quality
npm install && npm run build
```

## Testes manuais (API)

Com token JWT válido (`dashboard-quality.view` ou `api-delpi.quality.access`):

```bash
export TOKEN="seu-jwt"
export BASE="http://localhost/apps/api-delpi/quality"

curl -s -H "Authorization: Bearer $TOKEN" "$BASE/ppm/internal/summary" | jq .
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/ppm/external/summary" | jq .
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/ppm/internal?page=1&page_size=10" | jq .
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/kaizens/summary" | jq .
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/audit-5s/summary" | jq .
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/nonconformities?type=all&page=1&page_size=20" | jq .
```

No código do plugin, importe de `src/api/qualityApi.ts` ou use os hooks em `src/hooks/useQualityQueries.ts`.
