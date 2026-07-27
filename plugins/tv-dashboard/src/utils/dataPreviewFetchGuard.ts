/** Timeout padrão do preview-block no editor (acima do gateway 30s + margem). */
export const DATA_PREVIEW_BLOCK_TIMEOUT_MS = 60_000;

export const DATA_PREVIEW_TIMEOUT_MESSAGE =
  "Tempo esgotado ao carregar esta fonte. Tente Atualizar visual.";

export function isAbortError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  const name = "name" in err ? String((err as { name: unknown }).name) : "";
  return name === "AbortError" || name === "TimeoutError";
}

/**
 * AbortSignal que dispara após `timeoutMs`, opcionalmente ligado a um signal pai (lote).
 * Retorna cleanup para limpar o timer.
 */
export function createLinkedTimeoutSignal(
  timeoutMs: number,
  parent?: AbortSignal | null,
): { signal: AbortSignal; cleanup: () => void } {
  const controller = new AbortController();
  let cleaned = false;

  const abortFromParent = () => {
    if (!controller.signal.aborted) {
      controller.abort(parent?.reason ?? new DOMException("Aborted", "AbortError"));
    }
  };

  if (parent?.aborted) {
    abortFromParent();
  } else if (parent) {
    parent.addEventListener("abort", abortFromParent, { once: true });
  }

  const timer =
    typeof window !== "undefined"
      ? window.setTimeout(() => {
          if (!controller.signal.aborted) {
            controller.abort(new DOMException(DATA_PREVIEW_TIMEOUT_MESSAGE, "TimeoutError"));
          }
        }, timeoutMs)
      : null;

  const cleanup = () => {
    if (cleaned) return;
    cleaned = true;
    if (timer != null) window.clearTimeout(timer);
    parent?.removeEventListener("abort", abortFromParent);
  };

  return { signal: controller.signal, cleanup };
}

export function resolvePreviewAbortMessage(err: unknown, superseded: boolean): string | null {
  if (superseded) return null;
  if (!isAbortError(err)) {
    return err instanceof Error ? err.message : "Falha ao carregar dados.";
  }
  const message = err instanceof Error ? err.message : "";
  if (message && message !== "Aborted" && message !== "The operation was aborted.") {
    return message;
  }
  return DATA_PREVIEW_TIMEOUT_MESSAGE;
}

/** Rótulo curto da fonte para a barra de progresso. */
export function resolveDataSourceProgressLabel(block: {
  id: string;
  title?: unknown;
  dataBinding?: { operationId?: string } | null;
}): string {
  if (typeof block.title === "string" && block.title.trim()) return block.title.trim();
  const operationId = block.dataBinding?.operationId?.trim();
  if (operationId) return operationId;
  return block.id;
}

export function formatDataPreviewLoadingLabel(args: {
  completed: number;
  total: number;
  pendingLabels: readonly string[];
}): string {
  const { completed, total, pendingLabels } = args;
  if (total <= 0) return "Carregando dados";
  if (total === 1) {
    const only = pendingLabels[0] ?? "fonte";
    return `Carregando ${only}`;
  }
  const pending = pendingLabels[0];
  if (pending && completed < total) {
    return `Carregando ${completed}/${total}: ${pending}`;
  }
  return `Carregando ${completed}/${total} fontes`;
}
