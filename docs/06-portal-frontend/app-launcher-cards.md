# Minha DELPI — App Launcher Cards (UI)

> **Arquivo:** `docs/06-portal-frontend/app-launcher-cards.md`  
> **Status:** documentação oficial (jun/2026)  
> **Código:** `portal/src/components/AppLauncherCard.tsx`, `AppLauncherReorderList.tsx`, `AppLauncher.css`  
> **Relacionado:** [favoritos.md](./favoritos.md), [menu-dinamico.md](./menu-dinamico.md)

---

## 1. Objetivo

Descreve o componente compartilhado de **card de aplicativo** usado no Portal para exibir, abrir, favoritar e (na sidebar) reordenar apps.

Um único componente (`AppLauncherCard`) atende todos os contextos; variações de layout e interação vêm de **props** e **variant**, não de cópias locais.

---

## 2. Onde aparece

| Superfície | Variant | Favoritar (pin) | Reordenar |
|---|---|:---:|:---:|
| Sidebar — favoritos | `sidebar` | Não | Sim (segurar + arrastar) |
| Home — Favoritos | `home` | Sim | Não |
| Home — Continuar trabalhando | `home` | Sim | Não |
| Modal **Apps** (launcher) | `launcher` (default) | Sim | Não |
| Perfil — Aplicações disponíveis | `launcher` | Sim | Não |

---

## 3. Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `components/AppLauncherCard.tsx` | Card, link principal, rotas inline, pin, integração com reorder |
| `components/AppLauncherCard.css` | Estilos do card, grid `.launcher-pinned-grid`, reorder na sidebar |
| `components/appLauncherAppearance.ts` | Rotas ativas, animações de aparecimento/navegação, helpers de path |
| `components/AppLauncherReorderList.tsx` | Contexto de drag, hold-to-reorder, persistência via callback |
| `layout/SidebarFavoritesList.tsx` | Monta favoritos da sidebar (`AppLauncherReorderList` + cards) |
| `utils/favoriteOrder.ts` | `reorderList`, `mergeFavoriteOrder` (mescla apps ocultos na ordem persistida) |
| `components/AppLauncher.css` | Modal de apps (overlay, busca, altura adaptável) |
| `state/AuthContext.tsx` | `addFavorite`, `removeFavorite`, `reorderFavorites` |
| `data/coreApi.ts` | `reorderFavoriteApps` → `PUT /me/apps/favorites/order` |

---

## 4. Grid de cards (`.launcher-pinned-grid`)

Definido em **`AppLauncherCard.css`** para carregar em qualquer página que importe o card (home, perfil).

```css
grid-template-columns: repeat(auto-fill, minmax(112px, 128px));
justify-content: center;
```

Comportamento (home / perfil):

- Cada card ocupa **no máximo ~128px** de largura.
- Com poucos apps, os cards **não esticam** e ficam **centralizados** na área disponível.
- Painéis da home usam `align-items: start` e `height: fit-content` para não criar área vazia entre colunas.

**Modal Apps** (`AppLauncher.css` — sobrescreve o grid):

- Largura: `clamp(360px, 94vw, 1120px)`; altura: `min(90vh, 860px)` com scroll interno (`.launcher-body`).
- Grid flexível: `repeat(auto-fill, minmax(120px, 1fr))` — cards **preenchem** a largura do modal.
- Overlay com padding **16px** (mais área útil que o default anterior).

### 4.1 Tipografia dos nomes

| Contexto | Tamanho base | Tiers (medium / long) |
|---|---|---|
| Grid home / modal / perfil | **15px** | 14px / 13px |
| Sidebar — app | **15px** | ellipsis em 1 linha |
| Sub-rotas inline (modal expandido) | **15px** | — |
| Sub-rotas sidebar | **13px** | — |

Regra canônica: `.launcher-app-tile:not(.sidebar-variant) .launcher-app-name { font-size: 15px; }`.

### 4.2 Hover (grid / modal / home / perfil)

Em `@media (hover: hover)`, tiles fora da sidebar recebem destaque suave ao hover:

- Fundo ~10% primary, borda ~30% primary, sombra leve, `translateY(-1px)`.
- Transições alinhadas à sidebar: **320ms** no tile, **280ms** no nome.

---

## 5. Favoritar (pin)

- Botão no canto superior direito do card (visível no hover; fixo quando já favoritado).
- Disponível quando `onTogglePin` é passado e `variant !== sidebar`.
- Fluxo: otimista em `AuthContext` → `POST` / `DELETE` `/me/apps/favorites/<app_id>` → recarga da lista.

