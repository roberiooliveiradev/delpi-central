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
| Revisões temporais | 📋 Especificado — [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md) |

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
5. Alterações de status/economia sobrescrevem o registro — **sem histórico** até implementar revisões (Fase 6a)

## Próximo passo

1. **Fase 4** do [ROADMAP.md](./ROADMAP.md): registro no portal, RBAC e importação validada em staging.
2. **Fase 6a** (após prod): migration `kaizen_revisions` conforme [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md).

> Evolução planejada (modo visual/edição, evidências do processo, revisões versionadas, descrição e múltiplos responsáveis): [PLAYBOOK-EVOLUCAO-KAIZEN.md](./PLAYBOOK-EVOLUCAO-KAIZEN.md).
