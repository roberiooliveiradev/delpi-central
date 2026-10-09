import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

function successPayload(n: number, content?: string) {
  return {
    session_id: `s-${n}`,
    user_turn_id: `ut-${n}`,
    result_turn_id: `rt-${n}`,
    content: content ?? `Resposta ${n} da DÉLIA.`,
    epistemic_class: "HYPOTHESIS",
    limitations: [],
    generated_at: "2026-01-01T00:00:00+00:00",
    model_invocation_id: `inv-${n}`,
  };
}

function mockFetchSequence(payloads: object[]) {
  let call = 0;
  return vi.fn().mockImplementation(() => {
    const body = payloads[Math.min(call, payloads.length - 1)];
    call += 1;
    return Promise.resolve(
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function submitTurn(input: string) {
  fireEvent.change(screen.getByLabelText("Pergunte à DÉLIA"), {
    target: { value: input },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// --- S2-A — Reception ------------------------------------------------

describe("S2-A reception surface", () => {
  it("renders the reception greeting when the session has no turns", () => {
    const { container } = render(<App />);
    expect(
      screen.getByRole("heading", {
        name: "Como posso ajudar você hoje?",
      }),
    ).toBeTruthy();
    const reception = container.querySelector(".delia-reception");
    expect(reception).toBeTruthy();
    expect(reception!.textContent).toMatch(
      /dependem das informações e permissões/,
    );
    // Honest boundary — the session is transient, not persisted.
    expect(reception!.textContent).toMatch(/não é salva/);
    // The composer is present and usable from reception.
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toBeTruthy();
  });

  it("reception makes no unproven capability claims", () => {
    const { container } = render(<App />);
    const reception = container.querySelector(".delia-reception");
    expect(reception).toBeTruthy();
    // No suggestion cards / fake affordances for capabilities that
    // are not contract-proven.
    expect(
      reception!.querySelectorAll("button, a"),
    ).toHaveLength(0);
    const text = (reception!.textContent ?? "").toLowerCase();
    for (const forbidden of [
      "produtos",
      "indicadores",
      "solicitações",
      "investigar",
      "pesquisa na web",
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });

  it("first submission transitions reception to the timeline", async () => {
    vi.stubGlobal("fetch", mockFetchSequence([successPayload(1)]));
    render(<App getAccessToken={() => "t"} />);

    submitTurn("primeira pergunta");

    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );
    expect(
      screen.queryByRole("heading", {
        name: "Como posso ajudar você hoje?",
      }),
    ).toBeNull();
    expect(screen.getByRole("log")).toBeTruthy();
  });
});

// --- S3 — chat-first identity -----------------------------------------

describe("S3 chat-first visual identity", () => {
  it("reception shows the DÉLIA glyph — never the DELPI wordmark", () => {
    const { container } = render(<App />);
    const mark = container.querySelector(".delia-reception__mark");
    expect(mark).toBeTruthy();
    // Lucide Sparkles glyph — an icon, not the DELPI logo image.
    expect(mark!.querySelector("svg")).toBeTruthy();
    expect(mark!.querySelector("[role='img']")).toBeNull();
    expect(mark!.textContent).not.toContain("DELPI");
  });

  it("each timeline turn carries its role avatar", async () => {
    vi.stubGlobal("fetch", mockFetchSequence([successPayload(1)]));
    const { container } = render(<App getAccessToken={() => "t"} />);

    submitTurn("pergunta");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );

    const avatars = container.querySelectorAll(".delia-turn__avatar");
    expect(avatars).toHaveLength(2);
    // User avatar first (own message), DÉLIA avatar second.
    expect(
      avatars[0].closest(".delia-turn")!.className,
    ).toContain("delia-turn--user");
    expect(
      avatars[1].closest(".delia-turn")!.className,
    ).toContain("delia-turn--delia");
    expect(avatars[0].getAttribute("aria-hidden")).toBe("true");
  });
});

// --- S2-B — Conversation timeline ------------------------------------

describe("S2-B conversation timeline", () => {
  it("renders user and DÉLIA turns with semantic classes in order", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchSequence([successPayload(1), successPayload(2)]),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);

    submitTurn("pergunta um");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );
    submitTurn("pergunta dois");
    await waitFor(() =>
      expect(screen.getByText("Resposta 2 da DÉLIA.")).toBeTruthy(),
    );

    const items = Array.from(
      container.querySelectorAll(".delia-timeline .delia-turn"),
    );
    expect(items).toHaveLength(4);
    expect(items.map((el) => el.className)).toEqual([
      "delia-turn delia-turn--user",
      "delia-turn delia-turn--delia",
      "delia-turn delia-turn--user",
      "delia-turn delia-turn--delia",
    ]);
    expect(items[0].textContent).toContain("pergunta um");
    expect(items[3].textContent).toContain("Resposta 2 da DÉLIA.");
  });

  it("timeline is a polite log region for assistive tech", async () => {
    vi.stubGlobal("fetch", mockFetchSequence([successPayload(1)]));
    render(<App getAccessToken={() => "t"} />);
    submitTurn("olá");
    await waitFor(() => expect(screen.getByRole("log")).toBeTruthy());
    expect(screen.getByRole("log").getAttribute("aria-label")).toBe(
      "Conversa atual",
    );
  });
});

// --- S2-C — Composer -------------------------------------------------

describe("S2-C composer", () => {
  it("Enter submits the turn", async () => {
    const fetchMock = mockFetchSequence([successPayload(1)]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    const input = screen.getByLabelText("Pergunte à DÉLIA");
    fireEvent.change(input, { target: { value: "via teclado" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(
      JSON.parse(fetchMock.mock.calls[0][1].body as string).input,
    ).toBe("via teclado");
  });

  it("Shift+Enter keeps a newline instead of submitting", async () => {
    const fetchMock = mockFetchSequence([successPayload(1)]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    const input = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "linha um" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });

    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(fetchMock).not.toHaveBeenCalled();
    expect(input.value).toBe("linha um");
  });

  it("IME composition Enter does not submit", async () => {
    const fetchMock = mockFetchSequence([successPayload(1)]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    const input = screen.getByLabelText("Pergunte à DÉLIA");
    fireEvent.change(input, { target: { value: "日文" } });
    fireEvent.keyDown(input, { key: "Enter", isComposing: true });

    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("draft is preserved after a failed request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("network down")),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("pergunta importante");
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement)
        .value,
    ).toBe("pergunta importante");
  });

  it("Enter on empty input does not submit", async () => {
    const fetchMock = mockFetchSequence([successPayload(1)]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    fireEvent.keyDown(screen.getByLabelText("Pergunte à DÉLIA"), {
      key: "Enter",
    });
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

// --- S2-D — honest loading + errors ----------------------------------

describe("S2-D loading and error states", () => {
  it("shows an honest indeterminate indicator while the POST is pending", async () => {
    let resolveFetch: (value: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        () =>
          new Promise<Response>((resolve) => {
            resolveFetch = resolve;
          }),
      ),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("consulta");

    await waitFor(() =>
      expect(screen.getByRole("status")).toBeTruthy(),
    );
    const statusText = screen.getByRole("status").textContent ?? "";
    expect(statusText).toContain("processando sua solicitação");
    // Honest loading: never claims a provider/stage without evidence.
    for (const forbidden of [
      "DAVI",
      "VISTA",
      "MCP",
      "web",
      "ferramenta",
      "executando ação",
    ]) {
      expect(statusText.toLowerCase()).not.toContain(
        forbidden.toLowerCase(),
      );
    }

    resolveFetch(
      new Response(JSON.stringify(successPayload(1)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("status")).toBeNull(),
    );
  });

  it("recovers after a failure — the next turn submits normally", async () => {
    let call = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => {
        call += 1;
        if (call === 1) {
          return Promise.resolve(
            new Response(
              JSON.stringify({ code: "internal_error" }),
              {
                status: 500,
                headers: { "Content-Type": "application/json" },
              },
            ),
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify(successPayload(2)), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("primeira");
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    submitTurn("segunda");
    await waitFor(() =>
      expect(screen.getByText("Resposta 2 da DÉLIA.")).toBeTruthy(),
    );
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
