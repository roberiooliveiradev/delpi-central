import type {
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../data/types/settings";

export function buildSettingsPayloadFromResponse(
  data: StrategicIndicatorsSettingsResponse,
): StrategicIndicatorsSettingsUpdateRequest {
  return {
    weights: { items: data.weights.items },
    goals: { items: data.goals.items },
    parameters: { items: data.parameters.items },
    governance: { items: data.governance.items },
  };
}

export function normalizeSettingsPayload(
  payload: StrategicIndicatorsSettingsUpdateRequest,
): string {
  return JSON.stringify(payload);
}

export function hasSettingsChanged(
  original: StrategicIndicatorsSettingsUpdateRequest,
  current: StrategicIndicatorsSettingsUpdateRequest,
): boolean {
  return normalizeSettingsPayload(original) !== normalizeSettingsPayload(current);
}