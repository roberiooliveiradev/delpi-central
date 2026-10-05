import { describe, expect, it } from "vitest";

import {
  DELPI_WORKSPACE_CONTEXT_EVENT,
  publishPlaylistWorkspaceContext,
  publishSurfaceWorkspaceContext,
  type TvDashboardWorkspaceContext,
} from "./workspaceContext";

function capture(): {
  events: TvDashboardWorkspaceContext[];
  detach: () => void;
} {
  const events: TvDashboardWorkspaceContext[] = [];
  const handler = (event: Event) => {
    events.push(
      (event as CustomEvent<TvDashboardWorkspaceContext>).detail,
    );
  };
  window.addEventListener(DELPI_WORKSPACE_CONTEXT_EVENT, handler);
  return {
    events,
    detach: () =>
      window.removeEventListener(DELPI_WORKSPACE_CONTEXT_EVENT, handler),
  };
}

describe("workspaceContext publisher (§6.130)", () => {
  it("publishes playlist + selected slide as entity refs", () => {
    const { events, detach } = capture();
    try {
      publishPlaylistWorkspaceContext({
        playlistId: "pl-1",
        viewRef: "deck_editor",
        selectedSlideId: "sl-9",
        playlistLabel: "Piso A",
      });
    } finally {
      detach();
    }
    expect(events).toHaveLength(1);
    const ctx = events[0];
    expect(ctx.host_app_id).toBe("tv-dashboard");
    expect(ctx.view_ref).toBe("deck_editor");
    expect(ctx.selected_entity_ref).toEqual({
      entity_type: "slide",
      entity_id: "sl-9",
      source_system: "vista",
    });
    expect(ctx.entity_refs).toEqual([
      { entity_type: "slide", entity_id: "sl-9", source_system: "vista" },
      {
        entity_type: "playlist",
        entity_id: "pl-1",
        source_system: "vista",
        label: "Piso A",
      },
    ]);
  });

  it("falls back to the playlist as selected ref without a slide", () => {
    const { events, detach } = capture();
    try {
      publishPlaylistWorkspaceContext({
        playlistId: "pl-2",
        viewRef: "preview",
      });
    } finally {
      detach();
    }
    const ctx = events[0];
    expect(ctx.selected_entity_ref).toEqual({
      entity_type: "playlist",
      entity_id: "pl-2",
      source_system: "vista",
    });
    expect(ctx.entity_refs).toHaveLength(1);
  });

  it("publishes playlist-less surfaces without entity refs", () => {
    const { events, detach } = capture();
    try {
      publishSurfaceWorkspaceContext("tv_dashboard_list");
    } finally {
      detach();
    }
    expect(events).toEqual([
      { host_app_id: "tv-dashboard", view_ref: "tv_dashboard_list" },
    ]);
  });
});
