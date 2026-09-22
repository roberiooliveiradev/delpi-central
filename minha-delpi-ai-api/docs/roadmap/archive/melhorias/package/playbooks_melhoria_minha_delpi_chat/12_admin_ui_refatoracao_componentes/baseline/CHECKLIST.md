# Baseline Admin UI — checklist (Fase 0)

> Capturas em **tema escuro** (padrão do chat). Viewports: **1440×900** (desktop) e **768×1024** (tablet).  
> Rota base: `/apps/minha-delpi-chat/admin` (ajustar host do Portal conforme ambiente).

## Legenda de severidade

| Nível | Significado |
|-------|-------------|
| **B** | Bloqueante — dados ilegíveis ou ação principal prejudicada |
| **C** | Cosmético — layout, hierarquia ou copy |

## Matriz componente × problema (pré-refatoração)

| Seção / sub-aba | Componente | Problema observado | Sev. | Pós Fase 2/3 |
|-----------------|------------|-------------------|------|--------------|
| Qualidade → Métricas → Roteamento | `AdminIntentRoutingMetrics` | Lista “Por intenção” sem alinhamento label/valor; tabela Recentes sem estilo | B | Migrado — primitivos |
| Qualidade → Interatividade | `AdminInteractivityMetrics` | KPIs agrupados à esquerda; ranking vazio com buraco | B | Migrado — primitivos |
| Qualidade → demais blocos | `Admin*Metrics` (lote) | `drawing-metrics__status-list` / `__recent` sem CSS dedicado | B | Migrado — Fase 2 |
| Qualidade → Operações | `AdminQualityOperations` | Header legado `drawing-metrics__header` | C | Eyebrow “Qualidade” |
| Agentes → Especialização | `AdminAgentsTab` sidebar | UUID como título; sem badge de status | B | Fase 3 — nome + badge + `<code>` id |
| Agentes → Uso | `AgentMiniDashboard` | KPIs em lista vertical do chat; selects pequenos | B | Fase 3 — `AdminKpiGrid` + variant admin |
| Agentes → Uso | `ChatRichDashboard` | Toolbar e ações de chat no admin | C | `variant="admin"` |
| Conhecimento | `AdminKnowledgeTab` | Toolbar heterogênea | C | Fase 4 |
| Plataforma → Tools | `AdminToolsTab` | Strips sem `AdminKpiGrid` | C | Fase 4 |
| Governança → Auditoria | `AuditTablePanel` | Tabela fora de `AdminDataTable` | C | Fase 4 |
| Transversal | Eyebrows “Playbook NN” | Ruído na UI operacional | C | Removidos nas métricas |

## Capturas obrigatórias (`screenshots/`)

Para cada linha, salvar `{viewport}/{section}-{subtab}.png` (ex.: `1440/quality-metrics-routing.png`).

| # | Seção | Sub-aba / foco | Arquivo sugerido |
|---|--------|----------------|------------------|
| 1 | Painel | Overview | `overview-main.png` |
| 2 | Conhecimento | Documentos | `knowledge-documents.png` |
| 3 | Agentes | Especialização (lista + detalhe) | `agents-specialization.png` |
| 4 | Qualidade | Métricas (topo + roteamento) | `quality-metrics.png` |
| 5 | Plataforma | Tools | `platform-tools.png` |
| 6 | Governança | Auditoria | `governance-audit.png` |

### Como gerar

Ver [screenshots/README.md](./screenshots/README.md) e o script `scripts/capture-admin-baseline.sh` no plugin `minha-delpi-chat`.

## Auditoria de markup legado

Ver [LEGACY_MARKUP_AUDIT.md](./LEGACY_MARKUP_AUDIT.md) — gerado em jun/2026 após migração Fase 2.

## Critérios de comparação pós-refatoração

- [ ] Mesmas 6 capturas repetidas em 1440px para diff visual.
- [ ] Blocos de métricas ocupam largura útil (≥70% em ≥1280px).
- [ ] Lista de agentes: nome legível + badge; UUID só em `<code>`.
- [ ] Zero uso de `__status-list` / `__recent` em TSX de métricas (compat só em CSS legado).
