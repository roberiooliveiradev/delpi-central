/** ENG-REALTIME-01 — contrato do transporte neutro: heartbeat,
 * reconnect, rejoin de assinaturas, dedupe e debounce. */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  RealtimeSocketClient,
  createEventDispatcher,
} from "./realtimeSocket";

class FakeWebSocket {
  static OPEN = 1;
  static instances: FakeWebSocket[] = [];

  readyState = 0;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  closed = false;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  emitClose(code = 1006) {
    this.readyState = 3;
    this.onclose?.({ code });
  }

  emitMessage(data: string) {
    this.onmessage?.({ data });
  }

  send(payload: string) {
    this.sent.push(payload);
  }

  close() {
    this.closed = true;
    if (!this.readyState) return;
    this.readyState = 3;
    this.onclose?.();
  }
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  vi.useFakeTimers();
  vi.stubGlobal("WebSocket", FakeWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function makeClient(overrides: Partial<Parameters<typeof RealtimeSocketClient.prototype.start>> extends never ? object : object = {}) {
  return new RealtimeSocketClient({
    buildUrl: () => "wss://h/v1/realtime/ws?token=t&client_id=c",
    onMessage: () => undefined,
    ...(overrides as object),
  });
}

describe("RealtimeSocketClient", () => {
  it("conecta, envia assinaturas desejadas no open e rejoin após reconnect", () => {
    const messages: string[] = [];
    const client = new RealtimeSocketClient({
      buildUrl: () => "wss://h/ws?token=t&client_id=c",
      onMessage: (raw) => messages.push(raw),
    });
    client.start();
    client.subscribe('{"type":"subscribe","resourceId":"r-1"}');

    const first = FakeWebSocket.instances[0];
    first.open();
    expect(first.sent).toContain(
      '{"type":"subscribe","resourceId":"r-1"}',
    );

    first.emitClose();
    vi.advanceTimersByTime(4_500);
    const second = FakeWebSocket.instances[1];
    second.open();
    expect(second.sent).toContain(
      '{"type":"subscribe","resourceId":"r-1"}',
    );
    client.stop();
  });

  it("envia ping no heartbeat e mensagem chega ao consumidor", () => {
    const messages: string[] = [];
    const client = new RealtimeSocketClient({
      buildUrl: () => "wss://h/ws",
      pingMs: 1_000,
      onMessage: (raw) => messages.push(raw),
    });
    client.start();
    const socket = FakeWebSocket.instances[0];
    socket.open();
    vi.advanceTimersByTime(2_500);
    expect(socket.sent.filter((p) => p === "ping")).toHaveLength(2);
    socket.emitMessage('{"type":"pong"}');
    expect(messages).toEqual(['{"type":"pong"}']);
    client.stop();
  });

  it("unsubscribe remove da lista desejada e não rejoina", () => {
    const client = makeClient();
    client.start();
    const first = FakeWebSocket.instances[0];
    first.open();
    client.subscribe('{"a":1}');
    client.unsubscribe('{"a":1}');
    first.emitClose();
    vi.advanceTimersByTime(4_500);
    const second = FakeWebSocket.instances[1];
    second.open();
    expect(second.sent).not.toContain('{"a":1}');
    client.stop();
  });

  it("sem token (buildUrl null) reconecta depois", () => {
    let ready = false;
    const client = new RealtimeSocketClient({
      buildUrl: () => (ready ? "wss://h/ws" : null),
      onMessage: () => undefined,
    });
    client.start();
    expect(FakeWebSocket.instances).toHaveLength(0);
    expect(client.getState().error).toBe("not_ready");
    ready = true;
    vi.advanceTimersByTime(4_500);
    expect(FakeWebSocket.instances).toHaveLength(1);
    client.stop();
  });
});

describe("createEventDispatcher", () => {
  it("deduplica por eventId e descarrega um batch após debounce", () => {
    const batches: unknown[][] = [];
    const dispatch = createEventDispatcher({
      debounceMs: 100,
      onFlush: (events) => batches.push(events),
    });
    dispatch({ eventId: "e-1", a: 1 });
    dispatch({ eventId: "e-1", a: 1 });
    dispatch({ eventId: "e-2", a: 2 });
    vi.advanceTimersByTime(150);
    expect(batches).toHaveLength(1);
    expect(batches[0]).toHaveLength(2);
  });
});

describe("RealtimeSocketClient opções aditivas", () => {
  it("reconnect exponencial com jitter fica entre a base e o teto", () => {
    const client = new RealtimeSocketClient({
      buildUrl: () => "wss://h/ws",
      onMessage: () => undefined,
      reconnect: { mode: "exponential", baseMs: 1_000, maxMs: 30_000, jitter: true },
    });
    client.start();
    FakeWebSocket.instances[0].emitClose();
    vi.advanceTimersByTime(999);
    expect(FakeWebSocket.instances).toHaveLength(1);
    vi.advanceTimersByTime(30_000);
    expect(FakeWebSocket.instances.length).toBeGreaterThan(1);
    client.stop();
  });

  it("não reconecta em 1008 com a mesma URL e reconecta quando a URL muda", () => {
    let url = "wss://h/ws?token=a";
    const client = new RealtimeSocketClient({
      buildUrl: () => url,
      onMessage: () => undefined,
      shouldReconnect: ({ closeCode, sameUrl }) => !(closeCode === 1008 && sameUrl),
    });
    client.start();
    const first = FakeWebSocket.instances[0];
    first.open();
    first.emitClose(1008);
    vi.advanceTimersByTime(10_000);
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(client.getStatus()).toBe("unavailable");
    url = "wss://h/ws?token=b";
    first.emitClose(1008);
    vi.advanceTimersByTime(4_500);
    expect(FakeWebSocket.instances.at(-1)?.url).toBe("wss://h/ws?token=b");
    client.stop();
  });

  it("onResync só dispara depois da primeira conexão e o status passa por open", () => {
    const statuses: string[] = [];
    let resyncs = 0;
    const client = new RealtimeSocketClient({
      buildUrl: () => "wss://h/ws",
      onMessage: () => undefined,
      onResync: () => {
        resyncs += 1;
      },
    });
    client.onStatusChange((status) => statuses.push(status));
    expect(client.getStatus()).toBe("idle");
    client.start();
    expect(statuses).toContain("connecting");
    FakeWebSocket.instances[0].open();
    expect(client.getStatus()).toBe("open");
    expect(resyncs).toBe(0);
    FakeWebSocket.instances[0].emitClose();
    vi.advanceTimersByTime(4_500);
    FakeWebSocket.instances[1].open();
    expect(resyncs).toBe(1);
    client.stop();
    expect(client.getStatus()).toBe("closed");
  });

  it("resubscribeOnReconnect false não reenvia a sala", () => {
    const client = new RealtimeSocketClient({
      buildUrl: () => "wss://h/ws",
      onMessage: () => undefined,
      resubscribeOnReconnect: false,
    });
    client.start();
    client.subscribe('{"type":"subscribe","room":"a"}');
    FakeWebSocket.instances[0].open();
    FakeWebSocket.instances[0].emitClose();
    vi.advanceTimersByTime(4_500);
    FakeWebSocket.instances[1].open();
    expect(FakeWebSocket.instances[1].sent).not.toContain(
      '{"type":"subscribe","room":"a"}',
    );
    client.stop();
  });
});
