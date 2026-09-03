# Descubra o portal (tour gamificado)

> **Nome na UI:** **Descubra o portal** · **Doc de produto:** [descubra-o-portal.md](./descubra-o-portal.md)  
> **Código:** `portal/src/tour/` · **Integração:** `App.tsx` (`PortalTour`), `HomePage.tsx` (`PortalTourHomeBanner` + `PortalTourHomeEntry`)

Getting started **opt-in** e **não linear** para explorar a Minha DELPI. Exibido por versão; pode ser adiado (**Agora não** → `dismissed`) ou reiniciado em **Meu Perfil**.

Versão: `2026-08-portal-v7-notification-channels`.

---

## Comportamento

| Aspecto | Detalhe |
|---|---|
| Disparo automático de painel | **Nunca** (`shouldAutoOpenPortalTourPanel` → `false`) |
| Entrada | Faixa na home + card; perfil «Continuar explorando» |
| Agora não | `PATCH status=dismissed` (persistente até bump com novidades ou retomada) |
| Persistência | `localStorage` + **core-api** |
| Reinício | Continuar (sem apagar) · Zerar → `DELETE /me/portal-tour` |
| Fechar lista | ✕ / Esc — sem chip permanente no canto |
| Conclusão | 100% dos **obrigatórios** do catálogo filtrado |
| Ordem | Livre |
| Bloqueio | Nenhum |
| Destaques | Só após **Dica** (1 anel); Esc oculta a dica |
| Level-up | Toast/banner — sem overlay modal |
| Watch de cliques | Só com sessão `exploring` (após Explorar) ou lista aberta; `dismissed` = zero watch |

O tour observa cliques (`watchTourQuests`) quando a sessão está ativa. Cada desafio tem **passos** no botão **Dica**.

---

## API (core-api)

| Método | Path | Auth | Descrição |
|---|---|---|---|
| GET | `/me/portal-tour` | Usuário | Estado (`exploring` \| `completed` \| `dismissed`) |
| PATCH | `/me/portal-tour` | Usuário | Sync progresso / dismissed / completed |
| GET | `/me/portal-tour/catalog` | Usuário | Catálogo disponível (RBAC + novidades) |
| GET | `/me/portal-tour/achievements` | Usuário | Conquistas |
| DELETE | `/me/portal-tour` | Usuário | Zera progresso |
| GET | `/admin/portal-tour/explorers` | `rbac.manage` | Quem explora / adiou / concluiu |
| GET | `/admin/portal-tour/top-explorers` | `rbac.manage` | Ranking semanal |

**Status:** `exploring` · `completed` · `dismissed` («Agora não» — **não** normalizado para exploring).

Fonte de verdade dos desafios: `portal_tour_quest_catalog.py`. DOM: `portalTourQuests.ts`.

---

## First-run (obrigatórios)

| ID | Título |
|---|---|
| `open-apps` | Catálogo de apps |
| `pin-app` | Fixar um app |
| `sidebar-logo-home` | Voltar à home pelo logo |
| `sidebar-notifications` | Sino na sidebar |
| `sidebar-profile` | Menu de perfil |
| `sidebar-theme` | Personalizar tema |

Todo o restante do catálogo é `optional=True` (aprofundar), inclusive admin e canais de notificação v7.

---

## UI

- Faixa **in-page** na home (não overlay / não FAB)
- Card no grid de resumos
- Lista flutuante **só sob clique** (inferior direito enquanto aberta)
- Sem auto-open; sem chip persistente ao fechar
- Anel de destaque apenas com Dica ativa

---

## Nova versão do tour

1. Desafio em `portal_tour_quest_catalog.py` (preferir `optional=True` salvo se for núcleo)
2. Ligar em `portalTourQuests.ts` + `data-tour`
3. Bump `CURRENT_PORTAL_TOUR_VERSION` / `PORTAL_TOUR_VERSION` se quiser reexibir a quem concluiu
4. Novidades: badge na home — **sem** auto-open do painel
5. Documentar em [descubra-o-portal.md](./descubra-o-portal.md)

---

## Relacionados

- [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md)
- Chat onboarding (`ChatOnboardingTour`) — **fora** deste fluxo
