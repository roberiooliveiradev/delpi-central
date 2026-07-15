# Status atual — Cadastro de Kaizens

> Snapshot em **2026-07-15**. Roadmap completo: [ROADMAP.md](./ROADMAP.md)

## Resumo

| Camada | Status |
|--------|--------|
| PostgreSQL `quality.kaizens` | ✅ Migrations V026–V043 |
| API CRUD + import | ✅ Em `main` |
| MFE `cadastro-kaizen` | ✅ Build + Docker dev |
| Dados piloto (dev) | ✅ 21+ registros via API |
| Core API register + RBAC prod | ⏳ Pendente |
| Dashboard `summary` (Sheets) | ⚠️ Legado — não lê Postgres ainda |
| Revisões versionadas | ✅ Migration V029 + serviço + rotas `/revisions` (dev) |
| Evidências (Antes/Depois) | ✅ Migration V030 + volume + rotas `/evidences` (dev) |
| Campos ricos + múltiplos responsáveis | ✅ Migration V031 + `kaizen_participants` (dev) |
| Ficha visual + edição por seção (MFE) | ✅ `KaizenDetailPage` + pipeline + timeline (dev) |
| Resultado real vs. estimado (F5) | ✅ Migration V032 + fallback calculado quando `realized_*` omitido (dev) |
| Validade da economia (1 ano) | ✅ `kaizen_savings_validity` — cap no ganho + `savings_active`/`savings_valid_until` (dev) |
| **Versões completas (ciclo de vida)** | ✅ Migration V034 + `version_status` + `/versions` (criar/editar/implantar) + só 1 implantada por vez (dev) |
| Melhoria = versão nova (clone + rascunho → implantar) | ✅ Seletor de versões + `create/implement_version`; edição inline = correção (dev) |
| Ganho por período (só versões implantadas) | ✅ `kaizen_savings_timeline` + `/savings-timeline` (rascunho não conta) (dev) |
| Evidências por versão | ✅ `kaizen_evidences.revision_id` + painel por versão (dev) |
| Registro de alterações (auditoria 3 camadas) | ✅ `kaizen_history` + `kaizen_audit_log` (append-only) + `/history` `/audit-log` (dev) |
| **Data recebimento da ideia** | ✅ Migration V035 + campo no Estágio + coluna na listagem (dev) |
| **Categorias múltiplas** | ✅ Migration V036 `categories TEXT[]` + multi-select creatable na ficha (dev) |
| **Data implantação = vigência** | ✅ UI unificada — `date_implemented` espelha `effective_from` da revisão; sem campo «Vigente a partir de» (dev) |
| Status `aprovado` + `date_committee_approved` | ✅ Migration V042 + regras de data/indicadores |
| Status `recebido` (ex-`em_andamento`) | ✅ Migration V043 |
| Formulário público + notificação | ✅ public-hub wizard + `POST /public/kaizen/suggestions` + sino Core |
| Compartilhar sugestão (QR/PNG) | ✅ Modal na listagem |
| Cálculo temporal do dashboard (revisões) | 📋 Especificado — [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md) (Fase 6b/6c) |

## O que já funciona

- Listagem com filtros (filial, status, tipo economia, título) e colunas **Recebimento da ideia** e **Implantação**
- Criar kaizen (com equipe, **categorias múltiplas** e descrição do processo)
- Ficha visual (`detalhe/{id}`) com edição por seção (identificação, estágio, economia)
- Excluir kaizen
- Cálculo automático de economia diária/anual; **ganho realizado** usa estimativa calculada quando `realized_daily_savings` não informado
- **Estágio:** recebimento da ideia, **data implantação** (única referência de vigência), descontinuação
- **Versões completas do kaizen**: cada "melhoria" é uma **versão nova e completa**.
  Botão **Criar nova versão** clona todos os dados num formulário completo → nasce
  **Recebido** (rascunho) sem afetar a versão implantada. Ao **implantar**
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
- Permissões `cadastro-kaizen.view` / `cadastro-kaizen.manage` / `cadastro-kaizen.notify-suggestions`
- **Formulário público de sugestão** (`/p/kaizen/sugestao/aberto`) com wizard 2 etapas,
  % de preenchimento e conclusão; botão **Compartilhar sugestão** (QR + link + PNG)
- Status **Recebido** / **Aprovado** / **Implantado** com regras de datas e indicadores

## Bloqueios para produção

1. Manifesto não registrado na Core API do ambiente alvo
2. Perfis sem permissão `cadastro-kaizen.*`
3. Ausência de scripts de homologação automatizada (`check-cadastro-kaizen.sh`)
4. Dashboard de qualidade ainda consome Google Sheets — usuários podem ver divergência até o dashboard ler as revisões (Fase 6b/6c)
5. Volume `kaizen-evidences` precisa existir no host de produção (`${DELPI_DATA_HOST_DIR}/kaizen-evidences`) — ver [infra/README-ambiente.md](../../../infra/README-ambiente.md)

## Próximo passo

1. **Fase 4** do [ROADMAP.md](./ROADMAP.md): registro no portal, RBAC e importação validada em staging (inclui volume de evidências).
2. **Fase 6b/6c**: cálculo temporal do dashboard lendo `kaizen_revisions` conforme [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md).

> Evolução planejada (modo visual/edição, evidências do processo, revisões versionadas, descrição e múltiplos responsáveis): [PLAYBOOK-EVOLUCAO-KAIZEN.md](./PLAYBOOK-EVOLUCAO-KAIZEN.md).

## Entregas recentes (jul/2026)

| Entrega | Onde | Notas |
|---------|------|-------|
| Ganho realizado com fallback | `kaizen_savings_calculator.resolve_realized_*`, summary PG | Sem medição informada, painel usa estimativa calculada (não R$ 0) |
| `date_idea_received` | V035, Estágio, listagem | Data de registro/recebimento da ideia |
| `categories TEXT[]` | V036, `kaizen_categories.py`, `CategoryMultiSelectField` | Multi-seleção + criar novas (localStorage `delpi-kaizen-custom-categories`) |
| `DateField` compartilhado | `@delpi/plugin-ui` + wrapper `components/ui/DateField.tsx` | Datas ISO no formulário e no detalhe |
| Vigência unificada | `kaizen_revision_service.resolve_effective_from` | `date_implemented` espelha `effective_from`; UI sem «Vigente a partir de»; implantar versão usa data do Estágio |
| Status `aprovado` + data comitê | V042, `kaizen_status_date_rules`, indicadores | Quantidade sim; ganhos financeiros não |
| Status `recebido` | V043 (rename `em_andamento`) | Default; fila pública/gestor; fora dos KPIs |
| Sugestão pública | `POST /public/kaizen/suggestions`, public-hub wizard | Sem JWT; notifica `notify-suggestions` |
| Compartilhar sugestão | Modal QR + link + Exportar PNG | `kaizenPublicSuggestionLink.ts` |
| Migração UI `@delpi/plugin-ui` | `plugins/cadastro-kaizen/docs/UI-PLUGIN-UI.md` | F2/F3 concluído: filtros, KPI, forms, SectionCard, dashboard e detalhe |
