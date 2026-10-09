/**
 * Save state machine — contrato FROZEN (P4 §12/§13) + autosave.
 *
 * states: LOADING | CLEAN | DIRTY | SAVING | SAVE_FAILED | OFFLINE |
 *         SESSION_EXPIRED | CONFLICT
 * modo ortogonal: READ_ONLY (substitui estados de save; nunca DIRTY)
 *
 * Dirty tracking é branch-aware: identidade de estado por tokens,
 * nunca profundidade de stack (undo→undo→novas edições ≠ mesmo token).
 * Comandos durante SAVING continuam registrados: SAVE_VERIFIED marca
 * como salvo o token capturado no SAVE_REQUEST, nunca o cursor atual —
 * edições in-flight voltam a DIRTY para o próximo autosave.
 */

export type SaveState =
  | "LOADING"
  | "CLEAN"
  | "DIRTY"
  | "SAVING"
  | "SAVE_FAILED"
  | "OFFLINE"
  | "SESSION_EXPIRED"
  | "CONFLICT"
  | "READ_ONLY";

export type SaveTrigger =
  | "execute"
  | "undo"
  | "redo"
  | "clear";

export type SaveEvent =
  | { type: "LOAD_OK"; editable: boolean }
  | { type: "LOAD_FAILED" }
  | { type: "COMMAND"; trigger: SaveTrigger }
  | { type: "SAVE_REQUEST" }
  | { type: "SAVE_VERIFIED" }
  | { type: "VALIDATION_BLOCKED" }
  | { type: "VERSION_CONFLICT" }
  | { type: "SAVE_FAILED" }
  | { type: "NETWORK_OFFLINE" }
  | { type: "AUTH_EXPIRED" }
  | { type: "RETRY_SAVE" }
  | { type: "DISCARD_AND_RELOAD" }
  | { type: "CONFLICT_RELOAD" }
  | { type: "SET_READ_ONLY" };

let tokenCounter = 0;
export function newToken(): string {
  tokenCounter += 1;
  return `t${tokenCounter}-${Date.now()}`;
}

export class SaveMachine {
  state: SaveState = "LOADING";
  private stateTokens: string[] = [];
  private cursor = -1;
  private savedToken: string | null = null;
  /** Token do estado capturado no início do write in-flight. */
  private pendingSaveToken: string | null = null;

  /** Chamado pelo adapter após import/load inicial. */
  markLoaded(): void {
    this.stateTokens = [newToken()];
    this.cursor = 0;
    this.savedToken = this.stateTokens[0];
  }

  /** commandStack.changed → execute|undo|redo|clear (API pública do vendor). */
  onCommand(trigger: SaveTrigger): boolean {
    if (this.cursor < 0) return this.dirty();
    switch (trigger) {
      case "execute":
        this.stateTokens = this.stateTokens.slice(0, this.cursor + 1);
        this.stateTokens.push(newToken());
        this.cursor += 1;
        break;
      case "undo":
        if (this.cursor > 0) this.cursor -= 1;
        break;
      case "redo":
        if (this.cursor < this.stateTokens.length - 1) this.cursor += 1;
        break;
      case "clear":
        this.markLoaded();
        break;
    }
    // durante SAVING/SAVE_FAILED/etc. o estado permanece — dirty() segue
    // calculável via tokens e decide o retomar do autosave.
    if (this.state === "CLEAN" || this.state === "DIRTY") {
      this.state = this.dirty() ? "DIRTY" : "CLEAN";
    }
    return this.dirty();
  }

  dirty(): boolean {
    if (this.cursor < 0 || this.savedToken === null) return false;
    return this.stateTokens[this.cursor] !== this.savedToken;
  }

  /** Somente após read-back verificado pelo backend. */
  markSaved(token?: string | null): void {
    if (this.cursor < 0) return;
    this.savedToken = token ?? this.stateTokens[this.cursor];
  }

  private beginSave(): boolean {
    const saveable =
      this.state === "DIRTY" ||
      this.state === "SAVE_FAILED" ||
      this.state === "OFFLINE" ||
      this.state === "SESSION_EXPIRED";
    if (!saveable || !this.dirty()) return false;
    this.pendingSaveToken = this.stateTokens[this.cursor];
    this.state = "SAVING";
    return true;
  }

  private endSave(): void {
    this.pendingSaveToken = null;
  }

  dispatch(event: SaveEvent): SaveState {
    switch (event.type) {
      case "LOAD_OK":
        this.state = event.editable ? "CLEAN" : "READ_ONLY";
        if (event.editable) this.markLoaded();
        break;
      case "LOAD_FAILED":
        break;
      case "COMMAND":
        this.onCommand(event.trigger);
        break;
      case "SAVE_REQUEST":
      case "RETRY_SAVE":
        this.beginSave();
        break;
      case "SAVE_VERIFIED":
        if (this.state === "SAVING") {
          // marca como salvo o token do início do write: edições feitas
          // durante o save permanecem DIRTY para o próximo autosave.
          this.markSaved(this.pendingSaveToken);
          this.endSave();
          this.state = this.dirty() ? "DIRTY" : "CLEAN";
        }
        break;
      case "VALIDATION_BLOCKED":
        if (this.state === "SAVING") {
          this.endSave();
          this.state = "DIRTY";
        }
        break;
      case "VERSION_CONFLICT":
        if (this.state === "SAVING") {
          this.endSave();
          this.state = "CONFLICT";
        }
        break;
      case "SAVE_FAILED":
        if (this.state === "SAVING") {
          this.endSave();
          this.state = "SAVE_FAILED";
        }
        break;
      case "NETWORK_OFFLINE":
        if (this.state === "SAVING") {
          this.endSave();
          this.state = "OFFLINE";
        }
        break;
      case "AUTH_EXPIRED":
        if (this.state === "SAVING") {
          this.endSave();
          this.state = "SESSION_EXPIRED";
        }
        break;
      case "DISCARD_AND_RELOAD":
        if (this.state === "SAVE_FAILED") this.state = "READ_ONLY";
        break;
      case "CONFLICT_RELOAD":
        if (this.state === "CONFLICT") this.state = "READ_ONLY";
        break;
      case "SET_READ_ONLY":
        this.state = "READ_ONLY";
        break;
    }
    return this.state;
  }

  canEdit(): boolean {
    return this.state === "CLEAN" || this.state === "DIRTY";
  }

  canSave(): boolean {
    return (
      this.dirty() &&
      (this.state === "DIRTY" ||
        this.state === "SAVE_FAILED" ||
        this.state === "OFFLINE" ||
        this.state === "SESSION_EXPIRED")
    );
  }
}
