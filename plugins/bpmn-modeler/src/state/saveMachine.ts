/**
 * Save state machine — contrato FROZEN (P4 §12/§13).
 *
 * states: LOADING | CLEAN | DIRTY | SAVING | SAVE_FAILED | CONFLICT
 * modo ortogonal: READ_ONLY (substitui estados de save; nunca DIRTY)
 *
 * Dirty tracking é branch-aware: identidade de estado por tokens,
 * nunca profundidade de stack (undo→undo→novas edições ≠ mesmo token).
 */

export type SaveState =
  | "LOADING"
  | "CLEAN"
  | "DIRTY"
  | "SAVING"
  | "SAVE_FAILED"
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

  /** Chamado pelo adapter após import/load inicial. */
  markLoaded(): void {
    this.stateTokens = [newToken()];
    this.cursor = 0;
    this.savedToken = this.stateTokens[0];
  }

  /** commandStack.changed → execute|undo|redo|clear (API pública do vendor). */
  onCommand(trigger: SaveTrigger): boolean {
    if (this.state !== "CLEAN" && this.state !== "DIRTY") return this.dirty();
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
    this.state = this.dirty() ? "DIRTY" : "CLEAN";
    return this.dirty();
  }

  dirty(): boolean {
    if (this.cursor < 0 || this.savedToken === null) return false;
    return this.stateTokens[this.cursor] !== this.savedToken;
  }

  /** Somente após read-back verificado pelo backend. */
  markSaved(): void {
    if (this.cursor >= 0) {
      this.savedToken = this.stateTokens[this.cursor];
      this.state = "CLEAN";
    }
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
        if (this.state === "DIRTY") this.state = "SAVING";
        break;
      case "SAVE_VERIFIED":
        if (this.state === "SAVING") this.markSaved();
        break;
      case "VALIDATION_BLOCKED":
        if (this.state === "SAVING") this.state = "DIRTY";
        break;
      case "VERSION_CONFLICT":
        if (this.state === "SAVING") this.state = "CONFLICT";
        break;
      case "SAVE_FAILED":
        if (this.state === "SAVING") this.state = "SAVE_FAILED";
        break;
      case "RETRY_SAVE":
        if (this.state === "SAVE_FAILED") this.state = "SAVING";
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
    return this.state === "DIRTY" || this.state === "SAVE_FAILED";
  }
}
