const FOCUSABLE = "button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex='-1'])";

export function focusableInDialog(dialog: HTMLElement): HTMLElement[] {
  return Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((element) => {
    if (element.getAttribute("aria-hidden") === "true") return false;
    return element.tabIndex !== -1;
  });
}

/** Mantém o foco no diálogo aberto e devolve o foco anterior ao fechar. */
export function retainModalFocus(dialog: HTMLElement): () => void {
  const previously = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  const initial = focusableInDialog(dialog)[0];
  initial?.focus();

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key !== "Tab") return;
    const items = focusableInDialog(dialog);
    if (items.length === 0) {
      event.preventDefault();
      return;
    }
    const first = items[0];
    const last = items[items.length - 1];
    const active = document.activeElement;
    const inside = active instanceof Node && dialog.contains(active);
    if (event.shiftKey && (!inside || active === first)) {
      event.preventDefault();
      last.focus();
      return;
    }
    if (!event.shiftKey && (!inside || active === last)) {
      event.preventDefault();
      first.focus();
    }
  };

  dialog.addEventListener("keydown", onKeyDown);
  return () => {
    dialog.removeEventListener("keydown", onKeyDown);
    if (previously && document.contains(previously)) previously.focus();
  };
}
