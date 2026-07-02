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
| **Versões completas (ciclo de vida)** | ✅ Migration V034 + `version_status` + `/versions` (criar/editar/implantar) + só 1 implantada por vez (dev) |
| Melhoria = versão nova (clone + rascunho → implantar) | ✅ Modal de formulário completo + `create/implement_version`; edição inline = correção (dev) |
| Ganho por período (só versões implantadas) | ✅ `kaizen_savings_timeline` + `/savings-timeline` (rascunho não conta) (dev) |
| Evidências por versão | ✅ `kaizen_evidences.revision_id` + painel por versão (dev) |
| Registro de alterações (auditoria 3 camadas) | ✅ `kaizen_history` + `kaizen_audit_log` (append-only) + `/history` `/audit-log` (dev) |
| Cálculo temporal do dashboard (revisões) | 📋 Especificado — [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md) (Fase 6b/6c) |

## O que já funciona

- Listagem com filtros (filial, status, tipo economia, título)
- Criar kaizen (com equipe, categoria e descrição do processo)
- Ficha visual (`detalhe/{id}`) com edição por seção (identificação, estágio, economia)
- Excluir kaizen
- Cálculo automático de economia diária/anual
- **Versões completas do kaizen**: cada "melhoria" é uma **versão nova e completa**.
  Botão **Criar nova versão** clona todos os dados num formulário completo → nasce
  **Em andamento** (rascunho) sem afetar a versão implantada. Ao **implantar**
  (`POST /versions/{n}/implement`), a anterior vira **Substituída** e a nova assume,
  com aniversário de 1 ano próprio. **Só uma versão implantada por vez**. Edição inline
  das seções = **correção** da versão vigente (não cria versão).
- **Ganho por período**: soma só das versões que estiveram implantadas, respeitando a
  validade de 1 ano de cada segmento (`/savings-timeline`, `kaizen_savings_timeline`) —
  rascunhos não contam.
- **Evidências do processo** com galeria Antes/Depois, upload multi-arquivo (dropzone),
  link e download; evidências **gerais** (kaizen) ou **por versão** (`revision_id`)
- **Registro de alterações** (padrão PAC, 3 camadas): linha do tempo operacional
  (`kaizen_history`), versões/diffs (`kaizen_revisions`) e governança append-only
  (`kaizen_audit_log`)
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
