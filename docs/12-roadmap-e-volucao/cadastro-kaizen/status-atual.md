# Status atual — Cadastro de Kaizens

> Snapshot em **2026-06-15**. Roadmap completo: [ROADMAP.md](./ROADMAP.md)

## Resumo

| Camada | Status |
|--------|--------|
| PostgreSQL `quality.kaizens` | ✅ Migrations V026/V027 |
| API CRUD + import | ✅ Em `main` |
| MFE `cadastro-kaizen` | ✅ Build + Docker dev |
| Dados piloto (dev) | ✅ 21 registros via API |
| Core API register + RBAC prod | ⏳ Pendente |
| Dashboard `summary` (Sheets) | ⚠️ Legado — não lê Postgres ainda |

## O que já funciona

- Listagem com filtros (filial, status, tipo economia, título)
- Criar / editar / excluir kaizen
- Cálculo automático de economia diária/anual
- Importar planilha (botão na UI ou `POST .../import-from-sheet`)
- Permissões `cadastro-kaizen.view` / `cadastro-kaizen.manage`

## Bloqueios para produção

1. Manifesto não registrado na Core API do ambiente alvo
2. Perfis sem permissão `cadastro-kaizen.*`
3. Ausência de scripts de homologação automatizada (`check-cadastro-kaizen.sh`)
4. Dashboard de qualidade ainda consome Google Sheets — usuários podem ver divergência até Fase 6 do roadmap

## Próximo passo

**Fase 4** do [ROADMAP.md](./ROADMAP.md): registro no portal, RBAC e importação validada em staging.
