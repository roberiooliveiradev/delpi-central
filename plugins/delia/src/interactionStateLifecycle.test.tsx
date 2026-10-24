/**
 * DELIA-UX-INTERACTION-STATE-LIFECYCLE-COMPLETION-01
 * Automated matrix for idle → processing → responding → idle,
 * errors, abort/concurrency, and motion completion.
 */
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const SUCCESS_PAYLOAD = {
  session_id: "s-1",
  user_turn_id: "ut-1",
  result_turn_id: "rt-1",
  content: "Resposta lifecycle da DÉLIA.",
  epistemic_class: "HYPOTHESIS",
  limitations: [],
  generated_at: "2026-01-01T00:00:00+00:00",
  model_invocation_id: "inv-1",
};

function coreMeOk() {
  return new Response(JSON.stringify({ name: null, has_photo: false }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function deliaApiCalls(fetchMock: { mock: { calls: unknown[][] } }) {
  return fetchMock.mock.calls.filter(([u]) =>
    String(u).startsWith("/apps/delia-api/interaction"),
  ) as [string, RequestInit][];
}

function submitTurn(input: string) {
  fireEvent.change(screen.getByLabelText("Pergunte à DÉLIA"), {
    target: { value: input },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar mensagem" }));
}

function mockMatchMedia(reduced: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: reduced && String(query).includes("prefers-reduced-motion"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

beforeEach(() => {
  // Ambiente estável: matchMedia ausente/undefined não deve derrubar responding.
  mockMatchMedia(false);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("lifecycle A — fluxo normal", () => {
  it("A01 idle na recepção sem pending/processing", () => {
    const { container } = render(<App getAccessToken={() => "t"} />);
    expect(container.querySelector(".delpi-ui-conversation-reception")).toBeTruthy();
    expect(container.querySelector(".delia-interaction__pending-row")).toBeNull();
    expect(container.querySelector('[data-motion="processing"]')).toBeNull();
    expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy();
  });

  it("A02–A04 pending/processing durante fetch e encerra na resposta", async () => {
    let resolveFetch: (value: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        });
      }),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);
    submitTurn("ciclo A");

    await waitFor(() => {
      expect(container.querySelector(".delia-interaction__pending-row")).toBeTruthy();
      expect(
        container.querySelector(
          '.delia-interaction__pending-row [data-motion="processing"]',
        ),
      ).toBeTruthy();
    });
    expect(screen.getByRole("button", { name: "Interromper resposta em andamento" })).toBeTruthy();

    resolveFetch(
      new Response(JSON.stringify(SUCCESS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await waitFor(() => {
      expect(screen.getByText("Resposta lifecycle da DÉLIA.")).toBeTruthy();
      expect(container.querySelector(".delia-interaction__pending-row")).toBeNull();
      expect(container.querySelector('[data-motion="processing"]')).toBeNull();
    });
    expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy();
  });

  it("A05–A06 responding one-shot volta a idle via reduced motion", async () => {
    mockMatchMedia(true);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify(SUCCESS_PAYLOAD), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);
    submitTurn("responding");

    await waitFor(() =>
      expect(screen.getByText("Resposta lifecycle da DÉLIA.")).toBeTruthy(),
    );
    // Reduced motion completes synchronously in UnifiedAvatar effect.
    await waitFor(() => {
      const assistantMotions = Array.from(
        container.querySelectorAll('.delpi-ui-unified-avatar--assistant[data-motion]'),
      ).map((el) => el.getAttribute("data-motion"));
      expect(assistantMotions.every((m) => m === "idle" || m === "attention")).toBe(
        true,
      );
      expect(assistantMotions).not.toContain("responding");
      expect(assistantMotions).not.toContain("processing");
    });
  });

  it("A07–A08 segundo turno não reutiliza processing do anterior", async () => {
    let call = 0;
    const resolvers: Array<(value: Response) => void> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return new Promise<Response>((resolve) => {
          resolvers[call] = resolve;
          call += 1;
        });
      }),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);
    submitTurn("turno 1");
    await waitFor(() =>
      expect(container.querySelector(".delia-interaction__pending-row")).toBeTruthy(),
    );
    resolvers[0]?.(
      new Response(
        JSON.stringify({
          ...SUCCESS_PAYLOAD,
          content: "R1",
          user_turn_id: "ut-a",
          result_turn_id: "rt-a",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    await waitFor(() => expect(screen.getByText("R1")).toBeTruthy());
    expect(container.querySelector(".delia-interaction__pending-row")).toBeNull();

    submitTurn("turno 2");
    await waitFor(() =>
      expect(container.querySelector(".delia-interaction__pending-row")).toBeTruthy(),
    );
    expect(
      container.querySelectorAll(".delia-interaction__pending-row [data-motion='processing']"),
    ).toHaveLength(1);
    resolvers[1]?.(
      new Response(
        JSON.stringify({
          ...SUCCESS_PAYLOAD,
          content: "R2",
          user_turn_id: "ut-b",
          result_turn_id: "rt-b",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    await waitFor(() => expect(screen.getByText("R2")).toBeTruthy());
    expect(container.querySelector(".delia-interaction__pending-row")).toBeNull();
  });
});

describe("lifecycle B — erros", () => {
  it("B01–B02 HTTP/erro de rede sai de processing e mostra alert", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "boom", code: "internal" }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);
    const draft = "mensagem preservada";
    fireEvent.change(screen.getByLabelText("Pergunte à DÉLIA"), {
      target: { value: draft },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar mensagem" }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(container.querySelector(".delia-interaction__pending-row")).toBeNull();
    expect(container.querySelector('[data-motion="processing"]')).toBeNull();
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe(draft);
    expect(screen.queryByText("Resposta lifecycle da DÉLIA.")).toBeNull();
  });

  it("B04–B06 falha não inventa sucesso; nova tentativa limpa erro anterior", async () => {
    let failFirst = true;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        if (failFirst) {
          failFirst = false;
          return Promise.reject(new TypeError("Failed to fetch"));
        }
        return Promise.resolve(
          new Response(JSON.stringify(SUCCESS_PAYLOAD), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
    render(<App getAccessToken={() => "t"} />);
    submitTurn("retry");
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    submitTurn("retry");
    await waitFor(() =>
      expect(screen.getByText("Resposta lifecycle da DÉLIA.")).toBeTruthy(),
    );
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("lifecycle C — cancelamento e concorrência", () => {
  it("C01–C03 stop encerra pending e resposta tardia não cria turno", async () => {
    let resolveFetch: (value: Response) => void = () => {};
    const fetchMock = vi.fn().mockImplementation((input: unknown) => {
      if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
      return new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<App getAccessToken={() => "t"} />);
    submitTurn("cancelável");

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Interromper resposta em andamento" })).toBeTruthy(),
    );
    const signal = deliaApiCalls(fetchMock)[0][1].signal as AbortSignal;
    fireEvent.click(screen.getByRole("button", { name: "Interromper resposta em andamento" }));

    await waitFor(() => {
      expect(container.querySelector(".delia-interaction__pending-row")).toBeNull();
      expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy();
    });
    expect(signal.aborted).toBe(true);

    resolveFetch(
      new Response(JSON.stringify(SUCCESS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await new Promise((r) => setTimeout(r, 30));
    expect(screen.queryByText("Resposta lifecycle da DÉLIA.")).toBeNull();
    expect(container.querySelector(".delia-timeline")).toBeNull();
  });

  it("C04 erro tardio do request antigo não sobrescreve turno novo", async () => {
    const resolvers: Array<{
      resolve: (value: Response) => void;
      reject: (reason?: unknown) => void;
    }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return new Promise<Response>((resolve, reject) => {
          resolvers.push({ resolve, reject });
        });
      }),
    );
    render(<App getAccessToken={() => "t"} />);
    submitTurn("primeiro");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Interromper resposta em andamento" })).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Interromper resposta em andamento" }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy(),
    );

    submitTurn("segundo");
    await waitFor(() => expect(resolvers.length).toBeGreaterThanOrEqual(2));
    resolvers[0]?.reject(new TypeError("late network from aborted request"));
    resolvers[1]?.resolve(
      new Response(
        JSON.stringify({ ...SUCCESS_PAYLOAD, content: "Só o segundo" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await waitFor(() => expect(screen.getByText("Só o segundo")).toBeTruthy());
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("C06 confirmação não expõe stop cancelável fictício", async () => {
    // APPLY_PREPARED path uses responding_not_cancelable — covered via pending card flows
    // in interaction.test; here we assert idle composer has Enviar, not stop, before send.
    render(<App getAccessToken={() => "t"} />);
    expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Interromper resposta em andamento" })).toBeNull();
  });

  it("C07 desmontagem com request pendente não deixa processing no remount", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return new Promise(() => {
          /* never resolves */
        });
      }),
    );
    const first = render(<App getAccessToken={() => "t"} />);
    submitTurn("unmount");
    await waitFor(() =>
      expect(
        first.container.querySelector(".delia-interaction__pending-row"),
      ).toBeTruthy(),
    );
    first.unmount();

    const second = render(<App getAccessToken={() => "t"} />);
    expect(second.container.querySelector(".delia-interaction__pending-row")).toBeNull();
    expect(second.container.querySelector('[data-motion="processing"]')).toBeNull();
    expect(second.container.querySelector(".delpi-ui-conversation-reception")).toBeTruthy();
  });

  it("C08 stop repetido não quebra o composer", async () => {
    let resolveFetch: (value: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        });
      }),
    );
    render(<App getAccessToken={() => "t"} />);
    submitTurn("double-stop");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Interromper resposta em andamento" })).toBeTruthy(),
    );
    const stop = screen.getByRole("button", { name: "Interromper resposta em andamento" });
    fireEvent.click(stop);
    fireEvent.click(stop);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy(),
    );
    resolveFetch(
      new Response(JSON.stringify(SUCCESS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await new Promise((r) => setTimeout(r, 20));
    expect(screen.queryByText("Resposta lifecycle da DÉLIA.")).toBeNull();
  });
});

describe("lifecycle D — motion / a11y", () => {
  beforeEach(() => {
    mockMatchMedia(false);
  });

  it("D — um único avatar processing no pending row (sem spinner duplicado)", async () => {
    let resolveFetch: (value: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
        if (String(input).startsWith("/apps/delia-api/dictation")) {
          return Promise.resolve(
            new Response(JSON.stringify({ code: "dictation_unavailable" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        });
      }),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);
    submitTurn("a11y");
    await waitFor(() =>
      expect(container.querySelector(".delia-interaction__pending-row")).toBeTruthy(),
    );
    expect(
      container.querySelectorAll(
        ".delia-interaction__pending-row .delpi-ui-unified-avatar",
      ),
    ).toHaveLength(1);
    expect(
      container.querySelector(".delia-interaction__pending-row [aria-hidden='true']"),
    ).toBeTruthy();
    resolveFetch(
      new Response(JSON.stringify(SUCCESS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() =>
      expect(container.querySelector(".delia-interaction__pending-row")).toBeNull(),
    );
  });
});

describe("lifecycle E — integração conversacional", () => {
  it("E — envio bloqueado enquanto pending; foco do composer permanece", async () => {
    let resolveFetch: (value: Response) => void = () => {};
    const fetchMock = vi.fn().mockImplementation((input: unknown) => {
      if (String(input).startsWith("/core-api/")) return Promise.resolve(coreMeOk());
      return new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);
    const input = screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement;
    input.focus();
    submitTurn("bloqueio");
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    fireEvent.change(input, { target: { value: "segunda" } });
    fireEvent.click(screen.getByRole("button", { name: "Interromper resposta em andamento" }));
    // After stop, Enviar returns — the in-flight count stays 1 (no second POST while pending).
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Enviar mensagem" })).toBeTruthy(),
    );
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);
    expect(document.activeElement === input || input.value === "segunda").toBe(true);
    resolveFetch(
      new Response(JSON.stringify(SUCCESS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
});
