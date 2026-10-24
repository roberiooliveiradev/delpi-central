/**
 * Spec 127 — message context popover bound to real turn data +
 * conversation-scoped global panel + wire parse of the additive
 * observability projection.
 */
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DeliaConversationContextPanel,
  DeliaTurnContextPanel,
} from "./contextPanel";
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

describe("Message context inline expansion (INLINE-01..INLINE-14)", () => {
  function renderMessage(turn = makeTurn()) {
    return render(
      <ul>
        <li className="delia-turn delia-turn--delia delpi-ui-message-action-scope">
          <DeliaAssistantMessage
            turn={turn}
            loading={false}
            onConfirmation={vi.fn()}
          />
        </li>
      </ul>,
    );
  }

  it("INLINE-01/08: 'Ver contexto' is a visible disclosure control bound to a region", () => {
    renderMessage();
    const action = screen.getByRole("button", { name: "Ver contexto" });
    expect(action.getAttribute("aria-expanded")).toBe("false");
    expect(action.getAttribute("aria-controls")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Copiar resposta" }),
    ).toBeTruthy();
  });

  it("INLINE-01/02/03: expands a real region inside the message — no portal, no overlay", () => {
    renderMessage(makeTurn({ observability: OBS as never }));
    fireEvent.click(screen.getByRole("button", { name: "Ver contexto" }));
    const region = screen.getByRole("region", {
      name: "Contexto desta resposta",
    });
    expect(within(region).getByText("Contexto desta resposta")).toBeTruthy();
    expect(within(region).getByText("qwen2.5:3b (1)")).toBeTruthy();
    // INLINE-08: aria-controls points at the real region.
    const trigger = screen.getByRole("button", { name: "Ocultar contexto" });
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    expect(trigger.getAttribute("aria-controls")).toBe(region.id);
    // INLINE-02: region lives inside the turn bubble (flow), not a body portal.
    expect(region.closest(".delia-turn__bubble")).toBeTruthy();
    expect(
      region.closest(".delpi-ui-shape-menu__panel"),
    ).toBeNull();
    // No side/complementary panel opened.
    expect(screen.queryByRole("complementary")).toBeNull();
    expect(
      document.querySelector(".delpi-ui-shape-menu__panel--portal"),
    ).toBeNull();
  });

  it("INLINE-05: 'Ocultar contexto' collapses only that region", () => {
    renderMessage();
    fireEvent.click(screen.getByRole("button", { name: "Ver contexto" }));
    expect(
      screen.getByRole("region", { name: "Contexto desta resposta" }),
    ).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: "Ocultar contexto" }),
    );
    expect(
      screen.queryByRole("region", { name: "Contexto desta resposta" }),
    ).toBeNull();
  });

  it("INLINE-06: outside clicks and Escape never collapse it", () => {
    renderMessage();
    fireEvent.click(screen.getByRole("button", { name: "Ver contexto" }));
    const region = screen.getByRole("region", {
      name: "Contexto desta resposta",
    });
    fireEvent.pointerDown(document.body);
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(
      screen.getByRole("region", { name: "Contexto desta resposta" }),
    ).toBe(region);
    expect(
      screen.getByRole("button", { name: "Ocultar contexto" }).getAttribute(
        "aria-expanded",
      ),
    ).toBe("true");
  });

  it("INLINE-09: shows only the turn's own provenance and sources", () => {
    renderMessage(
      makeTurn({
        groundingStatus: "GROUNDED",
        provenance: {
          specialist_id: "mcp:x",
          remote_capability: "search_things",
          source: {
            source_id: "src-1",
            source_system: "api-delpi",
            observed_at: "2026-01-01T12:00:00Z",
          },
        },
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Ver contexto" }));
    const region = screen.getByRole("region", {
      name: "Contexto desta resposta",
    });
    expect(within(region).getByText("mcp:x")).toBeTruthy();
    expect(within(region).getByText("search_things")).toBeTruthy();
  });

  it("INLINE-10: material limitations stay visible on the message itself", () => {
    renderMessage(makeTurn({ limitations: ["resultado truncado"] }));
    // Visible without expanding the region.
    expect(screen.getByText(/resultado truncado/)).toBeTruthy();
  });

  it("INLINE-07: two messages stay expanded simultaneously, isolated", () => {
    const obsA = { ...OBS, composition_mode: "cri" };
    const obsB = { ...OBS, composition_mode: "model" };
    render(
      <ul>
        {[
          makeTurn({ id: "a", content: "R-A", observability: obsA as never }),
          makeTurn({ id: "b", content: "R-B", observability: obsB as never }),
        ].map((turn) => (
          <li
            key={turn.id}
            className="delia-turn delia-turn--delia delpi-ui-message-action-scope"
          >
            <DeliaAssistantMessage
              turn={turn}
              loading={false}
              onConfirmation={vi.fn()}
            />
          </li>
        ))}
      </ul>,
    );
    for (const trigger of screen.getAllByRole("button", {
      name: "Ver contexto",
    })) {
      fireEvent.click(trigger);
    }
    const regions = screen.getAllByRole("region", {
      name: "Contexto desta resposta",
    });
    expect(regions).toHaveLength(2);
    expect(
      within(regions[0]).getByText("Resposta organizada com CRI"),
    ).toBeTruthy();
    expect(
      within(regions[0]).queryByText("Resposta gerada pelo modelo"),
    ).toBeNull();
    expect(
      within(regions[1]).getByText("Resposta gerada pelo modelo"),
    ).toBeTruthy();
    // Collapsing the first never touches the second.
    fireEvent.click(
      screen.getAllByRole("button", { name: "Ocultar contexto" })[0],
    );
    const remaining = screen.getAllByRole("region", {
      name: "Contexto desta resposta",
    });
    expect(remaining).toHaveLength(1);
    expect(
      within(remaining[0]).getByText("Resposta gerada pelo modelo"),
    ).toBeTruthy();
  });
});

describe("DeliaConversationContextPanel (GC-01..GC-08)", () => {
  it("GC-01/08: conversation-scoped and honestly empty without a global contract", () => {
    render(<DeliaConversationContextPanel />);
    expect(
      screen.getByText(/Nenhum contexto adicional vinculado a esta conversa/i),
    ).toBeTruthy();
    // No fabricated sections (GC-02/03/04): no Files/Links/Sources blocks.
    for (const heading of ["Arquivos", "Links", "Fontes"]) {
      expect(screen.queryByText(heading)).toBeNull();
    }
  });

  it("GC-04/05: never derives global sources from individual turns", () => {
    render(<DeliaConversationContextPanel />);
    // Even with grounded turns in the timeline, the panel stays empty —
    // it receives no per-turn aggregate at all.
    expect(screen.queryByText(/api-delpi/)).toBeNull();
    expect(screen.queryByText(/mcp:x/)).toBeNull();
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

describe("Clean inline context card (CLEANCTX-01..CLEANCTX-16)", () => {
  function renderMessage(turn = makeTurn()) {
    return render(
      <ul>
        <li className="delia-turn delia-turn--delia delpi-ui-message-action-scope">
          <DeliaAssistantMessage
            turn={turn}
            loading={false}
            onConfirmation={vi.fn()}
          />
        </li>
      </ul>,
    );
  }

  function openContext() {
    fireEvent.click(screen.getByRole("button", { name: "Ver contexto" }));
    return screen.getByRole("region", { name: "Contexto desta resposta" });
  }

  it("CLEANCTX-01: no lateral accent bar is applied to the bubble", () => {
    renderMessage();
    const bubble = document.querySelector(".delia-turn__bubble");
    openContext();
    expect(bubble?.classList.contains("delia-turn__bubble--context-open")).toBe(
      false,
    );
  });

  it("CLEANCTX-03: header has a single title + subtitle, no duplicate control", () => {
    renderMessage();
    const region = openContext();
    expect(
      within(region).getByRole("heading", { name: "Contexto desta resposta" }),
    ).toBeTruthy();
    expect(
      within(region).getByText(
        "Detalhes da geração, evidências e atividade relacionada.",
      ),
    ).toBeTruthy();
    // The only hide control stays in the message action strip.
    expect(
      within(region).queryByRole("button", { name: "Ocultar contexto" }),
    ).toBeNull();
    expect(
      screen.getAllByRole("button", { name: "Ocultar contexto" }),
    ).toHaveLength(1);
  });

  it("CLEANCTX-04/05: 'Detalhes da geração' renders real label/value pairs", () => {
    renderMessage(makeTurn({ observability: OBS as never }));
    const region = openContext();
    expect(
      within(region).getByRole("heading", { name: "Detalhes da geração" }),
    ).toBeTruthy();
    expect(within(region).getByText("qwen2.5:3b (1)")).toBeTruthy();
    expect(within(region).getByText("Custo indisponível")).toBeTruthy();
  });

  it("CLEANCTX-10: technical trace sits in a collapsed disclosure", () => {
    renderMessage(makeTurn({ observability: OBS as never }));
    const region = openContext();
    const trace = region.querySelector("details.delia-context__trace");
    expect(trace).toBeTruthy();
    expect(trace?.hasAttribute("open")).toBe(false);
    expect(
      within(region).getByText("Rastreamento técnico"),
    ).toBeTruthy();
    // Real span rows remain in the DOM once the disclosure opens.
    fireEvent.click(
      within(region).getByText("Rastreamento técnico"),
    );
    expect(trace?.hasAttribute("open")).toBe(true);
    expect(
      within(region).getByText("delia.capability_orchestration.select_group"),
    ).toBeTruthy();
  });

  it("CLEANCTX-06/09: evidences and related activities keep real titles", () => {
    const turn = makeTurn({
      observability: OBS as never,
      groundingStatus: "NON_GROUNDED",
      activityView: {
        title: "Atividade concluída",
        state: "completed",
        steps: [
          { id: "r", label: "Solicitação recebida", state: "completed" },
        ],
      } as never,
    });
    renderMessage(turn);
    const region = openContext();
    expect(
      within(region).getByRole("heading", { name: "Evidências" }),
    ).toBeTruthy();
    expect(
      within(region).getByRole("heading", {
        name: "Atividades relacionadas",
      }),
    ).toBeTruthy();
    // CLEANCTX-07: "Sem fonte vinculada" is neutral context copy.
    expect(within(region).getByText("Sem fonte vinculada")).toBeTruthy();
  });
});
