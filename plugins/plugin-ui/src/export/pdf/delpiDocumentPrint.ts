import { scheduleTargetWindowPrint } from "./printOnce";

function printViaIframe(html: string, iframeTitle: string, onDone?: () => void): boolean {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("title", iframeTitle);
  iframe.setAttribute(
    "style",
    [
      "position:fixed",
      "inset:0",
      "width:100%",
      "height:100%",
      "border:0",
      "z-index:99999",
      "background:#ffffff",
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

  scheduleTargetWindowPrint(targetWindow, () => {
    window.setTimeout(() => {
      iframe.remove();
      onDone?.();
    }, 1_000);
  });

  return true;
}

/** Imprime HTML: janela nova se pop-up permitido; senão iframe. Um único diálogo. */
export function printDelpiDocumentHtml(
  html: string,
  options?: { iframeTitle?: string },
): boolean {
  const iframeTitle = options?.iframeTitle || "Documento DELPI";
  const printWindow = window.open("", "_blank");

  if (printWindow) {
    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
    scheduleTargetWindowPrint(printWindow);
    return true;
  }

  return printViaIframe(html, iframeTitle);
}
