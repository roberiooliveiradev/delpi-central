/**
 * Presets nomeados de knobs de inteligência (admin Plataforma).
 * Patches sobre AdminChatIntelligenceSettingsPayload — sem segundo store.
 */

import type { AdminChatIntelligenceSettingsPayload } from "../../../../data/api/adminTypes";

export type IntelligencePresetKey = "fast" | "balanced" | "max_quality";

export type IntelligencePresetId = IntelligencePresetKey | "custom";

export type IntelligencePresetDefinition = {
  key: IntelligencePresetKey;
  /** Chaves de knobs que o preset define (usadas em detectPreset). */
  patch: Partial<AdminChatIntelligenceSettingsPayload>;
};

/** Labels PT — espelhar em adminHelpTooltips / UI. */
export const INTELLIGENCE_PRESET_LABELS: Record<IntelligencePresetKey, string> = {
  fast: "Rápido",
  balanced: "Equilibrado",
  max_quality: "Máxima qualidade",
};

/**
 * Três perfis derivados do impacto velocidade/qualidade em chatIntelligenceSettingMeta.
 * Só knobs booleanos/números do contrato; não inclui source/defaults.
 */
export const INTELLIGENCE_PRESETS: readonly IntelligencePresetDefinition[] = [
  {
    key: "fast",
    patch: {
      operationalFastPathEnabled: true,
      externalActionDirectResponseEnabled: true,
      fastPathEnabled: true,
      assistantIdentityDirectEnabled: true,
      webSearchDirectResponseEnabled: true,
      ragHybridEnabled: false,
      ragRerankEnabled: false,
      ragFtsEnabled: false,
      ragPreferKeywordSearch: true,
      multiActionEnabled: false,
      paginationAutoFetchEnabled: false,
      agenticLoopEnabled: false,
      agenticLoopMaxSteps: 2,
      chatToolRouterEnabled: false,
      nativeToolCallingEnabled: true,
      externalActionSemanticRankEnabled: false,
      chatHistorySummaryEnabled: false,
      webSearchAutoAugmentEnabled: false,
      webSearchEnabled: false,
    },
  },
  {
    key: "balanced",
    patch: {
      operationalFastPathEnabled: true,
      externalActionDirectResponseEnabled: true,
      fastPathEnabled: true,
      assistantIdentityDirectEnabled: true,
      webSearchDirectResponseEnabled: true,
      ragHybridEnabled: true,
      ragRerankEnabled: false,
      ragFtsEnabled: true,
      ragPreferKeywordSearch: false,
      multiActionEnabled: true,
      paginationAutoFetchEnabled: false,
      agenticLoopEnabled: false,
      agenticLoopMaxSteps: 3,
      chatToolRouterEnabled: true,
      nativeToolCallingEnabled: true,
      externalActionSemanticRankEnabled: true,
      chatHistorySummaryEnabled: true,
      webSearchAutoAugmentEnabled: false,
      webSearchEnabled: true,
    },
  },
  {
    key: "max_quality",
    patch: {
      operationalFastPathEnabled: false,
      externalActionDirectResponseEnabled: false,
      fastPathEnabled: false,
      assistantIdentityDirectEnabled: true,
      webSearchDirectResponseEnabled: false,
      ragHybridEnabled: true,
      ragRerankEnabled: true,
      ragFtsEnabled: true,
      ragPreferKeywordSearch: false,
      multiActionEnabled: true,
      paginationAutoFetchEnabled: true,
      agenticLoopEnabled: true,
      agenticLoopMaxSteps: 6,
      chatToolRouterEnabled: true,
      nativeToolCallingEnabled: true,
      externalActionSemanticRankEnabled: true,
      chatHistorySummaryEnabled: true,
      webSearchAutoAugmentEnabled: true,
      webSearchEnabled: true,
    },
  },
] as const;

export function getIntelligencePreset(
  key: IntelligencePresetKey,
): IntelligencePresetDefinition | undefined {
  return INTELLIGENCE_PRESETS.find((preset) => preset.key === key);
}

export function applyIntelligencePreset(
  current: AdminChatIntelligenceSettingsPayload,
  key: IntelligencePresetKey,
): AdminChatIntelligenceSettingsPayload {
  const preset = getIntelligencePreset(key);
  if (!preset) {
    return { ...current };
  }
  return { ...current, ...preset.patch };
}

function valuesMatch(
  settings: Partial<AdminChatIntelligenceSettingsPayload>,
  patch: Partial<AdminChatIntelligenceSettingsPayload>,
): boolean {
  for (const [rawKey, expected] of Object.entries(patch)) {
    const key = rawKey as keyof AdminChatIntelligenceSettingsPayload;
    if (settings[key] !== expected) {
      return false;
    }
  }
  return true;
}

/** Detecta qual preset corresponde aos knobs atuais (ou custom). */
export function detectIntelligencePreset(
  settings: Partial<AdminChatIntelligenceSettingsPayload>,
): IntelligencePresetId {
  for (const preset of INTELLIGENCE_PRESETS) {
    if (valuesMatch(settings, preset.patch)) {
      return preset.key;
    }
  }
  return "custom";
}
