import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";

import {
  DEFAULT_STAGE_DISPLAY_PREFERENCES,
  normalizeStageDisplayPreferences,
  readStageDisplayPreferences,
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

  it("persiste e relê preferências de exibição", () => {
    writeStageDisplayPreferences({
      stageZoom: 0.7,
      showStageRulers: false,
      showStageGrid: true,
      showStageGuides: false,
      snapEnabled: false,
    });

    expect(readStageDisplayPreferences()).toEqual({
      stageZoom: 0.7,
      showStageRulers: false,
      showStageGrid: true,
      showStageGuides: false,
      snapEnabled: false,
    });
  });

  it("limita zoom ao intervalo válido", () => {
    expect(normalizeStageDisplayPreferences({ stageZoom: 9 }).stageZoom).toBe(2);
    expect(normalizeStageDisplayPreferences({ stageZoom: 0.1 }).stageZoom).toBe(0.5);
  });
});
