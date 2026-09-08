import { describe, expect, it } from "vitest";

import type { AdminChatIntelligenceSettingsPayload } from "../../../../data/api/adminTypes";
import {
  applyIntelligencePreset,
  detectIntelligencePreset,
  getIntelligencePreset,
  INTELLIGENCE_PRESETS,
} from "./chatIntelligencePresets";

const BASE: AdminChatIntelligenceSettingsPayload = {
  ragContextMinScore: 0.35,
  externalActionSemanticMinScore: 0.4,
  externalActionSemanticRankEnabled: false,
  chatToolRouterEnabled: false,
  chatHistorySummaryEnabled: false,
  ragHybridEnabled: false,
  ragRerankEnabled: false,
  ragFtsEnabled: false,
  nativeToolCallingEnabled: true,
  agenticLoopEnabled: false,
  agenticLoopMaxSteps: 3,
  webSearchEnabled: false,
  operationalFastPathEnabled: true,
  externalActionDirectResponseEnabled: true,
  preferApiExternaProvider: true,
  multiActionEnabled: false,
  paginationAutoFetchEnabled: false,
  externalActionEmbeddingOnImport: false,
  ragPreferKeywordSearch: false,
  ragIdentityQuestionMinScore: 0.5,
  fastPathEnabled: true,
  assistantIdentityDirectEnabled: true,
  webSearchDirectResponseEnabled: true,
  webSearchAutoAugmentEnabled: false,
};

describe("chatIntelligencePresets", () => {
  it("define três presets com patches não vazios", () => {
    expect(INTELLIGENCE_PRESETS).toHaveLength(3);
    for (const preset of INTELLIGENCE_PRESETS) {
      expect(Object.keys(preset.patch).length).toBeGreaterThan(5);
      expect(getIntelligencePreset(preset.key)?.key).toBe(preset.key);
    }
  });

  it("aplica balanced e detecta o mesmo preset", () => {
    const next = applyIntelligencePreset(BASE, "balanced");
    expect(detectIntelligencePreset(next)).toBe("balanced");
    expect(next.ragHybridEnabled).toBe(true);
    expect(next.agenticLoopEnabled).toBe(false);
  });

  it("retorna custom quando um knob diverge do patch", () => {
    const next = applyIntelligencePreset(BASE, "fast");
    expect(detectIntelligencePreset(next)).toBe("fast");
    expect(
      detectIntelligencePreset({ ...next, ragHybridEnabled: true }),
    ).toBe("custom");
  });

  it("max_quality liga rerank e agentic", () => {
    const next = applyIntelligencePreset(BASE, "max_quality");
    expect(detectIntelligencePreset(next)).toBe("max_quality");
    expect(next.ragRerankEnabled).toBe(true);
    expect(next.agenticLoopEnabled).toBe(true);
    expect(next.agenticLoopMaxSteps).toBe(6);
  });
});
