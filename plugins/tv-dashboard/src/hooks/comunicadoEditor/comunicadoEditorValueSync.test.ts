import { describe, expect, it } from "vitest";

import {
  fingerprintComunicadoValue,
  shouldAcceptExternalComunicadoValue,
  shouldForceAcceptRemoteComunicadoValue,
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

  it("aceita restore de undo/redo mesmo quando parece eco stale", () => {
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: false,
        incomingFingerprint: "pos-antiga",
        lastEmittedFingerprint: "pos-nova",
        currentFingerprint: "pos-nova",
        forceAccept: true,
      }),
    ).toBe(true);
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

describe("shouldForceAcceptRemoteComunicadoValue", () => {
  it("aceita mudança vinda de outro editor (bump de revisão + conteúdo novo)", () => {
    expect(
      shouldForceAcceptRemoteComunicadoValue({
        remoteRevisionChanged: true,
        incomingFingerprint: "remoto",
        currentFingerprint: "local",
      }),
    ).toBe(true);
  });

  it("ignora bump sem mudança real (eco do próprio save)", () => {
    expect(
      shouldForceAcceptRemoteComunicadoValue({
        remoteRevisionChanged: true,
        incomingFingerprint: "igual",
        currentFingerprint: "igual",
      }),
    ).toBe(false);
  });

  it("sem bump de revisão o valor externo divergente segue as regras normais", () => {
    expect(
      shouldForceAcceptRemoteComunicadoValue({
        remoteRevisionChanged: false,
        incomingFingerprint: "remoto",
        currentFingerprint: "local",
      }),
    ).toBe(false);
  });

  it("regressão colaborativa: remoto divergente era rejeitado como eco stale sem o bump", () => {
    // Sem forceAccept (regra antiga) o valor remoto é descartado…
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: false,
        incomingFingerprint: "remoto",
        lastEmittedFingerprint: "meu-ultimo-emit",
        currentFingerprint: "meu-ultimo-emit",
      }),
    ).toBe(false);
    // …e com o bump remoto passa a ser aceito.
    expect(
      shouldAcceptExternalComunicadoValue({
        identityChanged: false,
        incomingFingerprint: "remoto",
        lastEmittedFingerprint: "meu-ultimo-emit",
        currentFingerprint: "meu-ultimo-emit",
        forceAccept: shouldForceAcceptRemoteComunicadoValue({
          remoteRevisionChanged: true,
          incomingFingerprint: "remoto",
          currentFingerprint: "meu-ultimo-emit",
        }),
      }),
    ).toBe(true);
  });
});
