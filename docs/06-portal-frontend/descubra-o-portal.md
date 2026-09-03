# Minha DELPI — Descubra o portal

> **Arquivo:** `docs/06-portal-frontend/descubra-o-portal.md`  
> **Status:** documentação oficial  
> **Implementação:** `portal/src/tour/` · **API:** Core API `/me/portal-tour*`  
> **Produto:** Minha DELPI  
> **Escopo:** getting started opt-in do Portal (faixa na home, card, lista sob demanda, perfil)

Documentação complementar (API, desafios, âncoras): [portal-tour.md](./portal-tour.md) · Gamificação: [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md)

---

## 1. Objetivo

**Descubra o portal** orienta novos usuários (e quem retorna após novidades) a conhecer apps, avisos, perfil e tema **sem atrapalhar o trabalho**.

Não é chat, bolha de atendimento nem companion persistente no canto da tela.

---

## 2. O que é

Tour **não linear** e **opt-in**:

- o usuário completa **desafios** no próprio ritmo (cliques reais na interface);
- o first-run tem **~6 desafios obrigatórios**; o restante é aprofundamento opcional;
- ganha XP / nível / conquistas (visíveis sobretudo no **perfil**);
- progresso sincroniza com a **Core API** e cache local;
- a exploração **não trava** menus nem apps.

Versão atual do tour: `2026-08-portal-v7-notification-channels` (`PORTAL_TOUR_VERSION` / `CURRENT_PORTAL_TOUR_VERSION`).

---

## 3. Onde o usuário vê «Descubra o portal»

| Superfície | Onde | Função |
|---|---|---|
| **Faixa na home** | Abaixo do saudação | CTA in-page: **Explorar** / **Agora não** + progresso |
| **Card na home** | Grid de resumos | Retomar exploração (`N/M`, `%`, novidades) |
| **Lista (drawer)** | Só após clique explícito | Desafios, barra XP, botão **Dica** (1 destaque) |
| **Meu perfil** | Conquistas do portal | **Continuar explorando** · **Zerar** · selos |

**Não há** auto-abertura de painel após o login. O canto inferior direito fica vazio até o usuário pedir.

---

## 4. Fluxo típico

```text
Login + consentimento LGPD
  ↓
Home mostra faixa + card (se não dismissed / não 100%)
  ↓
Usuário escolhe Explorar → abre a lista · ou Agora não → status dismissed (card some)
  ↓
Com lista aberta: cliques reais concluem desafios; Dica destaca 1 alvo
  ↓
✕ / Esc fecha só a lista (sem chip permanente no canto)
  ↓
100% dos obrigatórios → modal de celebração + completed
```

---

## 5. First-run (obrigatórios)

1. Abrir o catálogo de apps (`open-apps`)
2. Fixar um favorito (`pin-app`)
3. Voltar à home pelo logo (`sidebar-logo-home`)
4. Abrir notificações (`sidebar-notifications`)
5. Abrir o perfil (`sidebar-profile`)
6. Escolher o tema (`sidebar-theme`)

Demais desafios (home detalhada, canais de notificação, LGPD, admin…) são **opcionais**.

---

## 6. Agora não / retomar

| Ação | Efeito |
|---|---|
| **Agora não** | `PATCH` `status: dismissed` — faixa e card somem até bump com novidades ou retomada no perfil |
| Card / Explorar / Continuar | `status: exploring` + abre a lista |
| Novidades pós-versão | Badge no card/faixa — **sem** reabrir a lista sozinha |

---

## 7. Gamificação (resumo)

| Elemento | Comportamento |
|---|---|
| Toast +XP | Curto (≤ 2 s) ao concluir desafio |
| Level-up | Banner/toast — **sem** modal full-screen |
| Modal | Só no 100% dos obrigatórios |
| Conquistas / nível | Perfil |

---

## 8. Arquivos principais

```text
portal/src/tour/
├── PortalTour.tsx                 Lista sob demanda + detecção
├── PortalTourHomeBanner.tsx       Faixa in-page
├── PortalTourHomeEntry.tsx        Card na home
├── usePortalTourHomeProgress.ts   Dados compartilhados home
├── portalTourPersistence.ts       Sync + dismissed + no auto-open
└── portalTourQuests.ts            Seletores DOM

core-api/app/domain/portal_tour/
├── portal_tour_quest_catalog.py
└── …
```

Integração: `App.tsx` → `<PortalTour />` · `HomePage.tsx` → faixa + card.

---

## 9. Relacionados

- [portal-tour.md](./portal-tour.md) — referência técnica
- [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md)
- O onboarding do **chat** (`ChatOnboardingTour`) é produto **separado** — não unificar.
