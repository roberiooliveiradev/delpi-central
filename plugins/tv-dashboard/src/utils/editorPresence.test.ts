import { beforeEach, describe, expect, it, vi } from "vitest";

import { resolveEditorDisplayName } from "./editorPresence";

function accessToken(claims: Record<string, unknown>): string {
  const payload = btoa(JSON.stringify(claims))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
  return `header.${payload}.signature`;
}

describe("resolveEditorDisplayName", () => {
  it("usa o nome do perfil Keycloak", () => {
    expect(resolveEditorDisplayName(accessToken({ name: "Ana Souza" }))).toBe("Ana Souza");
  });

  it("usa Editor quando o token não traz perfil válido", () => {
    expect(resolveEditorDisplayName("token-inválido")).toBe("Editor");
  });
});

const STORAGE_KEY = "tv-dashboard:editor-presence-client-id";

describe("getEditorPresenceClientId", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.resetModules();
  });

  it("retorna identidade composta sessionId:contextId estável no contexto", async () => {
    const mod = await import("./editorPresence");
    const first = mod.getEditorPresenceClientId();
    const second = mod.getEditorPresenceClientId();
    expect(first).toBe(second);
    const [sessionId, contextId] = first.split(":");
    expect(sessionId).toBeTruthy();
    expect(contextId).toBeTruthy();
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe(sessionId);
  });

  it("aba duplicada (sessionStorage herdado) recebe contexto distinto", async () => {
    const modA = await import("./editorPresence");
    const idA = modA.getEditorPresenceClientId();
    const [sessionA, contextA] = idA.split(":");

    // Simula nova aba que herdou o sessionStorage da original (duplicar aba).
    vi.resetModules();
    const modB = await import("./editorPresence");
    const idB = modB.getEditorPresenceClientId();
    const [sessionB, contextB] = idB.split(":");

    // A sessão de editor é correlacionável (mesma aba lógica)…
    expect(sessionB).toBe(sessionA);
    // …mas o contexto JS é distinto — presence/mutation/log separam os dois.
    expect(contextB).not.toBe(contextA);
    expect(idB).not.toBe(idA);
  });

  it("nova aba (sessionStorage vazio) gera sessão e contexto distintos", async () => {
    const modA = await import("./editorPresence");
    const idA = modA.getEditorPresenceClientId();

    vi.resetModules();
    window.sessionStorage.clear();
    const modB = await import("./editorPresence");
    const idB = modB.getEditorPresenceClientId();

    expect(idB.split(":")[0]).not.toBe(idA.split(":")[0]);
    expect(idB).not.toBe(idA);
  });
});
