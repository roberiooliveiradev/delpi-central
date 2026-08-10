import { useEffect, useRef, type RefObject } from "react";

/**
 * Portais aninhados (cor, select, diálogo) vivem no body fora do panelRef —
 * clique neles não deve fechar o popover pai.
 *
 * Não incluir `.delpi-ui-shape-menu__panel`: painéis peer (Preench. × Contorno)
 * também usam essa classe — tratá-los como “aninhados” deixa dois popovers abertos.
 */
const NESTED_OVERLAY_SELECTOR = [
  '[aria-modal="true"]',
  ".delpi-ui-color-picker",
  ".delpi-ui-color-more-popover",
  ".delpi-ui-select__panel",
  ".delpi-ui-shape-dialog",
  ".delpi-ui-help-tooltip",
  ".delpi-ui-combobox-number__panel",
  /* Nested AnchoredPanelPortal marked non-exclusive (select/combobox inside menu). */
  '[data-delpi-anchored-exclusive="false"]',
].join(", ");

/**
 * Overlay «aninhado» (não fecha o popover) vs. modal pai (fecha).
 *
 * Não usar ordem no DOM: ModalShell host-contained vive no root do MFE
 * (antes do portal do popover no `body`). Ordem faria o Formatar parecer
 * «pai» e um clique no card fecharia o grupo Número — desmontando o próprio
 * dialog que ainda estava dentro do popover.
 *
 * Regra: se o overlay contém âncora/painel, é contexto ancestral (workbench).
 * Se não contém nenhum ref, é peer/filho lógico (Formatar, cor, select).
 */
function isInsideNestedOverlay(target: Node, related: HTMLElement[]): boolean {
  if (!(target instanceof Element)) return false;
  const overlay = target.closest(NESTED_OVERLAY_SELECTOR);
  if (!overlay) return false;
  if (related.some((el) => overlay.contains(el))) return false;
  return true;
}

/**
 * Fecha overlay ao interagir fora dos refs.
 * Usa fase de captura para não depender do bubble (palco/editores costumam
 * chamar stopPropagation em pointerdown/mousedown).
 */
export function useClickOutside<T extends HTMLElement>(
  refs: RefObject<T | null>[],
  active: boolean,
  onOutside: () => void,
): void {
  const onOutsideRef = useRef(onOutside);
  onOutsideRef.current = onOutside;
  const refsRef = useRef(refs);
  refsRef.current = refs;

  useEffect(() => {
    if (!active) return;

    const handlePointerDown = (event: Event) => {
      const target = event.target as Node | null;
      if (!target) return;
      const panels = refsRef.current
        .map((ref) => ref.current)
        .filter((panel): panel is T => Boolean(panel));
      const inside = panels.some((panel) => panel.contains(target));
      if (inside || isInsideNestedOverlay(target, panels)) return;
      onOutsideRef.current();
    };

    document.addEventListener("pointerdown", handlePointerDown, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown, true);
    };
  }, [active]);
}
