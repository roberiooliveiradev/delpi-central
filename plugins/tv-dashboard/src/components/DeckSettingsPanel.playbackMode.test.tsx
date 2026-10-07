// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetExclusiveAnchoredPanelForTests } from "@delpi/plugin-ui/index";

import type { Playlist } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckSettingsPanel } from "./DeckSettingsPanel";

const DESCRIPTIONS = TV_DASHBOARD_HELP_TOOLTIPS.fields.playbackModeDescriptions;

function playlist(overrides: Partial<Playlist> = {}): Playlist {
  return {
    id: "pl-1",
    name: "Programação",
    defaultDurationSec: 15,
    globalRefreshSec: 300,
    transitionStyle: "fade",
    slides: [],
    ...overrides,
  } as Playlist;
}

function renderPanel(pl: Playlist, onSavePlaylistSettings = vi.fn()) {
  render(
    <div className="dashboard-tv-dashboard">
      <DeckSettingsPanel
        activeTab="playlist"
        playlist={pl}
        slide={null}
        catalog={[]}
        branchScope={null}
        onSavePlaylistSettings={onSavePlaylistSettings}
        onSaveSlide={vi.fn()}
      />
    </div>,
  );
  return onSavePlaylistSettings;
}

function openModePanel(tileLabel: string) {
  fireEvent.click(screen.getAllByRole("button", { name: tileLabel })[0]!);
  const panel = screen.getByRole("dialog", { name: "Modo de reprodução" });
  const group = within(panel).getByRole("group", { name: "Modo de reprodução" });
  return { panel, group };
}

beforeEach(() => resetExclusiveAnchoredPanelForTests());
afterEach(() => {
  cleanup();
  resetExclusiveAnchoredPanelForTests();
});

describe("DeckSettingsPanel — modo de reprodução (SegmentToggle)", () => {
  it("sem playbackMode assume Apresentação no tile e no toggle", () => {
    renderPanel(playlist());
    const { panel, group } = openModePanel("Apresentação");

    const presentation = within(group).getByRole("button", { name: "Apresentação" });
    const meeting = within(group).getByRole("button", { name: "Reunião" });
    expect(presentation.getAttribute("aria-pressed")).toBe("true");
    expect(meeting.getAttribute("aria-pressed")).toBe("false");
    expect(group.classList.contains("delpi-ui-segment-toggle")).toBe(true);
    expect(panel.textContent).toContain(DESCRIPTIONS.presentation);
    expect(panel.querySelector('input[type="radio"]')).toBeNull();
    expect(panel.querySelector('[role="radiogroup"]')).toBeNull();
  });

  it("clicar Reunião grava exatamente playbackMode=meeting", () => {
    const save = renderPanel(playlist());
    const { group } = openModePanel("Apresentação");

    fireEvent.click(within(group).getByRole("button", { name: "Reunião" }));
    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith("playbackMode", "meeting");
  });

  it("em Reunião, tile mostra o modo e clicar Apresentação grava presentation", () => {
    const save = renderPanel(playlist({ playbackMode: "meeting" }));
    const { panel, group } = openModePanel("Reunião");

    expect(
      within(group).getByRole("button", { name: "Reunião" }).getAttribute("aria-pressed"),
    ).toBe("true");
    expect(panel.textContent).toContain(DESCRIPTIONS.meeting);

    fireEvent.click(within(group).getByRole("button", { name: "Apresentação" }));
    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith("playbackMode", "presentation");
  });

  it("clicar o modo já ativo não grava de novo", () => {
    const save = renderPanel(playlist({ playbackMode: "presentation" }));
    const { group } = openModePanel("Apresentação");

    fireEvent.click(within(group).getByRole("button", { name: "Apresentação" }));
    expect(save).not.toHaveBeenCalled();
  });
});
