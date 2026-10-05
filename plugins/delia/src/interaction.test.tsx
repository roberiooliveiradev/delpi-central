import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const SUCCESS_PAYLOAD = {
  session_id: "s-1",
  user_turn_id: "ut-1",
  result_turn_id: "rt-1",
  content: "Resposta determinística da DÉLIA.",
  epistemic_class: "HYPOTHESIS",
  limitations: ["deterministic_test_adapter"],
  generated_at: "2026-01-01T00:00:00+00:00",
  model_invocation_id: "inv-1",
};

function mockFetchOk() {
  return vi.fn().mockResolvedValue(
    new Response(JSON.stringify(SUCCESS_PAYLOAD), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
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

describe("DÉLIA interaction surface", () => {
  it("renders the interaction UI (input + submit)", () => {
    render(<App />);
    expect(
      screen.getByLabelText("Interação com a DÉLIA"),
    ).toBeTruthy();
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeTruthy();
  });

  it("input accepts text", () => {
    render(<App />);
    const input = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "olá DÉLIA" } });
    expect(input.value).toBe("olá DÉLIA");
  });

  it("submit calls the delia-api endpoint with host bearer token", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    const getAccessToken = vi.fn().mockReturnValue("host-token");

    render(<App getAccessToken={getAccessToken} />);
    submitTurn("olá");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/apps/delia-api/interaction/turns");
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>).Authorization).toBe(
      "Bearer host-token",
    );
    expect(JSON.parse(init.body as string)).toEqual({ input: "olá" });
    // Token comes from the host per request; nothing is persisted.
    expect(localStorage.length).toBe(0);
  });

  it("renders the DÉLIA response on success", async () => {
    vi.stubGlobal("fetch", mockFetchOk());
    render(<App getAccessToken={() => "t"} />);

    submitTurn("olá");

    await waitFor(() =>
      expect(
        screen.getByText("Resposta determinística da DÉLIA."),
      ).toBeTruthy(),
    );
    expect(screen.getByText("Você")).toBeTruthy();
    expect(screen.getByText(/HYPOTHESIS/)).toBeTruthy();
  });

  it("renders a bounded error on API failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: "Forbidden", code: "forbidden" }),
          { status: 403, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("oi");

    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toContain(
      "não autorizado",
    );
  });

  it("does not submit empty input", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    const button = screen.getByRole("button", {
      name: "Enviar",
    }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fails safely when no host token is available", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => undefined} />);

    submitTurn("oi");

    expect(fetchMock).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toContain(
      "Token de acesso indisponível",
    );
  });

  it("disables submit while a request is in flight", async () => {
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

    submitTurn("oi");

    await waitFor(() =>
      expect(
        (screen.getByRole("button", {
          name: "Enviando…",
        }) as HTMLButtonElement).disabled,
      ).toBe(true),
    );
    resolveFetch(
      new Response(JSON.stringify(SUCCESS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Enviar" })).toBeTruthy(),
    );
  });

  it("does not render provider/model/agent pickers or tool controls", () => {
    const { container } = render(<App />);
    expect(container.querySelector("select")).toBeNull();
    const text = (container.textContent ?? "").toLowerCase();
    for (const forbidden of [
      "modelo",
      "model",
      "agente",
      "provider",
      "tools",
      "executar",
      "token",
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });

  it("host permissions props are never sent as backend authority", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    render(
      <App
        getAccessToken={() => "t"}
        permissions={["admin.everything"]}
        isSuperadmin={true}
      />,
    );

    submitTurn("oi");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const body = JSON.parse(init.body as string) as Record<string, unknown>;
    expect(Object.keys(body)).toEqual(["input"]);
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer t");
    expect(headers["X-Permissions"]).toBeUndefined();
  });
});

// --- C3-INTERACTION-CONTINUITY-01 -----------------------------------

function successPayload(n: number) {
  return {
    session_id: `s-${n}`,
    user_turn_id: `ut-${n}`,
    result_turn_id: `rt-${n}`,
    content: `Resposta ${n} da DÉLIA.`,
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

describe("DÉLIA transient multi-turn continuity", () => {
  it("second prompt keeps the first turn visible", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchSequence([successPayload(1), successPayload(2)]),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("primeira");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );
    submitTurn("segunda");
    await waitFor(() =>
      expect(screen.getByText("Resposta 2 da DÉLIA.")).toBeTruthy(),
    );
    // First turn is still rendered — the list is transient UI memory.
    expect(screen.getByText("primeira")).toBeTruthy();
    expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy();
  });

  it("second request includes bounded USER_INPUT/DELIA_RESULT context", async () => {
    const fetchMock = mockFetchSequence([
      successPayload(1),
      successPayload(2),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    submitTurn("primeira pergunta");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(
      JSON.parse(fetchMock.mock.calls[0][1].body as string),
    ).toEqual({ input: "primeira pergunta" });

    submitTurn("segunda pergunta");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const body = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(body.input).toBe("segunda pergunta");
    expect(body.context).toEqual([
      { kind: "USER_INPUT", content: "primeira pergunta" },
      {
        kind: "DELIA_RESULT",
        content: "Resposta 1 da DÉLIA.",
        epistemic_class: "HYPOTHESIS",
      },
    ]);
  });

  it("third turn preserves chronological context ordering", async () => {
    const fetchMock = mockFetchSequence([
      successPayload(1),
      successPayload(2),
      successPayload(3),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    submitTurn("p1");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    submitTurn("p2");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    submitTurn("p3");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));

    const body = JSON.parse(fetchMock.mock.calls[2][1].body as string);
    expect(
      body.context.map((t: { kind: string }) => t.kind),
    ).toEqual([
      "USER_INPUT",
      "DELIA_RESULT",
      "USER_INPUT",
      "DELIA_RESULT",
    ]);
    expect(body.context[0].content).toBe("p1");
    expect(body.context[2].content).toBe("p2");
  });

  it("context never carries authority, provider, or token fields", async () => {
    const fetchMock = mockFetchSequence([
      successPayload(1),
      successPayload(2),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    render(
      <App
        getAccessToken={() => "secret-token"}
        permissions={["x"]}
        isSuperadmin={true}
      />,
    );

    submitTurn("p1");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    submitTurn("p2");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    const serialized = JSON.stringify(
      JSON.parse(fetchMock.mock.calls[1][1].body as string),
    ).toLowerCase();
    for (const forbidden of [
      "permission",
      "superadmin",
      "token",
      "secret",
      "provider",
      "model",
      "system",
      "tool",
    ]) {
      expect(serialized).not.toContain(forbidden);
    }
  });

  it("remount starts with an empty conversation", async () => {
    vi.stubGlobal("fetch", mockFetchSequence([successPayload(1)]));
    const first = render(<App getAccessToken={() => "t"} />);
    submitTurn("p1");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );
    first.unmount();

    render(<App getAccessToken={() => "t"} />);
    expect(screen.queryByText("Resposta 1 da DÉLIA.")).toBeNull();
    expect(screen.queryByText("p1")).toBeNull();
  });

  it("error does not erase prior successful turns", async () => {
    let call = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => {
        call += 1;
        if (call === 1) {
          return Promise.resolve(
            new Response(JSON.stringify(successPayload(1)), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return Promise.resolve(
          new Response(
            JSON.stringify({ code: "model_unavailable" }),
            { status: 503, headers: { "Content-Type": "application/json" } },
          ),
        );
      }),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("p1");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );
    submitTurn("p2");
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    // Prior turns survive the failed request.
    expect(screen.getByText("p1")).toBeTruthy();
    expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy();
  });

  it("never touches localStorage/sessionStorage/IndexedDB", async () => {
    const localSet = vi.spyOn(Storage.prototype, "setItem");
    const indexedSpy = vi.fn();
    vi.stubGlobal("indexedDB", { open: indexedSpy });
    vi.stubGlobal("fetch", mockFetchSequence([successPayload(1)]));

    render(<App getAccessToken={() => "t"} />);
    submitTurn("p1");
    await waitFor(() =>
      expect(screen.getByText("Resposta 1 da DÉLIA.")).toBeTruthy(),
    );

    expect(localSet).not.toHaveBeenCalled();
    expect(indexedSpy).not.toHaveBeenCalled();
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});

// --- §6.130: provider-neutral workspace context ---

describe("DÉLIA workspace context propagation", () => {
  it("sends the bounded workspace hint when the host provides one", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    const getWorkspaceContext = vi.fn().mockReturnValue({
      host_app_id: "tv-dashboard",
      view_ref: "deck_editor",
      selected_entity_ref: {
        entity_type: "slide",
        entity_id: "sl-9",
        source_system: "vista",
      },
    });

    render(
      <App
        getAccessToken={() => "t"}
        getWorkspaceContext={getWorkspaceContext}
      />,
    );
    submitTurn("descreva este slide");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const body = JSON.parse(
      fetchMock.mock.calls[0][1].body as string,
    ) as Record<string, unknown>;
    expect(getWorkspaceContext).toHaveBeenCalled();
    expect(body.workspace).toEqual({
      host_app_id: "tv-dashboard",
      view_ref: "deck_editor",
      selected_entity_ref: {
        entity_type: "slide",
        entity_id: "sl-9",
        source_system: "vista",
      },
    });
  });

  it("omits workspace when the host has no context", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    render(
      <App
        getAccessToken={() => "t"}
        getWorkspaceContext={() => null}
      />,
    );

    submitTurn("olá");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const body = JSON.parse(
      fetchMock.mock.calls[0][1].body as string,
    ) as Record<string, unknown>;
    expect(body.workspace).toBeUndefined();
  });

  it("workspace hint carries no authority or credentials", async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal("fetch", fetchMock);
    render(
      <App
        getAccessToken={() => "secret-token"}
        getWorkspaceContext={() => ({
          host_app_id: "tv-dashboard",
          view_ref: "deck_editor",
        })}
      />,
    );

    submitTurn("olá");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const serialized = JSON.stringify(
      fetchMock.mock.calls[0][1].body as string,
    ).toLowerCase();
    for (const forbidden of [
      "permission",
      "superadmin",
      "secret-token",
      "authorization",
    ]) {
      expect(serialized).not.toContain(forbidden);
    }
  });
});

// --- ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03: confirmation ---

const CONFIRMATION_REQUEST = {
  session_id: "s-1",
  capability_ref: "vista.prepare_change",
  proposal_digest: "a".repeat(64),
  preview_fingerprint: "b".repeat(64),
  expires_at_epoch: 9999999999,
};

function confirmationPayload(n: number) {
  return {
    ...successPayload(n),
    content: `Prévia ${n}: confirme a alteração.`,
    confirmation_request: CONFIRMATION_REQUEST,
  };
}

describe("DÉLIA governed-write confirmation surface", () => {
  it("renders a confirmation card when confirmation_request arrives", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchSequence([confirmationPayload(1)]),
    );
    render(<App getAccessToken={() => "t"} />);

    submitTurn("altere o nome");
    await waitFor(() =>
      expect(
        screen.getByRole("group", { name: "Confirmação pendente" }),
      ).toBeTruthy(),
    );
    expect(
      screen.getByRole("button", { name: "Confirmar" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Cancelar" }),
    ).toBeTruthy();
    // The digests are transport echoes — never rendered to the user.
    expect(screen.queryByText(/a{64}/)).toBeNull();
  });

  it("Confirmar echoes the bounded digests back verbatim", async () => {
    const fetchMock = mockFetchSequence([
      confirmationPayload(1),
      successPayload(2),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    submitTurn("altere o nome");
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Confirmar" }),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const body = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(body.confirmation).toEqual({
      decision: "CONFIRM",
      proposal_digest: "a".repeat(64),
      preview_fingerprint: "b".repeat(64),
      session_id: "s-1",
    });
    // No raw owner handle exists client-side to leak.
    expect(JSON.stringify(body)).not.toContain("proposal_handle");
  });

  it("Cancelar submits decision REJECT", async () => {
    const fetchMock = mockFetchSequence([
      confirmationPayload(1),
      successPayload(2),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    submitTurn("altere o nome");
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Cancelar" }),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const body = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(body.confirmation.decision).toBe("REJECT");
  });

  it("an answered confirmation card is consumed (single use)", async () => {
    const fetchMock = mockFetchSequence([
      confirmationPayload(1),
      successPayload(2),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    submitTurn("altere o nome");
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Confirmar" }),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    await waitFor(() =>
      expect(
        screen.queryByRole("group", { name: "Confirmação pendente" }),
      ).toBeNull(),
    );
  });
});
