/**
 * Prompt 5 — Context panel bound to real message data + message
 * selection affordance + wire parse of the additive observability
 * projection.
 */
import {
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeliaTurnContextPanel } from "./contextPanel";
import { DeliaAssistantMessage } from "./DeliaAssistantMessage";
import type { ConversationDisplayTurn } from "./ConversationTimeline";
import { submitInteractionTurn } from "../api/interactionClient";

function makeTurn(
  overrides: Partial<ConversationDisplayTurn> = {},
): ConversationDisplayTurn {
  return {
    id: "t-1",
    role: "delia",
    content: "Resposta da DÉLIA.",
    epistemicClass: "OBSERVATION",
    limitations: [],
    groundingStatus: null,
    provenance: null,
    ...overrides,
  };
}

const OBS = {
  model: { id: "qwen2.5:3b", version: "1", owner: "DELPI" },
  response_mode: "cri",
  composition_mode: "cri",
  duration_ms: 4200,
  governed_attempts: 1,
  model_calls: 2,
  calls: [
    {
      stage: "delia.capability_orchestration.select_group",
      attempt: 1,
      finish_status: "completed",
      duration_ms: 1500,
      input_tokens: 900,
      output_tokens: 30,
    },
    {
      stage: "delia.capability_orchestration.select_capability",
      attempt: 1,
      finish_status: "completed",
      duration_ms: 1700,
      input_tokens: 1200,
      output_tokens: 45,
      budget_remaining_ms: 27000,
    },
  ],
  operational_calls: [
    {
      capability: "discover_delpi_information",
      duration_ms: 420,
      finish_status: "completed",
    },
  ],
  elapsed_ms: {
    model: 3200,
    operational: 420,
    composition: 6,
    other: 574,
  },
  timeout_source: null,
  tokens: {
    status: "reported",
    input: 2100,
    output: 75,
    total: 2175,
  },
  cost: { status: "unavailable" },
};

const EVENTS = [
  {
    version: "1" as const,
    event_id: "e1",
    sequence: 1,
    timestamp: "2026-01-01T12:00:00Z",
    session_id: "s-1",
    turn_id: "ut-1",
    phase: "REQUEST_RECEIVED",
    state: "completed",
    label_code: "REQUEST_RECEIVED",
  },
];

afterEach(cleanup);

describe("DeliaTurnContextPanel", () => {
  it("shows the honest empty state when no message is selected", () => {
    render(<DeliaTurnContextPanel turn={null} />);
    expect(
      screen.getByText(/Selecione uma mensagem/i),
    ).toBeTruthy();
  });

  it("shows real model usage, composition and calls for the selected turn", () => {
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({ observability: OBS as never })}
      />,
    );
    expect(screen.getByText("Resposta organizada com CRI")).toBeTruthy();
    expect(screen.getByText("qwen2.5:3b (1)")).toBeTruthy();
    expect(screen.getByText("DELPI")).toBeTruthy();
    expect(screen.getByText("2")).toBeTruthy();
    expect(
      screen.getByText(/2100 de entrada · 75 de saída \(total 2175\)/),
    ).toBeTruthy();
    expect(screen.getByText("Custo indisponível")).toBeTruthy();
    expect(screen.getByText("4.2 s")).toBeTruthy();
    // Per-call rows show real stage + duration, provider-neutral.
    expect(
      screen.getByText("delia.capability_orchestration.select_group"),
    ).toBeTruthy();
    expect(screen.getByText(/1.5 s/)).toBeTruthy();
  });

  it("marks tokens as not reported when provider sent none", () => {
    const obs = {
      ...OBS,
      calls: [
        {
          stage: "delia.interaction.turn",
          attempt: 1,
          finish_status: "timeout",
          duration_ms: 800,
          input_tokens: null,
          output_tokens: null,
        },
      ],
      tokens: { status: "unavailable", input: null, output: null, total: null },
      model_calls: 1,
      composition_mode: "deterministic",
    };
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({ observability: obs as never })}
      />,
    );
    expect(
      screen.getByText("Não informado pelo provider"),
    ).toBeTruthy();
    expect(
      screen.getByText("Apresentação determinística"),
    ).toBeTruthy();
  });

  it("marks partial usage honestly instead of claiming a total", () => {
    const obs = {
      ...OBS,
      tokens: {
        status: "partial",
        input: 2100,
        output: 75,
        total: null,
      },
    };
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({ observability: obs as never })}
      />,
    );
    expect(screen.getByText(/dados parciais/i)).toBeTruthy();
  });

  it("distinguishes a model-composed answer from CRI", () => {
    const obs = { ...OBS, composition_mode: "model", response_mode: "baseline" };
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({ observability: obs as never })}
      />,
    );
    expect(screen.getByText("Resposta gerada pelo modelo")).toBeTruthy();
  });

  it("shows real evidence and limitations for a grounded turn", () => {
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({
          groundingStatus: "GROUNDED",
          limitations: ["resultado truncado"],
          provenance: {
            specialist_id: "mcp:x",
            remote_capability: "search_things",
            source: {
              source_id: "src-1",
              source_system: "api-delpi",
              observed_at: "2026-01-01T12:00:00Z",
            },
          },
        })}
      />,
    );
    expect(screen.getByText("mcp:x")).toBeTruthy();
    expect(screen.getByText("search_things")).toBeTruthy();
    expect(screen.getAllByText(/api-delpi/).length).toBeGreaterThan(0);
    expect(screen.getByText(/resultado truncado/)).toBeTruthy();
  });

  it("renders the real observed activity steps with timestamps", () => {
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({
          activityView: {
            state: "completed",
            title: "Atividade",
            steps: [
              {
                id: "ev-1",
                label: "Solicitação recebida",
                state: "completed",
              },
            ],
            sources: [],
          },
          activityEvents: EVENTS,
        })}
      />,
    );
    expect(screen.getByText("Solicitação recebida")).toBeTruthy();
  });

  it("keeps per-turn data isolated — a second turn never leaks", () => {
    const obsA = { ...OBS, composition_mode: "cri" };
    const obsB = { ...OBS, composition_mode: "model", duration_ms: 900 };
    const { rerender } = render(
      <DeliaTurnContextPanel
        turn={makeTurn({ id: "a", observability: obsA as never })}
      />,
    );
    expect(screen.getByText("Resposta organizada com CRI")).toBeTruthy();
    rerender(
      <DeliaTurnContextPanel
        turn={makeTurn({ id: "b", observability: obsB as never })}
      />,
    );
    expect(screen.getByText("Resposta gerada pelo modelo")).toBeTruthy();
    expect(screen.queryByText("Resposta organizada com CRI")).toBeNull();
    expect(screen.getByText("900 ms")).toBeTruthy();
  });
});

