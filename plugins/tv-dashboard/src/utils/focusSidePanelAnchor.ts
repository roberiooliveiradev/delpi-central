/**
 * Após abrir a aba Dados do painel lateral, espera o React commitar o DOM
 * e rola até o âncora (fonte / colunas / eixos).
 */
export function focusSidePanelAnchor(anchorId: string): void {
  const scroll = () => {
    const node = document.getElementById(anchorId);
    if (!node) return false;
    const details = node.closest("details");
    if (details) {
      details.setAttribute("open", "");
    }
    node.scrollIntoView({ block: "nearest", behavior: "smooth" });
    return true;
  };

  requestAnimationFrame(() => {
    if (scroll()) return;
    window.setTimeout(() => {
      requestAnimationFrame(() => {
        scroll();
      });
    }, 50);
  });
}
