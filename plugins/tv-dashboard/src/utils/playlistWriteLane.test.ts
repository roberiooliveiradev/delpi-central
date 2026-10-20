import { describe, expect, it } from "vitest";

import { enqueuePlaylistWrite } from "./playlistWriteLane";

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
});
