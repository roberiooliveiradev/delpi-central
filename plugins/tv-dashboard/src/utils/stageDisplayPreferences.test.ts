import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";

import {
  DEFAULT_STAGE_DISPLAY_PREFERENCES,
  normalizeStageDisplayPreferences,
  readStageDisplayPreferences,
  stageViewNeedsInitialFit,
  writeStageDisplayPreferences,
} from "./stageDisplayPreferences";

describe("stageDisplayPreferences", () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("normaliza payload inválido para defaults", () => {
    expect(normalizeStageDisplayPreferences(null)).toEqual(DEFAULT_STAGE_DISPLAY_PREFERENCES);
    expect(normalizeStageDisplayPreferences({ showStageGrid: "yes" }).showStageGrid).toBe(
      DEFAULT_STAGE_DISPLAY_PREFERENCES.showStageGrid,
    );
  });

  it("persiste e relê preferências de exibição inclusive âncora do palco", () => {
    writeStageDisplayPreferences({
      stageZoom: 0.7,
      showStageRulers: false,
      showStageGrid: true,
      stageGridSizePx: 50,
      showStageGuides: false,
      snapEnabled: false,
      stageViewAnchorX: 120.5,
      stageViewAnchorY: -40,
      stageScrollLeft: 340,
      stageScrollTop: 210,
      stageViewAnchorSaved: true,
    });

    expect(readStageDisplayPreferences()).toEqual({
      stageZoom: 0.7,
      showStageRulers: false,
      showStageGrid: true,
      stageGridSizePx: 50,
      showStageGuides: false,
      snapEnabled: false,
      stageViewAnchorX: 120.5,
      stageViewAnchorY: -40,
      stageScrollLeft: 340,
      stageScrollTop: 210,
      stageViewAnchorSaved: true,
    });
  });

  it("prefs antigas sem âncora ficam com stageViewAnchorSaved false", () => {
    expect(
      normalizeStageDisplayPreferences({
        stageZoom: 0.8,
        showStageRulers: true,
        showStageGrid: false,
        showStageGuides: true,
        snapEnabled: true,
      }).stageViewAnchorSaved,
    ).toBe(false);
  });

  it("sem âncora salva indica bootstrap com Ajustar", () => {
    expect(stageViewNeedsInitialFit({ stageViewAnchorSaved: false })).toBe(true);
    expect(stageViewNeedsInitialFit({ stageViewAnchorSaved: true })).toBe(false);
    expect(stageViewNeedsInitialFit(DEFAULT_STAGE_DISPLAY_PREFERENCES)).toBe(true);
  });

  it("limita zoom e tamanho da grade ao intervalo válido", () => {
    expect(normalizeStageDisplayPreferences({ stageZoom: 9 }).stageZoom).toBe(2);
    expect(normalizeStageDisplayPreferences({ stageZoom: 0.05 }).stageZoom).toBe(0.1);
    expect(normalizeStageDisplayPreferences({ stageGridSizePx: 2 }).stageGridSizePx).toBe(10);
    expect(normalizeStageDisplayPreferences({ stageGridSizePx: 9000 }).stageGridSizePx).toBe(540);
  });
});