Na **home**, no **modal Apps** e no **perfil**, o pin alterna favorito. Na **sidebar** o pin **não** é exibido — a lista já representa favoritos; fixar/desfixar permanece nas outras superfícies.

---

## 6. Sidebar — contexto de rota e estados visuais (jun/2026)

Módulo canônico: `appLauncherAppearance.ts` + `AppLauncherCard` (`variant="sidebar"`).

### 6.1 Hierarquia ativo (app vs rota)

| Camada | Classe / estado | Visual |
|---|---|---|
| App no contexto da rota | `.route-active` no tile | Fundo suave (~8% primary) agrupando header + sub-rotas |
| Rota selecionada | `.sidebar-inline-route.active` | Fundo um pouco mais forte (~16% primary), texto primary |
| App de rota única ativo | `.active` no tile (sem sub-rotas) | Destaque no link principal apenas |

Regras:

- Prefix match de path **não** marca várias rotas: `isLauncherRouteSelected` escolhe só a rota **mais específica** (`resolveActiveRouteForApp` — path mais longo).
- Apps com **uma rota visível** não expandem lista duplicada; `openApps` na sidebar não abre tile de rota única.

### 6.2 Expand / collapse de sub-rotas

Painel `launcher-inline-routes-panel` com `grid-template-rows: 0fr → 1fr` (~380ms). Rotas permanecem no DOM; `aria-hidden` e `tabIndex={-1}` quando recolhido.

- Chevron só expande/recolhe; clique no header navega para rota default.
- Ao sair do app (`isLauncherAppContextActive` falso), `Sidebar` remove `openApps[appId]` e o painel recolhe com animação.

### 6.3 Hover e animações

- Hover do tile e das sub-rotas com opacidades baixas e transições ~280–320ms.
- Animações de rota do launcher modal (`launcher-app-tile--routed`) **desligadas** na sidebar para não sobrescrever fundo de `.route-active`.
- Reset de links (`:visited`, `:hover`) não compete com `.sidebar-inline-route.active` — regras de ativo vêm **depois** do reset.

### 6.4 Nomes longos

`data-name-tier` (`short` | `medium` | `long`) ajusta `font-size` e truncamento no tile da sidebar (ellipsis em uma linha).

---

## 7. Reordenar favoritos na sidebar

### 7.1 Ativação (hold-to-drag)

A reorder **não** fica sempre visível (sem cursor `grab` permanente):

1. **Clique rápido** → navegação normal (SPA) ou expande rotas; Ctrl/Cmd+clique e clique do meio abrem em nova aba (`<a href>` real).
2. **Segurar ~380ms** → overlay *"Arraste para reordenar os favoritos"*, cursor `grab`.
3. **Mover** → modo arraste (*"Solte para reordenar"*), cursor `grabbing`, highlight de drop.
4. **Soltar** → `PUT /me/apps/favorites/order` com ordem mesclada.
5. **Segurar e soltar sem mover** → cancela (não navega, não reordena).

### 7.2 Área interativa

Toda a região principal do card (ícone + nome + chevron) participa do hold/drag. Sub-rotas expandidas permanecem links independentes.

### 7.3 Firefox — prévia de link

O arraste nativo de `<a href>` é bloqueado durante hold/drag (`dragstart`, `selectstart`, `mousedown` controlado) para evitar o popup *"O Firefox não pode exibir prévia deste link"*.

### 7.4 Ordem persistida com apps ocultos

Favoritos não lançáveis (sem rotas / não autorizados) não aparecem na sidebar, mas permanecem no backend. Ao reordenar só os visíveis, `mergeFavoriteOrder` preserva a posição relativa dos ocultos na lista completa.

---

## 8. Variants do card

| Variant | Layout | Link |
|---|---|---|
| `launcher` | Grid compacto, pin | `<a href>` + `onClick` SPA |
| `home` | Grid compacto, pin | Idem |
| `sidebar` | Coluna ícone + nome; rotas inline | `<a href>`; reorder via pointer events quando `reorderable` |

Props relevantes:

- `reorderable` — ativa reorder (requer ancestral `AppLauncherReorderList`).
- `isPinned` / `onTogglePin` — favorito.
- `isOpen` / `onToggleOpen` — expandir múltiplas rotas.

---

## 9. Testes e build

- Build Portal: `cd portal && npm run build`
- Core API (reorder): `core-api/app/tests/use_cases/test_reorder_favorite_apps_use_case.py`

---

## 10. Evoluções possíveis

- Reordenar favoritos na seção **Favoritos** da home (hoje só sidebar).
- Toasts de erro ao falhar reorder/favoritar.
- Limite máximo de favoritos na UI.