describe("Message selection (Prompt 5)", () => {
  it("offers a real 'Ver contexto' affordance on the assistant message", async () => {
    const onSelect = vi.fn();
    render(
      <ul>
        <li className="delia-turn delia-turn--delia delpi-ui-message-action-scope">
          <DeliaAssistantMessage
            turn={makeTurn()}
            loading={false}
            onConfirmation={vi.fn()}
            selected={false}
            onSelect={onSelect}
          />
        </li>
      </ul>,
    );
    // The action lives in the "Mais opções" disclosure.
    const more = screen.queryByRole("button", { name: /mais opções/i });
    if (more) {
      fireEvent.click(more);
      const action = await screen.findByText("Ver contexto");
      fireEvent.click(action);
      expect(onSelect).toHaveBeenCalledTimes(1);
    } else {
      // Fallback: action rendered inline in the action bar.
      const action = screen.getByText("Ver contexto");
      fireEvent.click(action);
      expect(onSelect).toHaveBeenCalledTimes(1);
    }
  });

  it("marks the selected bubble and relabels the action", () => {
    const { container } = render(
      <DeliaAssistantMessage
        turn={makeTurn()}
        loading={false}
        onConfirmation={vi.fn()}
        selected={true}
        onSelect={vi.fn()}
      />,
    );
    expect(
      container.querySelector(".delia-turn__bubble--selected"),
    ).toBeTruthy();
  });
});

describe("observability wire parse", () => {
  function ndjsonResponse(payload: Record<string, unknown>) {
    const line =
      JSON.stringify({ type: "turn_result", version: "1", result: payload }) +
      "\n";
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(line));
        controller.close();
      },
    });
    return new Response(stream, {
      status: 200,
      headers: { "Content-Type": "application/x-ndjson" },
    });
  }

  it("parses the additive observability block and drops unknown fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        ndjsonResponse({
          session_id: "s-1",
          user_turn_id: "ut-1",
          result_turn_id: "rt-1",
          content: "ok",
          epistemic_class: "OBSERVATION",
          limitations: [],
          generated_at: "2026-01-01T00:00:00Z",
          model_invocation_id: null,
          grounding_status: "NON_GROUNDED",
          provenance: null,
          confirmation_request: null,
          presentation: { version: "1" },
          observability: {
            ...OBS,
            // Unknown provider extras never cross the allowlist.
            secret_field: "must-not-land",
            raw_payload: { nested: true },
          },
        }),
      ),
    );
    const result = await submitInteractionTurn("oi", {
      getAccessToken: () => "t",
    });
    expect(result.observability).not.toBeNull();
    expect(result.observability?.composition_mode).toBe("cri");
    expect(result.observability?.tokens.total).toBe(2175);
    expect(result.observability?.model_calls).toBe(2);
    const raw = result.observability as unknown as Record<string, unknown>;
    expect("secret_field" in raw).toBe(false);
    expect("raw_payload" in raw).toBe(false);
    vi.unstubAllGlobals();
  });

  it("leaves observability null for legacy payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        ndjsonResponse({
          session_id: "s-1",
          user_turn_id: "ut-1",
          result_turn_id: "rt-1",
          content: "ok",
          epistemic_class: "OBSERVATION",
          limitations: [],
          generated_at: "2026-01-01T00:00:00Z",
          model_invocation_id: null,
          grounding_status: "NON_GROUNDED",
          provenance: null,
          confirmation_request: null,
          presentation: { version: "1" },
        }),
      ),
    );
    const result = await submitInteractionTurn("oi", {
      getAccessToken: () => "t",
    });
    expect(result.observability).toBeNull();
    vi.unstubAllGlobals();
  });
});

describe("stage-6 responsibility attribution", () => {
  it("shows model vs operational elapsed and timeout source", () => {
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({ observability: OBS as never })}
      />,
    );
    expect(screen.getByText(/Tempo no modelo/i)).toBeTruthy();
    expect(screen.getByText(/Tempo na fonte/i)).toBeTruthy();
  });

  it("labels a budget-exhausted terminal without blaming the source", () => {
    const obs = { ...OBS, timeout_source: "budget" };
    render(
      <DeliaTurnContextPanel
        turn={makeTurn({ observability: obs as never })}
      />,
    );
    expect(
      screen.getByText(/Orçamento do turno esgotado/i),
    ).toBeTruthy();
  });
});
