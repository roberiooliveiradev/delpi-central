/**
 * Agenda impressão de HTML em janela/iframe.
 * Garante no máximo um `print()` por documento — o fallback de imagens
 * não pode reabrir o diálogo depois que o usuário cancelou o primeiro.
 */
function waitForImagesThenPrint(targetWindow: Window, onDone?: () => void): void {
  const doc = targetWindow.document;
  const images = Array.from(doc.images);
  let printed = false;
  let readyTimer: ReturnType<typeof window.setTimeout> | undefined;
  let fallbackTimer: ReturnType<typeof window.setTimeout> | undefined;

  const clearTimers = () => {
    if (readyTimer !== undefined) window.clearTimeout(readyTimer);
    if (fallbackTimer !== undefined) window.clearTimeout(fallbackTimer);
    readyTimer = undefined;
    fallbackTimer = undefined;
  };

  const runPrint = () => {
    if (printed || targetWindow.closed) return;
    printed = true;
    clearTimers();
    targetWindow.focus();
    targetWindow.scrollTo(0, 0);
    targetWindow.print();
    onDone?.();
  };

  if (images.length === 0) {
    readyTimer = window.setTimeout(runPrint, 100);
    return;
  }

  let ready = 0;

  const tryPrint = () => {
    ready += 1;
    if (ready >= images.length) {
      readyTimer = window.setTimeout(runPrint, 150);
    }
  };

  for (const image of images) {
    if (image.complete) {
      tryPrint();
    } else {
      image.addEventListener("load", tryPrint, { once: true });
      image.addEventListener("error", tryPrint, { once: true });
    }
  }

  // Só dispara se as imagens não ficarem prontas a tempo — nunca como 2º print.
  fallbackTimer = window.setTimeout(runPrint, 1_500);
}

function scheduleDelpiDocumentPrint(targetWindow: Window, onDone?: () => void): void {
  let started = false;

  const triggerPrint = () => {
    if (started || targetWindow.closed) {
      return;
    }

    started = true;
    waitForImagesThenPrint(targetWindow, onDone);
  };

  targetWindow.addEventListener("load", triggerPrint, { once: true });
  window.setTimeout(triggerPrint, 1_000);
}

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

  scheduleDelpiDocumentPrint(targetWindow, () => {
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
    scheduleDelpiDocumentPrint(printWindow);
    return true;
  }

  return printViaIframe(html, iframeTitle);
}
