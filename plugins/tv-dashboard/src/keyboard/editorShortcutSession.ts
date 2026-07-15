export type EditorShortcutPhase = "capture" | "bubble";

export type EditorShortcutResult = {
  /** Se true, a session chama preventDefault (+ stopPropagation na captura). */
  handled?: boolean;
};

export type EditorShortcutHandler = (event: KeyboardEvent) => EditorShortcutResult | void;

type RegisteredHandler = {
  id: string;
  phase: EditorShortcutPhase;
  priority: number;
  handler: EditorShortcutHandler;
};

/**
 * Sessão única de atalhos do editor TV.
 *
 * Regras:
 * - Um listener por fase no `window` (sem duplicar registro).
 * - Só `preventDefault`/`stopPropagation` quando um handler retorna `{ handled: true }`.
 * - `setEnabled(false)` desliga tudo (ex.: editor montado sob prévia).
 * - `dispose()` remove listeners — chamar no unmount do editor.
 */
export class EditorShortcutSession {
  private enabled = true;
  private disposed = false;
  private handlers: RegisteredHandler[] = [];
  private attached = false;
  private readonly onCapture = (event: KeyboardEvent) => this.dispatch(event, "capture");
  private readonly onBubble = (event: KeyboardEvent) => this.dispatch(event, "bubble");

  setEnabled(next: boolean): void {
    if (this.disposed) return;
    this.enabled = next;
  }

  isEnabled(): boolean {
    return this.enabled && !this.disposed;
  }

  isDisposed(): boolean {
    return this.disposed;
  }

  register(
    id: string,
    handler: EditorShortcutHandler,
    options?: { phase?: EditorShortcutPhase; priority?: number },
  ): () => void {
    if (this.disposed) return () => undefined;
    this.handlers = this.handlers.filter((entry) => entry.id !== id);
    this.handlers.push({
      id,
      phase: options?.phase ?? "bubble",
      priority: options?.priority ?? 0,
      handler,
    });
    this.ensureAttached();
    return () => {
      this.handlers = this.handlers.filter((entry) => entry.id !== id);
      this.detachIfIdle();
    };
  }

  dispose(): void {
    this.disposed = true;
    this.handlers = [];
    this.detach();
  }

  private ensureAttached(): void {
    if (this.attached || this.disposed) return;
    window.addEventListener("keydown", this.onCapture, true);
    window.addEventListener("keydown", this.onBubble, false);
    this.attached = true;
  }

  private detachIfIdle(): void {
    if (this.handlers.length === 0) this.detach();
  }

  private detach(): void {
    if (!this.attached) return;
    window.removeEventListener("keydown", this.onCapture, true);
    window.removeEventListener("keydown", this.onBubble, false);
    this.attached = false;
  }

  private dispatch(event: KeyboardEvent, phase: EditorShortcutPhase): void {
    if (!this.isEnabled()) return;
    const ranked = this.handlers
      .filter((entry) => entry.phase === phase)
      .sort((left, right) => right.priority - left.priority);
    for (const entry of ranked) {
      const result = entry.handler(event);
      if (result?.handled) {
        event.preventDefault();
        if (phase === "capture") event.stopPropagation();
        return;
      }
    }
  }
}

let sharedSession: EditorShortcutSession | null = null;

/** Sessão compartilhada do MFE — criada sob demanda; reincarna após dispose. */
export function getEditorShortcutSession(): EditorShortcutSession {
  if (!sharedSession || sharedSession.isDisposed()) {
    sharedSession = new EditorShortcutSession();
  }
  return sharedSession;
}

/** Descarta listeners e zera a sessão (unmount do editor / plugin). */
export function disposeEditorShortcutSession(): void {
  sharedSession?.dispose();
  sharedSession = null;
}
