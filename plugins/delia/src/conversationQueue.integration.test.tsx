import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

/**
 * Doc 71/122 §11 (F03-B) — integration of the ephemeral conversation
 * queue with the REAL sendTurn flow. The fetch mock is a controllable
 * gate: each delia-api call resolves only when the test releases it,
 * so "A in-flight while B/C queue" is exercised deterministically and
 * every assertion counts actual POSTs — not just rendered state.
 */

function successPayload(n: number, extra: Record<string, unknown> = {}) {
  return {
    session_id: `s-${n}`,
    user_turn_id: `ut-${n}`,
    result_turn_id: `rt-${n}`,
    content: `Resposta ${n} da DÉLIA.`,
    epistemic_class: "HYPOTHESIS",
    limitations: [],
    generated_at: "2026-01-01T00:00:00+00:00",
    model_invocation_id: `inv-${n}`,
    ...extra,
  };
}

const CONFIRMATION_REQUEST = {
  session_id: "s-conf",
  proposal_digest: "a".repeat(64),
  preview_fingerprint: "b".repeat(64),
  expires_at_epoch: 9999999999,
  pending_purpose: "execution_scope_plus_owner_confirmation",
};

type Gate = { resolve: (payload?: object) => void; reject: (status?: number) => void };

/**
 * Fetch mock: delia-api calls park on manual gates (in order). Core
 * identity and dictation status resolve immediately. Exposes the
 * captured request bodies so tests verify WHAT was sent, in order.
 */
function mockFetchGated() {
  const gates: Gate[] = [];
  const bodies: Record<string, unknown>[] = [];
  const fetchMock = vi.fn().mockImplementation(
    (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.startsWith("/core-api/")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({ name: null, has_photo: false }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (url.startsWith("/apps/delia-api/dictation")) {
        return Promise.resolve(
          new Response(JSON.stringify({ code: "dictation_unavailable" }), {
            status: 404,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      if (url.startsWith("/apps/delia-api/interaction")) {
        if (init?.body) bodies.push(JSON.parse(String(init.body)));
        return new Promise<Response>((resolvePromise, rejectPromise) => {
          gates.push({
            resolve: (payload) =>
              resolvePromise(
                new Response(JSON.stringify(payload ?? successPayload(gates.length)), {
                  status: 200,
                  headers: { "Content-Type": "application/json" },
                }),
              ),
            reject: (status = 500) =>
              resolvePromise(
                new Response(JSON.stringify({ message: "falha" }), {
                  status,
                  headers: { "Content-Type": "application/json" },
                }),
              ) ?? rejectPromise(new Error("http")),
          });
        });
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    },
  );
  return { fetchMock, gates, bodies };
}

function deliaApiCalls(fetchMock: { mock: { calls: unknown[][] } }) {
  return fetchMock.mock.calls.filter(([u]) =>
    String(u).startsWith("/apps/delia-api/interaction"),
  );
}

function typeDraft(text: string) {
  fireEvent.change(screen.getByLabelText("Pergunte à DÉLIA"), {
    target: { value: text },
  });
}

function sendDraft() {
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

function enqueueDraft() {
  fireEvent.click(
    screen.getByRole("button", { name: "Adicionar à fila" }),
  );
}

function expandQueue() {
  fireEvent.click(
    screen.getByRole("button", { name: /solicitaç(ão|ões) aguardando/ }),
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("F03-B ephemeral conversation queue — admission", () => {
  it("idle submit sends immediately without creating a pending", async () => {
    const { fetchMock, gates } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("pergunta A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    expect(gates).toHaveLength(1);
    expect(
      screen.queryByLabelText("Fila de solicitações da conversa"),
    ).toBeNull();
  });

  it("while responding, the composer offers Adicionar à fila and typing stays enabled", async () => {
    const { fetchMock } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("pergunta A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));

    const input = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    expect(input.disabled).toBe(false);
    expect(
      screen.getByRole("button", { name: "Adicionar à fila" }),
    ).toBeTruthy();
  });

  it("enqueue admits B/C without a second POST and renders real pendings", async () => {
    const { fetchMock } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("pergunta A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));

    typeDraft("pergunta B");
    enqueueDraft();
    typeDraft("pergunta C");
    enqueueDraft();

    // Enqueue cleared the draft and created exactly 2 pendings.
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement)
        .value,
    ).toBe("");
    expect(
      screen.getByRole("button", { name: /2 solicitações aguardando/ }),
    ).toBeTruthy();
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);

    expandQueue();
    expect(screen.getByText("pergunta B")).toBeTruthy();
    expect(screen.getByText("pergunta C")).toBeTruthy();
  });

  it("Enter key enqueues while in-flight", async () => {
    const { fetchMock } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("pergunta A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));

    const input = screen.getByLabelText("Pergunte à DÉLIA");
    fireEvent.change(input, { target: { value: "pergunta B" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });

    expect(
      screen.getByRole("button", { name: /1 solicitação aguardando/ }),
    ).toBeTruthy();
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);
  });
});

describe("F03-B ephemeral conversation queue — sequential dispatch", () => {
  it("A completes → B dispatched once → C dispatched once → surface disappears", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("pergunta A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("pergunta B");
    enqueueDraft();
    typeDraft("pergunta C");
    enqueueDraft();
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);

    gates[0].resolve(successPayload(1));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));
    expect(bodies[1].input).toBe("pergunta B");
    // B is in-flight: queue now shows only C.
    expect(
      screen.getByRole("button", { name: /1 solicitação aguardando/ }),
    ).toBeTruthy();

    gates[1].resolve(successPayload(2));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(3));
    expect(bodies[2].input).toBe("pergunta C");

    gates[2].resolve(successPayload(3));
    await waitFor(() =>
      expect(
        screen.queryByLabelText("Fila de solicitações da conversa"),
      ).toBeNull(),
    );
    expect(deliaApiCalls(fetchMock)).toHaveLength(3);
  });

  it("dispatched item context includes the just-finished response", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("pergunta A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("pergunta B");
    enqueueDraft();

    gates[0].resolve(successPayload(1));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));

    // B's prior-turn context must contain A's user turn AND A's result —
    // proving the context was built after the completion committed.
    const ctxTurns =
      (bodies[1].context as { kind: string; content: string }[] | undefined) ??
      [];
    expect(
      ctxTurns.some(
        (t) => t.kind === "USER_INPUT" && t.content === "pergunta A",
      ),
    ).toBe(true);
    expect(
      ctxTurns.some(
        (t) => t.kind === "DELIA_RESULT" && t.content === "Resposta 1 da DÉLIA.",
      ),
    ).toBe(true);
  });

  it("reorder while pending changes the next dispatched item", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("B");
    enqueueDraft();
    typeDraft("C");
    enqueueDraft();

    expandQueue();
    fireEvent.click(
      screen.getByRole("button", { name: 'Mover "C" para cima' }),
    );

    gates[0].resolve(successPayload(1));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));
    expect(bodies[1].input).toBe("C");
    gates[1].resolve(successPayload(2));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(3));
    expect(bodies[2].input).toBe("B");
  });

  it("removing a pending prevents its dispatch", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("B");
    enqueueDraft();
    typeDraft("C");
    enqueueDraft();

    expandQueue();
    fireEvent.click(
      screen.getByRole("button", { name: 'Remover "B" da fila' }),
    );

    gates[0].resolve(successPayload(1));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));
    expect(bodies[1].input).toBe("C");
    // B was consumed nowhere — it must never be sent.
    expect(bodies.map((b) => b.input)).not.toContain("B");
  });
});

