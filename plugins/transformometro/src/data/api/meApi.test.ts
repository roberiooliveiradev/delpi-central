import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchMeProfile, greetingFirstNameFromProfile } from "./meApi";

describe("transformometro meApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("lê só o nome de /core-api/me e não persiste PII", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "u1", name: "Robério Silva", email: "roberio@delpi.local" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const storage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    vi.stubGlobal("localStorage", storage);

    const profile = await fetchMeProfile(() => "token-1");
    expect(profile).toEqual({ id: "u1", name: "Robério Silva" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/core-api/me",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer token-1" }),
      }),
    );
    expect(storage.setItem).not.toHaveBeenCalled();
  });

  it("usa o primeiro nome do contrato name e recusa e-mail no lugar do nome", () => {
    expect(greetingFirstNameFromProfile({ name: "Robério Silva" })).toBe("Robério");
    expect(greetingFirstNameFromProfile({ name: "  " })).toBeNull();
    expect(greetingFirstNameFromProfile({ name: "roberio@delpi.local" })).toBeNull();
    expect(greetingFirstNameFromProfile({ name: "", email: "roberio@delpi.local" })).toBeNull();
  });
});
