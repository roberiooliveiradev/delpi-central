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

/** Interaction assertions scope to the delia-api boundary — the app may
 *  legitimately read /core-api/me* for the user avatar identity. */
function deliaApiCalls(fetchMock: { mock: { calls: unknown[][] } }) {
  return fetchMock.mock.calls.filter(([u]) =>
    String(u).startsWith("/apps/delia-api"),
  ) as [string, RequestInit][];
}

function mockFetchSequence(payloads: object[]) {
  let call = 0;
  return vi.fn().mockImplementation((input: unknown) => {
    if (String(input).startsWith("/core-api/")) {
      return Promise.resolve(
        new Response(JSON.stringify({ name: null, has_photo: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
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
    const reception = container.querySelector(".delpi-ui-conversation-reception");
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
    const reception = container.querySelector(".delpi-ui-conversation-reception");
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
    const mark = container.querySelector(".delpi-ui-conversation-reception__avatar");
    expect(mark).toBeTruthy();
    // Lucide Sparkles glyph — an icon, not the DELPI logo image.
    expect(mark!.querySelector("svg")).toBeTruthy();
    // The DÉLIA mark is the UnifiedAvatar glyph; no raster/logo image.
    expect(mark!.querySelector("img")).toBeNull();
    expect(mark!.textContent).not.toContain("DELPI");
  });

  it("each timeline turn carries its role avatar", async () => {
    vi.stubGlobal("fetch", mockFetchSequence([successPayload(1)]));
    render(<App getAccessToken={() => "t"} />);

    submitTurn("pergunta");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );

    const items = Array.from(
      screen.getByRole("log", { name: "Conversa atual" }).children,
    );
    expect(items).toHaveLength(2);
    // The user avatar now lives in shared ConversationUserMessage chrome.
    const userAvatar = items[0].querySelector(
      ".delpi-ui-conversation-user-message__avatar",
    );
    const deliaAvatar = items[1].querySelector(".delia-turn__avatar");
    expect(userAvatar).toBeTruthy();
    expect(userAvatar?.querySelector(".delpi-ui-unified-avatar--person")).toBeTruthy();
    expect(deliaAvatar?.querySelector(".delpi-ui-unified-avatar--assistant")).toBeTruthy();
    expect(items[0].querySelector(".delpi-ui-conversation-user-message")).toBeTruthy();
    expect(items[1].classList.contains("delia-turn--delia")).toBe(true);
    expect(userAvatar?.getAttribute("aria-hidden")).toBe("true");
    expect(deliaAvatar?.getAttribute("aria-hidden")).toBe("true");
  });
});

// --- S2-B — Conversation timeline ------------------------------------

describe("S2-B conversation timeline", () => {
  it("renders user and DÉLIA turns with semantic classes in order", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchSequence([successPayload(1), successPayload(2)]),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("pergunta um");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );
    submitTurn("pergunta dois");
    await waitFor(() =>
      expect(screen.getByText("Resposta 2 da DÉLIA.")).toBeTruthy(),
    );

    const items = Array.from(
      screen.getByRole("log", { name: "Conversa atual" }).children,
    );
    expect(items).toHaveLength(4);
    // Turn order is the timeline's contract; visual message chrome is
    // owned by plugin-ui only for user turns, not by local BEM classes.
    expect(
      items.map((item) =>
        item.querySelector(".delpi-ui-conversation-user-message")
          ? "user"
          : item.classList.contains("delia-turn--delia")
            ? "delia"
            : "unknown",
      ),
    ).toEqual(["user", "delia", "user", "delia"]);
    expect(items[0].querySelector(".delpi-ui-conversation-user-message__content")?.textContent)
      .toBe("pergunta um");
    expect(items[2].querySelector(".delpi-ui-conversation-user-message__content")?.textContent)
      .toBe("pergunta dois");
    expect(items[1].querySelector(".delia-turn__content")?.textContent)
      .toBe("Resposta 1 da DÉLIA.");
    expect(items[3].querySelector(".delia-turn__content")?.textContent)
      .toBe("Resposta 2 da DÉLIA.");
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

    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    expect(
      JSON.parse(deliaApiCalls(fetchMock)[0][1].body as string).input,
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
    expect(deliaApiCalls(fetchMock)).toHaveLength(0);
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
    expect(deliaApiCalls(fetchMock)).toHaveLength(0);
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
    expect(deliaApiCalls(fetchMock)).toHaveLength(0);
  });

  it("uses the shared plugin-ui composer surface (two bands)", () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response()));
    const { container } = render(<App getAccessToken={() => "t"} />);

    const composer = container.querySelector(
      ".delpi-ui-message-composer.delia-composer",
    );
    expect(composer).toBeTruthy();
    expect(
      composer!.querySelector(".delpi-ui-message-composer__write"),
    ).toBeTruthy();
    expect(
      composer!.querySelector(".delpi-ui-message-composer__toolbar"),
    ).toBeTruthy();
  });

  it("shows the real input bound counter and the trust helper", () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response()));
    render(<App getAccessToken={() => "t"} />);

    expect(screen.getByText("0/16384")).toBeTruthy();
    expect(
      screen.getByText(
        "A DÉLIA pode cometer erros. Confirme informações importantes.",
      ),
    ).toBeTruthy();
    // The mic trigger is the only secondary action — local capture is
    // available to every legitimately admitted DÉLIA user (no dedicated
    // permission), with bounded test limits.
    const toolbar = document.querySelector(
      ".delpi-ui-message-composer__toolbar",
    )!;
    expect(toolbar.querySelectorAll("button")).toHaveLength(2);
    expect(screen.getByLabelText(/Gravar áudio|Gravação de áudio/)).toBeTruthy();
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
vi.fn().mockImplementation((input: unknown) => {
        if (String(input).startsWith("/core-api/")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({ name: null, has_photo: false }),
              { status: 200, headers: { "Content-Type": "application/json" } },
            ),
          );
        }
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

