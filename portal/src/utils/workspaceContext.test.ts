import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  DELPI_WORKSPACE_CONTEXT_EVENT,
  clearWorkspaceContext,
  getWorkspaceContext,
  initWorkspaceContextListener,
} from "./workspaceContext.ts";

// Node:test has no DOM — stub `window` with a plain EventTarget.
// `initWorkspaceContextListener` guards on typeof window, so we set
// it before init and dispatch CustomEvents through the same target.
const eventTarget = new EventTarget();
(globalThis as Record<string, unknown>).window = eventTarget;

function publish(detail: unknown): void {
  eventTarget.dispatchEvent(
    new CustomEvent(DELPI_WORKSPACE_CONTEXT_EVENT, { detail }),
  );
}

describe("workspaceContext registry (§6.130)", () => {
  it("stores the latest valid published context", () => {
    initWorkspaceContextListener();
    clearWorkspaceContext();
    publish({
      host_app_id: "tv-dashboard",
      view_ref: "deck_editor",
      selected_entity_ref: {
        entity_type: "slide",
        entity_id: "s-1",
        source_system: "vista",
      },
      entity_refs: [
        { entity_type: "slide", entity_id: "s-1", source_system: "vista" },
        { entity_type: "playlist", entity_id: "p-1", source_system: "vista" },
      ],
    });
    const ctx = getWorkspaceContext();
    assert.equal(ctx?.host_app_id, "tv-dashboard");
    assert.equal(ctx?.selected_entity_ref?.entity_id, "s-1");
  });

  it("rejects malformed payloads (missing host_app_id)", () => {
    clearWorkspaceContext();
    publish({ view_ref: "deck_editor" });
    assert.equal(getWorkspaceContext(), null);
  });

  it("rejects oversized entity_refs lists", () => {
    clearWorkspaceContext();
    publish({
      host_app_id: "tv-dashboard",
      entity_refs: Array.from({ length: 5 }, (_, i) => ({
        entity_type: "slide",
        entity_id: `s-${i}`,
        source_system: "vista",
      })),
    });
    assert.equal(getWorkspaceContext(), null);
  });

  it("clear removes stale context (route-change semantics)", () => {
    publish({ host_app_id: "tv-dashboard", view_ref: "deck_editor" });
    assert.ok(getWorkspaceContext());
    clearWorkspaceContext();
    assert.equal(getWorkspaceContext(), null);
  });

  it("returns a defensive copy, never the stored object", () => {
    clearWorkspaceContext();
    publish({ host_app_id: "tv-dashboard", view_ref: "x" });
    const first = getWorkspaceContext();
    if (first) (first as Record<string, unknown>).host_app_id = "mutated";
    assert.equal(getWorkspaceContext()?.host_app_id, "tv-dashboard");
  });
});
