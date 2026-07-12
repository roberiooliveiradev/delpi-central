import { describe, expect, it } from "vitest";

import {
  fingerprintComunicadoValue,
  shouldAcceptExternalComunicadoValue,
} from "./comunicadoEditorValueSync";

describe("shouldAcceptExternalComunicadoValue", () => {
  it("aceita na troca de slide/playlist", () => {
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: true,
        incomingFingerprint: "a",
        lastEmittedFingerprint: "b",
        currentFingerprint: "b",
      }),
    ).toBe(true);
  });

  it("ignora eco do próprio onChange (mesmo fingerprint emitido)", () => {
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: false,
        incomingFingerprint: "live",
        lastEmittedFingerprint: "live",
        currentFingerprint: "live",
      }),
    ).toBe(false);
  });

  it("ignora nativeConfig stale do pai após drag (emitido ≠ incoming)", () => {
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: false,
        incomingFingerprint: "pos-antiga",
        lastEmittedFingerprint: "pos-nova",
        currentFingerprint: "pos-nova",
      }),
    ).toBe(false);
  });

  it("aceita valor externo quando ainda não houve emit local e conteúdo mudou", () => {
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: false,
        incomingFingerprint: "server",
        lastEmittedFingerprint: null,
        currentFingerprint: "initial",
      }),
    ).toBe(true);
  });

  it("fingerprint estável para o mesmo payload", () => {
    const a = fingerprintComunicadoValue({ blocks: [{ id: "1" }] });
    const b = fingerprintComunicadoValue({ blocks: [{ id: "1" }] });
    expect(a).toBe(b);
  });
});
