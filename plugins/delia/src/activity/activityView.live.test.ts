/**
 * Live ActivityEvent.v1 → ActivityViewerProps reducer tests (doc 70 §16):
 * every step must come from a real observed event — nothing invented.
 */
import { describe, expect, it } from "vitest";

import { buildLiveActivityView } from "./activityView";
import type { DeliaActivityEvent } from "../api/interactionClient";

let seq = 0;
function ev(overrides: Partial<DeliaActivityEvent>): DeliaActivityEvent {
  seq += 1;
  return {
    version: "1",
    event_id: `ev-${seq}`,
    sequence: seq,
    timestamp: "2026-01-01T00:00:00+00:00",
    session_id: "s",
    turn_id: "t",
    phase: "REQUEST_RECEIVED",
    state: "completed",
    label_code: "REQUEST_RECEIVED",
    ...overrides,
  };
}

describe("buildLiveActivityView", () => {
  it("returns null without events — the honest generic fallback stays", () => {
    expect(buildLiveActivityView([])).toBeNull();
  });

  it("keeps running state while no terminal event arrived", () => {
    const view = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "CONTEXTUALIZING", state: "running" }),
    ])!;
    expect(view.state).toBe("running");
    const labels = view.steps!.map((s) => s.label);
    expect(labels).toContain("Solicitação recebida");
    expect(labels).toContain("Entendendo a solicitação");
  });

  it("shows the selected capability and owner only when observed", () => {
    const view = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "CONTEXTUALIZING", state: "running" }),
      ev({
        phase: "CAPABILITY_SELECTED",
        state: "completed",
        capability_ref: { remote_name: "list_items" },
        owner_ref: { display_name: "DAVI — Dados e Informações" },
      }),
    ])!;
    const step = view.steps!.find((s) => s.label === "Capacidade selecionada")!;
    // remote_name is a technical identifier — never a display label.
    expect(step.capabilityLabel).toBeUndefined();
    expect(step.sourceLabel).toContain("DAVI");
    expect(JSON.stringify(view)).not.toContain("list_items");
    // The contextualizing step auto-resolves — no invented progress.
    expect(
      view.steps!.find((s) => s.label === "Entendendo a solicitação")!
        .state,
    ).toBe("completed");
  });

  it("resolves a started query step in place on completion", () => {
    const view = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({
        phase: "SOURCE_QUERY_STARTED",
        state: "running",
        capability_ref: { remote_name: "list_items" },
        owner_ref: { display_name: "DAVI" },
      }),
      ev({
        phase: "SOURCE_QUERY_COMPLETED",
        state: "completed",
        capability_ref: { remote_name: "list_items", protocol: "MCP" },
        source_ref: { source_system: "Cadastro DELPI" },
        outcome_ref: { status: "returned_data", record_count: 1 },
      }),
    ])!;
    const query = view.steps!.find((s) => s.label === "Consulta finalizada")!;
    expect(query.state).toBe("completed");
    expect(query.description).toBe("1 registro(s) localizado(s)");
    expect(query.sourceLabel).toBe("Cadastro DELPI");
    expect(view.sources).toHaveLength(1);
    // protocol is transport mechanics — never surfaced as detail.
    expect(view.sources![0].detail).toBeUndefined();
    expect(JSON.stringify(view)).not.toContain("list_items");
    expect(JSON.stringify(view)).not.toContain("MCP");
  });

  it("marks a failed source query honestly — never as success", () => {
    const view = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "SOURCE_QUERY_STARTED", state: "running" }),
      ev({
        phase: "SOURCE_QUERY_COMPLETED",
        state: "failed",
        outcome_ref: { status: "error" },
      }),
      ev({ phase: "BLOCKED", state: "blocked" }),
    ])!;
    const step = view.steps!.find((s) => s.label === "Consulta finalizada")!;
    expect(step.state).toBe("failed");
    expect(step.description).toBe("consulta falhou");
    expect(view.state).toBe("blocked");
  });

  it("maps terminal phases to truthful overall states", () => {
    const completed = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "COMPLETED", state: "completed" }),
    ])!;
    expect(completed.state).toBe("completed");
    expect(completed.title).toBe("Atividade concluída");

    const waiting = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "WAITING_CONFIRMATION", state: "waiting" }),
    ])!;
    expect(waiting.state).toBe("pending");
    expect(waiting.title).toBe("Aguardando uma decisão governada");

    const denied = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "BLOCKED", state: "denied" }),
    ])!;
    expect(denied.state).toBe("denied");
    expect(denied.outcome?.persistent).toBe(true);

    const failed = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "FAILED", state: "failed" }),
    ])!;
    expect(failed.state).toBe("failed");
    expect(failed.outcome?.tone).toBe("danger");
  });

  it("never invents a specialist when no capability event arrived", () => {
    const view = buildLiveActivityView([
      ev({ phase: "REQUEST_RECEIVED", state: "completed" }),
      ev({ phase: "OUTCOME_PREPARING", state: "running" }),
      ev({ phase: "COMPLETED", state: "completed" }),
    ])!;
    const wire = JSON.stringify(view);
    expect(wire).not.toContain("DAVI");
    expect(wire).not.toContain("capability");
    expect(view.state).toBe("completed");
  });
});
