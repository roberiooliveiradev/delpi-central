# Status atual — Cadastro de Kaizens

> Snapshot em **2026-07-02**. Roadmap completo: [ROADMAP.md](./ROADMAP.md)

## Resumo

| Camada | Status |
|--------|--------|
| PostgreSQL `quality.kaizens` | ✅ Migrations V026/V027 |
| API CRUD + import | ✅ Em `main` |
| MFE `cadastro-kaizen` | ✅ Build + Docker dev |
| Dados piloto (dev) | ✅ 21 registros via API |
| Core API register + RBAC prod | ⏳ Pendente |
| Dashboard `summary` (Sheets) | ⚠️ Legado — não lê Postgres ainda |
| Revisões versionadas | ✅ Migration V029 + serviço + rotas `/revisions` (dev) |
| Evidências (Antes/Depois) | ✅ Migration V030 + volume + rotas `/evidences` (dev) |
| Campos ricos + múltiplos responsáveis | ✅ Migration V031 + `kaizen_participants` (dev) |
| Ficha visual + edição por seção (MFE) | ✅ `KaizenDetailPage` + pipeline + timeline (dev) |
| Resultado real vs. estimado (F5) | ✅ Migration V032 + efetividade na ficha (dev) |
| Validade da economia (1 ano) | ✅ `kaizen_savings_validity` — cap no ganho + `savings_active`/`savings_valid_until` (dev) |
| Cálculo temporal do dashboard (revisões) | 📋 Especificado — [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md) (Fase 6b/6c) |

## O que já funciona

- Listagem com filtros (filial, status, tipo economia, título)
- Criar kaizen (com equipe, categoria e descrição do processo)
- Ficha visual (`detalhe/{id}`) com edição por seção (identificação, estágio, economia)
- Excluir kaizen
- Cálculo automático de economia diária/anual
- **Revisões versionadas**: mudança de status/economia gera revisão (baseline →
  implantação → melhoria), com vigência e estado por data (`/revisions`, `/at`)
- **Evidências do processo** com galeria Antes/Depois, upload (arquivo/link) e download
- **Múltiplos responsáveis/participantes** (accountable segue como principal)
- Importar planilha (botão na UI ou `POST .../import-from-sheet`)
- Permissões `cadastro-kaizen.view` / `cadastro-kaizen.manage`

## Bloqueios para produção

1. Manifesto não registrado na Core API do ambiente alvo
2. Perfis sem permissão `cadastro-kaizen.*`
3. Ausência de scripts de homologação automatizada (`check-cadastro-kaizen.sh`)
4. Dashboard de qualidade ainda consome Google Sheets — usuários podem ver divergência até o dashboard ler as revisões (Fase 6b/6c)
5. Volume `kaizen-evidences` precisa existir no host de produção (`${DELPI_DATA_HOST_DIR}/kaizen-evidences`) — ver [infra/README-ambiente.md](../../../infra/README-ambiente.md)

## Próximo passo

1. **Fase 4** do [ROADMAP.md](./ROADMAP.md): registro no portal, RBAC e importação validada em staging (inclui volume de evidências).
2. **Fase 6b/6c**: cálculo temporal do dashboard lendo `kaizen_revisions` conforme [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md).
3. Extras priorizáveis (Eixo F do playbook): resultado real vs. estimado, vínculo com PAC, auditoria de governança.

> Evolução planejada (modo visual/edição, evidências do processo, revisões versionadas, descrição e múltiplos responsáveis): [PLAYBOOK-EVOLUCAO-KAIZEN.md](./PLAYBOOK-EVOLUCAO-KAIZEN.md).
