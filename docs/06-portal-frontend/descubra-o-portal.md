# Minha DELPI — Descubra o portal

> **Arquivo:** `docs/06-portal-frontend/descubra-o-portal.md`  
> **Status:** documentação oficial  
> **Implementação:** `portal/src/tour/` · **API:** Core API `/me/portal-tour*`  
> **Produto:** Minha DELPI  
> **Escopo:** onboarding gamificado do Portal (tour, card na home, painel flutuante, perfil)

Documentação complementar (API, desafios, âncoras): [portal-tour.md](./portal-tour.md) · Gamificação: [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md)

---

## 1. Objetivo

Este documento descreve o recurso **Descubra o portal** — nome exibido na interface para o tour gamificado da Minha DELPI.

Ele orienta novos usuários (e quem retorna após uma nova versão) a conhecer favoritos, catálogo de apps, notificações, perfil, privacidade, tema e administração, sem bloquear o uso da plataforma.

---

## 2. O que é

**Descubra o portal** é um tour **não linear** e **gamificado**:

- o usuário completa **desafios** no próprio ritmo (cliques reais na interface);
- ganha **XP**, **nível de explorador** e **conquistas**;
- o progresso sincroniza com a **Core API** e cache local;
- a exploração **não trava** menus nem apps — painel flutuante + destaques visuais.

Versão atual do tour: `2026-06-portal-v6-explore` (`PORTAL_TOUR_VERSION` / `CURRENT_PORTAL_TOUR_VERSION`).

---

## 3. Onde o usuário vê «Descubra o portal»

| Superfície | Onde | Função |
|---|---|---|
| **Painel flutuante** | Canto inferior direito (full-width no mobile) | Lista de desafios, barra de XP, botão **Dica**, minimizar (✕ / `Esc`) |
| **Card na home** | Grid de resumos no topo da página inicial | Retomar exploração com progresso (`N/M`, `%`, nível) |
| **Meu perfil** | Seção do tour | **Continuar explorando** · **Zerar progresso e recomeçar** · conquistas |

Implementação:

| Superfície | Componente |
|---|---|
| Painel | `PortalTour.tsx` |
| Card na home | `PortalTourHomeEntry.tsx` |
| Perfil | `PortalTourProfileControls.tsx` · `PortalTourAchievementsPanel.tsx` |

---

## 4. Fluxo típico

```text
Login + consentimento LGPD
  ↓
Portal verifica versão do tour (localStorage + GET /me/portal-tour)
  ↓
Se ainda não concluiu → painel «Descubra o portal» abre automaticamente
  ↓
Usuário explora desafios (ordem livre) — cliques detectados em segundo plano
  ↓
Fechar painel (✕ / Esc) → exploração continua; card na home permanece disponível
  ↓
100% dos desafios obrigatórios → modal de celebração + status completed no servidor
  ↓
Card e painel somem até bump de versão ou reset manual no perfil
```

---

## 5. Card «Descubra o portal» na home

### 5.1 Conteúdo

O card usa o mesmo visual dos demais resumos da home (`home-summary-card`):

- **Título:** Descubra o portal  
- **Valor:** `desafios concluídos / obrigatórios` (ex.: `3/12`)  
- **Subtítulo:** `percentual · nível` (ex.: `25% · Explorador`)  
- **Ícone:** troféu · **Ação:** abre ou retoma o painel

Âncora de tour: `[data-tour="home-portal-tour-resume"]` · Desafio opcional: `home-portal-tour-resume`.

### 5.2 Quando o card aparece

Regras em `resolvePortalTourHomeEntryState` (`portalTourHomeEntry.ts`):

| Condição | Card visível? |
|---|---|
| Usuário não autenticado | Não |
| Tour da versão atual **concluído** (`completed`) | Não |
| Progresso **100%** dos obrigatórios | Não |
| Explorando (`exploring`) com desafios pendentes | **Sim** |
| Painel flutuante **aberto** | **Sim** (não some ao abrir o modal do tour) |

A visibilidade depende do **progresso da exploração**, não do estado `panelOpen` da sessão.

### 5.3 Anti-flicker no refresh

Para evitar piscar ou sumir no carregamento:

- **Shell estável:** o card permanece montado enquanto `shouldShowPortalTour` indica tour provável e os dados ainda carregam;
- **Cache de exibição:** `sessionStorage` (`delpi.portal.tourHomeEntry.v1`) guarda percentual e nível por usuário entre refreshes;
- **Animação:** `initial={false}` no card — sem entrada animada a cada reload;
- **Fetch estável:** `coreApiRef` evita re-fetch desnecessário ao trocar referência do cliente HTTP.

Estado de carregamento: classe `portal-tour-home-entry--loading`, botão desabilitado, subtítulo «Carregando…» (ou valores em cache).

### 5.4 Clique no card

