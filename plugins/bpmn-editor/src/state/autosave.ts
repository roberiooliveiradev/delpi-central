/**
 * Autosave do Working Copy — persiste o artefato mutável, nunca cria
 * Revision (checkpoint imutável segue contrato explícito do domínio).
 *
 * Garantias:
 * - debounce/coalescing: bursts de commandStack viram um único write;
 * - single-flight: um write por vez; edições in-flight re-agendam pelo
 *   token branch-aware da SaveMachine (latest state wins);
 * - "Salvo" só após WRITE → AUTHORITATIVE READ-BACK → VERIFY;
 * - falha de rede → OFFLINE (retry no evento `online` ou nova edição);
 * - 401 → pedido de refresh ao host (`requestTokenRefresh`) + 1 retry;
 *   persistindo → SESSION_EXPIRED; 403 → READ_ONLY (fail closed);
 *   CONFLICT (409/412) → CONFLICT, nunca last-write-wins silencioso.
 */

import { BpmnDocumentError } from "../host/types";
import type { SaveMachine, SaveState } from "./saveMachine";

export const AUTOSAVE_DEBOUNCE_MS = 1500;

export type AutosaveDeps = {
  machine: SaveMachine;
  /** editável + adapter montado; false em preview/read-only/unmount. */
  canAutosave: () => boolean;
  exportXml: () => Promise<string>;
  write: (xml: string, expectedVersion: number) => Promise<{ version: number }>;
  readBack: () => Promise<{ xml: string; version: number }>;
  getVersion: () => number;
  setVersion: (v: number) => void;
  /** Pede refresh ao host (portal AppHost → DELPI_REFRESH_REQUEST). */
  requestTokenRefresh: () => Promise<boolean>;
  emit: (state: SaveState) => void;
  onValidationBlocked?: (err: BpmnDocumentError) => void;
  onVerificationFailed?: () => void;
  debounceMs?: number;
};

const SAVEABLE: SaveState[] = [
  "DIRTY",
  "SAVE_FAILED",
  "OFFLINE",
  "SESSION_EXPIRED",
];

export class AutosaveController {
  private timer: ReturnType<typeof setTimeout> | null = null;
  private running = false;
  private runPromise: Promise<void> | null = null;
  private disposed = false;
  private readonly deps: AutosaveDeps;
  private readonly debounceMs: number;
  private readonly onlineHandler = () => this.onOnline();

  constructor(deps: AutosaveDeps) {
    this.deps = deps;
    this.debounceMs = deps.debounceMs ?? AUTOSAVE_DEBOUNCE_MS;
    if (typeof window !== "undefined") {
      window.addEventListener("online", this.onlineHandler);
    }
  }

  /** commandStack.changed → agenda write coalesced do estado mais novo. */
  notifyCommand(): void {
    if (this.disposed || !this.deps.canAutosave()) return;
    if (!this.deps.machine.dirty()) return;
    if (this.running) return; // loop re-avalia dirty() ao fim do write
    if (!SAVEABLE.includes(this.deps.machine.state)) return;
    this.schedule();
  }

  /** Write imediato (Ctrl+S, retry, guard de navegação). */
  async flush(): Promise<boolean> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.runPromise) await this.runPromise;
    if (
      this.deps.machine.dirty() &&
      this.deps.canAutosave() &&
      SAVEABLE.includes(this.deps.machine.state)
    ) {
      await this.run();
    }
    return !this.deps.machine.dirty();
  }

  dispose(): void {
    this.disposed = true;
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
    if (typeof window !== "undefined") {
      window.removeEventListener("online", this.onlineHandler);
    }
  }

  private onOnline(): void {
    if (this.disposed) return;
    if (this.deps.machine.state === "OFFLINE" && this.deps.machine.dirty()) {
      void this.run();
    }
  }

  private schedule(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => {
      this.timer = null;
      void this.run();
    }, this.debounceMs);
  }

  private run(): Promise<void> {
    if (this.runPromise) return this.runPromise;
    const work = (async () => {
      try {
        while (
          this.deps.machine.dirty() &&
          this.deps.canAutosave() &&
          SAVEABLE.includes(this.deps.machine.state)
        ) {
          if (!(await this.saveOnce())) break;
        }
      } finally {
        this.running = false;
        this.runPromise = null;
      }
    })();
    this.running = true;
    this.runPromise = work;
    return work;
  }

  /** WRITE → AUTHORITATIVE READ-BACK → VERIFY. `false` = terminal failure. */
  private async saveOnce(): Promise<boolean> {
    const d = this.deps;
    const m = d.machine;
    m.dispatch({ type: "SAVE_REQUEST" });
    if (m.state !== "SAVING") return false;
    d.emit(m.state);

    try {
      const candidate = await d.exportXml();
      const outcome = await this.writeWithAuthRetry(candidate);
      const read = await d.readBack();
      if (read.xml !== candidate) {
        d.onVerificationFailed?.();
        m.dispatch({ type: "SAVE_FAILED" });
        d.emit(m.state);
        return false;
      }
      d.setVersion(outcome.version);
      m.dispatch({ type: "SAVE_VERIFIED" });
      d.emit(m.state);
      return true;
    } catch (err) {
      this.classify(err);
      d.emit(m.state);
      return false;
    }
  }

  /** 401 → refresh via host + 1 retry (contrato shared-auth; nunca cego). */
  private async writeWithAuthRetry(
    xml: string,
  ): Promise<{ version: number }> {
    try {
      return await this.deps.write(xml, this.deps.getVersion());
    } catch (err) {
      if (err instanceof BpmnDocumentError && err.status === 401) {
        await this.deps.requestTokenRefresh();
        return await this.deps.write(xml, this.deps.getVersion());
      }
      throw err;
    }
  }

  private classify(err: unknown): void {
    const m = this.deps.machine;
    if (err instanceof BpmnDocumentError) {
      if (err.code === "VALIDATION_BLOCKED") {
        this.deps.onValidationBlocked?.(err);
        m.dispatch({ type: "VALIDATION_BLOCKED" });
      } else if (err.status === 401) {
        m.dispatch({ type: "AUTH_EXPIRED" });
      } else if (err.status === 403) {
        // permissão revogada → fail closed, sem autosave silencioso
        m.dispatch({ type: "SET_READ_ONLY" });
      } else if (err.code === "CONFLICT") {
        m.dispatch({ type: "VERSION_CONFLICT" });
      } else {
        m.dispatch({ type: "SAVE_FAILED" });
      }
    } else if (err instanceof TypeError) {
      // fetch network failure (offline, DNS, CORS) — nunca AbortError
      m.dispatch({ type: "NETWORK_OFFLINE" });
    } else {
      m.dispatch({ type: "SAVE_FAILED" });
    }
  }
}
