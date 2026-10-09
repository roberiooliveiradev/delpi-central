import { describe, expect, it } from "vitest";

import { buildDeliaActivityView } from "./activity/activityView";
import type { ConversationDisplayTurn } from "./ui/ConversationTimeline";

function deliaTurn(
  overrides: Partial<ConversationDisplayTurn> = {},
): ConversationDisplayTurn {
  return {
    id: "t1",
    role: "delia",
    content: "Resposta.",
    presentation: {
      messageKind: "RESULT",
      semanticStatus: null,
      groundingStatus: "NON_GROUNDED",
      blocks: [],
      allowedInteractions: ["reply"],
    },
    ...overrides,
  };
}

describe("buildDeliaActivityView", () => {
  it("returns null for user turns", () => {
    expect(
      buildDeliaActivityView({ id: "u", role: "user", content: "x" }),
    ).toBeNull();
  });

  it("maps a bare RESULT to completed with honest minimal steps", () => {
    const view = buildDeliaActivityView(deliaTurn());
    expect(view?.state).toBe("completed");
    expect(view?.title).toBe("Atividade concluída");
    const labels = view?.steps?.map((s) => s.label) ?? [];
    expect(labels).toEqual([
      "Solicitação recebida",
      "Resposta elaborada",
    ]);
    expect(view?.sources).toBeUndefined();
  });

  it("does not invent capability/source steps without provenance", () => {
    const view = buildDeliaActivityView(deliaTurn());
    const labels = view?.steps?.map((s) => s.label) ?? [];
    expect(labels).not.toContain("Capacidade acionada");
    expect(labels).not.toContain("Fonte consultada");
  });

  it("maps provenance to capability + source steps and source item", () => {
    const view = buildDeliaActivityView(
      deliaTurn({
        groundingStatus: "GROUNDED",
        provenance: {
          specialist_id: "davi",
          remote_capability: "consultar_indicador",
          protocol: "mcp",
          is_complete: true,
          source: {
            source_id: "erp-1",
            source_system: "TOTVS",
            observed_at: "2026-10-09T14:00:00Z",
          },
        },
      }),
    );
    expect(view?.steps?.map((s) => s.label)).toContain("Capacidade acionada");
    expect(view?.steps?.map((s) => s.label)).toContain("Fonte consultada");
    expect(view?.sources?.[0].label).toBe("TOTVS");
    expect(view?.sources?.[0].statusLabel).toBe("resultado fundamentado");
    expect(view?.outcome?.label).toContain("fundamentado");
  });

  it("marks incomplete provenance as partial, never grounded", () => {
    const view = buildDeliaActivityView(
      deliaTurn({
        groundingStatus: "NON_GROUNDED",
        provenance: {
          is_complete: false,
          source: { source_id: "erp-1", source_system: "TOTVS" },
        },
      }),
    );
    const sourceStep = view?.steps?.find((s) => s.id === "source");
    expect(sourceStep?.state).toBe("partial");
    expect(view?.sources?.[0].statusLabel).toBe("consultada");
  });

  it("maps AUTHZ_DENIED to denied with persistent outcome", () => {
    const view = buildDeliaActivityView(
      deliaTurn({
        presentation: {
          messageKind: "AUTHZ_DENIED",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [],
          allowedInteractions: ["reply"],
        },
      }),
    );
    expect(view?.state).toBe("denied");
    expect(view?.title).toBe("Atividade não autorizada");
    expect(view?.outcome?.persistent).toBe(true);
  });

  it("maps SOURCE_UNAVAILABLE and PRECONDITION_REQUIRED to blocked", () => {
    for (const kind of [
      "SOURCE_UNAVAILABLE",
      "PRECONDITION_REQUIRED",
    ] as const) {
      const view = buildDeliaActivityView(
        deliaTurn({
          presentation: {
            messageKind: kind,
            semanticStatus: null,
            groundingStatus: null,
            blocks: [],
            allowedInteractions: ["reply"],
          },
        }),
      );
      expect(view?.state).toBe("blocked");
      expect(view?.outcome?.persistent).toBe(true);
    }
  });

  it("maps CONFIRMATION_REQUIRED to pending", () => {
    const view = buildDeliaActivityView(
      deliaTurn({
        presentation: {
          messageKind: "CONFIRMATION_REQUIRED",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [],
          allowedInteractions: ["reply", "confirm", "reject"],
        },
      }),
    );
    expect(view?.state).toBe("pending");
  });

  it("respects an explicit activityView override (demo fixtures)", () => {
    const override = {
      title: "Atividade demo",
      state: "completed" as const,
    };
    expect(
      buildDeliaActivityView(deliaTurn({ activityView: override })),
    ).toBe(override);
  });

  it("never fabricates timestamps for absent observed_at", () => {
    const view = buildDeliaActivityView(
      deliaTurn({
        provenance: {
          is_complete: true,
          source: { source_id: "s", source_system: "X" },
        },
      }),
    );
    const sourceStep = view?.steps?.find((s) => s.id === "source");
    expect(sourceStep?.timestampLabel).toBeUndefined();
  });
});