| Situação | Comportamento |
|---|---|
| Sessão do tour ativa | `openPortalTourPanel()` — só reabre o painel |
| Sessão inativa | `resumePortalTour()` — retoma exploração e abre painel |

---

## 6. Painel flutuante

| Aspecto | Comportamento |
|---|---|
| Posição | Inferior direita; safe-area no mobile |
| Minimizar | ✕ ou `Esc` — **não** encerra a exploração |
| Desafios | Agrupados por categoria; estados: disponível, indisponível, concluído |
| Dica | Passos práticos sob demanda (sem balão automático) |
| Destaque | Anéis `portal-tour-highlight-ring` nos elementos-alvo |
| Bloqueio | Nenhum — interface sempre clicável |

Durante o tour, `html[data-portal-tour-active="true"]` ajusta z-index (painel acima do launcher) e impede que dropdowns da sidebar fechem por clique externo.

---

## 7. Retomar e reiniciar

| Ação | Onde | Efeito |
|---|---|---|
| Card na home | `/` | Abre/retoma painel |
| **Continuar explorando** | `/profile` | Retoma sem apagar progresso |
| **Zerar progresso e recomeçar** | `/profile` | Confirmação → `DELETE /me/portal-tour` → tour do zero |

---

## 8. Desafios em destaque (home e navegação)

| ID | Título | Interação |
|---|---|---|
| `sidebar-logo-home` | Voltar à home pelo logo | Clique no logo Minha DELPI na sidebar (`#sidebar-logo`, `data-tour="sidebar-logo"`) fora da home |
| `home-portal-tour-resume` | Retomar o tour na home | Clique no card **Descubra o portal** (opcional) |

O logo na sidebar é um botão acessível (`role="button"`, Enter/Espaço) que navega para `/`. O hover mantém as cores originais do SVG; apenas escala e sombra no círculo de fundo.

Lista completa de desafios: [portal-tour.md § Categorias e desafios](./portal-tour.md#categorias-e-desafios).

---

## 9. Gamificação (resumo)

| Elemento | Origem |
|---|---|
| XP e percentual | `portal_tour_gamification_service.py` (Core API) |
| Nível (`Explorador`, …) | Catálogo + progresso sincronizado |
| Toast +XP ao concluir desafio | `PortalTour.tsx` |
| Modal de conclusão + confetti | Ao atingir 100% obrigatórios |
| Conquistas | Perfil + `GET /me/portal-tour/achievements` |
| Admin — acompanhamento | Estatísticas → Acompanhamento ([admin-estatisticas.md](./admin-estatisticas.md)) |

Detalhes e roadmap: [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md).

---

## 10. API e persistência

| Camada | Detalhe |
|---|---|
| **Core API** | `user_portal_tour_progress`, `portal_tour_quest_events` |
| **Endpoints** | `GET/PATCH/DELETE /me/portal-tour`, `GET /me/portal-tour/catalog`, `GET /me/portal-tour/achievements` |
| **Cache local** | `localStorage` — versão, ids concluídos, dismiss |
| **Sync** | Debounce ~650 ms após cada desafio concluído |

Referência HTTP: [controllers-e-rotas.md § portal-tour](../04-core-api/controllers-e-rotas.md).

---

## 11. Arquivos principais

```text
portal/src/tour/
├── PortalTour.tsx              Painel + detecção de cliques
├── PortalTourHomeEntry.tsx     Card na home
├── portalTourHomeEntry.ts      Regras de visibilidade do card
├── portalTourQuests.ts         Desafios, seletores, isAvailable
├── portalTourSession.ts        Sessão (panelOpen, progresso UI)
├── portalTourPersistence.ts    Sync remoto + localStorage
├── portalTourStorage.ts        Versão e shouldShowPortalTour
└── PortalTourProfileControls.tsx Perfil — continuar / zerar

core-api/app/domain/portal_tour/
├── portal_tour_quest_catalog.py    Catálogo canônico
├── portal_tour_gamification_service.py
└── portal_tour_availability_service.py
```

Integração global: `App.tsx` monta `<PortalTour />` · `HomePage.tsx` monta `<PortalTourHomeEntry />`.

---

## 12. Nova versão ou novo desafio

1. Registrar desafio em `portal_tour_quest_catalog.py`.
2. Ligar DOM em `portalTourQuests.ts` + `data-tour`.
3. Incrementar `CURRENT_PORTAL_TOUR_VERSION` (API) e `PORTAL_TOUR_VERSION` (portal).
4. Atualizar [portal-tour.md](./portal-tour.md) e este documento se mudar UX do card ou painel.

---

## 13. Relacionados

- [portal-tour.md](./portal-tour.md) — referência técnica completa (API, âncoras, eventos)
- [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md) — XP, celebrações, conquistas
- [admin-estatisticas.md](./admin-estatisticas.md) — painel admin do tour
- [visao-geral-portal.md](./visao-geral-portal.md) — estrutura do shell React
