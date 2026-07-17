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
  ".delpi-ui-select__panel",
  ".delpi-ui-shape-dialog",
  ".delpi-ui-help-tooltip",
  ".delpi-ui-combobox-number__panel",
  /* Nested AnchoredPanelPortal marked non-exclusive (select/combobox inside menu). */
  '[data-delpi-anchored-exclusive="false"]',
].join(", ");

/**
 * Overlay é «aninhado» só quando abriu DEPOIS do popover (portal appendado
 * após o painel → visualmente acima). Um modal ancestral ou aberto ANTES
 * (ex.: workbench em ModalShell `aria-modal`) é contexto pai: clique nele,
 * fora do painel, deve fechar o popover normalmente.
 */
function isInsideNestedOverlay(target: Node, panels: HTMLElement[]): boolean {
  if (!(target instanceof Element)) return false;
  const overlay = target.closest(NESTED_OVERLAY_SELECTOR);
  if (!overlay) return false;

  return panels.every((panel) => {
    if (overlay.contains(panel)) return false;
    const position = overlay.compareDocumentPosition(panel);
    // Painel vem depois do overlay no DOM → overlay abriu antes (é o pai).
    if (position & Node.DOCUMENT_POSITION_FOLLOWING) return false;
    return true;
  });
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
