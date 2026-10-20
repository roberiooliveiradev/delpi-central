import { beforeEach, describe, expect, it } from "vitest";

import {
  detectSharedSlideWrite,
  publishPlaylistWriteHead,
  readSharedPlaylistRevision,
  readSharedSlideWriteHead,
} from "./playlistWriteHead";

const PL = "pl-head";
const SLIDE = "slide-1";

beforeEach(() => {
  window.localStorage.clear();
});

describe("publishPlaylistWriteHead", () => {
  it("publica revisão global monotônica — nunca regride", () => {
    publishPlaylistWriteHead(PL, { revision: 12, clientId: "ctx-a" });
    publishPlaylistWriteHead(PL, { revision: 11, clientId: "ctx-a" });
    expect(readSharedPlaylistRevision(PL)).toBe(12);
    publishPlaylistWriteHead(PL, { revision: 15, clientId: "ctx-b" });
    expect(readSharedPlaylistRevision(PL)).toBe(15);
  });

  it("retorna 0 para playlist desconhecida", () => {
    expect(readSharedPlaylistRevision("pl-none")).toBe(0);
  });

  it("publica head por slide com clientId autor", () => {
    publishPlaylistWriteHead(PL, { revision: 8, slideId: SLIDE, clientId: "ctx-a" });
    const head = readSharedSlideWriteHead(PL, SLIDE);
    expect(head?.revision).toBe(8);
    expect(head?.clientId).toBe("ctx-a");
    expect(readSharedSlideWriteHead(PL, "slide-other")).toBeNull();
  });
});

describe("detectSharedSlideWrite", () => {
  it("detecta commit de contexto irmão posterior à captura", () => {
    publishPlaylistWriteHead(PL, { revision: 20, slideId: SLIDE, clientId: "ctx-b:2" });
    const hit = detectSharedSlideWrite(PL, SLIDE, 19, "ctx-a:1");
    expect(hit?.clientId).toBe("ctx-b:2");
  });

  it("ignora o próprio clientId — commit próprio não é conflito", () => {
    publishPlaylistWriteHead(PL, { revision: 20, slideId: SLIDE, clientId: "ctx-a:1" });
    expect(detectSharedSlideWrite(PL, SLIDE, 19, "ctx-a:1")).toBeNull();
  });

  it("ignora head anterior ou igual à base capturada", () => {
    publishPlaylistWriteHead(PL, { revision: 18, slideId: SLIDE, clientId: "ctx-b" });
    expect(detectSharedSlideWrite(PL, SLIDE, 19, "ctx-a")).toBeNull();
    expect(detectSharedSlideWrite(PL, SLIDE, 18, "ctx-a")).toBeNull();
  });

  it("snapshot stale não pode sobrescrever commit de outro cliente", () => {
    // STOP CONDITION: captura em base 10, irmão comitou 12 no mesmo slide —
    // o gate deve detectar e NÃO liberar a escrita com revisão atualizada.
    publishPlaylistWriteHead(PL, { revision: 12, slideId: SLIDE, clientId: "ctx-b" });
    expect(detectSharedSlideWrite(PL, SLIDE, 10, "ctx-a")).not.toBeNull();
    // Escrita em slide diferente não é afetada pelo head deste slide.
    expect(detectSharedSlideWrite(PL, "slide-independent", 10, "ctx-a")).toBeNull();
  });
});
