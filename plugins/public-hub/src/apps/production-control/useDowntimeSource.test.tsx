/** @vitest-environment jsdom */
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDowntimeSource } from "./useDowntimeSource.ts";

const MES = {
  source: "mes",
  reason: "bound_counter",
  branch: "02",
  workCenter: "CT-63",
  referenceAt: "2026-10-19T16:00:00Z",
};

const TOTVS = {
  source: "totvs",
  reason: "no_bound_counter",
  branch: "02",
  workCenter: "CT-63",
  referenceAt: "2026-10-19T16:00:00Z",
};

const WATCH_MS = 30_000;
const STALE_MS = 5 * 60_000;

function ok(data: unknown, status = 200): Response {
  return new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>,
) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal(
    "fetch",
    async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return handler(String(url), init);
    },
  );
  return calls;
}

async function tick(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe("useDowntimeSource", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("resolve a fonte oficial na montagem", async () => {
    stubFetch(() => ok(MES));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await waitFor(() => expect(hook.result.current.source).toBe("mes"));
    expect(hook.result.current.error).toBeNull();
  });

  it("revalida no watch e percebe transição TOTVS → MES sem remontar", async () => {
    vi.useFakeTimers();
    let source: "totvs" | "mes" = "totvs";
    const calls = stubFetch(() => ok(source === "mes" ? MES : TOTVS));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await act(async () => {});
    expect(hook.result.current.source).toBe("totvs");

    // Sensor ativado com o tablet já aberto: o próximo tick resolve a fonte nova.
    source = "mes";
    await tick(WATCH_MS);

    expect(hook.result.current.source).toBe("mes");
    expect(calls.length).toBeGreaterThanOrEqual(2);
    expect(calls[0].url).toContain("downtime-source");
    expect(calls[0].url).toContain("workCenter=CT-63");
  });

  it("revalida quando a aba volta a ficar visível", async () => {
    vi.useFakeTimers();
    let source: "totvs" | "mes" = "totvs";
    stubFetch(() => ok(source === "mes" ? MES : TOTVS));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await act(async () => {});
    expect(hook.result.current.source).toBe("totvs");

    source = "mes";
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    expect(hook.result.current.source).toBe("mes");
  });

  it("revalida na reconexão do realtime", async () => {
    vi.useFakeTimers();
    const calls = stubFetch(() => ok(MES));
    const hook = renderHook(
      ({ connected }: { connected: boolean }) =>
        useDowntimeSource("tok", "02", "CT-63", connected),
      { initialProps: { connected: false } },
    );

    await act(async () => {});
    expect(hook.result.current.source).toBe("mes");
    expect(calls).toHaveLength(1);

    // A reconexão dispara reload imediato — sem esperar o próximo tick.
    hook.rerender({ connected: true });
    await act(async () => {});

    expect(calls).toHaveLength(2);
    expect(hook.result.current.source).toBe("mes");
  });

  it("falha de refetch preserva a resolução dentro da janela de frescor", async () => {
    vi.useFakeTimers();
    let fail = false;
    stubFetch(() => (fail ? err(503) : ok(MES)));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await act(async () => {});
    expect(hook.result.current.source).toBe("mes");

    fail = true;
    await tick(WATCH_MS);

    // Erro transitório: fonte anterior continua válida e o erro fica exposto.
    expect(hook.result.current.source).toBe("mes");
    expect(hook.result.current.error?.retryable).toBe(true);
  });

  it("falhas além da janela derrubam a fonte antiga — nunca exibe stale como válida", async () => {
    vi.useFakeTimers();
    let fail = false;
    stubFetch(() => (fail ? err(503) : ok(MES)));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await act(async () => {});
    expect(hook.result.current.source).toBe("mes");

    fail = true;
    // 5 min de falhas consecutivas ainda preserva; o próximo tick expira.
    await tick(STALE_MS);

    expect(hook.result.current.source).toBe("mes");
    expect(hook.result.current.error?.retryable).toBe(true);

    await tick(WATCH_MS);

    expect(hook.result.current.source).toBeNull();
    expect(hook.result.current.resolution).toBeNull();
    expect(hook.result.current.error?.message).toBeTruthy();
  });

  it("falha na resolução inicial mostra indisponibilidade, nunca fonte inventada", async () => {
    stubFetch(() => err(503));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await waitFor(() => expect(hook.result.current.error).not.toBeNull());
    expect(hook.result.current.source).toBeNull();
    expect(hook.result.current.error?.retryable).toBe(true);
  });

  it("recupera sozinho quando o endpoint volta — sem reload manual", async () => {
    vi.useFakeTimers();
    let fail = true;
    stubFetch(() => (fail ? err(503) : ok(TOTVS)));
    const hook = renderHook(() => useDowntimeSource("tok", "02", "CT-63"));

    await act(async () => {});
    expect(hook.result.current.source).toBeNull();

    fail = false;
    await tick(WATCH_MS);

    expect(hook.result.current.source).toBe("totvs");
    expect(hook.result.current.error).toBeNull();
  });
});

function err(status: number): Response {
  return new Response(JSON.stringify({ success: false, message: "down" }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
