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

export type RealtimeSocketOptions = {
  /** Devolve a URL pronta (token já embutido) ou `null` quando ainda
   * não há credencial — nesse caso reconecta depois. */
  buildUrl: () => string | null;
  pingMs?: number;
  reconnectMs?: number;
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
  private state: RealtimeSocketState = { connected: false, error: null };

  constructor(options: RealtimeSocketOptions) {
    this.options = options;
  }

  getState(): RealtimeSocketState {
    return this.state;
  }

  start(): void {
    if (!this.stopped) return;
    this.stopped = false;
    this.connect();
  }

  stop(): void {
    this.stopped = true;
    this.clearTimers();
    this.socket?.close();
    this.socket = null;
    this.setState({ connected: false, error: null });
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
    }, this.options.reconnectMs ?? DEFAULT_RECONNECT_MS);
  }

  private connect(): void {
    this.clearTimers();
    this.socket?.close();

    const url = this.options.buildUrl();
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

    socket.onopen = () => {
      if (this.stopped) return;
      this.setState({ connected: true, error: null });
      for (const payload of this.desired) {
        socket.send(payload);
      }
      this.pingTimer = window.setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send("ping");
        }
      }, this.options.pingMs ?? DEFAULT_PING_MS);
    };

    socket.onmessage = (message) => {
      if (typeof message.data === "string") {
        this.options.onMessage(message.data);
      }
    };

    socket.onclose = () => {
      if (this.stopped) return;
      this.setState({ connected: false, error: null });
      this.clearTimers();
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
