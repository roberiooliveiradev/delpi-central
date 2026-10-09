import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import {
  DELIA_DEMO_BANNER,
  resolveDemoScenario,
} from "./demo/demoMode";

function setDemoLocation(scenario?: string) {
  const search =
    scenario === undefined ? "/" : `/?delia-demo=${scenario}`;
  window.history.pushState({}, "", search);
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
  window.history.pushState({}, "", "/");
});

// --- resolver unit tests -------------------------------------------

describe("resolveDemoScenario", () => {
  it("returns null when the query param is absent", () => {
    expect(resolveDemoScenario("/")).toBeNull();
    expect(resolveDemoScenario("")).toBeNull();
  });

  it("resolves each documented scenario", () => {
    for (const scenario of [
      "simple",
      "long",
      "clarification",
      "source_unavailable",
      "authz_denied",
      "precondition",
      "confirmation",
      "error",
      "loading",
    ]) {
      expect(resolveDemoScenario(`/?delia-demo=${scenario}`)).toBe(
        scenario,
      );
    }
  });

  it("falls back to simple for unknown values and empty param", () => {
    expect(resolveDemoScenario("/?delia-demo=bogus")).toBe("simple");
    expect(resolveDemoScenario("/?delia-demo")).toBe("simple");
  });
});

// --- App integration — demo OFF -------------------------------------

describe("demo mode OFF", () => {
  it("does not render the demo banner by default", () => {
    setDemoLocation();
    render(<App />);
    expect(screen.queryByText(DELIA_DEMO_BANNER)).toBeNull();
  });

  it("keeps the real backend path when demo is off", async () => {
    setDemoLocation();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          session_id: "s-1",
          user_turn_id: "ut-1",
          result_turn_id: "rt-1",
          content: "Resposta real.",
          epistemic_class: "HYPOTHESIS",
          limitations: [],
          generated_at: "2026-01-01T00:00:00+00:00",
          model_invocation_id: "inv-1",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);
    submitTurn("pergunta real");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(screen.queryByText(DELIA_DEMO_BANNER)).toBeNull();
  });
});

// --- App integration — demo ON --------------------------------------

describe("demo mode ON", () => {
  it("renders the visible simulated-data banner", () => {
    setDemoLocation("simple");
    render(<App />);
    expect(screen.getByText(DELIA_DEMO_BANNER)).toBeTruthy();
  });

  it("appends user + simulated turn without any network call", async () => {
    setDemoLocation("simple");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    submitTurn("pergunta de teste");
    await waitFor(() =>
      expect(
        screen.getByText(/resposta de demonstração da DÉLIA/),
      ).toBeTruthy(),
    );
    expect(screen.getByText("pergunta de teste")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("marks simulated responses as simulated, never grounded", async () => {
    setDemoLocation("simple");
    render(<App />);
    submitTurn("pergunta");
    await waitFor(() =>
      expect(
        screen.getByText(/resposta simulada — nenhum dado operacional/),
      ).toBeTruthy(),
    );
    expect(screen.queryByText(/grounded/i)).toBeNull();
  });

  it("supports multiple turns in the same demo session", async () => {
    setDemoLocation("simple");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<App />);
    submitTurn("primeira");
    await waitFor(() =>
      expect(container.querySelectorAll(".delia-turn").length).toBe(2),
    );
    submitTurn("segunda");
    await waitFor(() =>
      expect(container.querySelectorAll(".delia-turn").length).toBe(4),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("long scenario renders the extended response", async () => {
    setDemoLocation("long");
    render(<App />);
    submitTurn("pergunta");
    await waitFor(() =>
      expect(screen.getByText(/Terceiro parágrafo/)).toBeTruthy(),
    );
  });

  it("clarification scenario renders the semantic state", async () => {
    setDemoLocation("clarification");
    render(<App />);
    submitTurn("pergunta");
    await waitFor(() =>
      expect(
        screen.getByText(/preciso de um esclarecimento/),
      ).toBeTruthy(),
    );
  });

  it("source_unavailable scenario renders the honest state", async () => {
    setDemoLocation("source_unavailable");
    render(<App />);
    submitTurn("pergunta");
    await waitFor(() =>
      expect(
        screen.getByText(/fonte necessária .* indisponível/),
      ).toBeTruthy(),
    );
  });

  it("authz_denied scenario renders the honest denial", async () => {
    setDemoLocation("authz_denied");
    render(<App />);
    submitTurn("pergunta");
    await waitFor(() =>
      expect(
        screen.getByText(/não possui autorização/),
      ).toBeTruthy(),
    );
  });

  it("precondition scenario renders the owner-hint notice", async () => {
    setDemoLocation("precondition");
    render(<App />);
    submitTurn("pergunta");
    await waitFor(() =>
      expect(
        screen.getByText(/demo_precondition_required/),
      ).toBeTruthy(),
    );
  });

  it("error scenario shows an error and preserves the draft", async () => {
    setDemoLocation("error");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    submitTurn("minha pergunta importante");
    await waitFor(() =>
      expect(screen.getByRole("alert")).toBeTruthy(),
    );
    expect(screen.getByRole("alert").textContent).toContain(
      "Falha simulada",
    );
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement)
        .value,
    ).toBe("minha pergunta importante");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("loading scenario shows the processing badge before responding", async () => {
    setDemoLocation("loading");
    render(<App />);
    submitTurn("pergunta");
    expect(
      screen.getByText(/está processando sua solicitação/),
    ).toBeTruthy();
    await waitFor(
      () =>
        expect(
          screen.getByText(/cenário de espera simulada/),
        ).toBeTruthy(),
      { timeout: 3000 },
    );
  });

  it("confirmation demo is visual-only — no network, honest ack", async () => {
    setDemoLocation("confirmation");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    submitTurn("executar operação");
    const confirm = await screen.findByRole("button", {
      name: "Confirmar",
    });
    fireEvent.click(confirm);
    await waitFor(() =>
      expect(
        screen.getByText(/confirmada apenas visualmente/),
      ).toBeTruthy(),
    );
    expect(fetchMock).not.toHaveBeenCalled();
    // The pending card is resolved — buttons are gone.
    expect(
      screen.queryByRole("button", { name: "Confirmar" }),
    ).toBeNull();
  });
});
