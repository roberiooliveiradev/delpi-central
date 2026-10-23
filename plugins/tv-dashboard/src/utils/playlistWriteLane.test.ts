import { afterEach, describe, expect, it, vi } from "vitest";

import {
  enqueuePlaylistWrite,
  onPlaylistWriteSettled,
} from "./playlistWriteLane";

/**
 * Web Locks API fake — o registry é por ORIGIN: dois "contextos" (abas)
 * compartilham o mesmo registro e serializam pelo nome do lock.
 */
function makeLockRegistry() {
  const chains = new Map<string, Promise<unknown>>();
  const calls: string[] = [];
  return {
    calls,
    request(name: string, callback: () => Promise<unknown>): Promise<unknown> {
      calls.push(name);
      const prev = chains.get(name) ?? Promise.resolve();
      const next = prev.then(callback, callback);
      chains.set(name, next.catch(() => undefined));
      return next;
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("enqueuePlaylistWrite", () => {
  it("serializa escritas na mesma playlist — a segunda só envia após o ack da primeira", async () => {
    // Regressão TV-ICON-CONFLICT: mutations concorrentes do mesmo cliente
    // resolviam expectedRevision antes do ack e colidiam no CAS (self-409).
    const sentIfMatch: Array<number | null | undefined> = [];
    const tracker = { revision: 5 };
    let releaseFirst!: () => void;
    const firstGate = new Promise<void>((resolve) => (releaseFirst = resolve));

    const fakeWrite = (label: string) =>
      enqueuePlaylistWrite("pl-1", async () => {
        sentIfMatch.push(tracker.revision);
        if (label === "first") await firstGate;
        tracker.revision += 1; // ack avança a revisão conhecida
        return label;
      });

    const first = fakeWrite("first");
    const second = fakeWrite("second");
    const third = fakeWrite("third");

    await Promise.resolve();
    releaseFirst();

    await expect(third).resolves.toBe("third");
    await Promise.all([first, second]);
    expect(sentIfMatch).toEqual([5, 6, 7]);
  });

  it("continua a fila após falha — um 409 não trava escritas seguintes", async () => {
    const failing = enqueuePlaylistWrite("pl-2", () =>
      Promise.reject(new Error("revision conflict")),
    );
    await expect(failing).rejects.toThrow("revision conflict");

    const recovered = enqueuePlaylistWrite("pl-2", async () => "ok");
    await expect(recovered).resolves.toBe("ok");
  });

  it("não serializa entre playlists distintas", async () => {
    let release!: () => void;
    const hold = new Promise<void>((resolve) => (release = resolve));
    const held = enqueuePlaylistWrite("pl-3", () => hold.then(() => "held"));
    const free = enqueuePlaylistWrite("pl-4", async () => "free");

    await expect(free).resolves.toBe("free");
    release();
    await expect(held).resolves.toBe("held");
  });

  it("serializa entre contextos via Web Locks — thunk resolve revisão fresca", async () => {
    // TV-EDITOR-CROSS-CONTEXT: dois contextos JS (abas) com trackers próprios
    // produziam 409 determinístico; o lock por playlist faz o segundo contexto
    // esperar o commit do primeiro e resolver expectedRevision atualizado.
    const locks = makeLockRegistry();
    vi.stubGlobal("navigator", { locks });

    const sentIfMatch: number[] = [];
    const tracker = { revision: 10 };
    let releaseFirst!: () => void;
    const gate = new Promise<void>((resolve) => (releaseFirst = resolve));

    // "contexto A" — commita primeiro
    const first = enqueuePlaylistWrite("pl-ctx", async () => {
      sentIfMatch.push(tracker.revision);
      await gate;
      tracker.revision += 1;
      return "first";
    });
    // "contexto B" — enfileirado em outra aba; thunk deve resolver dentro do
    // lock, DEPOIS do ack de A (revisão já avançada).
    const second = enqueuePlaylistWrite("pl-ctx", async () => {
      sentIfMatch.push(tracker.revision);
      tracker.revision += 1;
      return "second";
    });

    await new Promise((resolve) => setTimeout(resolve, 0)); // flush microtasks
    expect(sentIfMatch).toEqual([10]); // B ainda não enviou
    releaseFirst();
    await Promise.all([first, second]);

    expect(sentIfMatch).toEqual([10, 11]); // B usou revisão fresca
    expect(locks.calls).toEqual([
      "tv-dashboard:playlist-write:pl-ctx",
      "tv-dashboard:playlist-write:pl-ctx",
    ]);
  });

  it("libera o lock após falha — a fila cross-context continua", async () => {
    const locks = makeLockRegistry();
    vi.stubGlobal("navigator", { locks });

    const failing = enqueuePlaylistWrite("pl-lock", () =>
      Promise.reject(new Error("revision conflict")),
    );
    await expect(failing).rejects.toThrow("revision conflict");

    const recovered = enqueuePlaylistWrite("pl-lock", async () => "ok");
    await expect(recovered).resolves.toBe("ok");
    expect(locks.calls).toHaveLength(2);
  });

  it("locks são por playlist — playlists distintas não bloqueiam", async () => {
    const locks = makeLockRegistry();
    vi.stubGlobal("navigator", { locks });

    let release!: () => void;
    const hold = new Promise<void>((resolve) => (release = resolve));
    const held = enqueuePlaylistWrite("pl-a", () => hold.then(() => "held"));
    const free = enqueuePlaylistWrite("pl-b", async () => "free");

    await expect(free).resolves.toBe("free");
    release();
    await expect(held).resolves.toBe("held");
    expect(locks.calls).toEqual([
      "tv-dashboard:playlist-write:pl-a",
      "tv-dashboard:playlist-write:pl-b",
    ]);
  });

  it("fallback sem Web Locks mantém FIFO local", async () => {
    vi.stubGlobal("navigator", {}); // ambiente sem navigator.locks
    const sentIfMatch: number[] = [];
    const tracker = { revision: 3 };
    let releaseFirst!: () => void;
    const gate = new Promise<void>((resolve) => (releaseFirst = resolve));

    const first = enqueuePlaylistWrite("pl-fb", async () => {
      sentIfMatch.push(tracker.revision);
      await gate;
      tracker.revision += 1;
    });
    const second = enqueuePlaylistWrite("pl-fb", async () => {
      sentIfMatch.push(tracker.revision);
    });

    await Promise.resolve();
    releaseFirst();
    await Promise.all([first, second]);
    expect(sentIfMatch).toEqual([3, 4]);
  });
});

describe("onPlaylistWriteSettled — reconciliação diferida (024-R1)", () => {
  it("notifica fulfilled no ack da escrita", async () => {
    const seen: Array<{ playlistId: string; outcome: string }> = [];
    const unsub = onPlaylistWriteSettled("pl-s1", (info) => seen.push(info));
    await enqueuePlaylistWrite("pl-s1", async () => "ok");
    unsub();
    expect(seen).toEqual([{ playlistId: "pl-s1", outcome: "fulfilled" }]);
  });

  it("notifica rejected em falha não-CAS (rede/timeout/cancelamento)", async () => {
    const seen: string[] = [];
    const unsub = onPlaylistWriteSettled("pl-s2", (info) =>
      seen.push(info.outcome),
    );
    await expect(
      enqueuePlaylistWrite("pl-s2", () =>
        Promise.reject(new Error("network timeout")),
      ),
    ).rejects.toThrow("network timeout");
    unsub();
    expect(seen).toEqual(["rejected"]);
  });

  it("A3 — escrita estrangeira N+1 + falha não-CAS local: settle rejected expõe recuperação", async () => {
    // Simula a sequência: evento ambíguo suprimido, escrita própria falha sem
    // 409 → o listener é o ponto único que garante reload obrigatório.
    const outcomes: string[] = [];
    const unsub = onPlaylistWriteSettled("pl-s3", (info) =>
      outcomes.push(info.outcome),
    );
    await expect(
      enqueuePlaylistWrite("pl-s3", () => Promise.reject(new Error("abort"))),
    ).rejects.toThrow("abort");
    unsub();
    expect(outcomes).toEqual(["rejected"]);
  });

  it("unsubscribe para de receber notificações", async () => {
    const seen: string[] = [];
    const unsub = onPlaylistWriteSettled("pl-s4", (info) =>
      seen.push(info.outcome),
    );
    unsub();
    await enqueuePlaylistWrite("pl-s4", async () => "ok");
    expect(seen).toEqual([]);
  });

  it("listener que lança não quebra a lane nem outros listeners", async () => {
    const seen: string[] = [];
    onPlaylistWriteSettled("pl-s5", () => {
      throw new Error("listener bug");
    });
    onPlaylistWriteSettled("pl-s5", (info) => seen.push(info.outcome));
    await expect(
      enqueuePlaylistWrite("pl-s5", async () => "ok"),
    ).resolves.toBe("ok");
    expect(seen).toEqual(["fulfilled"]);
  });
});
