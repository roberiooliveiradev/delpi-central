# Playbook — Gamificação do tour do portal

> **Código:** `portal/src/tour/` · **Doc base:** [portal-tour.md](./portal-tour.md)  
> **Versão do tour:** `2026-06-portal-v6-explore` · **Playbook gamificação:** v1 (jun/2026)

Roadmap de evolução da experiência gamificada do tour. Implementação **centralizada** em módulos do tour — sem `if` espalhado na Sidebar/Home.

---

## Princípios

| Regra | Detalhe |
|---|---|
| Celebrar, não distrair | Efeitos ≤ 2 s; sem loops |
| `prefers-reduced-motion` | Confetti e animações desligados; toast + check estáticos |
| Recompensa simbólica | XP e selos — sem economia real ou prêmios físicos |
| Módulo canônico | `portalTourGamification.ts`, `portalTourCelebration.ts`, `PortalTour.css` |
| Persistência | Fases A–B só UI; C+ estendem core-api se necessário |

---

## Estado atual (baseline)

- Barra de progresso (% desafios obrigatórios)
- Toast textual ao concluir desafio
- Badge `concluídos/total` no painel
- Anéis de destaque (outline azul)
- Botão **Dica** sob demanda nos cards
- Sync servidor (`user_portal_tour_progress`, `portal_tour_quest_events`)
- Admin: painel «quem está explorando»

---

## Roadmap

### Fase A — Micro-feedback ✅

**Objetivo:** reforço imediato a cada desafio sem poluir a tela.

| Item | Módulo | Status |
|---|---|---|
| Toast rico (+XP, categoria) | `PortalTour.tsx` + CSS | ✅ |
| Bump na barra XP | `portal-tour-xp-bar-fill.is-bump` | ✅ |
| Ring verde no acerto (~400 ms) | `portal-tour-highlight-ring.is-success` | ✅ |
| Pop no card concluído | `portal-tour-quest-item.is-just-done` | ✅ |
| Nível simbólico no painel | `portalTourGamification.ts` | ✅ |
| Banner categoria concluída | `PortalTour.tsx` | ✅ |
| Banner marco 25/50/75% | `portalTourGamification.ts` | ✅ |

**XP padrão:** 10 por desafio obrigatório, 5 opcional (`resolveQuestXp`).

**Níveis (por % do tour):**

| % | Rótulo |
|---|---|
| 0–24 | Explorador |
| 25–49 | Curioso |
| 50–74 | Expert |
| 75–99 | Embaixador DELPI |
| 100 | Mestre DELPI |

---

### Fase B — Celebração de conclusão ✅

**Objetivo:** clímax ao terminar todos os desafios obrigatórios.

| Item | Módulo | Status |
|---|---|---|
| Modal de conclusão (stats + selo) | `PortalTourCompletionModal.tsx` | ✅ |
| Confetti leve no 100% (canvas, sem dep) | `portalTourCelebration.ts` | ✅ |
| Abrir modal após último desafio ou botão Concluir | `PortalTour.tsx` | ✅ |
| Resumo: desafios, XP, nível | `portalTourGamification.ts` | ✅ |

**Pendente Fase B+:** ~~tempo de exploração (`startedAt` da API) no modal~~ ✅

### Fase F — Polimento pós-lançamento ✅

| Item | Entrega |
|---|---|
| Desafios «Retomar na home» e «Acompanhamento admin» | Catálogo + `portalTourQuests.ts` |
| `% progresso por explorador` no admin | `progressPercent` / `explorerLevel` em `/admin/portal-tour/explorers` |
| Aviso de falha de sync | `portalTourSyncStatus.ts` + banner no tour |
| Conquistas no modal de 100% | `PortalTourCompletionModal` |

---

### Fase C — Conquistas no perfil ✅

**Objetivo:** coleção persistente de selos.

| Item | Entrega | Status |
|---|---|---|
| Catálogo de conquistas | `core-api/.../portal_tour_achievement_catalog.py` | ✅ |
| `GET /me/portal-tour/achievements` | Deriva de progress + `quest_events` | ✅ |
| UI grid em Meu Perfil | `PortalTourAchievementsPanel.tsx` | ✅ |
| Export LGPD | `portalTourAchievements` no data-export | ✅ |
| Migration | Não necessária (reusa tabelas existentes) | ✅ |

**Critério de done:** usuário vê selos desbloqueados após concluir desafios; export inclui conquistas.

---

### Fase D — Social / admin enriquecido ✅

| Item | Entrega |
|---|---|
| Ranking «top exploradores» (semana) | `GET /admin/portal-tour/top-explorers` |
| Streak «voltou e completou +N» | `insights.returnStreakMessage` em `GET /me/portal-tour` |
| Tempo de exploração | `insights.explorationDurationSeconds` + modal de conclusão |
| Toggle «Animações do tour» no perfil | `portalTourPreferences.ts` + `localStorage` |
| Som opcional (off por padrão) | Fora de escopo — opt-in futuro |

### Fase E — Catálogo extensível + RBAC ✅

| Item | Entrega |
|---|---|
| Catálogo canônico backend | `portal_tour_quest_catalog.py` |
| Disponibilidade por permissão | `portal_tour_availability_service.py` |
| API catálogo personalizado | `GET /me/portal-tour/catalog` |
| Progresso/conquistas escopados | achievements + sync filtram pelo usuário |
| Novidades na versão | `newQuestIds` + badge «novidade» no portal |

---

## Mapa de arquivos

```
portal/src/tour/
├── PortalTour.tsx              # Orquestra UI + callbacks de celebração
├── PortalTourCompletionModal.tsx
├── PortalTourAchievementsPanel.tsx
├── portalTourAchievements.css
├── portalTourAchievementIcons.ts
├── PortalTour.css
├── portalTourGamification.ts   # XP, níveis, marcos, categorias
├── portalTourCelebration.ts    # Confetti, reduced-motion
├── portalTourPreferences.ts    # Toggle animações (localStorage)
├── portalTourInsights.ts       # Formatação duração / streak (UI)
├── PortalTourPreferencesToggle.tsx
├── portalTourQuests.ts         # Catálogo de desafios
└── portalTourPersistence.ts    # Sync servidor (Fase C pode estender)
```

---

## Checklist por fase (agente / dev)

### Ao implementar Fase A

- [ ] Toast mostra XP e não quebra mobile
- [ ] Ring success some em ≤ 500 ms
- [ ] `prefers-reduced-motion`: sem bump/confetti
- [ ] Build `npm run build` no portal

### Ao implementar Fase B

- [ ] Modal só quando `requiredDone >= requiredTotal`
- [ ] Confetti não bloqueia cliques (pointer-events: none)
- [ ] Esc fecha modal e conclui tour
- [ ] Documentar em [portal-tour.md](./portal-tour.md)

### Ao implementar Fase C

- [ ] Bump `PORTAL_TOUR_VERSION` se reexibir tour
- [ ] Migration + testes core-api
- [ ] Export/anonymize LGPD

### Ao implementar Fase D

- [ ] `GET /me/portal-tour` inclui `insights`
- [ ] Admin ranking semanal carrega sem erro
- [ ] Toggle animações persiste no perfil
- [ ] `prefers-reduced-motion` continua desligando confetti
- [ ] Build `npm run build` no portal

---

## Referências

- [portal-tour.md](./portal-tour.md) — comportamento e API
- [admin-estatisticas.md](./admin-estatisticas.md) — painel exploradores
- Regra workspace: `centralized-rules-first.mdc` — um módulo canônico por regra
