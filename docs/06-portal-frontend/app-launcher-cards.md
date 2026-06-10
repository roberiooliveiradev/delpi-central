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
| `components/AppLauncherReorderList.tsx` | Contexto de drag, hold-to-reorder, persistência via callback |
| `layout/SidebarFavoritesList.tsx` | Monta favoritos da sidebar (`AppLauncherReorderList` + cards) |
| `utils/favoriteOrder.ts` | `reorderList`, `mergeFavoriteOrder` (mescla apps ocultos na ordem persistida) |
| `components/AppLauncher.css` | Modal de apps (overlay, busca, altura adaptável) |
| `state/AuthContext.tsx` | `addFavorite`, `removeFavorite`, `reorderFavorites` |
| `data/coreApi.ts` | `reorderFavoriteApps` → `PUT /me/apps/favorites/order` |

---

## 4. Grid de cards (`.launcher-pinned-grid`)

Definido em **`AppLauncherCard.css`** para carregar em qualquer página que importe o card (home, perfil, modal).

```css
grid-template-columns: repeat(auto-fill, minmax(110px, 120px));
justify-content: center;
```

Comportamento:

- Cada card ocupa **no máximo ~120px** de largura.
- Com poucos apps, os cards **não esticam** e ficam **centralizados** na área disponível.
- Painéis da home usam `align-items: start` e `height: fit-content` para não criar área vazia entre colunas.

**Modal Apps:** altura `auto` com `max-height: min(85vh, 640px)`; scroll interno quando há muitos apps.

---

## 5. Favoritar (pin)

- Botão no canto superior direito do card (visível no hover; fixo quando já favoritado).
- Disponível quando `onTogglePin` é passado e `variant !== sidebar`.
- Fluxo: otimista em `AuthContext` → `POST` / `DELETE` `/me/apps/favorites/<app_id>` → recarga da lista.

Na **home** e no **perfil**, o mesmo handler alterna favorito; na sidebar o app já está na lista de favoritos (sem pin — remoção pode ser feita pelo launcher ou perfil).

---

## 6. Reordenar favoritos na sidebar

### 6.1 Ativação (hold-to-drag)

A reorder **não** fica sempre visível (sem cursor `grab` permanente):

1. **Clique rápido** → navegação normal (SPA) ou expande rotas; Ctrl/Cmd+clique e clique do meio abrem em nova aba (`<a href>` real).
2. **Segurar ~380ms** → overlay *"Arraste para reordenar os favoritos"*, cursor `grab`.
3. **Mover** → modo arraste (*"Solte para reordenar"*), cursor `grabbing`, highlight de drop.
4. **Soltar** → `PUT /me/apps/favorites/order` com ordem mesclada.
5. **Segurar e soltar sem mover** → cancela (não navega, não reordena).

### 6.2 Área interativa

Toda a região principal do card (ícone + nome + chevron) participa do hold/drag. Sub-rotas expandidas permanecem links independentes.

### 6.3 Firefox — prévia de link

O arraste nativo de `<a href>` é bloqueado durante hold/drag (`dragstart`, `selectstart`, `mousedown` controlado) para evitar o popup *"O Firefox não pode exibir prévia deste link"*.

### 6.4 Ordem persistida com apps ocultos

Favoritos não lançáveis (sem rotas / não autorizados) não aparecem na sidebar, mas permanecem no backend. Ao reordenar só os visíveis, `mergeFavoriteOrder` preserva a posição relativa dos ocultos na lista completa.

---

## 7. Variants do card

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

## 8. Testes e build

- Build Portal: `cd portal && npm run build`
- Core API (reorder): `core-api/app/tests/use_cases/test_reorder_favorite_apps_use_case.py`

---

## 9. Evoluções possíveis

- Reordenar favoritos na seção **Favoritos** da home (hoje só sidebar).
- Toasts de erro ao falhar reorder/favoritar.
- Limite máximo de favoritos na UI.
