import { afterEach, describe, expect, it, vi } from "vitest";
import { createAnonymousDenuncia } from "./canalDenunciaApi";
import * as http from "./httpClient";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("createAnonymousDenuncia", () => {
  it("posta description sem campos de usuário", async () => {
    const spy = vi.spyOn(http, "httpPostJson").mockResolvedValue({
      id: "uuid",
      createdAt: "2026-07-14T12:00:00+00:00",
    });

    await createAnonymousDenuncia({ description: "Relato anônimo completo." });

    expect(spy).toHaveBeenCalledWith("/apps/api-delpi/canal-denuncia/denuncias", {
      description: "Relato anônimo completo.",
    });
    const body = spy.mock.calls[0]?.[1] as Record<string, unknown>;
    expect(Object.keys(body)).toEqual(["description"]);
    expect(body).not.toHaveProperty("userId");
    expect(body).not.toHaveProperty("email");
    expect(body).not.toHaveProperty("name");
  });
});
