import { scheduleTargetWindowPrint } from "./printOnce";

export type PrintDelpiDocumentHtmlOptions = {
  iframeTitle?: string;
  /**
   * @deprecated Preferência por popup removida: popup/about:blank rouba foco e
   * o fallback iframe fullscreen (z-index alto) bloqueia o hotspot da sidebar
   * do portal até reload. Sempre usa iframe oculto no host.
   */
  preferPopup?: boolean;
};

const PRINT_FRAME_ATTR = "data-delpi-document-print-frame";

function removeStalePrintFrames(): void {
  document.querySelectorAll(`iframe[${PRINT_FRAME_ATTR}]`).forEach((node) => {
    node.remove();
  });
}

function printViaHiddenIframe(
  html: string,
  iframeTitle: string,
  onDone?: () => void,
): boolean {
  removeStalePrintFrames();

  const iframe = document.createElement("iframe");
  iframe.setAttribute(PRINT_FRAME_ATTR, "1");
  iframe.setAttribute("title", iframeTitle);
  iframe.setAttribute("aria-hidden", "true");
  iframe.setAttribute(
    "style",
    [
      "position:fixed",
      "left:0",
      "top:0",
      "width:0",
      "height:0",
      "border:0",
      "opacity:0",
      "pointer-events:none",
      "z-index:-1",
      "visibility:hidden",
    ].join(";"),
  );
  document.body.appendChild(iframe);

  const targetWindow = iframe.contentWindow;
  const doc = iframe.contentDocument ?? targetWindow?.document;

  if (!targetWindow || !doc) {
    iframe.remove();
    return false;
  }

  doc.open();
  doc.write(html);
  doc.close();

  const cleanup = () => {
    iframe.remove();
    try {
      window.focus();
    } catch {
      /* ignore */
    }
    onDone?.();
  };

  scheduleTargetWindowPrint(targetWindow, {
    onPrinted: cleanup,
    closeTargetAfterPrint: false,
  });

  return true;
}

/**
 * Imprime HTML via iframe oculto no host (um único diálogo).
 * Não usa `window.open` — evita overlay fullscreen e perda de foco da sidebar.
 */
export function printDelpiDocumentHtml(
  html: string,
  options?: PrintDelpiDocumentHtmlOptions,
): boolean {
  void options?.preferPopup;
  const iframeTitle = options?.iframeTitle || "Documento DELPI";
  return printViaHiddenIframe(html, iframeTitle);
}
