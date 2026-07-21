import { describe, expect, it } from "vitest";

import {
  bumpComunicadoAutosaveVersion,
  isStaleComunicadoAutosave,
  resolveNativeConfigAfterAutosave,
  shouldClearComunicadoDraftAfterSave,
  shouldClearComunicadoPendingAfterSave,
} from "./comunicadoSlideAutosave";

describe("comunicadoSlideAutosave", () => {
  it("bump monotônico por slide", () => {
    const versions = new Map<string, number>();
    expect(bumpComunicadoAutosaveVersion(versions, "a")).toBe(1);
    expect(bumpComunicadoAutosaveVersion(versions, "a")).toBe(2);
    expect(bumpComunicadoAutosaveVersion(versions, "b")).toBe(1);
  });

  it("detecta save stale", () => {
    expect(isStaleComunicadoAutosave(1, 2)).toBe(true);
    expect(isStaleComunicadoAutosave(2, 2)).toBe(false);
    expect(isStaleComunicadoAutosave(undefined, 5)).toBe(false);
  });

  it("não limpa draft/pending quando a resposta é stale", () => {
    expect(shouldClearComunicadoDraftAfterSave({ completedVersion: 1, latestVersion: 3 })).toBe(
      false,
    );
    expect(
      shouldClearComunicadoPendingAfterSave({
        pending: { slideId: "s1", nativeConfig: { v: 3 }, version: 3 },
        slideId: "s1",
        completedVersion: 1,
      }),
    ).toBe(false);
  });

  it("preserva nativeConfig pending após save stale", () => {
    const resolved = resolveNativeConfigAfterAutosave({
      slideId: "s1",
      serverNativeConfig: { v: 1 },
      completedVersion: 1,
      latestVersion: 2,
      pending: { slideId: "s1", nativeConfig: { v: 2 }, version: 2 },
      liveConfig: { v: 2 },
      selectedSlideId: "s1",
    });
    expect(resolved).toEqual({ v: 2 });
  });

  it("limpa pending quando a versão salva é a corrente", () => {
    expect(
      shouldClearComunicadoPendingAfterSave({
        pending: { slideId: "s1", nativeConfig: { v: 2 }, version: 2 },
        slideId: "s1",
        completedVersion: 2,
      }),
    ).toBe(true);
  });
});
