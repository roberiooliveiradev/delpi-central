/** ENG-REALTIME-01 — transporte WebSocket neutro reutilizável.
 *
 * Responsabilidades: conexão, heartbeat, reconnect com retry fixo,
 * assinaturas desejadas com rejoin automático e limpeza no dispose.
 * NÃO conhece token, AuthZ, domínio ou payload de negócio — o consumidor
 * fornece `buildUrl()` e interpreta as mensagens.
 */

export type RealtimeSocketState = {
  connected: boolean;
  error: string | null;
};

export type RealtimeConnectionStatus =
  | "idle"
  | "connecting"
  | "open"
  | "reconnecting"
  | "unavailable"
  | "closed";

export type RealtimeReconnectOptions = {
  mode?: "fixed" | "exponential";
  baseMs?: number;
  maxMs?: number;
  jitter?: boolean;
};

export type RealtimeCloseContext = {
  closeCode: number;
  attempt: number;
  sameUrl: boolean;
};

export type RealtimeSocketOptions = {
  /** Devolve a URL pronta (token já embutido) ou `null` quando ainda
   * não há credencial — nesse caso reconecta depois. */
  buildUrl: () => string | null;
  /** Se existir, é chamada a cada tentativa. Pode devolver uma Promise. */
  resolveUrl?: () => string | null | Promise<string | null>;
  pingMs?: number;
  reconnectMs?: number;
  /** Sem esta opção o reconnect continua fixo em 4s. */
  reconnect?: RealtimeReconnectOptions;
  shouldReconnect?: (ctx: RealtimeCloseContext) => boolean;
  /** Default true: o cliente já reenvia as salas desejadas no open. */
  resubscribeOnReconnect?: boolean;
  onResync?: () => void;
  onMessage: (raw: string) => void;
  onStateChange?: (state: RealtimeSocketState) => void;
};

const DEFAULT_PING_MS = 25_000;
const DEFAULT_RECONNECT_MS = 4_000;

export class RealtimeSocketClient {
  private socket: WebSocket | null = null;
  private pingTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private stopped = true;
  private readonly desired = new Set<string>();
  private readonly options: RealtimeSocketOptions;
  private readonly statusListeners = new Set<(status: RealtimeConnectionStatus) => void>();
  private readonly messageListeners = new Set<(raw: string) => void>();
  private state: RealtimeSocketState = { connected: false, error: null };
  private status: RealtimeConnectionStatus = "idle";
  private attempt = 0;
  private openedOnce = false;
  private lastUrl: string | null = null;

  constructor(options: RealtimeSocketOptions) {
    this.options = options;
  }

  getState(): RealtimeSocketState {
    return this.state;
  }

  getStatus(): RealtimeConnectionStatus {
    return this.status;
  }

  onStatusChange(listener: (status: RealtimeConnectionStatus) => void): () => void {
    this.statusListeners.add(listener);
    return () => {
      this.statusListeners.delete(listener);
    };
  }

  addMessageListener(listener: (raw: string) => void): () => void {
    this.messageListeners.add(listener);
    return () => {
      this.messageListeners.delete(listener);
    };
  }

  start(): void {
    if (!this.stopped) return;
    this.stopped = false;
    this.setStatus("connecting");
    this.connect();
  }

  stop(): void {
    this.stopped = true;
    this.clearTimers();
    this.socket?.close();
    this.socket = null;
    this.setState({ connected: false, error: null });
    this.setStatus("closed");
  }

