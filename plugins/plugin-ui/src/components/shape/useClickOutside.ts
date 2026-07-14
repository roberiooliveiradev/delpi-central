import { useEffect, useRef, type RefObject } from "react";

/**
 * Portais aninhados (cor, select, diálogo) vivem no body fora do panelRef —
 * clique neles não deve fechar o popover pai.
 */
const NESTED_OVERLAY_SELECTOR = [
  '[aria-modal="true"]',
  ".delpi-ui-shape-menu__panel",
  ".delpi-ui-color-picker",
  ".delpi-ui-select__panel",
  ".delpi-ui-shape-dialog",
  ".delpi-ui-help-tooltip",
  ".delpi-ui-combobox-number__panel",
].join(", ");

function isInsideNestedOverlay(target: Node): boolean {
  return target instanceof Element && Boolean(target.closest(NESTED_OVERLAY_SELECTOR));
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
      const inside = refsRef.current.some((ref) => ref.current?.contains(target));
      if (inside || isInsideNestedOverlay(target)) return;
      onOutsideRef.current();
    };

    document.addEventListener("pointerdown", handlePointerDown, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown, true);
    };
  }, [active]);
}