// --- Workspace layout (shared ConversationWorkspace (plugin-ui)) ----

describe("conversation workspace layout", () => {
  it("shell splits into scrollable viewport column + anchored footer", () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response()));
    const { container } = render(<App getAccessToken={() => "t"} />);

    const interaction = container.querySelector(".delpi-ui-conversation-workspace")!;
    const body = interaction.querySelector(".delpi-ui-conversation-workspace__body")!;
    const column = body.querySelector(".delpi-ui-conversation-workspace__column")!;
    const footer = interaction.querySelector(".delpi-ui-conversation-workspace__footer")!;

    // Viewport scrolls independently; footer (composer region) is a
    // sibling outside the scroll area — the composer never scrolls away.
    expect(column.querySelector(".delpi-ui-conversation-reception")).toBeTruthy();
    expect(footer.querySelector(".delia-composer")).toBeTruthy();
    expect(body.contains(footer)).toBe(false);
    expect(interaction.lastElementChild).toBe(footer);
  });

  it("root publishes the portal fill contract so the workspace owns the host height", () => {
    // `dashboard-page--fill` is the existing Portal contract that lets an
    // MFE fill .content and keep the scroll inside the app surface
    // (same class used by sibling immersive MFEs). Without it the host
    // shrinks to content height and the composer scrolls away.
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response()));
    const { container } = render(<App getAccessToken={() => "t"} />);
    const root = container.firstElementChild!;
    expect(root.classList.contains("dashboard-page--fill")).toBe(true);
  });

  it("timeline replaces reception inside the reading column", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(successPayload(1)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);

    submitTurn("olá");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );

    const column = container.querySelector(".delpi-ui-conversation-workspace__column")!;
    expect(column.querySelector(".delia-timeline")).toBeTruthy();
    expect(column.querySelector(".delpi-ui-conversation-reception")).toBeNull();
  });

  it("no host-context debug line in the conversation UI", () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response()));
    const { container } = render(
      <App getAccessToken={() => "t"} pathname="/apps/delia" />,
    );
    expect(container.querySelector(".delia-host-meta")).toBeNull();
    expect(container.textContent).not.toContain("Contexto de host");
  });

  it("error alert stays in the anchored footer, draft preserved", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("network down")),
    );
    const { container } = render(<App getAccessToken={() => "t"} />);

    submitTurn("pergunta");
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());

    const footer = container.querySelector(".delpi-ui-conversation-workspace__footer")!;
    expect(footer.querySelector(".delpi-ui-conversation-error")).toBeTruthy();
    expect(
      footer.querySelector(".delpi-ui-message-composer"),
    ).toBeTruthy();
  });
});
