import { describe, expect, it, vi } from "vitest";

import { parseApiEnvelope } from "./transformometroHttp";

describe("parseApiEnvelope", () => {
  it("converte 429 HTML em mensagem amigável (não JSON.parse cru)", async () => {
    const response = {
      ok: false,
      status: 429,
      json: vi.fn().mockRejectedValue(
        new SyntaxError("Unexpected token '<', \"<html> <h\"... is not valid JSON"),
      ),
    } as unknown as Response;

    await expect(parseApiEnvelope(response)).rejects.toThrow(/muitas requisições/i);
  });

  it("preserva o status HTTP 403 para a UI não tratar como lista vazia", async () => {
    const response = {
      ok: false,
      status: 403,
      json: vi.fn().mockResolvedValue({
        success: false,
        message: "Você não tem permissão para esta operação.",
        data: null,
      }),
    } as unknown as Response;

    await expect(parseApiEnvelope(response)).rejects.toMatchObject({ status: 403 });
  });

  it("retorna data do envelope de sucesso", async () => {
    const response = {
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({
        success: true,
        message: "ok",
        data: { id: "1" },
      }),
    } as unknown as Response;

    await expect(parseApiEnvelope<{ id: string }>(response)).resolves.toEqual({ id: "1" });
  });
});