describe("F03-B ephemeral conversation queue — pause and gates", () => {
  it("failed turn pauses dispatch; pendings preserved; explicit resume continues", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("B");
    enqueueDraft();

    gates[0].reject(500);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toBeTruthy(),
    );
    // No automatic continuation despite an idle transport.
    await new Promise((r) => setTimeout(r, 30));
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);
    expect(
      screen.getByRole("button", { name: /1 solicitação aguardando/ }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Retomar fila" }),
    ).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Retomar fila" }));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));
    expect(bodies[1].input).toBe("B");
  });

  it("user stop pauses dispatch; resume sends the preserved pending", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("B");
    enqueueDraft();

    fireEvent.click(
      screen.getByRole("button", { name: "Interromper resposta" }),
    );
    await new Promise((r) => setTimeout(r, 30));
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);
    expect(
      screen.getByRole("button", { name: "Retomar fila" }),
    ).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Retomar fila" }));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));
    expect(bodies[1].input).toBe("B");
    void gates;
  });

  it("pending governed confirmation blocks queue progression until decided", async () => {
    const { fetchMock, gates, bodies } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("altere o nome");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("pergunta B");
    enqueueDraft();

    gates[0].resolve(
      successPayload(1, { confirmation_request: CONFIRMATION_REQUEST }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Confirmar e executar" }),
      ).toBeTruthy(),
    );
    // Turn A finished BUT a governed decision is pending — B must not
    // dispatch on its own.
    await new Promise((r) => setTimeout(r, 30));
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);

    // Deciding sends the bound decision turn (no free text), then B
    // follows only after that turn completes cleanly.
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar e executar" }),
    );
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(2));
    const decisionBody = bodies[1];
    expect(decisionBody.command).toBeTruthy();
    gates[1].resolve(successPayload(2));
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(3));
    expect(bodies[2].input).toBe("pergunta B");
  });
});

describe("F03-B ephemeral conversation queue — regressions", () => {
  it("no backend calls are used to manage the queue itself", async () => {
    const { fetchMock, gates } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    render(<App getAccessToken={() => "t"} />);

    typeDraft("A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("B");
    enqueueDraft();
    typeDraft("C");
    enqueueDraft();
    expandQueue();
    fireEvent.click(
      screen.getByRole("button", { name: 'Mover "C" para cima' }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: 'Remover "B" da fila' }),
    );
    // Only the in-flight turn touched the API.
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);
    void gates;
  });

  it("unmount discards the queue — nothing is dispatched or persisted", async () => {
    const { fetchMock } = mockFetchGated();
    vi.stubGlobal("fetch", fetchMock);
    const { unmount } = render(<App getAccessToken={() => "t"} />);

    typeDraft("A");
    sendDraft();
    await waitFor(() => expect(deliaApiCalls(fetchMock)).toHaveLength(1));
    typeDraft("B");
    enqueueDraft();
    unmount();
    await new Promise((r) => setTimeout(r, 30));
    expect(deliaApiCalls(fetchMock)).toHaveLength(1);
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
  });
});
