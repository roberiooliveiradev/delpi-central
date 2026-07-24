/**
 * Sessão de impressão única — evita dois `window.print()` (ex.: duplo clique
 * ou fallback de imagens após o usuário cancelar o primeiro diálogo).
 */

let scopedPrintInFlight = false;

export type ScopedWindowPrintOptions = {
  /** Classe aplicada em `document.documentElement` durante a impressão. */
  rootClassName?: string;
  /** Classe aplicada em `document.body` durante a impressão. */
  bodyClassName?: string;
  /** Dispara `resize` antes do print (layouts que recalculam no print). */
  dispatchResize?: boolean;
  /** Aguarda 2 frames (padrão) para o CSS de escopo aplicar. */
  deferFrames?: boolean;
};

/**
 * Imprime a janela atual no máximo uma vez até `afterprint` (ou timeout).
 * Usado por DocumentReader e botões "Imprimir" de página.
 */
export function printScopedWindow(options: ScopedWindowPrintOptions = {}): boolean {
  if (scopedPrintInFlight) return false;
  scopedPrintInFlight = true;

  const root = document.documentElement;
  const body = document.body;
  const rootClass = options.rootClassName?.trim();
  const bodyClass = options.bodyClassName?.trim();

  if (rootClass) root.classList.add(rootClass);
  if (bodyClass) body.classList.add(bodyClass);
  if (options.dispatchResize) {
    window.dispatchEvent(new Event("resize"));
  }

  let fallbackTimer: ReturnType<typeof window.setTimeout> | undefined;

  const cleanup = () => {
    if (rootClass) root.classList.remove(rootClass);
    if (bodyClass) body.classList.remove(bodyClass);
    if (fallbackTimer !== undefined) window.clearTimeout(fallbackTimer);
    fallbackTimer = undefined;
    scopedPrintInFlight = false;
    window.removeEventListener("afterprint", cleanup);
  };

  window.addEventListener("afterprint", cleanup);
  // Liberação de emergência se o navegador não emitir afterprint.
  fallbackTimer = window.setTimeout(cleanup, 60_000);

  const run = () => {
    try {
      window.focus();
      window.print();
    } catch {
      cleanup();
    }
  };

  if (options.deferFrames === false) {
    run();
  } else {
    requestAnimationFrame(() => {
      requestAnimationFrame(run);
    });
  }

  return true;
}

/** Agenda um único `print()` no target (janela/iframe de documento HTML). */
export function scheduleTargetWindowPrint(
  targetWindow: Window,
  onPrinted?: () => void,
): void {
  let started = false;
  let scheduleTimer: ReturnType<typeof window.setTimeout> | undefined;

  const clearSchedule = () => {
    if (scheduleTimer !== undefined) window.clearTimeout(scheduleTimer);
    scheduleTimer = undefined;
  };

  const trigger = () => {
    if (started || targetWindow.closed) return;
    started = true;
    clearSchedule();
    waitForImagesThenPrintOnce(targetWindow, onPrinted);
  };

  targetWindow.addEventListener("load", trigger, { once: true });
  scheduleTimer = window.setTimeout(trigger, 1_000);
}

function waitForImagesThenPrintOnce(
  targetWindow: Window,
  onPrinted?: () => void,
): void {
  const images = Array.from(targetWindow.document.images);
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
    onPrinted?.();
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
    if (image.complete) tryPrint();
    else {
      image.addEventListener("load", tryPrint, { once: true });
      image.addEventListener("error", tryPrint, { once: true });
    }
  }

  fallbackTimer = window.setTimeout(runPrint, 1_500);
}

/** Exposto só para testes — reseta o mutex de impressão da janela atual. */
export function __resetScopedPrintForTests(): void {
  scopedPrintInFlight = false;
}
