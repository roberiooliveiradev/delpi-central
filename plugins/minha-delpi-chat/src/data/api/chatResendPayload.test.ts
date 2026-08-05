import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Regressão: o reenvio (botão «tentar novamente» / editar mensagem) enviava o
 * corpo sem `hostContext`, então um «crie um slide» no editor TV chegava à API
 * como pergunta genérica e o modelo respondia markdown em vez de criar a tela.
 */

const capturedBodies: string[] = [];

vi.mock("./chatApiFetch", () => ({
  fetchChatApi: vi.fn(async (_url: string, init: RequestInit) => {
    capturedBodies.push(String(init.body ?? ""));
    throw new Error("stream-interrompido-no-teste");
  }),
  fetchChatApiBootstrap: vi.fn(),
  formatTransientChatApiMessage: vi.fn(() => ""),
  isTransientHttpStatus: vi.fn(() => false),
}));

const { resendChatMessage } = await import("./chatApi");

describe("resendChatMessage", () => {
  beforeEach(() => {
    capturedBodies.length = 0;
  });

  it("propaga hostContext e formato do turno no reenvio", async () => {
    await expect(
      resendChatMessage(
        "session-1",
        "message-1",
        "crie um slide",
        {},
        {
          context: "geral",
          responseMode: "normal",
          responseFormat: "table",
          hostContext: {
            surface: "tv-dashboard",
            playlistId: "pl-1",
            slideId: "sl-1",
          },
        },
      ),
    ).rejects.toThrow();

    const body = JSON.parse(capturedBodies[0] ?? "{}");
    expect(body.content).toBe("crie um slide");
    expect(body.hostContext).toEqual({
      surface: "tv-dashboard",
      playlistId: "pl-1",
      slideId: "sl-1",
    });
    expect(body.responseFormat).toBe("table");
  });

  it("omite formato automático para não fixar apresentação no reenvio", async () => {
    await expect(
      resendChatMessage("session-1", "message-1", "crie um slide", {}, {
        responseFormat: "auto",
      }),
    ).rejects.toThrow();

    const body = JSON.parse(capturedBodies[0] ?? "{}");
    expect(body.responseFormat).toBeUndefined();
  });
});
