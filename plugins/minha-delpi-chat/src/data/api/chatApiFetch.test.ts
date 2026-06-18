import { describe, expect, it, vi } from "vitest";

import {
  fetchChatApi,
  isBootstrapLoadErrorMessage,
  isTransientHttpStatus,
} from "./chatApiFetch";

describe("chatApiFetch", () => {
  it("identifica status transitórios", () => {
    expect(isTransientHttpStatus(502)).toBe(true);
    expect(isTransientHttpStatus(503)).toBe(true);
    expect(isTransientHttpStatus(404)).toBe(false);
  });

  it("repete fetch em 502 e retorna resposta ok", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("bad gateway", { status: 502 }))
      .mockResolvedValueOnce(new Response("[]", { status: 200 }));

    vi.stubGlobal("fetch", fetchMock);

    const response = await fetchChatApi("/test", undefined, [1]);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(response.status).toBe(200);

    vi.unstubAllGlobals();
  });

  it("classifica mensagens de bootstrap", () => {
    expect(
      isBootstrapLoadErrorMessage(
        "Erro ao comunicar com o Minha DELPI Chat. (HTTP 502: <html>...",
      ),
    ).toBe(true);
    expect(isBootstrapLoadErrorMessage("Erro ao carregar agentes.")).toBe(true);
    expect(isBootstrapLoadErrorMessage("Campo obrigatório")).toBe(false);
  });
});