  /** Marca assinatura desejada e envia se o socket estiver aberto. */
  subscribe(payload: string): void {
    if (!payload) return;
    this.desired.add(payload);
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(payload);
    }
  }

  unsubscribe(payload: string): void {
    if (!payload) return;
    this.desired.delete(payload);
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(payload);
    }
  }

  private setState(next: RealtimeSocketState): void {
    this.state = next;
    this.options.onStateChange?.(next);
  }

  private setStatus(next: RealtimeConnectionStatus): void {
    this.status = next;
    for (const listener of this.statusListeners) listener(next);
  }

  private peekUrl(): string | null {
    const resolved = this.options.resolveUrl?.();
    if (resolved && typeof (resolved as Promise<string | null>).then === "function") {
      return this.lastUrl;
    }
    if (resolved !== undefined) return resolved as string | null;
    return this.options.buildUrl();
  }

  private delayMs(): number {
    const mode = this.options.reconnect?.mode ?? "fixed";
    if (mode !== "exponential") {
      return this.options.reconnectMs ?? DEFAULT_RECONNECT_MS;
    }
    const base = this.options.reconnect?.baseMs ?? 1_000;
    const max = this.options.reconnect?.maxMs ?? 30_000;
    const exp = Math.min(max, base * 2 ** Math.max(0, this.attempt - 1));
    if (this.options.reconnect?.jitter === false) return exp;
    const spread = exp * (0.5 + Math.random() * 0.5);
    return Math.min(max, Math.max(base, spread));
  }

  private clearTimers(): void {
    if (this.pingTimer != null) {
      window.clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    if (this.reconnectTimer != null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.stopped || this.reconnectTimer != null) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.delayMs());
  }

  private connect(): void {
    this.clearTimers();
    this.socket?.close();
    const resolved = this.options.resolveUrl?.();
    if (resolved && typeof (resolved as Promise<string | null>).then === "function") {
      void (resolved as Promise<string | null>).then((url) => {
        if (this.stopped) return;
        this.openSocket(url);
      });
      return;
    }
    const url =
      resolved === undefined ? this.options.buildUrl() : (resolved as string | null);
    this.openSocket(url);
  }

  private openSocket(url: string | null): void {
    if (!url) {
      this.setState({ connected: false, error: "not_ready" });
      this.scheduleReconnect();
      return;
    }

    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      this.setState({ connected: false, error: "connect_failed" });
      this.scheduleReconnect();
      return;
    }
    this.socket = socket;

    this.lastUrl = url;
    const reconnecting = this.openedOnce;

    socket.onopen = () => {
      if (this.stopped) return;
      this.setState({ connected: true, error: null });
      this.setStatus("open");
      const resubscribe = this.options.resubscribeOnReconnect !== false;
      if (!reconnecting || resubscribe) {
        for (const payload of this.desired) {
          socket.send(payload);
        }
      }
      if (reconnecting) this.options.onResync?.();
      this.openedOnce = true;
      this.attempt = 0;
      this.pingTimer = window.setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send("ping");
        }
      }, this.options.pingMs ?? DEFAULT_PING_MS);
    };

    socket.onmessage = (message) => {
      if (typeof message.data !== "string") return;
      this.options.onMessage(message.data);
      for (const listener of this.messageListeners) listener(message.data);
    };

    socket.onclose = (event?: { code?: number }) => {
      if (this.stopped) return;
      this.setState({ connected: false, error: null });
      this.clearTimers();
      this.attempt += 1;
      const code = event?.code ?? 1006;
      const nextUrl = this.peekUrl();
      const sameUrl = nextUrl != null && nextUrl === url;
      const allow = this.options.shouldReconnect?.({
        closeCode: code,
        attempt: this.attempt,
        sameUrl,
      }) ?? true;
      if (!allow) {
        this.setStatus("unavailable");
        return;
      }
      this.setStatus("reconnecting");
      this.scheduleReconnect();
    };

    socket.onerror = () => {
      this.setState({
        connected: false,
        error: "connection_error",
      });
    };
  }
}

/** Dispatcher com dedupe por `eventId` e debounce — evita refetch
 * múltiplo em rajadas de eventos do mesmo recurso. */
export function createEventDispatcher(options: {
  debounceMs?: number;
  dedupeWindowMs?: number;
  onFlush: (events: unknown[]) => void;
}): (event: unknown) => void {
  const debounceMs = options.debounceMs ?? 400;
  const dedupeWindowMs = options.dedupeWindowMs ?? 10_000;
  const seen = new Map<string, number>();
  const pending: unknown[] = [];
  let timer: number | null = null;

  return (event: unknown) => {
    const id =
      event && typeof event === "object"
        ? String((event as Record<string, unknown>).eventId || "")
        : "";
    if (id) {
      const now = Date.now();
      const last = seen.get(id) || 0;
      if (now - last < dedupeWindowMs) return;
      seen.set(id, now);
      for (const [key, ts] of seen) {
        if (now - ts > dedupeWindowMs) seen.delete(key);
      }
    }
    pending.push(event);
    if (timer != null) window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      timer = null;
      const batch = pending.splice(0, pending.length);
      options.onFlush(batch);
    }, debounceMs);
  };
}
