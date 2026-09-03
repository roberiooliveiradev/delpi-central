# Playbook — Gamificação do tour do portal

> **Código:** `portal/src/tour/` · **Doc base:** [portal-tour.md](./portal-tour.md)  
> **Versão do tour:** `2026-08-portal-v7-notification-channels` · **Playbook gamificação:** v1 (jun/2026) · UX opt-in (set/2026)

Roadmap da experiência gamificada. Getting started é **opt-in** (faixa na home / card) — **sem** widget estilo chat nem auto-open.

---

## Princípios

| Regra | Detalhe |
|---|---|
| Celebrar, não distrair | Efeitos ≤ 2 s; sem loops; sem modal de level-up |
| Opt-in | Nunca abrir lista sozinho; **Agora não** → `dismissed` |
| First-run curto | ~6 obrigatórios; resto opcional |
| `prefers-reduced-motion` | Confetti e animações desligados |
| Recompensa simbólica | XP e selos — sem economia real |
| Módulo canônico | `portal/src/tour/` + `core-api/.../portal_tour/` |
| Não é chat | Sem unificar com `ChatOnboardingTour` |

---

## Estado atual (baseline)

- Faixa + card na home; lista só sob clique
- Barra de progresso (% obrigatórios)
- Toast +XP curto; level-up via banner (sem overlay modal)
- Dica sob demanda (1 anel)
- Sync servidor; `dismissed` persistente
- Admin: exploradores + «Adiaram»
- Fases A–E (micro-feedback, conclusão, conquistas, insights, catálogo RBAC) ✅

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

## Fora de escopo

- Som opcional
- Ranking social para o usuário final (admin ranking permanece)
- Bolha / companion conversacional
- Unificar com o tour do chat

---

## Referências

- [descubra-o-portal.md](./descubra-o-portal.md) — produto e UX
- [portal-tour.md](./portal-tour.md) — comportamento e API
- [admin-estatisticas.md](./admin-estatisticas.md) — painel exploradores
- Regra workspace: `centralized-rules-first.mdc` — um módulo canônico por regra
