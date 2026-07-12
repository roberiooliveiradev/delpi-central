import { describe, expect, it } from "vitest";

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
