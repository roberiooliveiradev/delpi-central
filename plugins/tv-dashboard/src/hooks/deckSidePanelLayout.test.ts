import { describe, expect, it } from "vitest";

import {
  clampDeckSidePanelWidth,
  getDeckSidePanelLimits,
  readDeckSidePanelCollapsed,
  readDeckSidePanelWidth,
  writeDeckSidePanelCollapsed,
  writeDeckSidePanelWidth,
} from "../hooks/deckSidePanelLayout";

describe("deckSidePanelLayout", () => {
  it("limita largura do filmstrip e do inspetor", () => {
    expect(clampDeckSidePanelWidth("filmstrip", 50)).toBe(140);
    expect(clampDeckSidePanelWidth("filmstrip", 900)).toBe(320);
    expect(clampDeckSidePanelWidth("inspector", 100)).toBe(260);
    expect(clampDeckSidePanelWidth("inspector", 900)).toBe(560);
  });

  it("persiste largura e recolhimento no localStorage", () => {
    const filmstrip = getDeckSidePanelLimits("filmstrip");
    writeDeckSidePanelWidth("filmstrip", 240);
    writeDeckSidePanelCollapsed("filmstrip", true);
    expect(readDeckSidePanelWidth("filmstrip")).toBe(240);
    expect(readDeckSidePanelCollapsed("filmstrip")).toBe(true);
    writeDeckSidePanelCollapsed("filmstrip", false);
    expect(readDeckSidePanelCollapsed("filmstrip")).toBe(false);
    expect(filmstrip.collapsedWidth).toBe(40);
  });
});
