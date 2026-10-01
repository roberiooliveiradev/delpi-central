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
